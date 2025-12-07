"""
ChromaDB Re-seeder - 올바른 메타데이터 추출로 재인덱싱

기존 인덱서 버그 수정:
- 'domains' (복수) 필드에서 domain 추출
- 'title' 필드에서 name 추출
- 폴더 구조에서 category 추출
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


# Folder to category/domain mapping
FOLDER_CATEGORY_MAP = {
    "00-Fusion-Patterns": {"category": "fusion_pattern", "default_domain": "methodology"},
    "01-Fusion-Cases": {"category": "fusion_case", "default_domain": "interdisciplinary"},
    "02-Concepts": {"category": "concept", "default_domain": "transdisciplinary"},
    "03-Polymaths": {"category": "polymath", "default_domain": "biography"},
    "04-Big-Questions": {"category": "big_question", "default_domain": "philosophy"},
    "05-Hermeneutics": {"category": "hermeneutics", "default_domain": "hermeneutics"},
}


@dataclass
class DocumentChunk:
    """문서 청크"""
    id: str
    content: str
    metadata: Dict
    embedding: Optional[List[float]] = None


def parse_markdown(file_path: Path) -> Tuple[Dict, str]:
    """마크다운 파일 파싱"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    frontmatter = {}
    body = content

    if content.startswith('---'):
        end_idx = content.find('---', 3)
        if end_idx != -1:
            yaml_content = content[3:end_idx].strip()
            try:
                frontmatter = yaml.safe_load(yaml_content) or {}
            except yaml.YAMLError as e:
                print(f"Warning: Could not parse YAML in {file_path}: {e}")
            body = content[end_idx + 3:].strip()

    return frontmatter, body


def extract_domain(frontmatter: Dict, folder_name: str) -> str:
    """Extract domain from frontmatter or folder"""
    # Try 'domains' (plural array) first
    domains = frontmatter.get('domains', [])
    if domains:
        if isinstance(domains, list) and len(domains) > 0:
            return domains[0]  # Take first domain
        elif isinstance(domains, str):
            return domains

    # Try 'domain' (singular)
    domain = frontmatter.get('domain')
    if domain:
        return domain

    # Try 'parent_disciplines' for fusion cases
    parent_disciplines = frontmatter.get('parent_disciplines', [])
    if parent_disciplines:
        if isinstance(parent_disciplines, list) and len(parent_disciplines) > 0:
            return parent_disciplines[0]

    # Fall back to category-based default
    folder_info = FOLDER_CATEGORY_MAP.get(folder_name, {})
    return folder_info.get('default_domain', 'general')


def extract_name(frontmatter: Dict, file_stem: str) -> str:
    """Extract name from frontmatter or filename"""
    # Try 'title' first
    title = frontmatter.get('title')
    if title:
        return title

    # Try 'name'
    name = frontmatter.get('name')
    if name:
        return name

    # Fall back to filename
    return file_stem.replace('-', ' ').title()


def extract_category(frontmatter: Dict, folder_name: str) -> str:
    """Extract category from frontmatter or folder"""
    # Try frontmatter 'category'
    category = frontmatter.get('category')
    if category:
        return category

    # Fall back to folder mapping
    folder_info = FOLDER_CATEGORY_MAP.get(folder_name, {})
    return folder_info.get('category', folder_name)


def chunk_document(content: str, metadata: Dict, chunk_size: int = 1000) -> List[DocumentChunk]:
    """문서를 청크로 분할"""
    chunks = []
    doc_id = metadata.get('id', hashlib.md5(content.encode()).hexdigest()[:8])

    # Simple chunking by paragraphs
    paragraphs = content.split('\n\n')
    current_chunk = []
    current_length = 0
    chunk_idx = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_length = len(para)

        if current_length + para_length > chunk_size and current_chunk:
            # Save current chunk
            chunk_id = f"{doc_id}_{chunk_idx}"
            chunk_content = '\n\n'.join(current_chunk)
            chunk_metadata = {**metadata, 'chunk_index': chunk_idx}
            chunks.append(DocumentChunk(
                id=chunk_id,
                content=chunk_content,
                metadata=chunk_metadata
            ))
            chunk_idx += 1
            current_chunk = [para]
            current_length = para_length
        else:
            current_chunk.append(para)
            current_length += para_length

    # Save remaining chunk
    if current_chunk:
        chunk_id = f"{doc_id}_{chunk_idx}"
        chunk_content = '\n\n'.join(current_chunk)
        chunk_metadata = {**metadata, 'chunk_index': chunk_idx}
        chunks.append(DocumentChunk(
            id=chunk_id,
            content=chunk_content,
            metadata=chunk_metadata
        ))

    return chunks


