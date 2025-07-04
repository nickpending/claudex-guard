"""Common utilities for claudex-guard enforcers."""

import re
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional


def run_command(
    command: List[str], 
    cwd: Optional[Path] = None, 
    timeout: int = 30
) -> Tuple[int, str, str]:
    """Run a command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        return result.returncode, result.stdout, result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 1, "", f"Command failed or timed out: {' '.join(command)}"


def check_tool_available(tool_name: str) -> bool:
    """Check if a command-line tool is available."""
    exit_code, _, _ = run_command(["which", tool_name])
    return exit_code == 0


def find_config_file(start_path: Path, config_name: str) -> Optional[Path]:
    """Find a config file by walking up the directory tree."""
    current = start_path if start_path.is_dir() else start_path.parent
    
    while current != current.parent:
        config_path = current / config_name
        if config_path.exists():
            return config_path
        current = current.parent
    
    return None


def normalize_line_endings(content: str) -> str:
    """Normalize line endings to Unix-style."""
    return content.replace('\r\n', '\n').replace('\r', '\n')


def extract_file_extension(file_path: Path) -> str:
    """Extract normalized file extension."""
    return file_path.suffix.lower().lstrip('.')


def is_text_file(file_path: Path, max_check_bytes: int = 1024) -> bool:
    """Check if a file appears to be a text file."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(max_check_bytes)
            if b'\0' in chunk:  # Null bytes indicate binary
                return False
            
            # Try to decode as UTF-8
            chunk.decode('utf-8')
            return True
    except (UnicodeDecodeError, IOError):
        return False


def count_lines(file_path: Path) -> int:
    """Count lines in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except (IOError, UnicodeDecodeError):
        return 0


def find_pattern_matches(
    content: str, 
    pattern: str, 
    flags: int = re.MULTILINE
) -> List[Tuple[int, str]]:
    """Find all matches of a regex pattern and return (line_number, match_text)."""
    matches = []
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        if re.search(pattern, line, flags):
            matches.append((line_num, line.strip()))
    
    return matches


def get_project_type(project_root: Path) -> str:
    """Determine the type of project based on files present."""
    if (project_root / "pyproject.toml").exists():
        return "python"
    elif (project_root / "package.json").exists():
        return "javascript"
    elif (project_root / "Cargo.toml").exists():
        return "rust"
    elif (project_root / "go.mod").exists():
        return "go"
    elif (project_root / "pom.xml").exists():
        return "java"
    else:
        return "unknown"


class PerformanceTracker:
    """Simple performance tracking for enforcer operations."""
    
    def __init__(self):
        self.times = {}
        self.start_times = {}
    
    def start(self, operation: str) -> None:
        """Start timing an operation."""
        import time
        self.start_times[operation] = time.time()
    
    def end(self, operation: str) -> float:
        """End timing an operation and return duration."""
        import time
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            self.times[operation] = duration
            del self.start_times[operation]
            return duration
        return 0.0
    
    def get_summary(self) -> str:
        """Get a summary of all timed operations."""
        if not self.times:
            return "No operations timed"
        
        total = sum(self.times.values())
        lines = [f"Performance Summary (total: {total:.3f}s)"]
        for op, duration in sorted(self.times.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {op}: {duration:.3f}s")
        
        return "\n".join(lines)