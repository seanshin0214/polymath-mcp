"""
Fusion Tools - 융합 도구

브릿지 탐색, 융합 제안, 구조적 유사성 탐지, 신규성 평가 등
"""

from typing import List, Optional
from mcp.server import Server
from mcp.types import TextContent

from src.models.fusion import FusionPattern, FusionSuggestion, Bridge


# 7가지 융합 사고 패턴
FUSION_PATTERNS = {
    "metaphorical_transfer": {
        "name": "은유적 전이 (Metaphorical Transfer)",
        "description": "A는 B와 같다 - 한 분야의 개념을 다른 분야의 은유로 사용",
        "examples": ["조직=유기체", "마음=컴퓨터", "시장=생태계"],
        "key_question": "이 개념이 다른 분야에서 어떤 것의 은유가 될 수 있을까?"
    },
    "structural_isomorphism": {
        "name": "구조적 동형 (Structural Isomorphism)",
        "description": "같은 구조, 다른 분야 - 서로 다른 분야에서 동일한 구조/패턴 발견",
        "examples": ["진화 알고리즘 (생물학↔CS)", "네트워크 이론 (사회학↔물리학↔생물학)"],
        "key_question": "이 구조와 동일한 패턴이 다른 분야에 있을까?"
    },
    "assumption_subversion": {
        "name": "전제 전복 (Assumption Subversion)",
        "description": "A 분야가 B 분야의 핵심 전제를 도전/반박",
        "examples": ["행동경제학 (심리학→경제학)", "사회구성주의 (사회학→자연과학)"],
        "key_question": "이 분야가 당연시하는 것을 다른 분야는 어떻게 볼까?"
    },
    "scale_jump": {
        "name": "스케일 점프 (Scale Jump)",
        "description": "미시↔거시 이동 - 한 수준의 원리를 다른 수준에 적용",
        "examples": ["창발 (물리→복잡계→사회)", "게임이론 (개인→집단→국제관계)"],
        "key_question": "이 원리가 더 큰/작은 스케일에서도 작동할까?"
    },
    "temporal_transformation": {
        "name": "시간축 변환 (Temporal Transformation)",
        "description": "단기↔장기 원리 이동 - 시간 스케일을 변환하여 적용",
        "examples": ["문화 진화 (생물학적 시간→문화적 시간)", "역사적 제도주의"],
        "key_question": "이 원리가 다른 시간 스케일에서 어떻게 작동할까?"
    },
    "boundary_concept": {
        "name": "경계 개념 (Boundary Concept)",
        "description": "여러 분야가 공유하는 개념 발견/창조",
        "examples": ["네트워크", "정보", "복잡성", "피드백"],
        "key_question": "어떤 개념이 여러 분야를 연결하는 다리가 될 수 있을까?"
    },
    "dialectical_synthesis": {
        "name": "변증법적 종합 (Dialectical Synthesis)",
        "description": "대립하는 두 관점에서 제3의 통합적 관점 도출",
        "examples": ["구조-행위자 이중성 (Giddens)", "본성-양육→후성유전학"],
        "key_question": "이 두 대립하는 관점을 어떻게 통합할 수 있을까?"
    }
}


