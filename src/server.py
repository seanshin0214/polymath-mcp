"""
Polymath MCP Server - Main Entry Point

융합적 사고와 소크라테스적 대화를 지원하는 MCP 서버
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.tools.exploration import register_exploration_tools
from src.tools.fusion import register_fusion_tools
from src.tools.socratic import register_socratic_tools
from src.engines.fusion_engine import FusionEngine
from src.engines.socratic_engine import SocraticEngine
from src.engines.rag_pipeline import RAGPipeline
from src.config.settings import Settings

# Initialize server
server = Server("polymath-mcp")

# Global instances (initialized on startup)
settings: Settings = None
fusion_engine: FusionEngine = None
socratic_engine: SocraticEngine = None
rag_pipeline: RAGPipeline = None


async def initialize():
    """Initialize all engines and connections"""
    global settings, fusion_engine, socratic_engine, rag_pipeline

    settings = Settings()

    # Initialize RAG Pipeline
    rag_pipeline = RAGPipeline(settings)
    await rag_pipeline.initialize()

    # Initialize Fusion Engine
    fusion_engine = FusionEngine(rag_pipeline)

    # Initialize Socratic Engine
    socratic_engine = SocraticEngine(rag_pipeline, fusion_engine)

    print("Polymath MCP initialized successfully!")


# Register all tools
register_exploration_tools(server)
register_fusion_tools(server)
register_socratic_tools(server)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools"""
    return [
        # Exploration Tools
        Tool(
            name="search_concepts",
            description="Search concepts across domains using hybrid search (semantic + graph)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "domains": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by domains (optional)"
                    },
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="find_bridges",
            description="Find connections between a concept and other domains",
            inputSchema={
                "type": "object",
                "properties": {
                    "concept_id": {"type": "string"},
                    "target_domains": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["concept_id"]
            }
        ),
        Tool(
            name="suggest_fusion",
            description="Analyze fusion possibility between two concepts",
            inputSchema={
                "type": "object",
                "properties": {
                    "concept_a": {"type": "string"},
                    "concept_b": {"type": "string"}
                },
                "required": ["concept_a", "concept_b"]
            }
        ),
        Tool(
            name="socratic_dialogue",
            description="Start or continue a Socratic dialogue exploration",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic to explore"},
                    "user_position": {"type": "string", "description": "User's current position/idea"},
                    "depth": {
                        "type": "string",
                        "enum": ["shallow", "medium", "deep"],
                        "default": "medium"
                    },
                    "focus": {
                        "type": "string",
                        "enum": ["explore", "challenge", "synthesize"],
                        "default": "explore"
                    }
                },
                "required": ["topic"]
            }
        ),
        Tool(
            name="challenge_premise",
            description="Challenge hidden assumptions in a statement",
            inputSchema={
                "type": "object",
                "properties": {
                    "statement": {"type": "string"},
                    "perspective": {"type": "string", "description": "Perspective to challenge from"}
                },
                "required": ["statement"]
            }
        ),
        Tool(
            name="get_fusion_patterns",
            description="Get information about the 7 fusion thinking patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern_name": {"type": "string", "description": "Specific pattern name (optional)"}
                }
            }
        ),
        Tool(
            name="get_domains",
            description="List all available knowledge domains",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="set_dialogue_mode",
            description="Set the dialogue mode (socratic, direct, or hybrid)",
            inputSchema={
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["socratic", "direct", "hybrid"],
                        "description": "socratic: always questions, direct: direct answers, hybrid: context-aware"
                    }
                },
                "required": ["mode"]
            }
        )
    ]


async def main():
    """Main entry point"""
    await initialize()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
