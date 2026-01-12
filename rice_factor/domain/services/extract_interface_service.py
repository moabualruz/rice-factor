"""Extract interface service for creating interfaces from concrete classes.

This module provides the ExtractInterfaceService that enables extracting
interfaces from concrete classes across multiple languages using the
capability registry adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class InterfaceType(Enum):
    """Type of interface to extract."""

    INTERFACE = "interface"  # Java, C#, TypeScript
    PROTOCOL = "protocol"  # Python, Swift
    TRAIT = "trait"  # Rust, Scala
    ABSTRACT_CLASS = "abstract_class"  # PHP
    MODULE = "module"  # Ruby


class ExtractionStatus(Enum):
    """Status of an extraction operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class MemberInfo:
    """Information about a class member to include in interface.

    Attributes:
        name: Member name.
        kind: Member kind (method, property, field).
        return_type: Return type for methods.
        parameters: Parameter types for methods.
        is_static: Whether member is static.
        visibility: Access modifier.
    """

    name: str
    kind: str  # "method", "property", "field"
    return_type: str | None = None
    parameters: list[dict[str, str]] = field(default_factory=list)
    is_static: bool = False
    visibility: str = "public"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "kind": self.kind,
            "return_type": self.return_type,
            "parameters": self.parameters,
            "is_static": self.is_static,
            "visibility": self.visibility,
        }


@dataclass
class ExtractionRequest:
    """Request to extract an interface.

    Attributes:
        source_file: Path to source file.
        class_name: Name of class to extract from.
        interface_name: Name for the new interface.
        members: Optional list of specific members to include.
        interface_type: Type of interface to create.
        output_file: Optional output path (defaults to same directory).
    """

    source_file: Path
    class_name: str
    interface_name: str
    members: list[str] | None = None
    interface_type: InterfaceType = InterfaceType.INTERFACE
    output_file: Path | None = None


@dataclass
class ExtractionResult:
    """Result of an extraction operation.

    Attributes:
        status: Extraction status.
        source_file: Source file path.
        interface_name: Created interface name.
        output_file: Output file path.
        members_extracted: List of extracted members.
        interface_code: Generated interface code.
        error: Error message if failed.
        extracted_at: When extraction completed.
    """

    status: ExtractionStatus
    source_file: str
    interface_name: str
    output_file: str | None = None
    members_extracted: list[MemberInfo] = field(default_factory=list)
    interface_code: str | None = None
    error: str | None = None
    extracted_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "source_file": self.source_file,
            "interface_name": self.interface_name,
            "output_file": self.output_file,
            "members_extracted": [m.to_dict() for m in self.members_extracted],
            "interface_code": self.interface_code,
            "error": self.error,
            "extracted_at": (
                self.extracted_at.isoformat() if self.extracted_at else None
            ),
        }


