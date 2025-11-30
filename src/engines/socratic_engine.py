"""
Socratic Engine - 소크라테스적 대화 엔진

소크라테스적 질문 생성, 전제 도전, 변증법적 종합
"""

from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class DialogueMode(Enum):
    SOCRATIC = "socratic"    # 항상 질문으로 응답
    DIRECT = "direct"        # 직접 답변
    HYBRID = "hybrid"        # 맥락에 따라


class QuestionType(Enum):
    CLARIFICATION = "clarification"
    ASSUMPTION = "assumption"
    EVIDENCE = "evidence"
    VIEWPOINT = "viewpoint"
    IMPLICATION = "implication"
    META = "meta"
    BRIDGE = "bridge"


@dataclass
class SocraticQuestion:
    question: str
    question_type: str
    purpose: str
    follow_up_directions: List[str]


@dataclass
class DialogueResponse:
    questions: List[SocraticQuestion]
    related_concepts: List[str]
    suggested_direction: str
    depth_level: str


@dataclass
class HiddenPremise:
    premise: str
    premise_type: str
    potential_issue: str
    challenge_question: str


@dataclass
class PremiseChallenge:
    hidden_premises: List[HiddenPremise]
    counter_perspective: Optional[str]
    alternative_views: List


@dataclass
class PositionInsight:
    position: str
    core_insight: str


@dataclass
class Synthesis:
    position_insights: List[PositionInsight]
    synthesis_attempt: str
    remaining_tensions: str
    deeper_questions: List[str]


