"""
Fusion Models - 융합 모델

융합 사고 패턴, 브릿지, 융합 사례 등을 표현하는 데이터 모델
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class Bridge:
    """
    분야 간 연결점 (브릿지)

    한 개념에서 다른 분야로의 연결을 표현
    """
    source_concept: str  # 출발 개념 ID
    target_concept: str  # 도착 개념 ID
    target_domain: str  # 도착 도메인
    bridge_type: str  # 융합 패턴 유형
    strength: float  # 연결 강도 (0-1)
    description: str  # 연결 설명
    exploration_question: str  # 탐구 질문


@dataclass
class FusionPattern:
    """
    융합 사고 패턴 (7가지 중 하나)

    - metaphorical_transfer: 은유적 전이
    - structural_isomorphism: 구조적 동형
    - assumption_subversion: 전제 전복
    - scale_jump: 스케일 점프
    - temporal_transformation: 시간축 변환
    - boundary_concept: 경계 개념
    - dialectical_synthesis: 변증법적 종합
    """
    id: str
    name: str
    key: str  # 패턴 키 (영문)
    description: str
    examples: List[str] = field(default_factory=list)
    key_question: str = ""
    how_to_apply: str = ""


@dataclass
class FusionPrecedent:
    """
    융합 선례

    과거에 성공한 유사한 융합 사례
    """
    name: str
    source_domains: List[str]
    pattern: str
    insight: str


@dataclass
class FusionSuggestion:
    """
    융합 제안

    두 개념의 융합 가능성 분석 결과
    """
    concept_a: str
    concept_b: str
    applicable_patterns: List[Tuple[str, float]]  # (패턴, 적합도) 쌍
    precedents: List[FusionPrecedent]  # 유사 선례
    novelty_score: float  # 신규성 점수 (0-1)


@dataclass
class FusionCase:
    """
    융합 사례

    실제로 성공한 융합 사례 (역사적 또는 현대적)
    """
    id: str
    name: str  # 융합 결과물 이름
    creator: str  # 창시자
    pattern: str  # 사용된 융합 패턴
    source_domains: List[str]  # 원천 도메인들
    source_concepts: List[dict]  # 원천 개념들 [{concept, domain, role}]
    insight: str  # 핵심 통찰
    replicable_pattern: str  # 복제 가능한 패턴 설명
    key_insight: str = ""  # 핵심 통찰 (짧은 버전)


@dataclass
class StructuralAnalogy:
    """
    구조적 유사체

    다른 분야에서 발견된 구조적으로 유사한 개념
    """
    concept_name: str
    domain: str
    similarity_score: float
    shared_structure: str  # 공유하는 구조 설명
    exploration_suggestion: str  # 탐구 제안


@dataclass
class SimilarConcept:
    """
    유사한 기존 개념

    신규성 평가 시 발견된 유사 개념
    """
    name: str
    domain: str
    similarity: float


@dataclass
class NoveltyEvaluation:
    """
    신규성 평가 결과

    제안된 융합의 신규성 평가
    """
    score: float  # 신규성 점수 (0-1)
    similar_existing: List[SimilarConcept]  # 유사한 기존 개념들
    assessment: str  # 평가 의견
    improvement_suggestions: str  # 개선 제안


@dataclass
class MetaphorConnection:
    """
    은유적 연결

    은유적 전이 패턴에서 발견된 연결
    """
    source_concept: str
    target_concept: str
    metaphor_description: str  # "A는 B와 같다"
    metaphor_strength: float
    insight_potential: str


@dataclass
class ScaleAnalogy:
    """
    스케일 유사체

    다른 스케일에서 발견된 유사한 원리
    """
    concept_name: str
    domain: str
    scale: str  # micro, meso, macro
    principle_similarity: float
    application_insight: str
