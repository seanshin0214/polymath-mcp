"""
Socratic Engine V2 - 소크라테스 대화 엔진 풀버전

모든 컴포넌트를 통합한 완전한 소크라테스식 학습 시스템
- LLM 기반 동적 질문 생성
- 세션 상태 관리
- 학습 경로 추천
- 적응형 난이도 조절
"""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from src.engines.llm_questioner import (
    LLMQuestioner,
    QuestionContext,
    QuestionStrategy,
    GeneratedQuestion
)
from src.engines.session_manager import (
    SessionManager,
    Session,
    get_session_manager
)
from src.engines.learning_path import (
    LearningPathGenerator,
    LearningPath,
    PathType,
    PathStep
)
from src.engines.adaptive_difficulty import (
    AdaptiveDifficultyEngine,
    ResponseAnalysis,
    DifficultySettings,
    get_difficulty_engine
)
from src.models.dialogue import (
    DialogueMode,
    DialogueFocus,
    DepthLevel,
    SocraticQuestion,
    DialogueTurn
)


@dataclass
class SocraticResponse:
    """소크라테스 대화 응답"""
    session_id: str
    questions: List[GeneratedQuestion]
    context_summary: str
    learning_path_suggestion: Optional[str]
    difficulty_feedback: str
    encouragement: str
    next_step_hint: str
    related_concepts: List[str]
    progress_update: Dict[str, Any]


