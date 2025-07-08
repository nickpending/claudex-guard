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

        # Banned imports from claudex standards (2025 modern stack)
        self.BANNED_IMPORTS = {
            # HTTP Libraries
            "requests": "Use httpx (async-first, HTTP/2 support)",
            "urllib": "Use httpx (modern, cleaner API)",
            # Package Management
            "pip": "Use uv (10-100x faster, handles everything)",
            "pip-tools": "Use uv (comprehensive package management)",
            "poetry": "Use uv (faster, simpler package management)",
            "pipenv": "Use uv (eliminates environment conflicts)",
            "conda": "Use uv (unified Python management)",
            # Environment Management
            "virtualenv": "Use uv (automatic environment management)",
            "venv": "Use uv (automatic environment management)",
            "pyenv": "Use uv (Python version management)",
            # Build Tools
            "setuptools": "Use pyproject.toml with uv",
            "distutils": "Use pyproject.toml with uv (deprecated in Python 3.12+)",
            # Testing Frameworks
            "nose": "Use pytest (better fixtures, cleaner syntax)",
            "nose2": "Use pytest (better fixtures, cleaner syntax)",
            "unittest": "Use pytest (better fixtures, cleaner syntax)",
            # Code Quality Tools (replaced by ruff)
            "pylint": "Use ruff (10x faster, includes formatting)",
            "flake8": "Use ruff (faster, more comprehensive)",
            "black": "Use ruff (includes formatting)",
            "isort": "Use ruff (includes import sorting)",
            "autopep8": "Use ruff (faster, more comprehensive)",
            "yapf": "Use ruff (faster, more comprehensive)",
            # Documentation
            "sphinx": "Use mkdocs (cleaner for most projects)",
            # Data Processing
            "pandas": "Use polars (10x faster for large datasets)",
            # File/Path Operations
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
            # NOTE: String formatting detection moved to AST analysis for accuracy
            # - % formatting: visit_BinOp()
            # - .format(): visit_Call()
            # NOTE: Path handling moved to AST analysis (visit_Attribute) for accuracy
            # Closure gotchas
            (
                r"lambda\s+[^:]*:\s*\w+",
                "Late binding closure in loop (potential gotcha)",
            ),
            # NOTE: Security violations moved to AST analysis (visit_Call) for accuracy
            # Environment management violations (moved to shell context)
            # NOTE: Shell command patterns belong in bash-guard, not Python code analysis
            # NOTE: python/pytest command patterns moved to bash-guard (shell context, not Python code)
            # Threading gotchas
            (
                r"import\s+threading",
                "Threading only helps with I/O - use multiprocessing for CPU tasks",
            ),
            # NOTE: Debug patterns moved to AST analysis (visit_Call) for accuracy
            # NOTE: Type hints moved to AST analysis (visit_Attribute) for accuracy
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

                # Check for missing docstrings on public functions
                if not ast.get_docstring(node) and not node.name.startswith("_"):
                    self.violations.append(
                        Violation(
                            str(self.file_path),
                            node.lineno,
                            "missing_docstring",
                            f"Function '{node.name}' missing docstring",
                            "Add Google-style docstring with Args, Returns, Raises",
                            "warning",
                            ast_node=node,
                            language_context={
                                "pattern": "missing_function_docstring",
                                "function_name": node.name,
                                "is_public": not node.name.startswith("_"),
                            },
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

            def visit_ClassDef(self, node) -> None:
                """Detect opportunities for modern Python features and documentation."""
                # Check for missing class docstring
                if not ast.get_docstring(node) and not node.name.startswith("_"):
                    self.violations.append(
                        Violation(
                            str(self.file_path),
                            node.lineno,
                            "missing_docstring",
                            f"Class '{node.name}' missing docstring",
                            "Add class docstring explaining purpose and usage",
                            "warning",
                            ast_node=node,
                            language_context={
                                "pattern": "missing_class_docstring",
                                "class_name": node.name,
                                "is_public": not node.name.startswith("_"),
                            },
                        )
                    )

                # Check for manual __init__ methods that could use dataclasses
                init_method = None
                has_simple_attributes = False

                for item in node.body:
                    if (
                        isinstance(item, ast.FunctionDef)
                        and item.name == "__init__"
                        and len(item.args.args) > 1
                    ):  # Has self + parameters
                        init_method = item

                        # Check if it's just simple attribute assignment
                        if all(
                            isinstance(stmt, ast.Assign)
                            and len(stmt.targets) == 1
                            and isinstance(stmt.targets[0], ast.Attribute)
                            and isinstance(stmt.targets[0].value, ast.Name)
                            and stmt.targets[0].value.id == "self"
                            for stmt in item.body
                        ):
                            has_simple_attributes = True

                # Suggest dataclass for simple attribute-only classes
                if (
                    init_method
                    and has_simple_attributes
                    and len(init_method.args.args) >= 3
                ):
                    self.violations.append(
                        Violation(
                            str(self.file_path),
                            node.lineno,
                            "dataclass_opportunity",
                            f"Class '{node.name}' could use @dataclass decorator",
                            "Use @dataclass for simple attribute classes (Python 3.7+)",
                            "warning",
                            ast_node=node,
                            language_context={
                                "pattern": "manual_init_class",
                                "class_name": node.name,
                                "param_count": len(init_method.args.args) - 1,
                            },
                        )
                    )

                # Check for string constants that could be Enums
                string_constants = []
                for item in node.body:
                    if (
                        isinstance(item, ast.Assign)
                        and len(item.targets) == 1
                        and isinstance(item.targets[0], ast.Name)
                        and isinstance(item.value, ast.Constant)
                        and isinstance(item.value.value, str)
                    ):
                        string_constants.append(item.targets[0].id)

                if len(string_constants) >= 3:  # Multiple string constants
                    self.violations.append(
                        Violation(
                            str(self.file_path),
                            node.lineno,
                            "enum_opportunity",
                            f"Class '{node.name}' with {len(string_constants)} string constants could use Enum",
                            "Use enum.Enum for related constants (Python 3.4+)",
                            "warning",
                            ast_node=node,
                            language_context={
                                "pattern": "string_constants_class",
                                "class_name": node.name,
                                "constant_count": len(string_constants),
                            },
                        )
                    )

                self.generic_visit(node)

            def visit_If(self, node) -> None:
                """Detect opportunities for match/case statements."""
                # Check for long if/elif chains that could use match/case
                elif_count = 0
                current = node

                while hasattr(current, "orelse") and current.orelse:
                    if len(current.orelse) == 1 and isinstance(
                        current.orelse[0], ast.If
                    ):
                        elif_count += 1
                        current = current.orelse[0]
                    else:
                        break

                # Suggest match/case for 4+ elif chains
                if elif_count >= 3:
                    self.violations.append(
                        Violation(
                            str(self.file_path),
                            node.lineno,
                            "match_case_opportunity",
                            f"Long if/elif chain ({elif_count + 1} conditions) could use match/case",
                            "Use match/case for complex conditionals (Python 3.10+)",
                            "warning",
                            ast_node=node,
                            language_context={
                                "pattern": "long_if_elif_chain",
                                "condition_count": elif_count + 1,
                            },
                        )
                    )

                self.generic_visit(node)

            def visit_Module(self, node) -> None:
                """Check for module-level documentation standards."""
                # Check for module docstring
                module_docstring = ast.get_docstring(node)
                if not module_docstring:
                    self.violations.append(
                        Violation(
                            str(self.file_path),
                            1,
                            "missing_module_docstring",
                            "Module missing docstring",
                            "Add module docstring explaining purpose and functionality",
                            "warning",
                            ast_node=node,
                            language_context={
                                "pattern": "missing_module_docstring",
                                "file_type": "module",
                            },
                        )
                    )
                elif len(module_docstring.strip()) < 20:
                    self.violations.append(
                        Violation(
                            str(self.file_path),
                            1,
                            "inadequate_module_docstring",
                            "Module docstring too brief (less than 20 characters)",
                            "Expand docstring to explain module purpose and functionality",
                            "warning",
                            ast_node=node,
                            language_context={
                                "pattern": "brief_module_docstring",
                                "docstring_length": len(module_docstring.strip()),
                            },
                        )
                    )

                self.generic_visit(node)

            def visit_ImportFrom(self, node) -> None:
                """Check banned imports and old typing imports."""
                if node.module:
                    self._check_banned_import(node.module, node.lineno)

                    # Check for old typing imports (from typing import List, Dict, etc.)
                    if node.module == "typing":
                        builtin_replacements = {
                            "List": "list",
                            "Dict": "dict",
                            "Set": "set",
                            "Tuple": "tuple",
                            "FrozenSet": "frozenset",
                            "Deque": "collections.deque",
                            "DefaultDict": "collections.defaultdict",
                            "OrderedDict": "collections.OrderedDict",
                            "Counter": "collections.Counter",
                            "ChainMap": "collections.ChainMap",
                        }

                        union_replacements = {
                            "Union": "Use | union syntax (Python 3.10+)",
                            "Optional": "Use | None syntax (Python 3.10+)",
                        }

                        for alias in node.names:
                            if alias.name in builtin_replacements:
                                replacement = builtin_replacements[alias.name]
                                self.violations.append(
                                    Violation(
                                        str(self.file_path),
                                        node.lineno,
                                        "old_type_hints",
                                        "Use modern type hints in Python 3.9+",
                                        f"Replace typing.{alias.name} with {replacement}",
                                        "warning",
                                        ast_node=node,
                                        language_context={
                                            "pattern": "old_typing_import",
                                            "old_type": f"typing.{alias.name}",
                                            "new_type": replacement,
                                        },
                                    )
                                )
                            elif alias.name in union_replacements:
                                suggestion = union_replacements[alias.name]
                                self.violations.append(
                                    Violation(
                                        str(self.file_path),
                                        node.lineno,
                                        "old_type_hints",
                                        "Use modern type hints in Python 3.10+",
                                        suggestion,
                                        "warning",
                                        ast_node=node,
                                        language_context={
                                            "pattern": "old_typing_import",
                                            "old_type": f"typing.{alias.name}",
                                            "new_type": suggestion,
                                        },
                                    )
                                )

                self.generic_visit(node)

            def visit_BinOp(self, node) -> None:
                """Detect string % formatting and potential SQL injection."""
                # Check if this is a % operation on a string constant
                if (
                    isinstance(node.op, ast.Mod)
                    and isinstance(node.left, ast.Constant)
                    and isinstance(node.left.value, str)
                    and "%" in node.left.value
                ):
                    # Check for SQL injection in % formatting
                    sql_keywords = [
                        "SELECT",
                        "INSERT",
                        "UPDATE",
                        "DELETE",
                        "FROM",
                        "WHERE",
                        "JOIN",
                    ]
                    if any(
                        keyword in node.left.value.upper() for keyword in sql_keywords
                    ):
                        self.violations.append(
                            Violation(
                                str(self.file_path),
                                node.lineno,
                                "security_violation",
                                "Potential SQL injection in % formatting - use parameterized queries",
                                "Use cursor.execute(query, params) with placeholders instead of % formatting",
                                "error",
                                ast_node=node,
                                language_context={
                                    "pattern": "sql_injection_percent",
                                    "format_string": node.left.value[:100],
                                },
                            )
                        )
                    else:
                        # Regular % formatting violation
                        self.violations.append(
                            Violation(
                                str(self.file_path),
                                node.lineno,
                                "old_string_formatting",
                                "Use f-strings instead of % formatting (modern Python)",
                                'Replace with f-string: f"text {variable}"',
                                "error",
                                ast_node=node,
                                language_context={
                                    "pattern": "string_percent_formatting",
                                    "format_string": node.left.value[:50] + "..."
                                    if len(node.left.value) > 50
                                    else node.left.value,
                                },
                            )
                        )

                self.generic_visit(node)

            def visit_Call(self, node) -> None:
                """Detect security violations and formatting patterns (AST-based)."""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id

                    # Security violations - critical accuracy needed
                    if func_name == "eval":
                        self.violations.append(
                            Violation(
                                str(self.file_path),
                                node.lineno,
                                "security_violation",
                                "Never use eval() - consider ast.literal_eval() for safe evaluation",
                                "Replace with ast.literal_eval() or refactor logic",
                                "error",
                                ast_node=node,
                                language_context={
                                    "pattern": "eval_usage",
                                    "function": "eval",
                                },
                            )
                        )
                    elif func_name == "exec":
                        self.violations.append(
                            Violation(
                                str(self.file_path),
                                node.lineno,
                                "security_violation",
                                "Never use exec() - refactor to avoid dynamic code execution",
                                "Refactor to use explicit logic instead of dynamic execution",
                                "error",
                                ast_node=node,
                                language_context={
                                    "pattern": "exec_usage",
                                    "function": "exec",
                                },
                            )
                        )
                    elif func_name == "compile" and len(node.args) >= 2:
                        # Check if compile() is being used to execute code
                        self.violations.append(
                            Violation(
                                str(self.file_path),
                                node.lineno,
                                "security_violation",
                                "compile() with exec/eval can be dangerous - validate input carefully",
                                "Use ast.parse() for safe code analysis or validate input thoroughly",
                                "warning",
                                ast_node=node,
                                language_context={
                                    "pattern": "compile_usage",
                                    "function": "compile",
                                },
                            )
                        )

                # Check for pickle module usage (security risk)
                elif (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "pickle"
                    and node.func.attr in ("loads", "load", "dumps", "dump")
                ):
                    self.violations.append(
                        Violation(
                            str(self.file_path),
                            node.lineno,
                            "security_violation",
                            f"pickle.{node.func.attr}() can execute arbitrary code - use json/msgpack instead",
                            "Use json.loads() for simple data or msgpack for binary serialization",
                            "error",
                            ast_node=node,
                            language_context={
                                "pattern": "pickle_usage",
                                "method": f"pickle.{node.func.attr}",
                            },
                        )
                    )

                # Check for subprocess with shell=True
                elif (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "subprocess"
                ):
                    # Check for shell=True in keyword arguments
                    for keyword in node.keywords:
                        if (
                            keyword.arg == "shell"
                            and isinstance(keyword.value, ast.Constant)
                            and keyword.value.value is True
                        ):
                            self.violations.append(
                                Violation(
                                    str(self.file_path),
                                    node.lineno,
                                    "security_violation",
                                    "subprocess with shell=True can enable shell injection attacks",
                                    "Use shell=False and pass arguments as list to prevent injection",
                                    "error",
                                    ast_node=node,
                                    language_context={
                                        "pattern": "subprocess_shell_injection",
                                        "method": f"subprocess.{node.func.attr}",
                                    },
                                )
                            )

                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name == "print":
                        self.violations.append(
                            Violation(
                                str(self.file_path),
                                node.lineno,
                                "debug_pattern",
                                "Use rich.print() or icecream.ic() for better debugging output",
                                "Import rich: from rich import print",
                                "warning",
                                ast_node=node,
                                language_context={
                                    "pattern": "print_usage",
                                    "function": "print",
                                },
                            )
                        )

                # Check for .format() method calls and SQL injection
                elif (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "format"
                    and isinstance(node.func.value, ast.Constant)
                    and isinstance(node.func.value.value, str)
                ):
                    # Check for SQL injection in .format()
                    sql_keywords = [
                        "SELECT",
                        "INSERT",
                        "UPDATE",
                        "DELETE",
                        "FROM",
                        "WHERE",
                        "JOIN",
                    ]
                    if any(
                        keyword in node.func.value.value.upper()
                        for keyword in sql_keywords
                    ):
                        self.violations.append(
                            Violation(
                                str(self.file_path),
                                node.lineno,
                                "security_violation",
                                "Potential SQL injection in .format() - use parameterized queries",
                                "Use cursor.execute(query, params) with placeholders instead of .format()",
                                "error",
                                ast_node=node,
                                language_context={
                                    "pattern": "sql_injection_format",
                                    "format_string": node.func.value.value[:100],
                                },
                            )
                        )
                    else:
                        # Regular .format() violation
                        self.violations.append(
                            Violation(
                                str(self.file_path),
                                node.lineno,
                                "old_string_formatting",
                                "Use f-strings instead of .format() (faster, more readable)",
                                'Replace with f-string: f"text {variable}"',
                                "error",
                                ast_node=node,
                                language_context={
                                    "pattern": "format_method",
                                    "format_string": node.func.value.value[:50] + "..."
                                    if len(node.func.value.value) > 50
                                    else node.func.value.value,
                                },
                            )
                        )

                # Check for path traversal vulnerabilities in os.path calls
                elif (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Attribute)
                    and isinstance(node.func.value.value, ast.Name)
                    and node.func.value.value.id == "os"
                    and node.func.value.attr == "path"
                ):
                    # Check if arguments contain user input (variables, calls, subscripts)
                    has_user_input = any(
                        isinstance(arg, (ast.Name, ast.Call, ast.Subscript))
                        for arg in node.args
                    )

                    if has_user_input:
                        self.violations.append(
                            Violation(
                                str(self.file_path),
                                node.lineno,
                                "security_violation",
                                "Potential path traversal - validate and sanitize file paths",
                                "Use pathlib.Path.resolve() and validate against allowed directories",
                                "error",
                                ast_node=node,
                                language_context={
                                    "pattern": "path_traversal_risk",
                                    "method": f"os.path.{node.func.attr}",
                                },
                            )
                        )

                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node) -> None:
                """Handle async function definitions with same rules as regular functions."""
                # Reuse FunctionDef logic for async functions
                self.visit_FunctionDef(node)

            def visit_JoinedStr(self, node) -> None:
                """Detect potential SQL injection in f-strings."""
                # Check for SQL keywords in f-string content
                sql_keywords = [
                    "SELECT",
                    "INSERT",
                    "UPDATE",
                    "DELETE",
                    "FROM",
                    "WHERE",
                    "JOIN",
                ]

                # Get the f-string content
                f_string_parts = []
                for value in node.values:
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        f_string_parts.append(value.value.upper())

                f_string_content = " ".join(f_string_parts)

                # Check if this looks like SQL with user input
                # Must have SQL keywords AND look like actual query structure
                looks_like_sql = any(
                    keyword in f_string_content for keyword in sql_keywords
                )
                has_variables = len(node.values) > 1

                # More specific SQL pattern detection - must look like actual SQL
                sql_patterns = [
                    "SELECT * FROM",
                    "INSERT INTO",
                    "UPDATE SET",
                    "DELETE FROM",
                    "WHERE",
                    "VALUES",
                ]
                looks_like_actual_sql = any(
                    pattern in f_string_content for pattern in sql_patterns
                )

                if looks_like_sql and has_variables and looks_like_actual_sql:
                    # Has both SQL keywords and variables (potential injection)
                    self.violations.append(
                        Violation(
                            str(self.file_path),
                            node.lineno,
                            "security_violation",
                            "Potential SQL injection in f-string - use parameterized queries",
                            "Use cursor.execute(query, params) with placeholders instead of f-strings",
                            "error",
                            ast_node=node,
                            language_context={
                                "pattern": "sql_injection_fstring",
                                "sql_content": f_string_content[:100],
                            },
                        )
                    )

                self.generic_visit(node)

            def visit_Compare(self, node) -> None:
                """Detect identity comparison gotchas."""
                # Check for 'is' comparison with non-singleton values
                for i, op in enumerate(node.ops):
                    if isinstance(op, ast.Is) or isinstance(op, ast.IsNot):
                        # Get the right operand for this comparison
                        right = node.comparators[i]

                        # Check for dangerous 'is' comparisons
                        if isinstance(right, ast.Constant) and isinstance(
                            right.value, (int, float, str)
                        ):
                            if isinstance(right.value, int) and not (
                                -5 <= right.value <= 256
                            ):
                                # Large integers are not cached
                                self.violations.append(
                                    Violation(
                                        str(self.file_path),
                                        node.lineno,
                                        "identity_comparison_gotcha",
                                        f"Use == instead of 'is' for integer {right.value} (not cached)",
                                        "Use == for value comparison, 'is' only for None/True/False",
                                        "error",
                                        ast_node=node,
                                        language_context={
                                            "pattern": "integer_identity_comparison",
                                            "value": right.value,
                                        },
                                    )
                                )
                            elif isinstance(
                                right.value, (float, str)
                            ) and right.value not in (True, False, None):
                                # Floats and non-empty strings should use ==
                                value_type = (
                                    "float"
                                    if isinstance(right.value, float)
                                    else "string"
                                )
                                self.violations.append(
                                    Violation(
                                        str(self.file_path),
                                        node.lineno,
                                        "identity_comparison_gotcha",
                                        f"Use == instead of 'is' for {value_type} comparison",
                                        "Use == for value comparison, 'is' only for None/True/False",
                                        "error",
                                        ast_node=node,
                                        language_context={
                                            "pattern": f"{value_type}_identity_comparison",
                                            "value": str(right.value)[:50],
                                        },
                                    )
                                )

                self.generic_visit(node)

            def visit_Import(self, node) -> None:
                """Detect problematic import patterns."""
                # Check for threading imports in CPU-bound contexts
                for alias in node.names:
                    if alias.name == "threading":
                        self.violations.append(
                            Violation(
                                str(self.file_path),
                                node.lineno,
                                "gil_confusion",
                                "Threading only helps with I/O - use multiprocessing for CPU tasks",
                                "Use multiprocessing for CPU-bound work, asyncio for I/O-bound",
                                "warning",
                                ast_node=node,
                                language_context={
                                    "pattern": "threading_import",
                                    "import_name": alias.name,
                                },
                            )
                        )

                    # Check for direct local directory imports (Python 2 behavior)
                    if "." in alias.name and not alias.name.startswith("."):
                        # This could be importing from current directory
                        self.violations.append(
                            Violation(
                                str(self.file_path),
                                node.lineno,
                                "local_directory_import",
                                f"Avoid importing from current directory: {alias.name}",
                                "Use -m flag or src/ layout to avoid import path issues",
                                "warning",
                                ast_node=node,
                                language_context={
                                    "pattern": "local_import",
                                    "import_name": alias.name,
                                },
                            )
                        )

                # Call existing import analysis
                for alias in node.names:
                    self._check_banned_import(alias.name, node.lineno)
                self.generic_visit(node)

            def visit_Attribute(self, node) -> None:
                """Detect old-style imports and path handling patterns."""
                # Check for old typing module usage (Python 3.9+ has built-in generics)
                if isinstance(node.value, ast.Name) and node.value.id == "typing":
                    # Python 3.9+ built-in replacements
                    builtin_replacements = {
                        "List": "list",
                        "Dict": "dict",
                        "Set": "set",
                        "Tuple": "tuple",
                        "FrozenSet": "frozenset",
                        "Deque": "collections.deque",
                        "DefaultDict": "collections.defaultdict",
                        "OrderedDict": "collections.OrderedDict",
                        "Counter": "collections.Counter",
                        "ChainMap": "collections.ChainMap",
                    }

                    # Python 3.10+ union syntax
                    union_replacements = {
                        "Union": "Use | union syntax (Python 3.10+)",
                        "Optional": "Use | None syntax (Python 3.10+)",
                    }

                    # Contextlib replacements
                    contextlib_replacements = {
                        "ContextManager": "Use contextlib.AbstractContextManager",
                        "AsyncContextManager": "Use contextlib.AbstractAsyncContextManager",
                    }

                    replacement = None
                    suggestion = None

                    if node.attr in builtin_replacements:
                        replacement = builtin_replacements[node.attr]
                        suggestion = f"Replace typing.{node.attr} with {replacement}"
                    elif node.attr in union_replacements:
                        replacement = union_replacements[node.attr]
                        suggestion = replacement
                    elif node.attr in contextlib_replacements:
                        replacement = contextlib_replacements[node.attr]
                        suggestion = f"Replace typing.{node.attr} with {replacement}"

                    if replacement and suggestion:
                        self.violations.append(
                            Violation(
                                str(self.file_path),
                                node.lineno,
                                "old_type_hints",
                                "Use modern type hints in Python 3.9+",
                                suggestion,
                                "warning",
                                ast_node=node,
                                language_context={
                                    "pattern": "old_typing",
                                    "old_type": f"typing.{node.attr}",
                                    "new_type": replacement,
                                },
                            )
                        )

                # Check for os.path usage
                elif (
                    isinstance(node.value, ast.Attribute)
                    and isinstance(node.value.value, ast.Name)
                    and node.value.value.id == "os"
                    and node.value.attr == "path"
                ):
                    self.violations.append(
                        Violation(
                            str(self.file_path),
                            node.lineno,
                            "path_handling",
                            "Use pathlib instead of os.path (object-oriented, cross-platform)",
                            "Import pathlib: from pathlib import Path",
                            "warning",
                            ast_node=node,
                            language_context={
                                "pattern": "os_path_usage",
                                "method": node.attr,
                            },
                        )
                    )

                # Check for os.environ usage without defaults
                elif (
                    isinstance(node.value, ast.Name)
                    and node.value.id == "os"
                    and node.attr == "environ"
                ):
                    # This flags direct os.environ access - should suggest os.getenv()
                    self.violations.append(
                        Violation(
                            str(self.file_path),
                            node.lineno,
                            "environment_variable_handling",
                            "Use os.getenv() with defaults instead of direct os.environ access",
                            "Replace with: os.getenv('VAR_NAME', 'default_value')",
                            "warning",
                            ast_node=node,
                            language_context={
                                "pattern": "os_environ_direct_access",
                                "suggestion": "os.getenv() with default values",
                            },
                        )
                    )

                self.generic_visit(node)

            def _check_banned_import(self, import_name: str, line_num: int):
                # Context-aware import checking
                is_test_file = "test" in str(self.file_path)

                # Special cases first
                if import_name == "urllib.parse":
                    # urllib.parse is OK for URL parsing - don't flag it
                    return
                elif import_name == "unittest" and is_test_file:
                    suggestion = "Use pytest fixtures and pytest-mock (unittest.mock is OK in tests)"
                elif import_name == "unittest.mock" and is_test_file:
                    # unittest.mock is explicitly OK in test files per standards
                    return
                else:
                    # Check standard banned imports
                    suggestion = None
                    banned_match = None

                    for (
                        banned,
                        default_suggestion,
                    ) in self.patterns.BANNED_IMPORTS.items():
                        if import_name == banned or import_name.startswith(
                            banned + "."
                        ):
                            suggestion = default_suggestion
                            banned_match = banned
                            break

                    if not suggestion:
                        return  # Not a banned import

                # Add violation with context-aware message
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
                            "banned_module": banned_match or import_name,
                            "is_test_file": is_test_file,
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

        # Check if this is a test file
        is_test_file = (
            "test_" in file_path.name
            or file_path.name.endswith("_test.py")
            or "tests/" in str(file_path)
        )

        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # Test file standards
            if is_test_file:
                # Check test function naming conventions
                if line_stripped.startswith("def "):
                    func_match = re.match(r"def\s+(\w+)\s*\(", line)
                    if func_match:
                        func_name = func_match.group(1)
                        # Public function that doesn't start with test_
                        if not func_name.startswith("_") and not func_name.startswith(
                            "test_"
                        ):
                            violations.append(
                                Violation(
                                    str(file_path),
                                    line_num,
                                    "test_naming_convention",
                                    f"Test function '{func_name}' should start with 'test_'",
                                    "Use descriptive test names: test_should_do_something_when_condition()",
                                    "warning",
                                    language_context={
                                        "pattern": "test_function_naming",
                                        "function_name": func_name,
                                    },
                                )
                            )

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
