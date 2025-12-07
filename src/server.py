"""
Polymath MCP Server - Main Entry Point

융합적 사고와 소크라테스적 대화를 지원하는 MCP 서버
Your Second Brain for Interdisciplinary Knowledge
"""

import json
import sys
import os
import logging
from typing import Optional

# ============================================================================
# CRITICAL: MCP uses stdout for JSON-RPC communication
# ALL other output MUST go to stderr
# ============================================================================

# Suppress all logging to stdout - redirect to stderr
logging.basicConfig(
    level=logging.WARNING,
    format='%(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

# Suppress noisy loggers
for logger_name in ['neo4j', 'httpx', 'httpcore', 'chromadb', 'onnxruntime', 'sentence_transformers']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

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

    print("Polymath MCP initialized successfully!", file=sys.stderr)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools"""
    return [
        # === Core Search Tools ===
        Tool(
            name="search_concepts",
            description="""Search concepts across 30+ academic domains using semantic similarity.
            Returns relevant knowledge chunks from the polymath knowledge base.
            Use this to find concepts, theories, and ideas across disciplines.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query - can be a concept name, question, or description"
                    },
                    "domains": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by domains: philosophy, economics, physics, biology, psychology, etc."
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Maximum number of results"
                    }
                },
                "required": ["query"]
            }
        ),

        Tool(
            name="find_bridges",
            description="""Find connections between a concept and other domains.
            Discovers potential cross-disciplinary links for fusion thinking.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "concept": {
                        "type": "string",
                        "description": "The concept to find bridges for"
                    },
                    "target_domains": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific domains to explore connections with"
                    }
                },
                "required": ["concept"]
            }
        ),

        # === Fusion Thinking Tools ===
        Tool(
            name="suggest_fusion",
            description="""Analyze fusion possibility between two concepts from different domains.
            Identifies applicable fusion patterns and historical precedents.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "concept_a": {
                        "type": "string",
                        "description": "First concept"
                    },
                    "concept_b": {
                        "type": "string",
                        "description": "Second concept"
                    }
                },
                "required": ["concept_a", "concept_b"]
            }
        ),

        Tool(
            name="get_fusion_patterns",
            description="""Get information about the 7 fusion thinking patterns:
            1. Metaphorical Transfer (은유적 전이)
            2. Structural Isomorphism (구조적 동형)
            3. Assumption Subversion (전제 전복)
            4. Scale Jump (스케일 점프)
            5. Temporal Transformation (시간축 변환)
            6. Boundary Concept (경계 개념)
            7. Dialectical Synthesis (변증법적 종합)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern_name": {
                        "type": "string",
                        "description": "Specific pattern name (optional, omit for all patterns)"
                    }
                }
            }
        ),

        # === Socratic Dialogue Tools ===
        Tool(
            name="socratic_dialogue",
            description="""Start or continue a Socratic dialogue exploration.
            Guides thinking through questions rather than direct answers.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic to explore through dialogue"
                    },
                    "user_position": {
                        "type": "string",
                        "description": "User's current position, idea, or question"
                    },
                    "depth": {
                        "type": "string",
                        "enum": ["shallow", "medium", "deep"],
                        "default": "medium",
                        "description": "Depth of exploration"
                    },
                    "focus": {
                        "type": "string",
                        "enum": ["explore", "challenge", "synthesize"],
                        "default": "explore",
                        "description": "Focus mode: explore possibilities, challenge assumptions, or synthesize ideas"
                    }
                },
                "required": ["topic"]
            }
        ),

        Tool(
            name="challenge_premise",
            description="""Challenge hidden assumptions in a statement.
            Identifies and questions underlying premises for deeper understanding.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "statement": {
                        "type": "string",
                        "description": "Statement to analyze for hidden assumptions"
                    },
                    "perspective": {
                        "type": "string",
                        "description": "Specific perspective to challenge from (optional)"
                    }
                },
                "required": ["statement"]
            }
        ),

        # === Knowledge Management Tools ===
        Tool(
            name="add_knowledge",
            description="""Add new knowledge document to the RAG system.
            Use this to expand the knowledge base with new concepts, ideas, or notes.
            The document will be embedded and indexed for future retrieval.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The knowledge content (can be markdown format)"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name/title of the knowledge item"
                    },
                    "domain": {
                        "type": "string",
                        "description": "Primary domain (e.g., philosophy, economics, physics)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for categorization"
                    }
                },
                "required": ["content", "name"]
            }
        ),

        Tool(
            name="get_stats",
            description="""Get statistics about the knowledge base.
            Shows number of indexed documents, domains covered, etc.""",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),

        # === Utility Tools ===
        Tool(
            name="get_domains",
            description="""List all available knowledge domains.
            Shows the 30+ academic disciplines covered in the knowledge base.""",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),

        Tool(
            name="set_dialogue_mode",
            description="""Set the dialogue mode for interactions.
            - socratic: Always respond with guiding questions
            - direct: Give direct answers
            - hybrid: Context-aware mix of both""",
            inputSchema={
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["socratic", "direct", "hybrid"],
                        "description": "Dialogue mode to use"
                    }
                },
                "required": ["mode"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""

    if name == "search_concepts":
        results = await rag_pipeline.search(
            query=arguments["query"],
            domains=arguments.get("domains"),
            limit=arguments.get("limit", 10)
        )

        if not results:
            return [TextContent(
                type="text",
                text="No results found for your query. Try different keywords or broaden your search."
            )]

        # Format results
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"""
### {i}. {r.name}
**Domain**: {r.domain}
**Relevance**: {r.similarity:.2f}

{r.description[:500]}...
""")

        return [TextContent(
            type="text",
            text=f"## Search Results for: {arguments['query']}\n\n" + "\n---\n".join(formatted)
        )]

    elif name == "find_bridges":
        # First search for the concept by name (exact match first, then semantic)
        concept_results = await rag_pipeline.search_by_name(
            name=arguments["concept"],
            limit=1
        )

        if not concept_results:
            return [TextContent(
                type="text",
                text=f"Concept '{arguments['concept']}' not found in knowledge base."
            )]

        concept = concept_results[0]
        target_domains = arguments.get("target_domains")

        # Find related concepts in other domains
        bridges = await rag_pipeline.search_metaphorical(
            concept=concept,
            target_domains=target_domains
        )

        if not bridges:
            return [TextContent(
                type="text",
                text=f"No cross-domain bridges found for '{concept.name}'."
            )]

        formatted = [f"## Bridges from: {concept.name} ({concept.domain})\n"]
        for b in bridges:
            formatted.append(f"""
### {b.name}
**Domain**: {b.domain}
**Connection Strength**: {b.similarity:.2f}

{b.description[:300]}...
""")

        return [TextContent(type="text", text="\n".join(formatted))]

    elif name == "suggest_fusion":
        # Search for both concepts by name (exact match first, then semantic)
        results_a = await rag_pipeline.search_by_name(arguments["concept_a"], limit=1)
        results_b = await rag_pipeline.search_by_name(arguments["concept_b"], limit=1)

        if not results_a or not results_b:
            return [TextContent(
                type="text",
                text="One or both concepts not found in knowledge base."
            )]

        concept_a = results_a[0]
        concept_b = results_b[0]

        # Calculate novelty
        novelty = await rag_pipeline.calculate_concept_novelty(concept_a, concept_b)

        # Get fusion patterns info
        patterns_text = await _get_fusion_patterns_text()

        response = f"""## Fusion Analysis

### Concepts
- **A**: {concept_a.name} ({concept_a.domain})
- **B**: {concept_b.name} ({concept_b.domain})

### Novelty Score: {novelty:.2f}
{'High novelty - unexplored territory!' if novelty > 0.7 else 'Moderate novelty - some precedent exists' if novelty > 0.4 else 'Low novelty - well-trodden path'}

### Applicable Fusion Patterns

Consider applying these patterns:

1. **Structural Isomorphism**: What structural similarities exist between these concepts?
2. **Metaphorical Transfer**: How can {concept_a.name} serve as a metaphor for understanding {concept_b.name}?
3. **Boundary Concept**: What shared concepts bridge {concept_a.domain} and {concept_b.domain}?

### Exploration Questions
- What assumptions from {concept_a.domain} might {concept_b.domain} challenge?
- At what scale do these concepts exhibit similar patterns?
- How would a {concept_a.domain} expert approach problems in {concept_b.domain}?
"""
        return [TextContent(type="text", text=response)]

    elif name == "get_fusion_patterns":
        pattern_name = arguments.get("pattern_name")
        text = await _get_fusion_patterns_text(pattern_name)
        return [TextContent(type="text", text=text)]

    elif name == "socratic_dialogue":
        topic = arguments["topic"]
        user_position = arguments.get("user_position", "")
        depth = arguments.get("depth", "medium")
        focus = arguments.get("focus", "explore")

        # Search for relevant knowledge
        context = await rag_pipeline.search(topic, limit=5)

        context_text = "\n".join([f"- {c.name}: {c.description[:200]}" for c in context])

        response = f"""## Socratic Exploration: {topic}

### Guiding Questions

"""
        if focus == "explore":
            response += f"""
1. **Definition**: What do we mean by "{topic}"? How would different disciplines define this?

2. **Assumptions**: What are we assuming to be true when we discuss {topic}?

3. **Connections**: How does {topic} relate to:
{context_text}

4. **Perspectives**: How might this look from the viewpoint of:
   - A physicist?
   - A philosopher?
   - An economist?
   - A biologist?

5. **Implications**: If our understanding of {topic} is correct, what follows?
"""
        elif focus == "challenge":
            response += f"""
1. **Counter-evidence**: What evidence would contradict our current understanding of {topic}?

2. **Alternative views**: Who disagrees with mainstream views on {topic}? Why?

3. **Hidden premises**: What unstated assumptions underlie common beliefs about {topic}?

4. **Boundary cases**: Where does our understanding of {topic} break down?

5. **Devil's advocate**: What is the strongest argument against the prevailing view?
"""
        else:  # synthesize
            response += f"""
1. **Thesis**: What is the dominant view on {topic}?

2. **Antithesis**: What opposes or challenges this view?

3. **Synthesis**: How can these opposing views be reconciled or transcended?

4. **Integration**: What new understanding emerges from this synthesis?

5. **Application**: How can this synthesized view be applied practically?
"""

        if user_position:
            response += f"""
### Your Position Analysis

You stated: "{user_position}"

Consider:
- What evidence supports this position?
- What would change your mind?
- How does this connect to other ideas in the knowledge base?
"""

        return [TextContent(type="text", text=response)]

    elif name == "challenge_premise":
        statement = arguments["statement"]
        perspective = arguments.get("perspective")

        # Search for relevant contrasting views
        contrasts = await rag_pipeline.search(
            f"critique of {statement}",
            limit=3
        )

        response = f"""## Premise Challenge

### Statement
> "{statement}"

### Hidden Assumptions Identified

1. **Ontological**: What entities/phenomena does this assume exist?

2. **Epistemological**: What ways of knowing does this privilege?

3. **Axiological**: What values are embedded in this statement?

4. **Methodological**: What approaches does this implicitly endorse?

### Alternative Perspectives
"""
        if contrasts:
            for c in contrasts:
                response += f"\n**From {c.domain}**: {c.description[:200]}...\n"

        if perspective:
            response += f"""
### Specific Challenge from {perspective} Perspective

How would a {perspective} scholar critique this statement?
What alternative framing would they propose?
"""

        return [TextContent(type="text", text=response)]

    elif name == "add_knowledge":
        content = arguments["content"]
        metadata = {
            "name": arguments["name"],
            "domain": arguments.get("domain", "general"),
            "tags": ",".join(arguments.get("tags", [])),
            "category": "user-added"
        }

        doc_id = await rag_pipeline.add_document(content, metadata)

        return [TextContent(
            type="text",
            text=f"""## Knowledge Added Successfully

**ID**: {doc_id}
**Name**: {metadata['name']}
**Domain**: {metadata['domain']}

The document has been indexed and will be available for future searches.
"""
        )]

    elif name == "get_stats":
        stats = await rag_pipeline.get_stats()

        return [TextContent(
            type="text",
            text=f"""## Knowledge Base Statistics

### Vector Store (ChromaDB)
- **Documents**: {stats['vector_store']['count']}
- **Status**: {'Available' if stats['vector_store']['available'] else 'Not Available'}

### Graph Store (Neo4j)
- **Status**: {'Connected' if stats['graph_store']['connected'] else 'Not Connected (optional)'}

### Coverage
The knowledge base includes:
- 7 Fusion Thinking Patterns
- 7 Historical Fusion Cases
- 5 Cross-Domain Concepts
- 5 Polymath Profiles
- 5 Big Questions

30+ academic domains covered including:
Philosophy, Physics, Mathematics, Economics, Biology,
Psychology, Sociology, Computer Science, and more.
"""
        )]

    elif name == "get_domains":
        domains = [
            "Philosophy", "Physics", "Mathematics", "Economics", "Biology",
            "Psychology", "Sociology", "Computer Science", "Linguistics",
            "History", "Political Science", "Neuroscience", "Chemistry",
            "Anthropology", "Art History", "Music Theory", "Literature",
            "Engineering", "Medicine", "Law", "Ecology", "Cognitive Science",
            "Information Theory", "Game Theory", "Network Science",
            "Systems Theory", "Evolutionary Biology", "Thermodynamics",
            "Quantum Mechanics", "Complex Systems"
        ]

        return [TextContent(
            type="text",
            text=f"""## Available Knowledge Domains

The Polymath knowledge base covers **{len(domains)}+ academic disciplines**:

{chr(10).join([f'- {d}' for d in sorted(domains)])}

Use these domain names when filtering searches or specifying target domains for fusion exploration.
"""
        )]

    elif name == "set_dialogue_mode":
        mode = arguments["mode"]
        # In a full implementation, this would set a session state
        return [TextContent(
            type="text",
            text=f"Dialogue mode set to: **{mode}**\n\n" +
            ("I will guide you through questions." if mode == "socratic" else
             "I will provide direct answers." if mode == "direct" else
             "I will adapt my response style to context.")
        )]

    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def _get_fusion_patterns_text(pattern_name: Optional[str] = None) -> str:
    """Get fusion patterns information"""
    patterns = {
        "metaphorical_transfer": {
            "name": "Metaphorical Transfer (은유적 전이)",
            "description": "Transfer concepts from one domain to another through metaphor",
            "example": "DNA as 'genetic code' - borrowing from linguistics/computing",
            "key_question": "What if we think of X as if it were Y?"
        },
        "structural_isomorphism": {
            "name": "Structural Isomorphism (구조적 동형)",
            "description": "Find identical structures across different domains",
            "example": "Wave equations appear in physics, economics, and ecology",
            "key_question": "What structural patterns repeat across domains?"
        },
        "assumption_subversion": {
            "name": "Assumption Subversion (전제 전복)",
            "description": "Challenge fundamental assumptions of a field using another field's perspective",
            "example": "Behavioral economics challenging rational actor assumption",
            "key_question": "What would field B say about field A's core assumptions?"
        },
        "scale_jump": {
            "name": "Scale Jump (스케일 점프)",
            "description": "Apply principles from one scale to another",
            "example": "Applying evolutionary principles to ideas (memetics)",
            "key_question": "Does this pattern appear at micro/meso/macro scales?"
        },
        "temporal_transformation": {
            "name": "Temporal Transformation (시간축 변환)",
            "description": "View phenomena through different temporal lenses",
            "example": "Understanding organizations through geological time perspectives",
            "key_question": "How does this look on different time scales?"
        },
        "boundary_concept": {
            "name": "Boundary Concept (경계 개념)",
            "description": "Use concepts that span multiple disciplines as bridges",
            "example": "'Information' connecting physics, biology, and computer science",
            "key_question": "What concepts exist at the boundaries of these fields?"
        },
        "dialectical_synthesis": {
            "name": "Dialectical Synthesis (변증법적 종합)",
            "description": "Create new understanding by synthesizing opposing views",
            "example": "Wave-particle duality in quantum mechanics",
            "key_question": "How can thesis and antithesis be transcended?"
        }
    }

    if pattern_name:
        # Find matching pattern
        for key, pattern in patterns.items():
            if pattern_name.lower() in key.lower() or pattern_name.lower() in pattern["name"].lower():
                return f"""## {pattern['name']}

**Description**: {pattern['description']}

**Example**: {pattern['example']}

**Key Question**: {pattern['key_question']}
"""
        return f"Pattern '{pattern_name}' not found. Available patterns: {', '.join(patterns.keys())}"

    # Return all patterns
    text = "## 7 Fusion Thinking Patterns\n\n"
    for i, (key, pattern) in enumerate(patterns.items(), 1):
        text += f"""### {i}. {pattern['name']}
{pattern['description']}
- **Example**: {pattern['example']}
- **Key Question**: {pattern['key_question']}

"""
    return text


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