@dataclass
class ExtractInterfaceService:
    """Service for extracting interfaces from concrete classes.

    Uses the capability registry adapters to perform language-specific
    interface extraction.

    Attributes:
        repo_root: Root directory of the repository.
        capability_detector: Optional capability detector instance.
    """

    repo_root: Path
    capability_detector: Any = None
    _adapters: dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize adapters."""
        self._load_adapters()

    def _load_adapters(self) -> None:
        """Load language-specific adapters."""
        # Import adapters lazily
        try:
            from rice_factor.adapters.refactoring.rope_adapter import RopeAdapter

            self._adapters["python"] = RopeAdapter(project_root=self.repo_root)
        except ImportError:
            pass

        try:
            from rice_factor.adapters.refactoring.jscodeshift_adapter import (
                JscodeshiftAdapter,
            )

            self._adapters["javascript"] = JscodeshiftAdapter(project_root=self.repo_root)
            self._adapters["typescript"] = JscodeshiftAdapter(project_root=self.repo_root)
        except ImportError:
            pass

        try:
            from rice_factor.adapters.refactoring.openrewrite_adapter import (
                OpenRewriteAdapter,
            )

            self._adapters["java"] = OpenRewriteAdapter(project_root=self.repo_root)
            self._adapters["kotlin"] = OpenRewriteAdapter(project_root=self.repo_root)
        except ImportError:
            pass

        try:
            from rice_factor.adapters.refactoring.roslyn_adapter import RoslynAdapter

            self._adapters["csharp"] = RoslynAdapter(project_root=self.repo_root)
        except ImportError:
            pass

        try:
            from rice_factor.adapters.refactoring.ruby_parser_adapter import (
                RubyParserAdapter,
            )

            self._adapters["ruby"] = RubyParserAdapter(project_root=self.repo_root)
        except ImportError:
            pass

        try:
            from rice_factor.adapters.refactoring.rector_adapter import RectorAdapter

            self._adapters["php"] = RectorAdapter(project_root=self.repo_root)
        except ImportError:
            pass

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages.

        Returns:
            List of language names.
        """
        return list(self._adapters.keys())

    def detect_language(self, file_path: Path) -> str | None:
        """Detect language from file extension.

        Args:
            file_path: Path to file.

        Returns:
            Language name or None if unknown.
        """
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".kt": "kotlin",
            ".cs": "csharp",
            ".rb": "ruby",
            ".php": "php",
        }
        return ext_map.get(file_path.suffix.lower())

    def analyze_class(
        self,
        source_file: Path,
        class_name: str,
    ) -> list[MemberInfo]:
        """Analyze a class to find extractable members.

        Args:
            source_file: Path to source file.
            class_name: Name of class to analyze.

        Returns:
            List of extractable members.
        """
        language = self.detect_language(source_file)
        if not language or language not in self._adapters:
            return []

        # Use AST-based analysis for Python
        if language == "python" and source_file.exists():
            return self._analyze_python_class(source_file, class_name)

        # Default stub implementation for other languages
        return []

    def _analyze_python_class(
        self,
        source_file: Path,
        class_name: str,
    ) -> list[MemberInfo]:
        """Analyze a Python class for extractable members.

        Args:
            source_file: Path to Python file.
            class_name: Name of class.

        Returns:
            List of member info.
        """
        import ast

        members: list[MemberInfo] = []

        try:
            tree = ast.parse(source_file.read_text(encoding="utf-8"))

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            if not item.name.startswith("_") or item.name == "__init__":
                                params = [
                                    {"name": arg.arg, "type": "Any"}
                                    for arg in item.args.args
                                    if arg.arg != "self"
                                ]
                                members.append(
                                    MemberInfo(
                                        name=item.name,
                                        kind="method",
                                        return_type=self._get_annotation(
                                            item.returns
                                        ),
                                        parameters=params,
                                        is_static=False,
                                        visibility=(
                                            "private"
                                            if item.name.startswith("_")
                                            else "public"
                                        ),
                                    )
                                )

                    break

        except Exception:
            pass

        return members

    def _get_annotation(self, node: ast.expr | None) -> str | None:
        """Get type annotation as string."""
        import ast

        if node is None:
            return None
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Subscript):
            return ast.unparse(node)
        if isinstance(node, ast.Constant):
            return str(node.value)
        return "Any"

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        """Extract an interface from a class.

        Args:
            request: Extraction request.

        Returns:
            ExtractionResult with details.
        """
        language = self.detect_language(request.source_file)

        if not language:
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                source_file=str(request.source_file),
                interface_name=request.interface_name,
                error=f"Unknown language for file: {request.source_file}",
            )

        if language not in self._adapters:
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                source_file=str(request.source_file),
                interface_name=request.interface_name,
                error=f"No adapter available for language: {language}",
            )

        adapter = self._adapters[language]

        # Check if adapter supports extract_interface
        if not hasattr(adapter, "extract_interface"):
            return self._generate_interface(request, language)

        try:
            result = adapter.extract_interface(
                source_file=str(request.source_file),
                class_name=request.class_name,
                interface_name=request.interface_name,
                methods=request.members,
            )

            return ExtractionResult(
                status=ExtractionStatus.COMPLETED,
                source_file=str(request.source_file),
                interface_name=request.interface_name,
                output_file=result.get("output_file"),
                interface_code=result.get("code"),
                extracted_at=datetime.now(UTC),
            )

        except Exception as e:
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                source_file=str(request.source_file),
                interface_name=request.interface_name,
                error=str(e),
            )

    def _generate_interface(
        self,
        request: ExtractionRequest,
        language: str,
    ) -> ExtractionResult:
        """Generate interface code directly.

        Args:
            request: Extraction request.
            language: Target language.

        Returns:
            ExtractionResult with generated code.
        """
        members = self.analyze_class(request.source_file, request.class_name)

        if request.members:
            members = [m for m in members if m.name in request.members]

        if not members:
            return ExtractionResult(
                status=ExtractionStatus.SKIPPED,
                source_file=str(request.source_file),
                interface_name=request.interface_name,
                error="No extractable members found",
            )

        # Generate code based on interface type
        if language == "python":
            code = self._generate_python_protocol(request.interface_name, members)
        elif language == "typescript":
            code = self._generate_typescript_interface(request.interface_name, members)
        elif language == "java":
            code = self._generate_java_interface(request.interface_name, members)
        else:
            code = f"// Interface {request.interface_name} (stub)"

        output_file = request.output_file
        if output_file is None:
            output_file = request.source_file.parent / f"i_{request.interface_name.lower()}.{request.source_file.suffix}"

        return ExtractionResult(
            status=ExtractionStatus.COMPLETED,
            source_file=str(request.source_file),
            interface_name=request.interface_name,
            output_file=str(output_file),
            members_extracted=members,
            interface_code=code,
            extracted_at=datetime.now(UTC),
        )

    def _generate_python_protocol(
        self,
        name: str,
        members: list[MemberInfo],
    ) -> str:
        """Generate Python Protocol code."""
        lines = [
            "from typing import Protocol",
            "",
            "",
            f"class {name}(Protocol):",
        ]

        for member in members:
            if member.kind == "method":
                params = ", ".join(
                    f"{p['name']}: {p.get('type', 'Any')}"
                    for p in member.parameters
                )
                ret = member.return_type or "None"
                lines.append(f"    def {member.name}(self, {params}) -> {ret}:")
                lines.append("        ...")

        if not members:
            lines.append("    pass")

        return "\n".join(lines)

    def _generate_typescript_interface(
        self,
        name: str,
        members: list[MemberInfo],
    ) -> str:
        """Generate TypeScript interface code."""
        lines = [f"export interface {name} {{"]

        for member in members:
            if member.kind == "method":
                params = ", ".join(
                    f"{p['name']}: {p.get('type', 'any')}"
                    for p in member.parameters
                )
                ret = member.return_type or "void"
                lines.append(f"  {member.name}({params}): {ret};")

        lines.append("}")
        return "\n".join(lines)

    def _generate_java_interface(
        self,
        name: str,
        members: list[MemberInfo],
    ) -> str:
        """Generate Java interface code."""
        lines = [f"public interface {name} {{"]

        for member in members:
            if member.kind == "method":
                params = ", ".join(
                    f"{p.get('type', 'Object')} {p['name']}"
                    for p in member.parameters
                )
                ret = member.return_type or "void"
                lines.append(f"    {ret} {member.name}({params});")

        lines.append("}")
        return "\n".join(lines)

    def extract_batch(
        self,
        requests: list[ExtractionRequest],
    ) -> list[ExtractionResult]:
        """Extract multiple interfaces.

        Args:
            requests: List of extraction requests.

        Returns:
            List of extraction results.
        """
        return [self.extract(req) for req in requests]
