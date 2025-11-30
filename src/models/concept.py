"""
Concept Models - 개념 모델

학문적 개념과 그 관계를 표현하는 데이터 모델
"""

from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class Concept:
    """
    학문적 개념

    30개 도메인에 걸친 개념들을 표현
    """
    id: str
    name: str
    domain: str  # 소속 도메인 (philosophy, economics, etc.)
    description: str  # 상세 설명

    # Optional fields
    full_text: Optional[str] = None  # 전체 텍스트 (RAG용)
    category: str = "general"  # 개념 카테고리
    scale: Optional[str] = None  # micro, meso, macro
    era: Optional[str] = None  # ancient, medieval, modern, contemporary

    # Core intellectual content
    core_principle: str = ""  # 핵심 원리
    assumptions: List[str] = field(default_factory=list)  # 전제들
    implications: List[str] = field(default_factory=list)  # 함의들

    # Relationships
    related_concepts: List[str] = field(default_factory=list)  # 관련 개념 IDs
    bridge_domains: List[str] = field(default_factory=list)  # 연결 가능한 도메인들
    key_thinkers: List[str] = field(default_factory=list)  # 핵심 사상가들

    # Display
    short_description: str = ""  # 짧은 설명

    # Embedding (for vector search)
    embedding: Optional[List[float]] = None

    # Search result metadata
    similarity: float = 0.0

    def __post_init__(self):
        if not self.short_description:
            self.short_description = self.description[:100] if self.description else self.name


@dataclass
class ConceptLineage:
    """
    개념의 지적 계보

    선조 개념과 후손 개념, 핵심 영향 관계를 표현
    """
    concept: Concept
    ancestors: List[Concept] = field(default_factory=list)  # 선조 개념들
    descendants: List[Concept] = field(default_factory=list)  # 후손 개념들
    key_influences: str = ""  # 핵심 영향 관계 설명


@dataclass
class ConceptStructure:
    """
    개념의 구조적 특성

    구조적 동형 패턴 분석을 위한 표현
    """
    concept_id: str
    pattern_type: str  # hierarchical, network, cyclical, etc.
    components: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)
    dynamics: str = ""  # 동적 특성


@dataclass
class ConceptComparison:
    """
    두 개념 간 비교 결과
    """
    concept_a: str
    concept_b: str
    similarity: float
    shared_structure: str
    key_differences: List[str] = field(default_factory=list)
    fusion_potential: float = 0.0
