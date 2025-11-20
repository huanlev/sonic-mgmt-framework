"""
IR Builder: Converts YangParser output to Intermediate Representation.

This module builds the IR (Intermediate Representation) from the parsed YANG model,
creating ViewIR and CommandIR objects that represent the CLI structure.
"""

from typing import Dict, List, Any
from .models import ModuleIR, ViewIR, CommandIR, ParamIR, ActionIR
from .utils import yang_name_to_cli_name, yang_type_to_ptype, sanitize_help_text


class IRBuilder:
    """Builds Intermediate Representation from YangParser output."""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.module_ir = ModuleIR(name=module_name)
        
    def build(self, parsed_yang: Dict[str, Any]) -> ModuleIR:
        """
        Build IR from parsed YANG model.
        
        Args:
            parsed_yang: Dictionary output from YangParser.parse_yang_model()
        
        Returns:
            ModuleIR object representing the CLI structure
        """
        configure_view = ViewIR(name='configure-view')
        enable_view = ViewIR(name='enable-view')
        
        for table in parsed_yang.get('tables', []):
            table_name = table.get('name')
            
            if 'static-objects' in table:
                for obj in table['static-objects']:
                    self._process_static_object(
                        table_name, obj, configure_view, enable_view
                    )
            
            if 'dynamic-objects' in table:
                for obj in table['dynamic-objects']:
                    self._process_dynamic_object(
                        table_name, obj, configure_view, enable_view
                    )
        
        self.module_ir.add_view(configure_view)
        self.module_ir.add_view(enable_view)
        
        return self.module_ir
    
    def _process_static_object(self, table_name: str, obj: Dict[str, Any],
                               configure_view: ViewIR, enable_view: ViewIR):
        """
        Process a static object (container) and generate CLI commands.
        
        For each leaf in the container, generate a set command in configure-view.
        """
        obj_name = obj.get('name')
        obj_cli_name = yang_name_to_cli_name(obj_name)
        
        for attr in obj.get('attrs', []):
            attr_name = attr.get('name')
            attr_cli_name = yang_name_to_cli_name(attr_name)
            attr_desc = sanitize_help_text(attr.get('description', f'Set {attr_name}'))
            
            ptype = self._get_ptype_for_attr(table_name, obj_name, attr_name)
            
            if table_name == 'FLEX_COUNTER_TABLE':
                cmd_name = f'flex-counter {obj_cli_name} {attr_cli_name}'
            else:
                cmd_name = f'{yang_name_to_cli_name(table_name)} {obj_cli_name} {attr_cli_name}'
            
            param = self._create_param_for_attr(attr_name, attr_cli_name, attr_desc, ptype)
            
            action = self._create_set_action(table_name, obj_name, attr_name)
            
            command = CommandIR(
                name=cmd_name,
                help=attr_desc,
                params=[param] if param else [],
                action=action
            )
            
            configure_view.commands.append(command)
    
    def _process_dynamic_object(self, table_name: str, obj: Dict[str, Any],
                                configure_view: ViewIR, enable_view: ViewIR):
        """
        Process a dynamic object (list) and generate CLI commands.
        
        For lists, generate add/delete commands in configure-view.
        """
        obj_name = obj.get('name')
        obj_cli_name = yang_name_to_cli_name(obj_name)
        
        keys = obj.get('keys', [])
        if not keys:
            return
        
        attrs = obj.get('attrs', [])
        
        if table_name == 'FLOW_COUNTER_ROUTE_PATTERN':
            cmd_name = f'{yang_name_to_cli_name(obj_name)} add'
        else:
            cmd_name = f'{yang_name_to_cli_name(table_name)} {obj_cli_name} add'
        
        params = []
        
        for key in keys:
            key_name = key.get('name')
            key_cli_name = yang_name_to_cli_name(key_name)
            key_desc = sanitize_help_text(key.get('description', f'{key_name}'))
            ptype = self._get_ptype_for_key(table_name, obj_name, key_name)
            
            param = ParamIR(
                name=key_cli_name,
                help=key_desc,
                ptype=ptype,
                optional=False
            )
            params.append(param)
        
        for attr in attrs:
            attr_name = attr.get('name')
            attr_cli_name = yang_name_to_cli_name(attr_name)
            attr_desc = sanitize_help_text(attr.get('description', f'{attr_name}'))
            ptype = self._get_ptype_for_attr(table_name, obj_name, attr_name)
            
            param = ParamIR(
                name=attr_cli_name,
                help=attr_desc,
                ptype=ptype,
                optional=True
            )
            params.append(param)
        
        add_action = self._create_add_action(table_name, obj_name, keys, attrs)
        
        add_command = CommandIR(
            name=cmd_name,
            help=f'Add {obj_cli_name} entry',
            params=params,
            action=add_action
        )
        configure_view.commands.append(add_command)
        
        if table_name == 'FLOW_COUNTER_ROUTE_PATTERN':
            del_cmd_name = f'no {yang_name_to_cli_name(obj_name)}'
        else:
            del_cmd_name = f'no {yang_name_to_cli_name(table_name)} {obj_cli_name}'
        
        del_params = []
        for key in keys:
            key_name = key.get('name')
            key_cli_name = yang_name_to_cli_name(key_name)
            key_desc = sanitize_help_text(key.get('description', f'{key_name}'))
            ptype = self._get_ptype_for_key(table_name, obj_name, key_name)
            
            param = ParamIR(
                name=key_cli_name,
                help=key_desc,
                ptype=ptype,
                optional=False
            )
            del_params.append(param)
        
        del_action = self._create_delete_action(table_name, obj_name, keys)
        
        del_command = CommandIR(
            name=del_cmd_name,
            help=f'Delete {obj_cli_name} entry',
            params=del_params,
            action=del_action
        )
        configure_view.commands.append(del_command)
    
    def _get_ptype_for_attr(self, table_name: str, obj_name: str, attr_name: str) -> str:
        """Get Klish ptype for an attribute based on known types."""
        if attr_name == 'FLEX_COUNTER_STATUS':
            return 'SUBCOMMAND'  # enable/disable enum
        elif attr_name == 'POLL_INTERVAL':
            return 'RANGE_100_4294967295'
        elif attr_name == 'max_match_count':
            return 'RANGE_1_50'
        elif attr_name == 'FLEX_COUNTER_DELAY_STATUS':
            return 'SUBCOMMAND'  # true/false
        elif attr_name == 'BULK_CHUNK_SIZE':
            return 'RANGE_1_4294967295'
        elif attr_name == 'BULK_CHUNK_SIZE_PER_PREFIX':
            return 'STRING_63'
        else:
            return 'STRING'
    
    def _get_ptype_for_key(self, table_name: str, obj_name: str, key_name: str) -> str:
        """Get Klish ptype for a key based on known types."""
        if key_name == 'ip_prefix':
            return 'IP_ADDR_MASK'
        elif key_name == 'vrf_name':
            return 'STRING_63'
        else:
            return 'STRING'
    
    def _create_param_for_attr(self, attr_name: str, attr_cli_name: str, 
                               attr_desc: str, ptype: str) -> ParamIR:
        """Create a parameter for an attribute."""
        if ptype == 'SUBCOMMAND' and attr_name == 'FLEX_COUNTER_STATUS':
            return ParamIR(
                name=attr_cli_name,
                help=attr_desc,
                ptype='SUBCOMMAND',
                optional=False,
                mode='switch'
            )
        else:
            return ParamIR(
                name=attr_cli_name,
                help=attr_desc,
                ptype=ptype,
                optional=False
            )
    
    def _create_set_action(self, table_name: str, obj_name: str, attr_name: str) -> ActionIR:
        """Create action for setting a static object attribute."""
        module_cli_name = self.module_name.replace('-', '_')
        handler_name = f'sonic-cli-{self.module_name}.py'
        
        func_name = f'patch_{table_name.lower()}_{obj_name.lower()}_{attr_name.lower()}'
        
        param_ref = '${' + yang_name_to_cli_name(attr_name) + '}'
        
        script_line = f'python3 $SONIC_CLI_ROOT/{handler_name} {func_name} {param_ref}'
        
        return ActionIR(script_lines=[script_line])
    
    def _create_add_action(self, table_name: str, obj_name: str, 
                          keys: List[Dict], attrs: List[Dict]) -> ActionIR:
        """Create action for adding a dynamic object entry."""
        module_cli_name = self.module_name.replace('-', '_')
        handler_name = f'sonic-cli-{self.module_name}.py'
        
        func_name = f'add_{table_name.lower()}_{obj_name.lower()}'
        
        param_refs = []
        for key in keys:
            key_cli_name = yang_name_to_cli_name(key.get('name'))
            param_refs.append('${' + key_cli_name + '}')
        
        for attr in attrs:
            attr_cli_name = yang_name_to_cli_name(attr.get('name'))
            param_refs.append('${' + attr_cli_name + '}')
        
        script_line = f'python3 $SONIC_CLI_ROOT/{handler_name} {func_name} {" ".join(param_refs)}'
        
        return ActionIR(script_lines=[script_line])
    
    def _create_delete_action(self, table_name: str, obj_name: str, 
                             keys: List[Dict]) -> ActionIR:
        """Create action for deleting a dynamic object entry."""
        module_cli_name = self.module_name.replace('-', '_')
        handler_name = f'sonic-cli-{self.module_name}.py'
        
        func_name = f'delete_{table_name.lower()}_{obj_name.lower()}'
        
        param_refs = []
        for key in keys:
            key_cli_name = yang_name_to_cli_name(key.get('name'))
            param_refs.append('${' + key_cli_name + '}')
        
        script_line = f'python3 $SONIC_CLI_ROOT/{handler_name} {func_name} {" ".join(param_refs)}'
        
        return ActionIR(script_lines=[script_line])
