"""
Neo4j Graph Store - 관계 기반 검색

개념 간 관계, 계보, 융합 사례 등 그래프 데이터 담당
"""

import sys
import logging
from typing import List, Optional, Any, Dict

# Suppress Neo4j driver logs (they go to stdout by default)
logging.getLogger('neo4j').setLevel(logging.ERROR)
logging.getLogger('neo4j.io').setLevel(logging.ERROR)
logging.getLogger('neo4j.pool').setLevel(logging.ERROR)

from neo4j import AsyncGraphDatabase

from src.models.concept import Concept
from src.models.fusion import FusionCase


class Neo4jStore:
    """
    Neo4j 그래프 스토어

    - 개념 간 관계 저장 및 검색
    - 지적 계보 추적
    - 융합 사례 관리
    - 도메인 간 거리 계산
    """

    def __init__(self, settings):
        self.settings = settings
        self.driver = None

    async def initialize(self):
        """Neo4j 연결 초기화"""
        self.driver = AsyncGraphDatabase.driver(
            self.settings.neo4j_uri,
            auth=(self.settings.neo4j_user, self.settings.neo4j_password)
        )

        # Create indexes
        async with self.driver.session() as session:
            await session.run("""
                CREATE INDEX concept_id IF NOT EXISTS FOR (c:Concept) ON (c.id)
            """)
            await session.run("""
                CREATE INDEX concept_domain IF NOT EXISTS FOR (c:Concept) ON (c.domain)
            """)
            await session.run("""
                CREATE INDEX fusion_pattern IF NOT EXISTS FOR (f:FusionCase) ON (f.pattern)
            """)

        print("Neo4j initialized", file=sys.stderr)

    async def close(self):
        """연결 종료"""
        if self.driver:
            await self.driver.close()

    async def search(
        self,
        query: str,
        domains: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Any]:
        """
        그래프 기반 검색

        - 키워드 매칭
        - 관계 기반 확장
        """
        async with self.driver.session() as session:
            domain_filter = ""
            if domains:
                domain_filter = f"AND c.domain IN {domains}"

            result = await session.run(f"""
                MATCH (c:Concept)
                WHERE c.name CONTAINS $query OR c.description CONTAINS $query
                {domain_filter}
                OPTIONAL MATCH (c)-[r:RELATED_TO|DERIVED_FROM|INFLUENCES]->(related)
                RETURN c, count(related) as connections
                ORDER BY connections DESC
                LIMIT $limit
            """, query=query, limit=limit)

            concepts = []
            async for record in result:
                node = record["c"]
                concepts.append(Concept(
                    id=node["id"],
                    name=node["name"],
                    domain=node["domain"],
                    description=node.get("description", "")
                ))

            return concepts

    async def get_relationships(self, concept_id: str) -> Dict[str, List[str]]:
        """개념의 관계 조회"""
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (c:Concept {id: $concept_id})
                OPTIONAL MATCH (c)-[:RELATED_TO]->(related:Concept)
                OPTIONAL MATCH (c)-[:BRIDGES_TO]->(bridge:Domain)
                RETURN collect(DISTINCT related.name) as related,
                       collect(DISTINCT bridge.name) as bridges
            """, concept_id=concept_id)

            record = await result.single()
            if record:
                return {
                    "related": record["related"],
                    "bridges": record["bridges"]
                }
            return {"related": [], "bridges": []}

    async def get_ancestors(self, concept_id: str) -> List[Concept]:
        """선조 개념 조회"""
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (c:Concept {id: $concept_id})-[:DERIVED_FROM*1..5]->(ancestor:Concept)
                RETURN DISTINCT ancestor
            """, concept_id=concept_id)

            concepts = []
            async for record in result:
                node = record["ancestor"]
                concepts.append(Concept(
                    id=node["id"],
                    name=node["name"],
                    domain=node["domain"],
                    description=node.get("description", "")
                ))
            return concepts

    async def get_descendants(self, concept_id: str) -> List[Concept]:
        """후손 개념 조회"""
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (c:Concept {id: $concept_id})<-[:DERIVED_FROM*1..5]-(descendant:Concept)
                RETURN DISTINCT descendant
            """, concept_id=concept_id)

            concepts = []
            async for record in result:
                node = record["descendant"]
                concepts.append(Concept(
                    id=node["id"],
                    name=node["name"],
                    domain=node["domain"],
                    description=node.get("description", "")
                ))
            return concepts

    async def get_key_influences(self, concept_id: str) -> str:
        """핵심 영향 관계 텍스트"""
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (c:Concept {id: $concept_id})-[r:INFLUENCES|INFLUENCED_BY]-(other:Concept)
                RETURN type(r) as relation, other.name as name, r.description as description
                LIMIT 10
            """, concept_id=concept_id)

            influences = []
            async for record in result:
                direction = "→" if record["relation"] == "INFLUENCES" else "←"
                influences.append(f"- {direction} {record['name']}: {record['description']}")

            return "\n".join(influences) if influences else "핵심 영향 관계 없음"

    async def get_fusion_cases(
        self,
        pattern: Optional[str] = None,
        domains: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[FusionCase]:
        """융합 사례 검색"""
        async with self.driver.session() as session:
            pattern_filter = "AND f.pattern = $pattern" if pattern else ""
            domain_filter = ""
            if domains:
                domain_filter = """
                    AND any(d IN $domains WHERE d IN f.source_domains)
                """

            result = await session.run(f"""
                MATCH (f:FusionCase)
                WHERE true {pattern_filter} {domain_filter}
                RETURN f
                LIMIT $limit
            """, pattern=pattern, domains=domains, limit=limit)

            cases = []
            async for record in result:
                node = record["f"]
                cases.append(FusionCase(
                    id=node["id"],
                    name=node["name"],
                    creator=node.get("creator", "Unknown"),
                    pattern=node["pattern"],
                    source_domains=node["source_domains"],
                    source_concepts=node.get("source_concepts", []),
                    insight=node.get("insight", ""),
                    replicable_pattern=node.get("replicable_pattern", "")
                ))
            return cases

    async def find_structural_similar(
        self,
        concept_id: str,
        target_domains: Optional[List[str]] = None
    ) -> List[Any]:
        """구조적으로 유사한 개념 찾기"""
        async with self.driver.session() as session:
            domain_filter = ""
            if target_domains:
                domain_filter = f"AND target.domain IN {target_domains}"

            result = await session.run(f"""
                MATCH (c:Concept {{id: $concept_id}})-[:HAS_STRUCTURE]->(s:Structure)
                MATCH (target:Concept)-[:HAS_STRUCTURE]->(s)
                WHERE target.id <> c.id {domain_filter}
                RETURN target, s.pattern as shared_pattern
            """, concept_id=concept_id)

            results = []
            async for record in result:
                results.append({
                    "id": record["target"]["id"],
                    "name": record["target"]["name"],
                    "domain": record["target"]["domain"],
                    "shared_pattern": record["shared_pattern"],
                    "similarity": 0.8  # Placeholder
                })
            return results

    async def find_boundary_concepts(self, concept_id: str) -> List[Any]:
        """연결된 경계 개념 찾기"""
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (c:Concept {id: $concept_id})-[:USES]->(bc:BoundaryConcept)
                RETURN bc, bc.centrality as centrality
                ORDER BY centrality DESC
            """, concept_id=concept_id)

            concepts = []
            async for record in result:
                concepts.append({
                    "id": record["bc"]["id"],
                    "name": record["bc"]["name"],
                    "centrality": record["centrality"]
                })
            return concepts

    async def find_connected_through(
        self,
        boundary_concept_id: str,
        exclude_domain: str,
        target_domains: Optional[List[str]] = None
    ) -> List[Any]:
        """경계 개념을 통해 연결된 다른 개념 찾기"""
        async with self.driver.session() as session:
            domain_filter = ""
            if target_domains:
                domain_filter = f"AND c.domain IN {target_domains}"

            result = await session.run(f"""
                MATCH (bc:BoundaryConcept {{id: $bc_id}})<-[r:USES]-(c:Concept)
                WHERE c.domain <> $exclude_domain {domain_filter}
                RETURN c, r.strength as connection_strength
            """, bc_id=boundary_concept_id, exclude_domain=exclude_domain)

            concepts = []
            async for record in result:
                concepts.append({
                    "id": record["c"]["id"],
                    "name": record["c"]["name"],
                    "domain": record["c"]["domain"],
                    "connection_strength": record["connection_strength"] or 0.5
                })
            return concepts

    async def get_domain_distance(self, domain_a: str, domain_b: str) -> float:
        """두 도메인 간 거리 계산"""
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (a:Domain {name: $domain_a}), (b:Domain {name: $domain_b})
                MATCH path = shortestPath((a)-[:RELATED_TO*]-(b))
                RETURN length(path) as distance
            """, domain_a=domain_a, domain_b=domain_b)

            record = await result.single()
            if record:
                # Normalize distance to 0-1
                return min(1.0, record["distance"] / 10.0)
            return 0.8  # Default high distance if no path

    async def get_connection(
        self,
        concept_a_id: str,
        concept_b_id: str
    ) -> Optional[Dict]:
        """두 개념 간 직접 연결 조회"""
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (a:Concept {id: $a_id})-[r]-(b:Concept {id: $b_id})
                RETURN type(r) as type, r as relation
                LIMIT 1
            """, a_id=concept_a_id, b_id=concept_b_id)

            record = await result.single()
            if record:
                return {
                    "type": record["type"],
                    "relation": dict(record["relation"])
                }
            return None

    async def get_concept_structure(self, concept_id: str) -> Dict:
        """개념의 구조적 특성 조회"""
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (c:Concept {id: $concept_id})-[:HAS_STRUCTURE]->(s:Structure)
                RETURN s
            """, concept_id=concept_id)

            record = await result.single()
            if record:
                return dict(record["s"])
            return {}

    async def compare_structures(
        self,
        struct_a: Dict,
        struct_b: Dict
    ) -> Any:
        """두 구조 비교"""
        # Placeholder - would do actual structural comparison
        return {
            "similarity": 0.7,
            "description": "구조적 유사성이 발견됨",
            "key_aspect": "핵심 구조 요소"
        }

    async def search_fusion_cases_by_domains(
        self,
        domains: List[str]
    ) -> List[FusionCase]:
        """특정 도메인들이 포함된 융합 사례 검색"""
        return await self.get_fusion_cases(domains=domains)

    async def search_by_structure(
        self,
        structure: Any,
        exclude_domain: Optional[str] = None
    ) -> List[Concept]:
        """구조 기반 검색"""
        # Placeholder implementation
        return []
