"""SQLite-based violation storage for queryable history and pattern analysis."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .violation import Violation


class ViolationDB:
    """SQLite database for storing and querying code violations."""

    def __init__(self):
        """Initialize database in XDG base directory compliant location."""
        self.db_dir = Path.home() / ".config" / "claudex-guard"
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.db_dir / "violations.db"
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema if not exists."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_hash TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    line_num INTEGER NOT NULL,
                    violation_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    fix_suggestion TEXT,
                    severity TEXT,
                    function_name TEXT,
                    language TEXT,
                    UNIQUE(project_hash, file_path, line_num, violation_type, message)
                )
            """)

            # Create indexes for common queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_project_timestamp 
                ON violations(project_hash, timestamp DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_violation_type 
                ON violations(project_hash, violation_type)
            """)
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except sqlite3.Error:
            # Don't break workflow if database fails
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def log_violation(
        self, violation: Violation, project_hash: str, language: str = "python"
    ) -> None:
        """Log a violation to the database.

        Args:
            violation: Violation object to log
            project_hash: Hash identifying the project
            language: Programming language of the file
        """
        try:
            with self._get_connection() as conn:
                # Extract function name if available
                function_name = None
                if hasattr(violation, "function_name"):
                    function_name = violation.function_name
                elif violation.language_context:
                    function_name = violation.language_context.get("function")

                conn.execute(
                    """
                    INSERT OR REPLACE INTO violations 
                    (project_hash, timestamp, file_path, file_name, line_num, 
                     violation_type, message, fix_suggestion, severity, 
                     function_name, language)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        project_hash,
                        datetime.now().isoformat(),
                        str(violation.file_path),
                        Path(violation.file_path).name,
                        violation.line_num,
                        violation.violation_type,
                        violation.message,
                        violation.fix_suggestion,
                        violation.severity,
                        function_name,
                        language,
                    ),
                )
                conn.commit()
        except sqlite3.Error:
            # Don't break workflow if logging fails
            pass

    def get_recent_violations(
        self, project_hash: str, days: int = 7
    ) -> list[dict[str, Any]]:
        """Get recent violations for a project.

        Args:
            project_hash: Project identifier
            days: Number of days to look back

        Returns:
            List of violation records
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM violations
                    WHERE project_hash = ? AND timestamp > ?
                    ORDER BY timestamp DESC
                """,
                    (project_hash, cutoff),
                )

                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    def get_top_violations(
        self, project_hash: str, days: int = 7, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get most common violations for a project.

        Args:
            project_hash: Project identifier
            days: Number of days to look back
            limit: Maximum number of violation types to return

        Returns:
            List of violation types with counts
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT violation_type, COUNT(*) as count,
                           MAX(fix_suggestion) as fix_suggestion
                    FROM violations
                    WHERE project_hash = ? AND timestamp > ?
                    GROUP BY violation_type
                    ORDER BY count DESC
                    LIMIT ?
                """,
                    (project_hash, cutoff, limit),
                )

                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    def get_repeat_offenders(
        self, project_hash: str, days: int = 7
    ) -> list[dict[str, Any]]:
        """Get files with most violations.

        Args:
            project_hash: Project identifier
            days: Number of days to look back

        Returns:
            List of files with violation counts
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT file_name, COUNT(*) as violation_count,
                           COUNT(DISTINCT violation_type) as unique_violations
                    FROM violations
                    WHERE project_hash = ? AND timestamp > ?
                    GROUP BY file_name
                    ORDER BY violation_count DESC
                    LIMIT 10
                """,
                    (project_hash, cutoff),
                )

                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    def get_learning_summary(self, project_hash: str) -> dict[str, Any]:
        """Get learning summary for AI context injection.

        Args:
            project_hash: Project identifier

        Returns:
            Summary of recent patterns for AI assistant context
        """
        # Get top violations from last week
        top_violations = self.get_top_violations(project_hash, days=7, limit=5)

        # Get repeat offender files
        problem_files = self.get_repeat_offenders(project_hash, days=7)

        # Build summary
        summary = {
            "project_hash": project_hash,
            "generated_at": datetime.now().isoformat(),
            "top_issues": [
                {
                    "type": v["violation_type"],
                    "count": v["count"],
                    "fix": v["fix_suggestion"],
                }
                for v in top_violations
            ],
            "problem_files": [
                {"file": f["file_name"], "violations": f["violation_count"]}
                for f in problem_files[:3]  # Top 3 problem files
            ],
        }

        return summary

    def cleanup_old_violations(self, days: int = 90) -> None:
        """Remove violations older than specified days.

        Args:
            days: Number of days after which to remove violations
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    DELETE FROM violations
                    WHERE timestamp < ?
                """,
                    (cutoff,),
                )
                conn.commit()
        except sqlite3.Error:
            pass
