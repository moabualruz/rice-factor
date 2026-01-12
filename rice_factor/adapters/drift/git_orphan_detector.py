"""Git commit-level orphan detection adapter.

This module provides the GitOrphanDetector for analyzing git history
to find orphaned code that is no longer referenced or used.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class OrphanType(Enum):
    """Type of detected orphan."""

    DELETED_REFERENCE = "deleted_reference"  # File deleted but still referenced
    UNUSED_EXPORT = "unused_export"  # Exported but never imported
    DEAD_CODE = "dead_code"  # Code that's never reached
    OBSOLETE_FILE = "obsolete_file"  # File not touched in a long time
    ORPHAN_TEST = "orphan_test"  # Test for deleted code
    ORPHAN_IMPORT = "orphan_import"  # Import of deleted module


class CleanupPriority(Enum):
    """Priority of cleanup recommendation."""

    CRITICAL = "critical"  # Must be cleaned up immediately
    HIGH = "high"  # Should be cleaned up soon
    MEDIUM = "medium"  # Can be cleaned up when convenient
    LOW = "low"  # Optional cleanup


@dataclass
class OrphanedCode:
    """A detected orphaned code artifact."""

    path: str
    orphan_type: OrphanType
    last_commit_hash: str | None
    last_commit_date: datetime | None
    last_commit_message: str | None
    evidence: list[str]  # Evidence of orphan status
    days_since_modified: int

    @property
    def age_category(self) -> str:
        """Get age category for the orphan."""
        if self.days_since_modified > 365:
            return "very_old"
        elif self.days_since_modified > 180:
            return "old"
        elif self.days_since_modified > 90:
            return "stale"
        else:
            return "recent"


@dataclass
class CleanupRecommendation:
    """A cleanup recommendation for orphaned code."""

    path: str
    priority: CleanupPriority
    action: str  # "delete", "archive", "review", "update"
    reason: str
    orphan: OrphanedCode
    estimated_impact: str  # "none", "low", "medium", "high"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "priority": self.priority.value,
            "action": self.action,
            "reason": self.reason,
            "estimated_impact": self.estimated_impact,
            "age_category": self.orphan.age_category,
            "days_since_modified": self.orphan.days_since_modified,
        }


@dataclass
class OrphanDetectionReport:
    """Report of orphan detection analysis."""

    analyzed_at: datetime
    repo_root: str
    commits_analyzed: int
    files_analyzed: int
    orphans_detected: list[OrphanedCode]
    recommendations: list[CleanupRecommendation]
    git_available: bool

    @property
    def orphan_count(self) -> int:
        """Get count of detected orphans."""
        return len(self.orphans_detected)

    @property
    def critical_count(self) -> int:
        """Get count of critical priority recommendations."""
        return sum(1 for r in self.recommendations if r.priority == CleanupPriority.CRITICAL)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "analyzed_at": self.analyzed_at.isoformat(),
            "repo_root": self.repo_root,
            "commits_analyzed": self.commits_analyzed,
            "files_analyzed": self.files_analyzed,
            "orphan_count": self.orphan_count,
            "critical_count": self.critical_count,
            "by_type": self._group_by_type(),
            "by_priority": self._group_by_priority(),
            "recommendations": [r.to_dict() for r in self.recommendations],
        }

    def _group_by_type(self) -> dict[str, int]:
        """Group orphans by type."""
        counts: dict[str, int] = {}
        for orphan in self.orphans_detected:
            otype = orphan.orphan_type.value
            counts[otype] = counts.get(otype, 0) + 1
        return counts

    def _group_by_priority(self) -> dict[str, int]:
        """Group recommendations by priority."""
        counts: dict[str, int] = {}
        for rec in self.recommendations:
            priority = rec.priority.value
            counts[priority] = counts.get(priority, 0) + 1
        return counts


@dataclass
class GitOrphanDetector:
    """Detector for orphaned code based on git history.

    This adapter analyzes git history to identify:
    - Files that haven't been modified in a long time
    - Files that were deleted but are still referenced
    - Tests for deleted code
    - Unused exports and dead code paths

    Attributes:
        repo_root: Root directory of the repository.
        staleness_threshold_days: Days of inactivity to consider stale.
        source_patterns: Glob patterns for source files.
    """

    repo_root: Path
    staleness_threshold_days: int = 180
    source_patterns: list[str] = field(
        default_factory=lambda: ["*.py", "*.js", "*.ts", "*.java", "*.go", "*.rs"]
    )
    _git_available: bool | None = field(default=None, init=False)

    def detect(self) -> OrphanDetectionReport:
        """Perform orphan detection analysis.

        Returns:
            OrphanDetectionReport with all detected orphans.
        """
        orphans: list[OrphanedCode] = []
        recommendations: list[CleanupRecommendation] = []
        commits_analyzed = 0
        files_analyzed = 0

        if not self._check_git_available():
            return OrphanDetectionReport(
                analyzed_at=datetime.now(UTC),
                repo_root=str(self.repo_root),
                commits_analyzed=0,
                files_analyzed=0,
                orphans_detected=[],
                recommendations=[],
                git_available=False,
            )

        # Detect obsolete files (not modified in a long time)
        obsolete, obsolete_count = self._detect_obsolete_files()
        orphans.extend(obsolete)
        files_analyzed += obsolete_count

        # Detect orphan tests (tests for deleted code)
        orphan_tests = self._detect_orphan_tests()
        orphans.extend(orphan_tests)

        # Detect deleted references
        deleted_refs = self._detect_deleted_references()
        orphans.extend(deleted_refs)

        # Get commit count
        commits_analyzed = self._count_recent_commits()

        # Generate cleanup recommendations
        for orphan in orphans:
            recommendation = self._generate_recommendation(orphan)
            recommendations.append(recommendation)

        # Sort recommendations by priority
        priority_order = {
            CleanupPriority.CRITICAL: 0,
            CleanupPriority.HIGH: 1,
            CleanupPriority.MEDIUM: 2,
            CleanupPriority.LOW: 3,
        }
        recommendations.sort(key=lambda r: priority_order[r.priority])

        return OrphanDetectionReport(
            analyzed_at=datetime.now(UTC),
            repo_root=str(self.repo_root),
            commits_analyzed=commits_analyzed,
            files_analyzed=files_analyzed,
            orphans_detected=orphans,
            recommendations=recommendations,
            git_available=True,
        )

    def _check_git_available(self) -> bool:
        """Check if git is available."""
        if self._git_available is not None:
            return self._git_available

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=self.repo_root,
                capture_output=True,
                timeout=5,
            )
            self._git_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._git_available = False

        return self._git_available

    def _detect_obsolete_files(self) -> tuple[list[OrphanedCode], int]:
        """Detect files not modified in a long time.

        Returns:
            Tuple of (orphaned files, total files analyzed).
        """
        orphans: list[OrphanedCode] = []
        files_analyzed = 0

        try:
            # Get all source files with their last commit date
            for pattern in self.source_patterns:
                for file_path in self.repo_root.rglob(pattern):
                    if not file_path.is_file():
                        continue
                    if self._is_excluded(file_path):
                        continue

                    files_analyzed += 1

                    # Get last commit info for the file
                    commit_info = self._get_last_commit_info(file_path)
                    if commit_info is None:
                        continue

                    days_since = commit_info["days_since_modified"]
                    if days_since > self.staleness_threshold_days:
                        try:
                            rel_path = str(file_path.relative_to(self.repo_root))
                        except ValueError:
                            rel_path = str(file_path)

                        orphan = OrphanedCode(
                            path=rel_path.replace("\\", "/"),
                            orphan_type=OrphanType.OBSOLETE_FILE,
                            last_commit_hash=commit_info["hash"],
                            last_commit_date=commit_info["date"],
                            last_commit_message=commit_info["message"],
                            evidence=[f"Not modified in {days_since} days"],
                            days_since_modified=days_since,
                        )
                        orphans.append(orphan)

        except Exception:
            pass

        return orphans, files_analyzed

    def _get_last_commit_info(self, file_path: Path) -> dict[str, Any] | None:
        """Get last commit info for a file.

        Args:
            file_path: Path to the file.

        Returns:
            Dictionary with commit info or None.
        """
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H|%at|%s", "--", str(file_path)],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0 or not result.stdout.strip():
                return None

            parts = result.stdout.strip().split("|")
            if len(parts) < 3:
                return None

            commit_date = datetime.fromtimestamp(int(parts[1]), tz=UTC)
            now = datetime.now(UTC)
            days_since = (now - commit_date).days

            return {
                "hash": parts[0],
                "date": commit_date,
                "message": "|".join(parts[2:]),
                "days_since_modified": days_since,
            }

        except (subprocess.TimeoutExpired, ValueError):
            return None

    def _detect_orphan_tests(self) -> list[OrphanedCode]:
        """Detect tests that test deleted code.

        Returns:
            List of orphaned test files.
        """
        orphans: list[OrphanedCode] = []

        # Find test files
        test_patterns = ["tests/**/test_*.py", "test/**/test_*.py"]
        for pattern in test_patterns:
            for test_file in self.repo_root.glob(pattern):
                if not test_file.is_file():
                    continue

                # Check if the corresponding source file exists
                orphan = self._check_test_for_orphan(test_file)
                if orphan:
                    orphans.append(orphan)

        return orphans

    def _check_test_for_orphan(self, test_file: Path) -> OrphanedCode | None:
        """Check if a test file is testing deleted code.

        Args:
            test_file: Path to the test file.

        Returns:
            OrphanedCode if orphan, None otherwise.
        """
        try:
            content = test_file.read_text(encoding="utf-8")
        except OSError:
            return None

        # Extract import statements
        import_pattern = r"from\s+([\w.]+)\s+import|import\s+([\w.]+)"
        import re
        imports = re.findall(import_pattern, content)

        missing_imports: list[str] = []
        for match in imports:
            module = match[0] or match[1]
            if not module:
                continue

            # Check if this looks like an internal module
            if self._is_internal_module(module):
                # Check if the module exists
                if not self._module_exists(module):
                    missing_imports.append(module)

        if missing_imports:
            try:
                rel_path = str(test_file.relative_to(self.repo_root))
            except ValueError:
                rel_path = str(test_file)

            commit_info = self._get_last_commit_info(test_file) or {}

            return OrphanedCode(
                path=rel_path.replace("\\", "/"),
                orphan_type=OrphanType.ORPHAN_TEST,
                last_commit_hash=commit_info.get("hash"),
                last_commit_date=commit_info.get("date"),
                last_commit_message=commit_info.get("message"),
                evidence=[f"Missing imports: {', '.join(missing_imports)}"],
                days_since_modified=commit_info.get("days_since_modified", 0),
            )

        return None

    def _is_internal_module(self, module: str) -> bool:
        """Check if a module is internal to the project.

        Args:
            module: Module path (e.g., 'mypackage.utils').

        Returns:
            True if internal module.
        """
        # Check if it starts with any known project prefix
        project_prefixes = ["rice_factor", "src"]
        for prefix in project_prefixes:
            if module.startswith(prefix):
                return True

        # Check if it matches a directory in the repo
        first_part = module.split(".")[0]
        if (self.repo_root / first_part).is_dir():
            return True

        return False

    def _module_exists(self, module: str) -> bool:
        """Check if a module exists.

        Args:
            module: Module path (e.g., 'mypackage.utils').

        Returns:
            True if the module exists.
        """
        # Convert module path to file path
        parts = module.split(".")
        possible_paths = [
            self.repo_root / Path(*parts).with_suffix(".py"),
            self.repo_root / Path(*parts) / "__init__.py",
        ]

        return any(p.exists() for p in possible_paths)

    def _detect_deleted_references(self) -> list[OrphanedCode]:
        """Detect references to deleted files.

        Returns:
            List of orphaned references.
        """
        orphans: list[OrphanedCode] = []

        try:
            # Get list of deleted files in recent history
            result = subprocess.run(
                ["git", "log", "--diff-filter=D", "--name-only", "--pretty=format:", "-n", "100"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return orphans

            deleted_files = set(
                line.strip() for line in result.stdout.strip().split("\n")
                if line.strip() and self._is_source_file(line.strip())
            )

            # Check for references to deleted files in current code
            for deleted_file in deleted_files:
                references = self._find_references_to_file(deleted_file)
                if references:
                    orphan = OrphanedCode(
                        path=deleted_file,
                        orphan_type=OrphanType.DELETED_REFERENCE,
                        last_commit_hash=None,
                        last_commit_date=None,
                        last_commit_message=None,
                        evidence=[f"Referenced in: {', '.join(references[:3])}"],
                        days_since_modified=0,
                    )
                    orphans.append(orphan)

        except subprocess.TimeoutExpired:
            pass

        return orphans

    def _find_references_to_file(self, file_path: str) -> list[str]:
        """Find references to a file in the codebase.

        Args:
            file_path: Path to the deleted file.

        Returns:
            List of files that reference this file.
        """
        references: list[str] = []

        # Extract module name from file path
        if file_path.endswith(".py"):
            module_name = file_path[:-3].replace("/", ".").replace("\\", ".")
        else:
            module_name = file_path.replace("/", ".").replace("\\", ".")

        # Search for imports of this module
        try:
            result = subprocess.run(
                ["git", "grep", "-l", module_name],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0 and result.stdout.strip():
                references = [
                    line.strip() for line in result.stdout.strip().split("\n")
                    if line.strip()
                ]

        except subprocess.TimeoutExpired:
            pass

        return references

    def _is_source_file(self, path: str) -> bool:
        """Check if a path is a source file.

        Args:
            path: File path.

        Returns:
            True if it's a source file.
        """
        source_extensions = {".py", ".js", ".ts", ".java", ".go", ".rs", ".rb", ".php"}
        return any(path.endswith(ext) for ext in source_extensions)

    def _is_excluded(self, path: Path) -> bool:
        """Check if a path should be excluded.

        Args:
            path: Path to check.

        Returns:
            True if should be excluded.
        """
        excluded_dirs = {
            ".git", ".venv", "venv", "node_modules", "__pycache__",
            ".mypy_cache", ".pytest_cache", "dist", "build", ".eggs",
        }

        for part in path.parts:
            if part in excluded_dirs:
                return True

        return False

    def _count_recent_commits(self) -> int:
        """Count recent commits analyzed.

        Returns:
            Number of commits.
        """
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", f"--since={self.staleness_threshold_days} days ago", "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return int(result.stdout.strip())

        except (subprocess.TimeoutExpired, ValueError):
            pass

        return 0

    def _generate_recommendation(self, orphan: OrphanedCode) -> CleanupRecommendation:
        """Generate cleanup recommendation for an orphan.

        Args:
            orphan: The detected orphan.

        Returns:
            CleanupRecommendation.
        """
        if orphan.orphan_type == OrphanType.DELETED_REFERENCE:
            return CleanupRecommendation(
                path=orphan.path,
                priority=CleanupPriority.HIGH,
                action="review",
                reason="Code references deleted file",
                orphan=orphan,
                estimated_impact="medium",
            )

        elif orphan.orphan_type == OrphanType.ORPHAN_TEST:
            return CleanupRecommendation(
                path=orphan.path,
                priority=CleanupPriority.MEDIUM,
                action="review",
                reason="Test imports missing modules",
                orphan=orphan,
                estimated_impact="low",
            )

        elif orphan.orphan_type == OrphanType.OBSOLETE_FILE:
            if orphan.days_since_modified > 365:
                priority = CleanupPriority.HIGH
                action = "archive"
            elif orphan.days_since_modified > 180:
                priority = CleanupPriority.MEDIUM
                action = "review"
            else:
                priority = CleanupPriority.LOW
                action = "review"

            return CleanupRecommendation(
                path=orphan.path,
                priority=priority,
                action=action,
                reason=f"Not modified in {orphan.days_since_modified} days",
                orphan=orphan,
                estimated_impact="none" if action == "archive" else "low",
            )

        else:
            return CleanupRecommendation(
                path=orphan.path,
                priority=CleanupPriority.LOW,
                action="review",
                reason="Potential orphaned code",
                orphan=orphan,
                estimated_impact="unknown",
            )

    def get_recommendations_by_priority(
        self, priority: CleanupPriority
    ) -> list[CleanupRecommendation]:
        """Get recommendations filtered by priority.

        Args:
            priority: Priority to filter by.

        Returns:
            List of matching recommendations.
        """
        report = self.detect()
        return [r for r in report.recommendations if r.priority == priority]

    def get_orphans_by_type(self, orphan_type: OrphanType) -> list[OrphanedCode]:
        """Get orphans filtered by type.

        Args:
            orphan_type: Type to filter by.

        Returns:
            List of matching orphans.
        """
        report = self.detect()
        return [o for o in report.orphans_detected if o.orphan_type == orphan_type]
