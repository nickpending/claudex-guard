"""TypeScript/JavaScript code quality enforcer.

This module provides enforcement of TypeScript and JavaScript coding standards,
focusing on AI-generated code antipatterns.
"""

from pathlib import Path

from ..core.base_enforcer import BaseEnforcer
from ..core.violation import Violation
from ..services.typescript_auto_fixer import TypeScriptAutoFixer
from ..standards.typescript_patterns import TypeScriptPatterns


class TypeScriptEnforcer(BaseEnforcer):
    """TypeScript/JavaScript code quality enforcer using modular architecture."""

    def __init__(self) -> None:
        """Initialize TypeScript enforcer with patterns and auto-fixer."""
        super().__init__("typescript")
        self.patterns = TypeScriptPatterns()
        self.auto_fixer = TypeScriptAutoFixer()

    def is_supported_file(self, file_path: Path) -> bool:
        """Check if file is TypeScript/JavaScript (.ts, .tsx, .js, .jsx).

        Args:
            file_path: Path to file to check

        Returns:
            True if file extension is .ts, .tsx, .js, or .jsx
        """
        return file_path.suffix in {".ts", ".tsx", ".js", ".jsx"}

    def apply_automatic_fixes(self, file_path: Path) -> list[str]:
        """Apply automatic fixes via ESLint and Prettier integration.

        Args:
            file_path: Path to file to fix

        Returns:
            List of strings describing fixes applied
        """
        return self.auto_fixer.apply_fixes(file_path)

    def analyze_file(self, file_path: Path) -> list[Violation]:
        """Analyze TypeScript/JavaScript file using ESLint, tsc, and pattern detection.

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

        # Run ESLint for linting violations
        violations.extend(self.patterns.run_eslint(file_path))

        # Run tsc for type checking (TypeScript files only)
        if file_path.suffix in {".ts", ".tsx"}:
            violations.extend(self.patterns.run_tsc(file_path))

        # Check for banned imports
        violations.extend(self.patterns.check_banned_imports(content, file_path))

        # Check for console.log usage
        violations.extend(self.patterns.check_console_usage(lines, file_path))

        return violations
