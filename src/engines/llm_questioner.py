"""
LLM-Based Socratic Question Generator - LLM 기반 소크라테스 질문 생성기

Claude/GPT를 활용한 맥락 인식 질문 생성
지식 베이스와 연동하여 깊이 있는 탐구 질문 제공
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class QuestionStrategy(Enum):
    """질문 전략"""
    CLARIFY = "clarify"           # 개념 명료화
    CHALLENGE = "challenge"       # 가정 도전
    EXPAND = "expand"            # 관점 확장
    CONNECT = "connect"          # 분야 연결
    DEEPEN = "deepen"           # 깊이 탐구
    SYNTHESIZE = "synthesize"    # 종합
    META = "meta"               # 메타 성찰


@dataclass
class GeneratedQuestion:
    """생성된 질문"""
    question: str
    strategy: QuestionStrategy
    purpose: str
    related_concepts: List[str]
    difficulty: int  # 1-5
    follow_ups: List[str]


@dataclass
class QuestionContext:
    """질문 생성 컨텍스트"""
    topic: str
    user_position: Optional[str]
    dialogue_history: List[Dict[str, str]]
    explored_concepts: List[str]
    knowledge_context: List[Dict[str, Any]]
    depth_level: int  # 1-5
    focus_areas: List[str]


class LLMQuestioner:
    """
    LLM 기반 소크라테스 질문 생성기

    핵심 원칙:
    1. 지식 베이스 컨텍스트 활용
    2. 대화 히스토리 기반 연속성
    3. 전략적 질문 선택
    4. 난이도 적응
    """

    # 질문 전략별 프롬프트 템플릿
    STRATEGY_PROMPTS = {
        QuestionStrategy.CLARIFY: """
사용자가 '{topic}'에 대해 탐구하고 있습니다.
현재 위치: {user_position}

명료화 질문을 생성하세요:
- 핵심 개념의 정확한 정의 유도
- 모호한 용어 명확화
- 경계 사례 탐구

관련 지식:
{knowledge_context}
""",
        QuestionStrategy.CHALLENGE: """
사용자가 다음 입장을 취하고 있습니다:
"{user_position}"

주제: {topic}

전제 도전 질문을 생성하세요:
- 숨겨진 가정 드러내기
- 반례 제시 유도
- 대안적 관점 탐색

관련 지식:
{knowledge_context}
""",
        QuestionStrategy.EXPAND: """
사용자가 '{topic}'를 탐구 중입니다.
현재까지 탐구한 개념: {explored_concepts}

관점 확장 질문을 생성하세요:
- 다른 학문 분야의 시각
- 역사적 관점
- 실용적 관점

관련 지식 (다른 분야):
{knowledge_context}
""",
        QuestionStrategy.CONNECT: """
주제: {topic}
현재 위치: {user_position}

분야 연결 질문을 생성하세요:
- 다른 분야의 유사 개념 연결
- 구조적 동형 발견
- 융합적 사고 유도

연결 가능한 개념들:
{knowledge_context}
""",
        QuestionStrategy.DEEPEN: """
사용자가 '{topic}'를 깊이 탐구 중입니다.
현재 깊이: {depth_level}/5
현재 위치: {user_position}

더 깊은 탐구 질문을 생성하세요:
- 근본 원리로 파고들기
- 논리적 결과 추적
- 존재론적/인식론적 탐구

심층 지식:
{knowledge_context}
""",
        QuestionStrategy.SYNTHESIZE: """
사용자가 다음 관점들을 탐구했습니다:
{explored_concepts}

주제: {topic}

종합 질문을 생성하세요:
- 대립되는 관점의 통합점
- 새로운 이해의 형성
- 변증법적 진전

관련 지식:
{knowledge_context}
""",
        QuestionStrategy.META: """
사용자가 '{topic}'를 탐구 중입니다.
대화 히스토리: {dialogue_history}

메타 성찰 질문을 생성하세요:
- 탐구 방향에 대한 성찰
- 왜 이것이 중요한지
- 우리가 진정으로 알고 싶은 것

