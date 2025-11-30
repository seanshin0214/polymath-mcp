"""
Fusion Engine - 융합 사고 엔진

7가지 융합 패턴을 적용하여 개념 간 연결을 찾고 새로운 융합을 제안
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass

from src.models.fusion import (
    Bridge, FusionSuggestion, StructuralAnalogy,
    NoveltyEvaluation, FusionPrecedent
)


@dataclass
class FusionConfig:
    """Fusion engine configuration"""
    min_similarity_threshold: float = 0.3
    max_bridges_per_concept: int = 10
    novelty_check_depth: int = 3


class FusionEngine:
    """
    융합 사고 엔진

    7가지 융합 패턴:
    1. 은유적 전이 (Metaphorical Transfer)
    2. 구조적 동형 (Structural Isomorphism)
    3. 전제 전복 (Assumption Subversion)
    4. 스케일 점프 (Scale Jump)
    5. 시간축 변환 (Temporal Transformation)
    6. 경계 개념 (Boundary Concept)
    7. 변증법적 종합 (Dialectical Synthesis)
    """

    def __init__(self, rag_pipeline, config: Optional[FusionConfig] = None):
        self.rag = rag_pipeline
        self.config = config or FusionConfig()

    async def find_bridges(
        self,
        concept_id: str,
        target_domains: Optional[List[str]] = None
    ) -> List[Bridge]:
        """
        개념에서 다른 분야로의 연결점(브릿지) 탐색

        각 융합 패턴을 적용하여 가능한 연결점을 찾음
        """
        # Get source concept
        concept = await self.rag.get_concept(concept_id)
        if not concept:
            return []

        bridges = []

        # 1. 구조적 동형 탐색
        structural_bridges = await self._find_structural_bridges(
            concept, target_domains
        )
        bridges.extend(structural_bridges)

        # 2. 은유적 연결 탐색
        metaphorical_bridges = await self._find_metaphorical_bridges(
            concept, target_domains
        )
        bridges.extend(metaphorical_bridges)

        # 3. 경계 개념 기반 연결
        boundary_bridges = await self._find_boundary_bridges(
            concept, target_domains
        )
        bridges.extend(boundary_bridges)

        # 4. 스케일 점프 가능성
        scale_bridges = await self._find_scale_bridges(
            concept, target_domains
        )
        bridges.extend(scale_bridges)

        # Sort by strength and limit
        bridges.sort(key=lambda b: b.strength, reverse=True)
        return bridges[:self.config.max_bridges_per_concept]

    async def suggest_fusion(
        self,
        concept_a: str,
        concept_b: str
    ) -> FusionSuggestion:
        """
        두 개념의 융합 가능성 분석

        적용 가능한 패턴, 선례, 신규성 평가 제공
        """
        # Get both concepts
        ca = await self.rag.get_concept(concept_a)
        cb = await self.rag.get_concept(concept_b)

        # Analyze applicable patterns
        patterns = await self._analyze_applicable_patterns(ca, cb)

        # Find precedents
        precedents = await self._find_fusion_precedents(ca, cb)

        # Evaluate novelty
        novelty_score = await self._evaluate_fusion_novelty(
            ca, cb, precedents
        )

        return FusionSuggestion(
            concept_a=concept_a,
            concept_b=concept_b,
            applicable_patterns=patterns,
            precedents=precedents,
            novelty_score=novelty_score
        )

    async def find_structural_analogies(
        self,
        concept_id: str,
        exclude_same_domain: bool = True
    ) -> List[StructuralAnalogy]:
        """
        구조적으로 유사한 개념들 탐색 (다른 분야에서)

        구조적 동형 패턴 적용
        """
        concept = await self.rag.get_concept(concept_id)
        if not concept:
            return []

        # Extract structural features
        structure = await self._extract_structure(concept)

        # Search for similar structures in other domains
        candidates = await self.rag.search_by_structure(
            structure=structure,
            exclude_domain=concept.domain if exclude_same_domain else None
        )

        analogies = []
        for candidate in candidates:
            shared = await self._analyze_shared_structure(concept, candidate)
            analogies.append(StructuralAnalogy(
                concept_name=candidate.name,
                domain=candidate.domain,
                similarity_score=shared.similarity,
                shared_structure=shared.description,
                exploration_suggestion=self._generate_exploration_suggestion(
                    concept, candidate, shared
                )
            ))

        return analogies

    async def evaluate_novelty(
        self,
        proposed_concept: str,
        foundations: List[str]
    ) -> NoveltyEvaluation:
        """
        제안된 융합의 신규성 평가

        기존 유사 개념과 비교하여 얼마나 새로운지 평가
        """
        # Search for similar existing concepts
        similar = await self.rag.search(
            query=proposed_concept,
            limit=10
        )

        # Calculate novelty score
        if not similar:
            score = 0.95  # Very novel if nothing similar found
        else:
            max_similarity = max(c.similarity for c in similar)
            score = 1.0 - max_similarity

        # Generate assessment
        assessment = self._generate_novelty_assessment(
            proposed_concept, foundations, similar, score
        )

        # Generate improvement suggestions
        suggestions = self._generate_improvement_suggestions(
            proposed_concept, similar, score
        )

        return NoveltyEvaluation(
            score=score,
            similar_existing=similar[:5],
            assessment=assessment,
            improvement_suggestions=suggestions
        )

    # Private helper methods

    async def _find_structural_bridges(
        self,
        concept,
        target_domains: Optional[List[str]]
    ) -> List[Bridge]:
        """구조적 유사성 기반 브릿지 탐색"""
        bridges = []

        # Get structural similar concepts from graph
        similar = await self.rag.graph_store.find_structural_similar(
            concept_id=concept.id,
            target_domains=target_domains
        )

        for sim in similar:
            bridges.append(Bridge(
                source_concept=concept.id,
                target_concept=sim.id,
                target_domain=sim.domain,
                bridge_type="structural_isomorphism",
                strength=sim.similarity,
                description=f"구조적 유사성: {sim.shared_pattern}",
                exploration_question=f"'{concept.name}'의 구조가 '{sim.name}'에서 어떻게 작동하는가?"
            ))

        return bridges

    async def _find_metaphorical_bridges(
        self,
        concept,
        target_domains: Optional[List[str]]
    ) -> List[Bridge]:
        """은유적 연결 탐색"""
        bridges = []

        # Use semantic search to find metaphorical connections
        metaphors = await self.rag.search_metaphorical(
            concept=concept,
            target_domains=target_domains
        )

        for meta in metaphors:
            bridges.append(Bridge(
                source_concept=concept.id,
                target_concept=meta.id,
                target_domain=meta.domain,
                bridge_type="metaphorical_transfer",
                strength=meta.metaphor_strength,
                description=f"은유적 연결: '{concept.name}'은 '{meta.name}'와 같다",
                exploration_question=f"'{concept.name}'을 '{meta.domain}'의 은유로 사용하면 어떤 통찰을 얻을 수 있는가?"
            ))

        return bridges

    async def _find_boundary_bridges(
        self,
        concept,
        target_domains: Optional[List[str]]
    ) -> List[Bridge]:
        """경계 개념 기반 연결 탐색"""
        bridges = []

        # Find boundary concepts that this concept connects to
        boundary_concepts = await self.rag.graph_store.find_boundary_concepts(
            concept_id=concept.id
        )

        for bc in boundary_concepts:
            # Find concepts in other domains that also connect to this boundary concept
            connected = await self.rag.graph_store.find_connected_through(
                boundary_concept_id=bc.id,
                exclude_domain=concept.domain,
                target_domains=target_domains
            )

            for conn in connected:
                bridges.append(Bridge(
                    source_concept=concept.id,
                    target_concept=conn.id,
                    target_domain=conn.domain,
                    bridge_type="boundary_concept",
                    strength=bc.centrality * conn.connection_strength,
                    description=f"경계 개념 '{bc.name}'을 통한 연결",
                    exploration_question=f"'{bc.name}'이라는 경계 개념을 통해 '{concept.name}'과 '{conn.name}'은 어떻게 대화할 수 있는가?"
                ))

        return bridges

    async def _find_scale_bridges(
        self,
        concept,
        target_domains: Optional[List[str]]
    ) -> List[Bridge]:
        """스케일 점프 가능성 탐색"""
        bridges = []

        # Identify concept's scale level
        current_scale = await self._identify_scale(concept)

        # Find concepts at different scales with similar principles
        for scale in ["micro", "meso", "macro"]:
            if scale == current_scale:
                continue

            similar_at_scale = await self.rag.search_at_scale(
                principle=concept.core_principle,
                scale=scale,
                target_domains=target_domains
            )

            for sim in similar_at_scale:
                bridges.append(Bridge(
                    source_concept=concept.id,
                    target_concept=sim.id,
                    target_domain=sim.domain,
                    bridge_type="scale_jump",
                    strength=sim.principle_similarity,
                    description=f"스케일 점프: {current_scale} → {scale}",
                    exploration_question=f"'{concept.name}'의 원리가 {scale} 수준에서도 작동할까?"
                ))

        return bridges

    async def _analyze_applicable_patterns(
        self,
        concept_a,
        concept_b
    ) -> List[Tuple[str, float]]:
        """두 개념에 적용 가능한 융합 패턴 분석"""
        patterns = []

        # Check each pattern's applicability
        pattern_scores = {
            "metaphorical_transfer": await self._score_metaphorical_fit(concept_a, concept_b),
            "structural_isomorphism": await self._score_structural_fit(concept_a, concept_b),
            "assumption_subversion": await self._score_subversion_potential(concept_a, concept_b),
            "scale_jump": await self._score_scale_jump(concept_a, concept_b),
            "temporal_transformation": await self._score_temporal_fit(concept_a, concept_b),
            "boundary_concept": await self._score_boundary_potential(concept_a, concept_b),
            "dialectical_synthesis": await self._score_dialectical_fit(concept_a, concept_b)
        }

        # Sort by score and filter
        for pattern, score in sorted(pattern_scores.items(), key=lambda x: x[1], reverse=True):
            if score > 0.3:  # Threshold for applicability
                patterns.append((pattern, score))

        return patterns

    async def _find_fusion_precedents(
        self,
        concept_a,
        concept_b
    ) -> List[FusionPrecedent]:
        """유사한 융합 선례 탐색"""
        # Search for existing fusion cases involving similar domains/concepts
        cases = await self.rag.search_fusion_cases(
            domains=[concept_a.domain, concept_b.domain]
        )

        precedents = []
        for case in cases:
            precedents.append(FusionPrecedent(
                name=case.name,
                source_domains=case.source_domains,
                pattern=case.pattern,
                insight=case.key_insight
            ))

        return precedents

    async def _evaluate_fusion_novelty(
        self,
        concept_a,
        concept_b,
        precedents: List[FusionPrecedent]
    ) -> float:
        """융합의 신규성 점수 계산"""
        # Base novelty from domain distance
        domain_novelty = await self.rag.calculate_domain_distance(
            concept_a.domain, concept_b.domain
        )

        # Reduce novelty if many precedents exist
        precedent_penalty = min(0.3, len(precedents) * 0.05)

        # Check concept-level novelty
        concept_novelty = await self.rag.calculate_concept_novelty(
            concept_a, concept_b
        )

        return min(1.0, (domain_novelty + concept_novelty) / 2 - precedent_penalty)

    async def _extract_structure(self, concept):
        """개념의 구조적 특성 추출"""
        return await self.rag.extract_concept_structure(concept)

    async def _analyze_shared_structure(self, concept_a, concept_b):
        """두 개념의 공유 구조 분석"""
        return await self.rag.analyze_shared_structure(concept_a, concept_b)

    def _generate_exploration_suggestion(self, source, target, shared):
        """탐구 제안 생성"""
        return f"'{source.name}'의 {shared.key_aspect}가 '{target.name}'에서 어떻게 나타나는지 탐구해보세요."

    def _generate_novelty_assessment(self, proposed, foundations, similar, score):
        """신규성 평가 텍스트 생성"""
        if score >= 0.8:
            return "매우 높은 신규성을 보입니다. 기존에 잘 탐구되지 않은 새로운 연결입니다."
        elif score >= 0.6:
            return "높은 신규성을 보입니다. 일부 유사한 시도가 있으나 차별화 가능합니다."
        elif score >= 0.4:
            return "중간 수준의 신규성입니다. 기존 연구를 참고하되 새로운 관점이 필요합니다."
        else:
            return "낮은 신규성입니다. 기존 연구와 차별화 전략을 강화해야 합니다."

    def _generate_improvement_suggestions(self, proposed, similar, score):
        """신규성 개선 제안 생성"""
        if score < 0.4:
            return "새로운 융합 패턴을 적용하거나 제3의 개념을 도입해 차별화를 시도하세요."
        elif score < 0.7:
            return "기존 연구가 다루지 않은 특정 측면에 집중하거나 다른 스케일에서 접근해보세요."
        else:
            return "높은 신규성을 유지하면서 이론적 기여 가능성을 구체화하세요."

    async def _identify_scale(self, concept):
        """개념의 스케일 수준 식별"""
        # Placeholder - would use LLM or rules to identify
        return "meso"

    # Pattern scoring methods (placeholders)
    async def _score_metaphorical_fit(self, a, b):
        return 0.5

    async def _score_structural_fit(self, a, b):
        return 0.5

    async def _score_subversion_potential(self, a, b):
        return 0.5

    async def _score_scale_jump(self, a, b):
        return 0.5

    async def _score_temporal_fit(self, a, b):
        return 0.5

    async def _score_boundary_potential(self, a, b):
        return 0.5

    async def _score_dialectical_fit(self, a, b):
        return 0.5
