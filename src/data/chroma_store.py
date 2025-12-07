"""
ChromaDB Vector Store - 시맨틱 검색

임베딩 기반 유사성 검색 담당
"""

from typing import List, Optional, Any, Set
import sys
import logging
import re

# Suppress ChromaDB and related logs
logging.getLogger('chromadb').setLevel(logging.ERROR)
logging.getLogger('onnxruntime').setLevel(logging.ERROR)
logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.ERROR)

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.models.concept import Concept


class ChromaStore:
    """
    ChromaDB 벡터 스토어

    - 개념 임베딩 저장 및 검색
    - 시맨틱 유사성 기반 검색
    - 도메인/메타데이터 필터링
    """

    def __init__(self, settings):
        self.settings = settings
        self.client = None
        self.collection = None

    async def initialize(self):
        """ChromaDB 초기화"""
        # Use persistent storage
        self.client = chromadb.PersistentClient(
            path=str(self.settings.chroma_path),
            settings=ChromaSettings(
                anonymized_telemetry=False
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="polymath_concepts",
            metadata={"description": "Polymath MCP concept embeddings"}
        )

        print(f"ChromaDB initialized with {self.collection.count()} concepts", file=sys.stderr)

        # Cache available domains for fuzzy matching
        self._domain_cache: Set[str] = set()
        self._refresh_domain_cache()

    def _refresh_domain_cache(self):
        """도메인 캐시 갱신"""
        try:
            all_meta = self.collection.get(include=["metadatas"])
            if all_meta and all_meta["metadatas"]:
                self._domain_cache = set(
                    meta.get("domain", "") for meta in all_meta["metadatas"]
                )
        except Exception:
            pass

    def _normalize_domain(self, domain: str) -> str:
        """
        도메인명 정규화
        'Game Theory' -> 'game_theory'
        'gameTheory' -> 'game_theory'
        'GAME-THEORY' -> 'game_theory'
        """
        if not domain:
            return domain

        # Convert camelCase to snake_case
        domain = re.sub(r'([a-z])([A-Z])', r'\1_\2', domain)
        # Replace spaces, hyphens with underscores
        domain = re.sub(r'[\s\-]+', '_', domain)
        # Remove special characters except underscores
        domain = re.sub(r'[^\w]', '', domain)
        # Lowercase
        domain = domain.lower()
        # Remove duplicate underscores
        domain = re.sub(r'_+', '_', domain)
        # Strip leading/trailing underscores
        domain = domain.strip('_')

        return domain

    def _match_domain(self, user_domain: str) -> Optional[str]:
        """
        사용자 입력 도메인을 저장된 도메인과 매칭
        Returns the matched domain from cache or None
        """
        if not user_domain:
            return None

        normalized = self._normalize_domain(user_domain)

        # Direct match
        if normalized in self._domain_cache:
            return normalized

        # Try matching normalized versions
        for stored_domain in self._domain_cache:
            if self._normalize_domain(stored_domain) == normalized:
                return stored_domain

        # Fuzzy match: check if normalized is substring or vice versa
        for stored_domain in self._domain_cache:
            stored_normalized = self._normalize_domain(stored_domain)
            if normalized in stored_normalized or stored_normalized in normalized:
                return stored_domain

        # No match found - return normalized anyway (might still work)
        return normalized

    async def add_concept(self, concept: Concept):
        """개념 추가"""
        self.collection.add(
            ids=[concept.id],
            documents=[concept.full_text],
            embeddings=[concept.embedding] if concept.embedding else None,
            metadatas=[{
                "name": concept.name,
                "domain": concept.domain,
                "category": concept.category,
                "scale": concept.scale or "meso",
                "era": concept.era or "modern"
            }]
        )

    async def search(
        self,
        query: str,
        domains: Optional[List[str]] = None,
        exclude_domain: Optional[str] = None,
        metadata_filter: Optional[dict] = None,
        limit: int = 10
    ) -> List[Any]:
        """시맨틱 검색 (도메인 유연 매칭 지원)"""
        where_filter = {}

        if domains:
            # Normalize and match each domain
            matched_domains = []
            for d in domains:
                matched = self._match_domain(d)
                if matched:
                    matched_domains.append(matched)
            if matched_domains:
                where_filter["domain"] = {"$in": matched_domains}

        if exclude_domain:
            matched_exclude = self._match_domain(exclude_domain)
            if matched_exclude:
                where_filter["domain"] = {"$ne": matched_exclude}

        if metadata_filter:
            where_filter.update(metadata_filter)

        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"]
        )

        concepts = []
        if results and results["ids"]:
            for i, id in enumerate(results["ids"][0]):
                # Convert L2 distance to similarity score (0-1 range)
                # Using 1/(1+d) formula to ensure positive values
                distance = results["distances"][0][i]
                similarity = 1.0 / (1.0 + distance)

                concept = Concept(
                    id=id,
                    name=results["metadatas"][0][i]["name"],
                    domain=results["metadatas"][0][i]["domain"],
                    full_text=results["documents"][0][i][:500],
                    similarity=similarity
                )
                concepts.append(concept)

        return concepts

    async def search_by_name(
        self,
        name: str,
        limit: int = 5
    ) -> List[Any]:
        """이름 기반 검색 (정확한 매칭 우선)"""
        # First try exact match with where filter
        results = self.collection.get(
            where={"name": name},
            include=["documents", "metadatas"]
        )

        concepts = []
        if results and results["ids"]:
            for i, id in enumerate(results["ids"]):
                concept = Concept(
                    id=id,
                    name=results["metadatas"][i]["name"],
                    domain=results["metadatas"][i]["domain"],
                    full_text=results["documents"][i][:500] if results["documents"] else "",
                    similarity=1.0  # Exact match
                )
                concepts.append(concept)
            return concepts

        # If no exact match, try partial match (case insensitive)
        all_results = self.collection.get(
            include=["documents", "metadatas"]
        )

        name_lower = name.lower()
        if all_results and all_results["ids"]:
            for i, id in enumerate(all_results["ids"]):
                concept_name = all_results["metadatas"][i].get("name", "")
                if name_lower in concept_name.lower():
                    concept = Concept(
                        id=id,
                        name=concept_name,
                        domain=all_results["metadatas"][i]["domain"],
                        full_text=all_results["documents"][i][:500] if all_results["documents"] else "",
                        similarity=0.9  # Partial match
                    )
                    concepts.append(concept)
                    if len(concepts) >= limit:
                        break

        return concepts

    async def get(self, concept_id: str) -> Optional[Concept]:
        """ID로 개념 조회"""
        result = self.collection.get(
            ids=[concept_id],
            include=["documents", "metadatas", "embeddings"]
        )

        if result and result["ids"]:
            return Concept(
                id=concept_id,
                name=result["metadatas"][0]["name"],
                domain=result["metadatas"][0]["domain"],
                full_text=result["documents"][0],
                embedding=result["embeddings"][0] if result["embeddings"] else None
            )
        return None

    async def calculate_similarity(
        self,
        embedding_a: List[float],
        embedding_b: List[float]
    ) -> float:
        """두 임베딩 간 유사도 계산"""
        import numpy as np

        a = np.array(embedding_a)
        b = np.array(embedding_b)

        # Cosine similarity
        similarity = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        return float(similarity)

    async def update_concept(self, concept: Concept):
        """개념 업데이트"""
        self.collection.update(
            ids=[concept.id],
            documents=[concept.full_text],
            embeddings=[concept.embedding] if concept.embedding else None,
            metadatas=[{
                "name": concept.name,
                "domain": concept.domain,
                "category": concept.category,
                "scale": concept.scale or "meso",
                "era": concept.era or "modern"
            }]
        )

    async def delete_concept(self, concept_id: str):
        """개념 삭제"""
        self.collection.delete(ids=[concept_id])

    def count(self) -> int:
        """총 개념 수"""
        return self.collection.count()

    def get_all_domains(self) -> List[str]:
        """모든 고유 도메인 목록 반환"""
        self._refresh_domain_cache()
        return sorted(list(self._domain_cache))
