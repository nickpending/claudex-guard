#!/usr/bin/env python3
"""
Test file with syntax errors for hook integration testing.

This file contains intentional syntax errors to test how
claudex-guard-python handles unparseable files.
"""

def broken_function(
    # Missing closing parenthesis - syntax error

def another_broken():
    if True
        # Missing colon - syntax error
        pass

# Invalid indentation
  def bad_indent():
      pass

# Unclosed string
message = "This string is not closed

if __name__ == "__main__":
    print("This will not run due to syntax errors")