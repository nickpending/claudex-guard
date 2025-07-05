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
from typing import List

# Import modular components for PythonEnforcer
from ..core.base_enforcer import BaseEnforcer
from ..core.violation import Violation
from ..standards.python_patterns import PythonPatterns
from .python_auto_fixer import PythonAutoFixer


def main() -> int:
    """Main entry point for Python quality enforcement."""
    enforcer = PythonEnforcer()
    exit_code = enforcer.run()
    sys.exit(exit_code)


class PythonEnforcer(BaseEnforcer):
    """Python-specific code quality enforcer using modular architecture."""

    def __init__(self):
        super().__init__("python")
        self.patterns = PythonPatterns()
        self.auto_fixer = PythonAutoFixer()

    def is_supported_file(self, file_path: Path) -> bool:
        """Check if file is Python (.py extension)."""
        return file_path.suffix == ".py"

    def apply_automatic_fixes(self, file_path: Path) -> List[str]:
        """Apply automatic fixes via ruff/mypy integration."""
        return self.auto_fixer.apply_fixes(file_path)

    def analyze_file(self, file_path: Path) -> List[Violation]:
        """Analyze Python file using AST and pattern detection."""
        violations = []

        try:
            content = file_path.read_text(encoding="utf-8")
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
    main()
