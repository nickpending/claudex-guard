"""Test Phase 1 standards coverage: comprehensive enforcement of modern Python patterns."""

import ast
from pathlib import Path

from claudex_guard.standards.python_patterns import PythonPatterns


def test_expanded_banned_imports() -> None:
    """Test all banned legacy libraries are detected."""
    patterns = PythonPatterns()

    # Test comprehensive banned imports
    banned_import_tests = [
        # HTTP Libraries
        ("import requests", "requests"),
        ("import urllib.parse", "urllib"),
        # Package Management
        ("import pip", "pip"),
        ("import poetry", "poetry"),
        ("import pipenv", "pipenv"),
        ("import conda", "conda"),
        # Code Quality Tools
        ("import pylint", "pylint"),
        ("import flake8", "flake8"),
        ("import black", "black"),
        ("import isort", "isort"),
        # Data Processing
        ("import pandas", "pandas"),
        # Testing
        ("import unittest", "unittest"),
        ("import nose", "nose"),
    ]

    print("=== Testing Expanded Banned Imports ===")
    for code, expected_banned in banned_import_tests:
        tree = ast.parse(code)
        violations = patterns.analyze_ast(tree, Path("test.py"))

        banned_violations = [
            v for v in violations if v.violation_type == "banned_import"
        ]

        if banned_violations:
            print(f"✅ PASS - Detected banned import: {expected_banned}")
            assert expected_banned in banned_violations[0].message
        else:
            print(f"❌ FAIL - Missed banned import: {expected_banned}")
            assert False, f"Failed to detect banned import: {expected_banned}"


def test_modern_type_hints_comprehensive() -> None:
    """Test comprehensive Python 3.9+ type hints enforcement."""
    patterns = PythonPatterns()

    # Test all old typing patterns
    old_typing_tests = [
        # Basic types
        ("from typing import List; items: List[str] = []", "List"),
        ("from typing import Dict; data: Dict[str, int] = {}", "Dict"),
        ("from typing import Set; unique: Set[int] = set()", "Set"),
        ("from typing import Tuple; coords: Tuple[int, int] = (0, 0)", "Tuple"),
        # Collections types
        ("from typing import FrozenSet; fs: FrozenSet[str]", "FrozenSet"),
        ("from typing import Deque; dq: Deque[int]", "Deque"),
        ("from typing import DefaultDict; dd: DefaultDict[str, list]", "DefaultDict"),
        ("from typing import OrderedDict; od: OrderedDict[str, int]", "OrderedDict"),
        ("from typing import Counter; c: Counter[str]", "Counter"),
        ("from typing import ChainMap; cm: ChainMap[str, int]", "ChainMap"),
        # Union types (Python 3.10+)
        ("from typing import Union; value: Union[str, int]", "Union"),
        ("from typing import Optional; maybe: Optional[str]", "Optional"),
    ]

    print("\n=== Testing Modern Type Hints ===")
    for code, expected_type in old_typing_tests:
        tree = ast.parse(code)
        violations = patterns.analyze_ast(tree, Path("test.py"))

        type_violations = [
            v for v in violations if v.violation_type == "old_type_hints"
        ]

        if type_violations:
            print(f"✅ PASS - Detected old type hint: typing.{expected_type}")
            assert expected_type in type_violations[0].language_context["old_type"]
        else:
            print(f"❌ FAIL - Missed old type hint: typing.{expected_type}")
            assert False, f"Failed to detect old type hint: typing.{expected_type}"


def test_python_gotchas_detection() -> None:
    """Test Python-specific gotchas are detected."""
    patterns = PythonPatterns()

    # Test identity comparison gotchas
    identity_tests = [
        ("if x is 1000: pass", "integer"),  # Large integer
        ("if name is 'hello': pass", "string"),  # String comparison
        ("if value is 3.14: pass", "float"),  # Float comparison
    ]

    print("\n=== Testing Python Gotchas ===")
    for code, value_type in identity_tests:
        tree = ast.parse(code)
        violations = patterns.analyze_ast(tree, Path("test.py"))

        identity_violations = [
            v for v in violations if v.violation_type == "identity_comparison_gotcha"
        ]

        if identity_violations:
            print(f"✅ PASS - Detected {value_type} identity comparison gotcha")
            assert value_type in identity_violations[0].language_context["pattern"]
        else:
            print(f"❌ FAIL - Missed {value_type} identity comparison gotcha")
            assert False, f"Failed to detect {value_type} identity comparison gotcha"

    # Test GIL confusion
    threading_code = "import threading"
    tree = ast.parse(threading_code)
    violations = patterns.analyze_ast(tree, Path("test.py"))

    gil_violations = [v for v in violations if v.violation_type == "gil_confusion"]
    if gil_violations:
        print("✅ PASS - Detected GIL confusion (threading import)")
    else:
        print("❌ FAIL - Missed GIL confusion detection")
        assert False, "Failed to detect GIL confusion"


