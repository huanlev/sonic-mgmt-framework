"""
Intermediate Representation (IR) data models for Klish CLI generation.

These dataclasses represent the abstract structure of CLI commands
before they are rendered into Klish XML format.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ParamIR:
    """Represents a CLI command parameter."""
    name: str
    help: str
    ptype: str
    optional: bool = False
    mode: Optional[str] = None  # 'switch', 'subcommand', etc.
    value: Optional[str] = None  # For enum values


@dataclass
class ActionIR:
    """Represents the action to execute when a command is invoked."""
    script_lines: List[str] = field(default_factory=list)
    
    def to_shell_script(self) -> str:
        """Convert action lines to shell script with &#xA; separators."""
        return '&#xA;'.join(self.script_lines) + '&#xA;'


@dataclass
class CommandIR:
    """Represents a CLI command."""
    name: str
    help: str
    params: List[ParamIR] = field(default_factory=list)
    action: Optional[ActionIR] = None
    view: Optional[str] = None  # For commands that change view
    viewid: Optional[str] = None


@dataclass
class ViewIR:
    """Represents a CLI view (mode)."""
    name: str
    commands: List[CommandIR] = field(default_factory=list)
    prompt: Optional[str] = None
    depth: Optional[str] = None


@dataclass
class ModuleIR:
    """Represents a complete CLI module."""
    name: str
    views: List[ViewIR] = field(default_factory=list)
    
    def get_view(self, view_name: str) -> Optional[ViewIR]:
        """Get a view by name."""
        for view in self.views:
            if view.name == view_name:
                return view
        return None
    
    def add_view(self, view: ViewIR):
        """Add a view to the module."""
        self.views.append(view)