def reseed_chroma(knowledge_path: Path, chroma_path: Path):
    """Re-seed ChromaDB with correct metadata"""

    print(f"Knowledge path: {knowledge_path}")
    print(f"ChromaDB path: {chroma_path}")

    # Initialize ChromaDB
    chroma_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(chroma_path),
        settings=ChromaSettings(anonymized_telemetry=False)
    )

    # Delete existing collection
    print("\nClearing existing collection...")
    try:
        client.delete_collection("polymath_concepts")
        print("  Deleted existing collection")
    except Exception as e:
        print(f"  No existing collection to delete: {e}")

    # Create new collection
    collection = client.create_collection(
        name="polymath_concepts",
        metadata={"description": "Polymath MCP knowledge embeddings"}
    )
    print("  Created new collection")

    # Find all markdown files
    md_files = list(knowledge_path.rglob("*.md"))
    print(f"\nFound {len(md_files)} markdown files")

    # Skip MOC files
    md_files = [f for f in md_files if 'MOC' not in f.stem.upper()]
    print(f"Processing {len(md_files)} files (excluding MOC files)")

    # Statistics
    stats = {
        'total_files': 0,
        'total_chunks': 0,
        'by_domain': {},
        'by_category': {}
    }

    # Index each file
    for file_path in md_files:
        try:
            # Parse markdown
            frontmatter, content = parse_markdown(file_path)

            # Skip if no content
            if not content.strip():
                print(f"Skipping empty file: {file_path.name}")
                continue

            # Get folder name for category/domain inference
            relative_path = file_path.relative_to(knowledge_path)
            folder_name = relative_path.parts[0] if len(relative_path.parts) > 1 else ""

            # Extract metadata
            name = extract_name(frontmatter, file_path.stem)
            domain = extract_domain(frontmatter, folder_name)
            category = extract_category(frontmatter, folder_name)

            metadata = {
                'id': frontmatter.get('key', file_path.stem),
                'name': name,
                'domain': domain,
                'category': category,
                'file_path': str(relative_path),
                'era': frontmatter.get('era', 'modern'),
                'scale': frontmatter.get('scale', 'meso'),
                'importance': frontmatter.get('importance', 'normal'),
            }

            # Create chunks
            chunks = chunk_document(content, metadata)

            if not chunks:
                print(f"Warning: No chunks for {file_path.name}")
                continue

            # Add to ChromaDB
            ids = [chunk.id for chunk in chunks]
            documents = [chunk.content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]

            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

            # Update stats
            stats['total_files'] += 1
            stats['total_chunks'] += len(chunks)
            stats['by_domain'][domain] = stats['by_domain'].get(domain, 0) + len(chunks)
            stats['by_category'][category] = stats['by_category'].get(category, 0) + len(chunks)

            print(f"  {file_path.name}: {name} | {domain} | {category} ({len(chunks)} chunks)")

        except Exception as e:
            print(f"Error indexing {file_path}: {e}")
            import traceback
            traceback.print_exc()

    # Print summary
    print(f"\n{'='*60}")
    print(f"Re-seeding Complete!")
    print(f"{'='*60}")
    print(f"Total files: {stats['total_files']}")
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"\nBy Domain ({len(stats['by_domain'])} unique):")
    for domain, count in sorted(stats['by_domain'].items(), key=lambda x: -x[1]):
        print(f"  {domain}: {count}")
    print(f"\nBy Category ({len(stats['by_category'])} unique):")
    for category, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
        print(f"  {category}: {count}")

    # Verify
    print(f"\nVerification:")
    print(f"  Collection count: {collection.count()}")

    # Sample check
    print(f"\nSample metadata (first 5):")
    sample = collection.get(limit=5, include=['metadatas'])
    for i, meta in enumerate(sample['metadatas']):
        print(f"  {i+1}. name={meta.get('name', '?')[:40]} | domain={meta.get('domain', '?')} | category={meta.get('category', '?')}")


def main():
    """메인 실행"""
    base_path = Path(__file__).parent.parent
    knowledge_path = base_path / "knowledge"
    chroma_path = base_path / "data" / "chroma"

    reseed_chroma(knowledge_path, chroma_path)


if __name__ == '__main__':
    main()
