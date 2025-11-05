"""
Useful unit tests for core components.

Tests that actually catch bugs, not pointless matchy-match nonsense.
"""

import ast
import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from claudex_guard.core.base_enforcer import BaseEnforcer
from claudex_guard.core.violation import Violation, ViolationReporter
from claudex_guard.services.auto_fixer import PythonAutoFixer
from claudex_guard.standards.python_patterns import PythonPatterns


def test_banned_import_detection_actually_works() -> None:
    """Test that banned imports are actually caught, not just happy path."""
    patterns = PythonPatterns()

    # Test the import matching bug that was fixed
    code = "import requests\nimport pipeline_tool"  # pipeline should NOT match pip
    tree = ast.parse(code)
    violations = patterns.analyze_ast(tree, Path("test.py"))

    # Should catch requests but NOT pipeline_tool
    banned_violations = [v for v in violations if v.violation_type == "banned_import"]
    assert len(banned_violations) == 1
    assert "requests" in banned_violations[0].message
    assert "pipeline" not in str(violations)  # Should not flag pipeline_tool


def test_hook_context_extraction_fallback_chain() -> None:
    """Test that hook context extraction handles real Claude Code scenarios."""
    # Use PythonEnforcer instead of abstract BaseEnforcer
    from claudex_guard.enforcers.python import PythonEnforcer

    enforcer = PythonEnforcer()

    # Test primary method: stdin JSON with tool_input
    hook_data = {"tool_input": {"file_path": __file__}}
    with patch("sys.stdin", StringIO(json.dumps(hook_data))):
        file_path = enforcer.get_file_path_from_hook_context()
        assert file_path == Path(__file__)

    # Test fallback: stdin JSON with direct file_path
    hook_data = {"file_path": __file__}
    with patch("sys.stdin", StringIO(json.dumps(hook_data))):
        file_path = enforcer.get_file_path_from_hook_context()
        assert file_path == Path(__file__)

    # Test environment variable fallback
    with (
        patch("sys.stdin", StringIO("")),
        patch.dict("os.environ", {"CLAUDE_FILE_PATHS": __file__}),
    ):
        file_path = enforcer.get_file_path_from_hook_context()
        assert file_path == Path(__file__)


def test_global_reminder_deduplication() -> None:
    """Test that global reminders don't spam when multiple files have prints."""
    reporter = ViolationReporter("python")

    # Add same reminder multiple times (simulating multiple files)
    reminder_text = "💡 Consider logging for production code"
    reporter.add_global_reminder(reminder_text)
    reporter.add_global_reminder(reminder_text)
    reporter.add_global_reminder(reminder_text)

    # Should only store one copy (set deduplication)
    assert len(reporter.global_reminders) == 1
    assert reminder_text in reporter.global_reminders


def test_auto_fixer_handles_missing_tools_gracefully() -> None:
    """Test auto-fixer doesn't crash when ruff/mypy are missing."""
    fixer = PythonAutoFixer()

    # Create a temp file to test with
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def test(): pass")
        test_file = Path(f.name)

    try:
        # Should not crash even if tools fail
        fixes = fixer.apply_fixes(test_file)
        # Should return a list (even if empty due to missing tools)
        assert isinstance(fixes, list)
    finally:
        test_file.unlink()


def test_violation_severity_affects_exit_code() -> None:
    """Test that violation severity actually controls blocking behavior."""
    reporter = ViolationReporter("python")

    # Add warning - should not block
    warning = Violation("test.py", 1, "test", "Warning message", severity="warning")
    reporter.add_violation(warning)
    exit_code = reporter.report()
    assert exit_code == 0  # Should not block

    # Add error - should block
    reporter = ViolationReporter("python")  # Fresh reporter
    error = Violation("test.py", 1, "test", "Error message", severity="error")
    reporter.add_violation(error)

    # Capture stderr to avoid noise in test output
    with patch("sys.stderr", StringIO()):
        exit_code = reporter.report()
    assert exit_code == 2  # Should block


def test_ast_node_context_preservation() -> None:
    """Test that AST context is preserved for enhanced violations."""
    # Create violation with AST context
    code = "def test_func(): pass"
    tree = ast.parse(code)
    func_node = tree.body[0]

    violation = Violation.from_ast_node("test.py", func_node, "test", "Test message")

    # Should preserve AST context
    assert violation.ast_node == func_node
    assert violation.function_name == "test_func"
    assert violation.line_num == func_node.lineno


def test_factory_creates_python_enforcer_for_py_files() -> None:
    """Test factory method creates PythonEnforcer for .py files."""
    test_file = Path(__file__)  # This test file is .py
    enforcer = BaseEnforcer.create(test_file)

    # Should return a PythonEnforcer instance
    assert enforcer is not None
    assert enforcer.__class__.__name__ == "PythonEnforcer"
    assert enforcer.language == "python"


def test_factory_returns_none_for_unsupported_extensions() -> None:
    """Test factory returns None for unsupported file types."""
    import tempfile

    # Test various unsupported extensions
    unsupported_extensions = [".txt", ".md", ".json", ".yaml", ".xml", ""]

    for ext in unsupported_extensions:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            test_file = Path(f.name)

        try:
            enforcer = BaseEnforcer.create(test_file)
            assert enforcer is None, f"Expected None for {ext}, got {enforcer}"
        finally:
            test_file.unlink()


def test_run_for_file_returns_zero_for_unsupported_files() -> None:
    """Test run_for_file skips unsupported files gracefully."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("test content")
        test_file = Path(f.name)

    try:
        exit_code = BaseEnforcer.run_for_file(test_file)
        assert exit_code == 0, "Unsupported file should return 0 (no false blocking)"
    finally:
        test_file.unlink()


def test_factory_handles_case_insensitive_extensions() -> None:
    """Test factory handles uppercase extensions."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".PY", delete=False) as f:
        f.write("# test")
        test_file = Path(f.name)

    try:
        enforcer = BaseEnforcer.create(test_file)
        assert enforcer is not None, "Should handle .PY (uppercase)"
        assert enforcer.__class__.__name__ == "PythonEnforcer"
    finally:
        test_file.unlink()


if __name__ == "__main__":
    # Run the useful tests
    test_functions = [
        test_banned_import_detection_actually_works,
        test_hook_context_extraction_fallback_chain,
        test_global_reminder_deduplication,
        test_auto_fixer_handles_missing_tools_gracefully,
        test_violation_severity_affects_exit_code,
        test_ast_node_context_preservation,
        test_factory_creates_python_enforcer_for_py_files,
        test_factory_returns_none_for_unsupported_extensions,
        test_run_for_file_returns_zero_for_unsupported_files,
        test_factory_handles_case_insensitive_extensions,
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            print(f"✅ {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__}: {e}")
            failed += 1

    print(f"\n📊 Unit tests: {passed} passed, {failed} failed")

    if failed > 0:
        exit(1)
    else:
        print("🎉 All unit tests passed!")