def test_modern_features_detection() -> None:
    """Test Python 3.13+ modern features suggestions."""
    patterns = PythonPatterns()

    # Test dataclass opportunity
    dataclass_code = """
class Person:
    def __init__(self, name, age, email):
        self.name = name
        self.age = age  
        self.email = email
    """

    tree = ast.parse(dataclass_code)
    violations = patterns.analyze_ast(tree, Path("test.py"))

    dataclass_violations = [
        v for v in violations if v.violation_type == "dataclass_opportunity"
    ]
    if dataclass_violations:
        print("\n=== Testing Modern Features ===")
        print("✅ PASS - Detected dataclass opportunity")
        assert "Person" in dataclass_violations[0].message
    else:
        print("❌ FAIL - Missed dataclass opportunity")
        assert False, "Failed to detect dataclass opportunity"

    # Test enum opportunity
    enum_code = """
class Status:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected" 
    CANCELLED = "cancelled"
    """

    tree = ast.parse(enum_code)
    violations = patterns.analyze_ast(tree, Path("test.py"))

    enum_violations = [v for v in violations if v.violation_type == "enum_opportunity"]
    if enum_violations:
        print("✅ PASS - Detected enum opportunity")
        assert "Status" in enum_violations[0].message
    else:
        print("❌ FAIL - Missed enum opportunity")
        assert False, "Failed to detect enum opportunity"

    # Test match/case opportunity
    match_case_code = """
if status == "pending":
    handle_pending()
elif status == "approved":
    handle_approved()
elif status == "rejected":
    handle_rejected()
elif status == "cancelled":
    handle_cancelled()
else:
    handle_unknown()
    """

    tree = ast.parse(match_case_code)
    violations = patterns.analyze_ast(tree, Path("test.py"))

    match_violations = [
        v for v in violations if v.violation_type == "match_case_opportunity"
    ]
    if match_violations:
        print("✅ PASS - Detected match/case opportunity")
        assert "4 conditions" in match_violations[0].message
    else:
        print("❌ FAIL - Missed match/case opportunity")
        assert False, "Failed to detect match/case opportunity"


def test_comprehensive_phase1_coverage() -> None:
    """Test comprehensive real-world code with Phase 1 patterns."""
    patterns = PythonPatterns()

    # Comprehensive test code with all Phase 1 patterns
    comprehensive_code = """
import requests  # Should be banned
import pandas as pd  # Should be banned  
import pylint  # Should be banned
import threading  # Should trigger GIL warning
from typing import List, Dict, Union, Optional  # Should suggest modern types

def old_style_function(items: List[str]) -> Dict[str, int]:  # Old types
    result = {}
    for item in items:
        if item is "special":  # Identity comparison gotcha
            result[item] = 1000
        elif item is 999:  # Large integer identity
            result[item] = 2000
    return result

class Person:  # Could use dataclass
    def __init__(self, name, age, email):
        self.name = name
        self.age = age
        self.email = email

class Status:  # Could use enum
    PENDING = "pending"
    APPROVED = "approved" 
    REJECTED = "rejected"
    CANCELLED = "cancelled"

def process_status(status):  # Could use match/case
    if status == "pending":
        return "waiting"
    elif status == "approved":
        return "done"
    elif status == "rejected":
        return "failed"
    elif status == "cancelled":
        return "stopped"
    else:
        return "unknown"
    """

    tree = ast.parse(comprehensive_code)
    violations = patterns.analyze_ast(tree, Path("comprehensive_test.py"))

    # Expected violation types from Phase 1
    expected_violations = {
        "banned_import": 3,  # requests, pandas, pylint
        "gil_confusion": 1,  # threading import
        "old_type_hints": 4,  # List, Dict, Union, Optional
        "identity_comparison_gotcha": 2,  # string and integer 'is'
        "dataclass_opportunity": 1,  # Person class
        "enum_opportunity": 1,  # Status class
        "match_case_opportunity": 1,  # process_status function
    }

    print("\n=== Comprehensive Phase 1 Coverage Test ===")
    violation_counts = {}
    for violation in violations:
        vtype = violation.violation_type
        violation_counts[vtype] = violation_counts.get(vtype, 0) + 1

    print(f"Total violations found: {len(violations)}")

    all_passed = True
    for vtype, expected_count in expected_violations.items():
        actual_count = violation_counts.get(vtype, 0)
        status = "✅ PASS" if actual_count >= expected_count else "❌ FAIL"
        print(f"{status} {vtype}: {actual_count}/{expected_count}")

        if actual_count < expected_count:
            all_passed = False

    assert all_passed, "Phase 1 comprehensive coverage test failed"
    print("🎉 Phase 1 comprehensive coverage test passed!")


if __name__ == "__main__":
    print("Testing Phase 1 Standards Coverage...")

    test_expanded_banned_imports()
    test_modern_type_hints_comprehensive()
    test_python_gotchas_detection()
    test_modern_features_detection()
    test_comprehensive_phase1_coverage()

    print("\n🚀 All Phase 1 standards coverage tests passed!")
