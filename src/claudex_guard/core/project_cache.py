"""Project root discovery cache to eliminate repeated directory scanning."""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional


class ProjectRootCache:
    """Cache discovered project roots to avoid expensive repeated scanning."""

    def __init__(self):
        """Initialize cache with XDG base directory compliant location."""
        self.cache_dir = Path.home() / ".config" / "claudex-guard"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "project_roots.json"
        self.cache: dict[str, dict[str, Any]] = self._load_cache()

    def _load_cache(self) -> dict[str, dict[str, Any]]:
        """Load cache from disk, return empty dict if not found or corrupt."""
        if self.cache_file.exists():
            try:
                data = json.loads(self.cache_file.read_text())
                # Validate cache structure
                if isinstance(data, dict):
                    return data
            except (json.JSONDecodeError, OSError):
                # Corrupt or inaccessible cache, start fresh
                pass
        return {}

    def _save_cache(self) -> None:
        """Save cache to disk atomically to prevent corruption."""
        try:
            # Write to temp file first for atomic operation
            temp_file = self.cache_file.with_suffix(".tmp")
            temp_file.write_text(json.dumps(self.cache, indent=2))
            temp_file.replace(self.cache_file)
        except OSError:
            # Don't break workflow if cache can't be saved
            pass

    def get_project_root(self, file_path: Path) -> Optional[Path]:
        """Get cached project root for a file path.

        Args:
            file_path: Path to file being analyzed

        Returns:
            Cached project root path or None if not in cache
        """
        # Check if any parent directory is in cache
        current = file_path.parent.resolve()

        while current != current.parent:
            cache_key = str(current)

            if cache_key in self.cache:
                entry = self.cache[cache_key]
                # Update last accessed time
                entry["last_accessed"] = datetime.now().isoformat()
                self._save_cache()
                return Path(entry["root"])

            current = current.parent

        return None

    def add_project_root(self, file_path: Path, root: Path, markers: list[str]) -> None:
        """Add discovered project root to cache.

        Args:
            file_path: Path to file that triggered discovery
            root: Discovered project root path
            markers: List of markers found (e.g., [".git", "pyproject.toml"])
        """
        # Cache for the file's parent directory
        cache_key = str(file_path.parent.resolve())

        self.cache[cache_key] = {
            "root": str(root.resolve()),
            "discovered_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "markers": markers,
            "project_hash": self._get_project_hash(root),
        }

        self._save_cache()

    def _get_project_hash(self, root: Path) -> str:
        """Generate a short hash for project root path.

        Used for organizing project-specific data.
        """
        return hashlib.md5(str(root.resolve()).encode()).hexdigest()[:8]

    def get_project_hash(self, file_path: Path) -> Optional[str]:
        """Get project hash for a file if its root is cached."""
        root = self.get_project_root(file_path)
        if root:
            return self._get_project_hash(root)
        return None

    def cleanup_stale_entries(self, days: int = 30) -> None:
        """Remove cache entries not accessed in specified days.

        Args:
            days: Number of days after which to consider entry stale
        """
        cutoff = datetime.now() - timedelta(days=days)

        # Filter out stale entries
        self.cache = {
            key: entry
            for key, entry in self.cache.items()
            if datetime.fromisoformat(
                entry.get("last_accessed", entry["discovered_at"])
            )
            > cutoff
        }

        self._save_cache()

    def clear_cache(self) -> None:
        """Clear all cached entries."""
        self.cache = {}
        self._save_cache()
