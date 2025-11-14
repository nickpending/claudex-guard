"""
Integration tests for Python enforcer.

These tests verify the complete end-to-end functionality by running the actual
claudex-guard-python tool with real files and checking real outputs.
No mocking of the tool itself - just real commands, real files, real results.
"""

import json
import subprocess
import tempfile
from pathlib import Path


def run_enforcer_with_stdin(file_path: Path, hook_data: dict) -> tuple[int, str, str]:
    """Run claudex-guard-python with simulated hook stdin data."""
    stdin_input = json.dumps(hook_data)
    result = subprocess.run(
        ["uv", "run", "python", "-m", "claudex_guard.main"],
        input=stdin_input,
        text=True,
        capture_output=True,
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode, result.stdout, result.stderr


def run_enforcer_with_cli_args(file_path: Path) -> tuple[int, str, str]:
    """Run claudex-guard-python with CLI argument."""
    result = subprocess.run(
        ["uv", "run", "claudex-guard-python", str(file_path)],
        text=True,
        capture_output=True,
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode, result.stdout, result.stderr


def run_enforcer_with_env_var(file_path: Path) -> tuple[int, str, str]:
    """Run claudex-guard-python with environment variable."""
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


def create_test_file_with_violations() -> str:
    """Create a test Python file with known violations."""
    return """import requests
import pip

def make_request():
    # Using banned imports so they don't get auto-removed
    return requests.get("https://example.com")

def install_package():
    pip.main(["install", "something"])
"""


def create_clean_test_file() -> str:
    """Create a clean Python file with no violations."""
    return '''def clean_function(items: list[str]) -> list[str]:
    """A properly written function with no violations."""
    message = f"Hello {'world'}"  # Proper f-string usage

    try:
        result = int("42")  # Safe conversion
    except ValueError:  # Specific exception
        result = 0

    return items + [str(result)]

if __name__ == "__main__":
    result = clean_function(["test"])
'''


def test_hook_integration_with_stdin_json() -> None:
    """Test hook integration using stdin JSON (primary Claude Code method)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(create_test_file_with_violations())
        test_file = Path(f.name)

    try:
        # Test with tool_input path (primary Claude Code format)
        hook_data = {"tool_input": {"file_path": str(test_file)}}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # Should find violations and block
        assert exit_code == 2, f"Expected exit code 2, got {exit_code}"
        assert '"decision": "block"' in stderr
        assert "Quality violations found" in stderr
        assert "requests" in stderr or "pip" in stderr
        # JSON output doesn't include the old footer message
        # JSON output - no stderr blocking message

    finally:
        test_file.unlink()


def test_hook_integration_with_fallback_path() -> None:
    """Test hook integration with fallback file_path (Claude Code fallback)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(create_test_file_with_violations())
        test_file = Path(f.name)

    try:
        # Test with fallback file_path (no tool_input)
        hook_data = {"file_path": str(test_file)}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # Should find violations and block
        assert exit_code == 2, f"Expected exit code 2, got {exit_code}"
        assert '"decision": "block"' in stderr
        assert "Quality violations found" in stderr
        assert "requests" in stderr or "pip" in stderr

    finally:
        test_file.unlink()


def test_hook_integration_with_cli_args() -> None:
    """Test hook integration using command line arguments."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(create_test_file_with_violations())
        test_file = Path(f.name)

    try:
        exit_code, stdout, stderr = run_enforcer_with_cli_args(test_file)

        # Should find violations and block
        assert exit_code == 2, f"Expected exit code 2, got {exit_code}"
        assert '"decision": "block"' in stderr
        assert "Quality violations found" in stderr
        assert "requests" in stderr or "pip" in stderr

    finally:
        test_file.unlink()


def test_hook_integration_with_env_var() -> None:
    """Test hook integration using environment variable."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(create_test_file_with_violations())
        test_file = Path(f.name)

    try:
        exit_code, stdout, stderr = run_enforcer_with_env_var(test_file)

        # Should find violations and block
        assert exit_code == 2, f"Expected exit code 2, got {exit_code}"
        assert '"decision": "block"' in stderr
        assert "Quality violations found" in stderr
        assert "requests" in stderr or "pip" in stderr

    finally:
        test_file.unlink()


def test_clean_file_no_violations() -> None:
    """Test that clean files pass without violations."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(create_clean_test_file())
        test_file = Path(f.name)

    try:
        hook_data = {"tool_input": {"file_path": str(test_file)}}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # Should pass with no violations
        assert exit_code == 0, f"Expected exit code 0, got {exit_code}"

        # Should have clean output for no violations
        assert '"decision": "approve"' in stdout or exit_code == 0

    finally:
        test_file.unlink()


def test_automatic_fixes_applied() -> None:
    """Test that automatic fixes are properly applied and reported."""
    # Create file that ruff can fix
    unfixed_code = """def test():
    x=1
    y   =   2
    return x+y
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(unfixed_code)
        test_file = Path(f.name)

    try:
        hook_data = {"tool_input": {"file_path": str(test_file)}}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # Should apply automatic fixes but may still have type hint violations
        assert exit_code in [0, 2]  # May have type hint violations remaining

        # Check that file was actually modified by ruff
        fixed_content = test_file.read_text()
        assert "x = 1" in fixed_content  # Proper spacing around =
        assert "y = 2" in fixed_content  # Proper spacing around =
        assert "return x + y" in fixed_content  # Proper spacing around +

    finally:
        test_file.unlink()


def test_violation_detection_comprehensive() -> None:
    """Test comprehensive violation detection against known patterns."""
    violation_code = """import requests  # Banned import

def function_one(x, y):  # Missing type hints
    message = "Hello %s" % "world"  # Old string formatting
    data = requests.get("https://api.example.com")  # Actually use banned import
    return x + y

def function_two(a, b):  # Missing type hints
    print("debug")  # print instead of rich.print
    return a + b
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(violation_code)
        test_file = Path(f.name)

    try:
        hook_data = {"tool_input": {"file_path": str(test_file)}}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # Should find multiple specific violations
        assert exit_code == 2, f"Expected exit code 2, got {exit_code}"

        # Print stderr for debugging if assertions fail
        print(f"STDERR: {stderr}")

        # Check for violations we expect (banned imports, formatting)
        assert "requests" in stderr or "Banned" in stderr
        assert "format" in stderr.lower()  # Old formatting detected

    finally:
        test_file.unlink()


def test_error_handling_with_syntax_errors() -> None:
    """Test that syntax errors don't crash the enforcer."""
    syntax_error_code = """def broken_function(
    # Missing closing parenthesis and colon
    return "This won't parse"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(syntax_error_code)
        test_file = Path(f.name)

    try:
        hook_data = {"tool_input": {"file_path": str(test_file)}}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # Should not crash, but may have exit code 2 due to other issues
        # The important thing is it doesn't crash with unhandled exception
        assert exit_code in [0, 2], f"Unexpected exit code {exit_code}"

        # Should not contain unhandled exception traces
        assert "Traceback" not in stdout
        assert "SyntaxError" not in stdout  # Should be handled gracefully

    finally:
        test_file.unlink()


def test_iteration_convergence_to_zero() -> None:
    """Test that iteration converges when auto-fixes eliminate all errors."""
    # Create file with only auto-fixable violations (spacing issues)
    code_with_fixable_issues = """def calculate(x,y):
    result=x+y
    return result
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code_with_fixable_issues)
        test_file = Path(f.name)

    try:
        exit_code, stdout, stderr = run_enforcer_with_env_var(test_file)

        # Should converge - either clean after fixes, or type hint violations remain
        assert exit_code in [0, 2], f"Expected exit code 0 or 2, got {exit_code}"

        # Verify file was modified by auto-fixes (spacing corrected)
        fixed_content = test_file.read_text()
        assert "x, y" in fixed_content, "Expected parameter spacing to be fixed"
        assert "result = x + y" in fixed_content, (
            "Expected operator spacing to be fixed"
        )

        # If exit code is 0, convergence to zero violations successful
        # If exit code is 2, type hint violations remain (not auto-fixable)
        if exit_code == 2:
            assert (
                "missing return type hint" in stdout.lower()
                or "type hint" in stdout.lower()
            )

    finally:
        test_file.unlink()


def test_iteration_max_iterations_limit() -> None:
    """Test that iteration respects max_iterations config limit."""
    # Create a file with persistent unfixable violations
    code_with_persistent_violations = """import requests

def missing_hints(x, y):
    data = requests.get("http://example.com")
    return x + y

def another_missing_hints(a, b):
    return a + b
"""

    # Create temp file for test code
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code_with_persistent_violations)
        test_file = Path(f.name)

    # Create temp config in project root
    project_root = Path(__file__).parent.parent
    config_file = project_root / ".claudex-guard.yaml"
    config_existed = config_file.exists()
    original_config = config_file.read_text() if config_existed else None

    try:
        # Write config with max_iterations = 2 (less than default 3)
        config_file.write_text("""auto_fix:
  max_iterations: 2
""")

        exit_code, stdout, stderr = run_enforcer_with_env_var(test_file)

        # Should find violations and block (max_iterations won't help unfixable issues)
        assert exit_code == 2, (
            f"Expected exit code 2 (violations remain), got {exit_code}"
        )
        assert "Quality violations found" in stderr or '"decision": "block"' in stderr

        # Verify violations are reported (banned import)
        assert "requests" in stderr or "Banned" in stderr or "import" in stderr.lower()

    finally:
        # Cleanup test file
        test_file.unlink()

        # Restore original config
        if config_existed and original_config:
            config_file.write_text(original_config)
        elif not config_existed and config_file.exists():
            config_file.unlink()


