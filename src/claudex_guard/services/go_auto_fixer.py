"""Automatic fixing for Go files.

This module provides automatic fixes via gofmt integration.
"""

import subprocess
from pathlib import Path


class GoAutoFixer:
    """Fixes Go issues that don't require human decisions."""

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

        if not file_path.exists() or file_path.suffix != ".go":
            return []

        # Apply gofmt formatting (safe, mechanical)
        self._run_gofmt(file_path)

        return self.fixes_applied

    def _run_gofmt(self, file_path: Path) -> bool:
        """Run gofmt to format Go code.

        Args:
            file_path: Path to file to format

        Returns:
            True if formatting was applied successfully
        """
        try:
            result = subprocess.run(
                ["gofmt", "-w", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                self.fixes_applied.append("Applied gofmt formatting")
                return True
        except subprocess.TimeoutExpired:
            self.fixes_applied.append("gofmt timed out (skipped)")
        except FileNotFoundError:
            # gofmt not installed - fail with clear error per user decision
            self.fixes_applied.append(
                "gofmt not found. Install Go toolchain: https://go.dev/doc/install"
            )

        return False
