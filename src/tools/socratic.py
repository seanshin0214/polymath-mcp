"""
Socratic Tools - 소크라테스적 대화 도구

소크라테스적 질문, 전제 도전, 대화 관리 등
"""

from typing import List, Optional
from mcp.server import Server
from mcp.types import TextContent

from src.models.dialogue import DialogueState, SocraticQuestion


# 7가지 소크라테스적 질문 유형
SOCRATIC_QUESTION_TYPES = {
    "clarification": {
        "name": "명료화 질문 (Clarification)",
        "description": "개념의 정확한 의미 탐구",
        "examples": [
            "'{concept}'이라고 할 때 정확히 무엇을 의미하나요?",
            "이 맥락에서 '{concept}'를 어떻게 정의하시겠어요?",
            "'{concept}'의 핵심 특성은 무엇인가요?"
        ],
        "purpose": "모호한 개념을 명확히 정의"
    },
    "assumption": {
        "name": "전제 탐구 질문 (Assumption Probing)",
        "description": "숨겨진 가정과 전제 노출",
        "examples": [
            "이 주장의 전제는 무엇인가요?",
            "'{concept}'이 항상 참이라고 가정하는 이유는?",
            "만약 그 전제가 거짓이라면 어떻게 될까요?"
        ],
        "purpose": "당연시되는 가정을 드러내고 검토"
    },
    "evidence": {
        "name": "증거/이유 질문 (Evidence/Reasoning)",
        "description": "주장을 뒷받침하는 근거 탐구",
        "examples": [
            "그렇게 생각하는 근거는 무엇인가요?",
            "어떤 증거가 이 주장을 지지하나요?",
            "다른 설명은 가능하지 않을까요?"
        ],
        "purpose": "논리적 근거와 증거 검토"
    },
    "viewpoint": {
        "name": "관점/시각 질문 (Viewpoint)",
        "description": "다른 관점에서 바라보기",
        "examples": [
            "{other_domain}의 관점에서 이것을 어떻게 볼까요?",
            "반대 입장에서는 어떤 주장을 할까요?",
            "{thinker}라면 이것을 어떻게 볼까요?"
        ],
        "purpose": "다양한 관점 탐색으로 시야 확장"
    },
    "implication": {
        "name": "함의/결과 질문 (Implication)",
        "description": "논리적 결과와 영향 탐구",
        "examples": [
            "이것이 참이라면 어떤 결과가 따를까요?",
            "이 아이디어를 끝까지 밀고 가면 어디에 도달할까요?",
            "실제로 적용된다면 어떤 영향이 있을까요?"
        ],
        "purpose": "아이디어의 논리적 결과 추적"
    },
    "meta": {
        "name": "메타 질문 (Meta-Question)",
        "description": "질문 자체에 대한 질문",
        "examples": [
            "이 질문이 중요한 이유는 무엇일까요?",
            "우리가 진짜 알고 싶은 것은 무엇인가요?",
            "왜 이 문제에 관심을 갖게 되었나요?"
        ],
        "purpose": "탐구의 방향과 목적 성찰"
    },
    "bridge": {
        "name": "연결 질문 (Bridge Question)",
        "description": "분야 간 연결점 탐색",
        "examples": [
            "{domain_a}의 이 개념이 {domain_b}와 어떻게 연결될까요?",
            "다른 분야에서 비슷한 현상은 무엇일까요?",
            "이 패턴이 다른 곳에서도 나타날까요?"
        ],
        "purpose": "융합적 사고 촉진"
    }
}


