"""Configuration management for claudex-guard."""

from pathlib import Path
from typing import Optional


class Config:
    """Load and manage claudex-guard configuration from .claudex-guard.yaml."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize configuration with defaults.

        Args:
            project_root: Project root directory to search for config file.
                         If None, uses current working directory.
        """
        # Default configuration values
        self.max_iterations: int = 3
        self.timeout: int = 30

        # Load from YAML if available
        self._load_from_yaml(project_root)

    def _load_from_yaml(self, project_root: Optional[Path]) -> None:
        """Load configuration from .claudex-guard.yaml file.

        Args:
            project_root: Directory to search for config file
        """
        try:
            import yaml
        except ImportError:
            # PyYAML not installed - skip config loading, use defaults
            return

        # Determine config file location
        config_dir = project_root if project_root else Path.cwd()
        config_file = config_dir / ".claudex-guard.yaml"

        if not config_file.exists():
            return  # No config file - use defaults

        try:
            with open(config_file) as f:
                config = yaml.safe_load(f)

                if not config:
                    return  # Empty config file - use defaults

                # Load auto_fix settings
                if "auto_fix" in config:
                    auto_fix_config = config["auto_fix"]

                    if "max_iterations" in auto_fix_config:
                        max_iter = auto_fix_config["max_iterations"]
                        if isinstance(max_iter, int) and max_iter > 0:
                            self.max_iterations = max_iter

                    if "timeout" in auto_fix_config:
                        timeout = auto_fix_config["timeout"]
                        if isinstance(timeout, int) and timeout > 0:
                            self.timeout = timeout

        except Exception:
            # Config file invalid - silently continue with defaults
            # Don't break workflow due to config issues
            pass
