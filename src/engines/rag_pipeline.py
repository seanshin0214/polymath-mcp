"""
RAG Pipeline - 하이브리드 검색 파이프라인

ChromaDB (벡터) 기반 검색 (Neo4j 옵션)
"""

from typing import List, Optional, Any, Dict
from dataclasses import dataclass
import os

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

    - ChromaDB: 시맨틱 유사성 검색 (필수)
    - Neo4j: 관계 기반 그래프 검색 (옵션)
    """

    def __init__(self, settings):
        self.settings = settings
        self.vector_store = None  # ChromaStore
        self.graph_store = None   # Neo4jStore (optional)
        self.initialized = False
        self.use_graph = False

    async def initialize(self):
        """데이터베이스 연결 초기화"""
        from src.data.chroma_store import ChromaStore

        # Initialize vector store (required)
        self.vector_store = ChromaStore(self.settings)
        await self.vector_store.initialize()

        # Try to initialize graph store (optional)
        try:
            if os.getenv("USE_NEO4J", "false").lower() == "true":
                from src.data.neo4j_store import Neo4jStore
                self.graph_store = Neo4jStore(self.settings)
                await self.graph_store.initialize()
                self.use_graph = True
                print("Neo4j graph store initialized")
        except Exception as e:
            print(f"Neo4j not available (optional): {e}")
            self.graph_store = None
            self.use_graph = False

        self.initialized = True
        print(f"RAG Pipeline initialized (graph={self.use_graph})")

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
        # 1. Vector search (semantic similarity) - always available
        vector_results = await self.vector_store.search(
            query=query,
            domains=domains,
            limit=limit * 2 if self.use_graph else limit
        )

        # 2. Graph search (relationship-based) - optional
        if self.use_graph and self.graph_store:
            try:
                graph_results = await self.graph_store.search(
                    query=query,
                    domains=domains,
                    limit=limit * 2
                )
                # Fuse results using RRF
                fused = self._fuse_results(vector_results, graph_results)
                return fused[:limit]
            except Exception as e:
                print(f"Graph search failed, using vector only: {e}")

        # Vector only
        return vector_results[:limit]

    async def get_concept(self, concept_id: str) -> Optional[Concept]:
        """단일 개념 조회"""
        concept = await self.vector_store.get(concept_id)
        if concept and self.use_graph and self.graph_store:
            try:
                relationships = await self.graph_store.get_relationships(concept_id)
                concept.related_concepts = relationships.get("related", [])
                concept.bridge_domains = relationships.get("bridges", [])
            except:
                pass
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
        key_influences = ""

        if self.use_graph and self.graph_store:
            try:
                if direction in ["ancestors", "both"]:
                    ancestors = await self.graph_store.get_ancestors(concept_id)
                if direction in ["descendants", "both"]:
                    descendants = await self.graph_store.get_descendants(concept_id)
                key_influences = await self.graph_store.get_key_influences(concept_id)
            except:
                pass

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
        if self.use_graph and self.graph_store:
            try:
                return await self.graph_store.get_fusion_cases(
                    pattern=pattern,
                    domains=domains,
                    limit=limit
                )
            except:
                pass

        # Fallback: search vector store for fusion cases
        query = f"fusion case {pattern or ''} {' '.join(domains or [])}"
        results = await self.vector_store.search(
            query=query,
            metadata_filter={"category": "01-Fusion-Cases"},
            limit=limit
        )
        return results

    async def search_by_structure(
        self,
        structure: Any,
        exclude_domain: Optional[str] = None
    ) -> List[Concept]:
        """구조 기반 검색"""
        if self.use_graph and self.graph_store:
            try:
                return await self.graph_store.search_by_structure(
                    structure=structure,
                    exclude_domain=exclude_domain
                )
            except:
                pass
        return []

    async def search_metaphorical(
        self,
        concept: Concept,
        target_domains: Optional[List[str]] = None
    ) -> List[Any]:
        """은유적 연결 검색"""
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
        if self.use_graph and self.graph_store:
            try:
                return await self.graph_store.search_fusion_cases_by_domains(domains)
            except:
                pass
        return []

    async def calculate_domain_distance(
        self,
        domain_a: str,
        domain_b: str
    ) -> float:
        """두 도메인 간 거리 계산 (0=같음, 1=매우 다름)"""
        if self.use_graph and self.graph_store:
            try:
                return await self.graph_store.get_domain_distance(domain_a, domain_b)
            except:
                pass
        return 0.5  # Default moderate distance

    async def calculate_concept_novelty(
        self,
        concept_a: Concept,
        concept_b: Concept
    ) -> float:
        """두 개념 융합의 신규성 계산"""
        # Check for existing connections in graph
        if self.use_graph and self.graph_store:
            try:
                connection = await self.graph_store.get_connection(
                    concept_a.id, concept_b.id
                )
                if connection:
                    return 0.2  # Already connected
            except:
                pass

        # Check semantic similarity
        if concept_a.embedding and concept_b.embedding:
            similarity = await self.vector_store.calculate_similarity(
                concept_a.embedding,
                concept_b.embedding
            )
            return 1.0 - similarity

        return 0.7  # Default moderate novelty

    async def extract_concept_structure(self, concept: Concept) -> dict:
        """개념의 구조적 특성 추출"""
        if self.use_graph and self.graph_store:
            try:
                return await self.graph_store.get_concept_structure(concept.id)
            except:
                pass
        return {}

    async def analyze_shared_structure(
        self,
        concept_a: Concept,
        concept_b: Concept
    ) -> Any:
        """두 개념의 공유 구조 분석"""
        struct_a = await self.extract_concept_structure(concept_a)
        struct_b = await self.extract_concept_structure(concept_b)

        if self.use_graph and self.graph_store:
            try:
                return await self.graph_store.compare_structures(struct_a, struct_b)
            except:
                pass

        return {
            "similarity": 0.5,
            "description": "구조 분석 (그래프 DB 미연결)",
            "key_aspect": "시맨틱 유사성 기반 분석"
        }

    async def add_document(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        새 문서 추가

        Args:
            content: 문서 내용
            metadata: 메타데이터 (name, domain, category 등)

        Returns:
            생성된 문서 ID
        """
        import hashlib

        # Generate ID
        doc_id = metadata.get('id') or hashlib.md5(content.encode()).hexdigest()[:12]

        # Create concept
        concept = Concept(
            id=doc_id,
            name=metadata.get('name', 'Untitled'),
            domain=metadata.get('domain', 'general'),
            description=content[:500],
            full_text=content,
            category=metadata.get('category', 'user-added')
        )

        # Add to vector store
        await self.vector_store.add_concept(concept)

        print(f"Added document: {doc_id} ({concept.name})")
        return doc_id

    async def get_stats(self) -> Dict[str, Any]:
        """저장소 통계 조회"""
        return {
            "vector_store": {
                "count": self.vector_store.count() if self.vector_store else 0,
                "available": self.vector_store is not None
            },
            "graph_store": {
                "available": self.use_graph,
                "connected": self.graph_store is not None
            }
        }

    def _fuse_results(
        self,
        vector_results: List[Any],
        graph_results: List[Any]
    ) -> List[Concept]:
        """
        Reciprocal Rank Fusion (RRF)으로 결과 융합

        RRF score = Σ 1/(k + rank) for each result list
        """
        k = 60  # RRF constant
        scores = {}

        # Score from vector results
        for rank, result in enumerate(vector_results):
            concept_id = result.id if hasattr(result, 'id') else str(result)
            if concept_id not in scores:
                scores[concept_id] = {"concept": result, "score": 0}
            scores[concept_id]["score"] += 1 / (k + rank + 1)

        # Score from graph results
        for rank, result in enumerate(graph_results):
            concept_id = result.id if hasattr(result, 'id') else str(result)
            if concept_id not in scores:
                scores[concept_id] = {"concept": result, "score": 0}
            scores[concept_id]["score"] += 1 / (k + rank + 1)

        # Sort by fused score
        sorted_results = sorted(
            scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )

        return [r["concept"] for r in sorted_results]
