"""Undocumented behavior detector adapter.

This module provides the UndocumentedBehaviorDetector for analyzing tests
and identifying behavior that is not documented in requirements.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class DetectionConfidence(Enum):
    """Confidence level of undocumented behavior detection."""

    HIGH = "high"  # Strong evidence of undocumented behavior
    MEDIUM = "medium"  # Possible undocumented behavior
    LOW = "low"  # Weak evidence, may be false positive


class BehaviorCategory(Enum):
    """Category of detected behavior."""

    EDGE_CASE = "edge_case"  # Edge case handling not in requirements
    ERROR_HANDLING = "error_handling"  # Error handling not documented
    PERFORMANCE = "performance"  # Performance-related behavior
    INTEGRATION = "integration"  # Integration behavior
    REGRESSION = "regression"  # Regression test without requirement
    UNKNOWN = "unknown"  # Cannot categorize


@dataclass
class DetectedBehavior:
    """A detected undocumented behavior."""

    test_file: str
    test_name: str
    line_number: int
    description: str
    category: BehaviorCategory
    confidence: DetectionConfidence
    suggested_requirement: str | None = None
    docstring: str | None = None


@dataclass
class RequirementMatch:
    """A match between a test and a requirement."""

    test_name: str
    requirement_id: str
    requirement_text: str
    match_score: float  # 0.0 to 1.0


@dataclass
class AnalysisReport:
    """Report of undocumented behavior analysis."""

    analyzed_at: datetime
    repo_root: str
    test_files_scanned: int
    requirements_loaded: int
    total_tests: int
    matched_tests: int
    undocumented_behaviors: list[DetectedBehavior]
    matches: list[RequirementMatch]

    @property
    def undocumented_count(self) -> int:
        """Get count of undocumented behaviors."""
        return len(self.undocumented_behaviors)

    @property
    def coverage_percentage(self) -> float:
        """Get percentage of tests with requirements."""
        if self.total_tests == 0:
            return 100.0
        return (self.matched_tests / self.total_tests) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "analyzed_at": self.analyzed_at.isoformat(),
            "repo_root": self.repo_root,
            "test_files_scanned": self.test_files_scanned,
            "requirements_loaded": self.requirements_loaded,
            "total_tests": self.total_tests,
            "matched_tests": self.matched_tests,
            "undocumented_count": self.undocumented_count,
            "coverage_percentage": round(self.coverage_percentage, 2),
            "by_category": self._group_by_category(),
            "by_confidence": self._group_by_confidence(),
        }

    def _group_by_category(self) -> dict[str, int]:
        """Group undocumented behaviors by category."""
        counts: dict[str, int] = {}
        for behavior in self.undocumented_behaviors:
            cat = behavior.category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def _group_by_confidence(self) -> dict[str, int]:
        """Group undocumented behaviors by confidence."""
        counts: dict[str, int] = {}
        for behavior in self.undocumented_behaviors:
            conf = behavior.confidence.value
            counts[conf] = counts.get(conf, 0) + 1
        return counts


@dataclass
class UndocumentedBehaviorDetector:
    """Detector for undocumented behavior in tests.

    This adapter performs static analysis of test files to identify
    tests that appear to cover behavior not documented in requirements.

    Attributes:
        repo_root: Root directory of the repository.
        requirements_paths: Paths to requirements documents.
        test_patterns: Glob patterns for test files.
    """

    repo_root: Path
    requirements_paths: list[str] = field(
        default_factory=lambda: [".project/requirements.md", "docs/requirements.md"]
    )
    test_patterns: list[str] = field(
        default_factory=lambda: ["tests/**/*.py", "test/**/*.py"]
    )
    _requirements_keywords: set[str] = field(default_factory=set, init=False)
    _requirement_ids: set[str] = field(default_factory=set, init=False)

    def analyze(self) -> AnalysisReport:
        """Perform full analysis of test coverage.

        Returns:
            AnalysisReport with all detected undocumented behaviors.
        """
        # Load requirements
        self._load_requirements()

        # Find all test files
        test_files = self._find_test_files()

        # Analyze each test file
        all_behaviors: list[DetectedBehavior] = []
        all_matches: list[RequirementMatch] = []
        total_tests = 0

        for test_file in test_files:
            behaviors, matches, test_count = self._analyze_test_file(test_file)
            all_behaviors.extend(behaviors)
            all_matches.extend(matches)
            total_tests += test_count

        return AnalysisReport(
            analyzed_at=datetime.now(UTC),
            repo_root=str(self.repo_root),
            test_files_scanned=len(test_files),
            requirements_loaded=len(self._requirements_keywords) + len(self._requirement_ids),
            total_tests=total_tests,
            matched_tests=len(all_matches),
            undocumented_behaviors=all_behaviors,
            matches=all_matches,
        )

    def _load_requirements(self) -> None:
        """Load and parse requirements documents."""
        self._requirements_keywords = set()
        self._requirement_ids = set()

        for rel_path in self.requirements_paths:
            path = self.repo_root / rel_path
            if path.exists():
                content = path.read_text(encoding="utf-8")
                self._extract_keywords(content)
                self._extract_requirement_ids(content)

    def _extract_keywords(self, content: str) -> None:
        """Extract keywords from requirements content.

        Args:
            content: Requirements document content.
        """
        # Common stop words to exclude
        stop_words = {
            "the", "and", "for", "are", "but", "not", "you", "all",
            "can", "has", "was", "one", "our", "out", "use", "with",
            "this", "that", "have", "from", "they", "will", "would",
            "could", "should", "must", "may", "when", "what", "which",
            "each", "any", "more", "some", "such", "only", "other",
            "than", "then", "into", "also", "most", "very", "just",
            "test", "tests", "testing", "tested", "shall", "given",
        }

        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", "", content)
        text = re.sub(r"`[^`]+`", "", text)

        # Extract meaningful words from bullet points and headers
        patterns = [
            r"^[\s]*[-*]\s+(.+)$",  # Bullet points
            r"^\d+\.\s+(.+)$",  # Numbered lists
            r"^#{1,6}\s+(.+)$",  # Headers
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                words = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", match)
                for word in words:
                    lower = word.lower()
                    if len(lower) >= 3 and lower not in stop_words:
                        self._requirements_keywords.add(lower)

    def _extract_requirement_ids(self, content: str) -> None:
        """Extract requirement IDs from content.

        Args:
            content: Requirements document content.
        """
        # Match patterns like FR-001, REQ-123, US-456, etc.
        pattern = r"\b([A-Z]{2,}-\d+)\b"
        matches = re.findall(pattern, content)
        self._requirement_ids.update(m.lower() for m in matches)

    def _find_test_files(self) -> list[Path]:
        """Find all test files matching patterns.

        Returns:
            List of test file paths.
        """
        files: list[Path] = []

        for pattern in self.test_patterns:
            for path in self.repo_root.glob(pattern):
                if path.is_file():
                    # Check if it's actually a test file
                    name = path.name
                    if name.startswith("test_") or name.endswith("_test.py"):
                        files.append(path)

        return list(set(files))

    def _analyze_test_file(
        self, test_file: Path
    ) -> tuple[list[DetectedBehavior], list[RequirementMatch], int]:
        """Analyze a test file for undocumented behavior.

        Args:
            test_file: Path to the test file.

        Returns:
            Tuple of (undocumented behaviors, matched requirements, test count).
        """
        behaviors: list[DetectedBehavior] = []
        matches: list[RequirementMatch] = []
        test_count = 0

        try:
            content = test_file.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except (OSError, SyntaxError):
            return behaviors, matches, 0

        try:
            rel_path = str(test_file.relative_to(self.repo_root))
        except ValueError:
            rel_path = str(test_file)
        rel_path = rel_path.replace("\\", "/")

        # Find all test functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                test_count += 1
                docstring = ast.get_docstring(node) or ""

                # Try to match to requirement
                match = self._match_to_requirement(node.name, docstring)
                if match:
                    matches.append(match)
                else:
                    # This is potentially undocumented behavior
                    behavior = self._analyze_test_function(
                        node, rel_path, docstring
                    )
                    if behavior:
                        behaviors.append(behavior)

        return behaviors, matches, test_count

    def _match_to_requirement(
        self, test_name: str, docstring: str
    ) -> RequirementMatch | None:
        """Try to match a test to a requirement.

        Args:
            test_name: Name of the test function.
            docstring: Test docstring.

        Returns:
            RequirementMatch if found, None otherwise.
        """
        # Extract words from test name
        test_suffix = test_name.replace("test_", "")
        test_words = set(w.lower() for w in test_suffix.split("_") if len(w) >= 3)

        # Check for requirement ID patterns in test name
        id_pattern = re.findall(r"([a-z]+)_(\d+)", test_suffix, re.IGNORECASE)
        for prefix, num in id_pattern:
            req_id = f"{prefix.lower()}-{num}"
            if req_id in self._requirement_ids:
                return RequirementMatch(
                    test_name=test_name,
                    requirement_id=req_id.upper(),
                    requirement_text=f"Requirement {req_id.upper()}",
                    match_score=1.0,
                )

        # Check for requirement IDs in docstring
        if docstring:
            doc_ids = re.findall(r"\b([A-Z]{2,}-\d+)\b", docstring)
            for doc_id in doc_ids:
                if doc_id.lower() in self._requirement_ids:
                    return RequirementMatch(
                        test_name=test_name,
                        requirement_id=doc_id,
                        requirement_text=f"Requirement {doc_id}",
                        match_score=1.0,
                    )

        # Check for keyword matches
        keyword_matches = test_words & self._requirements_keywords
        if keyword_matches:
            score = len(keyword_matches) / max(len(test_words), 1)
            if score >= 0.5:  # At least 50% keyword match
                return RequirementMatch(
                    test_name=test_name,
                    requirement_id="",
                    requirement_text=f"Keywords: {', '.join(keyword_matches)}",
                    match_score=score,
                )

        # Check docstring for keywords
        if docstring:
            doc_words = set(
                w.lower() for w in docstring.split()
                if len(w) >= 3 and w.isalpha()
            )
            doc_matches = doc_words & self._requirements_keywords
            if len(doc_matches) >= 2:
                score = min(len(doc_matches) / 5, 1.0)
                return RequirementMatch(
                    test_name=test_name,
                    requirement_id="",
                    requirement_text=f"Doc keywords: {', '.join(list(doc_matches)[:5])}",
                    match_score=score,
                )

        return None

    def _analyze_test_function(
        self, node: ast.FunctionDef, file_path: str, docstring: str
    ) -> DetectedBehavior | None:
        """Analyze a test function for undocumented behavior.

        Args:
            node: AST node of the test function.
            file_path: Path to the test file.
            docstring: Test docstring.

        Returns:
            DetectedBehavior if undocumented, None otherwise.
        """
        test_name = node.name
        line_number = node.lineno

        # Determine category and confidence
        category = self._categorize_test(test_name, docstring)
        confidence = self._determine_confidence(test_name, docstring, category)

        # Generate suggested requirement
        suggested = self._suggest_requirement(test_name, docstring, category)

        return DetectedBehavior(
            test_file=file_path,
            test_name=test_name,
            line_number=line_number,
            description=self._generate_description(test_name, category),
            category=category,
            confidence=confidence,
            suggested_requirement=suggested,
            docstring=docstring if docstring else None,
        )

    def _categorize_test(
        self, test_name: str, docstring: str
    ) -> BehaviorCategory:
        """Categorize a test based on its name and docstring.

        Args:
            test_name: Name of the test function.
            docstring: Test docstring.

        Returns:
            BehaviorCategory.
        """
        name_lower = test_name.lower()
        doc_lower = (docstring or "").lower()
        combined = f"{name_lower} {doc_lower}"

        # Edge case indicators
        edge_indicators = [
            "edge", "boundary", "limit", "max", "min", "empty",
            "null", "none", "zero", "negative", "overflow", "underflow",
        ]
        if any(ind in combined for ind in edge_indicators):
            return BehaviorCategory.EDGE_CASE

        # Error handling indicators
        error_indicators = [
            "error", "exception", "fail", "invalid", "malformed",
            "corrupt", "missing", "timeout", "retry",
        ]
        if any(ind in combined for ind in error_indicators):
            return BehaviorCategory.ERROR_HANDLING

        # Performance indicators
        perf_indicators = [
            "performance", "benchmark", "speed", "fast", "slow",
            "memory", "cache", "optimize", "efficient",
        ]
        if any(ind in combined for ind in perf_indicators):
            return BehaviorCategory.PERFORMANCE

        # Integration indicators
        integration_indicators = [
            "integration", "e2e", "end_to_end", "system",
            "api", "database", "external",
        ]
        if any(ind in combined for ind in integration_indicators):
            return BehaviorCategory.INTEGRATION

        # Regression indicators
        regression_indicators = [
            "regression", "bug", "fix", "issue", "ticket",
            "gh_", "jira_", "bug_",
        ]
        if any(ind in combined for ind in regression_indicators):
            return BehaviorCategory.REGRESSION

        return BehaviorCategory.UNKNOWN

    def _determine_confidence(
        self,
        test_name: str,
        docstring: str,
        category: BehaviorCategory,
    ) -> DetectionConfidence:
        """Determine confidence level of detection.

        Args:
            test_name: Name of the test function.
            docstring: Test docstring.
            category: Detected category.

        Returns:
            DetectionConfidence level.
        """
        # If we couldn't categorize, lower confidence
        if category == BehaviorCategory.UNKNOWN:
            return DetectionConfidence.LOW

        # If there's a docstring, it might be intentionally undocumented
        if docstring and len(docstring) > 50:
            return DetectionConfidence.MEDIUM

        # Regression tests are typically intentionally undocumented
        if category == BehaviorCategory.REGRESSION:
            return DetectionConfidence.LOW

        # Edge cases and error handling are often legitimately undocumented
        if category in (BehaviorCategory.EDGE_CASE, BehaviorCategory.ERROR_HANDLING):
            return DetectionConfidence.MEDIUM

        return DetectionConfidence.HIGH

    def _generate_description(
        self, test_name: str, category: BehaviorCategory
    ) -> str:
        """Generate a description for the undocumented behavior.

        Args:
            test_name: Name of the test function.
            category: Detected category.

        Returns:
            Human-readable description.
        """
        suffix = test_name.replace("test_", "")
        readable = suffix.replace("_", " ")

        category_descriptions = {
            BehaviorCategory.EDGE_CASE: "Edge case test",
            BehaviorCategory.ERROR_HANDLING: "Error handling test",
            BehaviorCategory.PERFORMANCE: "Performance test",
            BehaviorCategory.INTEGRATION: "Integration test",
            BehaviorCategory.REGRESSION: "Regression test",
            BehaviorCategory.UNKNOWN: "Test",
        }

        prefix = category_descriptions.get(category, "Test")
        return f"{prefix}: {readable}"

    def _suggest_requirement(
        self,
        test_name: str,
        docstring: str,
        category: BehaviorCategory,
    ) -> str:
        """Suggest a requirement for the behavior.

        Args:
            test_name: Name of the test function.
            docstring: Test docstring.
            category: Detected category.

        Returns:
            Suggested requirement text.
        """
        suffix = test_name.replace("test_", "")
        readable = suffix.replace("_", " ")

        if category == BehaviorCategory.EDGE_CASE:
            return f"The system shall handle {readable}"
        elif category == BehaviorCategory.ERROR_HANDLING:
            return f"The system shall gracefully handle {readable}"
        elif category == BehaviorCategory.PERFORMANCE:
            return f"The system shall meet performance requirements for {readable}"
        elif category == BehaviorCategory.INTEGRATION:
            return f"The system shall integrate with {readable}"
        elif category == BehaviorCategory.REGRESSION:
            return f"The system shall not regress on {readable}"
        else:
            return f"The system shall support {readable}"

    def get_high_confidence_behaviors(self) -> list[DetectedBehavior]:
        """Get only high-confidence undocumented behaviors.

        Returns:
            List of high-confidence detections.
        """
        report = self.analyze()
        return [
            b for b in report.undocumented_behaviors
            if b.confidence == DetectionConfidence.HIGH
        ]

    def get_behaviors_by_category(
        self, category: BehaviorCategory
    ) -> list[DetectedBehavior]:
        """Get undocumented behaviors by category.

        Args:
            category: Category to filter by.

        Returns:
            List of matching behaviors.
        """
        report = self.analyze()
        return [
            b for b in report.undocumented_behaviors
            if b.category == category
        ]