class SocraticEngineV2:
    """
    소크라테스 대화 엔진 V2 (풀버전)

    핵심 철학:
    "나는 아무것도 가르치지 않는다. 나는 단지 생각하게 만들 뿐이다." - 소크라테스

    기능:
    1. 맥락 인식 질문 생성
    2. 세션 기반 대화 관리
    3. 학습 경로 추천
    4. 적응형 난이도 조절
    5. 통찰 추적 및 기록
    """

    def __init__(self, rag_pipeline, fusion_engine=None):
        """
        Args:
            rag_pipeline: RAG 검색 파이프라인
            fusion_engine: 융합 엔진 (선택)
        """
        self.rag = rag_pipeline
        self.fusion = fusion_engine

        # 서브 시스템 초기화
        self.questioner = LLMQuestioner(rag_pipeline)
        self.session_mgr = get_session_manager()
        self.path_generator = LearningPathGenerator(rag_pipeline)
        self.difficulty_engine = get_difficulty_engine()

        # 대화 모드
        self.mode = DialogueMode.HYBRID

    def set_mode(self, mode: str):
        """대화 모드 설정"""
        self.mode = DialogueMode(mode)

    async def start_dialogue(
        self,
        topic: str,
        user_id: str = "default",
        initial_position: Optional[str] = None,
        focus: str = "explore",
        depth: str = "medium"
    ) -> SocraticResponse:
        """
        새로운 소크라테스 대화 시작

        Args:
            topic: 탐구 주제
            user_id: 사용자 ID
            initial_position: 사용자의 초기 입장
            focus: explore/challenge/synthesize
            depth: shallow/medium/deep

        Returns:
            소크라테스 응답 (질문들 포함)
        """
        # 1. 세션 생성
        session = self.session_mgr.create_session(
            topic=topic,
            user_id=user_id,
            focus=DialogueFocus(focus),
            depth=DepthLevel(depth),
            tags=[topic, focus]
        )

        # 2. 난이도 설정 가져오기
        difficulty = self.difficulty_engine.get_difficulty_settings(
            user_id, topic
        )

        # 3. 질문 컨텍스트 구성
        knowledge_context = await self._get_knowledge_context(topic)

        context = QuestionContext(
            topic=topic,
            user_position=initial_position,
            dialogue_history=[],
            explored_concepts=[],
            knowledge_context=knowledge_context,
            depth_level=difficulty.question_complexity,
            focus_areas=[focus]
        )

        # 4. 질문 생성
        questions = await self.questioner.generate_questions(
            context,
            num_questions=3,
            strategies=self._select_initial_strategies(focus)
        )

        # 5. 학습 경로 제안
        path_suggestion = await self._generate_path_suggestion(
            topic, user_id, difficulty.question_complexity
        )

        # 6. 세션에 첫 턴 기록
        socratic_questions = [
            SocraticQuestion(
                question=q.question,
                question_type=q.strategy.value,
                purpose=q.purpose,
                follow_up_directions=q.follow_ups
            )
            for q in questions
        ]

        self.session_mgr.add_turn(
            session_id=session.metadata.session_id,
            speaker="polymath",
            content=f"'{topic}'에 대한 소크라테스적 탐구를 시작합니다.",
            questions=socratic_questions,
            related_concepts=[c["name"] for c in knowledge_context[:3]]
        )

        # 7. 응답 구성
        return SocraticResponse(
            session_id=session.metadata.session_id,
            questions=questions,
            context_summary=self._create_context_summary(knowledge_context),
            learning_path_suggestion=path_suggestion,
            difficulty_feedback=f"현재 난이도: {difficulty.question_complexity}/5",
            encouragement="함께 탐구를 시작해볼까요?",
            next_step_hint=self._generate_next_step_hint(questions[0] if questions else None),
            related_concepts=[c["name"] for c in knowledge_context[:5]],
            progress_update={
                "session_started": True,
                "topic": topic,
                "focus": focus,
                "depth": depth
            }
        )

    async def continue_dialogue(
        self,
        session_id: str,
        user_response: str,
        user_id: str = "default"
    ) -> SocraticResponse:
        """
        진행 중인 대화 계속

        Args:
            session_id: 세션 ID
            user_response: 사용자 응답
            user_id: 사용자 ID

        Returns:
            다음 소크라테스 응답
        """
        # 1. 세션 조회
        session = self.session_mgr.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # 2. 사용자 응답 분석
        analysis = self.difficulty_engine.analyze_response(
            response=user_response,
            question_difficulty=session.progress.depth_reached,
            time_taken=60,  # 실제로는 측정 필요
            expected_concepts=session.progress.concepts_explored[-3:]
        )

        # 3. 프로필 업데이트
        self.difficulty_engine.update_profile(
            user_id,
            analysis,
            session.dialogue.topic
        )

        # 4. 난이도 조정
        new_difficulty = self._adjust_difficulty(session, analysis)

        # 5. 사용자 턴 기록
        insights = self._extract_insights(user_response)
        self.session_mgr.add_turn(
            session_id=session_id,
            speaker="user",
            content=user_response,
            insights=insights
        )

        # 6. 통찰 기록
        for insight in insights:
            self.session_mgr.add_insight(session_id, insight)

        # 7. 현재 위치 업데이트
        self.session_mgr.update_position(session_id, user_response[:200])

        # 8. 다음 질문 생성
        knowledge_context = await self._get_knowledge_context(
            session.dialogue.topic,
            exclude=session.progress.concepts_explored
        )

        context = QuestionContext(
            topic=session.dialogue.topic,
            user_position=user_response,
            dialogue_history=self._get_dialogue_history(session),
            explored_concepts=session.progress.concepts_explored,
            knowledge_context=knowledge_context,
            depth_level=new_difficulty,
            focus_areas=[session.dialogue.focus.value]
        )

        strategies = self._select_follow_up_strategies(analysis, session)
        questions = await self.questioner.generate_questions(
            context,
            num_questions=2,
            strategies=strategies
        )

        # 9. 폴리매스 턴 기록
        socratic_questions = [
            SocraticQuestion(
                question=q.question,
                question_type=q.strategy.value,
                purpose=q.purpose,
                follow_up_directions=q.follow_ups
            )
            for q in questions
        ]

        self.session_mgr.add_turn(
            session_id=session_id,
            speaker="polymath",
            content="탐구를 계속합니다.",
            questions=socratic_questions,
            related_concepts=[c["name"] for c in knowledge_context[:3]]
        )

        # 10. 격려 메시지
        encouragement = self.difficulty_engine.get_encouragement_message(
            analysis, user_id
        )

        # 11. 진행 상황
        progress = self.session_mgr.get_session_summary(session_id)

        return SocraticResponse(
            session_id=session_id,
            questions=questions,
            context_summary=self._create_response_summary(analysis),
            learning_path_suggestion=None,
            difficulty_feedback=f"난이도 조정: {analysis.suggested_adjustment:+d}",
            encouragement=encouragement,
            next_step_hint=self._generate_next_step_hint(
                questions[0] if questions else None,
                analysis
            ),
            related_concepts=[c["name"] for c in knowledge_context[:5]],
            progress_update=progress
        )

    async def challenge_statement(
        self,
        session_id: str,
        statement: str,
        perspective: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        진술의 전제 도전

        Args:
            session_id: 세션 ID
            statement: 도전할 진술
            perspective: 특정 관점

        Returns:
            전제 분석 및 도전 질문들
        """
        session = self.session_mgr.get_session(session_id)

        # 숨겨진 전제 추출
        hidden_premises = self._extract_hidden_premises(statement)

        # 도전 질문 생성
        challenge_questions = []
        for premise in hidden_premises:
            challenge_questions.append({
                "premise": premise["premise"],
                "type": premise["type"],
                "challenge": premise["challenge"],
                "alternative": premise["alternative"]
            })

        # 다른 관점에서의 반론
        counter_perspectives = []
        if perspective:
            counter_perspectives = await self._generate_counter_perspective(
                statement, perspective
            )
        else:
            # 기본적으로 3가지 다른 관점
            counter_perspectives = await self._generate_multiple_perspectives(
                statement
            )

        # 전제 도전 기록
        if session:
            self.session_mgr.challenge_premise(session_id, statement)

        return {
            "original_statement": statement,
            "hidden_premises": challenge_questions,
            "counter_perspectives": counter_perspectives,
            "synthesis_question": f"이러한 다양한 관점들을 어떻게 통합할 수 있을까요?"
        }

    async def synthesize_dialogue(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        대화 종합

        Args:
            session_id: 세션 ID

        Returns:
            종합된 통찰과 남은 질문들
        """
        session = self.session_mgr.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # 탐구한 개념들
        concepts = session.progress.concepts_explored

        # 도출된 통찰들
        insights = session.progress.insights_gained

        # 발견된 연결들
        connections = session.progress.connections_made

        # 종합 시도
        synthesis = self._create_synthesis(concepts, insights, connections)

        # 남은 긴장과 질문
        remaining_tensions = self._identify_remaining_tensions(session)
        deeper_questions = self._generate_deeper_questions(session, synthesis)

        # 세션 완료 처리 (선택적)
        # self.session_mgr.complete_session(session_id)

        return {
            "topic": session.dialogue.topic,
            "explored_concepts": concepts,
            "key_insights": insights[-5:],  # 최근 5개
            "connections_discovered": connections,
            "synthesis": synthesis,
            "remaining_tensions": remaining_tensions,
            "deeper_questions": deeper_questions,
            "session_summary": self.session_mgr.get_session_summary(session_id)
        }

    async def get_learning_path(
        self,
        user_id: str,
        start_concept: str,
        path_type: str = "spiral",
        goal: Optional[str] = None
    ) -> LearningPath:
        """
        학습 경로 생성

        Args:
            user_id: 사용자 ID
            start_concept: 시작 개념
            path_type: 경로 유형
            goal: 목표 개념

        Returns:
            학습 경로
        """
        profile = self.difficulty_engine.get_or_create_profile(user_id)

        return await self.path_generator.generate_path(
            start_concept=start_concept,
            goal=goal,
            path_type=PathType(path_type),
            user_level=profile.current_level,
            max_steps=7
        )

    async def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """
        사용자 학습 진행 상황

        Args:
            user_id: 사용자 ID

        Returns:
            진행 상황 요약
        """
        # 난이도 엔진에서 성과 요약
        performance = self.difficulty_engine.get_performance_summary(user_id)

        # 세션 목록
        sessions = self.session_mgr.list_sessions(user_id)

        # 총 통계
        total_concepts = set()
        total_insights = 0
        total_connections = 0

        for session_info in sessions:
            session = self.session_mgr.get_session(session_info["session_id"])
            if session:
                total_concepts.update(session.progress.concepts_explored)
                total_insights += len(session.progress.insights_gained)
                total_connections += len(session.progress.connections_made)

        return {
            "performance": performance,
            "sessions": {
                "total": len(sessions),
                "active": len([s for s in sessions if s["status"] == "active"]),
                "completed": len([s for s in sessions if s["status"] == "completed"])
            },
            "learning": {
                "concepts_explored": len(total_concepts),
                "insights_gained": total_insights,
                "connections_made": total_connections
            },
            "recent_sessions": sessions[:5]
        }

    # ===== Private Helper Methods =====

    async def _get_knowledge_context(
        self,
        topic: str,
        exclude: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """지식 컨텍스트 검색"""
        results = await self.rag.search(query=topic, limit=10)

        context = []
        for r in results:
            if exclude and r.name in exclude:
                continue
            context.append({
                "name": r.name,
                "domain": r.domain,
                "description": r.description[:300] if hasattr(r, 'description') else ""
            })

        return context[:7]

    def _select_initial_strategies(
        self,
        focus: str
    ) -> List[QuestionStrategy]:
        """초기 질문 전략 선택"""
        if focus == "explore":
            return [
                QuestionStrategy.CLARIFY,
                QuestionStrategy.EXPAND,
                QuestionStrategy.CONNECT
            ]
        elif focus == "challenge":
            return [
                QuestionStrategy.CHALLENGE,
                QuestionStrategy.DEEPEN,
                QuestionStrategy.META
            ]
        else:  # synthesize
            return [
                QuestionStrategy.CONNECT,
                QuestionStrategy.SYNTHESIZE,
                QuestionStrategy.META
            ]

    def _select_follow_up_strategies(
        self,
        analysis: ResponseAnalysis,
        session: Session
    ) -> List[QuestionStrategy]:
        """후속 질문 전략 선택"""
        strategies = []

        # 응답 품질에 따른 전략
        if analysis.quality.value >= 4:
            strategies.append(QuestionStrategy.DEEPEN)
        elif analysis.quality.value <= 2:
            strategies.append(QuestionStrategy.CLARIFY)

        # 돌파구 신호가 있으면 연결 탐색
        if analysis.breakthrough_signals:
            strategies.append(QuestionStrategy.CONNECT)

        # 충분히 탐구했으면 종합
        if len(session.progress.concepts_explored) >= 3:
            strategies.append(QuestionStrategy.SYNTHESIZE)

        # 기본 전략 추가
        if len(strategies) < 2:
            strategies.extend([
                QuestionStrategy.EXPAND,
                QuestionStrategy.CONNECT
            ])

        return strategies[:3]

    def _adjust_difficulty(
        self,
        session: Session,
        analysis: ResponseAnalysis
    ) -> int:
        """난이도 조정"""
        current = session.progress.depth_reached
        adjustment = analysis.suggested_adjustment

        new_level = max(1, min(5, current + adjustment))
        self.session_mgr.set_depth(session.metadata.session_id, new_level)

        return new_level

    def _extract_insights(self, response: str) -> List[str]:
        """응답에서 통찰 추출"""
        insights = []

        # 통찰 지표 키워드
        insight_markers = [
            "깨달", "발견", "연결", "관계", "이해하게",
            "새롭게", "다르게 보", "결국", "핵심은"
        ]

        sentences = response.split(".")
        for sentence in sentences:
            if any(marker in sentence for marker in insight_markers):
                insights.append(sentence.strip())

        return insights[:3]  # 최대 3개

    def _get_dialogue_history(
        self,
        session: Session
    ) -> List[Dict[str, str]]:
        """대화 히스토리 추출"""
        history = []
        for turn in session.dialogue.turns[-6:]:  # 최근 6턴
            history.append({
                "speaker": turn.speaker,
                "content": turn.content[:200]
            })
        return history

    def _create_context_summary(
        self,
        knowledge_context: List[Dict[str, Any]]
    ) -> str:
        """컨텍스트 요약 생성"""
        if not knowledge_context:
            return "관련 지식을 검색 중입니다..."

        domains = list(set(c["domain"] for c in knowledge_context))
        concepts = [c["name"] for c in knowledge_context[:3]]

        return f"관련 분야: {', '.join(domains[:3])} | 연결 개념: {', '.join(concepts)}"

    def _create_response_summary(self, analysis: ResponseAnalysis) -> str:
        """응답 분석 요약"""
        quality_text = {
            5: "훌륭한 통찰",
            4: "좋은 이해",
            3: "기본적 파악",
            2: "부분적 이해",
            1: "탐구 필요"
        }

        summary = quality_text.get(analysis.quality.value, "분석 중")

        if analysis.breakthrough_signals:
            summary += " | 돌파구 발견!"
        if analysis.confusion_signals:
            summary += " | 추가 설명 필요"

        return summary

    def _generate_next_step_hint(
        self,
        question: Optional[GeneratedQuestion],
        analysis: Optional[ResponseAnalysis] = None
    ) -> str:
        """다음 단계 힌트"""
        if not question:
            return "다음 질문을 생각해보세요."

        hints = {
            QuestionStrategy.CLARIFY: "개념의 정확한 의미를 생각해보세요.",
            QuestionStrategy.CHALLENGE: "당연하게 여겨지는 것에 의문을 품어보세요.",
            QuestionStrategy.EXPAND: "다른 분야에서 비슷한 것을 찾아보세요.",
            QuestionStrategy.CONNECT: "개념들 사이의 다리를 찾아보세요.",
            QuestionStrategy.DEEPEN: "더 근본적인 원리로 내려가보세요.",
            QuestionStrategy.SYNTHESIZE: "대립되는 관점들의 공통점을 찾아보세요.",
            QuestionStrategy.META: "왜 이것이 중요한지 생각해보세요."
        }

        return hints.get(question.strategy, "깊이 생각해보세요.")

    async def _generate_path_suggestion(
        self,
        topic: str,
        user_id: str,
        level: int
    ) -> str:
        """학습 경로 제안"""
        profile = self.difficulty_engine.get_or_create_profile(user_id)

        if level <= 2:
            return f"'{topic}'의 기초부터 차근차근 탐구하는 것을 추천합니다."
        elif level <= 4:
            return f"'{topic}'와 관련 개념들의 연결을 탐색해보세요."
        else:
            return f"'{topic}'의 심층적 도전과 미해결 문제를 탐구해보세요."

    def _extract_hidden_premises(self, statement: str) -> List[Dict[str, str]]:
        """숨겨진 전제 추출"""
        # 기본 분석 (실제로는 LLM 사용)
        premises = [
            {
                "premise": "이 진술이 가정하는 존재론적 전제",
                "type": "존재론적",
                "challenge": "이것이 반드시 존재해야 하는가?",
                "alternative": "다른 존재론적 가정에서 출발하면?"
            },
            {
                "premise": "이 진술이 가정하는 인식론적 전제",
                "type": "인식론적",
                "challenge": "우리는 이것을 어떻게 알 수 있는가?",
                "alternative": "다른 방법으로 알 수 있다면?"
            },
            {
                "premise": "이 진술에 내포된 가치 판단",
                "type": "가치론적",
                "challenge": "왜 이것이 중요한가?",
                "alternative": "다른 가치 체계에서 보면?"
            }
        ]
        return premises

    async def _generate_counter_perspective(
        self,
        statement: str,
        perspective: str
    ) -> List[Dict[str, str]]:
        """특정 관점에서의 반론 생성"""
        return [{
            "perspective": perspective,
            "counter_argument": f"{perspective}의 관점에서 보면, 이 진술은 다른 해석이 가능합니다.",
            "key_insight": f"{perspective}이 강조하는 가치는 다른 측면을 조명합니다."
        }]

    async def _generate_multiple_perspectives(
        self,
        statement: str
    ) -> List[Dict[str, str]]:
        """다양한 관점 생성"""
        perspectives = [
            {
                "perspective": "실용주의적 관점",
                "counter_argument": "실제 결과와 유용성에 초점을 맞추면?",
                "key_insight": "진리는 그것이 작동하는지에 의해 검증됩니다."
            },
            {
                "perspective": "비판적 관점",
                "counter_argument": "누구의 이익에 봉사하는 주장인가?",
                "key_insight": "모든 주장에는 권력 관계가 내포되어 있습니다."
            },
            {
                "perspective": "역사적 관점",
                "counter_argument": "이 생각은 어떤 역사적 맥락에서 나왔는가?",
                "key_insight": "개념은 시대에 따라 다르게 이해됩니다."
            }
        ]
        return perspectives

    def _create_synthesis(
        self,
        concepts: List[str],
        insights: List[str],
        connections: List[Dict[str, str]]
    ) -> str:
        """종합 생성"""
        if not concepts:
            return "아직 충분한 탐구가 이루어지지 않았습니다."

        synthesis_parts = []

        if concepts:
            synthesis_parts.append(
                f"탐구한 개념들({', '.join(concepts[:3])})은 "
                "서로 깊은 연결을 가지고 있습니다."
            )

        if insights:
            synthesis_parts.append(
                f"핵심 통찰: {insights[-1]}"
            )

        if connections:
            conn = connections[-1]
            synthesis_parts.append(
                f"특히 {conn.get('from', '')}과 {conn.get('to', '')}의 "
                f"연결({conn.get('type', '')})이 중요합니다."
            )

        return " ".join(synthesis_parts) if synthesis_parts else \
            "탐구를 통해 개념들 사이의 연결을 발견했습니다."

    def _identify_remaining_tensions(self, session: Session) -> List[str]:
        """남은 긴장 식별"""
        return [
            "완전히 해결되지 않은 대립 관점이 남아있습니다.",
            "더 깊은 탐구가 필요한 영역이 있습니다.",
            "새로운 질문들이 생겨났습니다."
        ]

    def _generate_deeper_questions(
        self,
        session: Session,
        synthesis: str
    ) -> List[str]:
        """더 깊은 질문 생성"""
        topic = session.dialogue.topic
        return [
            f"이 탐구가 열어준 새로운 문은 무엇인가요?",
            f"{topic}에 대한 이해가 어떻게 변화했나요?",
            f"아직 답하지 못한 가장 근본적인 질문은 무엇인가요?"
        ]


# 전역 엔진 팩토리
def create_socratic_engine_v2(rag_pipeline, fusion_engine=None) -> SocraticEngineV2:
    """소크라테스 엔진 V2 생성"""
    return SocraticEngineV2(rag_pipeline, fusion_engine)
