#!/usr/bin/env python3
"""
sonic-klish-gen: Generate Klish-based CLI from YANG modules

This tool generates Klish XML CLI command trees, Python action handlers,
and Jinja2 show templates from SONiC YANG modules.

Usage:
    python3 main.py generate config <module_name> --yang-dir <path> --output-dir <path>
"""

import sys
import os
import argparse
from pathlib import Path

SONIC_UTILITIES_PATH = '/home/ubuntu/repos/sonic-utilities'
if os.path.exists(SONIC_UTILITIES_PATH):
    sys.path.insert(0, SONIC_UTILITIES_PATH)

try:
    from sonic_cli_gen.yang_parser import YangParser
except ImportError as e:
    print(f"Error: Cannot import YangParser from sonic-utilities", file=sys.stderr)
    print(f"Tried the following paths:", file=sys.stderr)
    for path in SONIC_UTILITIES_PATHS:
        if path:
            exists = "✓" if os.path.exists(path) else "✗"
            print(f"  {exists} {path}", file=sys.stderr)
    print(f"\nPlease set SONIC_UTILITIES_PATH environment variable or clone sonic-utilities to one of the above paths.", file=sys.stderr)
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)

from ir_builder import IRBuilder
from xml_generator import KlishXmlGenerator
from action_handler_generator import ActionHandlerGenerator
from template_generator import TemplateGenerator


def generate_cli(module_name: str, yang_dir: str, output_dir: str):
    """
    Generate Klish CLI for a YANG module.
    
    Args:
        module_name: Name of the YANG module (e.g., 'sonic-flex_counter')
        yang_dir: Directory containing YANG models
        output_dir: Directory to write generated files
    """
    print(f"Generating Klish CLI for module: {module_name}")
    print(f"YANG directory: {yang_dir}")
    print(f"Output directory: {output_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    xml_dir = output_dir
    scripts_dir = os.path.join(os.path.dirname(output_dir), 'scripts')
    templates_dir = os.path.join(os.path.dirname(output_dir), 'templates')
    os.makedirs(scripts_dir, exist_ok=True)
    os.makedirs(templates_dir, exist_ok=True)
    
    print("\n[1/5] Parsing YANG model...")
    try:
        parser = YangParser(
            yang_model_name=module_name,
            config_db_path='',
            allow_tbl_without_yang=True,
            debug=False
        )
        
        if hasattr(parser.conf_mgmt, 'sy') and hasattr(parser.conf_mgmt.sy, 'yang_dir'):
            parser.conf_mgmt.sy.yang_dir = yang_dir
        
        parsed_yang = parser.parse_yang_model()
        print(f"Successfully parsed YANG model: {module_name}")
        print(f"Found {len(parsed_yang.get('tables', []))} table(s)")
        
    except Exception as e:
        print(f"Error parsing YANG model: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n[2/5] Building Intermediate Representation...")
    try:
        ir_builder = IRBuilder(module_name)
        module_ir = ir_builder.build(parsed_yang)
        print(f"Built IR with {len(module_ir.views)} view(s)")
        for view in module_ir.views:
            print(f"  - {view.name}: {len(view.commands)} command(s)")
    except Exception as e:
        print(f"Error building IR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n[3/5] Generating Klish XML...")
    try:
        xml_generator = KlishXmlGenerator()
        xml_filename = f'{module_name.replace("sonic-", "")}.xml'
        xml_path = os.path.join(xml_dir, xml_filename)
        xml_generator.generate(module_ir, xml_path)
    except Exception as e:
        print(f"Error generating XML: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n[4/5] Generating Python action handler...")
    try:
        handler_generator = ActionHandlerGenerator()
        handler_filename = f'sonic-cli-{module_name.replace("sonic-", "")}.py'
        handler_path = os.path.join(scripts_dir, handler_filename)
        handler_generator.generate(module_name, parsed_yang, handler_path)
        
        os.chmod(handler_path, 0o755)
    except Exception as e:
        print(f"Error generating action handler: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n[5/5] Generating Jinja2 show templates...")
    try:
        template_generator = TemplateGenerator()
        template_generator.generate(module_name, parsed_yang, templates_dir)
    except Exception as e:
        print(f"Error generating templates: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "="*60)
    print("SUCCESS: CLI generation completed!")
    print("="*60)
    print(f"\nGenerated files:")
    print(f"  XML:      {xml_path}")
    print(f"  Handler:  {handler_path}")
    print(f"  Templates: {templates_dir}/")
    print(f"\nNext steps:")
    print(f"  1. Validate XML: xmllint --noout --schema sonic-clish.xsd {xml_path}")
    print(f"  2. Copy files to build directory during build process")
    print(f"  3. Test CLI commands in sonic-mgmt-framework container")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate Klish-based CLI from YANG modules',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 main.py generate config sonic-flex_counter \\
      --yang-dir /path/to/yang-models \\
      --output-dir /path/to/output

  python3 tools/sonic-klish-gen/main.py generate config sonic-flex_counter \\
      --yang-dir build/yang-models \\
      --output-dir CLI/generated-cli/xml
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    gen_parser = subparsers.add_parser('generate', help='Generate CLI from YANG')
    gen_parser.add_argument('mode', choices=['config'], help='Generation mode')
    gen_parser.add_argument('module_name', help='YANG module name (e.g., sonic-flex_counter)')
    gen_parser.add_argument('--yang-dir', required=True, help='Directory containing YANG models')
    gen_parser.add_argument('--output-dir', required=True, help='Output directory for generated files')
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        generate_cli(args.module_name, args.yang_dir, args.output_dir)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
