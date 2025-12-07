"""
Concept Models - KSEA 기반 개념 모델

Knowledge, Skill, Experience, Ability 프레임워크로
학문적 개념을 다차원적으로 표현하는 데이터 모델
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class ConceptCategory(str, Enum):
    """개념 카테고리"""
    FOUNDATIONAL = "foundational"  # 기초 개념
    TRANSDISCIPLINARY = "transdisciplinary"  # 학제간 개념
    METHODOLOGICAL = "methodological"  # 방법론적 개념
    DOMAIN_SPECIFIC = "domain_specific"  # 분야 특화 개념
    META = "meta"  # 메타 개념


class MasteryLevel(str, Enum):
    """숙달 수준"""
    NOVICE = "novice"  # 입문
    COMPETENT = "competent"  # 이해
    PROFICIENT = "proficient"  # 숙련
    EXPERT = "expert"  # 전문
    MASTER = "master"  # 마스터


# ============================================================
# KSEA Components
# ============================================================

@dataclass
class Knowledge:
    """
    Knowledge (지식) - What & Why

    이론적, 명시적 앎. 개념의 정의, 원리, 이론적 기반.
    """
    # 핵심 정의
    definition: str = ""
    etymology: str = ""  # 어원

    # 핵심 원리들
    core_principles: List[str] = field(default_factory=list)

    # 이론적 기반
    theoretical_foundations: List[Dict[str, str]] = field(default_factory=list)
    # [{"source": "저자/연도", "insight": "핵심 통찰"}]

    # 전제와 가정
    assumptions: List[str] = field(default_factory=list)

    # 함의와 결과
    implications: List[str] = field(default_factory=list)

    # 핵심 구분/분류
    key_distinctions: List[Dict[str, str]] = field(default_factory=list)
    # [{"type_a": "...", "type_b": "...", "difference": "..."}]

    # 형식적 표현 (수식, 논리식 등)
    formal_expression: Optional[str] = None


@dataclass
class Skill:
    """
    Skill (스킬) - How to

    실행 능력. 개념을 적용하는 방법, 기술, 절차.
    """
    # 분석 스킬
    analytical: List[str] = field(default_factory=list)
    # ["현상에서 X를 식별하기", "Y와 Z를 구분하기"]

    # 실천 스킬
    practical: List[str] = field(default_factory=list)
    # ["X를 설계하기", "Y를 구현하기"]

    # 의사소통 스킬
    communicative: List[str] = field(default_factory=list)
    # ["X를 설명하기", "Y를 논증하기"]

    # 비판적 스킬
    critical: List[str] = field(default_factory=list)
    # ["전제를 검토하기", "한계를 평가하기"]

    # 도구 및 방법
    tools_and_methods: List[str] = field(default_factory=list)

    # 절차/프로세스
    procedures: List[Dict[str, Any]] = field(default_factory=list)
    # [{"name": "절차명", "steps": ["단계1", "단계2"]}]


@dataclass
class Experience:
    """
    Experience (경험) - When & Where

    맥락적 지혜. 적용 사례, 맥락, 실패와 성공의 교훈.
    """
    # 적용 사례
    cases: List[Dict[str, str]] = field(default_factory=list)
    # [{"domain": "분야", "example": "사례", "insight": "교훈"}]

    # 역사적 맥락
    historical_context: str = ""

    # 핵심 사상가/실천가
    key_figures: List[Dict[str, str]] = field(default_factory=list)
    # [{"name": "인물", "contribution": "기여", "era": "시대"}]

    # 흔한 실수/함정
    pitfalls: List[str] = field(default_factory=list)

    # 모범 사례
    best_practices: List[str] = field(default_factory=list)

    # 맥락 조건 (언제 적용해야/하지 말아야 하는지)
    context_conditions: Dict[str, List[str]] = field(default_factory=lambda: {
        "apply_when": [],
        "avoid_when": []
    })

    # 실패 사례와 교훈
    failure_cases: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class Ability:
    """
    Ability (능력) - Associational Thinking & Fusion Competence

    Innovator's DNA (Christensen, Dyer, Gregersen)의 Associational Thinking에 기반한
    융합적 역량. 서로 다른 분야의 지식, 아이디어, 패턴을 연결하여
    새로운 통찰과 혁신을 창출하는 능력.

    핵심 질문: "이것이 저것과 어떻게 연결되는가?"
    """

    # ===== Associational Thinking (연결적 사고) =====
    # 이 개념이 다른 분야/개념과 어떻게 연결될 수 있는가?

    # 크로스도메인 연결 (Cross-domain Connections)
    cross_domain_links: List[Dict[str, str]] = field(default_factory=list)
    # [{"domain": "분야", "connection": "연결점", "insight": "새로운 통찰"}]

    # 유추적 연결 (Analogical Connections)
    analogies: List[Dict[str, str]] = field(default_factory=list)
    # [{"source": "원천 개념", "target": "대상 분야", "mapping": "매핑 관계"}]

    # 패턴 인식 (Pattern Recognition across domains)
    recurring_patterns: List[str] = field(default_factory=list)
    # ["이 개념이 나타나는 보편적 패턴들"]

    # ===== Fusion Potential (융합 잠재력) =====

    # 융합 가능성
    fusion_potential: Dict[str, Any] = field(default_factory=lambda: {
        "high_potential_domains": [],  # 높은 융합 가능성 분야
        "fusion_patterns": [],  # 적합한 융합 패턴 (7가지 중)
        "fusion_questions": [],  # 융합을 촉진하는 질문들
        "obstacles": []  # 융합 장애물
    })

    # 다른 개념과의 시너지
    synergies: List[Dict[str, str]] = field(default_factory=list)
    # [{"concept": "개념", "synergy": "시너지 효과", "emergent_insight": "창발적 통찰"}]

    # ===== Innovation Triggers (혁신 촉발점) =====

    # 이 개념이 촉발할 수 있는 질문들 (Questioning - Innovator's DNA)
    provocative_questions: List[str] = field(default_factory=list)

    # 관찰 포인트 (Observing - Innovator's DNA)
    observation_triggers: List[str] = field(default_factory=list)
    # ["이 개념을 적용하면 무엇을 새롭게 관찰할 수 있는가?"]

    # 실험 아이디어 (Experimenting - Innovator's DNA)
    experiment_ideas: List[str] = field(default_factory=list)

    # ===== Transfer & Mastery =====

    # 전이 가능 분야
    transfer_domains: List[Dict[str, str]] = field(default_factory=list)
    # [{"domain": "분야", "application": "적용 방식"}]

    # 숙달 지표
    mastery_indicators: List[str] = field(default_factory=list)

    # 창조적 확장 가능성
    creative_extensions: List[str] = field(default_factory=list)

    # ===== Metacognitive (메타인지) =====

    # 메타인지적 요소
    metacognitive: List[str] = field(default_factory=list)
    # ["자신의 X 이해도 평가하기", "X 적용의 적절성 판단하기"]

    # 자기 제한 인식 (Knowing what you don't know)
    limitations: List[str] = field(default_factory=list)


# ============================================================
# Main Concept Model
# ============================================================

@dataclass
class Concept:
    """
    KSEA 기반 학문적 개념

    Knowledge, Skill, Experience, Ability의 통합적 표현으로
    개념을 다차원적으로 모델링
    """
    # 기본 식별 정보
    id: str
    name: str
    domain: str  # 주 소속 도메인
    domains: List[str] = field(default_factory=list)  # 관련 도메인들

    # 카테고리 및 메타정보
    category: ConceptCategory = ConceptCategory.DOMAIN_SPECIFIC
    scale: Optional[str] = None  # micro, meso, macro
    era: Optional[str] = None  # ancient, medieval, modern, contemporary

    # ===== KSEA 구조 =====
    knowledge: Knowledge = field(default_factory=Knowledge)
    skill: Skill = field(default_factory=Skill)
    experience: Experience = field(default_factory=Experience)
    ability: Ability = field(default_factory=Ability)

    # 관계
    related_concepts: List[str] = field(default_factory=list)
    prerequisite_concepts: List[str] = field(default_factory=list)  # 선행 개념

    # 성찰적 질문
    reflective_questions: List[str] = field(default_factory=list)

    # 전체 텍스트 (RAG용)
    full_text: Optional[str] = None

    # 임베딩 (벡터 검색용)
    embedding: Optional[List[float]] = None

    # 검색 결과 메타데이터
    similarity: float = 0.0

    # 상태
    version: str = "1.0"
    status: str = "draft"  # draft, review, published, world-class

    @property
    def description(self) -> str:
        """전체 설명 (full_text 또는 knowledge.definition)"""
        if self.full_text:
            return self.full_text
        if self.knowledge.definition:
            return self.knowledge.definition
        return self.name

    @property
    def short_description(self) -> str:
        """짧은 설명"""
        if self.knowledge.definition:
            return self.knowledge.definition[:150]
        return self.name

    @property
    def core_principle(self) -> str:
        """핵심 원리 (레거시 호환)"""
        if self.knowledge.core_principles:
            return self.knowledge.core_principles[0]
        return ""

    def get_ksea_summary(self) -> Dict[str, Any]:
        """KSEA 요약"""
        return {
            "knowledge": {
                "principles_count": len(self.knowledge.core_principles),
                "has_formal_expression": bool(self.knowledge.formal_expression)
            },
            "skill": {
                "analytical_count": len(self.skill.analytical),
                "practical_count": len(self.skill.practical),
                "tools_count": len(self.skill.tools_and_methods)
            },
            "experience": {
                "cases_count": len(self.experience.cases),
                "key_figures_count": len(self.experience.key_figures),
                "pitfalls_count": len(self.experience.pitfalls)
            },
            "ability": {
                "transfer_domains_count": len(self.ability.transfer_domains),
                "mastery_indicators_count": len(self.ability.mastery_indicators),
                "fusion_potential": len(self.ability.fusion_potential.get("high_potential_domains", []))
            }
        }

    def get_mastery_level(self) -> MasteryLevel:
        """KSEA 완성도에 따른 숙달 수준 추정"""
        summary = self.get_ksea_summary()
        score = 0

        # Knowledge 점수
        if summary["knowledge"]["principles_count"] >= 3:
            score += 2
        if summary["knowledge"]["has_formal_expression"]:
            score += 1

        # Skill 점수
        if summary["skill"]["analytical_count"] >= 2:
            score += 1
        if summary["skill"]["practical_count"] >= 2:
            score += 1

        # Experience 점수
        if summary["experience"]["cases_count"] >= 3:
            score += 2
        if summary["experience"]["pitfalls_count"] >= 2:
            score += 1

        # Ability 점수
        if summary["ability"]["transfer_domains_count"] >= 2:
            score += 1
        if summary["ability"]["mastery_indicators_count"] >= 3:
            score += 1

        if score >= 9:
            return MasteryLevel.MASTER
        elif score >= 7:
            return MasteryLevel.EXPERT
        elif score >= 5:
            return MasteryLevel.PROFICIENT
        elif score >= 3:
            return MasteryLevel.COMPETENT
        else:
            return MasteryLevel.NOVICE


# ============================================================
# Legacy Support & Utilities
# ============================================================

@dataclass
class ConceptLineage:
    """개념의 지적 계보"""
    concept: Concept
    ancestors: List[Concept] = field(default_factory=list)
    descendants: List[Concept] = field(default_factory=list)
    key_influences: str = ""


@dataclass
class ConceptStructure:
    """개념의 구조적 특성"""
    concept_id: str
    pattern_type: str
    components: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)
    dynamics: str = ""


@dataclass
class ConceptComparison:
    """두 개념 간 KSEA 비교"""
    concept_a: str
    concept_b: str

    # 전체 유사도
    similarity: float = 0.0

    # KSEA별 비교
    knowledge_overlap: float = 0.0
    skill_overlap: float = 0.0
    experience_parallel: float = 0.0
    ability_synergy: float = 0.0

    # 구조적 비교
    shared_structure: str = ""
    key_differences: List[str] = field(default_factory=list)

    # 융합 가능성
    fusion_potential: float = 0.0
    recommended_fusion_patterns: List[str] = field(default_factory=list)


# ============================================================
# Factory Functions
# ============================================================

def create_concept_from_markdown(
    id: str,
    name: str,
    domain: str,
    content: str,
    metadata: Dict[str, Any]
) -> Concept:
    """마크다운과 메타데이터에서 Concept 생성"""

    concept = Concept(
        id=id,
        name=name,
        domain=domain,
        domains=metadata.get("domains", [domain]),
        full_text=content,
        version=metadata.get("version", "1.0"),
        status=metadata.get("status", "draft")
    )

    # KSEA 매핑
    if "knowledge" in metadata:
        k = metadata["knowledge"]
        concept.knowledge = Knowledge(
            definition=k.get("definition", ""),
            etymology=k.get("etymology", ""),
            core_principles=k.get("core_principles", []),
            theoretical_foundations=k.get("theoretical_foundations", []),
            assumptions=k.get("assumptions", []),
            implications=k.get("implications", []),
            key_distinctions=k.get("key_distinctions", []),
            formal_expression=k.get("formal_expression")
        )

    if "skill" in metadata:
        s = metadata["skill"]
        concept.skill = Skill(
            analytical=s.get("analytical", []),
            practical=s.get("practical", []),
            communicative=s.get("communicative", []),
            critical=s.get("critical", []),
            tools_and_methods=s.get("tools_and_methods", []),
            procedures=s.get("procedures", [])
        )

    if "experience" in metadata:
        e = metadata["experience"]
        concept.experience = Experience(
            cases=e.get("cases", []),
            historical_context=e.get("historical_context", ""),
            key_figures=e.get("key_figures", []),
            pitfalls=e.get("pitfalls", []),
            best_practices=e.get("best_practices", []),
            context_conditions=e.get("context_conditions", {"apply_when": [], "avoid_when": []}),
            failure_cases=e.get("failure_cases", [])
        )

    if "ability" in metadata:
        a = metadata["ability"]
        concept.ability = Ability(
            transfer_domains=a.get("transfer_domains", []),
            synergies=a.get("synergies", []),
            mastery_indicators=a.get("mastery_indicators", []),
            creative_extensions=a.get("creative_extensions", []),
            fusion_potential=a.get("fusion_potential", {}),
            metacognitive=a.get("metacognitive", [])
        )

    concept.related_concepts = metadata.get("related_concepts", [])
    concept.reflective_questions = metadata.get("reflective_questions", [])

    return concept
