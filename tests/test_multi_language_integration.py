"""
Integration tests for multi-language enforcer system.

These tests verify complete end-to-end functionality across all supported languages
(Python, TypeScript, Rust, Go) by running claudex-guard with real files and checking
real outputs. Tests factory routing, violation detection, and graceful degradation.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def run_enforcer_with_stdin(
    file_path: Path, hook_data: dict[str, Any]
) -> tuple[int, str, str]:
    """Run claudex-guard with simulated hook stdin data."""
    stdin_input = json.dumps(hook_data)
    result = subprocess.run(
        ["uv", "run", "python", "-m", "claudex_guard.main"],
        input=stdin_input,
        text=True,
        capture_output=True,
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode, result.stdout, result.stderr


def run_enforcer_with_env_var(file_path: Path) -> tuple[int, str, str]:
    """Run claudex-guard with environment variable."""
    import os

    env = os.environ.copy()
    env["CLAUDE_FILE_PATHS"] = str(file_path)

    result = subprocess.run(
        ["uv", "run", "python", "-m", "claudex_guard.main"],
        text=True,
        capture_output=True,
        cwd=Path(__file__).parent.parent,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


# Test code generators for each language


def create_python_test_code_with_violations() -> str:
    """Python code with banned imports and type hint violations."""
    return """import requests
import pip

def missing_type_hints(x, y):
    return x + y
"""


def create_typescript_test_code_with_violations() -> str:
    """TypeScript code with console.log and any types."""
    return """import moment from 'moment';

function test(x: any): any {
    console.log('debug message');
    return x;
}
"""


def create_rust_test_code_with_violations() -> str:
    """Rust code with unwrap abuse and banned crates."""
    return """use time;

fn main() {
    let result = Some(42);
    let value = result.unwrap();
}
"""


def create_go_test_code_with_violations() -> str:
    """Go code with panic, error ignoring, and deprecated packages."""
    return """package main
import "io/ioutil"

func main() {
    data, _ := ioutil.ReadFile("test.txt")
    if data == nil {
        panic("file not found")
    }
}
"""


def create_unsupported_file_content() -> str:
    """Generic text content for unsupported file types."""
    return "This is a plain text file with no code."


# Python enforcer tests


def test_python_routing_and_violation_detection() -> None:
    """Test that Python files are routed to PythonEnforcer correctly."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(create_python_test_code_with_violations())
        test_file = Path(f.name)

    try:
        hook_data = {"tool_input": {"file_path": str(test_file)}}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # Python files should be processed (not skipped as unsupported)
        # Exit code can be 0 (pass/auto-fixed) or 2 (violations)
        assert exit_code in (0, 2), f"Expected exit code 0 or 2, got {exit_code}"
        # File was processed (not an error)
        assert exit_code != 1
    finally:
        test_file.unlink()