def register_fusion_tools(server: Server):
    """Register fusion tools with the MCP server"""

    @server.call_tool()
    async def find_bridges(
        concept_id: str,
        target_domains: Optional[List[str]] = None
    ) -> List[TextContent]:
        """
        다른 분야와의 연결점 탐색

        Args:
            concept_id: 출발 개념 ID
            target_domains: 타겟 도메인 목록 (선택)

        Returns:
            발견된 브릿지 목록
        """
        from src.server import fusion_engine

        bridges = await fusion_engine.find_bridges(
            concept_id=concept_id,
            target_domains=target_domains
        )

        if not bridges:
            return [TextContent(
                type="text",
                text="발견된 연결점이 없습니다. 다른 개념이나 도메인을 시도해보세요."
            )]

        text = f"## {concept_id}의 분야 간 연결점\n\n"
        for bridge in bridges:
            text += f"""
### → {bridge.target_concept} ({bridge.target_domain})

**연결 유형**: {bridge.bridge_type}
**연결 강도**: {bridge.strength:.2f}

**연결 설명**:
{bridge.description}

**탐구 질문**:
- {bridge.exploration_question}

---
"""

        return [TextContent(type="text", text=text)]

    @server.call_tool()
    async def suggest_fusion(
        concept_a: str,
        concept_b: str
    ) -> List[TextContent]:
        """
        두 개념의 융합 가능성 분석

        Args:
            concept_a: 첫 번째 개념
            concept_b: 두 번째 개념

        Returns:
            융합 가능성 분석 결과
        """
        from src.server import fusion_engine

        suggestion = await fusion_engine.suggest_fusion(concept_a, concept_b)

        text = f"""
## 융합 분석: {concept_a} × {concept_b}

### 적용 가능한 융합 패턴

"""
        for pattern, score in suggestion.applicable_patterns:
            pattern_info = FUSION_PATTERNS.get(pattern, {})
            text += f"""
#### {pattern_info.get('name', pattern)} (적합도: {score:.2f})

{pattern_info.get('description', '')}

**핵심 질문**: {pattern_info.get('key_question', '')}

"""

        text += f"""
### 유사 선례

"""
        for precedent in suggestion.precedents[:3]:
            text += f"- **{precedent.name}**: {precedent.insight}\n"

        text += f"""
### 신규성 평가

**신규성 점수**: {suggestion.novelty_score:.2f}/1.0

{_get_novelty_interpretation(suggestion.novelty_score)}
"""

        return [TextContent(type="text", text=text)]

    @server.call_tool()
    async def find_structural_analogies(
        concept_id: str,
        exclude_same_domain: bool = True
    ) -> List[TextContent]:
        """
        구조적 유사성 탐지 - 다른 분야에서 동일한 구조를 가진 개념 찾기

        Args:
            concept_id: 분석할 개념 ID
            exclude_same_domain: 같은 도메인 제외 여부

        Returns:
            구조적으로 유사한 개념들
        """
        from src.server import fusion_engine

        analogies = await fusion_engine.find_structural_analogies(
            concept_id=concept_id,
            exclude_same_domain=exclude_same_domain
        )

        text = f"## {concept_id}의 구조적 유사체\n\n"
        for analogy in analogies:
            text += f"""
### {analogy.concept_name} ({analogy.domain})

**구조적 유사성**: {analogy.similarity_score:.2f}

**공유 구조**:
{analogy.shared_structure}

**탐구 제안**:
> {analogy.exploration_suggestion}

---
"""

        return [TextContent(type="text", text=text)]

    @server.call_tool()
    async def evaluate_novelty(
        proposed_concept: str,
        foundations: List[str]
    ) -> List[TextContent]:
        """
        제안된 융합의 신규성 평가

        Args:
            proposed_concept: 제안된 새 개념 설명
            foundations: 기반이 되는 기존 개념들

        Returns:
            신규성 평가 결과
        """
        from src.server import fusion_engine

        evaluation = await fusion_engine.evaluate_novelty(
            proposed_concept=proposed_concept,
            foundations=foundations
        )

        text = f"""
## 신규성 평가

### 제안된 개념
{proposed_concept}

### 기반 개념들
{', '.join(foundations)}

### 평가 결과

**신규성 점수**: {evaluation.score:.2f}/1.0

**유사한 기존 개념**:
"""
        for similar in evaluation.similar_existing[:3]:
            text += f"- {similar.name}: 유사도 {similar.similarity:.2f}\n"

        text += f"""
**평가 의견**:
{evaluation.assessment}

**개선 제안**:
{evaluation.improvement_suggestions}
"""

        return [TextContent(type="text", text=text)]

    @server.call_tool()
    async def get_fusion_patterns(
        pattern_name: Optional[str] = None
    ) -> List[TextContent]:
        """
        7가지 융합 사고 패턴 정보 반환

        Args:
            pattern_name: 특정 패턴 이름 (선택, 없으면 전체)

        Returns:
            융합 패턴 정보
        """
        if pattern_name and pattern_name in FUSION_PATTERNS:
            patterns = {pattern_name: FUSION_PATTERNS[pattern_name]}
        else:
            patterns = FUSION_PATTERNS

        text = "## 7가지 융합 사고 패턴\n\n"
        for key, pattern in patterns.items():
            text += f"""
### {pattern['name']}

**설명**: {pattern['description']}

**예시**: {', '.join(pattern['examples'])}

**핵심 질문**: *{pattern['key_question']}*

---
"""

        return [TextContent(type="text", text=text)]


def _get_novelty_interpretation(score: float) -> str:
    """신규성 점수 해석"""
    if score >= 0.8:
        return "**매우 높은 신규성**: 기존에 없는 새로운 연결입니다. 이론적 기여 가능성이 높습니다."
    elif score >= 0.6:
        return "**높은 신규성**: 기존 연구에서 드물게 다뤄진 연결입니다. 깊이 탐구할 가치가 있습니다."
    elif score >= 0.4:
        return "**중간 신규성**: 일부 선행 연구가 있지만, 새로운 관점을 제시할 수 있습니다."
    elif score >= 0.2:
        return "**낮은 신규성**: 이미 많이 연구된 연결입니다. 차별화 전략이 필요합니다."
    else:
        return "**매우 낮은 신규성**: 잘 알려진 연결입니다. 새로운 각도를 찾아보세요."
