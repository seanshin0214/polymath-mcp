"""
Learning Path System - 학습 경로 시스템

개념 그래프 기반의 적응형 학습 경로 생성
사용자 수준과 목표에 맞는 탐구 여정 설계
"""

from typing import List, Optional, Dict, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random


class PathType(Enum):
    """학습 경로 유형"""
    DEPTH_FIRST = "depth_first"      # 깊이 우선 (한 개념 깊이 탐구)
    BREADTH_FIRST = "breadth_first"  # 너비 우선 (넓게 연결)
    SPIRAL = "spiral"                # 나선형 (점진적 심화)
    BRIDGE = "bridge"                # 다리 (두 분야 연결)
    CHALLENGE = "challenge"          # 도전 (어려운 개념 중심)


class ConceptDifficulty(Enum):
    """개념 난이도"""
    FOUNDATIONAL = 1  # 기초
    INTERMEDIATE = 2  # 중급
    ADVANCED = 3      # 고급
    EXPERT = 4        # 전문가
    FRONTIER = 5      # 최전선


@dataclass
class ConceptNode:
    """개념 노드"""
    id: str
    name: str
    domain: str
    difficulty: ConceptDifficulty
    prerequisites: List[str] = field(default_factory=list)
    related: List[str] = field(default_factory=list)
    description: str = ""
    key_questions: List[str] = field(default_factory=list)
    fusion_potential: List[str] = field(default_factory=list)  # 융합 가능 분야


@dataclass
class PathStep:
    """경로의 한 단계"""
    concept: ConceptNode
    focus: str  # 이 단계의 초점
    questions: List[str]  # 탐구 질문
    connections: List[str]  # 이전 단계와의 연결
    estimated_time: int  # 예상 시간 (분)
    checkpoint: str  # 이해 확인 질문


@dataclass
class LearningPath:
    """완성된 학습 경로"""
    id: str
    title: str
    description: str
    path_type: PathType
    steps: List[PathStep]
    total_concepts: int
    estimated_duration: int  # 분
    difficulty_range: Tuple[int, int]
    domains_covered: List[str]
    learning_objectives: List[str]