class SocraticEngine:
    """
    소크라테스적 대화 엔진

    핵심 원칙:
    - 답을 주지 않고 질문을 통해 발견하게 함
    - 숨겨진 전제를 드러냄
    - 다양한 관점에서 바라보게 함
    - 논리적 결과를 추적하게 함
    """

    def __init__(self, rag_pipeline, fusion_engine):
        self.rag = rag_pipeline
        self.fusion = fusion_engine
        self.mode = DialogueMode.HYBRID
        self.dialogue_history = []

    def set_mode(self, mode: str):
        """대화 모드 설정"""
        self.mode = DialogueMode(mode)

    async def conduct_dialogue(
        self,
        topic: str,
        user_position: Optional[str] = None,
        depth: str = "medium",
        focus: str = "explore"
    ) -> DialogueResponse:
        """
        소크라테스적 대화 수행

        Args:
            topic: 탐구 주제
            user_position: 사용자의 현재 입장
            depth: shallow/medium/deep
            focus: explore/challenge/synthesize
        """
        # Get related concepts for context
        related_concepts = await self._get_related_concepts(topic)

        # Generate questions based on focus
        if focus == "explore":
            questions = await self._generate_exploration_questions(
                topic, user_position, depth, related_concepts
            )
        elif focus == "challenge":
            questions = await self._generate_challenge_questions(
                topic, user_position, depth, related_concepts
            )
        else:  # synthesize
            questions = await self._generate_synthesis_questions(
                topic, user_position, depth, related_concepts
            )

        # Determine suggested direction
        direction = self._suggest_direction(topic, questions, related_concepts)

        return DialogueResponse(
            questions=questions,
            related_concepts=[c.name for c in related_concepts],
            suggested_direction=direction,
            depth_level=depth
        )

    async def challenge_premise(
        self,
        statement: str,
        perspective: Optional[str] = None
    ) -> PremiseChallenge:
        """
        진술의 숨겨진 전제 도전

        소크라테스적 검토(elenchus)를 통해 숨겨진 가정을 드러내고 도전
        """
        # Extract hidden premises
        premises = await self._extract_hidden_premises(statement)

        # Get counter-perspective if specified
        counter = None
        if perspective:
            counter = await self._generate_counter_perspective(
                statement, perspective
            )

        # Find alternative views
        alternatives = await self._find_alternative_views(statement)

        return PremiseChallenge(
            hidden_premises=premises,
            counter_perspective=counter,
            alternative_views=alternatives
        )

    async def synthesize(
        self,
        topic: str,
        positions: List[str]
    ) -> Synthesis:
        """
        변증법적 종합 시도

        대립하는 입장들에서 각각의 통찰을 추출하고
        제3의 통합적 관점을 모색
        """
        # Extract core insights from each position
        insights = []
        for pos in positions:
            insight = await self._extract_core_insight(pos)
            insights.append(PositionInsight(
                position=pos[:50] + "..." if len(pos) > 50 else pos,
                core_insight=insight
            ))

        # Attempt synthesis
        synthesis = await self._attempt_synthesis(topic, insights)

        # Identify remaining tensions
        tensions = await self._identify_tensions(insights)

        # Generate deeper questions
        deeper_qs = await self._generate_deeper_questions(
            topic, insights, synthesis, tensions
        )

        return Synthesis(
            position_insights=insights,
            synthesis_attempt=synthesis,
            remaining_tensions=tensions,
            deeper_questions=deeper_qs
        )

    # Private helper methods

    async def _get_related_concepts(self, topic: str):
        """주제 관련 개념들 검색"""
        return await self.rag.search(query=topic, limit=5)

    async def _generate_exploration_questions(
        self,
        topic: str,
        user_position: Optional[str],
        depth: str,
        related_concepts
    ) -> List[SocraticQuestion]:
        """탐구형 질문 생성"""
        questions = []

        # 1. Clarification question
        questions.append(SocraticQuestion(
            question=f"'{topic}'에서 가장 핵심적인 개념은 무엇인가요? 그 개념을 어떻게 정의하시겠어요?",
            question_type="clarification",
            purpose="핵심 개념의 명확한 정의 도출",
            follow_up_directions=[
                "정의의 경계 사례 탐구",
                "다른 정의와 비교",
                "정의의 역사적 변천"
            ]
        ))

        # 2. Viewpoint question using related concepts
        if related_concepts:
            other_domain = related_concepts[0].domain
            questions.append(SocraticQuestion(
                question=f"{other_domain} 분야에서는 이 문제를 어떻게 바라볼까요?",
                question_type="viewpoint",
                purpose="다른 학문적 관점 탐색",
                follow_up_directions=[
                    f"{other_domain}의 핵심 개념 적용",
                    "분야 간 차이점과 공통점",
                    "융합적 관점의 가능성"
                ]
            ))

        # 3. Bridge question
        if len(related_concepts) >= 2:
            questions.append(SocraticQuestion(
                question=f"'{related_concepts[0].name}'과 '{related_concepts[1].name}'이 '{topic}'에서 만난다면 어떤 대화를 나눌까요?",
                question_type="bridge",
                purpose="분야 간 연결 탐색",
                follow_up_directions=[
                    "공통된 구조 찾기",
                    "상호 보완 가능성",
                    "새로운 융합 개념 도출"
                ]
            ))

        # Adjust depth
        if depth == "deep":
            questions.append(SocraticQuestion(
                question=f"이 주제를 탐구하는 것이 왜 중요한가요? 우리가 진정으로 알고 싶은 것은 무엇인가요?",
                question_type="meta",
                purpose="탐구의 목적과 의미 성찰",
                follow_up_directions=[
                    "개인적/학문적 동기 탐구",
                    "더 근본적인 질문으로 이동",
                    "실천적 함의 고려"
                ]
            ))

        return questions

    async def _generate_challenge_questions(
        self,
        topic: str,
        user_position: Optional[str],
        depth: str,
        related_concepts
    ) -> List[SocraticQuestion]:
        """도전형 질문 생성"""
        questions = []

        if user_position:
            # Challenge assumptions
            questions.append(SocraticQuestion(
                question=f"'{user_position[:30]}...'라고 하셨는데, 이 주장이 전제하는 것은 무엇인가요?",
                question_type="assumption",
                purpose="숨겨진 가정 드러내기",
                follow_up_directions=[
                    "전제의 타당성 검토",
                    "전제가 거짓일 경우의 결과",
                    "대안적 전제 탐색"
                ]
            ))

            # Challenge evidence
            questions.append(SocraticQuestion(
                question="이 입장을 지지하는 가장 강력한 증거는 무엇인가요? 그 증거는 얼마나 확실한가요?",
                question_type="evidence",
                purpose="근거의 강도 검토",
                follow_up_directions=[
                    "반대 증거 탐색",
                    "증거의 한계 인식",
                    "추가 증거 필요성"
                ]
            ))

        # Implication question
        questions.append(SocraticQuestion(
            question=f"이 생각을 끝까지 밀고 가면 어떤 결론에 도달하나요? 그 결론을 받아들일 수 있나요?",
            question_type="implication",
            purpose="논리적 결과 추적",
            follow_up_directions=[
                "극단적 사례 검토",
                "실제 적용 시 문제점",
                "수정이 필요한 부분"
            ]
        ))

        return questions

    async def _generate_synthesis_questions(
        self,
        topic: str,
        user_position: Optional[str],
        depth: str,
        related_concepts
    ) -> List[SocraticQuestion]:
        """종합형 질문 생성"""
        questions = []

        questions.append(SocraticQuestion(
            question="지금까지 탐구한 다양한 관점들에서 공통적으로 발견되는 것은 무엇인가요?",
            question_type="bridge",
            purpose="공통 패턴 발견",
            follow_up_directions=[
                "공통점의 의미",
                "차이점의 의미",
                "통합 가능성"
            ]
        ))

        questions.append(SocraticQuestion(
            question="서로 대립하는 것처럼 보이는 관점들을 모두 포괄하는 더 높은 관점이 있을까요?",
            question_type="viewpoint",
            purpose="변증법적 종합 시도",
            follow_up_directions=[
                "각 관점의 부분적 진리",
                "통합의 조건",
                "새로운 프레임 창조"
            ]
        ))

        if depth == "deep":
            questions.append(SocraticQuestion(
                question="이 탐구를 통해 발견한 것이 당신의 기존 생각을 어떻게 변화시켰나요?",
                question_type="meta",
                purpose="학습과 변화 성찰",
                follow_up_directions=[
                    "인식의 변화 지점",
                    "남은 불확실성",
                    "다음 탐구 방향"
                ]
            ))

        return questions

    async def _extract_hidden_premises(self, statement: str) -> List[HiddenPremise]:
        """숨겨진 전제 추출"""
        # This would use LLM to analyze statement
        # Placeholder implementation
        premises = [
            HiddenPremise(
                premise="진술에 내포된 가정이 분석됩니다",
                premise_type="존재론적 가정",
                potential_issue="이 가정이 보편적으로 성립하지 않을 수 있음",
                challenge_question="이 가정이 성립하지 않는 경우는 어떤 경우인가요?"
            )
        ]
        return premises

    async def _generate_counter_perspective(
        self,
        statement: str,
        perspective: str
    ) -> str:
        """반대 관점 생성"""
        return f"{perspective}의 관점에서 보면, 이 진술은 다른 해석이 가능합니다."

    async def _find_alternative_views(self, statement: str) -> List:
        """대안적 관점 탐색"""
        return []

    async def _extract_core_insight(self, position: str) -> str:
        """입장에서 핵심 통찰 추출"""
        return f"이 입장의 핵심은 특정한 가치나 원리를 강조합니다."

    async def _attempt_synthesis(
        self,
        topic: str,
        insights: List[PositionInsight]
    ) -> str:
        """종합 시도"""
        return f"""
각 입장이 포착하는 부분적 진리를 인정하면서,
이들을 포괄하는 더 통합적인 관점을 구성할 수 있습니다.

핵심은 대립을 '이것 아니면 저것'으로 보지 않고,
'이것과 저것의 관계'로 재구성하는 것입니다.
"""

    async def _identify_tensions(
        self,
        insights: List[PositionInsight]
    ) -> str:
        """남은 긴장 식별"""
        return "완전한 종합에 이르지 못한 긴장 지점들이 남아있으며, 이는 더 깊은 탐구의 출발점이 됩니다."

    async def _generate_deeper_questions(
        self,
        topic: str,
        insights: List[PositionInsight],
        synthesis: str,
        tensions: str
    ) -> List[str]:
        """더 깊은 질문 생성"""
        return [
            "종합이 불가능해 보이는 지점에서, 우리가 놓치고 있는 것은 무엇인가요?",
            "이 긴장 자체가 우리에게 말해주는 것은 무엇인가요?",
            "이 탐구가 열어주는 새로운 질문은 무엇인가요?"
        ]

    def _suggest_direction(
        self,
        topic: str,
        questions: List[SocraticQuestion],
        related_concepts
    ) -> str:
        """탐구 방향 제안"""
        if related_concepts:
            domains = set(c.domain for c in related_concepts)
            return f"""
다음 탐구 방향을 제안합니다:

1. **개념 명료화**: '{topic}'의 핵심 개념을 더 정확히 정의하기
2. **분야 간 대화**: {', '.join(list(domains)[:3])} 관점에서 바라보기
3. **전제 검토**: 당연시되는 가정들을 드러내고 검토하기
4. **함의 추적**: 이 생각이 이끄는 결론을 끝까지 따라가기

"검증되지 않은 삶은 살 가치가 없다" - 소크라테스
"""
        return "개념을 명료화하고 숨겨진 전제를 드러내는 것부터 시작하세요."
