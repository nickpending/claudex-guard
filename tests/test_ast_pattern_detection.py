"""Test AST-based pattern detection accuracy against real-world false positive cases."""

import ast
from pathlib import Path

from claudex_guard.standards.python_patterns import PythonPatterns


def test_ast_string_formatting_detection():
    """Test AST detection of string % formatting vs legitimate % usage."""
    patterns = PythonPatterns()

    # Test cases from real-world false positives
    test_cases = [
        # Should detect (actual % formatting that should use f-strings)
        ('result = "Hello %s" % name', True, "String % formatting"),
        ('message = "Value: %d, Name: %s" % (count, name)', True, "Tuple % formatting"),
        ('template = "Processing %s" % item', True, "Simple % formatting"),
        # Should NOT detect (legitimate % usage)
        (
            'datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")',
            False,
            "Datetime format string",
        ),
        ('"%(title)s.%(ext)s"', False, "Template string (no % operator)"),
        (
            'logging.info("Processing %s", item)',
            False,
            "Logging format (no % operator)",
        ),
        ('command = "ffmpeg -i input.%s -o output.%s"', False, "Template string only"),
        ('format_str = "%Y-%m-%d"', False, "Format string constant"),
        # Edge cases
        ('percent = "100%"', False, "Literal percent symbol"),
        ('regex = r"%s+"', False, "Raw string with %"),
        ('f"Value: {item}"', False, "F-string (already modern)"),
    ]

    for code, should_detect, description in test_cases:
        print(f"\nTesting: {description}")
        print(f"Code: {code}")

        try:
            tree = ast.parse(code)
            violations = patterns.analyze_ast(tree, Path("test.py"))

            # Filter for string formatting violations
            formatting_violations = [
                v for v in violations if v.violation_type == "old_string_formatting"
            ]

            detected = len(formatting_violations) > 0

            if detected == should_detect:
                print(f"✅ PASS - Detection: {detected} (expected: {should_detect})")
            else:
                print(f"❌ FAIL - Detection: {detected} (expected: {should_detect})")
                if formatting_violations:
                    print(f"   Violation: {formatting_violations[0].message}")

                # This is a critical test failure
                assert False, f"AST detection failed for: {description}"

        except SyntaxError:
            print(f"⚠️  SYNTAX ERROR - Skipping: {code}")
            continue


def test_real_world_false_positive_cases():
    """Test specific cases that caused false positives in real projects."""
    patterns = PythonPatterns()

    # Real code that was falsely flagged
    real_world_cases = [
        # YouTube-dl style format strings (should NOT be flagged)
        """
def extract_info(self):
    output_template = "%(title)s.%(ext)s"
    return output_template
        """,
        # Datetime parsing (should NOT be flagged)
        """
import datetime
def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        """,
        # Logging format strings (should NOT be flagged)
        """
import logging
def process_item(item):
    logging.info("Processing %s", item)
    return item
        """,
        # Actual string formatting that SHOULD be flagged
        """
def bad_formatting(name, age):
    return "Hello %s, you are %d years old" % (name, age)
        """,
    ]

    expected_detections = [
        False,
        False,
        False,
        True,
    ]  # Only last case should be detected

    for i, (code, should_detect) in enumerate(
        zip(real_world_cases, expected_detections)
    ):
        print(f"\n=== Real World Case {i + 1} ===")
        print(f"Should detect: {should_detect}")

        try:
            tree = ast.parse(code)
            violations = patterns.analyze_ast(tree, Path("test.py"))

            # Filter for string formatting violations
            formatting_violations = [
                v for v in violations if v.violation_type == "old_string_formatting"
            ]

            detected = len(formatting_violations) > 0

            if detected == should_detect:
                print("✅ PASS - Real world case detection correct")
            else:
                print("❌ FAIL - Real world case detection wrong")
                print(f"   Expected: {should_detect}, Got: {detected}")
                if formatting_violations:
                    for v in formatting_violations:
                        print(f"   Violation: {v.message} (line {v.line_num})")

                # This is a critical failure
                assert False, f"Real world case {i + 1} failed detection test"

        except SyntaxError as e:
            print(f"⚠️  SYNTAX ERROR: {e}")
            continue


def test_ast_performance_vs_regex():
    """Basic performance check to ensure AST analysis isn't too slow."""
    import time

    patterns = PythonPatterns()

    # Sample code with various patterns
    test_code = '''
import datetime
import logging

def process_data(items, format_str="%Y-%m-%d"):
    """Process data with various formatting approaches."""
    # Old formatting (should be detected)
    message = "Processing %d items" % len(items)
    
    # Template strings (should NOT be detected)
    template = "%(name)s_%(id)s.txt"
    
    # Datetime formatting (should NOT be detected)
    date = datetime.strptime("2025-01-01", "%Y-%m-%d")
    
    # Logging (should NOT be detected)
    logging.info("Found %d items", len(items))
    
    return message
    '''

    # Time the AST analysis
    start_time = time.time()

    for _ in range(100):  # Run 100 times to get meaningful timing
        tree = ast.parse(test_code)
        violations = patterns.analyze_ast(tree, Path("test.py"))

    end_time = time.time()
    avg_time_ms = (end_time - start_time) * 1000 / 100

    print("\n=== Performance Test ===")
    print(f"Average AST analysis time: {avg_time_ms:.2f}ms")
    print("Target: <50ms per analysis")

    # Should be very fast for hook integration
    assert avg_time_ms < 50, f"AST analysis too slow: {avg_time_ms:.2f}ms"

    print("✅ PASS - Performance within acceptable limits")


if __name__ == "__main__":
    print("Testing AST-based pattern detection accuracy...")

    test_ast_string_formatting_detection()
    test_real_world_false_positive_cases()
    test_ast_performance_vs_regex()

    print("\n🎉 All AST pattern detection tests passed!")
