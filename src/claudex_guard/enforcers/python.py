#!/usr/bin/env python3
"""
Python Quality Enforcer

Enforces sophisticated Python standards from CLAUDE.local.md automatically via hooks.
Goes way beyond basic linting - validates development philosophy and workflow patterns.

Usage: python python-quality-enforcer.py <file1> <file2> ...
Called automatically by Claude Code PostToolUse hooks on Python file changes.

This is the system that eliminates /complete-task entirely.
"""

import ast
import sys
from pathlib import Path

# Import modular components for PythonEnforcer
from ..core.base_enforcer import BaseEnforcer
from ..core.utils import is_text_file
from ..core.violation import Violation
from ..services.auto_fixer import PythonAutoFixer
from ..standards.python_patterns import PythonPatterns


def main() -> int:
    """Main entry point for Python quality enforcement."""
    enforcer = PythonEnforcer()
    exit_code = enforcer.run()
    sys.stdout.flush()  # Ensure JSON decision control is output before exit
    return exit_code


class PythonEnforcer(BaseEnforcer):
    """Python-specific code quality enforcer using modular architecture."""

    def __init__(self):
        super().__init__("python")
        self.patterns = PythonPatterns()
        self.auto_fixer = PythonAutoFixer()

    def is_supported_file(self, file_path: Path) -> bool:
        """Check if file is Python (.py extension)."""
        return file_path.suffix == ".py"

    def apply_automatic_fixes(self, file_path: Path) -> list[str]:
        """Apply automatic fixes via ruff/mypy integration."""
        return self.auto_fixer.apply_fixes(file_path)

    def _is_test_file(self, file_path: Path) -> bool:
        """Check if file is a test file."""
        file_str = str(file_path).lower()
        file_name = file_path.name.lower()

        # Check file name patterns
        if file_name.startswith("test_") or file_name.endswith("_test.py"):
            return True

        # Check if in test directory
        if "/tests/" in file_str or "/test/" in file_str:
            return True

        return False

    def _run_ruff_analysis(self, file_path: Path) -> list[Violation]:
        """Run ruff check for security and quality violations."""
        import json
        import subprocess

        violations = []
        is_test_file = self._is_test_file(file_path)

        try:
            # Use --extend-select to layer security rules on top of project config
            # This respects per-file-ignores (e.g., S101 in test files)
            result = subprocess.run(
                [
                    "ruff",
                    "check",
                    str(file_path),
                    "--extend-select=S,B,UP",  # Security, bugs, upgrades
                    "--output-format=json",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.stdout:
                ruff_violations = json.loads(result.stdout)
                for rv in ruff_violations:
                    # Skip syntax errors - let other tools handle them
                    if "SyntaxError" in rv.get("message", ""):
                        continue

                    code = rv.get("code", "")
                    message = rv.get("message", "Ruff violation")
                    fix_suggestion = (
                        rv.get("fix", {}).get("message", "") if rv.get("fix") else ""
                    )

                    # Enhanced error message for test file violations
                    if is_test_file and code in ["S101", "S603", "S607"]:
                        fix_suggestion = self._get_test_file_config_suggestion(code)

                    violations.append(
                        Violation(
                            str(file_path),
                            rv.get("location", {}).get("row", 0),
                            code,
                            message,
                            fix_suggestion,
                            "error",
                        )
                    )
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass  # Ruff not available or failed - graceful degradation

        return violations

    def _get_test_file_config_suggestion(self, code: str) -> str:
        """Generate helpful config suggestion for test file violations."""
        rule_descriptions = {
            "S101": "assert usage (legitimate in pytest tests)",
            "S603": "subprocess without shell=True check (safe in tests)",
            "S607": "subprocess call with string path (acceptable in tests)",
        }

        description = rule_descriptions.get(code, "rule")

        return f"""Test files need per-file-ignores in pyproject.toml.

Add this to your pyproject.toml:

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "S603", "S607"]
"test_*.py" = ["S101", "S603", "S607"]
"**/test_*.py" = ["S101", "S603", "S607"]

This excludes {code} ({description}) from test files while maintaining
security checks in production code.
"""

    def analyze_file(self, file_path: Path) -> list[Violation]:
        """Analyze Python file using AST and pattern detection."""
        violations = []

        # Check file size to prevent memory exhaustion (also validates file exists)
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
        try:
            file_size = file_path.stat().st_size
            if file_size > MAX_FILE_SIZE:
                violations.append(
                    Violation(
                        str(file_path),
                        0,
                        "file_too_large",
                        (
                            f"File too large: {file_size:,} bytes "
                            f"(limit: {MAX_FILE_SIZE:,} bytes)"
                        ),
                        "Split large files or increase MAX_FILE_SIZE limit if needed",
                        "error",
                    )
                )
                return violations
        except OSError as e:
            violations.append(
                Violation(
                    str(file_path),
                    0,
                    "file_stat_error",
                    f"Cannot get file size: {e}",
                    "Check file permissions and existence",
                    "error",
                )
            )
            return violations

        # Check if file is actually a text file
        if not is_text_file(file_path):
            violations.append(
                Violation(
                    str(file_path),
                    0,
                    "binary_file_error",
                    f"File appears to be binary: {file_path}",
                    "Ensure file is a text file, not binary",
                    "error",
                )
            )
            return violations

        try:
            # Read file with proper error handling
            try:
                content = file_path.read_text(encoding="utf-8")
            except FileNotFoundError:
                violations.append(
                    Violation(
                        str(file_path),
                        0,
                        "file_access_error",
                        f"File not found: {file_path}",
                        "Ensure file exists and path is correct",
                        "error",
                    )
                )
                return violations
            except PermissionError:
                violations.append(
                    Violation(
                        str(file_path),
                        0,
                        "file_access_error",
                        f"Permission denied: {file_path}",
                        "Check file permissions",
                        "error",
                    )
                )
                return violations
            except UnicodeDecodeError as e:
                violations.append(
                    Violation(
                        str(file_path),
                        0,
                        "encoding_error",
                        f"File encoding error: {e}",
                        "Ensure file is UTF-8 encoded or specify correct encoding",
                        "error",
                    )
                )
                return violations
            except OSError as e:
                violations.append(
                    Violation(
                        str(file_path),
                        0,
                        "io_error",
                        f"File I/O error: {e}",
                        "Check file system and network connectivity",
                        "error",
                    )
                )
                return violations

            # Handle empty files
            if not content.strip():
                return []  # No violations for empty files

            lines = content.splitlines()

            # AST analysis (using PythonPatterns)
            try:
                tree = ast.parse(content)
                violations.extend(self.patterns.analyze_ast(tree, file_path))
            except SyntaxError:
                pass  # Let other tools handle syntax errors

            # Pattern analysis (using PythonPatterns)
            violations.extend(
                self.patterns.analyze_patterns(lines, file_path, self.reporter)
            )

            # Import analysis (using PythonPatterns)
            violations.extend(self.patterns.analyze_imports(content, file_path))

            # Development pattern analysis (using PythonPatterns)
            violations.extend(
                self.patterns.analyze_development_patterns(content, lines, file_path)
            )

            # Ruff security and quality checks (S, B, UP rules)
            violations.extend(self._run_ruff_analysis(file_path))

        except Exception as e:
            # Don't break workflow on analysis failure
            violations.append(
                Violation(
                    str(file_path),
                    0,
                    "analysis_error",
                    f"Quality analysis failed: {e}",
                    severity="warning",
                )
            )

        return violations


if __name__ == "__main__":
    sys.exit(main())
