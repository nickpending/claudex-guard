#!/usr/bin/env python3
"""
Python Quality Enforcer

Enforces sophisticated Python standards from CLAUDE.local.md automatically via hooks.
Goes way beyond basic linting - validates development philosophy and workflow patterns.

Usage: python python-quality-enforcer.py <file1> <file2> ...
Called automatically by Claude Code PostToolUse hooks on Python file changes.

This is the system that eliminates /complete-task entirely.
"""

import sys
import subprocess
import ast
import re
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json


class PythonQualityViolation:
    """Represents a quality standard violation with context and fix suggestions."""

    def __init__(
        self,
        file_path: str,
        line_num: int,
        violation_type: str,
        message: str,
        fix_suggestion: str = "",
        severity: str = "error",
    ):
        self.file_path = file_path
        self.line_num = line_num
        self.violation_type = violation_type
        self.message = message
        self.fix_suggestion = fix_suggestion
        self.severity = severity

    def __str__(self):
        fix_part = f"\n  💡 Fix: {self.fix_suggestion}" if self.fix_suggestion else ""
        filename = Path(self.file_path).name
        return f"📍 {filename}:{self.line_num} - {self.message}{fix_part}"


class PythonPhilosophyEnforcer:
    """
    Enforces Rudy's Python development philosophy and standards.

    This goes beyond syntax - validates approach, patterns, and workflow integration.
    """

    # Banned imports from claudex standards
    BANNED_IMPORTS = {
        "requests": "Use httpx (async-first, HTTP/2 support)",
        "urllib": "Use httpx (modern, cleaner API)",
        "pip": "Use uv (10-100x faster, handles everything)",
        "virtualenv": "Use uv (automatic environment management)",
        "venv": "Use uv (automatic environment management)",
        "setuptools": "Use pyproject.toml with uv",
        "nose": "Use pytest (better fixtures, cleaner syntax)",
        "unittest": "Use pytest (better fixtures, cleaner syntax)",
        "os.path": "Use pathlib (object-oriented, cross-platform)",
    }

    # Required patterns
    REQUIRED_PATTERNS = {
        "f_strings": r'f["\'].*{.*}.*["\']',
        "pathlib_usage": r"from pathlib import Path|Path\(",
        "type_hints": r"def \w+\([^)]*\) -> ",
        "context_managers": r"with open\(",
    }

    # Anti-patterns that violate coding standards
    ANTIPATTERNS = [
        # Classic Python gotchas
        (
            r"def\s+\w+\([^)]*=\s*\[\]",
            "Mutable default argument (classic Python gotcha)",
        ),
        (
            r"def\s+\w+\([^)]*=\s*\{\}",
            "Mutable default argument (classic Python gotcha)",
        ),
        # Error handling violations
        (r"except\s*:", "Bare except clause (violates error handling standards)"),
        # String formatting preferences
        (r"\.format\(", "Use f-strings instead of .format() (faster, more readable)"),
        (r"%.*%", "Use f-strings instead of % formatting (modern Python)"),
        # Path handling
        (
            r"os\.path\.join",
            "Use pathlib instead of os.path (object-oriented, cross-platform)",
        ),
        # Closure gotchas
        (r"lambda\s+[^:]*:\s*\w+", "Late binding closure in loop (potential gotcha)"),
        # Security violations
        (
            r"\beval\s*\(",
            "Never use eval() - consider ast.literal_eval() for safe evaluation",
        ),
        (r"\bexec\s*\(", "Never use exec() - refactor to avoid dynamic code execution"),
        # Environment management violations
        (
            r"\bpip\s+install",
            "Use 'uv add package' instead of pip install (10-100x faster)",
        ),
        (r"python\s+", "Use 'uv run python' instead of bare python command"),
        (r"pytest\s", "Use 'uv run pytest' instead of bare pytest command"),
        # Threading gotchas
        (
            r"import\s+threading",
            "Threading only helps with I/O - use multiprocessing for CPU tasks",
        ),
        # Debug patterns
        (
            r"print\s*\(",
            "Use rich.print() or icecream.ic() for better debugging output",
        ),
        # Old-style type hints
        (
            r"typing\.(List|Dict|Set|Tuple)",
            "Use built-in types (list, dict, set, tuple) in Python 3.9+",
        ),
    ]

    def __init__(self):
        self.violations: List[PythonQualityViolation] = []

    def analyze_file(self, file_path: Path) -> List[PythonQualityViolation]:
        """
        Comprehensive analysis of Python file against coding standards.

        Returns violations that need Claude's attention for philosophical compliance.
        """
        self.violations = []

        if not file_path.exists() or file_path.suffix != ".py":
            return self.violations

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            # Parse AST for sophisticated analysis
            try:
                tree = ast.parse(content)
                self._analyze_ast(tree, file_path)
            except SyntaxError:
                # File has syntax errors - let normal tools handle this
                pass

            # Line-by-line pattern analysis
            self._analyze_patterns(lines, file_path)

            # Import analysis
            self._analyze_imports(content, file_path)

            # Rudy's specific philosophy enforcement
            self._analyze_development_patterns(content, lines, file_path)

        except Exception as e:
            # Don't break the workflow if analysis fails
            self.violations.append(
                PythonQualityViolation(
                    str(file_path),
                    0,
                    "analysis_error",
                    f"Quality analysis failed: {e}",
                    severity="warning",
                )
            )

        return self.violations

    def _analyze_ast(self, tree: ast.AST, file_path: Path):
        """AST-based analysis for sophisticated pattern detection."""

        class PhilosophyVisitor(ast.NodeVisitor):
            def __init__(self, enforcer):
                self.enforcer = enforcer
                self.file_path = file_path

            def visit_FunctionDef(self, node):
                # Check for type hints on functions (Rudy's requirement)
                if not node.returns and not node.name.startswith("_"):
                    self.enforcer.violations.append(
                        PythonQualityViolation(
                            str(self.file_path),
                            node.lineno,
                            "missing_type_hints",
                            f"Function '{node.name}' missing return type hint",
                            "Add -> return_type annotation (type hints required everywhere)",
                            "error",
                        )
                    )

                # Check for mutable defaults (more sophisticated than regex)
                for arg in node.args.defaults:
                    if isinstance(arg, (ast.List, ast.Dict, ast.Set)):
                        self.enforcer.violations.append(
                            PythonQualityViolation(
                                str(self.file_path),
                                node.lineno,
                                "mutable_default",
                                f"Mutable default argument in function '{node.name}'",
                                "Use None default, check inside function (classic Python gotcha)",
                                "error",
                            )
                        )

                self.generic_visit(node)

            def visit_Import(self, node):
                # Sophisticated import analysis
                for alias in node.names:
                    self._check_banned_import(alias.name, node.lineno)
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                if node.module:
                    self._check_banned_import(node.module, node.lineno)
                self.generic_visit(node)

            def _check_banned_import(self, import_name: str, line_num: int):
                for banned, suggestion in self.enforcer.BANNED_IMPORTS.items():
                    if banned in import_name:
                        self.enforcer.violations.append(
                            PythonQualityViolation(
                                str(self.file_path),
                                line_num,
                                "banned_import",
                                f"Banned import: {import_name}",
                                suggestion,
                                "error",
                            )
                        )

        visitor = PhilosophyVisitor(self)
        visitor.visit(tree)

    def _analyze_patterns(self, lines: List[str], file_path: Path):
        """Pattern-based analysis for Rudy's specific standards."""

        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # Check anti-patterns
            for pattern, message in self.ANTIPATTERNS:
                if re.search(pattern, line):
                    self.violations.append(
                        PythonQualityViolation(
                            str(file_path),
                            line_num,
                            "antipattern",
                            message,
                            "",
                            "error",
                        )
                    )

    def _analyze_imports(self, content: str, file_path: Path):
        """Import analysis for banned libraries and missing preferred imports."""

        # Check if file uses file operations but doesn't import pathlib
        if (
            "open(" in content or "file" in content.lower()
        ) and "pathlib" not in content:
            self.violations.append(
                PythonQualityViolation(
                    str(file_path),
                    1,
                    "missing_pathlib",
                    "File operations detected but pathlib not imported",
                    "Use 'from pathlib import Path' (preferred approach)",
                    "warning",
                )
            )

        # Check for string formatting without f-strings
        if re.search(r'["\'].*%[sd].*["\']', content) and 'f"' not in content:
            self.violations.append(
                PythonQualityViolation(
                    str(file_path),
                    1,
                    "old_formatting",
                    "Old-style string formatting detected",
                    "Use f-strings for formatting (fastest, most readable)",
                    "warning",
                )
            )

    def _analyze_development_patterns(
        self, content: str, lines: List[str], file_path: Path
    ):
        """Enforce development workflow patterns."""

        # Check for proper error handling patterns
        if "except Exception" in content and "log" not in content.lower():
            self.violations.append(
                PythonQualityViolation(
                    str(file_path),
                    1,
                    "error_handling",
                    "Exception handling without logging detected",
                    "Include context in log messages (debugging standards)",
                    "warning",
                )
            )

        # Check for composition principles in class design
        class_count = len([line for line in lines if line.strip().startswith("class ")])
        inheritance_count = len(
            [
                line
                for line in lines
                if " inheritance " in line.lower() or "super()" in line
            ]
        )

        if class_count > 0 and inheritance_count > class_count * 0.5:
            self.violations.append(
                PythonQualityViolation(
                    str(file_path),
                    1,
                    "composition_violation",
                    "Heavy inheritance usage detected",
                    "Prefer composition over inheritance (design philosophy)",
                    "warning",
                )
            )


