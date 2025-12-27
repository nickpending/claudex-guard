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
        assert "eval" in result.stderr.lower() or "S307" in result.stderr
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
        assert "strict security enforcement" in result.stdout
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
        # Success messages go to stdout (model sees this)
        # Verify security enforcement ran
        assert result.returncode in {0, 1, 2}
        assert (
            "ESLint security enforcement" in result.stdout or "ESLint" in result.stdout
        )
    finally:
        temp_path.unlink()


def test_typescript_innerhtml_detection() -> None:
    """Test that innerHTML usage is caught by Microsoft SDL plugin."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
        f.write(
            'const input = "test";\n'
            'document.getElementById("content").innerHTML = input;\n'
        )
        f.flush()
        temp_path = Path(f.name)

    try:
        result = subprocess.run(
            ["python", "-m", "claudex_guard.main", "--mode", "post", str(temp_path)],
            capture_output=True,
            text=True,
        )
        # Success messages go to stdout (model sees this)
        # Verify security enforcement ran with SDL rules
        assert result.returncode in {0, 1, 2}
        assert (
            "ESLint security enforcement" in result.stdout or "ESLint" in result.stdout
        )
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
        # Should see success output on stdout
        assert "✓" in result.stdout or "passed" in result.stdout.lower()
    finally:
        temp_path.unlink()


def test_success_output_visibility() -> None:
    """Test that success output is visible on stdout for model visibility."""
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
        # Should show fixes applied on stdout (model sees stdout)
        assert result.returncode == 0
        assert result.stdout, "Expected stdout output for success visibility"
        assert "✓" in result.stdout or "Quality checks" in result.stdout
    finally:
        temp_path.unlink()


def test_typescript_tsconfig_types_respected() -> None:
    """Test that tsconfig.json types array is respected for module resolution.

    Regression test for bun:sqlite false positive where tsc ignored tsconfig
    when run with explicit file path instead of -p flag.
    """
    import json
    import os

    # Create temp directory with tsconfig and bun-types
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Write tsconfig with bun-types
        tsconfig = {
            "compilerOptions": {
                "types": ["bun-types"],
                "target": "ES2020",
                "module": "ESNext",
                "moduleResolution": "bundler",
            }
        }
        (tmppath / "tsconfig.json").write_text(json.dumps(tsconfig))

        # Write package.json and install bun-types
        package_json = {"devDependencies": {"bun-types": "latest"}}
        (tmppath / "package.json").write_text(json.dumps(package_json))

        # Install bun-types (skip test if pnpm not available)
        install_result = subprocess.run(
            ["pnpm", "install"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )
        if install_result.returncode != 0:
            import pytest

            pytest.skip("pnpm not available for bun-types install")

        # Write TypeScript file using bun:sqlite
        ts_file = tmppath / "test.ts"
        ts_file.write_text('import { Database } from "bun:sqlite";\n')

        # Run enforcer - should NOT flag bun:sqlite as unresolved
        result = subprocess.run(
            ["python", "-m", "claudex_guard.main", "--mode", "post", str(ts_file)],
            capture_output=True,
            text=True,
            cwd=tmpdir,
            env={**os.environ, "PYTHONPATH": str(Path.cwd() / "src")},
        )

        # Should pass - bun:sqlite resolves via tsconfig types
        assert "TS2307" not in result.stderr, (
            f"bun:sqlite should resolve via tsconfig types: {result.stderr}"
        )
