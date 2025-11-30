"""
RAG Pipeline - 하이브리드 검색 파이프라인

ChromaDB (벡터) + Neo4j (그래프) 통합 검색
"""

from typing import List, Optional, Any
from dataclasses import dataclass

from src.models.concept import Concept, ConceptLineage
from src.models.fusion import FusionCase


@dataclass
class SearchResult:
    concept: Concept
    similarity: float
    source: str  # "vector", "graph", "hybrid"


class RAGPipeline:
    """
    하이브리드 RAG 파이프라인

    - ChromaDB: 시맨틱 유사성 검색
    - Neo4j: 관계 기반 그래프 검색
    - 두 결과를 융합하여 최적의 결과 제공
    """

    def __init__(self, settings):
        self.settings = settings
        self.vector_store = None  # ChromaStore
        self.graph_store = None   # Neo4jStore
        self.initialized = False

    async def initialize(self):
        """데이터베이스 연결 초기화"""
        from src.data.chroma_store import ChromaStore
        from src.data.neo4j_store import Neo4jStore

        # Initialize vector store
        self.vector_store = ChromaStore(self.settings)
        await self.vector_store.initialize()

        # Initialize graph store
        self.graph_store = Neo4jStore(self.settings)
        await self.graph_store.initialize()

        self.initialized = True
        print("RAG Pipeline initialized")

    async def search(
        self,
        query: str,
        domains: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Concept]:
        """
        하이브리드 검색 (시맨틱 + 그래프)

        Args:
            query: 검색 쿼리
            domains: 도메인 필터 (선택)
            limit: 결과 수 제한

        Returns:
            검색된 개념 목록
        """
        # 1. Vector search (semantic similarity)
        vector_results = await self.vector_store.search(
            query=query,
            domains=domains,
            limit=limit * 2  # Get more for fusion
        )

        # 2. Graph search (relationship-based)
        graph_results = await self.graph_store.search(
            query=query,
            domains=domains,
            limit=limit * 2
        )

        # 3. Fuse results using RRF (Reciprocal Rank Fusion)
        fused = self._fuse_results(vector_results, graph_results)

        return fused[:limit]

    async def get_concept(self, concept_id: str) -> Optional[Concept]:
        """단일 개념 조회"""
        # Try vector store first
        concept = await self.vector_store.get(concept_id)
        if concept:
            # Enrich with graph relationships
            relationships = await self.graph_store.get_relationships(concept_id)
            concept.related_concepts = relationships.get("related", [])
            concept.bridge_domains = relationships.get("bridges", [])
        return concept

    async def get_lineage(
        self,
        concept_id: str,
        direction: str = "both"
    ) -> ConceptLineage:
        """개념의 지적 계보 조회"""
        concept = await self.get_concept(concept_id)

        ancestors = []
        descendants = []

        if direction in ["ancestors", "both"]:
            ancestors = await self.graph_store.get_ancestors(concept_id)

        if direction in ["descendants", "both"]:
            descendants = await self.graph_store.get_descendants(concept_id)

        key_influences = await self.graph_store.get_key_influences(concept_id)

        return ConceptLineage(
            concept=concept,
            ancestors=ancestors,
            descendants=descendants,
            key_influences=key_influences
        )

    async def get_fusion_cases(
        self,
        pattern: Optional[str] = None,
        domains: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[FusionCase]:
        """융합 사례 검색"""
        return await self.graph_store.get_fusion_cases(
            pattern=pattern,
            domains=domains,
            limit=limit
        )

    async def search_by_structure(
        self,
        structure: Any,
        exclude_domain: Optional[str] = None
    ) -> List[Concept]:
        """구조 기반 검색"""
        return await self.graph_store.search_by_structure(
            structure=structure,
            exclude_domain=exclude_domain
        )

    async def search_metaphorical(
        self,
        concept: Concept,
        target_domains: Optional[List[str]] = None
    ) -> List[Any]:
        """은유적 연결 검색"""
        # Use vector similarity across domains
        query = f"{concept.name}: {concept.core_principle}"
        results = await self.vector_store.search(
            query=query,
            domains=target_domains,
            exclude_domain=concept.domain,
            limit=10
        )
        return results

    async def search_at_scale(
        self,
        principle: str,
        scale: str,
        target_domains: Optional[List[str]] = None
    ) -> List[Any]:
        """특정 스케일에서 유사 원리 검색"""
        query = f"{principle} at {scale} level"
        return await self.vector_store.search(
            query=query,
            domains=target_domains,
            metadata_filter={"scale": scale},
            limit=10
        )

    async def search_fusion_cases(
        self,
        domains: List[str]
    ) -> List[FusionCase]:
        """특정 도메인들이 관련된 융합 사례 검색"""
        return await self.graph_store.search_fusion_cases_by_domains(domains)

    async def calculate_domain_distance(
        self,
        domain_a: str,
        domain_b: str
    ) -> float:
        """두 도메인 간 거리 계산 (0=같음, 1=매우 다름)"""
        return await self.graph_store.get_domain_distance(domain_a, domain_b)

    async def calculate_concept_novelty(
        self,
        concept_a: Concept,
        concept_b: Concept
    ) -> float:
        """두 개념 융합의 신규성 계산"""
        # Check for existing connections
        connection = await self.graph_store.get_connection(
            concept_a.id, concept_b.id
        )

        if connection:
            return 0.2  # Already connected

        # Check semantic similarity
        similarity = await self.vector_store.calculate_similarity(
            concept_a.embedding,
            concept_b.embedding
        )

        # Higher distance = more novel
        return 1.0 - similarity

    async def extract_concept_structure(self, concept: Concept) -> dict:
        """개념의 구조적 특성 추출"""
        return await self.graph_store.get_concept_structure(concept.id)

    async def analyze_shared_structure(
        self,
        concept_a: Concept,
        concept_b: Concept
    ) -> Any:
        """두 개념의 공유 구조 분석"""
        struct_a = await self.extract_concept_structure(concept_a)
        struct_b = await self.extract_concept_structure(concept_b)

        return await self.graph_store.compare_structures(struct_a, struct_b)

    def _fuse_results(
        self,
        vector_results: List[SearchResult],
        graph_results: List[SearchResult]
    ) -> List[Concept]:
        """
        Reciprocal Rank Fusion (RRF)으로 결과 융합

        RRF score = Σ 1/(k + rank) for each result list
        """
        k = 60  # RRF constant

        scores = {}

        # Score from vector results
        for rank, result in enumerate(vector_results):
            concept_id = result.concept.id
            if concept_id not in scores:
                scores[concept_id] = {"concept": result.concept, "score": 0}
            scores[concept_id]["score"] += 1 / (k + rank + 1)

        # Score from graph results
        for rank, result in enumerate(graph_results):
            concept_id = result.concept.id
            if concept_id not in scores:
                scores[concept_id] = {"concept": result.concept, "score": 0}
            scores[concept_id]["score"] += 1 / (k + rank + 1)

        # Sort by fused score
        sorted_results = sorted(
            scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )

        return [r["concept"] for r in sorted_results]
