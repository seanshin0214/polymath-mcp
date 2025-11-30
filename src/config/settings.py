"""
Settings - 설정 관리

환경 변수 및 설정 관리
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


def get_base_path() -> Path:
    """프로젝트 루트 경로 반환"""
    # 1. 환경 변수에서
    if env_path := os.getenv("POLYMATH_BASE_PATH"):
        return Path(env_path)

    # 2. 파일 위치 기반
    return Path(__file__).parent.parent.parent


@dataclass
class Settings:
    """
    Polymath MCP 설정

    환경 변수에서 설정을 로드하거나 기본값 사용
    """

    # Paths - 기본값은 __post_init__에서 설정
    base_path: Path = field(default_factory=get_base_path)
    chroma_path: Optional[Path] = None
    knowledge_path: Optional[Path] = None

    # Neo4j (optional)
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # OpenAI (for embeddings - optional)
    openai_api_key: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"

    # Sentence Transformers (alternative embeddings - recommended)
    use_local_embeddings: bool = True
    local_embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # Dialogue settings
    default_dialogue_mode: str = "hybrid"
    default_depth: str = "medium"

    # RAG settings
    vector_weight: float = 0.6
    graph_weight: float = 0.4
    max_results: int = 10
    similarity_threshold: float = 0.3

    def __post_init__(self):
        """환경 변수에서 설정 로드 및 경로 초기화"""

        # Set base path from environment if provided
        if env_base := os.getenv("POLYMATH_BASE_PATH"):
            self.base_path = Path(env_base)

        # Set derived paths
        if self.chroma_path is None:
            chroma_env = os.getenv("CHROMA_PATH")
            if chroma_env:
                self.chroma_path = Path(chroma_env)
            else:
                self.chroma_path = self.base_path / "data" / "chroma"

        if self.knowledge_path is None:
            knowledge_env = os.getenv("KNOWLEDGE_PATH")
            if knowledge_env:
                self.knowledge_path = Path(knowledge_env)
            else:
                self.knowledge_path = self.base_path / "knowledge"

        # Neo4j settings (optional)
        self.neo4j_uri = os.getenv("NEO4J_URI", self.neo4j_uri)
        self.neo4j_user = os.getenv("NEO4J_USER", self.neo4j_user)
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", self.neo4j_password)

        # OpenAI
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Boolean settings
        self.use_local_embeddings = os.getenv("USE_LOCAL_EMBEDDINGS", "true").lower() == "true"

        # Numeric settings
        try:
            self.vector_weight = float(os.getenv("VECTOR_WEIGHT", str(self.vector_weight)))
            self.graph_weight = float(os.getenv("GRAPH_WEIGHT", str(self.graph_weight)))
        except ValueError:
            pass

        # Create directories if needed
        self.chroma_path.mkdir(parents=True, exist_ok=True)

    def validate(self) -> bool:
        """설정 유효성 검사"""
        errors = []

        # Check required paths
        if not self.knowledge_path.exists():
            print(f"Warning: Knowledge path not found: {self.knowledge_path}")
            # Not a hard error - can be created later

        # Check embeddings configuration
        if not self.use_local_embeddings and not self.openai_api_key:
            errors.append("OpenAI API key required when not using local embeddings")

        if errors:
            for error in errors:
                print(f"Configuration error: {error}")
            return False

        return True

    def to_dict(self) -> dict:
        """설정을 딕셔너리로 변환"""
        return {
            "base_path": str(self.base_path),
            "chroma_path": str(self.chroma_path),
            "knowledge_path": str(self.knowledge_path),
            "neo4j_uri": self.neo4j_uri,
            "use_local_embeddings": self.use_local_embeddings,
            "default_dialogue_mode": self.default_dialogue_mode,
            "vector_weight": self.vector_weight,
            "graph_weight": self.graph_weight,
        }

    def __repr__(self) -> str:
        return f"Settings(base={self.base_path}, chroma={self.chroma_path}, knowledge={self.knowledge_path})"
