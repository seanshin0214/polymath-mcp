"""
Socratic V2 Tools - 소크라테스 학습 시스템 MCP 도구

풀버전 소크라테스 대화 시스템의 MCP 도구 인터페이스
"""

from typing import List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent


def get_socratic_v2_tools() -> List[Tool]:
    """소크라테스 V2 도구 정의 반환"""
    return [
        # === 대화 시작/계속 ===
        Tool(
            name="start_socratic_session",
            description="""소크라테스적 탐구 세션 시작.
            주제에 대한 깊은 탐구를 위한 새 대화 세션을 생성합니다.
            질문을 통해 스스로 답을 찾도록 안내합니다.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "탐구할 주제 (예: '복잡성', '창발', '엔트로피')"
                    },
                    "initial_position": {
                        "type": "string",
                        "description": "주제에 대한 현재 생각이나 질문 (선택)"
                    },
                    "focus": {
                        "type": "string",
                        "enum": ["explore", "challenge", "synthesize"],
                        "default": "explore",
                        "description": "탐구 초점: explore(탐색), challenge(도전), synthesize(종합)"
                    },
                    "depth": {
                        "type": "string",
                        "enum": ["shallow", "medium", "deep"],
                        "default": "medium",
                        "description": "탐구 깊이"
                    }
                },
                "required": ["topic"]
            }
        ),

        Tool(
            name="continue_socratic",
            description="""진행 중인 소크라테스 대화 계속.
            사용자 응답을 분석하고 다음 탐구 질문을 생성합니다.
            적응형 난이도 조절이 적용됩니다.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "세션 ID"
                    },
                    "response": {
                        "type": "string",
                        "description": "이전 질문에 대한 응답"
                    }
                },
                "required": ["session_id", "response"]
            }
        ),

        # === 전제 도전 ===
        Tool(
            name="challenge_statement",
            description="""진술의 숨겨진 전제를 분석하고 도전합니다.
            존재론적, 인식론적, 가치론적 가정을 드러냅니다.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "세션 ID (선택, 있으면 세션에 기록)"
                    },
                    "statement": {
                        "type": "string",
                        "description": "분석할 진술"
                    },
                    "perspective": {
                        "type": "string",
                        "description": "특정 관점에서 도전 (예: '실용주의', '비판이론')"
                    }
                },
                "required": ["statement"]
            }
        ),

        # === 종합 ===
        Tool(
            name="synthesize_dialogue",
            description="""대화를 종합하고 통찰을 정리합니다.
            탐구한 개념, 발견한 연결, 남은 질문을 요약합니다.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "세션 ID"
                    }
                },
                "required": ["session_id"]
            }
        ),

        # === 학습 경로 ===
        Tool(
            name="get_learning_path",
            description="""맞춤형 학습 경로를 생성합니다.
            사용자 수준과 관심사에 맞는 탐구 여정을 설계합니다.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_concept": {
                        "type": "string",
                        "description": "시작 개념"
                    },
                    "path_type": {
                        "type": "string",
                        "enum": ["depth_first", "breadth_first", "spiral", "bridge", "challenge"],
                        "default": "spiral",
                        "description": "경로 유형"
                    },
                    "goal": {
                        "type": "string",
                        "description": "목표 개념 (bridge 유형에서 사용)"
                    }
                },
                "required": ["start_concept"]
            }
        ),

        # === 진행 상황 ===
        Tool(
            name="get_learning_progress",
            description="""학습 진행 상황을 조회합니다.
            탐구한 개념, 도출한 통찰, 현재 수준을 보여줍니다.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "default": "default",
                        "description": "사용자 ID"
                    }
                }
            }
        ),

        # === 세션 관리 ===
        Tool(
            name="list_sessions",
            description="""진행 중인 소크라테스 세션 목록을 조회합니다.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "default": "default",
                        "description": "사용자 ID"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["active", "completed", "all"],
                        "default": "active",
                        "description": "세션 상태 필터"
                    }
                }
            }
        ),

        Tool(
            name="get_session_summary",
            description="""특정 세션의 요약 정보를 조회합니다.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "세션 ID"
                    }
                },
                "required": ["session_id"]
            }
        ),

        Tool(
            name="export_session",
            description="""세션을 마크다운 형식으로 내보냅니다.
            학습 기록을 저장하거나 공유할 수 있습니다.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "세션 ID"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["markdown", "json"],
                        "default": "markdown",
                        "description": "내보내기 형식"
                    }
                },
                "required": ["session_id"]
            }
        ),

        # === 7가지 질문 유형 ===
        Tool(
            name="get_question_types",
            description="""7가지 소크라테스적 질문 유형 정보를 반환합니다.
            각 유형의 목적, 예시, 사용 시점을 설명합니다.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "type_name": {
                        "type": "string",
                        "enum": [
                            "clarification", "assumption", "evidence",
                            "viewpoint", "implication", "meta", "bridge"
                        ],
                        "description": "특정 유형 이름 (선택, 없으면 전체)"
                    }
                }
            }
        )
    ]


