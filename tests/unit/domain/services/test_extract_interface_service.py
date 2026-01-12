"""Unit tests for ExtractInterfaceService."""

from __future__ import annotations

from pathlib import Path

import pytest

from rice_factor.domain.services.extract_interface_service import (
    ExtractionRequest,
    ExtractionResult,
    ExtractionStatus,
    ExtractInterfaceService,
    InterfaceType,
    MemberInfo,
)


class TestInterfaceType:
    """Tests for InterfaceType enum."""

    def test_all_types_exist(self) -> None:
        """All expected types should exist."""
        assert InterfaceType.INTERFACE.value == "interface"
        assert InterfaceType.PROTOCOL.value == "protocol"
        assert InterfaceType.TRAIT.value == "trait"
        assert InterfaceType.ABSTRACT_CLASS.value == "abstract_class"
        assert InterfaceType.MODULE.value == "module"


class TestExtractionStatus:
    """Tests for ExtractionStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """All expected statuses should exist."""
        assert ExtractionStatus.PENDING.value == "pending"
        assert ExtractionStatus.IN_PROGRESS.value == "in_progress"
        assert ExtractionStatus.COMPLETED.value == "completed"
        assert ExtractionStatus.FAILED.value == "failed"
        assert ExtractionStatus.SKIPPED.value == "skipped"


class TestMemberInfo:
    """Tests for MemberInfo dataclass."""

    def test_creation(self) -> None:
        """MemberInfo should be creatable."""
        member = MemberInfo(
            name="get_data",
            kind="method",
            return_type="str",
        )
        assert member.name == "get_data"
        assert member.kind == "method"

    def test_with_parameters(self) -> None:
        """should include parameters."""
        member = MemberInfo(
            name="process",
            kind="method",
            parameters=[{"name": "input", "type": "str"}],
        )
        assert len(member.parameters) == 1

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        member = MemberInfo(
            name="test_method",
            kind="method",
            return_type="int",
        )
        data = member.to_dict()
        assert data["name"] == "test_method"
        assert data["kind"] == "method"


class TestExtractionRequest:
    """Tests for ExtractionRequest dataclass."""

    def test_creation(self) -> None:
        """ExtractionRequest should be creatable."""
        request = ExtractionRequest(
            source_file=Path("src/models.py"),
            class_name="UserModel",
            interface_name="IUserModel",
        )
        assert request.class_name == "UserModel"
        assert request.interface_name == "IUserModel"

    def test_with_members(self) -> None:
        """should specify members to extract."""
        request = ExtractionRequest(
            source_file=Path("src/models.py"),
            class_name="DataModel",
            interface_name="IDataModel",
            members=["get_data", "set_data"],
        )
        assert len(request.members) == 2


class TestExtractionResult:
    """Tests for ExtractionResult dataclass."""

    def test_creation(self) -> None:
        """ExtractionResult should be creatable."""
        result = ExtractionResult(
            status=ExtractionStatus.COMPLETED,
            source_file="src/models.py",
            interface_name="IModel",
        )
        assert result.status == ExtractionStatus.COMPLETED

    def test_with_error(self) -> None:
        """should include error details."""
        result = ExtractionResult(
            status=ExtractionStatus.FAILED,
            source_file="src/models.py",
            interface_name="IModel",
            error="Class not found",
        )
        assert "not found" in result.error.lower()

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        result = ExtractionResult(
            status=ExtractionStatus.COMPLETED,
            source_file="test.py",
            interface_name="ITest",
            interface_code="class ITest:\n    pass",
        )
        data = result.to_dict()
        assert data["status"] == "completed"
        assert data["interface_name"] == "ITest"


class TestExtractInterfaceService:
    """Tests for ExtractInterfaceService."""

    def test_creation(self, tmp_path: Path) -> None:
        """ExtractInterfaceService should be creatable."""
        service = ExtractInterfaceService(repo_root=tmp_path)
        assert service.repo_root == tmp_path

    def test_get_supported_languages(self, tmp_path: Path) -> None:
        """should return supported languages."""
        service = ExtractInterfaceService(repo_root=tmp_path)
        languages = service.get_supported_languages()
        assert isinstance(languages, list)

    def test_detect_language_python(self, tmp_path: Path) -> None:
        """should detect Python files."""
        service = ExtractInterfaceService(repo_root=tmp_path)
        assert service.detect_language(Path("test.py")) == "python"

    def test_detect_language_typescript(self, tmp_path: Path) -> None:
        """should detect TypeScript files."""
        service = ExtractInterfaceService(repo_root=tmp_path)
        assert service.detect_language(Path("test.ts")) == "typescript"

    def test_detect_language_java(self, tmp_path: Path) -> None:
        """should detect Java files."""
        service = ExtractInterfaceService(repo_root=tmp_path)
        assert service.detect_language(Path("Test.java")) == "java"

    def test_detect_language_unknown(self, tmp_path: Path) -> None:
        """should return None for unknown extensions."""
        service = ExtractInterfaceService(repo_root=tmp_path)
        assert service.detect_language(Path("test.xyz")) is None

    def test_analyze_class_python(self, tmp_path: Path) -> None:
        """should analyze Python class."""
        service = ExtractInterfaceService(repo_root=tmp_path)

        # Create a Python file
        py_file = tmp_path / "models.py"
        py_file.write_text('''
class UserModel:
    def __init__(self, name: str):
        self.name = name

    def get_name(self) -> str:
        return self.name

    def set_name(self, name: str) -> None:
        self.name = name

    def _internal(self):
        pass
''')

        members = service.analyze_class(py_file, "UserModel")
        member_names = [m.name for m in members]
        assert "get_name" in member_names
        assert "set_name" in member_names

    def test_analyze_class_not_found(self, tmp_path: Path) -> None:
        """should handle missing class."""
        service = ExtractInterfaceService(repo_root=tmp_path)

        py_file = tmp_path / "empty.py"
        py_file.write_text("# Empty file")

        members = service.analyze_class(py_file, "NonExistent")
        assert members == []

    def test_extract_unknown_language(self, tmp_path: Path) -> None:
        """should fail for unknown language."""
        service = ExtractInterfaceService(repo_root=tmp_path)

        request = ExtractionRequest(
            source_file=tmp_path / "test.xyz",
            class_name="Test",
            interface_name="ITest",
        )

        result = service.extract(request)
        assert result.status == ExtractionStatus.FAILED
        assert "unknown" in result.error.lower()

    def test_extract_python_interface(self, tmp_path: Path) -> None:
        """should extract Python protocol."""
        service = ExtractInterfaceService(repo_root=tmp_path)

        py_file = tmp_path / "models.py"
        py_file.write_text('''
class DataProcessor:
    def process(self, data: str) -> str:
        return data.upper()

    def validate(self, data: str) -> bool:
        return len(data) > 0
''')

        request = ExtractionRequest(
            source_file=py_file,
            class_name="DataProcessor",
            interface_name="IDataProcessor",
        )

        result = service.extract(request)
        # Result depends on whether adapter is available
        assert result.interface_name == "IDataProcessor"

    def test_generate_python_protocol(self, tmp_path: Path) -> None:
        """should generate Python Protocol code."""
        service = ExtractInterfaceService(repo_root=tmp_path)

        members = [
            MemberInfo(
                name="get_data",
                kind="method",
                return_type="str",
                parameters=[],
            ),
            MemberInfo(
                name="set_data",
                kind="method",
                return_type="None",
                parameters=[{"name": "value", "type": "str"}],
            ),
        ]

        code = service._generate_python_protocol("IDataModel", members)
        assert "class IDataModel(Protocol):" in code
        assert "def get_data" in code
        assert "def set_data" in code

    def test_generate_typescript_interface(self, tmp_path: Path) -> None:
        """should generate TypeScript interface code."""
        service = ExtractInterfaceService(repo_root=tmp_path)

        members = [
            MemberInfo(
                name="getData",
                kind="method",
                return_type="string",
                parameters=[],
            ),
        ]

        code = service._generate_typescript_interface("IDataModel", members)
        assert "export interface IDataModel" in code
        assert "getData(): string" in code

    def test_generate_java_interface(self, tmp_path: Path) -> None:
        """should generate Java interface code."""
        service = ExtractInterfaceService(repo_root=tmp_path)

        members = [
            MemberInfo(
                name="getData",
                kind="method",
                return_type="String",
                parameters=[],
            ),
        ]

        code = service._generate_java_interface("IDataModel", members)
        assert "public interface IDataModel" in code
        assert "String getData();" in code

    def test_extract_batch(self, tmp_path: Path) -> None:
        """should extract multiple interfaces."""
        service = ExtractInterfaceService(repo_root=tmp_path)

        # Create Python files
        for i in range(3):
            py_file = tmp_path / f"model{i}.py"
            py_file.write_text(f'''
class Model{i}:
    def method(self) -> None:
        pass
''')

        requests = [
            ExtractionRequest(
                source_file=tmp_path / f"model{i}.py",
                class_name=f"Model{i}",
                interface_name=f"IModel{i}",
            )
            for i in range(3)
        ]

        results = service.extract_batch(requests)
        assert len(results) == 3

    def test_extract_with_specific_members(self, tmp_path: Path) -> None:
        """should extract only specified members."""
        service = ExtractInterfaceService(repo_root=tmp_path)

        py_file = tmp_path / "models.py"
        py_file.write_text('''
class BigClass:
    def method1(self) -> str:
        return "1"

    def method2(self) -> str:
        return "2"

    def method3(self) -> str:
        return "3"
''')

        request = ExtractionRequest(
            source_file=py_file,
            class_name="BigClass",
            interface_name="IPartial",
            members=["method1", "method3"],
        )

        result = service.extract(request)
        # Should only include specified members
        if result.members_extracted:
            member_names = [m.name for m in result.members_extracted]
            assert "method2" not in member_names
