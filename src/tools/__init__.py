"""
Polymath MCP Tools
"""

from src.tools.exploration import register_exploration_tools
from src.tools.fusion import register_fusion_tools
from src.tools.socratic import register_socratic_tools

__all__ = [
    "register_exploration_tools",
    "register_fusion_tools",
    "register_socratic_tools",
]
