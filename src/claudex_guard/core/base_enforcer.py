"""Base enforcer class for claudex-guard language enforcers."""

import json
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from .violation import Violation, ViolationReporter


class BaseEnforcer(ABC):
    """Base class for language-specific code quality enforcers."""

    def __init__(self, language: str):
        self.language = language
        self.reporter = ViolationReporter(language)

    @abstractmethod
    def analyze_file(self, file_path: Path) -> List[Violation]:
        """Analyze a file and return list of violations."""
        pass

    @abstractmethod
    def apply_automatic_fixes(self, file_path: Path) -> List[str]:
        """Apply automatic fixes and return list of changes made."""
        pass

    def get_file_path_from_hook_context(self) -> Optional[Path]:
        """Extract file path from Claude Code hook context."""
        try:
            # Method 1: Claude Code environment variable (preferred - simple and reliable)
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
            file_path = self.get_file_path_from_hook_context()

            if not file_path or not self.should_analyze_file(file_path):
                return 0

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
        self.project_root = self._find_project_root()
        self.is_development_project = self._is_development_project()

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
