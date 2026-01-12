"""Cross-language dependency tracking service.

This module provides the CrossLanguageTracker that detects and maps
dependencies between different programming languages in polyglot repositories.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from rice_factor.domain.services.language_detector import Language, LanguageDetector


class IntegrationPointType(Enum):
    """Type of cross-language integration point."""

    REST_API = "rest_api"  # HTTP REST endpoints
    GRAPHQL = "graphql"  # GraphQL endpoints
    GRPC = "grpc"  # gRPC services
    FFI = "ffi"  # Foreign function interface
    MESSAGE_QUEUE = "message_queue"  # Message queue consumers/producers
    DATABASE = "database"  # Shared database tables
    FILE_EXCHANGE = "file_exchange"  # File-based data exchange
    CLI = "cli"  # Command-line interface calls
    WEBSOCKET = "websocket"  # WebSocket connections
    SHARED_MEMORY = "shared_memory"  # Shared memory IPC


class DependencyDirection(Enum):
    """Direction of dependency."""

    PROVIDER = "provider"  # Provides the API/service
    CONSUMER = "consumer"  # Consumes the API/service
    BIDIRECTIONAL = "bidirectional"  # Both provider and consumer


@dataclass
class IntegrationPoint:
    """An integration point between languages.

    Attributes:
        type: Type of integration.
        name: Name/identifier of the integration point.
        file_path: File where integration is defined.
        line: Line number.
        endpoint: API endpoint or path if applicable.
        direction: Whether this is provider or consumer.
    """

    type: IntegrationPointType
    name: str
    file_path: str
    line: int = 0
    endpoint: str | None = None
    direction: DependencyDirection = DependencyDirection.PROVIDER

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "name": self.name,
            "file_path": self.file_path,
            "line": self.line,
            "endpoint": self.endpoint,
            "direction": self.direction.value,
        }


@dataclass
class LanguageDependency:
    """A dependency between two languages.

    Attributes:
        from_language: Source language.
        to_language: Target language.
        integration_points: List of integration points.
        description: Human-readable description.
    """

    from_language: Language
    to_language: Language
    integration_points: list[IntegrationPoint] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_language": self.from_language.value,
            "to_language": self.to_language.value,
            "integration_points": [p.to_dict() for p in self.integration_points],
            "description": self.description,
        }


@dataclass
class DependencyGraph:
    """Graph of cross-language dependencies.

    Attributes:
        dependencies: List of language dependencies.
        languages: Languages in the graph.
        total_integration_points: Total number of integration points.
        analyzed_at: When analysis was performed.
    """

    dependencies: list[LanguageDependency] = field(default_factory=list)
    languages: list[Language] = field(default_factory=list)
    total_integration_points: int = 0
    analyzed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dependencies": [d.to_dict() for d in self.dependencies],
            "languages": [l.value for l in self.languages],
            "total_integration_points": self.total_integration_points,
            "analyzed_at": (
                self.analyzed_at.isoformat() if self.analyzed_at else None
            ),
        }

    def get_providers(self, language: Language) -> list[LanguageDependency]:
        """Get dependencies where language is a provider."""
        return [d for d in self.dependencies if d.from_language == language]

    def get_consumers(self, language: Language) -> list[LanguageDependency]:
        """Get dependencies where language is a consumer."""
        return [d for d in self.dependencies if d.to_language == language]


# Patterns for detecting API endpoints by language
API_PATTERNS: dict[Language, list[tuple[str, IntegrationPointType]]] = {
    Language.PYTHON: [
        (r'@app\.route\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'@router\.(get|post|put|delete)\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'@api_view\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'grpc\.server', IntegrationPointType.GRPC),
        (r'pika\.BasicProperties|kombu\.Queue', IntegrationPointType.MESSAGE_QUEUE),
        (r'websocket|WebSocket', IntegrationPointType.WEBSOCKET),
    ],
    Language.JAVASCRIPT: [
        (r'app\.(get|post|put|delete)\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'router\.(get|post|put|delete)\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'fetch\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'axios\.(get|post|put|delete)\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'graphql|gql`', IntegrationPointType.GRAPHQL),
        (r'WebSocket\(["\']([^"\']+)["\']', IntegrationPointType.WEBSOCKET),
    ],
    Language.TYPESCRIPT: [
        (r'app\.(get|post|put|delete)\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'@Get\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'@Post\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'graphql|gql`', IntegrationPointType.GRAPHQL),
        (r'WebSocket\(["\']([^"\']+)["\']', IntegrationPointType.WEBSOCKET),
    ],
    Language.JAVA: [
        (r'@(Get|Post|Put|Delete)Mapping\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'@RequestMapping\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'@Path\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'@GrpcService|GrpcServer', IntegrationPointType.GRPC),
        (r'@RabbitListener|@KafkaListener', IntegrationPointType.MESSAGE_QUEUE),
    ],
    Language.GO: [
        (r'http\.HandleFunc\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'router\.(GET|POST|PUT|DELETE)\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'grpc\.NewServer', IntegrationPointType.GRPC),
    ],
    Language.RUST: [
        (r'#\[get\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'#\[post\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'tonic::transport::Server', IntegrationPointType.GRPC),
    ],
    Language.RUBY: [
        (r'get ["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'post ["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'resources? :[a-z_]+', IntegrationPointType.REST_API),
    ],
    Language.PHP: [
        (r'@Route\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'\$router->(get|post|put|delete)\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
    ],
}

# Patterns for detecting API consumers
CONSUMER_PATTERNS: dict[Language, list[tuple[str, IntegrationPointType]]] = {
    Language.PYTHON: [
        (r'requests\.(get|post|put|delete)\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'httpx\.(get|post|put|delete)', IntegrationPointType.REST_API),
        (r'grpc\.insecure_channel', IntegrationPointType.GRPC),
    ],
    Language.JAVASCRIPT: [
        (r'fetch\(["\']([^"\']+)["\']', IntegrationPointType.REST_API),
        (r'axios\.(get|post|put|delete)', IntegrationPointType.REST_API),
    ],
    Language.JAVA: [
        (r'RestTemplate|WebClient', IntegrationPointType.REST_API),
        (r'@FeignClient', IntegrationPointType.REST_API),
        (r'ManagedChannelBuilder', IntegrationPointType.GRPC),
    ],
    Language.GO: [
        (r'http\.Get\(|http\.Post\(', IntegrationPointType.REST_API),
        (r'grpc\.Dial', IntegrationPointType.GRPC),
    ],
}


@dataclass
class CrossLanguageTracker:
    """Service for tracking cross-language dependencies.

    Analyzes codebases to find integration points between different
    programming languages.

    Attributes:
        repo_root: Root directory of the repository.
        language_detector: LanguageDetector instance.
    """

    repo_root: Path
    language_detector: LanguageDetector | None = None

    def __post_init__(self) -> None:
        """Initialize language detector if not provided."""
        if self.language_detector is None:
            self.language_detector = LanguageDetector(repo_root=self.repo_root)

    def analyze(self) -> DependencyGraph:
        """Analyze the repository for cross-language dependencies.

        Returns:
            DependencyGraph with all detected dependencies.
        """
        # First detect languages
        detection_result = self.language_detector.detect()
        languages = [stats.language for stats in detection_result.languages]

        if len(languages) < 2:
            # Not a polyglot repo, no cross-language deps
            return DependencyGraph(
                languages=languages,
                analyzed_at=datetime.now(UTC),
            )

        # Find integration points for each language
        all_points: dict[Language, list[IntegrationPoint]] = {}

        for language in languages:
            points = self._find_integration_points(language)
            if points:
                all_points[language] = points

        # Build dependency graph
        dependencies = self._build_dependencies(all_points)

        total_points = sum(len(d.integration_points) for d in dependencies)

        return DependencyGraph(
            dependencies=dependencies,
            languages=languages,
            total_integration_points=total_points,
            analyzed_at=datetime.now(UTC),
        )

    def _find_integration_points(
        self,
        language: Language,
    ) -> list[IntegrationPoint]:
        """Find integration points for a language.

        Args:
            language: Language to analyze.

        Returns:
            List of IntegrationPoint objects.
        """
        points: list[IntegrationPoint] = []

        files = self.language_detector.get_files_for_language(language)

        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            # Check provider patterns
            if language in API_PATTERNS:
                for pattern, point_type in API_PATTERNS[language]:
                    for match in re.finditer(pattern, content):
                        # Find line number
                        line_num = content[:match.start()].count("\n") + 1

                        endpoint = None
                        groups = match.groups()
                        if groups:
                            # Last group is usually the endpoint
                            endpoint = groups[-1] if groups[-1] else None

                        points.append(
                            IntegrationPoint(
                                type=point_type,
                                name=f"{point_type.value}_{len(points)}",
                                file_path=str(file_path),
                                line=line_num,
                                endpoint=endpoint,
                                direction=DependencyDirection.PROVIDER,
                            )
                        )

            # Check consumer patterns
            if language in CONSUMER_PATTERNS:
                for pattern, point_type in CONSUMER_PATTERNS[language]:
                    for match in re.finditer(pattern, content):
                        line_num = content[:match.start()].count("\n") + 1

                        endpoint = None
                        groups = match.groups()
                        if groups:
                            endpoint = groups[-1] if groups[-1] else None

                        points.append(
                            IntegrationPoint(
                                type=point_type,
                                name=f"{point_type.value}_consumer_{len(points)}",
                                file_path=str(file_path),
                                line=line_num,
                                endpoint=endpoint,
                                direction=DependencyDirection.CONSUMER,
                            )
                        )

        return points

    def _build_dependencies(
        self,
        all_points: dict[Language, list[IntegrationPoint]],
    ) -> list[LanguageDependency]:
        """Build dependency graph from integration points.

        Args:
            all_points: Dict mapping language to integration points.

        Returns:
            List of LanguageDependency objects.
        """
        dependencies: list[LanguageDependency] = []

        languages = list(all_points.keys())

        # For each pair of languages
        for i, lang_a in enumerate(languages):
            for lang_b in languages[i + 1:]:
                points_a = all_points.get(lang_a, [])
                points_b = all_points.get(lang_b, [])

                # Find provider-consumer relationships
                providers_a = [
                    p for p in points_a if p.direction == DependencyDirection.PROVIDER
                ]
                consumers_a = [
                    p for p in points_a if p.direction == DependencyDirection.CONSUMER
                ]
                providers_b = [
                    p for p in points_b if p.direction == DependencyDirection.PROVIDER
                ]
                consumers_b = [
                    p for p in points_b if p.direction == DependencyDirection.CONSUMER
                ]

                # A provides, B consumes
                if providers_a and consumers_b:
                    dep = LanguageDependency(
                        from_language=lang_a,
                        to_language=lang_b,
                        integration_points=providers_a,
                        description=f"{lang_a.value} provides APIs consumed by {lang_b.value}",
                    )
                    dependencies.append(dep)

                # B provides, A consumes
                if providers_b and consumers_a:
                    dep = LanguageDependency(
                        from_language=lang_b,
                        to_language=lang_a,
                        integration_points=providers_b,
                        description=f"{lang_b.value} provides APIs consumed by {lang_a.value}",
                    )
                    dependencies.append(dep)

        return dependencies

    def get_api_endpoints(
        self,
        language: Language | None = None,
    ) -> list[IntegrationPoint]:
        """Get all API endpoints, optionally filtered by language.

        Args:
            language: Optional language filter.

        Returns:
            List of IntegrationPoint objects for REST/GraphQL/gRPC endpoints.
        """
        endpoints: list[IntegrationPoint] = []

        if language:
            languages = [language]
        else:
            detection = self.language_detector.detect()
            languages = [s.language for s in detection.languages]

        for lang in languages:
            points = self._find_integration_points(lang)
            endpoints.extend(
                p
                for p in points
                if p.type
                in (
                    IntegrationPointType.REST_API,
                    IntegrationPointType.GRAPHQL,
                    IntegrationPointType.GRPC,
                )
            )

        return endpoints

    def get_message_queues(self) -> list[IntegrationPoint]:
        """Get all message queue integration points.

        Returns:
            List of IntegrationPoint objects for message queues.
        """
        queues: list[IntegrationPoint] = []

        detection = self.language_detector.detect()
        for stats in detection.languages:
            points = self._find_integration_points(stats.language)
            queues.extend(
                p for p in points if p.type == IntegrationPointType.MESSAGE_QUEUE
            )

        return queues

    def detect_shared_resources(self) -> dict[str, list[IntegrationPoint]]:
        """Detect shared resources (databases, files) between languages.

        Returns:
            Dict mapping resource type to integration points.
        """
        resources: dict[str, list[IntegrationPoint]] = {
            "database": [],
            "file_exchange": [],
        }

        detection = self.language_detector.detect()

        for stats in detection.languages:
            files = self.language_detector.get_files_for_language(stats.language)

            for file_path in files:
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue

                # Database patterns
                db_patterns = [
                    r"(mysql|postgres|mongodb|sqlite|redis)",
                    r"(SQLAlchemy|TypeORM|Sequelize|GORM|Diesel)",
                    r"DATABASE_URL|DB_HOST|MONGODB_URI",
                ]

                for pattern in db_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        line_num = 0
                        for i, line in enumerate(content.split("\n"), 1):
                            if re.search(pattern, line, re.IGNORECASE):
                                line_num = i
                                break

                        resources["database"].append(
                            IntegrationPoint(
                                type=IntegrationPointType.DATABASE,
                                name="database_connection",
                                file_path=str(file_path),
                                line=line_num,
                                direction=DependencyDirection.BIDIRECTIONAL,
                            )
                        )
                        break

        return resources
