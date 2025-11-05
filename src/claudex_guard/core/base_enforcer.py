"""Base enforcer class for claudex-guard language enforcers."""

import importlib
import json
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from .project_cache import ProjectRootCache
from .violation import Violation, ViolationReporter


class BaseEnforcer(ABC):
    """Base class for language-specific code quality enforcers."""

    # Extension to enforcer mapping (module_path, class_name)
    EXTENSION_MAP = {
        ".py": ("claudex_guard.enforcers.python", "PythonEnforcer"),
        # Future language support will be added here:
        # '.ts': ('claudex_guard.enforcers.typescript', 'TypeScriptEnforcer'),
        # '.js': ('claudex_guard.enforcers.typescript', 'TypeScriptEnforcer'),
        # '.tsx': ('claudex_guard.enforcers.typescript', 'TypeScriptEnforcer'),
        # '.jsx': ('claudex_guard.enforcers.typescript', 'TypeScriptEnforcer'),
        # '.rs': ('claudex_guard.enforcers.rust', 'RustEnforcer'),
        # '.go': ('claudex_guard.enforcers.go', 'GoEnforcer'),
    }

    def __init__(self, language: str):
        self.language = language
        self.reporter = ViolationReporter(language)
        self.cache = ProjectRootCache()

    @staticmethod
    def create(file_path: Path) -> Optional["BaseEnforcer"]:
        """Factory method: create appropriate enforcer for file extension.

        Args:
            file_path: Path to file to analyze

        Returns:
            Enforcer instance for the file type, or None if unsupported
        """
        ext = file_path.suffix.lower()

        if ext not in BaseEnforcer.EXTENSION_MAP:
            return None  # Unsupported file type - skip gracefully

        # Lazy import to avoid loading all enforcers at startup
        module_path, class_name = BaseEnforcer.EXTENSION_MAP[ext]
        try:
            module = importlib.import_module(module_path)
            enforcer_class = getattr(module, class_name)
            return enforcer_class()
        except (ImportError, AttributeError):
            # Enforcer not available - return None to skip gracefully
            return None

    @staticmethod
    def run_for_file(file_path: Path) -> int:
        """Convenience method: create enforcer and run analysis.

        Args:
            file_path: Path to file to analyze

        Returns:
            Exit code: 0 (success), 1 (error), 2 (violations found)
        """
        enforcer = BaseEnforcer.create(file_path)
        if not enforcer:
            return 0  # Unsupported file type - skip gracefully (no false blocking)
        return enforcer.run()

    @abstractmethod
    def analyze_file(self, file_path: Path) -> list[Violation]:
        """Analyze a file and return list of violations."""
        pass

    @abstractmethod
    def apply_automatic_fixes(self, file_path: Path) -> list[str]:
        """Apply automatic fixes and return list of changes made."""
        pass

    @staticmethod
    def get_file_path_from_hook_context() -> Optional[Path]:
        """Extract file path from Claude Code hook context."""
        try:
            # Method 1: Claude Code env var (preferred - simple and reliable)
            claude_file_paths = os.environ.get("CLAUDE_FILE_PATHS", "")
            if claude_file_paths:
                file_path = Path(claude_file_paths.split()[0])
                if file_path.exists():
                    return file_path

            # Method 2: JSON stdin (fallback for compatibility)
            stdin_data = sys.stdin.read()
            if stdin_data.strip():
                hook_data = json.loads(stdin_data)
                # Try tool_input first (primary Claude Code format)
                tool_input = hook_data.get("tool_input", {})
                file_path_str = tool_input.get("file_path", "")
                if file_path_str:
                    file_path = Path(file_path_str)
                    if file_path.exists():
                        return file_path

                # Try top-level file_path (fallback)
                file_path_str = hook_data.get("file_path", "")
                if file_path_str:
                    file_path = Path(file_path_str)
                    if file_path.exists():
                        return file_path

            # Method 3: Command line args (testing/standalone use)
            if len(sys.argv) > 1:
                file_path = Path(sys.argv[1])
                if file_path.exists():
                    return file_path

            return None

        except Exception:
            return None

    def should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed by this enforcer."""
        return file_path.exists() and self.is_supported_file(file_path)

    @abstractmethod
    def is_supported_file(self, file_path: Path) -> bool:
        """Check if file type is supported by this enforcer."""
        pass

    def run(self) -> int:
        """Main entry point for enforcer execution."""
        try:
            file_path = BaseEnforcer.get_file_path_from_hook_context()

            if not file_path or not self.should_analyze_file(file_path):
                return 0

            # Create workflow context to determine project root
            workflow_context = WorkflowContext(file_path)

            # Pass project root to reporter for centralized memory storage
            if workflow_context.project_root:
                self.reporter.set_project_root(workflow_context.project_root)

            # Apply automatic fixes first
            fixes = self.apply_automatic_fixes(file_path)
            for fix in fixes:
                self.reporter.add_fix(fix)

            # Analyze for violations
            violations = self.analyze_file(file_path)
            for violation in violations:
                self.reporter.add_violation(violation)

            # Report results
            return self.reporter.report()

        except (OSError, ValueError, TypeError, ImportError) as e:
            # Don't break the workflow if analysis fails, but log the error
            import sys

            print(f"Error: Analysis failed: {e}", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            # User interrupted - re-raise to allow clean shutdown
            raise
        except Exception as e:
            # Unexpected error - log and fail
            import sys

            print(f"Error: Unexpected analysis failure: {e}", file=sys.stderr)
            return 1


class WorkflowContext:
    """Understands development workflow context for intelligent enforcement."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.cache = ProjectRootCache()

        # Try to get from cache first
        self.project_root = self.cache.get_project_root(file_path)

        # If not cached, discover and cache it
        if self.project_root is None:
            self.project_root = self._find_project_root()
            if self.project_root:
                # Determine what markers we found
                markers = self._get_found_markers(self.project_root)
                self.cache.add_project_root(file_path, self.project_root, markers)

        self.is_development_project = self._is_development_project()

    def _find_project_root(self) -> Optional[Path]:
        """Find project root by looking for development workflow markers.

        Priority order (searches ALL directories then picks highest priority):
        1. Git repository root (.git directory)
        2. Language-specific project files (pyproject.toml, package.json, etc.)
        3. Claude configuration markers (.claude/, CLAUDE.md)
        """
        # Collect all potential roots with their priority
        candidates = []

        current = self.file_path.parent
        while current != current.parent:
            # Priority 1: Git repository root - most definitive
            if (current / ".git").exists():
                candidates.append((1, current))

            # Priority 2: Language-specific project markers
            project_markers = [
                "pyproject.toml",  # Python with modern tooling
                "setup.py",  # Python legacy
                "package.json",  # JavaScript/TypeScript
                "Cargo.toml",  # Rust
                "go.mod",  # Go
                "pom.xml",  # Java/Maven
                "build.gradle",  # Java/Gradle
                "Gemfile",  # Ruby
                "mix.exs",  # Elixir
                "composer.json",  # PHP
            ]
            if any((current / marker).exists() for marker in project_markers):
                candidates.append((2, current))

            # Priority 3: Claude configuration (might be subdirectory configs)
            if (current / ".claude").exists() or (current / "CLAUDE.md").exists():
                candidates.append((3, current))

            current = current.parent

        # Return the highest priority (lowest number) candidate
        if candidates:
            # Sort by priority (asc) then path depth (desc to prefer root)
            candidates.sort(key=lambda x: (x[0], -len(x[1].parts)))
            return candidates[0][1]

        return None

    def _get_found_markers(self, root: Path) -> list[str]:
        """Get list of markers found at the project root."""
        markers = []

        if (root / ".git").exists():
            markers.append(".git")

        project_files = [
            "pyproject.toml",
            "setup.py",
            "package.json",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
            "Gemfile",
            "mix.exs",
            "composer.json",
        ]

        for marker in project_files:
            if (root / marker).exists():
                markers.append(marker)

        if (root / ".claude").exists():
            markers.append(".claude")
        if (root / "CLAUDE.md").exists():
            markers.append("CLAUDE.md")

        return markers

    def _is_development_project(self) -> bool:
        """Check if this is a systematic development project."""
        if not self.project_root:
            return False

        return (
            (self.project_root / ".claude").exists()
            or (self.project_root / "CLAUDE.md").exists()
            or (self.project_root / "pyproject.toml").exists()
            or (self.project_root / "package.json").exists()
        )

    def should_enforce_strict_quality(self) -> bool:
        """Determine if strict quality enforcement should apply."""
        return self.is_development_project

    def get_context_message(self) -> str:
        """Get context message about current workflow state."""
        if not self.is_development_project:
            return "Regular file - applying basic quality standards"

        return "Development project - standard quality enforcement"
