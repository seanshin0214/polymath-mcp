#!/usr/bin/env python3
"""
Setup Script - Polymath MCP 초기 설정

1. 의존성 설치 확인
2. 지식 문서 인덱싱
3. 설정 검증
"""

import subprocess
import sys
from pathlib import Path


def check_dependencies():
    """필수 패키지 확인"""
    print("Checking dependencies...")

    required = [
        'chromadb',
        'sentence_transformers',
        'mcp',
        'pyyaml'
    ]

    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} (missing)")
            missing.append(pkg)

    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False

    return True


def index_knowledge():
    """지식 문서 인덱싱"""
    print("\nIndexing knowledge documents...")

    from index_knowledge import KnowledgeIndexer

    base_path = Path(__file__).parent.parent
    knowledge_path = base_path / "knowledge"
    chroma_path = base_path / "data" / "chroma"

    if not knowledge_path.exists():
        print(f"Knowledge path not found: {knowledge_path}")
        return False

    indexer = KnowledgeIndexer(knowledge_path, chroma_path)
    indexer.clear_index()
    stats = indexer.index_all()

    print("\nIndexing complete!")
    return True


def verify_setup():
    """설정 검증"""
    print("\nVerifying setup...")

    base_path = Path(__file__).parent.parent
    chroma_path = base_path / "data" / "chroma"

    if chroma_path.exists():
        print(f"  ✓ ChromaDB path exists: {chroma_path}")
    else:
        print(f"  ✗ ChromaDB path not found")
        return False

    # Test ChromaDB connection
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(chroma_path))
        collection = client.get_or_create_collection("polymath_concepts")
        count = collection.count()
        print(f"  ✓ ChromaDB connected ({count} documents)")
    except Exception as e:
        print(f"  ✗ ChromaDB error: {e}")
        return False

    return True


def print_next_steps():
    """다음 단계 안내"""
    base_path = Path(__file__).parent.parent

    print("\n" + "="*50)
    print("SETUP COMPLETE!")
    print("="*50)

    print(f"""
Next Steps:

1. Add to Claude Desktop config:

   Windows: %APPDATA%\\Claude\\claude_desktop_config.json
   Mac: ~/Library/Application Support/Claude/claude_desktop_config.json

   {{
     "mcpServers": {{
       "polymath": {{
         "command": "python",
         "args": ["-m", "src.server"],
         "cwd": "{base_path}",
         "env": {{
           "POLYMATH_BASE_PATH": "{base_path}"
         }}
       }}
     }}
   }}

2. Restart Claude Desktop

3. Test with:
   - "search_concepts" tool
   - "get_stats" tool
   - "get_fusion_patterns" tool

Happy thinking!
""")


def main():
    """메인 실행"""
    print("="*50)
    print("Polymath MCP Setup")
    print("="*50)

    # Check dependencies
    if not check_dependencies():
        print("\nPlease install missing dependencies first.")
        sys.exit(1)

    # Index knowledge
    if not index_knowledge():
        print("\nKnowledge indexing failed.")
        sys.exit(1)

    # Verify setup
    if not verify_setup():
        print("\nSetup verification failed.")
        sys.exit(1)

    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
