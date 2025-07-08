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

from claudex_guard.core.violation import Violation, ViolationReporter
from claudex_guard.services.auto_fixer import PythonAutoFixer
from claudex_guard.standards.python_patterns import PythonPatterns


def test_banned_import_detection_actually_works():
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


def test_mutable_default_argument_detection():
    """Test that mutable default detection catches the actual Python gotcha."""
    patterns = PythonPatterns()

    # This is the actual bug pattern that causes runtime issues
    code = """
def bad_function(items=[]):  # This shares state between calls!
    items.append("new")
    return items

def good_function(items=None):  # This is safe
    if items is None:
        items = []
    return items
"""
    tree = ast.parse(code)
    violations = patterns.analyze_ast(tree, Path("test.py"))

    mutable_violations = [
        v for v in violations if v.violation_type == "mutable_default"
    ]
    assert len(mutable_violations) == 1
    assert "bad_function" in mutable_violations[0].message


def test_hook_context_extraction_fallback_chain():
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


def test_global_reminder_deduplication():
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


def test_auto_fixer_handles_missing_tools_gracefully():
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


def test_violation_severity_affects_exit_code():
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


def test_ast_node_context_preservation():
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


if __name__ == "__main__":
    # Run the useful tests
    test_functions = [
        test_banned_import_detection_actually_works,
        test_mutable_default_argument_detection,
        test_hook_context_extraction_fallback_chain,
        test_global_reminder_deduplication,
        test_auto_fixer_handles_missing_tools_gracefully,
        test_violation_severity_affects_exit_code,
        test_ast_node_context_preservation,
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
