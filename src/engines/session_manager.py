"""
Session Manager - 대화 세션 관리자

소크라테스적 대화의 상태를 저장, 복원, 추적
학습 진행 상황 및 통찰 기록
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict

from src.models.dialogue import (
    DialogueState,
    DialogueTurn,
    DialogueMode,
    DialogueFocus,
    DepthLevel,
    SocraticQuestion
)


@dataclass
class LearningProgress:
    """학습 진행 상황"""
    concepts_explored: List[str] = field(default_factory=list)
    insights_gained: List[str] = field(default_factory=list)
    questions_asked: int = 0
    questions_answered: int = 0
    depth_reached: int = 1
    connections_made: List[Dict[str, str]] = field(default_factory=list)  # [{from, to, type}]
    challenges_faced: List[str] = field(default_factory=list)


@dataclass
class SessionMetadata:
    """세션 메타데이터"""
    session_id: str
    user_id: str = "default"
    created_at: str = ""
    updated_at: str = ""
    total_turns: int = 0
    status: str = "active"  # active, paused, completed
    tags: List[str] = field(default_factory=list)


@dataclass
class Session:
    """완전한 대화 세션"""
    metadata: SessionMetadata
    dialogue: DialogueState
    progress: LearningProgress

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "metadata": asdict(self.metadata),
            "dialogue": {
                "id": self.dialogue.id,
                "topic": self.dialogue.topic,
                "mode": self.dialogue.mode.value,
                "focus": self.dialogue.focus.value,
                "depth": self.dialogue.depth.value,
                "current_position": self.dialogue.current_position,
                "explored_concepts": self.dialogue.explored_concepts,
                "challenged_premises": self.dialogue.challenged_premises,
                "synthesized_insights": self.dialogue.synthesized_insights,
                "turns": [
                    {
                        "timestamp": turn.timestamp.isoformat(),
                        "speaker": turn.speaker,
                        "content": turn.content,
                        "questions": [asdict(q) for q in turn.questions],
                        "related_concepts": turn.related_concepts,
                        "insights": turn.insights
                    }
                    for turn in self.dialogue.turns
                ]
            },
            "progress": asdict(self.progress)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """딕셔너리에서 복원"""
        metadata = SessionMetadata(**data["metadata"])

        # 대화 상태 복원
        dialogue_data = data["dialogue"]
        dialogue = DialogueState(
            id=dialogue_data["id"],
            topic=dialogue_data["topic"],
            mode=DialogueMode(dialogue_data["mode"]),
            focus=DialogueFocus(dialogue_data["focus"]),
            depth=DepthLevel(dialogue_data["depth"]),
            current_position=dialogue_data["current_position"],
            explored_concepts=dialogue_data["explored_concepts"],
            challenged_premises=dialogue_data["challenged_premises"],
            synthesized_insights=dialogue_data["synthesized_insights"]
        )

        # 턴 복원
        for turn_data in dialogue_data["turns"]:
            turn = DialogueTurn(
                timestamp=datetime.fromisoformat(turn_data["timestamp"]),
                speaker=turn_data["speaker"],
                content=turn_data["content"],
                questions=[
                    SocraticQuestion(**q) for q in turn_data["questions"]
                ],
                related_concepts=turn_data["related_concepts"],
                insights=turn_data["insights"]
            )
            dialogue.turns.append(turn)

        progress = LearningProgress(**data["progress"])

        return cls(
            metadata=metadata,
            dialogue=dialogue,
            progress=progress
        )


class SessionManager:
    """
    대화 세션 관리자

    기능:
    - 세션 생성, 저장, 복원
    - 대화 히스토리 관리
    - 학습 진행 추적
    - 통찰 및 연결 기록
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Args:
            storage_path: 세션 저장 경로 (기본: ./data/sessions)
        """
        self.storage_path = storage_path or Path("./data/sessions")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 메모리 내 활성 세션
        self.active_sessions: Dict[str, Session] = {}

    def create_session(
        self,
        topic: str,
        user_id: str = "default",
        mode: DialogueMode = DialogueMode.HYBRID,
        focus: DialogueFocus = DialogueFocus.EXPLORE,
        depth: DepthLevel = DepthLevel.MEDIUM,
        tags: Optional[List[str]] = None
    ) -> Session:
        """
        새 세션 생성

        Args:
            topic: 탐구 주제
            user_id: 사용자 ID
            mode: 대화 모드
            focus: 대화 초점
            depth: 탐구 깊이
            tags: 태그 목록
        """
        session_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()

        metadata = SessionMetadata(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            updated_at=now,
            total_turns=0,
            status="active",
            tags=tags or []
        )

        dialogue = DialogueState(
            id=session_id,
            topic=topic,
            mode=mode,
            focus=focus,
            depth=depth
        )

        progress = LearningProgress()

        session = Session(
            metadata=metadata,
            dialogue=dialogue,
            progress=progress
        )

        # 활성 세션에 추가
        self.active_sessions[session_id] = session

        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """세션 조회 (메모리 → 파일)"""
        # 메모리에서 조회
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]

        # 파일에서 로드
        return self._load_from_file(session_id)

    def save_session(self, session: Session) -> bool:
        """세션 저장"""
        session.metadata.updated_at = datetime.now().isoformat()

        # 파일에 저장
        file_path = self.storage_path / f"{session.metadata.session_id}.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False

    def _load_from_file(self, session_id: str) -> Optional[Session]:
        """파일에서 세션 로드"""
        file_path = self.storage_path / f"{session_id}.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            session = Session.from_dict(data)
            # 활성 세션에 추가
            self.active_sessions[session_id] = session
            return session
        except Exception as e:
            print(f"Error loading session: {e}")
            return None

    def add_turn(
        self,
        session_id: str,
        speaker: str,
        content: str,
        questions: Optional[List[SocraticQuestion]] = None,
        related_concepts: Optional[List[str]] = None,
        insights: Optional[List[str]] = None
    ) -> Optional[DialogueTurn]:
        """
        대화 턴 추가

        Args:
            session_id: 세션 ID
            speaker: 화자 ("user" or "polymath")
            content: 발화 내용
            questions: 소크라테스 질문 목록
            related_concepts: 관련 개념
            insights: 도출된 통찰
        """
        session = self.get_session(session_id)
        if not session:
            return None

        turn = DialogueTurn(
            timestamp=datetime.now(),
            speaker=speaker,
            content=content,
            questions=questions or [],
            related_concepts=related_concepts or [],
            insights=insights or []
        )

        session.dialogue.add_turn(turn)
        session.metadata.total_turns += 1

        # 진행 상황 업데이트
        if related_concepts:
            for concept in related_concepts:
                if concept not in session.progress.concepts_explored:
                    session.progress.concepts_explored.append(concept)

        if insights:
            session.progress.insights_gained.extend(insights)

        if speaker == "polymath" and questions:
            session.progress.questions_asked += len(questions)
        elif speaker == "user":
            session.progress.questions_answered += 1

        # 자동 저장
        self.save_session(session)

        return turn

    def update_position(
        self,
        session_id: str,
        new_position: str
    ) -> bool:
        """현재 탐구 위치 업데이트"""
        session = self.get_session(session_id)
        if not session:
            return False

        session.dialogue.current_position = new_position
        session.metadata.updated_at = datetime.now().isoformat()

        self.save_session(session)
        return True

    def add_insight(
        self,
        session_id: str,
        insight: str
    ) -> bool:
        """통찰 추가"""
        session = self.get_session(session_id)
        if not session:
            return False

        session.dialogue.synthesized_insights.append(insight)
        session.progress.insights_gained.append(insight)

        self.save_session(session)
        return True

    def add_connection(
        self,
        session_id: str,
        from_concept: str,
        to_concept: str,
        connection_type: str
    ) -> bool:
        """개념 연결 기록"""
        session = self.get_session(session_id)
        if not session:
            return False

        connection = {
            "from": from_concept,
            "to": to_concept,
            "type": connection_type
        }
        session.progress.connections_made.append(connection)

        self.save_session(session)
        return True

    def challenge_premise(
        self,
        session_id: str,
        premise: str
    ) -> bool:
        """전제 도전 기록"""
        session = self.get_session(session_id)
        if not session:
            return False

        session.dialogue.challenged_premises.append(premise)
        session.progress.challenges_faced.append(premise)

        self.save_session(session)
        return True

    def set_depth(
        self,
        session_id: str,
        depth: int
    ) -> bool:
        """탐구 깊이 설정"""
        session = self.get_session(session_id)
        if not session:
            return False

        depth_map = {
            1: DepthLevel.SHALLOW,
            2: DepthLevel.SHALLOW,
            3: DepthLevel.MEDIUM,
            4: DepthLevel.DEEP,
            5: DepthLevel.DEEP
        }

        session.dialogue.depth = depth_map.get(depth, DepthLevel.MEDIUM)
        session.progress.depth_reached = max(session.progress.depth_reached, depth)

        self.save_session(session)
        return True

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 요약 반환"""
        session = self.get_session(session_id)
        if not session:
            return None

        return {
            "session_id": session.metadata.session_id,
            "topic": session.dialogue.topic,
            "status": session.metadata.status,
            "created_at": session.metadata.created_at,
            "total_turns": session.metadata.total_turns,
            "concepts_explored": len(session.progress.concepts_explored),
            "insights_gained": len(session.progress.insights_gained),
            "depth_reached": session.progress.depth_reached,
            "connections_made": len(session.progress.connections_made),
            "current_position": session.dialogue.current_position[:100] if session.dialogue.current_position else ""
        }

    def list_sessions(
        self,
        user_id: str = "default",
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """사용자의 세션 목록 반환"""
        sessions = []

        # 파일에서 모든 세션 로드
        for file_path in self.storage_path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                meta = data.get("metadata", {})
                if meta.get("user_id") == user_id:
                    if status is None or meta.get("status") == status:
                        sessions.append({
                            "session_id": meta.get("session_id"),
                            "topic": data.get("dialogue", {}).get("topic"),
                            "status": meta.get("status"),
                            "created_at": meta.get("created_at"),
                            "updated_at": meta.get("updated_at"),
                            "total_turns": meta.get("total_turns", 0)
                        })
            except Exception:
                continue

        # 최신 순 정렬
        sessions.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
        return sessions

    def complete_session(self, session_id: str) -> bool:
        """세션 완료 처리"""
        session = self.get_session(session_id)
        if not session:
            return False

        session.metadata.status = "completed"
        session.metadata.updated_at = datetime.now().isoformat()

        self.save_session(session)

        # 활성 세션에서 제거
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

        return True

    def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        # 메모리에서 제거
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

        # 파일 삭제
        file_path = self.storage_path / f"{session_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True

        return False

    def export_session(
        self,
        session_id: str,
        format: str = "json"
    ) -> Optional[str]:
        """세션 내보내기"""
        session = self.get_session(session_id)
        if not session:
            return None

        if format == "json":
            return json.dumps(session.to_dict(), ensure_ascii=False, indent=2)

        elif format == "markdown":
            return self._export_as_markdown(session)

        return None

    def _export_as_markdown(self, session: Session) -> str:
        """마크다운 형식으로 내보내기"""
        md = f"""# 소크라테스적 탐구: {session.dialogue.topic}

## 세션 정보
- **세션 ID**: {session.metadata.session_id}
- **생성일**: {session.metadata.created_at}
- **대화 수**: {session.metadata.total_turns}
- **상태**: {session.metadata.status}

## 학습 진행

### 탐구한 개념들
{chr(10).join([f"- {c}" for c in session.progress.concepts_explored]) or "- (없음)"}

### 도출된 통찰
{chr(10).join([f"- {i}" for i in session.progress.insights_gained]) or "- (없음)"}

### 발견된 연결
{chr(10).join([f"- {c['from']} → {c['to']} ({c['type']})" for c in session.progress.connections_made]) or "- (없음)"}

## 대화 기록

"""
        for i, turn in enumerate(session.dialogue.turns, 1):
            speaker = "🧑 사용자" if turn.speaker == "user" else "🦉 폴리매스"
            md += f"""### 턴 {i} ({speaker})
{turn.content}

"""
            if turn.questions:
                md += "**질문들:**\n"
                for q in turn.questions:
                    md += f"- {q.question}\n"
                md += "\n"

            if turn.insights:
                md += "**통찰:**\n"
                for ins in turn.insights:
                    md += f"- {ins}\n"
                md += "\n"

        md += f"""
## 현재 위치
{session.dialogue.current_position or "(아직 정의되지 않음)"}

---
*Polymath MCP Socratic Dialogue Export*
"""
        return md


# 전역 세션 관리자 인스턴스
_session_manager: Optional[SessionManager] = None


def get_session_manager(storage_path: Optional[Path] = None) -> SessionManager:
    """세션 관리자 싱글톤"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(storage_path)
    return _session_manager
