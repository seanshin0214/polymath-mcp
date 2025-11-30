"""
Polymath MCP Data Layer
"""

from src.data.chroma_store import ChromaStore
from src.data.obsidian_sync import ObsidianSync

# Neo4j is optional
try:
    from src.data.neo4j_store import Neo4jStore
except ImportError:
    Neo4jStore = None  # type: ignore

__all__ = [
    "ChromaStore",
    "Neo4jStore",
    "ObsidianSync",
]