class AutomaticQualityFixer:
    """
    Automatically fixes issues that don't require human decision-making.

    Only touches mechanical issues - leaves architectural decisions to humans.
    """

    def __init__(self):
        self.fixes_applied = []

    def apply_automatic_fixes(self, file_path: Path) -> List[str]:
        """Apply safe automatic fixes and return list of changes made."""

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
        """Run ruff linting with automatic fixes."""
        try:
            result = subprocess.run(
                ["ruff", "check", "--fix", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                self.fixes_applied.append("Applied ruff linting fixes")
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


class WorkflowContextAwareness:
    """
    Understands Rudy's development workflow context for intelligent enforcement.

    This is what makes our system better than generic linters.
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.project_root = self._find_project_root()
        self.is_development_project = self._is_development_project()
        self.iteration_context = self._get_iteration_context()

    def _find_project_root(self) -> Optional[Path]:
        """Find project root by looking for development workflow markers."""
        current = self.file_path.parent
        while current != current.parent:
            if (current / ".claude").exists() or (current / "CLAUDE.md").exists():
                return current
            current = current.parent
        return None

    def _is_development_project(self) -> bool:
        """Check if this is a systematic development project."""
        if not self.project_root:
            return False

        return (
            (self.project_root / ".claude" / "artifacts").exists()
            or (self.project_root / "IDEA.md").exists()
            or (self.project_root / "CLAUDE.md").exists()
        )

    def _get_iteration_context(self) -> Dict[str, Any]:
        """Get current iteration context for workflow-aware enforcement."""
        context = {
            "has_active_iteration": False,
            "task_list_exists": False,
            "features_in_progress": [],
        }

        if not self.project_root:
            return context

        # Check for active iteration
        artifacts_dir = self.project_root / ".claude" / "artifacts"
        if artifacts_dir.exists():
            context["has_active_iteration"] = (artifacts_dir / "TASK_LIST.md").exists()
            context["task_list_exists"] = (artifacts_dir / "TASK_LIST.md").exists()

        return context

    def should_enforce_strict_quality(self) -> bool:
        """Determine if strict quality enforcement should apply."""
        return (
            self.is_development_project
            and self.iteration_context["has_active_iteration"]
        )

    def get_context_message(self) -> str:
        """Get context message for Claude about current workflow state."""
        if not self.is_development_project:
            return "Regular Python file - applying basic quality standards"

        if self.iteration_context["has_active_iteration"]:
            return (
                "Development project with active iteration - strict quality enforcement"
            )

        return "Development project - standard quality enforcement"


def main():
    """
    Main entry point for Python quality enforcement.

    This is the hook that eliminates /complete-task entirely.
    """
    try:
        # Read hook context from stdin (Claude passes tool context this way)
        stdin_data = sys.stdin.read()

        if stdin_data.strip():
            hook_data = json.loads(stdin_data)

            # Try tool_input path first (that's where Claude puts it)
            tool_input = hook_data.get("tool_input", {})
            file_path = Path(tool_input.get("file_path", ""))
            if not file_path.exists() or str(file_path) == ".":
                # Fallback to top-level file_path
                file_path = Path(hook_data.get("file_path", ""))
        else:
            # No stdin data, try environment variables
            claude_file_paths = os.environ.get("CLAUDE_FILE_PATHS", "")
            if claude_file_paths:
                file_path = Path(claude_file_paths.split()[0])
            else:
                # Fallback to command line args
                if len(sys.argv) < 2:
                    sys.exit(0)
                file_path = Path(sys.argv[1])

        if not file_path.exists():
            sys.exit(0)

    except Exception:
        sys.exit(1)

    all_violations = []
    all_fixes = []
    has_errors = False

    # Process the file
    if file_path.exists() and file_path.suffix == ".py":
        # Get workflow context for intelligent enforcement
        context = WorkflowContextAwareness(file_path)

        # Apply automatic fixes first
        fixer = AutomaticQualityFixer()
        fixes = fixer.apply_automatic_fixes(file_path)
        all_fixes.extend(fixes)

        # Analyze against Rudy's philosophy and standards
        enforcer = PythonPhilosophyEnforcer()
        violations = enforcer.analyze_file(file_path)

        # Filter violations based on context
        if context.should_enforce_strict_quality():
            # Strict enforcement during active development
            filtered_violations = violations
        else:
            # Relaxed enforcement for non-development files
            filtered_violations = [v for v in violations if v.severity == "error"]

        all_violations.extend(filtered_violations)

        # Count errors vs warnings
        errors = [v for v in filtered_violations if v.severity == "error"]
        if errors:
            has_errors = True

    # Report results to Claude
    if all_fixes:
        print("\n✅ Automatic fixes applied:", file=sys.stderr)
        for fix in all_fixes:
            print(f"  • {fix}", file=sys.stderr)

    if all_violations:
        print("🚨 Quality violations found:", file=sys.stderr)
        for violation in all_violations:
            print(f"  {violation}", file=sys.stderr)

        context_msg = context.get_context_message() if "context" in locals() else ""
        if context_msg:
            print(f"\n📋 Context: {context_msg}", file=sys.stderr)

        print(
            "\n💡 This enforces Python standards from claudex",
            file=sys.stderr,
        )
        print("📚 See claudex-python.md for complete Python standards", file=sys.stderr)
        print(
            "🔗 Built with claudex: https://github.com/nickpending/claudex",
            file=sys.stderr,
        )

        if has_errors:
            print("\n❌ Blocking due to quality standard violations", file=sys.stderr)
            sys.exit(2)  # Block operation, provide feedback to Claude

    if all_fixes and not all_violations:
        print(
            "✅ All quality standards met - proceeding with development",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
