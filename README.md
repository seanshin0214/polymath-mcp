# Polymath MCP

**Your Second Brain for Interdisciplinary Knowledge**

> 30개 학문 분야의 지식을 융합하여 새로운 개념 창조를 지원하는 MCP 서버

## Features

- **Semantic Search**: ChromaDB 기반 시맨틱 검색으로 30+ 학문 분야의 개념 탐색
- **7 Fusion Patterns**: 은유적 전이, 구조적 동형, 전제 전복 등 7가지 융합 사고 패턴
- **Socratic Dialogue**: 소크라테스적 대화를 통한 깊은 탐구
- **Knowledge Addition**: 새로운 지식을 RAG 시스템에 동적 추가
- **Cross-Domain Bridges**: 분야 간 연결점 발견 및 융합 가능성 분석

## Quick Start

### 1. Install Dependencies

```bash
cd polymath-mcp
pip install -e .
```

### 2. Index Knowledge Documents

```bash
python scripts/index_knowledge.py --clear
```

### 3. Configure Claude Desktop

Edit your Claude Desktop config file:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "polymath": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "C:\\Users\\sshin\\Documents\\polymath-mcp",
      "env": {
        "POLYMATH_BASE_PATH": "C:\\Users\\sshin\\Documents\\polymath-mcp"
      }
    }
  }
}
```

### 4. Restart Claude Desktop

## Available Tools

### Core Search
- `search_concepts` - 개념 검색 (시맨틱 유사성 기반)
- `find_bridges` - 분야 간 연결점 발견

### Fusion Thinking
- `suggest_fusion` - 두 개념의 융합 가능성 분석
- `get_fusion_patterns` - 7가지 융합 사고 패턴 정보

### Socratic Dialogue
- `socratic_dialogue` - 소크라테스적 대화 탐구
- `challenge_premise` - 숨겨진 전제 도전

### Knowledge Management
- `add_knowledge` - 새 지식 문서 추가 (RAG에 동적 인덱싱)
- `get_stats` - 지식 베이스 통계

### Utility
- `get_domains` - 사용 가능한 학문 분야 목록
- `set_dialogue_mode` - 대화 모드 설정

## 7가지 융합 사고 패턴

| 패턴 | 설명 | 핵심 질문 |
|------|------|----------|
| **은유적 전이** | A를 B로 생각하기 | "X를 Y처럼 생각하면?" |
| **구조적 동형** | 다른 분야의 동일 구조 발견 | "어떤 구조가 반복되는가?" |
| **전제 전복** | 다른 분야 관점에서 전제 도전 | "B 분야는 A의 전제를 어떻게 볼까?" |
| **스케일 점프** | 미시/거시 수준에서 동일 원리 | "이 패턴이 다른 스케일에서도?" |
| **시간축 변환** | 다른 시간 척도로 현상 관찰 | "다른 시간 척도에선?" |
| **경계 개념** | 분야를 가로지르는 개념 활용 | "어떤 개념이 분야의 경계에?" |
| **변증법적 종합** | 대립 관점의 초월적 통합 | "테제와 안티테제를 어떻게 초월?" |

## Knowledge Structure

```
knowledge/
├── 00-Fusion-Patterns/     # 7가지 융합 사고 패턴
├── 01-Fusion-Cases/        # 역사적 융합 사례 (7개)
├── 02-Concepts/            # 핵심 크로스도메인 개념 (5개)
├── 03-Polymaths/           # 위대한 폴리매스 프로필 (5인)
└── 04-Big-Questions/       # 분야를 넘는 큰 질문 (5개)
```

## Adding Your Own Knowledge

### Option 1: Using the `add_knowledge` Tool

```
add_knowledge(
  content="Your knowledge content in markdown...",
  name="Concept Name",
  domain="philosophy",
  tags=["tag1", "tag2"]
)
```

### Option 2: Add Markdown Files

1. Add markdown files to `knowledge/` directory
2. Re-index: `python scripts/index_knowledge.py`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POLYMATH_BASE_PATH` | Project root path | Auto-detect |
| `CHROMA_PATH` | ChromaDB storage path | `./data/chroma` |
| `KNOWLEDGE_PATH` | Knowledge documents path | `./knowledge` |
| `USE_LOCAL_EMBEDDINGS` | Use local sentence-transformers | `true` |
| `USE_NEO4J` | Enable Neo4j graph store (optional) | `false` |

## Architecture

```
┌─────────────────────────────────────────┐
│             Claude Desktop              │
└─────────────────┬───────────────────────┘
                  │ MCP Protocol
┌─────────────────▼───────────────────────┐
│           Polymath MCP Server           │
├─────────────────────────────────────────┤
│  Tools: search, fusion, socratic, etc.  │
├─────────────────────────────────────────┤
│           RAG Pipeline                  │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │  ChromaDB   │  │  Neo4j (opt)    │   │
│  │  (Vector)   │  │  (Graph)        │   │
│  └─────────────┘  └─────────────────┘   │
├─────────────────────────────────────────┤
│         Knowledge Documents             │
│    (Markdown with YAML frontmatter)     │
└─────────────────────────────────────────┘
```

## Knowledge Domains (30개 분야)

### 형식과학
수학, 논리학, 통계학, 컴퓨터과학

### 자연과학
양자물리학, 고전물리학, 천문학, 지구과학, 생물학, 화학

### 인문사회과학
철학, 역사, 사회학, 심리학, 인류학, 경제학, 정치학, 법학, 언어학

### 응용/공학
AI/ML, 공학, 의학, 경영학, 인지과학, 정보이론, 게임이론, 네트워크과학

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src tests
ruff check src tests

# Type checking
mypy src
```

## License

MIT License
