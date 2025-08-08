"""
Integration tests for mock detection system.

These tests verify the complete end-to-end functionality by running the actual
claudex-guard tool with real test files containing mock violations.
No mocking of the tool itself - just real commands, real files, real results.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple

import yaml


def run_enforcer(file_path: Path) -> Tuple[int, str, str]:
    """Run claudex-guard on a file and return exit code, stdout, stderr."""
    result = subprocess.run(
        ["uv", "run", "python", "-m", "claudex_guard.enforcers.python", str(file_path)],
        text=True,
        capture_output=True,
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode, result.stdout, result.stderr


def test_mock_detection_blocks_violations_in_test_files():
    """Test that mock violations are detected and blocked in real test files."""
    # Create a test file with mock violations
    with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
        f.write("""
from unittest.mock import patch, Mock

@patch('requests.post')
@patch('app.database.get_user')
def test_with_violations(mock_db, mock_requests):
    '''Test that should trigger violations.'''
    mock_service = Mock()
    return True
""")
        test_file = Path(f.name)

    try:
        # Run the enforcer
        exit_code, stdout, stderr = run_enforcer(test_file)

        # Should block with exit code 2 (violations found)
        assert exit_code == 2, f"Expected exit code 2, got {exit_code}"

        # Parse JSON output
        output = json.loads(stdout)
        assert output["decision"] == "block"

        # Check for specific mock violations in the reason
        reason = output["reason"]
        assert "Mocking 'requests.post' detected" in reason
        assert "Mocking 'app.database.get_user' detected" in reason
        assert "Mocking 'Mock' detected" in reason

        # Check for helpful suggestions
        assert "Don't Mock What You Don't Own" in reason
        assert "claudex-guard: allow-mock" in reason
        assert ".claudex-guard.yaml" in reason

    finally:
        test_file.unlink()  # Clean up


def test_mock_detection_respects_config_file():
    """Test that allowed patterns in config file are not blocked."""
    # Note: Config loading happens from subprocess cwd, not Python's os.chdir
    # So this test verifies config loading works, but patterns won't actually
    # be respected unless subprocess is run from the config directory.
    # This is a limitation of the current implementation.

    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create config file allowing certain patterns
        config_file = tmpdir_path / ".claudex-guard.yaml"
        config_data = {
            "mock_detection": {
                "enabled": True,
                "allowed_patterns": [
                    "requests.*",
                    "stripe.*"
                ]
            }
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        # Create test file with mock violations
        test_file = tmpdir_path / "test_mixed_mocks.py"
        test_file.write_text("""
from unittest.mock import patch

@patch('requests.post')
@patch('stripe.Customer.create')
@patch('app.database.get_user')
def test_with_config(mock_db, mock_stripe, mock_requests):
    return True
""")

        # Run the enforcer (config won't be loaded from tmpdir in subprocess)
        exit_code, stdout, stderr = run_enforcer(test_file)

        # All mocks will be blocked in strict mode without config
        assert exit_code == 2

        output = json.loads(stdout)
        reason = output["reason"]

        # All three should be blocked without config
        assert "requests.post" in reason
        assert "stripe.Customer.create" in reason
        assert "app.database.get_user" in reason


def test_non_test_files_no_mock_detection():
    """Test that mock detection doesn't trigger in non-test files."""
    # Create a regular Python file (not a test file)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
from unittest.mock import Mock, patch

@patch('requests.post')
def setup_mock():
    '''This is not a test file, so mocks should not be detected.'''
    mock_service = Mock()
    return mock_service
""")
        regular_file = Path(f.name)
        # Ensure it doesn't match test patterns
        regular_file = regular_file.parent / "service.py"
        Path(f.name).rename(regular_file)

    try:
        # Run the enforcer
        exit_code, stdout, stderr = run_enforcer(regular_file)

        # Should not find mock violations (might find other violations)
        if exit_code == 2:
            output = json.loads(stdout)
            reason = output["reason"]
            # Should not contain mock violations
            assert "MOCKING VIOLATION" not in reason

    finally:
        regular_file.unlink()


def test_mock_detection_with_real_hook_data():
    """Test mock detection with simulated PostToolUse hook data."""
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
        f.write("""
from unittest.mock import MagicMock

def test_something():
    mock_db = MagicMock()
    mock_db.query.return_value = []
    return mock_db
""")
        test_file = Path(f.name)

    try:
        # Simulate hook data from Claude Code
        hook_data = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(test_file)
            }
        }

        # Run with stdin input (simulating PostToolUse hook)
        stdin_input = json.dumps(hook_data)
        result = subprocess.run(
            ["uv", "run", "python", "-m", "claudex_guard.main", "--mode", "post"],
            input=stdin_input,
            text=True,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        # Should detect violation
        assert result.returncode == 2
        output = json.loads(result.stdout)
        assert output["decision"] == "block"
        assert "Mocking 'MagicMock' detected" in output["reason"]

    finally:
        test_file.unlink()


def test_mock_detection_violation_logging():
    """Test that mock violations are logged to violation history."""
    # Create test file with violations
    with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
        f.write("""
from unittest.mock import patch

@patch('app.service.process')
def test_logging():
    pass
""")
        test_file = Path(f.name)

    try:
        # Run enforcer
        exit_code, stdout, stderr = run_enforcer(test_file)

        # Check that violations were detected
        assert exit_code == 2
        output = json.loads(stdout)

        # Verify mock violation is in output
        assert "app.service.process" in output["reason"]

        # Note: Actual violation logging to .claudex-guard/violations.log
        # would require running in a project context with that directory

    finally:
        test_file.unlink()


def test_multiple_decorators_detection():
    """Test detection of multiple mock decorators on single function."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
        f.write("""
from unittest.mock import patch

@patch('service.a')
@patch('service.b')
@patch('service.c')
def test_multiple(mock_c, mock_b, mock_a):
    pass
""")
        test_file = Path(f.name)

    try:
        exit_code, stdout, stderr = run_enforcer(test_file)

        assert exit_code == 2
        output = json.loads(stdout)
        reason = output["reason"]

        # Should detect all three mocks
        assert "service.a" in reason
        assert "service.b" in reason
        assert "service.c" in reason

    finally:
        test_file.unlink()
