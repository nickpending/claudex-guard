"""Python automatic quality fixer for claudex-guard."""

import subprocess
from pathlib import Path
from typing import List


class PythonAutoFixer:
    """Automatically fixes issues that don't require human decision-making."""

    def __init__(self):
        """Initialize the auto-fixer."""
        self.fixes_applied: List[str] = []

    def apply_fixes(self, file_path: Path) -> List[str]:
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
        """Run ruff linting with automatic fixes (development mode - preserve imports)."""
        try:
            # During development, skip import-related fixes to avoid LLM timing conflicts
            # Full import cleanup happens later during /complete-task
            result = subprocess.run(
                [
                    "ruff",
                    "check",
                    "--fix",
                    str(file_path),
                    "--ignore=F401",  # Don't remove unused imports (LLM still working)
                    "--ignore=I001",  # Don't sort imports (LLM still adding them)
                    "--ignore=I002",  # Don't enforce import conventions yet
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.fixes_applied.append(
                    "Applied development auto-fixes (imports preserved)"
                )
                return True
            elif result.stderr:
                self.fixes_applied.append(
                    f"Ruff issues remain: {result.stderr.strip()}"
                )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return False

    def _run_mypy_check(self, file_path: Path) -> List[str]:
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
