#!/usr/bin/env python3

import requests  # Banned import - should use httpx


def bad_function(items=[]):  # Mutable default argument
    """Function with multiple violations."""
    result = "Hello %s!" % "world"  # Old string formatting
    return result


def another_bad_function():
    """Function with bare except clause."""
    try:
        data = requests.get("https://api.example.com")
        return data.json()
    except:  # Bare except clause
        pass


def security_violations():
    """Functions with security issues."""
    import os
    
    # Security violations
    user_input = "malicious code"
    result = eval(user_input)  # Security risk
    exec("print('hello')")     # Security risk
    
    # Environment violations
    os.system("pip install requests")  # Should use uv
    
    # Path handling
    file_path = os.path.join("data", "file.txt")  # Should use pathlib
    
    return result


def type_hint_violations(x, y):  # Missing type hints
    """Function missing return type hint."""
    # Debug pattern
    print("Debugging something")  # Should use rich.print()
    
    # Old formatting
    message = "Hello {}!".format("world")  # Should use f-strings
    
    return x + y


if __name__ == "__main__":
    print("Running test file with violations")
    bad_function()
    another_bad_function()
    security_violations()
    type_hint_violations(1, 2)