이 탐구의 큰 맥락:
{knowledge_context}
"""
    }

    # 7가지 소크라테스 질문 유형 매핑
    SOCRATIC_TYPES = {
        "clarification": {
            "name": "명료화 질문",
            "indicators": ["정의", "의미", "구분", "특성"],
            "templates": [
                "'{concept}'라고 할 때 정확히 무엇을 의미하나요?",
                "이 맥락에서 '{concept}'를 어떻게 정의하시겠어요?",
                "'{concept}'와 '{related}'의 핵심 차이는 무엇인가요?"
            ]
        },
        "assumption": {
            "name": "전제 탐구",
            "indicators": ["가정", "전제", "당연시", "기본"],
            "templates": [
                "이 주장이 전제하고 있는 것은 무엇인가요?",
                "만약 그 전제가 거짓이라면 어떻게 될까요?",
                "왜 그것을 당연하게 받아들이나요?"
            ]
        },
        "evidence": {
            "name": "근거 질문",
            "indicators": ["증거", "이유", "근거", "지지"],
            "templates": [
                "그렇게 생각하는 근거는 무엇인가요?",
                "어떤 증거가 이 주장을 지지하나요?",
                "반대 증거가 있다면 어떻게 대응하시겠어요?"
            ]
        },
        "viewpoint": {
            "name": "관점 질문",
            "indicators": ["관점", "시각", "입장", "분야"],
            "templates": [
                "{domain}의 관점에서 이것을 어떻게 볼까요?",
                "반대 입장에서는 어떤 주장을 할까요?",
                "{thinker}라면 이것을 어떻게 볼까요?"
            ]
        },
        "implication": {
            "name": "함의 질문",
            "indicators": ["결과", "함의", "영향", "귀결"],
            "templates": [
                "이것이 참이라면 어떤 결과가 따를까요?",
                "이 생각을 끝까지 밀고 가면 어디에 도달하나요?",
                "실제로 적용된다면 어떤 영향이 있을까요?"
            ]
        },
        "meta": {
            "name": "메타 질문",
            "indicators": ["왜", "목적", "의미", "중요"],
            "templates": [
                "이 질문이 중요한 이유는 무엇일까요?",
                "우리가 진짜 알고 싶은 것은 무엇인가요?",
                "왜 이 문제에 관심을 갖게 되었나요?"
            ]
        },
        "bridge": {
            "name": "연결 질문",
            "indicators": ["연결", "관계", "유사", "패턴"],
            "templates": [
                "{domain_a}의 이 개념이 {domain_b}와 어떻게 연결될까요?",
                "다른 분야에서 비슷한 현상은 무엇일까요?",
                "이 패턴이 다른 곳에서도 나타날까요?"
            ]
        }
    }

    def __init__(self, rag_pipeline, llm_client=None):
        """
        Args:
            rag_pipeline: RAG 검색 파이프라인
            llm_client: LLM API 클라이언트 (선택, 없으면 템플릿 기반)
        """
        self.rag = rag_pipeline
        self.llm = llm_client
        self.use_llm = llm_client is not None

    async def generate_questions(
        self,
        context: QuestionContext,
        num_questions: int = 3,
        strategies: Optional[List[QuestionStrategy]] = None
    ) -> List[GeneratedQuestion]:
        """
        컨텍스트 기반 소크라테스 질문 생성

        Args:
            context: 질문 생성 컨텍스트
            num_questions: 생성할 질문 수
            strategies: 사용할 전략 (없으면 자동 선택)

        Returns:
            생성된 질문 목록
        """
        # 1. 전략 선택
        if not strategies:
            strategies = await self._select_strategies(context)

        # 2. 지식 컨텍스트 보강
        enriched_context = await self._enrich_context(context)

        # 3. 질문 생성
        questions = []
        for strategy in strategies[:num_questions]:
            if self.use_llm:
                q = await self._generate_with_llm(enriched_context, strategy)
            else:
                q = await self._generate_from_template(enriched_context, strategy)
            questions.append(q)

        # 4. 질문 정제 및 순서화
        questions = self._refine_questions(questions, context)

        return questions

    async def _select_strategies(
        self,
        context: QuestionContext
    ) -> List[QuestionStrategy]:
        """
        대화 상황에 맞는 질문 전략 자동 선택
        """
        strategies = []

        # 초기 탐구 단계
        if not context.dialogue_history:
            strategies.append(QuestionStrategy.CLARIFY)
            strategies.append(QuestionStrategy.EXPAND)

        # 사용자가 입장을 밝힌 경우
        if context.user_position:
            strategies.append(QuestionStrategy.CHALLENGE)
            strategies.append(QuestionStrategy.DEEPEN)

        # 여러 개념을 탐구한 경우
        if len(context.explored_concepts) >= 3:
            strategies.append(QuestionStrategy.CONNECT)
            strategies.append(QuestionStrategy.SYNTHESIZE)

        # 깊은 탐구 단계
        if context.depth_level >= 4:
            strategies.append(QuestionStrategy.META)

        # 기본 전략 추가
        if not strategies:
            strategies = [
                QuestionStrategy.CLARIFY,
                QuestionStrategy.EXPAND,
                QuestionStrategy.CONNECT
            ]

        return strategies

    async def _enrich_context(
        self,
        context: QuestionContext
    ) -> QuestionContext:
        """
        RAG를 통해 컨텍스트 보강
        """
        # 지식 베이스에서 관련 정보 검색
        knowledge_results = await self.rag.search(
            query=context.topic,
            limit=5
        )

        # 연결 가능한 다른 분야 개념 검색
        if context.user_position:
            cross_domain = await self.rag.search_metaphorical(
                concept=context.topic,
                target_domains=None  # 모든 분야
            )
            knowledge_results.extend(cross_domain[:3])

        # 컨텍스트 업데이트
        context.knowledge_context = [
            {
                "name": r.name,
                "domain": r.domain,
                "description": r.description[:300]
            }
            for r in knowledge_results
        ]

        return context

    async def _generate_with_llm(
        self,
        context: QuestionContext,
        strategy: QuestionStrategy
    ) -> GeneratedQuestion:
        """
        LLM을 사용한 질문 생성 (향후 구현)
        """
        # LLM API 호출 로직
        # 현재는 템플릿 기반으로 폴백
        return await self._generate_from_template(context, strategy)

    async def _generate_from_template(
        self,
        context: QuestionContext,
        strategy: QuestionStrategy
    ) -> GeneratedQuestion:
        """
        템플릿 기반 질문 생성
        """
        # 전략에 따른 질문 유형 매핑
        strategy_to_type = {
            QuestionStrategy.CLARIFY: "clarification",
            QuestionStrategy.CHALLENGE: "assumption",
            QuestionStrategy.EXPAND: "viewpoint",
            QuestionStrategy.CONNECT: "bridge",
            QuestionStrategy.DEEPEN: "implication",
            QuestionStrategy.SYNTHESIZE: "viewpoint",
            QuestionStrategy.META: "meta"
        }

        q_type = strategy_to_type.get(strategy, "clarification")
        type_info = self.SOCRATIC_TYPES[q_type]

        # 템플릿에서 질문 생성
        template = type_info["templates"][0]  # 첫 번째 템플릿 사용

        # 변수 치환
        question = template.format(
            concept=context.topic,
            related=context.explored_concepts[0] if context.explored_concepts else "관련 개념",
            domain=context.knowledge_context[0]["domain"] if context.knowledge_context else "다른 분야",
            domain_a=context.knowledge_context[0]["domain"] if context.knowledge_context else "분야 A",
            domain_b=context.knowledge_context[1]["domain"] if len(context.knowledge_context) > 1 else "분야 B",
            thinker="해당 분야의 전문가"
        )

        # 지식 컨텍스트 기반 관련 개념 추출
        related_concepts = [
            kc["name"] for kc in context.knowledge_context[:3]
        ]

        # 후속 질문 방향
        follow_ups = [
            f"이 정의의 경계 사례는 무엇인가요?",
            f"역사적으로 이 개념은 어떻게 변해왔나요?",
            f"다른 분야에서는 이것을 어떻게 이해하나요?"
        ]

        return GeneratedQuestion(
            question=question,
            strategy=strategy,
            purpose=type_info["name"],
            related_concepts=related_concepts,
            difficulty=context.depth_level,
            follow_ups=follow_ups
        )

    def _refine_questions(
        self,
        questions: List[GeneratedQuestion],
        context: QuestionContext
    ) -> List[GeneratedQuestion]:
        """
        생성된 질문 정제 및 순서화
        """
        # 난이도 순 정렬 (낮은 것부터)
        questions.sort(key=lambda q: q.difficulty)

        # 중복 제거
        seen = set()
        unique_questions = []
        for q in questions:
            if q.question not in seen:
                seen.add(q.question)
                unique_questions.append(q)

        return unique_questions


# 전역 질문 생성기 팩토리
def create_questioner(rag_pipeline, llm_client=None) -> LLMQuestioner:
    """질문 생성기 생성"""
    return LLMQuestioner(rag_pipeline, llm_client)
