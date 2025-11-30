"""
Knowledge Indexer - 지식 문서 인덱싱

마크다운 지식 문서를 파싱하여 ChromaDB에 인덱싱
"""

import os
import sys
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

import yaml
import chromadb
from chromadb.config import Settings as ChromaSettings

# Sentence Transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    print("Warning: sentence-transformers not installed. Install with: pip install sentence-transformers")


@dataclass
class DocumentChunk:
    """문서 청크"""
    id: str
    content: str
    metadata: Dict
    embedding: Optional[List[float]] = None


class KnowledgeIndexer:
    """
    지식 문서 인덱서

    - 마크다운 파싱
    - YAML frontmatter 추출
    - 청킹 및 임베딩
    - ChromaDB 저장
    """

    def __init__(
        self,
        knowledge_path: Path,
        chroma_path: Path,
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ):
        self.knowledge_path = Path(knowledge_path)
        self.chroma_path = Path(chroma_path)
        self.embedding_model_name = embedding_model

        # Initialize ChromaDB
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.chroma_path),
            settings=ChromaSettings(anonymized_telemetry=False)
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="polymath_concepts",
            metadata={"description": "Polymath MCP knowledge embeddings"}
        )

        # Initialize embedding model
        self.embedding_model = None
        if HAS_SENTENCE_TRANSFORMERS:
            print(f"Loading embedding model: {embedding_model}")
            self.embedding_model = SentenceTransformer(embedding_model)
            print("Embedding model loaded!")

    def parse_markdown(self, file_path: Path) -> Tuple[Dict, str]:
        """
        마크다운 파일 파싱

        Returns:
            (frontmatter_dict, content_str)
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract YAML frontmatter
        frontmatter = {}
        body = content

        if content.startswith('---'):
            # Find end of frontmatter
            end_idx = content.find('---', 3)
            if end_idx != -1:
                yaml_content = content[3:end_idx].strip()
                try:
                    frontmatter = yaml.safe_load(yaml_content) or {}
                except yaml.YAMLError:
                    print(f"Warning: Could not parse YAML in {file_path}")
                body = content[end_idx + 3:].strip()

        return frontmatter, body

    def extract_sections(self, content: str) -> Dict[str, str]:
        """
        마크다운 섹션 추출

        헤더(##, ###)로 구분된 섹션들을 추출
        """
        sections = {}
        current_section = "introduction"
        current_content = []

        for line in content.split('\n'):
            # Check for headers
            header_match = re.match(r'^(#{1,3})\s+(.+)$', line)
            if header_match:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()

                # Start new section
                current_section = header_match.group(2).lower().replace(' ', '_')
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    def chunk_document(
        self,
        content: str,
        metadata: Dict,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[DocumentChunk]:
        """
        문서를 청크로 분할

        - 섹션 경계 존중
        - 의미 단위 유지
        """
        chunks = []
        doc_id = metadata.get('id', hashlib.md5(content.encode()).hexdigest()[:8])

        # First, try to split by sections
        sections = self.extract_sections(content)

        chunk_idx = 0
        for section_name, section_content in sections.items():
            if not section_content.strip():
                continue

            # If section is small enough, keep as one chunk
            if len(section_content) <= chunk_size:
                chunk_id = f"{doc_id}_{chunk_idx}"
                chunk_metadata = {
                    **metadata,
                    'section': section_name,
                    'chunk_index': chunk_idx
                }
                chunks.append(DocumentChunk(
                    id=chunk_id,
                    content=section_content,
                    metadata=chunk_metadata
                ))
                chunk_idx += 1
            else:
                # Split large sections by paragraphs
                paragraphs = section_content.split('\n\n')
                current_chunk = []
                current_length = 0

                for para in paragraphs:
                    para_length = len(para)

                    if current_length + para_length > chunk_size and current_chunk:
                        # Save current chunk
                        chunk_id = f"{doc_id}_{chunk_idx}"
                        chunk_metadata = {
                            **metadata,
                            'section': section_name,
                            'chunk_index': chunk_idx
                        }
                        chunks.append(DocumentChunk(
                            id=chunk_id,
                            content='\n\n'.join(current_chunk),
                            metadata=chunk_metadata
                        ))
                        chunk_idx += 1

                        # Start new chunk with overlap
                        if overlap > 0 and len(current_chunk) > 0:
                            overlap_text = current_chunk[-1]
                            current_chunk = [overlap_text, para]
                            current_length = len(overlap_text) + para_length
                        else:
                            current_chunk = [para]
                            current_length = para_length
                    else:
                        current_chunk.append(para)
                        current_length += para_length

                # Save remaining chunk
                if current_chunk:
                    chunk_id = f"{doc_id}_{chunk_idx}"
                    chunk_metadata = {
                        **metadata,
                        'section': section_name,
                        'chunk_index': chunk_idx
                    }
                    chunks.append(DocumentChunk(
                        id=chunk_id,
                        content='\n\n'.join(current_chunk),
                        metadata=chunk_metadata
                    ))
                    chunk_idx += 1

        return chunks

    def generate_embeddings(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """청크에 임베딩 생성"""
        if not self.embedding_model:
            print("Warning: No embedding model available, skipping embedding generation")
            return chunks

        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)

        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding.tolist()

        return chunks

    def index_file(self, file_path: Path) -> int:
        """
        단일 파일 인덱싱

        Returns:
            인덱싱된 청크 수
        """
        print(f"Indexing: {file_path.name}")

        # Parse markdown
        frontmatter, content = self.parse_markdown(file_path)

        # Determine category from path
        relative_path = file_path.relative_to(self.knowledge_path)
        category = relative_path.parts[0] if relative_path.parts else "general"

        # Build metadata
        metadata = {
            'id': frontmatter.get('id', file_path.stem),
            'name': frontmatter.get('title', file_path.stem.replace('-', ' ').title()),
            'domain': frontmatter.get('domain', 'general'),
            'category': category,
            'file_path': str(relative_path),
            'tags': ','.join(frontmatter.get('tags', [])),
            'type': frontmatter.get('type', 'concept')
        }

        # Create chunks
        chunks = self.chunk_document(content, metadata)

        if not chunks:
            print(f"  Warning: No chunks created for {file_path.name}")
            return 0

        # Generate embeddings
        chunks = self.generate_embeddings(chunks)

        # Store in ChromaDB
        ids = [chunk.id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        embeddings = [chunk.embedding for chunk in chunks if chunk.embedding]

        # Check if we have embeddings
        if embeddings and len(embeddings) == len(chunks):
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
        else:
            # Add without embeddings (ChromaDB will generate them)
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

        print(f"  Added {len(chunks)} chunks")
        return len(chunks)

    def index_all(self) -> Dict[str, int]:
        """
        모든 지식 문서 인덱싱

        Returns:
            카테고리별 인덱싱 통계
        """
        stats = {}
        total_chunks = 0

        # Find all markdown files
        md_files = list(self.knowledge_path.rglob("*.md"))
        print(f"Found {len(md_files)} markdown files")

        for file_path in md_files:
            try:
                num_chunks = self.index_file(file_path)

                # Track by category
                category = file_path.parent.name
                if category not in stats:
                    stats[category] = {'files': 0, 'chunks': 0}
                stats[category]['files'] += 1
                stats[category]['chunks'] += num_chunks
                total_chunks += num_chunks

            except Exception as e:
                print(f"Error indexing {file_path}: {e}")

        print(f"\n=== Indexing Complete ===")
        print(f"Total files: {len(md_files)}")
        print(f"Total chunks: {total_chunks}")
        print(f"\nBy category:")
        for cat, info in stats.items():
            print(f"  {cat}: {info['files']} files, {info['chunks']} chunks")

        return stats

    def clear_index(self):
        """인덱스 초기화"""
        print("Clearing existing index...")
        # Delete and recreate collection
        try:
            self.client.delete_collection("polymath_concepts")
        except:
            pass

        self.collection = self.client.create_collection(
            name="polymath_concepts",
            metadata={"description": "Polymath MCP knowledge embeddings"}
        )
        print("Index cleared!")

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        테스트용 검색
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            include=["documents", "metadatas", "distances"]
        )

        items = []
        if results and results['ids']:
            for i, id in enumerate(results['ids'][0]):
                items.append({
                    'id': id,
                    'name': results['metadatas'][0][i].get('name', 'Unknown'),
                    'domain': results['metadatas'][0][i].get('domain', 'general'),
                    'distance': results['distances'][0][i],
                    'content': results['documents'][0][i][:200] + '...'
                })

        return items


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description='Index knowledge documents for Polymath MCP')
    parser.add_argument('--knowledge-path', type=str, default='./knowledge',
                        help='Path to knowledge directory')
    parser.add_argument('--chroma-path', type=str, default='./data/chroma',
                        help='Path to ChromaDB storage')
    parser.add_argument('--clear', action='store_true',
                        help='Clear existing index before indexing')
    parser.add_argument('--test', type=str, default=None,
                        help='Test search query after indexing')

    args = parser.parse_args()

    # Resolve paths
    base_path = Path(__file__).parent.parent
    knowledge_path = base_path / args.knowledge_path
    chroma_path = base_path / args.chroma_path

    print(f"Knowledge path: {knowledge_path}")
    print(f"ChromaDB path: {chroma_path}")

    # Initialize indexer
    indexer = KnowledgeIndexer(knowledge_path, chroma_path)

    # Clear if requested
    if args.clear:
        indexer.clear_index()

    # Index all documents
    stats = indexer.index_all()

    # Test search if requested
    if args.test:
        print(f"\n=== Test Search: '{args.test}' ===")
        results = indexer.search(args.test)
        for r in results:
            print(f"\n[{r['name']}] ({r['domain']}) - distance: {r['distance']:.3f}")
            print(f"  {r['content']}")


if __name__ == '__main__':
    main()