async def handle_socratic_v2_tool(
    name: str,
    arguments: dict,
    socratic_engine
) -> List[TextContent]:
    """소크라테스 V2 도구 호출 처리"""

    if name == "start_socratic_session":
        response = await socratic_engine.start_dialogue(
            topic=arguments["topic"],
            initial_position=arguments.get("initial_position"),
            focus=arguments.get("focus", "explore"),
            depth=arguments.get("depth", "medium")
        )

        text = f"""## 소크라테스적 탐구 시작: {arguments['topic']}

**세션 ID**: `{response.session_id}`
**난이도**: {response.difficulty_feedback}

---

### 탐구 질문

"""
        for i, q in enumerate(response.questions, 1):
            text += f"""
**질문 {i}** ({q.purpose})

> {q.question}

*힌트*: {q.follow_ups[0] if q.follow_ups else ''}

"""

        text += f"""
---

### 관련 개념
{', '.join(response.related_concepts)}

### 학습 경로 제안
{response.learning_path_suggestion}

### 다음 단계
{response.next_step_hint}

---
*{response.encouragement}*

> "검증되지 않은 삶은 살 가치가 없다." - 소크라테스
"""
        return [TextContent(type="text", text=text)]

    elif name == "continue_socratic":
        response = await socratic_engine.continue_dialogue(
            session_id=arguments["session_id"],
            user_response=arguments["response"]
        )

        text = f"""## 탐구 계속

**응답 분석**: {response.context_summary}
**난이도**: {response.difficulty_feedback}

---

### 다음 질문

"""
        for i, q in enumerate(response.questions, 1):
            text += f"""
**질문 {i}** ({q.purpose})

> {q.question}

"""

        text += f"""
---

### 진행 상황
- 탐구한 개념: {response.progress_update.get('concepts_explored', 0)}개
- 도출한 통찰: {response.progress_update.get('insights_gained', 0)}개
- 도달 깊이: {response.progress_update.get('depth_reached', 1)}/5

### 힌트
{response.next_step_hint}

---
*{response.encouragement}*
"""
        return [TextContent(type="text", text=text)]

    elif name == "challenge_statement":
        result = await socratic_engine.challenge_statement(
            session_id=arguments.get("session_id"),
            statement=arguments["statement"],
            perspective=arguments.get("perspective")
        )

        text = f"""## 전제 도전

### 원본 진술
> "{result['original_statement']}"

---

### 발견된 숨겨진 전제

"""
        for i, premise in enumerate(result['hidden_premises'], 1):
            text += f"""
**전제 {i}** ({premise['type']})

*가정*: {premise['premise']}

*도전 질문*: {premise['challenge']}

*대안적 관점*: {premise['alternative']}

---
"""

        text += "\n### 다양한 관점에서의 반론\n\n"
        for counter in result['counter_perspectives']:
            text += f"""
**{counter['perspective']}**

{counter['counter_argument']}

*핵심*: {counter['key_insight']}

"""

        text += f"""
---

### 종합 질문
{result['synthesis_question']}
"""
        return [TextContent(type="text", text=text)]

    elif name == "synthesize_dialogue":
        result = await socratic_engine.synthesize_dialogue(
            session_id=arguments["session_id"]
        )

        text = f"""## 대화 종합: {result['topic']}

---

### 탐구한 개념들
{', '.join(result['explored_concepts']) if result['explored_concepts'] else '(없음)'}

### 핵심 통찰

"""
        for i, insight in enumerate(result['key_insights'], 1):
            text += f"{i}. {insight}\n"

        text += """
### 발견한 연결

"""
        for conn in result['connections_discovered']:
            text += f"- {conn.get('from', '')} → {conn.get('to', '')} ({conn.get('type', '')})\n"

        text += f"""
---

### 종합

{result['synthesis']}

### 남은 긴장

"""
        for tension in result['remaining_tensions']:
            text += f"- {tension}\n"

        text += """
### 더 깊은 탐구를 위한 질문

"""
        for q in result['deeper_questions']:
            text += f"> {q}\n\n"

        summary = result['session_summary']
        text += f"""
---

### 세션 통계
- 총 대화 수: {summary.get('total_turns', 0)}
- 탐구한 개념: {summary.get('concepts_explored', 0)}개
- 도출한 통찰: {summary.get('insights_gained', 0)}개
- 도달 깊이: {summary.get('depth_reached', 1)}/5
"""
        return [TextContent(type="text", text=text)]

    elif name == "get_learning_path":
        path = await socratic_engine.get_learning_path(
            user_id="default",
            start_concept=arguments["start_concept"],
            path_type=arguments.get("path_type", "spiral"),
            goal=arguments.get("goal")
        )

        text = f"""## 학습 경로: {path.title}

**유형**: {path.path_type.value}
**설명**: {path.description}
**예상 소요 시간**: {path.estimated_duration}분
**난이도 범위**: {path.difficulty_range[0]} ~ {path.difficulty_range[1]}

---

### 학습 목표

"""
        for obj in path.learning_objectives:
            text += f"- {obj}\n"

        text += """
---

### 탐구 단계

"""
        for i, step in enumerate(path.steps, 1):
            text += f"""
#### 단계 {i}: {step.concept.name}
**초점**: {step.focus}
**예상 시간**: {step.estimated_time}분

**탐구 질문**:
"""
            for q in step.questions:
                text += f"- {q}\n"

            text += f"""
**체크포인트**: {step.checkpoint}

---
"""

        text += f"""
### 다루는 분야
{', '.join(path.domains_covered)}
"""
        return [TextContent(type="text", text=text)]

    elif name == "get_learning_progress":
        progress = await socratic_engine.get_user_progress(
            user_id=arguments.get("user_id", "default")
        )

        perf = progress['performance']
        sessions = progress['sessions']
        learning = progress['learning']

        text = f"""## 학습 진행 상황

---

### 현재 수준

- **레벨**: {perf.get('current_level', 'N/A')}/5
- **최근 성과**: {perf.get('recent_performance', 'N/A')}/5
- **트렌드**: {'📈 향상 중' if perf.get('trend') == 'improving' else '📉 지원 필요'}
- **근접발달영역(ZPD)**: {perf.get('zpd', (1, 5))}

---

### 세션 통계

- 총 세션: {sessions.get('total', 0)}개
- 진행 중: {sessions.get('active', 0)}개
- 완료: {sessions.get('completed', 0)}개

---

### 학습 성과

- 탐구한 개념: {learning.get('concepts_explored', 0)}개
- 도출한 통찰: {learning.get('insights_gained', 0)}개
- 발견한 연결: {learning.get('connections_made', 0)}개

---

### 강점 분야
{', '.join(perf.get('expertise_areas', [])) or '(아직 없음)'}

### 개선 필요 분야
{', '.join(perf.get('areas_to_improve', [])) or '(없음)'}

---

### 최근 세션

"""
        for s in progress.get('recent_sessions', [])[:3]:
            text += f"- **{s.get('topic', 'N/A')}** ({s.get('status', 'N/A')}) - {s.get('total_turns', 0)}턴\n"

        return [TextContent(type="text", text=text)]

    elif name == "list_sessions":
        from src.engines.session_manager import get_session_manager

        session_mgr = get_session_manager()
        status_filter = arguments.get("status", "active")
        if status_filter == "all":
            status_filter = None

        sessions = session_mgr.list_sessions(
            user_id=arguments.get("user_id", "default"),
            status=status_filter
        )

        text = "## 소크라테스 세션 목록\n\n"

        if not sessions:
            text += "*세션이 없습니다.*\n"
        else:
            text += "| 세션 ID | 주제 | 상태 | 대화 수 | 업데이트 |\n"
            text += "|---------|------|------|---------|----------|\n"
            for s in sessions:
                text += f"| `{s.get('session_id', 'N/A')}` | {s.get('topic', 'N/A')} | {s.get('status', 'N/A')} | {s.get('total_turns', 0)} | {s.get('updated_at', 'N/A')[:10]} |\n"

        return [TextContent(type="text", text=text)]

    elif name == "get_session_summary":
        from src.engines.session_manager import get_session_manager

        session_mgr = get_session_manager()
        summary = session_mgr.get_session_summary(arguments["session_id"])

        if not summary:
            return [TextContent(type="text", text=f"세션 '{arguments['session_id']}'을 찾을 수 없습니다.")]

        text = f"""## 세션 요약

**세션 ID**: `{summary.get('session_id', 'N/A')}`
**주제**: {summary.get('topic', 'N/A')}
**상태**: {summary.get('status', 'N/A')}
**생성일**: {summary.get('created_at', 'N/A')}

---

### 진행 상황

- 총 대화 수: {summary.get('total_turns', 0)}
- 탐구한 개념: {summary.get('concepts_explored', 0)}개
- 도출한 통찰: {summary.get('insights_gained', 0)}개
- 도달 깊이: {summary.get('depth_reached', 1)}/5

---

### 현재 위치

{summary.get('current_position', '(정의되지 않음)')}
"""
        return [TextContent(type="text", text=text)]

    elif name == "export_session":
        from src.engines.session_manager import get_session_manager

        session_mgr = get_session_manager()
        format_type = arguments.get("format", "markdown")
        exported = session_mgr.export_session(
            arguments["session_id"],
            format=format_type
        )

        if not exported:
            return [TextContent(type="text", text=f"세션 '{arguments['session_id']}'을 찾을 수 없습니다.")]

        return [TextContent(type="text", text=exported)]

    elif name == "get_question_types":
        from src.tools.socratic import SOCRATIC_QUESTION_TYPES

        type_name = arguments.get("type_name")

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

    else:
        return [TextContent(type="text", text=f"알 수 없는 도구: {name}")]
