"""Test mock detection functionality."""

import ast
from pathlib import Path

from claudex_guard.standards.python_patterns import PythonPatterns


def test_mock_patch_decorator_detection():
    """Test that @mock.patch decorators are detected in test files."""
    patterns = PythonPatterns()

    # Test code with mock.patch decorator
    test_code = '''
import unittest.mock as mock

@mock.patch('requests.post')
def test_api_call(mock_post):
    mock_post.return_value = {'status': 'ok'}
    result = make_api_call()
    assert result['status'] == 'ok'
'''

    # Parse and analyze
    tree = ast.parse(test_code)
    test_file = Path("test_api.py")  # Test file name
    violations = patterns.analyze_ast(tree, test_file)

    # Should find mock violation in strict mode
    mock_violations = [v for v in violations if v.violation_type == "mock_violation"]
    assert len(mock_violations) == 1
    assert "requests.post" in mock_violations[0].message
    assert "Don't Mock What You Don't Own" in mock_violations[0].fix_suggestion


def test_mock_constructor_detection():
    """Test that Mock() and MagicMock() constructors are detected."""
    patterns = PythonPatterns()

    test_code = '''
from unittest.mock import Mock, MagicMock

def test_something():
    mock_service = Mock()
    mock_db = MagicMock()
    mock_service.process()
    mock_db.query()
'''

    tree = ast.parse(test_code)
    test_file = Path("test_service.py")
    violations = patterns.analyze_ast(tree, test_file)

    mock_violations = [v for v in violations if v.violation_type == "mock_violation"]
    assert len(mock_violations) == 2  # Mock() and MagicMock()


def test_non_test_file_no_detection():
    """Test that mock detection doesn't trigger in non-test files."""
    patterns = PythonPatterns()

    # Same code but in a non-test file
    code = '''
from unittest.mock import Mock

def setup_testing():
    mock_service = Mock()
    return mock_service
'''

    tree = ast.parse(code)
    regular_file = Path("service.py")  # Not a test file
    violations = patterns.analyze_ast(tree, regular_file)

    # Should not detect mocks in non-test files
    mock_violations = [v for v in violations if v.violation_type == "mock_violation"]
    assert len(mock_violations) == 0


def test_patch_without_mock_prefix():
    """Test detection of @patch decorator without mock prefix."""
    patterns = PythonPatterns()

    test_code = '''
from unittest.mock import patch

@patch('app.database.get_user')
def test_user_fetch(mock_get_user):
    mock_get_user.return_value = {'id': 1, 'name': 'Test'}
    user = fetch_user(1)
    assert user['name'] == 'Test'
'''

    tree = ast.parse(test_code)
    test_file = Path("test_database.py")
    violations = patterns.analyze_ast(tree, test_file)

    mock_violations = [v for v in violations if v.violation_type == "mock_violation"]
    assert len(mock_violations) == 1
    assert "app.database.get_user" in mock_violations[0].message


def test_allowed_patterns_from_config():
    """Test that allowed patterns from config are not flagged."""
    patterns = PythonPatterns()

    # Simulate allowed patterns (would normally come from .claudex-guard.yaml)
    patterns.ALLOWED_MOCK_PATTERNS = ["requests.*", "stripe.*"]

    test_code = '''
from unittest.mock import patch

@patch('requests.post')  # Should be allowed
@patch('stripe.Customer.create')  # Should be allowed
@patch('app.service.process')  # Should be blocked
def test_external_apis(mock_requests, mock_stripe, mock_service):
    pass
'''

    tree = ast.parse(test_code)
    test_file = Path("test_external.py")
    violations = patterns.analyze_ast(tree, test_file)

    mock_violations = [v for v in violations if v.violation_type == "mock_violation"]
    # Only app.service.process should be flagged
    assert len(mock_violations) == 1
    assert "app.service.process" in mock_violations[0].message


def test_mock_violation_message_quality():
    """Test that mock violation messages are helpful."""
    patterns = PythonPatterns()

    test_code = '''
from unittest.mock import patch

@patch('database.query')
def test_query(mock_query):
    pass
'''

    tree = ast.parse(test_code)
    test_file = Path("test_db.py")
    violations = patterns.analyze_ast(tree, test_file)

    mock_violations = [v for v in violations if v.violation_type == "mock_violation"]
    assert len(mock_violations) == 1

    violation = mock_violations[0]
    # Check for helpful content in the suggestion
    assert "Don't Mock What You Don't Own" in violation.fix_suggestion
    assert "wrapper/adapter" in violation.fix_suggestion
    assert "claudex-guard: allow-mock" in violation.fix_suggestion
    assert ".claudex-guard.yaml" in violation.fix_suggestion


def test_multiple_test_file_patterns():
    """Test various test file naming patterns are recognized."""
    patterns = PythonPatterns()

    test_code = '''
from unittest.mock import Mock

def test_func():
    m = Mock()
'''

    tree = ast.parse(test_code)

    # Test various test file patterns
    test_patterns = [
        Path("test_something.py"),
        Path("something_test.py"),
        Path("tests/test_module.py"),
        Path("src/tests/test_feature.py"),
        Path("test/test_unit.py"),
    ]

    for test_file in test_patterns:
        violations = patterns.analyze_ast(tree, test_file)
        mock_violations = [
            v for v in violations if v.violation_type == "mock_violation"
        ]
        assert len(mock_violations) == 1, f"Failed for pattern: {test_file}"

    # Non-test files should not trigger
    non_test_patterns = [
        Path("service.py"),
        Path("utils_test_helpers.py"),  # Has 'test' in middle, not a test file
        Path("testing_helpers.py"),
    ]

    for non_test_file in non_test_patterns:
        violations = patterns.analyze_ast(tree, non_test_file)
        mock_violations = [
            v for v in violations if v.violation_type == "mock_violation"
        ]
        assert len(mock_violations) == 0, f"False positive for: {non_test_file}"
