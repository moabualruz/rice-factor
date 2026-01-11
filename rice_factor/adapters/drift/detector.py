"""Drift detection adapter.

This module provides the DriftDetectorAdapter that implements drift detection
between code and artifacts in a project.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.drift.models import (
    DriftConfig,
    DriftReport,
    DriftSeverity,
    DriftSignal,
    DriftSignalType,
)

if TYPE_CHECKING:
    from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter


class DriftDetectorAdapter:
    """Adapter for detecting drift between code and artifacts.

    This adapter implements the DriftDetectorPort protocol, providing
    drift detection capabilities for the rice-factor system.
    """

    def __init__(
        self,
        storage: FilesystemStorageAdapter | None = None,
        config: DriftConfig | None = None,
    ) -> None:
        """Initialize the drift detector.

        Args:
            storage: Optional storage adapter for artifact access.
            config: Optional drift configuration. Uses defaults if not provided.
        """
        self._storage = storage
        self._config = config or DriftConfig()

    def detect_orphan_code(self, code_dir: Path, repo_root: Path) -> list[DriftSignal]:
        """Find code files not covered by any ImplementationPlan.

        Args:
            code_dir: Directory to scan for code files.
            repo_root: Root directory of the repository.

        Returns:
            List of drift signals for orphaned code.
        """
        signals: list[DriftSignal] = []

        if not code_dir.exists():
            return signals

        # Get all code files
        code_files = self._scan_code_files(code_dir)

        # Get all file paths covered by ImplementationPlans
        covered_paths = self._get_covered_paths(repo_root)

        # Find orphans
        for code_file in code_files:
            try:
                rel_path = str(code_file.relative_to(repo_root))
            except ValueError:
                rel_path = str(code_file)

            # Normalize path separators
            rel_path = rel_path.replace("\\", "/")

            if rel_path not in covered_paths:
                signals.append(
                    DriftSignal(
                        signal_type=DriftSignalType.ORPHAN_CODE,
                        severity=DriftSeverity.MEDIUM,
                        path=rel_path,
                        description=f"No ImplementationPlan covers {rel_path}",
                        detected_at=datetime.now(),
                        suggested_action="Create ImplementationPlan or document as legacy",
                    )
                )

        return signals

    def detect_orphan_plans(self, repo_root: Path) -> list[DriftSignal]:
        """Find ImplementationPlans targeting non-existent files.

        Args:
            repo_root: Root directory of the repository.

        Returns:
            List of drift signals for orphaned plans.
        """
        signals: list[DriftSignal] = []

        # Load ImplementationPlan artifacts
        impl_plans = self._load_artifacts_of_type(repo_root, "ImplementationPlan")

        for artifact_path, artifact_data in impl_plans:
            payload = artifact_data.get("payload", {})
            target_file = payload.get("target")

            if target_file:
                target_path = repo_root / target_file
                if not target_path.exists():
                    artifact_id = artifact_data.get("id", "unknown")
                    signals.append(
                        DriftSignal(
                            signal_type=DriftSignalType.ORPHAN_PLAN,
                            severity=DriftSeverity.HIGH,
                            path=target_file,
                            description=f"Plan {artifact_id} targets non-existent {target_file}",
                            detected_at=datetime.now(),
                            related_artifact_id=artifact_id,
                            suggested_action="Archive plan or restore target file",
                        )
                    )

        # Also check RefactorPlan targets
        refactor_plans = self._load_artifacts_of_type(repo_root, "RefactorPlan")

        for artifact_path, artifact_data in refactor_plans:
            payload = artifact_data.get("payload", {})
            from_path = payload.get("from_path")
            to_path = payload.get("to_path")

            # Check if 'from' file was supposed to be moved but doesn't exist at 'to'
            if from_path and to_path:
                from_exists = (repo_root / from_path).exists()
                to_exists = (repo_root / to_path).exists()

                if not from_exists and not to_exists:
                    artifact_id = artifact_data.get("id", "unknown")
                    signals.append(
                        DriftSignal(
                            signal_type=DriftSignalType.ORPHAN_PLAN,
                            severity=DriftSeverity.HIGH,
                            path=f"{from_path} -> {to_path}",
                            description=f"RefactorPlan {artifact_id} references missing files",
                            detected_at=datetime.now(),
                            related_artifact_id=artifact_id,
                            suggested_action="Archive refactor plan",
                        )
                    )

        return signals

    def detect_undocumented_behavior(self, repo_root: Path) -> list[DriftSignal]:
        """Find tests covering behavior not in requirements.

        This implementation:
        1. Parses test files to extract test function names and docstrings
        2. Loads requirements.md and extracts requirement keywords
        3. Identifies tests that don't match any documented requirement

        Args:
            repo_root: Root directory of the repository.

        Returns:
            List of drift signals for undocumented behavior.
        """
        signals: list[DriftSignal] = []

        # Load requirements
        requirements_text = self._load_requirements(repo_root)
        if not requirements_text:
            # No requirements.md, can't determine undocumented behavior
            return signals

        # Extract keywords from requirements
        requirement_keywords = self._extract_requirement_keywords(requirements_text)
        if not requirement_keywords:
            return signals

        # Find all test files
        test_files = self._scan_test_files(repo_root)

        # Analyze each test file
        for test_file in test_files:
            file_signals = self._analyze_test_file(
                test_file, repo_root, requirement_keywords
            )
            signals.extend(file_signals)

        return signals

    def _load_requirements(self, repo_root: Path) -> str:
        """Load requirements.md content.

        Args:
            repo_root: Root directory of the repository.

        Returns:
            Requirements file content, or empty string if not found.
        """
        requirements_path = repo_root / ".project" / "requirements.md"
        if not requirements_path.exists():
            return ""

        try:
            return requirements_path.read_text(encoding="utf-8")
        except OSError:
            return ""

    def _extract_requirement_keywords(self, requirements_text: str) -> set[str]:
        """Extract searchable keywords from requirements.

        Extracts:
        - Words from bullet points (- item)
        - Words from numbered lists (1. item)
        - Feature names (FR-xxx: description)
        - Section headers (## Section)

        Args:
            requirements_text: Content of requirements.md.

        Returns:
            Set of lowercase keywords (2+ characters).
        """
        import re

        keywords: set[str] = set()

        # Common stop words to exclude
        stop_words = {
            "the", "and", "for", "are", "but", "not", "you", "all",
            "can", "has", "was", "one", "our", "out", "use", "with",
            "this", "that", "have", "from", "they", "will", "would",
            "could", "should", "must", "may", "when", "what", "which",
            "each", "any", "more", "some", "such", "only", "other",
            "than", "then", "into", "also", "most", "very", "just",
        }

        # Extract words from markdown content
        # Remove code blocks first
        text = re.sub(r"```[\s\S]*?```", "", requirements_text)
        text = re.sub(r"`[^`]+`", "", text)

        # Extract feature IDs (e.g., FR-001, REQ-123)
        feature_ids = re.findall(r"\b([A-Z]{2,}-\d+)\b", text)
        keywords.update(f.lower() for f in feature_ids)

        # Extract bullet point items
        bullets = re.findall(r"^[\s]*[-*]\s+(.+)$", text, re.MULTILINE)
        for bullet in bullets:
            words = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", bullet)
            for word in words:
                lower = word.lower()
                if len(lower) >= 3 and lower not in stop_words:
                    keywords.add(lower)

        # Extract numbered list items
        numbered = re.findall(r"^\d+\.\s+(.+)$", text, re.MULTILINE)
        for item in numbered:
            words = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", item)
            for word in words:
                lower = word.lower()
                if len(lower) >= 3 and lower not in stop_words:
                    keywords.add(lower)

        # Extract section headers
        headers = re.findall(r"^#{1,6}\s+(.+)$", text, re.MULTILINE)
        for header in headers:
            words = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", header)
            for word in words:
                lower = word.lower()
                if len(lower) >= 3 and lower not in stop_words:
                    keywords.add(lower)

        return keywords

    def _scan_test_files(self, repo_root: Path) -> list[Path]:
        """Find all test files in the repository.

        Args:
            repo_root: Root directory of the repository.

        Returns:
            List of test file paths.
        """
        test_files: list[Path] = []

        # Check tests/ directory
        tests_dir = repo_root / "tests"
        if tests_dir.exists():
            for path in tests_dir.rglob("test_*.py"):
                if path.is_file():
                    test_files.append(path)
            for path in tests_dir.rglob("*_test.py"):
                if path.is_file():
                    test_files.append(path)

        # Check for test files in source directories
        for source_dir in self._config.source_dirs:
            src_path = repo_root / source_dir
            if src_path.exists():
                for path in src_path.rglob("test_*.py"):
                    if path.is_file():
                        test_files.append(path)
                for path in src_path.rglob("*_test.py"):
                    if path.is_file():
                        test_files.append(path)

        return list(set(test_files))

    def _analyze_test_file(
        self,
        test_file: Path,
        repo_root: Path,
        requirement_keywords: set[str],
    ) -> list[DriftSignal]:
        """Analyze a test file for undocumented behavior.

        Args:
            test_file: Path to the test file.
            repo_root: Repository root.
            requirement_keywords: Set of keywords from requirements.

        Returns:
            List of drift signals for undocumented tests.
        """
        import ast

        signals: list[DriftSignal] = []

        try:
            content = test_file.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except (OSError, SyntaxError):
            return signals

        try:
            rel_path = str(test_file.relative_to(repo_root))
        except ValueError:
            rel_path = str(test_file)
        rel_path = rel_path.replace("\\", "/")

        # Find all test functions and methods
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                # Extract test name and docstring
                test_name = node.name
                docstring = ast.get_docstring(node) or ""

                # Get all words in test name (e.g., test_user_login -> user, login)
                test_words = set(
                    w.lower()
                    for w in test_name.replace("test_", "").split("_")
                    if len(w) >= 3
                )

                # Also check for feature ID patterns in test name (e.g., fr_001 -> fr-001)
                import re
                test_suffix = test_name.replace("test_", "")
                # Match patterns like fr_001, req_123, etc.
                feature_pattern = re.findall(r"([a-z]+)_(\d+)", test_suffix, re.IGNORECASE)
                for prefix, num in feature_pattern:
                    test_words.add(f"{prefix.lower()}-{num}")

                # Get words from docstring
                if docstring:
                    doc_words = set(
                        w.lower()
                        for w in docstring.split()
                        if len(w) >= 3 and w.isalpha()
                    )
                    test_words.update(doc_words)
                    # Also extract feature IDs from docstring
                    doc_feature_ids = re.findall(r"\b([A-Z]{2,}-\d+)\b", docstring)
                    test_words.update(f.lower() for f in doc_feature_ids)

                # Check if any test word matches requirements
                matches_requirement = bool(test_words & requirement_keywords)

                if not matches_requirement:
                    # This test might be testing undocumented behavior
                    signals.append(
                        DriftSignal(
                            signal_type=DriftSignalType.UNDOCUMENTED_BEHAVIOR,
                            severity=DriftSeverity.LOW,
                            path=rel_path,
                            description=f"Test '{test_name}' may cover undocumented behavior",
                            detected_at=datetime.now(),
                            suggested_action="Update requirements.md or remove test if behavior is unintended",
                        )
                    )

        return signals

    def detect_refactor_hotspots(
        self,
        repo_root: Path,
        threshold: int | None = None,
        window_days: int | None = None,
    ) -> list[DriftSignal]:
        """Find frequently refactored areas.

        Args:
            repo_root: Root directory of the repository.
            threshold: Number of refactors to trigger signal.
            window_days: Lookback period in days.

        Returns:
            List of drift signals for refactor hotspots.
        """
        signals: list[DriftSignal] = []

        threshold = threshold or self._config.refactor_threshold
        window_days = window_days or self._config.refactor_window_days

        # Read audit log
        audit_log_path = repo_root / "audit" / "executions.log"
        if not audit_log_path.exists():
            return signals

        cutoff = datetime.now() - timedelta(days=window_days)
        refactor_counts: dict[str, int] = defaultdict(int)

        try:
            lines = audit_log_path.read_text(encoding="utf-8").strip().split("\n")
            for line in lines:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    # Check if this is a refactor operation
                    if entry.get("executor") != "refactor":
                        continue

                    # Check if within time window
                    timestamp_str = entry.get("timestamp", "")
                    if timestamp_str:
                        if timestamp_str.endswith("Z"):
                            timestamp_str = timestamp_str[:-1] + "+00:00"
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str)
                            # Make cutoff timezone-aware for comparison
                            if timestamp.tzinfo is not None:
                                cutoff_aware = cutoff.replace(
                                    tzinfo=timestamp.tzinfo
                                )
                                if timestamp < cutoff_aware:
                                    continue
                            elif timestamp.replace(tzinfo=None) < cutoff:
                                continue
                        except ValueError:
                            continue

                    # Count refactors per affected file
                    files_affected = entry.get("files_affected", [])
                    for file_path in files_affected:
                        refactor_counts[file_path] += 1

                except json.JSONDecodeError:
                    continue

        except OSError:
            return signals

        # Generate signals for hotspots
        for path, count in refactor_counts.items():
            if count >= threshold:
                signals.append(
                    DriftSignal(
                        signal_type=DriftSignalType.REFACTOR_HOTSPOT,
                        severity=DriftSeverity.MEDIUM,
                        path=path,
                        description=f"Refactored {count} times in {window_days} days",
                        detected_at=datetime.now(),
                        suggested_action="Review for architectural issues",
                    )
                )

        return signals

    def full_analysis(self, repo_root: Path) -> DriftReport:
        """Run complete drift analysis.

        Args:
            repo_root: Root directory of the repository.

        Returns:
            Complete drift analysis report.
        """
        signals: list[DriftSignal] = []
        code_files_count = 0
        artifacts_count = 0

        # Detect orphan code in configured source directories
        for source_dir in self._config.source_dirs:
            code_dir = repo_root / source_dir
            if code_dir.exists():
                orphan_code = self.detect_orphan_code(code_dir, repo_root)
                signals.extend(orphan_code)
                code_files_count += len(self._scan_code_files(code_dir))

        # Detect orphan plans
        orphan_plans = self.detect_orphan_plans(repo_root)
        signals.extend(orphan_plans)

        # Detect undocumented behavior
        undocumented = self.detect_undocumented_behavior(repo_root)
        signals.extend(undocumented)

        # Detect refactor hotspots
        hotspots = self.detect_refactor_hotspots(repo_root)
        signals.extend(hotspots)

        # Count artifacts
        artifacts_dir = repo_root / "artifacts"
        if artifacts_dir.exists():
            artifacts_count = sum(
                1 for _ in artifacts_dir.rglob("*.json")
                if "_meta" not in str(_)
            )

        return DriftReport(
            signals=signals,
            analyzed_at=datetime.now(),
            threshold=self._config.drift_threshold,
            code_files_scanned=code_files_count,
            artifacts_checked=artifacts_count,
        )

    def _scan_code_files(self, code_dir: Path) -> list[Path]:
        """Scan directory for code files.

        Args:
            code_dir: Directory to scan.

        Returns:
            List of code file paths.
        """
        files: list[Path] = []

        for pattern in self._config.code_patterns:
            for path in code_dir.rglob(pattern):
                if path.is_file():
                    rel_str = str(path.relative_to(code_dir))
                    if not self._config.should_ignore(rel_str):
                        files.append(path)

        return files

    def _get_covered_paths(self, repo_root: Path) -> set[str]:
        """Get all file paths covered by ImplementationPlans.

        Args:
            repo_root: Root directory of the repository.

        Returns:
            Set of covered file paths.
        """
        covered: set[str] = set()

        impl_plans = self._load_artifacts_of_type(repo_root, "ImplementationPlan")
        for _, artifact_data in impl_plans:
            payload = artifact_data.get("payload", {})
            if target := payload.get("target"):
                covered.add(target.replace("\\", "/"))

        # Also add files from RefactorPlans
        refactor_plans = self._load_artifacts_of_type(repo_root, "RefactorPlan")
        for _, artifact_data in refactor_plans:
            payload = artifact_data.get("payload", {})
            if from_path := payload.get("from_path"):
                covered.add(from_path.replace("\\", "/"))
            if to_path := payload.get("to_path"):
                covered.add(to_path.replace("\\", "/"))

        return covered

    def _load_artifacts_of_type(
        self, repo_root: Path, artifact_type: str
    ) -> list[tuple[Path, dict]]:
        """Load artifacts of a specific type from the filesystem.

        Args:
            repo_root: Root directory of the repository.
            artifact_type: Type of artifacts to load.

        Returns:
            List of (path, data) tuples for matching artifacts.
        """
        artifacts: list[tuple[Path, dict]] = []
        artifacts_dir = repo_root / "artifacts"

        if not artifacts_dir.exists():
            return artifacts

        # Map artifact type to directory name
        type_dir_map = {
            "ImplementationPlan": "implementation_plans",
            "RefactorPlan": "refactor_plans",
            "ProjectPlan": "project_plans",
            "ArchitecturePlan": "architecture_plans",
            "ScaffoldPlan": "scaffold_plans",
            "TestPlan": "test_plans",
        }

        dir_name = type_dir_map.get(artifact_type, artifact_type.lower())
        type_dir = artifacts_dir / dir_name

        if not type_dir.exists():
            return artifacts

        for artifact_path in type_dir.glob("*.json"):
            try:
                data = json.loads(artifact_path.read_text(encoding="utf-8"))
                if data.get("artifact_type") == artifact_type:
                    artifacts.append((artifact_path, data))
            except (json.JSONDecodeError, OSError):
                continue

        return artifacts