def register_socratic_tools(server: Server):
    """Register Socratic dialogue tools with the MCP server"""

    @server.call_tool()
    async def socratic_dialogue(
        topic: str,
        user_position: Optional[str] = None,
        depth: str = "medium",
        focus: str = "explore"
    ) -> List[TextContent]:
        """
        소크라테스적 대화 시작 또는 계속

        Args:
            topic: 탐구할 주제
            user_position: 사용자의 현재 입장/아이디어 (선택)
            depth: 탐구 깊이 (shallow/medium/deep)
            focus: 대화 초점 (explore/challenge/synthesize)

        Returns:
            소크라테스적 질문과 탐구 방향
        """
        from src.server import socratic_engine

        response = await socratic_engine.conduct_dialogue(
            topic=topic,
            user_position=user_position,
            depth=depth,
            focus=focus
        )

        text = f"""
## 소크라테스적 탐구: {topic}

### 현재 위치
{user_position or "(아직 정의되지 않음)"}

### 탐구 질문

"""
        for i, question in enumerate(response.questions, 1):
            q_type = SOCRATIC_QUESTION_TYPES.get(question.question_type, {})
            text += f"""
**질문 {i}** ({q_type.get('name', question.question_type)})

> {question.question}

*목적*: {q_type.get('purpose', '')}

"""

        text += f"""
### 관련 개념들
{', '.join(response.related_concepts[:5])}

### 추천 탐구 방향
{response.suggested_direction}
"""

        return [TextContent(type="text", text=text)]

    @server.call_tool()
    async def challenge_premise(
        statement: str,
        perspective: Optional[str] = None
    ) -> List[TextContent]:
        """
        진술의 숨겨진 전제 도전

        Args:
            statement: 도전할 진술
            perspective: 도전할 관점 (선택)

        Returns:
            드러난 전제와 도전 질문들
        """
        from src.server import socratic_engine

        challenge = await socratic_engine.challenge_premise(
            statement=statement,
            perspective=perspective
        )

        text = f"""
## 전제 도전: "{statement[:50]}..."

### 발견된 숨겨진 전제들

"""
        for i, premise in enumerate(challenge.hidden_premises, 1):
            text += f"""
**전제 {i}**: {premise.premise}

- **유형**: {premise.premise_type}
- **문제점**: {premise.potential_issue}
- **도전 질문**: *{premise.challenge_question}*

"""

        if perspective:
            text += f"""
### {perspective} 관점에서의 반론

{challenge.counter_perspective}

"""

        text += f"""
### 대안적 관점들

"""
        for alt in challenge.alternative_views[:3]:
            text += f"- **{alt.name}**: {alt.description}\n"

        return [TextContent(type="text", text=text)]

    @server.call_tool()
    async def get_question_types(
        type_name: Optional[str] = None
    ) -> List[TextContent]:
        """
        7가지 소크라테스적 질문 유형 정보 반환

        Args:
            type_name: 특정 유형 이름 (선택, 없으면 전체)

        Returns:
            질문 유형 정보
        """
        if type_name and type_name in SOCRATIC_QUESTION_TYPES:
            types = {type_name: SOCRATIC_QUESTION_TYPES[type_name]}
        else:
            types = SOCRATIC_QUESTION_TYPES

        text = "## 7가지 소크라테스적 질문 유형\n\n"
        for key, q_type in types.items():
            text += f"""
### {q_type['name']}

**설명**: {q_type['description']}

**목적**: {q_type['purpose']}

**예시 질문**:
"""
            for example in q_type['examples']:
                text += f"- {example}\n"
            text += "\n---\n"

        return [TextContent(type="text", text=text)]

    @server.call_tool()
    async def synthesize_dialogue(
        topic: str,
        positions: List[str]
    ) -> List[TextContent]:
        """
        대립하는 입장들의 변증법적 종합 시도

        Args:
            topic: 주제
            positions: 다양한 입장들

        Returns:
            종합 시도와 새로운 질문
        """
        from src.server import socratic_engine

        synthesis = await socratic_engine.synthesize(
            topic=topic,
            positions=positions
        )

        text = f"""
## 변증법적 종합: {topic}

### 제시된 입장들

"""
        for i, pos in enumerate(positions, 1):
            text += f"{i}. {pos}\n"

        text += f"""
### 각 입장의 핵심 통찰

"""
        for insight in synthesis.position_insights:
            text += f"- **{insight.position}**: {insight.core_insight}\n"

        text += f"""
### 종합 시도

{synthesis.synthesis_attempt}

### 남은 긴장

{synthesis.remaining_tensions}

### 더 깊은 탐구를 위한 질문

"""
        for q in synthesis.deeper_questions[:3]:
            text += f"> {q}\n\n"

        return [TextContent(type="text", text=text)]

    @server.call_tool()
    async def set_dialogue_mode(
        mode: str
    ) -> List[TextContent]:
        """
        대화 모드 설정

        Args:
            mode: socratic (항상 질문), direct (직접 답변), hybrid (맥락 따라)

        Returns:
            설정 확인
        """
        from src.server import socratic_engine

        socratic_engine.set_mode(mode)

        mode_descriptions = {
            "socratic": "소크라테스 모드: 항상 질문으로 응답하여 스스로 답을 찾도록 유도합니다.",
            "direct": "직접 모드: 요청에 따라 직접적인 답변을 제공합니다.",
            "hybrid": "하이브리드 모드: 맥락에 따라 질문과 답변을 적절히 혼합합니다."
        }

        return [TextContent(
            type="text",
            text=f"""
## 대화 모드 변경

**새 모드**: {mode}

{mode_descriptions.get(mode, "")}

소크라테스적 대화의 핵심은 답을 알려주는 것이 아니라,
올바른 질문을 통해 스스로 진리를 발견하도록 돕는 것입니다.

> "나는 아무것도 가르치지 않는다. 나는 단지 생각하게 만들 뿐이다." - 소크라테스
"""
        )]
