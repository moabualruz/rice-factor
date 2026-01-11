"""Unit tests for capability detector."""

from unittest.mock import MagicMock, patch

from rice_factor.adapters.refactoring.capability_detector import (
    CapabilityDetector,
    LanguageCapability,
    ToolAvailability,
    detect_all,
    get_detector,
    is_available,
)


class TestToolAvailability:
    """Tests for ToolAvailability dataclass."""

    def test_create_available_tool(self) -> None:
        """Test creating an available tool."""
        tool = ToolAvailability(
            name="rope",
            available=True,
            version="1.11.0",
            languages=["python"],
            operations=["rename", "move"],
        )

        assert tool.name == "rope"
        assert tool.available is True
        assert tool.version == "1.11.0"
        assert "python" in tool.languages
        assert "rename" in tool.operations

    def test_create_unavailable_tool(self) -> None:
        """Test creating an unavailable tool."""
        tool = ToolAvailability(
            name="missing_tool",
            available=False,
        )

        assert tool.name == "missing_tool"
        assert tool.available is False
        assert tool.version is None
        assert tool.languages == []
        assert tool.operations == []


class TestLanguageCapability:
    """Tests for LanguageCapability dataclass."""

    def test_create_capability(self) -> None:
        """Test creating a language capability."""
        cap = LanguageCapability(
            language="python",
            adapter="rope",
            available=True,
            operations={"rename": True, "move": True, "extract_interface": True},
        )

        assert cap.language == "python"
        assert cap.adapter == "rope"
        assert cap.available is True
        assert cap.operations["rename"] is True


class TestCapabilityDetector:
    """Tests for CapabilityDetector class."""

    def test_detect_all_returns_dict(self) -> None:
        """Test that detect_all returns a dictionary."""
        detector = CapabilityDetector()
        result = detector.detect_all()

        assert isinstance(result, dict)
        # Should have all expected tools
        expected_tools = [
            "rope",
            "openrewrite",
            "roslyn",
            "ruby_parser",
            "rector",
            "jscodeshift",
            "gopls",
            "rust_analyzer",
        ]
        for tool in expected_tools:
            assert tool in result
            assert isinstance(result[tool], ToolAvailability)

    def test_detect_all_caches_results(self) -> None:
        """Test that detect_all caches results."""
        detector = CapabilityDetector()

        # First call
        result1 = detector.detect_all()
        # Second call should return cached
        result2 = detector.detect_all()

        assert result1 is result2

    def test_refresh_clears_cache(self) -> None:
        """Test that refresh clears the cache."""
        detector = CapabilityDetector()

        # First call
        result1 = detector.detect_all()
        # Refresh and call again
        result2 = detector.refresh()

        # Should be different objects (cache cleared)
        assert result1 is not result2

    def test_get_tool_existing(self) -> None:
        """Test getting an existing tool."""
        detector = CapabilityDetector()
        tool = detector.get_tool("rope")

        assert tool is not None
        assert tool.name == "rope"

    def test_get_tool_nonexistent(self) -> None:
        """Test getting a non-existent tool."""
        detector = CapabilityDetector()
        tool = detector.get_tool("nonexistent_tool")

        assert tool is None

    def test_is_available(self) -> None:
        """Test is_available method."""
        detector = CapabilityDetector()

        # This depends on actual tool installation
        # Just verify it returns a boolean
        result = detector.is_available("rope")
        assert isinstance(result, bool)

    def test_is_available_unknown_tool(self) -> None:
        """Test is_available for unknown tool."""
        detector = CapabilityDetector()
        assert detector.is_available("unknown_tool") is False

    def test_get_language_capabilities(self) -> None:
        """Test getting language capabilities."""
        detector = CapabilityDetector()
        capabilities = detector.get_language_capabilities()

        assert isinstance(capabilities, list)
        assert len(capabilities) > 0

        # Check that expected languages are present
        languages = {cap.language for cap in capabilities}
        expected = {"python", "java", "javascript", "go", "rust"}
        assert expected.issubset(languages)

    def test_format_capabilities_table(self) -> None:
        """Test formatting capabilities as table."""
        detector = CapabilityDetector()
        table = detector.format_capabilities_table()

        assert isinstance(table, str)
        assert "Language" in table
        assert "Adapter" in table
        # Should have separator line
        assert "---" in table


