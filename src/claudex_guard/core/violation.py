"""Core violation data structures for claudex-guard."""

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional


class Violation:
    """Represents a code quality violation with context and fix suggestions."""

    def __init__(
        self,
        file_path: str,
        line_num: int,
        violation_type: str,
        message: str,
        fix_suggestion: str = "",
        severity: str = "error",
        # Language-specific optional fields
        ast_node: Optional[ast.AST] = None,
        function_name: Optional[str] = None,
        language_context: Optional[Dict[str, Any]] = None,
    ):
        self.file_path = file_path
        self.line_num = line_num
        self.violation_type = violation_type
        self.message = message
        self.fix_suggestion = fix_suggestion
        self.severity = severity
        # Language-specific context
        self.ast_node = ast_node
        self.function_name = function_name
        self.language_context = language_context or {}

    def __str__(self) -> str:
        """Format violation for display to AI assistant."""
        fix_part = f"\n  💡 Fix: {self.fix_suggestion}" if self.fix_suggestion else ""
        filename = Path(self.file_path).name
        return f"📍 {filename}:{self.line_num} - {self.message}{fix_part}"

    @classmethod
    def from_ast_node(
        cls,
        file_path: str,
        ast_node: ast.AST,
        violation_type: str,
        message: str,
        fix_suggestion: str = "",
        severity: str = "error",
    ) -> "Violation":
        """Create a violation from an AST node with automatic context extraction."""
        return cls(
            file_path=file_path,
            line_num=ast_node.lineno,
            violation_type=violation_type,
            message=message,
            fix_suggestion=fix_suggestion,
            severity=severity,
            ast_node=ast_node,
            function_name=getattr(ast_node, "name", None),
        )


class ViolationReporter:
    """Handles formatting and reporting violations to AI assistants."""

    def __init__(self, language: str):
        self.language = language
        self.violations: List[Violation] = []
        self.fixes_applied: List[str] = []
        self.context_message: Optional[str] = None
        self.global_reminders: set[str] = set()

    def add_violation(self, violation: Violation) -> None:
        """Add a violation to the report."""
        self.violations.append(violation)

    def add_fix(self, fix_description: str) -> None:
        """Add an applied fix to the report."""
        self.fixes_applied.append(fix_description)

    def set_context_message(self, message: str) -> None:
        """Set dynamic context message for reporting."""
        self.context_message = message

    def add_global_reminder(self, reminder: str) -> None:
        """Add a global reminder to be shown once per tool run."""
        self.global_reminders.add(reminder)

    def has_errors(self) -> bool:
        """Check if any violations are errors (vs warnings)."""
        return any(v.severity == "error" for v in self.violations)

    def report(self) -> int:
        """Report violations via JSON decision control for Claude. Returns exit code."""
        import sys

        # Only report errors via JSON decision control
        if self.violations and self.has_errors():
            # Claude Code decision control - block Claude from proceeding
            import json
            from pathlib import Path
            
            # Build detailed violation message for Claude
            error_violations = [v for v in self.violations if v.severity == "error"]
            violation_details = []
            
            for v in error_violations:
                detail = f"• {Path(v.file_path).name}:{v.line_num} - {v.message}"
                if v.fix_suggestion:
                    detail += f"\n  Fix: {v.fix_suggestion}"
                violation_details.append(detail)
            
            # Include all details in the reason field for Claude
            reason = f"Quality violations found ({len(error_violations)} errors):\n" + "\n".join(violation_details)
            
            decision = {
                "decision": "block",
                "reason": reason
            }
            print(json.dumps(decision))  # stdout for Claude decision control
            
            return 2  # Block operation

        return 0  # Success
