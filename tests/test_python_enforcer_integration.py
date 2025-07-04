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
from typing import Dict, Tuple


def run_enforcer_with_stdin(file_path: Path, hook_data: Dict) -> Tuple[int, str, str]:
    """Run claudex-guard-python with simulated hook stdin data."""
    stdin_input = json.dumps(hook_data)
    result = subprocess.run(
        ["uv", "run", "claudex-guard-python"],
        input=stdin_input,
        text=True,
        capture_output=True,
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode, result.stdout, result.stderr


def run_enforcer_with_cli_args(file_path: Path) -> Tuple[int, str, str]:
    """Run claudex-guard-python with CLI argument."""
    result = subprocess.run(
        ["uv", "run", "claudex-guard-python", str(file_path)],
        text=True,
        capture_output=True,
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode, result.stdout, result.stderr


def run_enforcer_with_env_var(file_path: Path) -> Tuple[int, str, str]:
    """Run claudex-guard-python with environment variable."""
    import os

    env = os.environ.copy()
    env["CLAUDE_FILE_PATHS"] = str(file_path)

    result = subprocess.run(
        ["uv", "run", "claudex-guard-python"],
        text=True,
        capture_output=True,
        cwd=Path(__file__).parent.parent,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


def create_test_file_with_violations() -> str:
    """Create a test Python file with known violations."""
    return '''def bad_function(items=[]):  # Mutable default argument
    """Function with multiple violations."""
    message = "Hello %s" % "world"  # Old string formatting
    try:
        result = eval("2+2")  # Never use eval
    except:  # Bare except clause
        pass
    return items

def missing_type_hints(x, y):  # Missing return type hint
    return x + y

print("Debug output")  # Use rich.print instead
'''


def create_clean_test_file() -> str:
    """Create a clean Python file with no violations."""
    return '''from typing import List

def clean_function(items: List[str]) -> List[str]:
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


def test_hook_integration_with_stdin_json():
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
        assert "🚨 Quality violations found:" in stderr
        assert "Mutable default argument" in stderr
        assert "/.claudex/standards/claudex-python.md" in stderr
        assert "❌ Blocking due to quality standard violations" in stderr

    finally:
        test_file.unlink()


def test_hook_integration_with_fallback_path():
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
        assert "🚨 Quality violations found:" in stderr
        assert "Mutable default argument" in stderr

    finally:
        test_file.unlink()


def test_hook_integration_with_cli_args():
    """Test hook integration using command line arguments."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(create_test_file_with_violations())
        test_file = Path(f.name)

    try:
        exit_code, stdout, stderr = run_enforcer_with_cli_args(test_file)

        # Should find violations and block
        assert exit_code == 2, f"Expected exit code 2, got {exit_code}"
        assert "🚨 Quality violations found:" in stderr
        assert "Mutable default argument" in stderr

    finally:
        test_file.unlink()


def test_hook_integration_with_env_var():
    """Test hook integration using environment variable."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(create_test_file_with_violations())
        test_file = Path(f.name)

    try:
        exit_code, stdout, stderr = run_enforcer_with_env_var(test_file)

        # Should find violations and block
        assert exit_code == 2, f"Expected exit code 2, got {exit_code}"
        assert "🚨 Quality violations found:" in stderr
        assert "Mutable default argument" in stderr

    finally:
        test_file.unlink()


def test_clean_file_no_violations():
    """Test that clean files pass without violations."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(create_clean_test_file())
        test_file = Path(f.name)

    try:
        hook_data = {"tool_input": {"file_path": str(test_file)}}
        exit_code, stdout, stderr = run_enforcer_with_stdin(test_file, hook_data)

        # Should pass with only automatic fixes (if any)
        assert exit_code == 0, f"Expected exit code 0, got {exit_code}"

        # May have automatic fixes applied, but no violations
        if "✅ Automatic fixes applied:" in stderr:
            assert (
                "✅ All quality standards met - proceeding with development" in stderr
            )

        # Should not have blocking violations
        assert "❌ Blocking due to quality standard violations" not in stderr

    finally:
        test_file.unlink()


def test_automatic_fixes_applied():
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

        # Should apply automatic fixes
        assert "✅ Automatic fixes applied:" in stderr
        assert "Applied ruff formatting" in stderr

        # Check that file was actually modified by ruff
        fixed_content = test_file.read_text()
        assert "x = 1" in fixed_content  # Proper spacing around =
        assert "y = 2" in fixed_content  # Proper spacing around =
        assert "return x + y" in fixed_content  # Proper spacing around +

    finally:
        test_file.unlink()


def test_violation_detection_comprehensive():
    """Test comprehensive violation detection against known patterns."""
    violation_code = """import requests  # Banned import
import pip

def bad_function(items=[]):  # Mutable default argument
    message = "Hello %s" % "world"  # Old string formatting
    try:
        result = eval("dangerous")  # eval usage
    except:  # Bare except
        print("debug")  # print instead of rich.print
    return items

def missing_hints(x, y):  # Missing type hints
    return x + y
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

        # Check for violations we expect (more flexible matching)
        assert "Mutable default argument" in stderr
        assert "Use f-strings" in stderr or "Old string formatting" in stderr
        assert "eval" in stderr
        assert "Bare except" in stderr

    finally:
        test_file.unlink()


def test_error_handling_with_syntax_errors():
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
        assert "Traceback" not in stderr
        assert "SyntaxError" not in stderr  # Should be handled gracefully

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
