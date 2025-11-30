"""
Settings - 설정 관리

환경 변수 및 설정 관리
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Settings:
    """
    Polymath MCP 설정

    환경 변수에서 설정을 로드하거나 기본값 사용
    """

    # Paths
    base_path: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    chroma_path: Path = field(default_factory=lambda: Path("./data/chroma"))
    obsidian_vault_path: Path = field(default_factory=lambda: Path("./knowledge"))

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # OpenAI (for embeddings)
    openai_api_key: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"

    # Sentence Transformers (alternative embeddings)
    use_local_embeddings: bool = True
    local_embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # Obsidian sync
    watch_vault: bool = True
    sync_interval_seconds: int = 60

    # Dialogue settings
    default_dialogue_mode: str = "hybrid"
    default_depth: str = "medium"

    # RAG settings
    vector_weight: float = 0.6  # Weight for vector search in hybrid
    graph_weight: float = 0.4  # Weight for graph search in hybrid
    max_results: int = 10
    similarity_threshold: float = 0.3

    def __post_init__(self):
        """환경 변수에서 설정 로드"""
        # Load from environment variables
        self.neo4j_uri = os.getenv("NEO4J_URI", self.neo4j_uri)
        self.neo4j_user = os.getenv("NEO4J_USER", self.neo4j_user)
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", self.neo4j_password)

        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Paths from environment
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
        if vault_path:
            self.obsidian_vault_path = Path(vault_path)

        chroma_path = os.getenv("CHROMA_PATH")
        if chroma_path:
            self.chroma_path = Path(chroma_path)

        # Boolean settings
        self.use_local_embeddings = os.getenv("USE_LOCAL_EMBEDDINGS", "true").lower() == "true"
        self.watch_vault = os.getenv("WATCH_VAULT", "true").lower() == "true"

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
        if not self.obsidian_vault_path.exists():
            errors.append(f"Obsidian vault not found: {self.obsidian_vault_path}")

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
            "obsidian_vault_path": str(self.obsidian_vault_path),
            "neo4j_uri": self.neo4j_uri,
            "use_local_embeddings": self.use_local_embeddings,
            "watch_vault": self.watch_vault,
            "default_dialogue_mode": self.default_dialogue_mode,
            "vector_weight": self.vector_weight,
            "graph_weight": self.graph_weight,
        }
