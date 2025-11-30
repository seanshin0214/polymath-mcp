"""
Polymath MCP HTTP Server - GPT Actions 커넥터

MCP 기능을 HTTP API로 노출하여 GPT Actions와 연동
ngrok으로 터널링하여 외부 접근 가능
"""

import asyncio
import json
import os
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Polymath MCP imports
from src.config.settings import Settings
from src.engines.rag_pipeline import RAGPipeline
from src.engines.fusion_engine import FusionEngine
from src.engines.socratic_engine_v2 import SocraticEngineV2, create_socratic_engine_v2


# Global instances
settings: Settings = None
rag_pipeline: RAGPipeline = None
fusion_engine: FusionEngine = None
socratic_engine: SocraticEngineV2 = None


async def initialize_engines():
    """엔진 초기화"""
    global settings, rag_pipeline, fusion_engine, socratic_engine

    settings = Settings()
    rag_pipeline = RAGPipeline(settings)
    await rag_pipeline.initialize()

    fusion_engine = FusionEngine(rag_pipeline)
    socratic_engine = create_socratic_engine_v2(rag_pipeline, fusion_engine)

    print("✅ Polymath MCP engines initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 라이프사이클 관리"""
    await initialize_engines()
    yield
    print("Shutting down...")


# FastAPI 앱 생성
app = FastAPI(
    title="Polymath MCP API",
    description="""
    30개 학문 분야의 지식을 융합하는 폴리매스 MCP API

    ## 주요 기능
    - **개념 검색**: 시맨틱 검색으로 30+ 학문 분야 탐색
    - **융합 사고**: 7가지 융합 패턴으로 새로운 연결 발견
    - **소크라테스 대화**: 질문을 통한 깊은 탐구
    - **학습 경로**: 맞춤형 학습 여정 설계
    """,
    version="2.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Pydantic Models =====

class SearchRequest(BaseModel):
    query: str = Field(..., description="검색 쿼리")
    domains: Optional[List[str]] = Field(None, description="필터링할 도메인 목록")
    limit: int = Field(10, description="결과 개수", ge=1, le=50)


class SearchResult(BaseModel):
    name: str
    domain: str
    description: str
    similarity: float


class FusionRequest(BaseModel):
    concept_a: str = Field(..., description="첫 번째 개념")
    concept_b: str = Field(..., description="두 번째 개념")


class SocraticStartRequest(BaseModel):
    topic: str = Field(..., description="탐구 주제")
    initial_position: Optional[str] = Field(None, description="초기 입장")
    focus: str = Field("explore", description="탐구 초점: explore, challenge, synthesize")
    depth: str = Field("medium", description="탐구 깊이: shallow, medium, deep")


class SocraticContinueRequest(BaseModel):
    session_id: str = Field(..., description="세션 ID")
    response: str = Field(..., description="사용자 응답")


class ChallengeRequest(BaseModel):
    statement: str = Field(..., description="분석할 진술")
    session_id: Optional[str] = Field(None, description="세션 ID")
    perspective: Optional[str] = Field(None, description="특정 관점")


class LearningPathRequest(BaseModel):
    start_concept: str = Field(..., description="시작 개념")
    path_type: str = Field("spiral", description="경로 유형")
    goal: Optional[str] = Field(None, description="목표 개념")


# ===== API Endpoints =====

@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "status": "running",
        "service": "Polymath MCP API",
        "version": "2.0.0",
        "features": [
            "concept_search",
            "fusion_thinking",
            "socratic_dialogue",
            "learning_paths"
        ]
    }


@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "healthy"}


# ===== 검색 API =====

