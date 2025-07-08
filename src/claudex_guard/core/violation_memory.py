"""Violation memory system for tracking and learning from code quality patterns."""

from datetime import datetime
from pathlib import Path
from typing import Set

from .violation import Violation


class ViolationMemory:
    """Tracks violations and generates memory for LLM context injection."""

    def __init__(self, project_root: Path):
        self.memory_dir = project_root / ".claudex-guard"
        self.memory_dir.mkdir(exist_ok=True)

        self.log_file = self.memory_dir / "violations.log"
        self.memory_file = self.memory_dir / "memory.md"

    def log_violation(self, violation: Violation) -> None:
        """Log violation with full context for metrics and memory.

        Note: This implementation is not concurrent-safe. Multiple Claude Code
        sessions writing simultaneously may corrupt log entries. Consider file
        locking if concurrent usage becomes common.
        """
        timestamp = datetime.now().isoformat()
        filename = Path(violation.file_path).name
        line = violation.line_num
        vtype = violation.violation_type

        # Extract context (function name or pattern)
        context = ""
        if hasattr(violation, "function_name") and violation.function_name:
            context = violation.function_name
        elif violation.language_context:
            context = violation.language_context.get("pattern", "")

        fix = violation.fix_suggestion or ""

        # Sanitize data to prevent log parsing issues
        def escape_pipes(s: str) -> str:
            """Escape pipe characters to prevent log parsing corruption."""
            return (
                s.replace("|", "\\|").replace("\n", "\\n").replace("\r", "\\r")
                if s
                else ""
            )

        # Append to detailed log for metrics with sanitized data
        entry = f"{timestamp}|{escape_pipes(filename)}|{line}|{escape_pipes(vtype)}|{escape_pipes(context)}|{escape_pipes(fix)}\n"
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(entry)

        # Update memory file for LLM injection
        self.update_memory_file()

    def update_memory_file(self) -> None:
        """Process log into deduplicated memory for LLM injection."""
        seen_fixes: Set[str] = set()
        fixes = []

        if self.log_file.exists():
            with self.log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("|")
                    if len(parts) >= 6:
                        fix = parts[5]  # fix_suggestion
                        if fix and fix not in seen_fixes:
                            seen_fixes.add(fix)
                            fixes.append(f"- {fix}")

        # Write memory file for LLM context injection
        with self.memory_file.open("w", encoding="utf-8") as f:
            f.write("# MEMORY:\n\n")
            if fixes:
                f.write("\n".join(fixes))
                f.write("\n")
            else:
                f.write("No violations logged yet.\n")

    def get_memory_content(self) -> str:
        """Get current memory content for injection."""
        if self.memory_file.exists():
            return self.memory_file.read_text(encoding="utf-8")
        return "# MEMORY:\n\nNo violations logged yet.\n"

    def clear_memory(self) -> None:
        """Clear all violation memory (for testing or reset)."""
        if self.log_file.exists():
            self.log_file.unlink()
        if self.memory_file.exists():
            self.memory_file.unlink()
