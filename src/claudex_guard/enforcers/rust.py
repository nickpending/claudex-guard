"""Rust code quality enforcer.

This module provides enforcement of Rust coding standards,
focusing on AI-generated code antipatterns.
"""

from pathlib import Path

from ..core.base_enforcer import BaseEnforcer
from ..core.violation import Violation
from ..services.rust_auto_fixer import RustAutoFixer
from ..standards.rust_patterns import RustPatterns


class RustEnforcer(BaseEnforcer):
    """Rust code quality enforcer using modular architecture."""

    def __init__(self) -> None:
        """Initialize Rust enforcer with patterns and auto-fixer."""
        super().__init__("rust")
        self.patterns = RustPatterns()
        self.auto_fixer = RustAutoFixer()

    def is_supported_file(self, file_path: Path) -> bool:
        """Check if file is Rust (.rs).

        Args:
            file_path: Path to file to check

        Returns:
            True if file extension is .rs
        """
        return file_path.suffix == ".rs"

    def apply_automatic_fixes(self, file_path: Path) -> list[str]:
        """Apply automatic fixes via cargo fmt integration.

        Args:
            file_path: Path to file to fix

        Returns:
            List of strings describing fixes applied
        """
        return self.auto_fixer.apply_fixes(file_path)

    def analyze_file(self, file_path: Path) -> list[Violation]:
        """Analyze Rust file using Clippy and pattern detection.

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

        # Run Clippy for linting violations
        violations.extend(self.patterns.run_clippy(file_path))

        # Check for banned crates
        violations.extend(self.patterns.check_banned_crates(content, file_path))

        # Check for .unwrap() abuse
        violations.extend(self.patterns.check_unwrap_usage(lines, file_path))

        return violations
