# Polymath MCP

> **컨셉공학을 위한 융합적 사고 지원 시스템**
>
> 30개 학문 분야의 지식을 융합하여 새로운 개념 창조를 지원하는 MCP 서버

## Overview

Polymath MCP는 단순한 RAG를 넘어, **융합적 사고(Fusion Thinking)**와 **소크라테스적 대화(Socratic Dialogue)**를 통해 연구자가 새로운 개념을 창조할 수 있도록 지원합니다.

### 핵심 특징

- **Fusion Engine**: 7가지 융합 패턴으로 분야 간 연결 탐지
- **Socratic Engine**: 답을 주지 않고 질문으로 이끄는 탐구적 대화
- **3층 지식 구조**: 개념 → 융합 패턴 → 융합 사례
- **Obsidian 연동**: 인간이 큐레이션, AI가 확장

## 7가지 융합 사고 패턴

| 패턴 | 설명 | 예시 |
|------|------|------|
| **은유적 전이** | A는 B와 같다 | 조직=유기체 |
| **구조적 동형** | 같은 구조, 다른 분야 | 진화 알고리즘 |
| **전제 전복** | A가 B의 전제 공격 | 행동경제학 |
| **스케일 점프** | 미시↔거시 이동 | 창발 |
| **시간축 변환** | 단기↔장기 원리 이동 | 문화 진화 |
| **경계 개념** | 여러 분야 공유 개념 | 네트워크, 정보 |
| **변증법적 종합** | 대립의 통합 | 구조-행위자 이중성 |

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/polymath-mcp.git
cd polymath-mcp

# Install dependencies
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

## Quick Start

```bash
# Run the MCP server
python -m src.server
```

## MCP Tools

### 탐구 도구 (Exploration)
- `search_concepts` - 개념 검색 (하이브리드)
- `trace_lineage` - 개념의 지적 계보 추적
- `get_fusion_cases` - 성공적 융합 사례 검색

### 융합 도구 (Fusion)
- `find_bridges` - 다른 분야와의 연결점 탐색
- `suggest_fusion` - 두 개념의 융합 가능성 분석
- `find_structural_analogies` - 구조적 유사성 탐지
- `evaluate_novelty` - 신규성 평가

### 소크라테스 대화 도구 (Socratic)
- `socratic_dialogue` - 소크라테스적 탐구 대화
- `challenge_premise` - 전제 도전
- `explore_viewpoints` - 다양한 관점 탐색

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  POLYMATH MCP SERVER                     │
├─────────────────────────────────────────────────────────┤
│  MCP Tools Layer                                         │
│  ├─ Exploration Tools                                    │
│  ├─ Fusion Tools                                         │
│  └─ Socratic Tools                                       │
├─────────────────────────────────────────────────────────┤
│  Core Engines                                            │
│  ├─ Fusion Engine (패턴 매칭, 구조 분석)                 │
│  ├─ Socratic Engine (질문 생성, 대화 관리)              │
│  └─ RAG Pipeline (하이브리드 검색)                       │
├─────────────────────────────────────────────────────────┤
│  Data Layer                                              │
│  ├─ ChromaDB (Vector Store)                             │
│  ├─ Neo4j (Graph DB)                                    │
│  └─ Obsidian Sync (File Watch)                          │
└─────────────────────────────────────────────────────────┘
```

## Knowledge Domains (30개 분야)

### 형식과학
수학, 논리학, 통계학, 컴퓨터과학

### 자연과학
양자물리학, 고전물리학, 천문학, 지구과학, 생물학, 화학

### 인문사회과학
철학, 역사, 사회학, 심리학, 조직심리학, 인류학, 경제학, 법학, 정의론, 종교학, 교육학, 행정학, 인문학

### 응용/공학
AI/ML, 로봇공학, BCI, 경영학, 이노베이션, 앙트레프레너십, 리더십, 예술/미학

## Development

```bash
# Run tests
pytest

# Format code
black src tests
ruff check src tests

# Type checking
mypy src
```

## Roadmap

- [x] Phase 0: 기획 완료
- [ ] Phase 1: MVP (4주) - 기본 RAG + 5개 분야
- [ ] Phase 2: 확장 (6주) - 소크라테스 엔진 + 30개 분야
- [ ] Phase 3: 고도화 (8주) - 커뮤니티 + AI 새 연결 생성

## License

MIT License

## Contributing

Contributions are welcome! Please read our contributing guidelines first.
