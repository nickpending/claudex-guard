"""Test that memory files are created in the project root, not cwd."""

import json
import os
import subprocess
import tempfile
from pathlib import Path
import pytest

pytestmark = pytest.mark.skip(reason="Storage migrated to SQLite - tests check .claudex-guard/memory.md but violations now in ~/.config/claudex-guard/violations.db")


def test_memory_file_created_at_project_root():
    """Test that .claudex-guard/memory.md is created at project root, not cwd."""
    
    # Create a temporary project structure
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Create project markers at root
        (project_root / ".git").mkdir()
        (project_root / "pyproject.toml").touch()
        
        # Create a subdirectory structure
        subdir = project_root / "src" / "components"
        subdir.mkdir(parents=True)
        
        # Create a Python file with violations in the subdirectory
        test_file = subdir / "bad_code.py"
        test_file.write_text("""
def bad_function(items=[]):
    '''Function with mutable default.'''
    return items
""")
        
        # Change to subdirectory to simulate Claude running from there
        original_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            
            # Run the enforcer on the file
            result = subprocess.run(
                ["uv", "run", "python", "-m", "claudex_guard.enforcers.python", str(test_file)],
                capture_output=True,
                text=True,
                cwd=original_cwd,  # Run from original dir but analyze file in subdir
            )
            
            # Check that memory was created at project root, not in subdirectory
            memory_at_root = project_root / ".claudex-guard" / "memory.md"
            memory_in_subdir = subdir / ".claudex-guard" / "memory.md"
            
            assert memory_at_root.exists(), f"Memory file should exist at project root: {memory_at_root}"
            assert not memory_in_subdir.exists(), f"Memory file should NOT exist in subdir: {memory_in_subdir}"
            
            # Verify the memory file has content
            memory_content = memory_at_root.read_text()
            assert "MEMORY:" in memory_content
            assert "mutable" in memory_content.lower() or "None default" in memory_content
            
        finally:
            os.chdir(original_cwd)


def test_memory_file_with_nested_claudes():
    """Test that multiple Claude instances in same project use same memory file."""
    
    # Create a temporary project structure
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Create project markers at root
        (project_root / ".git").mkdir()
        (project_root / "CLAUDE.md").write_text("# Project config")
        
        # Create two subdirectories
        frontend = project_root / "frontend"
        backend = project_root / "backend"
        frontend.mkdir()
        backend.mkdir()
        
        # Create bad Python files in each
        frontend_file = frontend / "app.py"
        frontend_file.write_text("def frontend_bad(x=[]): return x")
        
        backend_file = backend / "server.py"
        backend_file.write_text("import requests  # banned import")
        
        # Run enforcer from frontend directory
        subprocess.run(
            ["uv", "run", "python", "-m", "claudex_guard.enforcers.python", str(frontend_file)],
            capture_output=True,
            text=True,
        )
        
        # Run enforcer from backend directory
        subprocess.run(
            ["uv", "run", "python", "-m", "claudex_guard.enforcers.python", str(backend_file)],
            capture_output=True,
            text=True,
        )
        
        # Check that there's only ONE memory file at project root
        memory_at_root = project_root / ".claudex-guard" / "memory.md"
        memory_in_frontend = frontend / ".claudex-guard" / "memory.md"
        memory_in_backend = backend / ".claudex-guard" / "memory.md"
        
        assert memory_at_root.exists(), "Memory file should exist at project root"
        assert not memory_in_frontend.exists(), "Memory file should NOT exist in frontend dir"
        assert not memory_in_backend.exists(), "Memory file should NOT exist in backend dir"
        
        # Check that both violations are in the same memory file
        memory_content = memory_at_root.read_text()
        assert "mutable" in memory_content.lower() or "None default" in memory_content
        assert "httpx" in memory_content or "requests" in memory_content.lower()


if __name__ == "__main__":
    test_memory_file_created_at_project_root()
    test_memory_file_with_nested_claudes()
    print("✅ All memory location tests passed!")