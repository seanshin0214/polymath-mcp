"""
Polymath MCP Tools

소크라테스 학습 시스템 V2 포함
"""

from src.tools.exploration import register_exploration_tools
from src.tools.fusion import register_fusion_tools
from src.tools.socratic import register_socratic_tools

# Socratic V2 Tools
from src.tools.socratic_v2 import get_socratic_v2_tools, handle_socratic_v2_tool

__all__ = [
    "register_exploration_tools",
    "register_fusion_tools",
    "register_socratic_tools",
    # V2
    "get_socratic_v2_tools",
    "handle_socratic_v2_tool",
]
