"""Python-specific pattern definitions and analysis logic for claudex-guard."""

import ast
import re
from pathlib import Path
from typing import Dict, List, Tuple

from ..core.violation import Violation


class PythonPatterns:
    """Python-specific pattern definitions and analysis logic."""

    def __init__(self):
        """Initialize Python pattern definitions."""

        # Banned imports from claudex standards
        self.BANNED_IMPORTS = {
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
        self.REQUIRED_PATTERNS = {
            "f_strings": r'f["\'].*{.*}.*["\']',
            "pathlib_usage": r"from pathlib import Path|Path\(",
            "type_hints": r"def \w+\([^)]*\) -> ",
            "context_managers": r"with open\(",
        }

        # Anti-patterns that violate coding standards
        self.ANTIPATTERNS = [
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
            (
                r"\.format\(",
                "Use f-strings instead of .format() (faster, more readable)",
            ),
            (r"%.*%", "Use f-strings instead of % formatting (modern Python)"),
            # Path handling
            (
                r"os\.path\.join",
                "Use pathlib instead of os.path (object-oriented, cross-platform)",
            ),
            # Closure gotchas
            (
                r"lambda\s+[^:]*:\s*\w+",
                "Late binding closure in loop (potential gotcha)",
            ),
            # Security violations
            (
                r"\beval\s*\(",
                "Never use eval() - consider ast.literal_eval() for safe evaluation",
            ),
            (
                r"\bexec\s*\(",
                "Never use exec() - refactor to avoid dynamic code execution",
            ),
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

    def get_banned_imports(self) -> Dict[str, str]:
        """Get dictionary of banned imports and their replacements."""
        return self.BANNED_IMPORTS

    def get_required_patterns(self) -> Dict[str, str]:
        """Get dictionary of required patterns and their regex definitions."""
        return self.REQUIRED_PATTERNS

    def get_antipatterns(self) -> List[Tuple[str, str]]:
        """Get list of antipatterns as (regex, message) tuples."""
        return self.ANTIPATTERNS

    def analyze_ast(self, tree: ast.AST, file_path: Path) -> List[Violation]:
        """AST-based analysis for sophisticated pattern detection."""
        violations = []

        class PhilosophyVisitor(ast.NodeVisitor):
            def __init__(self, patterns: "PythonPatterns"):
                self.patterns = patterns
                self.file_path = file_path
                self.violations = violations

            def visit_FunctionDef(self, node) -> None:
                # Check for type hints on functions (Rudy's requirement)
                if not node.returns and not node.name.startswith("_"):
                    self.violations.append(
                        Violation(
                            str(self.file_path),
                            node.lineno,
                            "missing_type_hints",
                            f"Function '{node.name}' missing return type hint",
                            "Add -> return_type annotation (type hints required everywhere)",
                            "error",
                            ast_node=node,
                            function_name=node.name,
                        )
                    )

                # Check for mutable defaults (more sophisticated than regex)
                for arg in node.args.defaults:
                    if isinstance(arg, (ast.List, ast.Dict, ast.Set)):
                        self.violations.append(
                            Violation(
                                str(self.file_path),
                                node.lineno,
                                "mutable_default",
                                f"Mutable default argument in function '{node.name}'",
                                "Use None default, check inside function (classic Python gotcha)",
                                "error",
                                ast_node=node,
                                function_name=node.name,
                            )
                        )

                self.generic_visit(node)

            def visit_Import(self, node) -> None:
                # Sophisticated import analysis
                for alias in node.names:
                    self._check_banned_import(alias.name, node.lineno)
                self.generic_visit(node)

            def visit_ImportFrom(self, node) -> None:
                if node.module:
                    self._check_banned_import(node.module, node.lineno)
                self.generic_visit(node)

            def _check_banned_import(self, import_name: str, line_num: int):
                for banned, suggestion in self.patterns.BANNED_IMPORTS.items():
                    if import_name == banned or import_name.startswith(banned + "."):
                        self.violations.append(
                            Violation(
                                str(self.file_path),
                                line_num,
                                "banned_import",
                                f"Banned import: {import_name}",
                                suggestion,
                                "error",
                                language_context={
                                    "import_name": import_name,
                                    "banned_module": banned,
                                },
                            )
                        )

        visitor = PhilosophyVisitor(self)
        visitor.visit(tree)
        return violations

    def analyze_patterns(
        self, lines: List[str], file_path: Path, reporter=None
    ) -> List[Violation]:
        """Pattern-based analysis for specific standards."""
        violations = []
        has_print_usage = False

        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # Check anti-patterns
            for pattern, message in self.ANTIPATTERNS:
                if re.search(pattern, line):
                    # Special handling for print detection - use global reminder
                    if pattern == r"print\s*\(":
                        has_print_usage = True
                        continue  # Don't add as individual violation

                    violations.append(
                        Violation(
                            str(file_path),
                            line_num,
                            "antipattern",
                            message,
                            "",
                            "error",
                            language_context={"pattern": pattern, "line": line.strip()},
                        )
                    )

        # Add global reminder for print usage once per tool run
        if has_print_usage and reporter:
            reporter.add_global_reminder(
                "💡 Consider logging for production code or rich.print() for enhanced output"
            )

        return violations

    def analyze_imports(self, content: str, file_path: Path) -> List[Violation]:
        """Import analysis for banned libraries and missing preferred imports."""
        violations = []

        # Check if file uses file operations but doesn't import pathlib
        if (
            "open(" in content or "file" in content.lower()
        ) and "pathlib" not in content:
            violations.append(
                Violation(
                    str(file_path),
                    1,
                    "missing_pathlib",
                    "File operations detected but pathlib not imported",
                    "Use 'from pathlib import Path' (preferred approach)",
                    "warning",
                    language_context={"missing_import": "pathlib"},
                )
            )

        # Check for string formatting without f-strings
        if re.search(r'["\'].*%[sd].*["\']', content) and 'f"' not in content:
            violations.append(
                Violation(
                    str(file_path),
                    1,
                    "old_formatting",
                    "Old-style string formatting detected",
                    "Use f-strings for formatting (fastest, most readable)",
                    "warning",
                    language_context={"formatting_style": "old_percent"},
                )
            )

        return violations

    def analyze_development_patterns(
        self, content: str, lines: List[str], file_path: Path
    ) -> List[Violation]:
        """Enforce development workflow patterns."""
        violations = []

        # Check for proper error handling patterns
        if "except Exception" in content and "log" not in content.lower():
            violations.append(
                Violation(
                    str(file_path),
                    1,
                    "error_handling",
                    "Exception handling without logging detected",
                    "Include context in log messages (debugging standards)",
                    "warning",
                    language_context={"pattern": "exception_without_logging"},
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
            violations.append(
                Violation(
                    str(file_path),
                    1,
                    "composition_violation",
                    "Heavy inheritance usage detected",
                    "Prefer composition over inheritance (design philosophy)",
                    "warning",
                    language_context={
                        "class_count": class_count,
                        "inheritance_count": inheritance_count,
                    },
                )
            )

        return violations
