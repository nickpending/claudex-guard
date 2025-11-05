"""Automatic fixing for TypeScript/JavaScript files.

This module provides automatic fixes via ESLint and Prettier integration.
"""

import subprocess
from pathlib import Path


class TypeScriptAutoFixer:
    """Fixes TypeScript/JavaScript issues that don't require human decisions."""

    def __init__(self) -> None:
        """Initialize the auto-fixer."""
        self.fixes_applied: list[str] = []

    def apply_fixes(self, file_path: Path) -> list[str]:
        """Apply safe automatic fixes and return list of changes made.

        Args:
            file_path: Path to file to fix

        Returns:
            List of strings describing fixes applied
        """
        self.fixes_applied = []

        if not file_path.exists() or file_path.suffix not in {
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
        }:
            return []

        # Apply ESLint fixes first (safe linting fixes)
        self._run_eslint_fix(file_path)

        # Apply Prettier formatting (cosmetic, safe)
        self._run_prettier(file_path)

        return self.fixes_applied

    def _run_eslint_fix(self, file_path: Path) -> bool:
        """Run ESLint with --fix to apply safe automatic fixes.

        Args:
            file_path: Path to file to fix

        Returns:
            True if fixes were applied successfully
        """
        try:
            result = subprocess.run(
                ["npx", "eslint", "--fix", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # ESLint returns 0 if no violations, 1 if violations found
            # --fix modifies file in place, so check if it ran successfully
            if result.returncode in {0, 1}:
                self.fixes_applied.append("Applied ESLint automatic fixes")
                return True
        except subprocess.TimeoutExpired:
            self.fixes_applied.append("ESLint fix timed out (skipped)")
        except FileNotFoundError:
            # ESLint not installed - fail with clear error per user decision
            self.fixes_applied.append(
                "ESLint not found. Install with: npm install -g eslint"
            )

        return False

    def _run_prettier(self, file_path: Path) -> bool:
        """Run Prettier to format code.

        Args:
            file_path: Path to file to format

        Returns:
            True if formatting was applied successfully
        """
        try:
            result = subprocess.run(
                ["npx", "prettier", "--write", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                self.fixes_applied.append("Applied Prettier formatting")
                return True
        except subprocess.TimeoutExpired:
            self.fixes_applied.append("Prettier formatting timed out (skipped)")
        except FileNotFoundError:
            # Prettier not installed - skip gracefully (formatting is optional)
            self.fixes_applied.append("Prettier not found (formatting skipped)")

        return False
