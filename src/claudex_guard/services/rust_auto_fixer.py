"""Automatic fixing for Rust files.

This module provides automatic fixes via cargo fmt integration.
"""

import subprocess
from pathlib import Path


class RustAutoFixer:
    """Fixes Rust issues that don't require human decisions."""

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

        if not file_path.exists() or file_path.suffix != ".rs":
            return []

        # Apply cargo fmt formatting (safe, mechanical)
        self._run_cargo_fmt(file_path)

        return self.fixes_applied

    def _run_cargo_fmt(self, file_path: Path) -> bool:
        """Run cargo fmt to format Rust code.

        Args:
            file_path: Path to file to format

        Returns:
            True if formatting was applied successfully
        """
        try:
            result = subprocess.run(
                ["rustfmt", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                self.fixes_applied.append("Applied rustfmt formatting")
                return True
        except subprocess.TimeoutExpired:
            self.fixes_applied.append("rustfmt timed out (skipped)")
        except FileNotFoundError:
            # rustfmt not installed - fail with clear error per user decision
            self.fixes_applied.append(
                "rustfmt not found. Install Rust toolchain: https://rustup.rs"
            )

        return False
