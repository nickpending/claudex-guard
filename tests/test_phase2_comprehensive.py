"""Test Phase 2 comprehensive coverage: documentation, security, testing, and environment patterns."""

import ast
from pathlib import Path

from claudex_guard.standards.python_patterns import PythonPatterns


def test_documentation_standards() -> None:
    """Test comprehensive documentation enforcement."""
    patterns = PythonPatterns()

    # Test missing module docstring
    module_code = """
import os
def some_function():
    pass
"""
    tree = ast.parse(module_code)
    violations = patterns.analyze_ast(tree, Path("test.py"))

    docstring_violations = [v for v in violations if "docstring" in v.violation_type]
    assert len(docstring_violations) >= 1, (
        "Should detect missing module/function docstrings"
    )
    print("✅ PASS - Documentation standards enforced")


def test_security_patterns_comprehensive() -> None:
    """Test comprehensive security pattern detection."""
    patterns = PythonPatterns()

    # Test SQL injection detection
    sql_injection_tests = [
        # F-string SQL injection
        'query = f"SELECT * FROM users WHERE id = {user_id}"',
        # % formatting SQL injection
        'query = "SELECT * FROM users WHERE name = %s" % user_name',
        # .format() SQL injection
        'query = "INSERT INTO users VALUES ({})".format(values)',
        # Pickle security
        "data = pickle.loads(untrusted_data)",
        # Subprocess shell injection
        'subprocess.run(["ls", "-la"], shell=True)',
        # compile() usage
        'code = compile(user_input, "string", "exec")',
    ]

    print("\n=== Testing Security Patterns ===")
    total_security_violations = 0

    for test_code in sql_injection_tests:
        try:
            tree = ast.parse(test_code)
            violations = patterns.analyze_ast(tree, Path("test.py"))
            security_violations = [
                v for v in violations if v.violation_type == "security_violation"
            ]

            if security_violations:
                print(f"✅ PASS - Detected security issue: {test_code[:50]}...")
                total_security_violations += len(security_violations)
            else:
                print(f"❌ FAIL - Missed security issue: {test_code[:50]}...")

        except SyntaxError:
            print(f"⚠️  SYNTAX ERROR - Skipping: {test_code}")
            continue

    assert total_security_violations >= 4, (
        f"Should detect at least 4 security violations, got {total_security_violations}"
    )
    print(
        f"🎉 Security patterns comprehensive test passed! ({total_security_violations} violations detected)"
    )


def test_testing_standards() -> None:
    """Test testing standards enforcement."""
    patterns = PythonPatterns()

    # Test file with improper test function naming
    test_code = """
def should_validate_user_input():  # Bad - missing test_ prefix
    assert True

def test_proper_naming():  # Good
    assert True
    
def _helper_function():  # Good - private function
    pass
"""

    lines = test_code.strip().split("\n")
    test_file_path = Path("tests/test_example.py")
    violations = patterns.analyze_patterns(lines, test_file_path)

    naming_violations = [
        v for v in violations if v.violation_type == "test_naming_convention"
    ]
    assert len(naming_violations) == 1, (
        f"Should detect 1 test naming violation, got {len(naming_violations)}"
    )
    assert "should_validate_user_input" in naming_violations[0].message
    print("✅ PASS - Test naming standards enforced")


def test_environment_variable_patterns() -> None:
    """Test environment variable handling patterns."""
    patterns = PythonPatterns()

    # Test direct os.environ access
    env_code = """
import os
# Bad - direct access without defaults
config = os.environ['DATABASE_URL']
# Bad - direct environ access
debug = os.environ.get('DEBUG', False)
"""

    tree = ast.parse(env_code)
    violations = patterns.analyze_ast(tree, Path("test.py"))

    env_violations = [v for v in violations if "environment" in v.violation_type]
    assert len(env_violations) >= 1, (
        "Should detect environment variable handling issues"
    )
    print("✅ PASS - Environment variable patterns enforced")


def test_comprehensive_phase2_integration() -> None:
    """Test comprehensive real-world code with all Phase 2 patterns."""
    patterns = PythonPatterns()

    # Comprehensive test code with all Phase 2 patterns
    comprehensive_code = """
import os
import pickle
import subprocess

class UserManager:  # Missing docstring
    def create_user(self, name, email):  # Missing docstring and type hints
        # SQL injection vulnerability
        query = f"INSERT INTO users (name, email) VALUES ('{name}', '{email}')"
        
        # Direct environment access
        db_url = os.environ['DATABASE_URL']
        
        # Pickle security issue
        user_data = pickle.loads(data_from_client)
        
        # Subprocess shell injection
        result = subprocess.run(f"echo {name}", shell=True)
        
        return query

def validate_input(data):  # Missing docstring and type hints
    # Path traversal risk
    file_path = os.path.join("uploads", data["filename"])
    return file_path
"""

    tree = ast.parse(comprehensive_code)
    violations = patterns.analyze_ast(tree, Path("comprehensive_test.py"))

    # Expected Phase 2 violation types
    expected_violations = {
        "missing_module_docstring": 1,  # Module missing docstring
        "missing_docstring": 2,  # Class and function missing docstrings
        "missing_type_hints": 2,  # Functions missing type hints
        "security_violation": 4,  # SQL injection, pickle, subprocess, path traversal
        "environment_variable_handling": 1,  # Direct os.environ access
    }

    print("\n=== Comprehensive Phase 2 Integration Test ===")
    violation_counts = {}
    for violation in violations:
        vtype = violation.violation_type
        violation_counts[vtype] = violation_counts.get(vtype, 0) + 1

    print(f"Total violations found: {len(violations)}")

    # Debug: show all violations
    for violation in violations:
        print(f"  - {violation.violation_type}: {violation.message[:60]}...")

    all_passed = True
    for vtype, expected_count in expected_violations.items():
        actual_count = violation_counts.get(vtype, 0)
        status = "✅ PASS" if actual_count >= expected_count else "❌ FAIL"
        print(f"{status} {vtype}: {actual_count}/{expected_count}")

        if actual_count < expected_count:
            all_passed = False

    assert all_passed, "Phase 2 comprehensive integration test failed"
    print("🎉 Phase 2 comprehensive integration test passed!")


if __name__ == "__main__":
    print("Testing Phase 2 Comprehensive Coverage...")

    test_documentation_standards()
    test_security_patterns_comprehensive()
    test_testing_standards()
    test_environment_variable_patterns()
    test_comprehensive_phase2_integration()

    print("\n🚀 All Phase 2 comprehensive tests passed!")
