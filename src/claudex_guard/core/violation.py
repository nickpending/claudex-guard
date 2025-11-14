"""Core violation data structures for claudex-guard."""

import ast
from pathlib import Path
from typing import Any, Optional


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
        language_context: Optional[dict[str, Any]] = None,
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
        self.project_root: Optional[Path] = None
        self.violations: list[Violation] = []
        self.fixes_applied: list[str] = []
        self.context_message: Optional[str] = None
        self.global_reminders: set[str] = set()
        self.memory = None  # Will be initialized when first violation is added
        self.hook_mode = False  # True when running as Claude Code hook

    def set_project_root(self, project_root: Optional[Path]) -> None:
        """Set the project root for memory system."""
        self.project_root = project_root

    def set_hook_mode(self, enabled: bool = True) -> None:
        """Enable hook mode for JSON output format."""
        self.hook_mode = enabled

    def add_violation(self, violation: Violation) -> None:
        """Add a violation to the report and log to memory."""
        self.violations.append(violation)

        # Initialize memory on first violation with proper project root
        if self.memory is None:
            from .violation_memory import ViolationMemory

            # Pass project root if available for proper project hash
            self.memory = ViolationMemory(self.project_root)

        # Log violation to memory system (don't break main workflow if this fails)
        try:
            if self.memory:
                self.memory.log_violation(violation, self.language)
        except Exception as e:
            # Log the error but don't break violation reporting
            import sys

            print(f"Warning: Violation memory logging failed: {e}", file=sys.stderr)

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
        import json
        import sys

        # Hook mode: always output JSON format
        if self.hook_mode:
            if self.violations and self.has_errors():
                # Build detailed violation message
                error_violations = [v for v in self.violations if v.severity == "error"]
                violation_details = []

                for v in error_violations:
                    detail = f"• {Path(v.file_path).name}:{v.line_num} - {v.message}"
                    if v.fix_suggestion:
                        detail += f"\n  Fix: {v.fix_suggestion}"
                    violation_details.append(detail)

                reason = (
                    f"Quality violations found ({len(error_violations)} errors):\n"
                    + "\n".join(violation_details)
                )

                decision = {"decision": "block", "reason": reason}
                print(json.dumps(decision), file=sys.stderr)
                return 2  # Block operation
            else:
                # Success in hook mode - output JSON approve decision
                if self.fixes_applied:
                    reason = "Quality checks passed with auto-fixes:\n" + "\n".join(
                        f"• {fix}" for fix in self.fixes_applied
                    )
                else:
                    reason = "Quality checks passed - no issues found"

                decision = {"decision": "approve", "reason": reason}
                print(json.dumps(decision))
                return 0  # Success

        # Non-hook mode: only report errors via JSON, success via human-readable
        if self.violations and self.has_errors():
            # Claude Code decision control - block Claude from proceeding
            # Build detailed violation message for Claude
            error_violations = [v for v in self.violations if v.severity == "error"]
            violation_details = []

            for v in error_violations:
                detail = f"• {Path(v.file_path).name}:{v.line_num} - {v.message}"
                if v.fix_suggestion:
                    detail += f"\n  Fix: {v.fix_suggestion}"
                violation_details.append(detail)

            # Include all details in the reason field for Claude
            reason = (
                f"Quality violations found ({len(error_violations)} errors):\n"
                + "\n".join(violation_details)
            )

            decision = {"decision": "block", "reason": reason}
            print(
                json.dumps(decision), file=sys.stderr
            )  # stderr for Claude decision control

            return 2  # Block operation

        # Success - output applied fixes for model visibility (stdout - model sees this)
        if self.fixes_applied:
            print("✓ Quality checks passed:")
            for fix in self.fixes_applied:
                print(f"  • {fix}")

        return 0  # Success