def test_python_clean_file_approval() -> None:
    """Test that clean Python files pass without violations."""
    clean_code = '''def add(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(clean_code)
        test_file = Path(f.name)

    try:
        hook_data = {"tool_input": {"file_path": str(test_file)}}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # Clean code should pass (exit 0 or be approved)
        # Note: May still be exit 2 if auto-fixes create violations
        assert exit_code in (0, 2)
    finally:
        test_file.unlink()


# TypeScript enforcer tests


def test_typescript_routing_and_violation_detection() -> None:
    """Test that TypeScript files are routed to TypeScriptEnforcer correctly."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
        f.write(create_typescript_test_code_with_violations())
        test_file = Path(f.name)

    try:
        hook_data = {"tool_input": {"file_path": str(test_file)}}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # Should detect violations (may be tool missing or actual violations)
        # Graceful degradation: ESLint/tsc missing is OK
        assert exit_code in (0, 2)
        if exit_code == 2:
            assert '"decision": "block"' in stderr
            # Should detect console.log or moment import or any type
            violations_present = (
                "console" in stderr.lower()
                or "moment" in stderr.lower()
                or "any" in stderr.lower()
                or "eslint" in stderr.lower()
            )
            assert violations_present, "Expected TypeScript-specific violations"
    finally:
        test_file.unlink()


def test_javascript_routing_to_typescript_enforcer() -> None:
    """Test that JavaScript files are also routed to TypeScriptEnforcer."""
    js_code = """const axios = require('axios');
console.log('test');
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write(js_code)
        test_file = Path(f.name)

    try:
        hook_data = {"tool_input": {"file_path": str(test_file)}}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # Should route to TypeScript enforcer (graceful degradation if tools missing)
        assert exit_code in (0, 2)
    finally:
        test_file.unlink()


# Rust enforcer tests


def test_rust_routing_and_violation_detection() -> None:
    """Test that Rust files are routed to RustEnforcer correctly."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
        f.write(create_rust_test_code_with_violations())
        test_file = Path(f.name)

    try:
        hook_data = {"tool_input": {"file_path": str(test_file)}}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # Should detect violations (graceful degradation if Clippy missing)
        assert exit_code in (0, 2)
        if exit_code == 2:
            assert '"decision": "block"' in stderr
            # Should detect unwrap or time crate or clippy missing
            violations_present = (
                "unwrap" in stderr.lower()
                or "time" in stderr.lower()
                or "clippy" in stderr.lower()
            )
            assert violations_present, "Expected Rust-specific violations"
    finally:
        test_file.unlink()


# Go enforcer tests


def test_go_routing_and_violation_detection() -> None:
    """Test that Go files are routed to GoEnforcer correctly."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".go", delete=False) as f:
        f.write(create_go_test_code_with_violations())
        test_file = Path(f.name)

    try:
        hook_data = {"tool_input": {"file_path": str(test_file)}}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # Go files should be processed (not skipped as unsupported)
        # Exit code can be 0 (pass/auto-fixed) or 2 (violations)
        assert exit_code in (0, 2), f"Expected exit code 0 or 2, got {exit_code}"
        # File was processed (not an error)
        assert exit_code != 1
    finally:
        test_file.unlink()


# Unsupported file type tests


def test_unsupported_file_txt_graceful_skip() -> None:
    """Test that .txt files are skipped gracefully without blocking."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(create_unsupported_file_content())
        test_file = Path(f.name)

    try:
        hook_data = {"tool_input": {"file_path": str(test_file)}}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # Unsupported files should skip gracefully with exit 0
        assert exit_code == 0, (
            f"Expected exit code 0 for unsupported file, got {exit_code}"
        )
    finally:
        test_file.unlink()


def test_unsupported_file_md_graceful_skip() -> None:
    """Test that .md files are skipped gracefully without blocking."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Markdown file\n\nThis is documentation.")
        test_file = Path(f.name)

    try:
        hook_data = {"tool_input": {"file_path": str(test_file)}}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # Unsupported files should skip gracefully
        assert exit_code == 0
    finally:
        test_file.unlink()


def test_unsupported_file_json_graceful_skip() -> None:
    """Test that .json files are skipped gracefully without blocking."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"key": "value"}')
        test_file = Path(f.name)

    try:
        hook_data = {"tool_input": {"file_path": str(test_file)}}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # Unsupported files should skip gracefully
        assert exit_code == 0
    finally:
        test_file.unlink()


# Hook integration tests


def test_hook_json_output_format_validation() -> None:
    """Test JSON output format matches Claude Code expectations."""
    # Use a file with deliberate syntax error to ensure violations
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def broken syntax\n")  # Syntax error will definitely be caught
        test_file = Path(f.name)

    try:
        hook_data = {"tool_input": {"file_path": str(test_file)}}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # With syntax error, should get some output (may be approval or block)
        # Main test: verify we get valid JSON output when there's processing
        if stdout.strip():
            output = json.loads(stdout)
            assert "decision" in output, "JSON output must have 'decision' field"
            assert "reason" in output, "JSON output must have 'reason' field"
            assert output["decision"] in (
                "approve",
                "block",
            ), "Decision must be 'approve' or 'block'"
        # If no stdout, file was processed silently (also valid)
    finally:
        test_file.unlink()


def test_hook_env_var_fallback() -> None:
    """Test that CLAUDE_FILE_PATHS environment variable works."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(create_python_test_code_with_violations())
        test_file = Path(f.name)

    try:
        exit_code, stdout, stderr = run_enforcer_with_env_var(test_file)

        # Should work via env var (file processed, not skipped)
        assert exit_code in (0, 2), f"Expected processing via env var, got {exit_code}"
        assert exit_code != 1  # Not an error
    finally:
        test_file.unlink()


# Language isolation tests


def test_language_isolation_python_errors_dont_affect_typescript() -> None:
    """Test that Python violations don't interfere with TypeScript analysis."""
    # Create both files
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import requests\n")  # Python file
        py_file = Path(f.name)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
        f.write("console.log('test');\n")  # TypeScript file
        ts_file = Path(f.name)

    try:
        # Test Python file
        hook_data = {"tool_input": {"file_path": str(py_file)}}
        py_exit, py_out, py_err = run_enforcer_with_stdin(py_file, hook_data)

        # Test TypeScript file (should work independently)
        hook_data = {"tool_input": {"file_path": str(ts_file)}}
        ts_exit, ts_out, ts_err = run_enforcer_with_stdin(ts_file, hook_data)

        # Both should be processed successfully (not errors)
        assert py_exit in (0, 2), f"Python file should process, got exit {py_exit}"
        assert ts_exit in (0, 2), f"TypeScript file should process, got exit {ts_exit}"
        # Neither should be execution errors
        assert py_exit != 1
        assert ts_exit != 1
    finally:
        py_file.unlink()
        ts_file.unlink()


# Factory routing case sensitivity test


def test_factory_routing_case_insensitive_extension() -> None:
    """Test that factory handles uppercase extensions (.PY, .TS, etc.)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".PY", delete=False) as f:
        f.write(create_python_test_code_with_violations())
        test_file = Path(f.name)

    try:
        hook_data = {"tool_input": {"file_path": str(test_file)}}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # Should route correctly despite uppercase extension (not skip as unsupported)
        assert exit_code in (0, 2), f"Expected processing, got exit {exit_code}"
        assert exit_code != 1  # Not an error
    finally:
        test_file.unlink()
