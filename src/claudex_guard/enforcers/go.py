"""Go code quality enforcer.

This module provides enforcement of Go coding standards,
focusing on AI-generated code antipatterns.
"""

from pathlib import Path

from ..core.base_enforcer import BaseEnforcer
from ..core.violation import Violation
from ..services.go_auto_fixer import GoAutoFixer
from ..standards.go_patterns import GoPatterns


class GoEnforcer(BaseEnforcer):
    """Go code quality enforcer using modular architecture."""

    def __init__(self) -> None:
        """Initialize Go enforcer with patterns and auto-fixer."""
        super().__init__("go")
        self.patterns = GoPatterns()
        self.auto_fixer = GoAutoFixer()

    def is_supported_file(self, file_path: Path) -> bool:
        """Check if file is Go (.go).

        Args:
            file_path: Path to file to check

        Returns:
            True if file extension is .go
        """
        return file_path.suffix == ".go"

    def apply_automatic_fixes(self, file_path: Path) -> list[str]:
        """Apply automatic fixes via gofmt integration.

        Args:
            file_path: Path to file to fix

        Returns:
            List of strings describing fixes applied
        """
        return self.auto_fixer.apply_fixes(file_path)

    def analyze_file(self, file_path: Path) -> list[Violation]:
        """Analyze Go file using golangci-lint and pattern detection.

        Args:
            file_path: Path to file to analyze

        Returns:
            List of Violation objects found in the file
        """
        violations: list[Violation] = []

        if not file_path.exists():
            return violations

        # Read file content for pattern analysis
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()
        except (OSError, UnicodeDecodeError):
            return violations

        # Run golangci-lint for linting violations
        violations.extend(self.patterns.run_golangci_lint(file_path))

        # Check for banned packages
        violations.extend(self.patterns.check_banned_packages(content, file_path))

        # Check for panic() abuse
        violations.extend(self.patterns.check_panic_usage(lines, file_path))

        # Check for error ignoring
        violations.extend(self.patterns.check_error_ignoring(lines, file_path))

        return violations
