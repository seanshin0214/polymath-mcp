"""
Dialogue Models - 대화 모델

소크라테스적 대화 상태와 질문을 표현하는 데이터 모델
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DialogueMode(Enum):
    """대화 모드"""
    SOCRATIC = "socratic"    # 항상 질문으로 응답
    DIRECT = "direct"        # 직접 답변
    HYBRID = "hybrid"        # 맥락에 따라


class QuestionType(Enum):
    """소크라테스적 질문 유형"""
    CLARIFICATION = "clarification"  # 명료화
    ASSUMPTION = "assumption"        # 전제 탐구
    EVIDENCE = "evidence"            # 증거/이유
    VIEWPOINT = "viewpoint"          # 관점/시각
    IMPLICATION = "implication"      # 함의/결과
    META = "meta"                    # 메타 질문
    BRIDGE = "bridge"                # 연결 질문


class DialogueFocus(Enum):
    """대화 초점"""
    EXPLORE = "explore"        # 탐구
    CHALLENGE = "challenge"    # 도전
    SYNTHESIZE = "synthesize"  # 종합


class DepthLevel(Enum):
    """탐구 깊이"""
    SHALLOW = "shallow"
    MEDIUM = "medium"
    DEEP = "deep"


@dataclass
class SocraticQuestion:
    """
    소크라테스적 질문

    대화에서 사용되는 개별 질문
    """
    question: str
    question_type: str  # QuestionType value
    purpose: str  # 질문의 목적
    follow_up_directions: List[str] = field(default_factory=list)  # 후속 탐구 방향


@dataclass
class DialogueTurn:
    """
    대화 턴

    대화의 한 차례 (질문-응답 또는 질문만)
    """
    timestamp: datetime
    speaker: str  # "user" or "polymath"
    content: str
    questions: List[SocraticQuestion] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)


@dataclass
class DialogueState:
    """
    대화 상태

    진행 중인 소크라테스적 대화의 전체 상태
    """
    id: str
    topic: str
    mode: DialogueMode = DialogueMode.HYBRID
    focus: DialogueFocus = DialogueFocus.EXPLORE
    depth: DepthLevel = DepthLevel.MEDIUM

    # Progress tracking
    turns: List[DialogueTurn] = field(default_factory=list)
    current_position: str = ""  # 현재 도달한 위치/결론
    explored_concepts: List[str] = field(default_factory=list)
    challenged_premises: List[str] = field(default_factory=list)
    synthesized_insights: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_turn(self, turn: DialogueTurn):
        """턴 추가"""
        self.turns.append(turn)
        self.updated_at = datetime.now()


@dataclass
class HiddenPremise:
    """
    숨겨진 전제

    진술에서 발견된 암묵적 가정
    """
    premise: str  # 전제 내용
    premise_type: str  # 존재론적, 인식론적, 가치론적 등
    potential_issue: str  # 잠재적 문제점
    challenge_question: str  # 도전 질문


@dataclass
class AlternativeView:
    """
    대안적 관점
    """
    name: str  # 관점 이름 (예: "실용주의적 관점")
    description: str  # 관점 설명
    key_insight: str = ""  # 이 관점의 핵심 통찰


@dataclass
class PremiseChallenge:
    """
    전제 도전 결과

    진술의 전제를 도전한 결과
    """
    original_statement: str
    hidden_premises: List[HiddenPremise]
    counter_perspective: Optional[str] = None  # 반대 관점
    alternative_views: List[AlternativeView] = field(default_factory=list)


@dataclass
class PositionInsight:
    """
    입장에서 추출된 통찰
    """
    position: str  # 원래 입장 (축약)
    core_insight: str  # 핵심 통찰


@dataclass
class Synthesis:
    """
    변증법적 종합 결과
    """
    topic: str
    position_insights: List[PositionInsight]
    synthesis_attempt: str  # 종합 시도
    remaining_tensions: str  # 남은 긴장
    deeper_questions: List[str]  # 더 깊은 질문들


@dataclass
class DialogueResponse:
    """
    대화 응답

    소크라테스적 대화 요청에 대한 응답
    """
    questions: List[SocraticQuestion]
    related_concepts: List[str]
    suggested_direction: str
    depth_level: str
