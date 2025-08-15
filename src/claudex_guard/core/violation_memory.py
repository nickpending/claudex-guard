"""Violation memory system for tracking and learning from code quality patterns."""

from datetime import datetime
from pathlib import Path
from typing import Set, Optional

from .violation import Violation
from .violation_db import ViolationDB
from .project_cache import ProjectRootCache


class ViolationMemory:
    """Tracks violations using SQLite for efficient querying and pattern analysis."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize with SQLite database and project cache.
        
        Args:
            project_root: Optional project root for backward compatibility
        """
        # New centralized storage
        self.db = ViolationDB()
        self.cache = ProjectRootCache()
        
        # Get project hash from cache or generate from root
        if project_root:
            self.project_hash = self.cache._get_project_hash(project_root)
        else:
            self.project_hash = "unknown"
        
        # Keep legacy paths for migration
        if project_root:
            self.memory_dir = project_root / ".claudex-guard"
            self.log_file = self.memory_dir / "violations.log"
            self.memory_file = self.memory_dir / "memory.md"
            self._migrate_legacy_data()
        else:
            self.memory_dir = None
            self.log_file = None
            self.memory_file = None

    def log_violation(self, violation: Violation, language: str = "python") -> None:
        """Log violation to SQLite database.
        
        Args:
            violation: Violation to log
            language: Programming language of the file
        """
        # Log to new SQLite database
        self.db.log_violation(violation, self.project_hash, language)
        
        # No longer update markdown file - it's generated on demand

    def _migrate_legacy_data(self) -> None:
        """Migrate legacy markdown/log files to SQLite if they exist."""
        if not self.log_file or not self.log_file.exists():
            return
        
        try:
            # Read old log file and migrate to SQLite
            with self.log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("|")
                    if len(parts) >= 6:
                        # Create a minimal violation object for migration
                        violation = Violation(
                            file_path=parts[1].replace("\\|", "|"),
                            line_num=int(parts[2]) if parts[2].isdigit() else 0,
                            violation_type=parts[3].replace("\\|", "|"),
                            message=parts[3].replace("\\|", "|"),  # Use type as message
                            fix_suggestion=parts[5].replace("\\|", "|").replace("\\n", "\n"),
                            severity="error"
                        )
                        self.db.log_violation(violation, self.project_hash)
            
            # Rename old files to indicate migration
            self.log_file.rename(self.log_file.with_suffix(".migrated"))
            if self.memory_file and self.memory_file.exists():
                self.memory_file.rename(self.memory_file.with_suffix(".md.migrated"))
        except Exception:
            # Don't break if migration fails
            pass

    def get_memory_content(self) -> str:
        """Get current memory content for injection from SQLite."""
        # Get learning summary from database
        summary = self.db.get_learning_summary(self.project_hash)
        
        # Format as markdown for AI context
        content = ["# MEMORY:\n"]
        
        if summary["top_issues"]:
            content.append("## Recent Violation Patterns (Last 7 Days)\n")
            for issue in summary["top_issues"]:
                content.append(f"- **{issue['type']}** ({issue['count']}x): {issue['fix']}")
            content.append("")
        
        if summary["problem_files"]:
            content.append("## Files Needing Attention\n")
            for file_info in summary["problem_files"]:
                content.append(f"- {file_info['file']}: {file_info['violations']} violations")
            content.append("")
        
        if not summary["top_issues"] and not summary["problem_files"]:
            content.append("No violations logged yet.\n")
        
        return "\n".join(content)
    
    def clear_memory(self) -> None:
        """Clear all violation memory (for testing or reset)."""
        # Legacy file cleanup
        if self.log_file and self.log_file.exists():
            self.log_file.unlink()
        if self.memory_file and self.memory_file.exists():
            self.memory_file.unlink()
        
        # Note: We don't clear SQLite here as it's shared across projects
        # Use db.cleanup_old_violations() for database maintenance