class TestCapabilityDetectorDetection:
    """Tests for individual tool detection methods."""

    def test_detect_rope(self) -> None:
        """Test Rope detection."""
        detector = CapabilityDetector()
        result = detector._detect_rope()

        assert result.name == "rope"
        assert "python" in result.languages

    @patch("shutil.which")
    def test_detect_gopls_available(self, mock_which: MagicMock) -> None:
        """Test gopls detection when available."""
        mock_which.return_value = "/usr/bin/gopls"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="gopls version 0.12.0\n",
            )

            detector = CapabilityDetector()
            result = detector._detect_gopls()

            assert result.name == "gopls"
            assert result.available is True
            assert "go" in result.languages

    @patch("shutil.which")
    def test_detect_gopls_not_available(self, mock_which: MagicMock) -> None:
        """Test gopls detection when not available."""
        mock_which.return_value = None

        detector = CapabilityDetector()
        result = detector._detect_gopls()

        assert result.available is False

    @patch("shutil.which")
    def test_detect_rust_analyzer_available(self, mock_which: MagicMock) -> None:
        """Test rust-analyzer detection when available."""
        mock_which.return_value = "/usr/bin/rust-analyzer"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="rust-analyzer 2024-01-01\n",
            )

            detector = CapabilityDetector()
            result = detector._detect_rust_analyzer()

            assert result.name == "rust_analyzer"
            assert result.available is True
            assert "rust" in result.languages

    @patch("shutil.which")
    def test_detect_roslyn_via_dotnet(self, mock_which: MagicMock) -> None:
        """Test Roslyn detection via dotnet."""
        mock_which.return_value = "/usr/bin/dotnet"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="8.0.100\n",
            )

            detector = CapabilityDetector()
            result = detector._detect_roslyn()

            assert result.name == "roslyn"
            assert "csharp" in result.languages


class TestCapabilityDetectorPackageChecks:
    """Tests for package checking methods."""

    def test_check_python_package_installed(self) -> None:
        """Test checking an installed Python package."""
        detector = CapabilityDetector()
        # pytest should be installed
        version = detector._check_python_package("pytest")
        assert version is not None

    def test_check_python_package_not_installed(self) -> None:
        """Test checking a non-installed Python package."""
        detector = CapabilityDetector()
        version = detector._check_python_package("nonexistent_package_xyz")
        assert version is None

    @patch("shutil.which")
    def test_check_command_exists(self, mock_which: MagicMock) -> None:
        """Test checking an existing command."""
        mock_which.return_value = "/usr/bin/python"
        detector = CapabilityDetector()
        assert detector._check_command("python") is True

    @patch("shutil.which")
    def test_check_command_not_exists(self, mock_which: MagicMock) -> None:
        """Test checking a non-existing command."""
        mock_which.return_value = None
        detector = CapabilityDetector()
        assert detector._check_command("nonexistent_cmd") is False

    @patch("subprocess.run")
    def test_check_command_version(self, mock_run: MagicMock) -> None:
        """Test getting command version."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="1.2.3\n",
        )

        with patch("shutil.which", return_value="/usr/bin/cmd"):
            detector = CapabilityDetector()
            version = detector._check_command_version("cmd", ["--version"])
            assert version == "1.2.3"

    @patch("subprocess.run")
    def test_check_command_version_timeout(self, mock_run: MagicMock) -> None:
        """Test command version with timeout."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="cmd", timeout=10)

        with patch("shutil.which", return_value="/usr/bin/cmd"):
            detector = CapabilityDetector()
            version = detector._check_command_version("cmd", ["--version"])
            assert version is None


class TestModuleLevelFunctions:
    """Tests for module-level convenience functions."""

    def test_get_detector_singleton(self) -> None:
        """Test that get_detector returns singleton."""
        detector1 = get_detector()
        detector2 = get_detector()
        assert detector1 is detector2

    def test_detect_all_function(self) -> None:
        """Test detect_all convenience function."""
        result = detect_all()
        assert isinstance(result, dict)
        assert "rope" in result

    def test_is_available_function(self) -> None:
        """Test is_available convenience function."""
        result = is_available("rope")
        assert isinstance(result, bool)