@app.post("/api/search", response_model=List[SearchResult])
async def search_concepts(request: SearchRequest):
    """
    개념 검색

    30+ 학문 분야에서 시맨틱 유사성 기반으로 관련 개념을 검색합니다.
    """
    try:
        results = await rag_pipeline.search(
            query=request.query,
            domains=request.domains,
            limit=request.limit
        )

        return [
            SearchResult(
                name=r.name,
                domain=r.domain,
                description=r.description[:500] if hasattr(r, 'description') else "",
                similarity=r.similarity
            )
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search")
async def search_concepts_get(
    q: str = Query(..., description="검색 쿼리"),
    domains: Optional[str] = Query(None, description="도메인 목록 (쉼표 구분)"),
    limit: int = Query(10, description="결과 개수", ge=1, le=50)
):
    """GET 방식 개념 검색"""
    domain_list = domains.split(",") if domains else None
    request = SearchRequest(query=q, domains=domain_list, limit=limit)
    return await search_concepts(request)


# ===== 융합 사고 API =====

@app.post("/api/fusion/suggest")
async def suggest_fusion(request: FusionRequest):
    """
    융합 가능성 분석

    두 개념 간의 융합 가능성과 적용 가능한 패턴을 분석합니다.
    """
    try:
        # 두 개념 검색
        results_a = await rag_pipeline.search(request.concept_a, limit=1)
        results_b = await rag_pipeline.search(request.concept_b, limit=1)

        if not results_a or not results_b:
            raise HTTPException(status_code=404, detail="개념을 찾을 수 없습니다")

        concept_a = results_a[0]
        concept_b = results_b[0]

        # 노벨티 계산
        novelty = await rag_pipeline.calculate_concept_novelty(concept_a, concept_b)

        return {
            "concept_a": {"name": concept_a.name, "domain": concept_a.domain},
            "concept_b": {"name": concept_b.name, "domain": concept_b.domain},
            "novelty_score": round(novelty, 2),
            "novelty_level": "높음" if novelty > 0.7 else "중간" if novelty > 0.4 else "낮음",
            "suggested_patterns": [
                "구조적 동형 (Structural Isomorphism)",
                "은유적 전이 (Metaphorical Transfer)",
                "경계 개념 (Boundary Concept)"
            ],
            "exploration_questions": [
                f"{concept_a.domain}의 가정을 {concept_b.domain}에서 어떻게 볼까요?",
                f"두 개념이 공유하는 구조는 무엇인가요?",
                f"{concept_a.name}을 {concept_b.name}의 메타포로 사용하면?"
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/fusion/patterns")
async def get_fusion_patterns():
    """7가지 융합 사고 패턴 반환"""
    return {
        "patterns": [
            {
                "name": "은유적 전이 (Metaphorical Transfer)",
                "description": "한 분야의 개념을 다른 분야로 이전",
                "key_question": "X를 Y처럼 생각하면?"
            },
            {
                "name": "구조적 동형 (Structural Isomorphism)",
                "description": "다른 분야의 동일 구조 발견",
                "key_question": "어떤 구조가 반복되는가?"
            },
            {
                "name": "전제 전복 (Assumption Subversion)",
                "description": "다른 분야 관점에서 전제 도전",
                "key_question": "B 분야는 A의 전제를 어떻게 볼까?"
            },
            {
                "name": "스케일 점프 (Scale Jump)",
                "description": "미시/거시 수준에서 동일 원리 적용",
                "key_question": "다른 스케일에서도 이 패턴이?"
            },
            {
                "name": "시간축 변환 (Temporal Transformation)",
                "description": "다른 시간 척도로 현상 관찰",
                "key_question": "다른 시간 척도에선 어떤가?"
            },
            {
                "name": "경계 개념 (Boundary Concept)",
                "description": "분야를 가로지르는 개념 활용",
                "key_question": "어떤 개념이 분야의 경계에?"
            },
            {
                "name": "변증법적 종합 (Dialectical Synthesis)",
                "description": "대립 관점의 초월적 통합",
                "key_question": "테제와 안티테제를 어떻게 초월?"
            }
        ]
    }


# ===== 소크라테스 대화 API =====

@app.post("/api/socratic/start")
async def start_socratic_session(request: SocraticStartRequest):
    """
    소크라테스 대화 시작

    주제에 대한 깊은 탐구를 위한 새 대화 세션을 시작합니다.
    """
    try:
        response = await socratic_engine.start_dialogue(
            topic=request.topic,
            initial_position=request.initial_position,
            focus=request.focus,
            depth=request.depth
        )

        return {
            "session_id": response.session_id,
            "topic": request.topic,
            "questions": [
                {
                    "question": q.question,
                    "purpose": q.purpose,
                    "hints": q.follow_ups[:2]
                }
                for q in response.questions
            ],
            "related_concepts": response.related_concepts,
            "encouragement": response.encouragement,
            "difficulty": response.difficulty_feedback
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/socratic/continue")
async def continue_socratic(request: SocraticContinueRequest):
    """
    소크라테스 대화 계속

    사용자 응답을 분석하고 다음 탐구 질문을 생성합니다.
    """
    try:
        response = await socratic_engine.continue_dialogue(
            session_id=request.session_id,
            user_response=request.response
        )

        return {
            "session_id": response.session_id,
            "analysis": response.context_summary,
            "questions": [
                {
                    "question": q.question,
                    "purpose": q.purpose,
                    "hints": q.follow_ups[:2]
                }
                for q in response.questions
            ],
            "encouragement": response.encouragement,
            "progress": response.progress_update,
            "next_hint": response.next_step_hint
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/socratic/challenge")
async def challenge_statement(request: ChallengeRequest):
    """
    전제 도전

    진술의 숨겨진 전제를 분석하고 도전합니다.
    """
    try:
        result = await socratic_engine.challenge_statement(
            session_id=request.session_id,
            statement=request.statement,
            perspective=request.perspective
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/socratic/synthesize/{session_id}")
async def synthesize_dialogue(session_id: str):
    """
    대화 종합

    세션의 탐구 내용을 종합하고 통찰을 정리합니다.
    """
    try:
        result = await socratic_engine.synthesize_dialogue(session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== 학습 경로 API =====

@app.post("/api/learning/path")
async def get_learning_path(request: LearningPathRequest):
    """
    학습 경로 생성

    사용자 수준과 관심사에 맞는 맞춤형 학습 경로를 생성합니다.
    """
    try:
        path = await socratic_engine.get_learning_path(
            user_id="default",
            start_concept=request.start_concept,
            path_type=request.path_type,
            goal=request.goal
        )

        return {
            "id": path.id,
            "title": path.title,
            "description": path.description,
            "path_type": path.path_type.value,
            "total_concepts": path.total_concepts,
            "estimated_duration_minutes": path.estimated_duration,
            "difficulty_range": path.difficulty_range,
            "domains_covered": path.domains_covered,
            "learning_objectives": path.learning_objectives,
            "steps": [
                {
                    "concept": step.concept.name,
                    "domain": step.concept.domain,
                    "focus": step.focus,
                    "questions": step.questions,
                    "checkpoint": step.checkpoint,
                    "estimated_time": step.estimated_time
                }
                for step in path.steps
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/learning/progress")
async def get_learning_progress(user_id: str = "default"):
    """사용자 학습 진행 상황 조회"""
    try:
        progress = await socratic_engine.get_user_progress(user_id)
        return progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== 세션 관리 API =====

@app.get("/api/sessions")
async def list_sessions(
    user_id: str = Query("default"),
    status: str = Query("active", description="active, completed, all")
):
    """세션 목록 조회"""
    from src.engines.session_manager import get_session_manager

    session_mgr = get_session_manager()
    status_filter = None if status == "all" else status
    sessions = session_mgr.list_sessions(user_id, status_filter)
    return {"sessions": sessions}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """세션 상세 정보"""
    from src.engines.session_manager import get_session_manager

    session_mgr = get_session_manager()
    summary = session_mgr.get_session_summary(session_id)

    if not summary:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    return summary


@app.get("/api/sessions/{session_id}/export")
async def export_session(
    session_id: str,
    format: str = Query("markdown", description="markdown or json")
):
    """세션 내보내기"""
    from src.engines.session_manager import get_session_manager

    session_mgr = get_session_manager()
    exported = session_mgr.export_session(session_id, format)

    if not exported:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    if format == "json":
        return JSONResponse(content=json.loads(exported))
    else:
        return {"format": "markdown", "content": exported}


# ===== GPT Actions 전용 OpenAPI =====

@app.get("/gpt-openapi.json")
async def gpt_openapi():
    """GPT Actions용 간소화된 OpenAPI 스펙"""
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Polymath API",
            "description": "Interdisciplinary knowledge fusion API",
            "version": "2.0.0"
        },
        "servers": [{"url": "https://seanshin-mcp.ngrok.io"}],
        "paths": {
            "/api/search": {
                "get": {
                    "operationId": "searchConcepts",
                    "summary": "Search concepts across 30 academic domains",
                    "parameters": [
                        {"name": "q", "in": "query", "required": True, "schema": {"type": "string"}},
                        {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 10}}
                    ],
                    "responses": {"200": {"description": "Search results"}}
                }
            },
            "/api/domains": {
                "get": {
                    "operationId": "getDomains",
                    "summary": "List 30 academic domains",
                    "responses": {"200": {"description": "Domain list"}}
                }
            },
            "/api/fusion/patterns": {
                "get": {
                    "operationId": "getFusionPatterns",
                    "summary": "Get 7 fusion thinking patterns",
                    "responses": {"200": {"description": "Fusion patterns"}}
                }
            },
            "/api/fusion/suggest": {
                "post": {
                    "operationId": "suggestFusion",
                    "summary": "Analyze fusion between two concepts",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["concept_a", "concept_b"],
                                    "properties": {
                                        "concept_a": {"type": "string"},
                                        "concept_b": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Fusion analysis"}}
                }
            },
            "/api/socratic/start": {
                "post": {
                    "operationId": "startSocratic",
                    "summary": "Start a Socratic dialogue session",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["topic"],
                                    "properties": {
                                        "topic": {"type": "string"},
                                        "focus": {"type": "string", "default": "explore"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Session info with questions"}}
                }
            },
            "/api/socratic/continue": {
                "post": {
                    "operationId": "continueSocratic",
                    "summary": "Continue Socratic dialogue",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["session_id", "response"],
                                    "properties": {
                                        "session_id": {"type": "string"},
                                        "response": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Next questions"}}
                }
            },
            "/api/learning/path": {
                "post": {
                    "operationId": "getLearningPath",
                    "summary": "Generate personalized learning path",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["start_concept"],
                                    "properties": {
                                        "start_concept": {"type": "string"},
                                        "path_type": {"type": "string", "default": "spiral"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Learning path"}}
                }
            }
        }
    }


# ===== 도메인 정보 API =====

@app.get("/api/domains")
async def get_domains():
    """사용 가능한 학문 분야 목록"""
    return {
        "domains": [
            {"id": "philosophy", "name": "철학", "category": "인문학"},
            {"id": "physics", "name": "물리학", "category": "자연과학"},
            {"id": "mathematics", "name": "수학", "category": "형식과학"},
            {"id": "economics", "name": "경제학", "category": "사회과학"},
            {"id": "biology", "name": "생물학", "category": "자연과학"},
            {"id": "psychology", "name": "심리학", "category": "사회과학"},
            {"id": "computer_science", "name": "컴퓨터과학", "category": "형식과학"},
            {"id": "neuroscience", "name": "신경과학", "category": "자연과학"},
            {"id": "sociology", "name": "사회학", "category": "사회과학"},
            {"id": "linguistics", "name": "언어학", "category": "인문학"},
            {"id": "history", "name": "역사학", "category": "인문학"},
            {"id": "chemistry", "name": "화학", "category": "자연과학"},
            {"id": "ecology", "name": "생태학", "category": "자연과학"},
            {"id": "anthropology", "name": "인류학", "category": "사회과학"},
            {"id": "political_science", "name": "정치학", "category": "사회과학"},
            {"id": "law", "name": "법학", "category": "사회과학"},
            {"id": "engineering", "name": "공학", "category": "응용과학"},
            {"id": "medicine", "name": "의학", "category": "응용과학"},
            {"id": "information_theory", "name": "정보이론", "category": "형식과학"},
            {"id": "game_theory", "name": "게임이론", "category": "형식과학"},
            {"id": "complex_systems", "name": "복잡계과학", "category": "학제간"},
            {"id": "cognitive_science", "name": "인지과학", "category": "학제간"},
            {"id": "network_science", "name": "네트워크과학", "category": "학제간"},
            {"id": "thermodynamics", "name": "열역학", "category": "자연과학"},
            {"id": "quantum_mechanics", "name": "양자역학", "category": "자연과학"},
            {"id": "statistics", "name": "통계학", "category": "형식과학"},
            {"id": "logic", "name": "논리학", "category": "형식과학"},
            {"id": "art_history", "name": "미술사", "category": "인문학"},
            {"id": "music_theory", "name": "음악이론", "category": "인문학"},
            {"id": "literature", "name": "문학", "category": "인문학"}
        ],
        "total": 30
    }


# ===== 메인 실행 =====

def run_server(host: str = "0.0.0.0", port: int = 8000):
    """서버 실행"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