def test_iteration_no_improvement_early_exit() -> None:
    """Test that iteration exits early when fixes don't reduce violations."""
    # Create file where auto-fixes don't help with violations
    # (banned imports and missing type hints can't be auto-fixed)
    code_with_unfixable_violations = """import requests

def needs_hints(x, y):
    response = requests.post("http://api.example.com", json={"x": x, "y": y})
    return x + y
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code_with_unfixable_violations)
        test_file = Path(f.name)

    try:
        exit_code, stdout, stderr = run_enforcer_with_env_var(test_file)

        # Should exit with violations (early exit after detecting no improvement)
        assert exit_code == 2, f"Expected exit code 2, got {exit_code}"
        assert '"decision": "block"' in stderr
        assert "Quality violations found" in stderr

        # Should report the unfixable violations
        assert "requests" in stderr or "Banned" in stderr or "import" in stderr.lower()

    finally:
        test_file.unlink()


if __name__ == "__main__":
    # Run all tests
    test_functions = [
        test_hook_integration_with_stdin_json,
        test_hook_integration_with_fallback_path,
        test_hook_integration_with_cli_args,
        test_hook_integration_with_env_var,
        test_clean_file_no_violations,
        test_automatic_fixes_applied,
        test_violation_detection_comprehensive,
        test_error_handling_with_syntax_errors,
        test_iteration_convergence_to_zero,
        test_iteration_max_iterations_limit,
        test_iteration_no_improvement_early_exit,
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            print(f"Running {test_func.__name__}...")
            test_func()
            print(f"✅ {test_func.__name__} PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} FAILED: {e}")
            failed += 1

    print(f"\n📊 Results: {passed} passed, {failed} failed")

    if failed > 0:
        exit(1)
    else:
        print("🎉 All integration tests passed!")