class LearningPathGenerator:
    """
    학습 경로 생성기

    기능:
    - 개념 그래프 기반 경로 생성
    - 사용자 수준 맞춤
    - 다양한 경로 유형 지원
    - 융합적 탐구 경로
    """

    # 핵심 개념 그래프 (하드코딩된 기본 구조)
    CONCEPT_GRAPH = {
        # 02-Concepts의 핵심 개념들
        "entropy": ConceptNode(
            id="entropy",
            name="엔트로피",
            domain="physics",
            difficulty=ConceptDifficulty.INTERMEDIATE,
            prerequisites=[],
            related=["information", "equilibrium", "complexity"],
            description="무질서도, 정보, 불확실성의 척도",
            key_questions=[
                "엔트로피는 왜 항상 증가하는가?",
                "정보 엔트로피와 열역학 엔트로피는 같은 것인가?",
                "생명은 어떻게 엔트로피를 '극복'하는가?"
            ],
            fusion_potential=["information_theory", "biology", "economics"]
        ),
        "information": ConceptNode(
            id="information",
            name="정보",
            domain="information_theory",
            difficulty=ConceptDifficulty.INTERMEDIATE,
            prerequisites=[],
            related=["entropy", "complexity", "computation"],
            description="차이를 만드는 차이, 불확실성의 감소",
            key_questions=[
                "정보란 무엇인가?",
                "물리적 실체인가, 추상적 개념인가?",
                "정보는 보존되는가?"
            ],
            fusion_potential=["physics", "biology", "philosophy"]
        ),
        "emergence": ConceptNode(
            id="emergence",
            name="창발",
            domain="complex_systems",
            difficulty=ConceptDifficulty.ADVANCED,
            prerequisites=["complexity"],
            related=["complexity", "self-organization", "hierarchy"],
            description="전체는 부분의 합 이상이다",
            key_questions=[
                "창발은 환원 가능한가?",
                "약한 창발과 강한 창발의 차이는?",
                "의식은 창발적 현상인가?"
            ],
            fusion_potential=["neuroscience", "philosophy", "sociology"]
        ),
        "equilibrium": ConceptNode(
            id="equilibrium",
            name="평형",
            domain="physics",
            difficulty=ConceptDifficulty.FOUNDATIONAL,
            prerequisites=[],
            related=["entropy", "feedback", "stability"],
            description="변화가 없는 상태, 또는 힘의 균형",
            key_questions=[
                "평형 상태는 어떻게 도달하는가?",
                "비평형 상태는 왜 중요한가?",
                "경제적 평형과 물리적 평형의 유사성은?"
            ],
            fusion_potential=["economics", "ecology", "game_theory"]
        ),
        "feedback": ConceptNode(
            id="feedback",
            name="피드백",
            domain="cybernetics",
            difficulty=ConceptDifficulty.FOUNDATIONAL,
            prerequisites=[],
            related=["equilibrium", "control", "self-organization"],
            description="출력이 입력에 영향을 주는 순환",
            key_questions=[
                "양성 피드백과 음성 피드백의 역할은?",
                "피드백 루프는 어떻게 안정성을 만드는가?",
                "사회 시스템의 피드백은?"
            ],
            fusion_potential=["biology", "economics", "psychology"]
        ),
        "optimization": ConceptNode(
            id="optimization",
            name="최적화",
            domain="mathematics",
            difficulty=ConceptDifficulty.INTERMEDIATE,
            prerequisites=["feedback"],
            related=["equilibrium", "evolution", "adaptation"],
            description="제약 하에서 최선의 해 찾기",
            key_questions=[
                "자연은 최적화하는가?",
                "전역 최적과 국소 최적의 차이는?",
                "최적화의 한계는 무엇인가?"
            ],
            fusion_potential=["biology", "economics", "engineering"]
        ),
        "complexity": ConceptNode(
            id="complexity",
            name="복잡성",
            domain="complex_systems",
            difficulty=ConceptDifficulty.ADVANCED,
            prerequisites=["entropy", "information"],
            related=["emergence", "self-organization", "chaos"],
            description="단순함과 무작위 사이의 흥미로운 영역",
            key_questions=[
                "복잡성은 어떻게 측정하는가?",
                "복잡성은 어디서 오는가?",
                "복잡계는 예측 가능한가?"
            ],
            fusion_potential=["all_domains"]
        ),
    }

    # 분야 간 연결 다리
    DOMAIN_BRIDGES = {
        ("physics", "biology"): ["entropy", "information", "self-organization"],
        ("physics", "economics"): ["equilibrium", "optimization", "entropy"],
        ("biology", "economics"): ["evolution", "adaptation", "competition"],
        ("philosophy", "neuroscience"): ["consciousness", "emergence", "causation"],
        ("mathematics", "physics"): ["symmetry", "optimization", "structure"],
        ("computer_science", "biology"): ["information", "algorithm", "network"],
    }

    def __init__(self, rag_pipeline=None):
        """
        Args:
            rag_pipeline: RAG 파이프라인 (개념 검색용)
        """
        self.rag = rag_pipeline
        self.concept_graph = self.CONCEPT_GRAPH.copy()

    async def generate_path(
        self,
        start_concept: str,
        goal: Optional[str] = None,
        path_type: PathType = PathType.SPIRAL,
        user_level: int = 2,
        max_steps: int = 7,
        focus_domains: Optional[List[str]] = None
    ) -> LearningPath:
        """
        학습 경로 생성

        Args:
            start_concept: 시작 개념
            goal: 목표 개념 (선택)
            path_type: 경로 유형
            user_level: 사용자 수준 (1-5)
            max_steps: 최대 단계 수
            focus_domains: 집중할 분야들
        """
        # 경로 유형에 따른 생성
        if path_type == PathType.DEPTH_FIRST:
            steps = await self._generate_depth_first(
                start_concept, user_level, max_steps
            )
        elif path_type == PathType.BREADTH_FIRST:
            steps = await self._generate_breadth_first(
                start_concept, user_level, max_steps
            )
        elif path_type == PathType.BRIDGE:
            steps = await self._generate_bridge_path(
                start_concept, goal, user_level, max_steps
            )
        elif path_type == PathType.CHALLENGE:
            steps = await self._generate_challenge_path(
                start_concept, user_level, max_steps
            )
        else:  # SPIRAL (기본)
            steps = await self._generate_spiral_path(
                start_concept, user_level, max_steps
            )

        # 경로 메타데이터 계산
        domains = list(set(step.concept.domain for step in steps))
        difficulties = [step.concept.difficulty.value for step in steps]
        total_time = sum(step.estimated_time for step in steps)

        # 학습 목표 생성
        objectives = self._generate_objectives(steps, path_type)

        return LearningPath(
            id=f"path_{start_concept}_{path_type.value}",
            title=f"{start_concept} 탐구 여정 ({path_type.value})",
            description=self._generate_path_description(steps, path_type),
            path_type=path_type,
            steps=steps,
            total_concepts=len(steps),
            estimated_duration=total_time,
            difficulty_range=(min(difficulties), max(difficulties)),
            domains_covered=domains,
            learning_objectives=objectives
        )

    async def _generate_spiral_path(
        self,
        start: str,
        level: int,
        max_steps: int
    ) -> List[PathStep]:
        """나선형 경로: 점진적 심화"""
        steps = []
        visited = set()
        current = start

        for i in range(max_steps):
            concept = self._get_concept(current)
            if not concept or current in visited:
                break

            visited.add(current)

            # 난이도에 따른 초점 결정
            if i < max_steps // 3:
                focus = "기초 이해"
            elif i < 2 * max_steps // 3:
                focus = "연결과 적용"
            else:
                focus = "심층 탐구와 종합"

            step = PathStep(
                concept=concept,
                focus=focus,
                questions=concept.key_questions[:2],
                connections=[s.concept.name for s in steps[-2:]] if steps else [],
                estimated_time=15 + (i * 5),  # 점진적 시간 증가
                checkpoint=f"{concept.name}의 핵심을 한 문장으로 설명할 수 있는가?"
            )
            steps.append(step)

            # 다음 개념 선택 (관련 → 융합 가능 → 선행)
            next_candidates = concept.related + concept.fusion_potential
            next_candidates = [c for c in next_candidates if c not in visited]

            if next_candidates:
                # 사용자 수준에 맞는 개념 선택
                current = self._select_by_level(next_candidates, level)
            else:
                break

        return steps

    async def _generate_depth_first(
        self,
        start: str,
        level: int,
        max_steps: int
    ) -> List[PathStep]:
        """깊이 우선: 한 개념의 깊은 탐구"""
        steps = []
        concept = self._get_concept(start)

        if not concept:
            return steps

        # 같은 개념을 다른 깊이로 탐구
        depths = ["정의와 기원", "핵심 원리", "수학적 형식", "분야별 적용", "한계와 논쟁"]

        for i, depth in enumerate(depths[:max_steps]):
            step = PathStep(
                concept=concept,
                focus=depth,
                questions=self._questions_for_depth(concept, depth),
                connections=[depths[i-1]] if i > 0 else [],
                estimated_time=20,
                checkpoint=f"{depth} 수준에서 {concept.name}을 설명할 수 있는가?"
            )
            steps.append(step)

        return steps

    async def _generate_breadth_first(
        self,
        start: str,
        level: int,
        max_steps: int
    ) -> List[PathStep]:
        """너비 우선: 넓은 연결 탐색"""
        steps = []
        visited = set()
        queue = [start]

        while queue and len(steps) < max_steps:
            current = queue.pop(0)
            if current in visited:
                continue

            concept = self._get_concept(current)
            if not concept:
                continue

            visited.add(current)

            step = PathStep(
                concept=concept,
                focus="핵심 개념과 연결점",
                questions=[concept.key_questions[0]] if concept.key_questions else [],
                connections=[s.concept.name for s in steps if s.concept.id in concept.related],
                estimated_time=10,
                checkpoint=f"{concept.name}이 다른 개념들과 어떻게 연결되는지 설명할 수 있는가?"
            )
            steps.append(step)

            # 관련 개념들을 큐에 추가
            for related in concept.related:
                if related not in visited:
                    queue.append(related)

        return steps

    async def _generate_bridge_path(
        self,
        start: str,
        end: Optional[str],
        level: int,
        max_steps: int
    ) -> List[PathStep]:
        """다리 경로: 두 개념/분야 연결"""
        steps = []

        start_concept = self._get_concept(start)
        if not start_concept:
            return steps

        # 시작점
        steps.append(PathStep(
            concept=start_concept,
            focus="출발점 이해",
            questions=start_concept.key_questions[:1],
            connections=[],
            estimated_time=15,
            checkpoint=f"{start_concept.name}의 핵심 원리를 이해했는가?"
        ))

        # 중간 다리 개념들
        bridge_concepts = start_concept.fusion_potential[:max_steps-2]
        for bridge in bridge_concepts:
            bridge_node = self._get_concept(bridge) or self._create_placeholder(bridge)
            steps.append(PathStep(
                concept=bridge_node,
                focus=f"{start}과의 연결점",
                questions=[f"{start}의 관점에서 {bridge}을 어떻게 이해할 수 있는가?"],
                connections=[steps[-1].concept.name],
                estimated_time=15,
                checkpoint=f"{start}과 {bridge}의 공통점을 설명할 수 있는가?"
            ))

        # 종착점 (있는 경우)
        if end:
            end_concept = self._get_concept(end) or self._create_placeholder(end)
            steps.append(PathStep(
                concept=end_concept,
                focus="도착점과 통합",
                questions=[f"처음 {start}에서 출발해 {end}까지 어떤 여정이었는가?"],
                connections=[s.concept.name for s in steps],
                estimated_time=20,
                checkpoint=f"{start}에서 {end}까지의 개념적 연결을 설명할 수 있는가?"
            ))

        return steps

    async def _generate_challenge_path(
        self,
        start: str,
        level: int,
        max_steps: int
    ) -> List[PathStep]:
        """도전 경로: 어려운 질문 중심"""
        steps = []
        concept = self._get_concept(start)

        if not concept:
            return steps

        # 난이도 높은 질문들 중심
        challenges = [
            ("존재론적 도전", f"{concept.name}은 실재하는가, 우리 모델인가?"),
            ("환원 도전", f"{concept.name}을 더 기본적인 것으로 환원할 수 있는가?"),
            ("연결 도전", f"가장 멀어 보이는 분야와 {concept.name}을 연결할 수 있는가?"),
            ("역설 도전", f"{concept.name}과 관련된 역설을 해결할 수 있는가?"),
            ("예측 도전", f"{concept.name}의 미래는 어떻게 될 것인가?"),
        ]

        for i, (focus, question) in enumerate(challenges[:max_steps]):
            step = PathStep(
                concept=concept,
                focus=focus,
                questions=[question],
                connections=[challenges[i-1][0]] if i > 0 else [],
                estimated_time=25,
                checkpoint=f"{focus}에 대한 자신만의 답변을 제시할 수 있는가?"
            )
            steps.append(step)

        return steps

    def _get_concept(self, concept_id: str) -> Optional[ConceptNode]:
        """개념 조회"""
        return self.concept_graph.get(concept_id)

    def _create_placeholder(self, concept_id: str) -> ConceptNode:
        """임시 개념 노드 생성"""
        return ConceptNode(
            id=concept_id,
            name=concept_id,
            domain="general",
            difficulty=ConceptDifficulty.INTERMEDIATE,
            description=f"{concept_id} 개념",
            key_questions=[f"{concept_id}란 무엇인가?"]
        )

    def _select_by_level(self, candidates: List[str], level: int) -> str:
        """사용자 수준에 맞는 개념 선택"""
        scored = []
        for c in candidates:
            concept = self._get_concept(c)
            if concept:
                # 수준 차이가 작을수록 좋음
                diff = abs(concept.difficulty.value - level)
                scored.append((c, diff))
            else:
                scored.append((c, 2))  # 기본 중간 난이도

        scored.sort(key=lambda x: x[1])
        return scored[0][0] if scored else candidates[0]

    def _questions_for_depth(self, concept: ConceptNode, depth: str) -> List[str]:
        """깊이별 질문 생성"""
        depth_questions = {
            "정의와 기원": [
                f"{concept.name}의 역사적 기원은?",
                f"왜 이 개념이 필요했는가?"
            ],
            "핵심 원리": [
                f"{concept.name}의 수학적/논리적 구조는?",
                f"핵심 법칙이나 원리는 무엇인가?"
            ],
            "수학적 형식": [
                f"{concept.name}을 어떻게 수식으로 표현하는가?",
                f"어떤 수학적 도구가 사용되는가?"
            ],
            "분야별 적용": [
                f"다른 분야에서 {concept.name}은 어떻게 나타나는가?",
                f"실제 응용 사례는?"
            ],
            "한계와 논쟁": [
                f"{concept.name}의 한계는 무엇인가?",
                f"현재 진행 중인 논쟁은?"
            ]
        }
        return depth_questions.get(depth, concept.key_questions)

    def _generate_objectives(
        self,
        steps: List[PathStep],
        path_type: PathType
    ) -> List[str]:
        """학습 목표 생성"""
        concepts = [s.concept.name for s in steps]

        base_objectives = [
            f"핵심 개념 이해: {', '.join(concepts[:3])}",
            f"개념 간 연결 파악",
        ]

        if path_type == PathType.DEPTH_FIRST:
            base_objectives.append(f"{concepts[0]}에 대한 심층적 이해 달성")
        elif path_type == PathType.BREADTH_FIRST:
            base_objectives.append(f"{len(concepts)}개 개념의 연결망 구축")
        elif path_type == PathType.BRIDGE:
            base_objectives.append(f"분야 간 융합적 사고 개발")
        elif path_type == PathType.CHALLENGE:
            base_objectives.append(f"비판적 사고와 논증 능력 향상")
        else:
            base_objectives.append(f"나선형 심화 학습 완료")

        return base_objectives

    def _generate_path_description(
        self,
        steps: List[PathStep],
        path_type: PathType
    ) -> str:
        """경로 설명 생성"""
        type_descriptions = {
            PathType.DEPTH_FIRST: "하나의 개념을 깊이 파고드는 여정",
            PathType.BREADTH_FIRST: "넓게 연결된 개념들을 탐험하는 여정",
            PathType.SPIRAL: "점진적으로 심화되는 나선형 학습 여정",
            PathType.BRIDGE: "서로 다른 분야를 연결하는 다리 놓기 여정",
            PathType.CHALLENGE: "어려운 질문에 도전하는 지적 모험"
        }

        return f"{type_descriptions.get(path_type, '학습 여정')}. " \
               f"{len(steps)}단계로 구성, " \
               f"약 {sum(s.estimated_time for s in steps)}분 소요 예상."

    async def suggest_next_path(
        self,
        completed_concepts: List[str],
        user_interests: List[str],
        user_level: int
    ) -> LearningPath:
        """다음 학습 경로 추천"""
        # 아직 탐구하지 않은 개념 찾기
        all_concepts = set(self.concept_graph.keys())
        unexplored = all_concepts - set(completed_concepts)

        if not unexplored:
            # 모든 개념 탐구 완료 → 더 깊은 탐구
            start = random.choice(completed_concepts)
            return await self.generate_path(
                start, path_type=PathType.DEPTH_FIRST, user_level=user_level+1
            )

        # 관심 분야와 겹치는 개념 우선
        prioritized = []
        for concept_id in unexplored:
            concept = self._get_concept(concept_id)
            if concept and concept.domain in user_interests:
                prioritized.append(concept_id)

        start = prioritized[0] if prioritized else list(unexplored)[0]

        # 사용자 수준에 따른 경로 유형 선택
        if user_level <= 2:
            path_type = PathType.BREADTH_FIRST
        elif user_level <= 4:
            path_type = PathType.SPIRAL
        else:
            path_type = PathType.CHALLENGE

        return await self.generate_path(start, path_type=path_type, user_level=user_level)
