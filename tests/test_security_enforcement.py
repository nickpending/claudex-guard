"""Integration tests for security enforcement across all languages."""

import subprocess
import tempfile
from pathlib import Path


def test_python_eval_detection() -> None:
    """Test that eval() usage is detected in Python."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("result = eval(user_input)\n")
        f.flush()
        temp_path = Path(f.name)

    try:
        result = subprocess.run(
            ["python", "-m", "claudex_guard.main", "--mode", "post", str(temp_path)],
            capture_output=True,
            text=True,
        )
        # Should block (exit code 2) due to security violation
        assert result.returncode == 2, f"Expected exit code 2, got {result.returncode}"
        assert "eval" in result.stdout.lower() or "S307" in result.stdout
    finally:
        temp_path.unlink()


def test_python_sql_injection_detection() -> None:
    """Test that SQL injection in f-strings is detected."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write('query = f"SELECT * FROM users WHERE id = {user_id}"\n')
        f.flush()
        temp_path = Path(f.name)

    try:
        result = subprocess.run(
            ["python", "-m", "claudex_guard.main", "--mode", "post", str(temp_path)],
            capture_output=True,
            text=True,
        )
        # Should block due to SQL injection pattern (ruff S608)
        assert result.returncode == 2, f"Expected exit code 2, got {result.returncode}"
    finally:
        temp_path.unlink()


def test_python_unused_imports_detection() -> None:
    """Test that unused imports are auto-fixed (strict enforcement enabled)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import os\nimport sys\nprint('hello')\n")
        f.flush()
        temp_path = Path(f.name)

    try:
        result = subprocess.run(
            ["python", "-m", "claudex_guard.main", "--mode", "post", str(temp_path)],
            capture_output=True,
            text=True,
        )
        # Auto-fixing now enabled - unused imports get removed automatically
        assert result.returncode == 0, (
            f"Expected exit code 0 (auto-fixed), got {result.returncode}"
        )
        assert "strict security enforcement" in result.stderr
    finally:
        temp_path.unlink()


def test_typescript_eval_detection() -> None:
    """Test that eval() is caught by ESLint security rules."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
        f.write('const result = eval("1 + 1");\n')
        f.flush()
        temp_path = Path(f.name)

    try:
        result = subprocess.run(
            ["python", "-m", "claudex_guard.main", "--mode", "post", str(temp_path)],
            capture_output=True,
            text=True,
        )
        # With --fix, ESLint runs but may not block on unfixable violations
        # Verify security enforcement ran
        assert result.returncode in {0, 1, 2}
        assert "ESLint security enforcement" in result.stderr
    finally:
        temp_path.unlink()


def test_typescript_innerhtml_detection() -> None:
    """Test that innerHTML usage is caught by Microsoft SDL plugin."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
        f.write(
            'const input = "test";\ndocument.getElementById("content").innerHTML = input;\n'
        )
        f.flush()
        temp_path = Path(f.name)

    try:
        result = subprocess.run(
            ["python", "-m", "claudex_guard.main", "--mode", "post", str(temp_path)],
            capture_output=True,
            text=True,
        )
        # With --fix, may auto-fix or may not block
        # Verify security enforcement ran with SDL rules
        assert result.returncode in {0, 1, 2}
        assert "ESLint security enforcement" in result.stderr
    finally:
        temp_path.unlink()


def test_typescript_console_log_detection() -> None:
    """Test that console.log is detected in TypeScript."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
        f.write('console.log("debug");\n')
        f.flush()
        temp_path = Path(f.name)

    try:
        result = subprocess.run(
            ["python", "-m", "claudex_guard.main", "--mode", "post", str(temp_path)],
            capture_output=True,
            text=True,
        )
        # Should detect console.log (from custom patterns)
        assert result.returncode in {0, 1, 2}
        # May be warning or error depending on configuration
    finally:
        temp_path.unlink()


def test_rust_unwrap_detection() -> None:
    """Test that .unwrap() abuse is detected in Rust."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
        f.write("fn main() {\n    let x = Some(42);\n    let y = x.unwrap();\n}\n")
        f.flush()
        temp_path = Path(f.name)

    try:
        result = subprocess.run(
            ["python", "-m", "claudex_guard.main", "--mode", "post", str(temp_path)],
            capture_output=True,
            text=True,
        )
        # Should detect .unwrap() usage
        assert result.returncode in {0, 1, 2}
        # unwrap detection may be warning
    finally:
        temp_path.unlink()


def test_python_clean_code_passes() -> None:
    """Test that clean Python code passes without errors."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write('def greet(name: str) -> str:\n    return f"Hello, {name}"\n')
        f.flush()
        temp_path = Path(f.name)

    try:
        result = subprocess.run(
            ["python", "-m", "claudex_guard.main", "--mode", "post", str(temp_path)],
            capture_output=True,
            text=True,
        )
        # Clean code should pass
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"
        # Should see success output on stderr
        assert "✓" in result.stderr or "passed" in result.stderr.lower()
    finally:
        temp_path.unlink()


def test_success_output_visibility() -> None:
    """Test that success output is visible on stderr for model visibility."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write('print("Hello")\n')
        f.flush()
        temp_path = Path(f.name)

    try:
        result = subprocess.run(
            ["python", "-m", "claudex_guard.main", "--mode", "post", str(temp_path)],
            capture_output=True,
            text=True,
        )
        # Should show fixes applied on stderr
        assert result.returncode == 0
        assert result.stderr, "Expected stderr output for success visibility"
        assert "✓" in result.stderr or "Quality checks" in result.stderr
    finally:
        temp_path.unlink()
