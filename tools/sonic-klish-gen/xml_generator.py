"""
XML Generator: Generates Klish XML from Intermediate Representation.

This module renders the IR into Klish XML format using Jinja2 templates.
"""

import os
from jinja2 import Environment, FileSystemLoader, Template
from .models import ModuleIR


class KlishXmlGenerator:
    """Generates Klish XML from ModuleIR."""
    
    def __init__(self, templates_dir: str = None):
        """
        Initialize the XML generator.
        
        Args:
            templates_dir: Path to Jinja2 templates directory.
                          If None, uses default templates in this package.
        """
        if templates_dir is None:
            templates_dir = os.path.join(
                os.path.dirname(__file__),
                'templates'
            )
        
        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def generate(self, module_ir: ModuleIR, output_path: str):
        """
        Generate Klish XML file from ModuleIR.
        
        Args:
            module_ir: ModuleIR object to render
            output_path: Path to write the generated XML file
        """
        template = self.env.get_template('klish_module.xml.j2')
        
        xml_content = template.render(module=module_ir)
        
        with open(output_path, 'w') as f:
            f.write(xml_content)
        
        print(f"Generated Klish XML: {output_path}")
