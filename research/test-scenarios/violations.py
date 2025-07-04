#!/usr/bin/env python3
"""
Test file with known violations for hook integration testing.

This file contains intentional violations to test claudex-guard-python
detection capabilities and hook integration behavior.
"""


# Mutable default argument (classic Python gotcha)
def bad_function(items=[]):
    items.append("bad")
    return items


# Missing type hints
def another_function(x, y):
    return x + y


# Old string formatting
def format_message(name):
    return "Hello %s" % name  # Should suggest f-strings


# Bare except clause
def risky_operation():
    try:
        result = 1 / 0
    except:  # Bare except - violation
        pass


# eval usage (security violation)
def dangerous_eval(code):
    return eval(code)  # Security violation


# No pathlib usage but file operations
def read_config():
    with open("config.txt") as f:  # Should suggest pathlib
        return f.read()


# Threading for CPU work (antipattern)


def cpu_work():
    # Should suggest multiprocessing
    pass


# Old-style type hints
from typing import Dict, List


def process_data(items: List[str]) -> Dict[str, int]:
    # Should use built-in list, dict in Python 3.9+
    return {item: len(item) for item in items}


# Print debugging (should suggest rich.print or icecream)
def debug_function():
    print("Debug output")
    return True


if __name__ == "__main__":
    print("Test file with violations")
