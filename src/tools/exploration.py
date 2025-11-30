"""
Exploration Tools - 탐구 도구

개념 검색, 계보 추적, 융합 사례 검색 등
"""

from typing import List, Optional
from mcp.server import Server
from mcp.types import TextContent

from src.models.concept import Concept, ConceptLineage
from src.models.fusion import FusionCase


def register_exploration_tools(server: Server):
    """Register exploration tools with the MCP server"""

    @server.call_tool()
    async def search_concepts(
        query: str,
        domains: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[TextContent]:
        """
        개념 검색 - 하이브리드 (시맨틱 + 그래프)

        Args:
            query: 검색 쿼리
            domains: 필터링할 도메인 목록 (선택)
            limit: 반환할 최대 결과 수

        Returns:
            검색된 개념 목록
        """
        from src.server import rag_pipeline

        results = await rag_pipeline.search(
            query=query,
            domains=domains,
            limit=limit
        )

        # Format results
        formatted = []
        for concept in results:
            formatted.append(TextContent(
                type="text",
                text=f"""
**{concept.name}** ({concept.domain})

{concept.description}

관련 개념: {', '.join(concept.related_concepts[:5])}
융합 가능성: {', '.join(concept.bridge_domains[:3])}
"""
            ))

        return formatted

    @server.call_tool()
    async def trace_lineage(
        concept_id: str,
        direction: str = "both"
    ) -> List[TextContent]:
        """
        개념의 지적 계보 추적

        Args:
            concept_id: 개념 ID
            direction: ancestors(선조), descendants(후손), both(양쪽)

        Returns:
            개념 계보 정보
        """
        from src.server import rag_pipeline

        lineage = await rag_pipeline.get_lineage(
            concept_id=concept_id,
            direction=direction
        )

        return [TextContent(
            type="text",
            text=f"""
## {lineage.concept.name}의 지적 계보

### 선조 개념 (Ancestors)
{_format_concepts(lineage.ancestors)}

### 후손 개념 (Descendants)
{_format_concepts(lineage.descendants)}

### 핵심 영향
{lineage.key_influences}
"""
        )]

    @server.call_tool()
    async def get_fusion_cases(
        pattern: Optional[str] = None,
        domains: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[TextContent]:
        """
        성공적 융합 사례 검색

        Args:
            pattern: 특정 융합 패턴으로 필터링 (선택)
            domains: 관련 도메인으로 필터링 (선택)
            limit: 반환할 최대 결과 수

        Returns:
            융합 사례 목록
        """
        from src.server import rag_pipeline

        cases = await rag_pipeline.get_fusion_cases(
            pattern=pattern,
            domains=domains,
            limit=limit
        )

        formatted = []
        for case in cases:
            formatted.append(TextContent(
                type="text",
                text=f"""
## {case.name}

**창시자**: {case.creator}
**융합 패턴**: {case.pattern}

### 원천 개념들
{_format_source_concepts(case.source_concepts)}

### 융합 통찰
> {case.insight}

### 복제 가능한 패턴
{case.replicable_pattern}
"""
            ))

        return formatted

    @server.call_tool()
    async def get_domains() -> List[TextContent]:
        """
        사용 가능한 학문 분야 목록 반환

        Returns:
            도메인 목록 및 설명
        """
        domains = {
            "형식과학": ["mathematics", "logic", "statistics", "computer_science"],
            "자연과학": ["quantum_physics", "classical_physics", "astronomy",
                      "earth_science", "biology", "chemistry"],
            "인문사회과학": ["philosophy", "history", "sociology", "psychology",
                         "organizational_psychology", "anthropology", "economics",
                         "law", "justice_theory", "religious_studies", "education",
                         "public_administration", "humanities"],
            "응용/공학": ["ai_ml", "robotics", "bci", "management", "innovation",
                       "entrepreneurship", "leadership", "art_aesthetics"]
        }

        text = "## 사용 가능한 학문 분야 (30개)\n\n"
        for category, domain_list in domains.items():
            text += f"### {category}\n"
            for domain in domain_list:
                text += f"- `{domain}`\n"
            text += "\n"

        return [TextContent(type="text", text=text)]


def _format_concepts(concepts: List[Concept]) -> str:
    """Format concept list for display"""
    if not concepts:
        return "- (없음)"
    return "\n".join([f"- **{c.name}** ({c.domain}): {c.short_description}" for c in concepts])


def _format_source_concepts(sources: List[dict]) -> str:
    """Format source concepts for fusion case"""
    lines = []
    for src in sources:
        lines.append(f"- **{src['concept']}** ({src['domain']}): {src['role']}")
    return "\n".join(lines)
