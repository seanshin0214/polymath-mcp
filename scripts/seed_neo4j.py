"""
Neo4j Seeding Script for Polymath MCP

Syncs concept data from ChromaDB to Neo4j for graph-based queries.
Creates nodes for Concepts, Domains, FusionPatterns, and relationships.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase

# Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "polymath123")
KNOWLEDGE_PATH = Path(__file__).parent.parent / "knowledge"

# Domain definitions with relationships
DOMAINS = {
    "philosophy": {"related": ["psychology", "linguistics", "logic", "ethics"]},
    "physics": {"related": ["mathematics", "chemistry", "engineering", "cosmology"]},
    "mathematics": {"related": ["physics", "computer_science", "economics", "logic"]},
    "economics": {"related": ["psychology", "sociology", "mathematics", "political_science"]},
    "biology": {"related": ["chemistry", "medicine", "ecology", "neuroscience"]},
    "psychology": {"related": ["neuroscience", "sociology", "philosophy", "economics"]},
    "sociology": {"related": ["psychology", "economics", "anthropology", "political_science"]},
    "computer_science": {"related": ["mathematics", "engineering", "linguistics", "cognitive_science"]},
    "linguistics": {"related": ["philosophy", "psychology", "anthropology", "computer_science"]},
    "history": {"related": ["sociology", "political_science", "anthropology", "economics"]},
    "political_science": {"related": ["economics", "sociology", "history", "law"]},
    "neuroscience": {"related": ["biology", "psychology", "medicine", "cognitive_science"]},
    "chemistry": {"related": ["physics", "biology", "medicine", "materials_science"]},
    "anthropology": {"related": ["sociology", "linguistics", "archaeology", "biology"]},
    "cognitive_science": {"related": ["psychology", "neuroscience", "computer_science", "philosophy"]},
    "engineering": {"related": ["physics", "mathematics", "computer_science", "materials_science"]},
    "medicine": {"related": ["biology", "chemistry", "neuroscience", "psychology"]},
    "law": {"related": ["political_science", "philosophy", "economics", "sociology"]},
    "ecology": {"related": ["biology", "environmental_science", "economics", "geography"]},
    "art_history": {"related": ["history", "philosophy", "sociology", "anthropology"]},
    "music_theory": {"related": ["mathematics", "psychology", "physics", "cognitive_science"]},
    "literature": {"related": ["linguistics", "philosophy", "history", "psychology"]},
    "information_theory": {"related": ["mathematics", "computer_science", "physics", "linguistics"]},
    "game_theory": {"related": ["economics", "mathematics", "psychology", "political_science"]},
    "network_science": {"related": ["mathematics", "computer_science", "sociology", "physics"]},
    "systems_theory": {"related": ["engineering", "biology", "sociology", "cybernetics"]},
    "evolutionary_biology": {"related": ["biology", "genetics", "ecology", "anthropology"]},
    "thermodynamics": {"related": ["physics", "chemistry", "engineering", "biology"]},
    "quantum_mechanics": {"related": ["physics", "mathematics", "chemistry", "philosophy"]},
    "complex_systems": {"related": ["physics", "biology", "economics", "network_science"]},
}

# Fusion patterns
FUSION_PATTERNS = [
    {
        "id": "metaphorical_transfer",
        "name": "Metaphorical Transfer (은유적 전이)",
        "description": "Transfer concepts from one domain to another through metaphor",
        "example": "DNA as 'genetic code' - borrowing from linguistics/computing"
    },
    {
        "id": "structural_isomorphism",
        "name": "Structural Isomorphism (구조적 동형)",
        "description": "Find identical structures across different domains",
        "example": "Wave equations appear in physics, economics, and ecology"
    },
    {
        "id": "assumption_subversion",
        "name": "Assumption Subversion (전제 전복)",
        "description": "Challenge fundamental assumptions of a field using another field's perspective",
        "example": "Behavioral economics challenging rational actor assumption"
    },
    {
        "id": "scale_jump",
        "name": "Scale Jump (스케일 점프)",
        "description": "Apply principles from one scale to another",
        "example": "Applying evolutionary principles to ideas (memetics)"
    },
    {
        "id": "temporal_transformation",
        "name": "Temporal Transformation (시간축 변환)",
        "description": "View phenomena through different temporal lenses",
        "example": "Understanding organizations through geological time perspectives"
    },
    {
        "id": "boundary_concept",
        "name": "Boundary Concept (경계 개념)",
        "description": "Use concepts that span multiple disciplines as bridges",
        "example": "'Information' connecting physics, biology, and computer science"
    },
    {
        "id": "dialectical_synthesis",
        "name": "Dialectical Synthesis (변증법적 종합)",
        "description": "Create new understanding by synthesizing opposing views",
        "example": "Wave-particle duality in quantum mechanics"
    }
]

# Sample cross-domain concepts for relationships
CROSS_DOMAIN_CONCEPTS = [
    {"name": "Entropy", "domains": ["physics", "information_theory", "biology", "economics"]},
    {"name": "Feedback Loop", "domains": ["systems_theory", "biology", "economics", "psychology"]},
    {"name": "Network", "domains": ["network_science", "sociology", "neuroscience", "computer_science"]},
    {"name": "Evolution", "domains": ["biology", "economics", "linguistics", "technology"]},
    {"name": "Equilibrium", "domains": ["physics", "economics", "biology", "game_theory"]},
    {"name": "Information", "domains": ["information_theory", "physics", "biology", "philosophy"]},
    {"name": "Emergence", "domains": ["complex_systems", "philosophy", "biology", "sociology"]},
    {"name": "Optimization", "domains": ["mathematics", "economics", "biology", "engineering"]},
    {"name": "Self-Organization", "domains": ["complex_systems", "biology", "sociology", "physics"]},
    {"name": "Recursion", "domains": ["mathematics", "computer_science", "linguistics", "philosophy"]},
]


def create_constraints_and_indexes(tx):
    """Create constraints and indexes for better performance"""
    queries = [
        "CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT domain_name IF NOT EXISTS FOR (d:Domain) REQUIRE d.name IS UNIQUE",
        "CREATE CONSTRAINT pattern_id IF NOT EXISTS FOR (p:FusionPattern) REQUIRE p.id IS UNIQUE",
        "CREATE INDEX concept_name IF NOT EXISTS FOR (c:Concept) ON (c.name)",
        "CREATE INDEX concept_domain IF NOT EXISTS FOR (c:Concept) ON (c.domain)",
    ]
    for query in queries:
        try:
            tx.run(query)
        except Exception as e:
            print(f"  Warning: {e}")


def create_domains(tx):
    """Create Domain nodes"""
    for domain_name, props in DOMAINS.items():
        tx.run("""
            MERGE (d:Domain {name: $name})
            SET d.updated = datetime()
        """, name=domain_name)
    print(f"  Created {len(DOMAINS)} domain nodes")


def create_domain_relationships(tx):
    """Create RELATED_TO relationships between domains"""
    count = 0
    for domain_name, props in DOMAINS.items():
        for related in props.get("related", []):
            if related in DOMAINS:
                tx.run("""
                    MATCH (a:Domain {name: $domain_a})
                    MATCH (b:Domain {name: $domain_b})
                    MERGE (a)-[:RELATED_TO]->(b)
                """, domain_a=domain_name, domain_b=related)
                count += 1
    print(f"  Created {count} domain relationships")


def create_fusion_patterns(tx):
    """Create FusionPattern nodes"""
    for pattern in FUSION_PATTERNS:
        tx.run("""
            MERGE (p:FusionPattern {id: $id})
            SET p.name = $name,
                p.description = $description,
                p.example = $example,
                p.updated = datetime()
        """, **pattern)
    print(f"  Created {len(FUSION_PATTERNS)} fusion pattern nodes")


def create_boundary_concepts(tx):
    """Create BoundaryConcept nodes that span multiple domains"""
    for concept in CROSS_DOMAIN_CONCEPTS:
        # Create the boundary concept
        tx.run("""
            MERGE (bc:BoundaryConcept {name: $name})
            SET bc.centrality = $centrality,
                bc.updated = datetime()
        """, name=concept["name"], centrality=len(concept["domains"]) / 10.0)

        # Link to domains
        for domain in concept["domains"]:
            tx.run("""
                MATCH (bc:BoundaryConcept {name: $bc_name})
                MATCH (d:Domain {name: $domain})
                MERGE (bc)-[:BRIDGES]->(d)
            """, bc_name=concept["name"], domain=domain)

    print(f"  Created {len(CROSS_DOMAIN_CONCEPTS)} boundary concepts")


def sync_from_chroma(tx, chroma_path):
    """Sync concepts from ChromaDB to Neo4j"""
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    client = chromadb.PersistentClient(
        path=str(chroma_path),
        settings=ChromaSettings(anonymized_telemetry=False)
    )

    try:
        collection = client.get_collection("polymath_concepts")

        # Get all documents
        results = collection.get(include=["documents", "metadatas"])

        if not results["ids"]:
            print("  No concepts found in ChromaDB")
            return

        count = 0
        for i, doc_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i] if results["metadatas"] else {}
            document = results["documents"][i] if results["documents"] else ""

            name = metadata.get("name", doc_id)
            domain = metadata.get("domain", "general")

            # Create concept node
            tx.run("""
                MERGE (c:Concept {id: $id})
                SET c.name = $name,
                    c.domain = $domain,
                    c.description = $description,
                    c.category = $category,
                    c.updated = datetime()
            """,
                id=doc_id,
                name=name,
                domain=domain,
                description=document[:500] if document else "",
                category=metadata.get("category", "concept")
            )

            # Link to domain
            if domain and domain != "general":
                domain_key = domain.lower().replace(" ", "_")
                tx.run("""
                    MATCH (c:Concept {id: $concept_id})
                    MERGE (d:Domain {name: $domain})
                    MERGE (c)-[:BELONGS_TO]->(d)
                """, concept_id=doc_id, domain=domain_key)

            count += 1

        print(f"  Synced {count} concepts from ChromaDB")

    except Exception as e:
        print(f"  ChromaDB sync error: {e}")


def create_sample_relationships(tx):
    """Create sample INFLUENCES and DERIVED_FROM relationships"""
    # Sample intellectual lineage relationships
    lineages = [
        ("plato", "aristotle", "INFLUENCED"),
        ("aristotle", "aquinas", "INFLUENCED"),
        ("descartes", "spinoza", "INFLUENCED"),
        ("kant", "hegel", "INFLUENCED"),
        ("hegel", "marx", "INFLUENCED"),
        ("darwin", "evolutionary_biology", "FOUNDED"),
        ("shannon", "information_theory", "FOUNDED"),
        ("turing", "computer_science", "FOUNDED"),
    ]

    count = 0
    for source, target, rel_type in lineages:
        result = tx.run(f"""
            MATCH (a:Concept) WHERE toLower(a.name) CONTAINS $source
            MATCH (b:Concept) WHERE toLower(b.name) CONTAINS $target
            MERGE (a)-[:{rel_type}]->(b)
            RETURN count(*) as created
        """, source=source, target=target)
        record = result.single()
        if record:
            count += record["created"]

    print(f"  Created {count} intellectual lineage relationships")


def main():
    print("=" * 50)
    print("Neo4j Seeding for Polymath MCP")
    print("=" * 50)
    print(f"URI: {NEO4J_URI}")
    print(f"User: {NEO4J_USER}")
    print()

    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        # Verify connection
        driver.verify_connectivity()
        print("Connected to Neo4j!")
        print()

        with driver.session() as session:
            # Create constraints and indexes
            print("Creating constraints and indexes...")
            session.execute_write(create_constraints_and_indexes)

            # Create domain nodes
            print("Creating domain nodes...")
            session.execute_write(create_domains)

            # Create domain relationships
            print("Creating domain relationships...")
            session.execute_write(create_domain_relationships)

            # Create fusion patterns
            print("Creating fusion patterns...")
            session.execute_write(create_fusion_patterns)

            # Create boundary concepts
            print("Creating boundary concepts...")
            session.execute_write(create_boundary_concepts)

            # Sync from ChromaDB
            chroma_path = Path(__file__).parent.parent / "data" / "chroma"
            if chroma_path.exists():
                print("Syncing concepts from ChromaDB...")
                session.execute_write(lambda tx: sync_from_chroma(tx, chroma_path))

            # Create sample relationships
            print("Creating intellectual lineage relationships...")
            session.execute_write(create_sample_relationships)

        # Get statistics
        with driver.session() as session:
            result = session.run("""
                MATCH (c:Concept)
                WITH count(c) as concepts
                MATCH (d:Domain)
                WITH concepts, count(d) as domains
                MATCH (p:FusionPattern)
                WITH concepts, domains, count(p) as patterns
                MATCH (bc:BoundaryConcept)
                WITH concepts, domains, patterns, count(bc) as boundary
                MATCH ()-[r]->()
                RETURN concepts, domains, patterns, boundary, count(r) as relationships
            """)
            stats = result.single()

            print()
            print("=" * 50)
            print("Seeding Complete!")
            print("=" * 50)
            print(f"  Concepts: {stats['concepts']}")
            print(f"  Domains: {stats['domains']}")
            print(f"  Fusion Patterns: {stats['patterns']}")
            print(f"  Boundary Concepts: {stats['boundary']}")
            print(f"  Relationships: {stats['relationships']}")

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        driver.close()


if __name__ == "__main__":
    main()
