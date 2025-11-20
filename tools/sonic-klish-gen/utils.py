"""
Utility functions for sonic-klish-gen.
"""

import re
from typing import Dict, Any


def yang_name_to_cli_name(yang_name: str) -> str:
    """
    Convert YANG name to CLI command name.
    
    Examples:
        FLEX_COUNTER_STATUS -> flex-counter-status
        PORT -> port
        POLL_INTERVAL -> poll-interval
    """
    return yang_name.lower().replace('_', '-')


def yang_type_to_ptype(yang_type: str, yang_range: str = None, yang_enum: list = None) -> str:
    """
    Map YANG type to Klish ptype.
    
    Args:
        yang_type: YANG type (e.g., 'uint32', 'string', 'enumeration', 'inet:ip-prefix')
        yang_range: Optional range constraint (e.g., '100..4294967295')
        yang_enum: Optional list of enum values
    
    Returns:
        Klish ptype (e.g., 'UINT', 'STRING_63', 'IP_ADDR_MASK')
    """
    if 'inet:ip-prefix' in yang_type or 'ip-prefix' in yang_type:
        return 'IP_ADDR_MASK'
    
    if 'inet:ipv4-prefix' in yang_type or 'ipv4-prefix' in yang_type:
        return 'IPV4_ADDR_MASK'
    
    if 'inet:ipv6-prefix' in yang_type or 'ipv6-prefix' in yang_type:
        return 'IPV6_ADDR_MASK'
    
    if yang_type == 'uint32':
        if yang_range:
            match = re.match(r'(\d+)\.\.(\d+)', yang_range)
            if match:
                min_val, max_val = match.groups()
                return f'RANGE_{min_val}_{max_val}'
        return 'UINT'
    
    if yang_type in ['uint16', 'uint8']:
        return 'UINT'
    
    if yang_type == 'string':
        return 'STRING_63'
    
    if yang_type == 'enumeration' or yang_enum:
        return 'SUBCOMMAND'
    
    if yang_type in ['boolean', 'stypes:boolean_type']:
        return 'SUBCOMMAND'
    
    return 'STRING'


def get_yang_type_info(attr: Dict[str, Any]) -> tuple:
    """
    Extract type information from a YANG attribute.
    
    Returns:
        (type_name, range_constraint, enum_values)
    """
    return ('string', None, None)


def sanitize_help_text(text: str) -> str:
    """
    Sanitize help text for XML output.
    
    Args:
        text: Raw help text
    
    Returns:
        Sanitized help text safe for XML
    """
    if not text:
        return ''
    
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&apos;')
    
    text = ' '.join(text.split())
    
    return text


def generate_rest_path(module_name: str, table_name: str, object_name: str = None, 
                       attr_name: str = None) -> str:
    """
    Generate REST API path for a YANG element.
    
    This is a simplified version - actual REST paths would need to be
    determined from the REST API schema.
    """
    path_parts = [module_name.replace('-', '_')]
    
    if table_name:
        path_parts.append(table_name)
    
    if object_name:
        path_parts.append(object_name)
    
    if attr_name:
        path_parts.append(attr_name)
    
    return '_'.join(path_parts)
