"""
Adaptive Difficulty System - 적응형 난이도 시스템

사용자 응답과 진행 상황을 분석하여 난이도를 동적으로 조절
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta


class ResponseQuality(Enum):
    """응답 품질 등급"""
    EXCELLENT = 5      # 통찰력 있는 응답
    GOOD = 4           # 정확한 응답
    ADEQUATE = 3       # 기본적인 이해
    PARTIAL = 2        # 부분적 이해
    STRUGGLING = 1     # 어려움


class EngagementLevel(Enum):
    """참여도 수준"""
    HIGHLY_ENGAGED = 5   # 적극적 탐구
    ENGAGED = 4          # 정상 참여
    PASSIVE = 3          # 수동적
    DISTRACTED = 2       # 산만
    DISENGAGED = 1       # 이탈


@dataclass
class ResponseAnalysis:
    """응답 분석 결과"""
    quality: ResponseQuality
    engagement: EngagementLevel
    depth_indicators: List[str]  # 깊이 지표들
    confusion_signals: List[str]  # 혼란 신호들
    breakthrough_signals: List[str]  # 돌파구 신호들
    suggested_adjustment: int  # -2 ~ +2 난이도 조절 제안


@dataclass
class UserProfile:
    """사용자 프로필"""
    user_id: str
    current_level: int = 3  # 1-5
    expertise_areas: List[str] = field(default_factory=list)
    struggling_areas: List[str] = field(default_factory=list)

    # 성과 기록
    response_history: List[ResponseQuality] = field(default_factory=list)
    time_per_question: List[float] = field(default_factory=list)  # 초
    concepts_mastered: List[str] = field(default_factory=list)

    # 학습 스타일
    preferred_depth: str = "medium"  # shallow, medium, deep
    preferred_pace: str = "moderate"  # slow, moderate, fast
    engagement_pattern: str = "consistent"  # sporadic, consistent, intensive


@dataclass
class DifficultySettings:
    """난이도 설정"""
    question_complexity: int = 3  # 1-5
    abstraction_level: int = 3  # 1-5
    connection_breadth: int = 3  # 1-5 (연결해야 할 분야 수)
    time_pressure: int = 3  # 1-5
    hint_availability: int = 3  # 1-5 (힌트 제공 빈도)


class AdaptiveDifficultyEngine:
    """
    적응형 난이도 조절 엔진

    기능:
    - 사용자 응답 분석
    - 실시간 난이도 조절
    - 최적 학습 영역(ZPD) 유지
    - 동기부여 균형
    """

    # 응답 품질 지표 키워드
    QUALITY_INDICATORS = {
        "excellent": [
            "새로운 관점", "연결", "통합", "발견", "깨달음",
            "재정의", "확장", "비판적", "독창적", "심층"
        ],
        "good": [
            "이해", "설명", "예시", "적용", "분석",
            "비교", "구분", "정리", "파악", "인식"
        ],
        "struggling": [
            "모르겠", "헷갈", "어려", "복잡", "혼란",
            "이해 안", "무슨 뜻", "다시 설명", "힌트"
        ]
    }

    # 참여도 지표
    ENGAGEMENT_INDICATORS = {
        "high": [
            "더 알고 싶", "궁금", "흥미", "재미있",
            "깊이", "확장", "연결해보면", "생각해보니"
        ],
        "low": [
            "넘어가", "다음", "건너뛰", "나중에",
            "됐", "그만", "충분", "알겠"
        ]
    }

    def __init__(self):
        self.user_profiles: Dict[str, UserProfile] = {}
        self.session_adjustments: Dict[str, List[int]] = {}  # 세션별 조절 기록

    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """사용자 프로필 조회 또는 생성"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id=user_id)
        return self.user_profiles[user_id]

    def analyze_response(
        self,
        response: str,
        question_difficulty: int,
        time_taken: float,
        expected_concepts: List[str]
    ) -> ResponseAnalysis:
        """
        사용자 응답 분석

        Args:
            response: 사용자 응답 텍스트
            question_difficulty: 질문 난이도 (1-5)
            time_taken: 응답 소요 시간 (초)
            expected_concepts: 기대되는 개념들
        """
        response_lower = response.lower()

        # 품질 분석
        excellent_count = sum(1 for ind in self.QUALITY_INDICATORS["excellent"]
                              if ind in response_lower)
        good_count = sum(1 for ind in self.QUALITY_INDICATORS["good"]
                         if ind in response_lower)
        struggling_count = sum(1 for ind in self.QUALITY_INDICATORS["struggling"]
                               if ind in response_lower)

        # 품질 등급 결정
        if excellent_count >= 2:
            quality = ResponseQuality.EXCELLENT
        elif good_count >= 2 and struggling_count == 0:
            quality = ResponseQuality.GOOD
        elif struggling_count >= 2:
            quality = ResponseQuality.STRUGGLING
        elif struggling_count >= 1:
            quality = ResponseQuality.PARTIAL
        else:
            quality = ResponseQuality.ADEQUATE

        # 참여도 분석
        high_engagement = sum(1 for ind in self.ENGAGEMENT_INDICATORS["high"]
                              if ind in response_lower)
        low_engagement = sum(1 for ind in self.ENGAGEMENT_INDICATORS["low"]
                             if ind in response_lower)

        if high_engagement >= 2:
            engagement = EngagementLevel.HIGHLY_ENGAGED
        elif high_engagement >= 1 and low_engagement == 0:
            engagement = EngagementLevel.ENGAGED
        elif low_engagement >= 2:
            engagement = EngagementLevel.DISENGAGED
        elif low_engagement >= 1:
            engagement = EngagementLevel.DISTRACTED
        else:
            engagement = EngagementLevel.PASSIVE

        # 깊이 지표 추출
        depth_indicators = []
        if len(response) > 200:
            depth_indicators.append("detailed_response")
        if any(c in response for c in expected_concepts):
            depth_indicators.append("concept_recognition")
        if "?" in response:
            depth_indicators.append("asks_questions")
        if any(word in response_lower for word in ["예를 들어", "예시", "사례"]):
            depth_indicators.append("provides_examples")

        # 혼란 신호 추출
        confusion_signals = []
        if struggling_count > 0:
            confusion_signals.append("explicit_confusion")
        if len(response) < 20:
            confusion_signals.append("very_short_response")
        if time_taken > 180:  # 3분 이상
            confusion_signals.append("long_thinking_time")

        # 돌파구 신호 추출
        breakthrough_signals = []
        if "아!" in response or "그렇구나" in response:
            breakthrough_signals.append("aha_moment")
        if "연결" in response_lower or "관계" in response_lower:
            breakthrough_signals.append("makes_connections")
        if excellent_count >= 2:
            breakthrough_signals.append("deep_insight")

        # 난이도 조절 제안
        adjustment = self._calculate_adjustment(
            quality, engagement, question_difficulty, time_taken
        )

        return ResponseAnalysis(
            quality=quality,
            engagement=engagement,
            depth_indicators=depth_indicators,
            confusion_signals=confusion_signals,
            breakthrough_signals=breakthrough_signals,
            suggested_adjustment=adjustment
        )

    def _calculate_adjustment(
        self,
        quality: ResponseQuality,
        engagement: EngagementLevel,
        difficulty: int,
        time_taken: float
    ) -> int:
        """난이도 조절량 계산"""
        adjustment = 0

        # 품질 기반 조절
        if quality == ResponseQuality.EXCELLENT:
            adjustment += 1
        elif quality == ResponseQuality.STRUGGLING:
            adjustment -= 1

        # 참여도 기반 조절
        if engagement == EngagementLevel.HIGHLY_ENGAGED:
            adjustment += 0.5
        elif engagement in [EngagementLevel.DISTRACTED, EngagementLevel.DISENGAGED]:
            adjustment -= 0.5

        # 시간 기반 미세 조절
        if time_taken < 30 and quality.value >= 4:  # 빠르고 정확
            adjustment += 0.5
        elif time_taken > 120 and quality.value <= 2:  # 느리고 부정확
            adjustment -= 0.5

        # 현재 난이도 고려 (극단 방지)
        if difficulty >= 4 and adjustment > 0:
            adjustment = min(adjustment, 0.5)
        elif difficulty <= 2 and adjustment < 0:
            adjustment = max(adjustment, -0.5)

        return int(round(adjustment))

    def update_profile(
        self,
        user_id: str,
        analysis: ResponseAnalysis,
        concept: str
    ):
        """응답 분석 결과로 프로필 업데이트"""
        profile = self.get_or_create_profile(user_id)

        # 응답 기록 추가
        profile.response_history.append(analysis.quality)

        # 전문/약점 영역 업데이트
        if analysis.quality == ResponseQuality.EXCELLENT:
            if concept not in profile.expertise_areas:
                profile.expertise_areas.append(concept)
            if concept in profile.struggling_areas:
                profile.struggling_areas.remove(concept)

        elif analysis.quality == ResponseQuality.STRUGGLING:
            if concept not in profile.struggling_areas:
                profile.struggling_areas.append(concept)

        # 마스터한 개념 (연속 좋은 응답)
        if len(profile.response_history) >= 3:
            recent = profile.response_history[-3:]
            if all(q.value >= 4 for q in recent):
                if concept not in profile.concepts_mastered:
                    profile.concepts_mastered.append(concept)

        # 현재 레벨 조정
        self._adjust_user_level(profile, analysis)

    def _adjust_user_level(
        self,
        profile: UserProfile,
        analysis: ResponseAnalysis
    ):
        """사용자 레벨 조정"""
        # 최근 5개 응답 기반
        if len(profile.response_history) >= 5:
            recent = profile.response_history[-5:]
            avg_quality = sum(q.value for q in recent) / 5

            if avg_quality >= 4.5 and profile.current_level < 5:
                profile.current_level += 1
            elif avg_quality <= 2.0 and profile.current_level > 1:
                profile.current_level -= 1

    def get_difficulty_settings(
        self,
        user_id: str,
        concept: str,
        base_difficulty: int = 3
    ) -> DifficultySettings:
        """
        사용자 맞춤 난이도 설정 생성

        Args:
            user_id: 사용자 ID
            concept: 현재 개념
            base_difficulty: 기본 난이도
        """
        profile = self.get_or_create_profile(user_id)

        # 기본값 = 사용자 레벨
        level = profile.current_level

        # 개념별 조정
        if concept in profile.expertise_areas:
            level = min(5, level + 1)  # 전문 분야면 더 어렵게
        elif concept in profile.struggling_areas:
            level = max(1, level - 1)  # 약점 분야면 더 쉽게

        # 학습 스타일 반영
        if profile.preferred_depth == "deep":
            abstraction = min(5, level + 1)
        elif profile.preferred_depth == "shallow":
            abstraction = max(1, level - 1)
        else:
            abstraction = level

        # 힌트 가용성 (어려워하면 더 많이)
        hint_level = 6 - level  # 역비례

        return DifficultySettings(
            question_complexity=level,
            abstraction_level=abstraction,
            connection_breadth=level,
            time_pressure=level if profile.preferred_pace == "fast" else max(1, level - 1),
            hint_availability=hint_level
        )

    def should_provide_hint(
        self,
        user_id: str,
        time_elapsed: float,
        difficulty: int
    ) -> Tuple[bool, str]:
        """
        힌트 제공 여부 및 힌트 유형 결정

        Returns:
            (힌트 제공 여부, 힌트 유형)
        """
        profile = self.get_or_create_profile(user_id)

        # 시간 기반 힌트
        time_threshold = 60 + (5 - difficulty) * 30  # 난이도 낮을수록 더 오래 기다림

        if time_elapsed > time_threshold:
            # 힌트 유형 결정
            if len(profile.response_history) >= 2:
                recent = profile.response_history[-2:]
                if all(q.value <= 2 for q in recent):
                    return (True, "direct_hint")  # 직접적 힌트
                else:
                    return (True, "guiding_question")  # 유도 질문

            return (True, "encouragement")  # 격려

        return (False, "")

    def get_encouragement_message(
        self,
        analysis: ResponseAnalysis,
        user_id: str
    ) -> str:
        """상황에 맞는 격려 메시지 생성"""
        profile = self.get_or_create_profile(user_id)

        if analysis.quality == ResponseQuality.EXCELLENT:
            return "훌륭한 통찰입니다! 더 깊이 탐구해볼까요?"

        elif analysis.quality == ResponseQuality.GOOD:
            return "좋은 이해입니다. 한 걸음 더 나아가볼까요?"

        elif analysis.quality == ResponseQuality.STRUGGLING:
            if len(profile.response_history) >= 2:
                # 이전에 잘했었다면
                if any(q.value >= 4 for q in profile.response_history[-5:-1]):
                    return "어려운 부분이네요. 조금 다른 각도에서 접근해볼까요?"
            return "괜찮습니다. 함께 차근차근 살펴봅시다."

        elif analysis.breakthrough_signals:
            return "좋습니다! 중요한 연결을 발견하셨네요."

        return "계속해서 탐구해봅시다."

    def calculate_zone_of_proximal_development(
        self,
        user_id: str
    ) -> Tuple[int, int]:
        """
        근접발달영역(ZPD) 계산

        Returns:
            (하한, 상한) 난이도 범위
        """
        profile = self.get_or_create_profile(user_id)

        # 기본 ZPD = 현재 레벨 ± 1
        lower = max(1, profile.current_level - 1)
        upper = min(5, profile.current_level + 1)

        # 최근 성과에 따라 조정
        if len(profile.response_history) >= 5:
            recent = profile.response_history[-5:]
            avg = sum(q.value for q in recent) / 5

            if avg >= 4:  # 잘하고 있음
                upper = min(5, upper + 1)
            elif avg <= 2:  # 어려워함
                lower = max(1, lower - 1)

        return (lower, upper)

    def get_performance_summary(self, user_id: str) -> Dict[str, Any]:
        """사용자 성과 요약"""
        profile = self.get_or_create_profile(user_id)

        if not profile.response_history:
            return {
                "status": "new_user",
                "message": "아직 충분한 데이터가 없습니다."
            }

        recent_avg = sum(q.value for q in profile.response_history[-10:]) / min(10, len(profile.response_history))

        return {
            "current_level": profile.current_level,
            "recent_performance": round(recent_avg, 1),
            "total_responses": len(profile.response_history),
            "concepts_mastered": len(profile.concepts_mastered),
            "expertise_areas": profile.expertise_areas[:5],
            "areas_to_improve": profile.struggling_areas[:3],
            "zpd": self.calculate_zone_of_proximal_development(user_id),
            "trend": "improving" if recent_avg >= 3.5 else "needs_support"
        }


# 전역 난이도 엔진 인스턴스
_difficulty_engine: Optional[AdaptiveDifficultyEngine] = None


def get_difficulty_engine() -> AdaptiveDifficultyEngine:
    """적응형 난이도 엔진 싱글톤"""
    global _difficulty_engine
    if _difficulty_engine is None:
        _difficulty_engine = AdaptiveDifficultyEngine()
    return _difficulty_engine
