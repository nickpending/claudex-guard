"""Python automatic quality fixer for claudex-guard."""

import subprocess
from pathlib import Path


class PythonAutoFixer:
    """Automatically fixes issues that don't require human decision-making."""

    def __init__(self) -> None:
        """Initialize the auto-fixer."""
        self.fixes_applied: list[str] = []

    def apply_fixes(self, file_path: Path) -> list[str]:
        """Apply safe automatic fixes and return list of changes made."""
        self.fixes_applied = []

        if not file_path.exists() or file_path.suffix != ".py":
            return []

        # Apply ruff formatting (safe, mechanical)
        self._run_ruff_format(file_path)

        # Apply ruff linting with safe fixes
        self._run_ruff_check_fix(file_path)

        # Run mypy for type checking (report only, don't fix)
        type_issues = self._run_mypy_check(file_path)
        if type_issues:
            self.fixes_applied.append(
                f"Type issues found: {len(type_issues)} (review needed)"
            )

        return self.fixes_applied

    def _run_ruff_format(self, file_path: Path) -> bool:
        """Format code with ruff (preferred formatter)."""
        try:
            result = subprocess.run(
                ["ruff", "format", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                self.fixes_applied.append("Applied ruff formatting")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return False

    def _run_ruff_check_fix(self, file_path: Path) -> bool:
        """Run ruff linting with automatic fixes (strict enforcement mode)."""
        try:
            # Strict enforcement - no development mode compromises
            result = subprocess.run(
                [
                    "ruff",
                    "check",
                    "--fix",
                    str(file_path),
                    # Security, bugs, upgrades, errors, imports
                    "--select=S,B,UP,E,F,W,I",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.fixes_applied.append(
                    "Applied strict security enforcement + automatic fixes"
                )
                return True
            elif result.stderr:
                self.fixes_applied.append(
                    f"Ruff issues remain: {result.stderr.strip()}"
                )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return False

    def _run_mypy_check(self, file_path: Path) -> list[str]:
        """Check types with mypy (preferred type checker)."""
        try:
            result = subprocess.run(
                ["mypy", str(file_path)], capture_output=True, text=True, timeout=30
            )
            if result.stdout:
                return result.stdout.strip().split("\n")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return []
