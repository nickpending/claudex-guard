# Python Development Preferences

# 🚨 CRITICAL: Virtual Environment Hell - READ THIS FIRST 🚨

## BEFORE DOING ANYTHING IN PYTHON PROJECTS:

**THE PROBLEM**: Python's environment system is a clusterfuck of conflicting tools. You'll import packages from wrong environments, get mysterious "module not found" errors, and waste hours debugging when the issue is just running commands in global Python.

🛑 NEVER DO THIS:
- Run `python` or `pip` directly without checking your environment
- Use `pip install` globally (you'll pollute your system)
- Mix virtualenv, conda, pipenv, and poetry in the same workflow
- Assume your terminal is in the right environment

✅ ALWAYS DO THIS:
- Use `uv` for ALL Python package management (10-100x faster than pip)
- Run `uv run python` instead of bare `python` commands
- Check `which python` and `which pip` when things seem broken
- Start new projects with `uv init project-name`

🔥 IF YOU FUCK THIS UP: You'll waste 30+ minutes debugging import errors, version conflicts, and package installation failures when you're just running commands in the wrong Python environment. Your production deployment will break because dev dependencies leak everywhere.

# 🚨 CRITICAL: Environment Switching Between Projects - READ THIS FIRST 🚨

## BEFORE SWITCHING BETWEEN PYTHON PROJECTS:

**THE PROBLEM**: uv creates `.venv` directories locally but doesn't auto-activate them. You'll run commands in the wrong environment and get mysterious "package not found" errors.

🛑 NEVER DO THIS:
- Run `python` or `pip` directly after `uv sync` (wrong environment)
- Switch between projects without checking environment
- Assume `uv add package` affects your global Python

✅ ALWAYS DO THIS:
- Use `uv run python` instead of bare `python` commands
- Run `uv run pytest` instead of `pytest` directly
- Check `which python` if things seem broken
- Use `uv sync` when switching to existing projects

🔥 IF YOU FUCK THIS UP: You'll waste 20+ minutes debugging package import failures when you're just running commands in the wrong Python environment.

## Developer Info
- Call me "Mate" in all interactions
- Python 3.13.5 (latest stable with JIT compilation and enhanced interpreter)
- uv 0.7.15 for package management (10-100x faster than pip)
- VS Code with Python extension for development

## Modern Python Stack (2025)

- **Package Management**: uv 0.7.15 (replaces pip, poetry, virtualenv, pyenv in one tool)
- **Testing**: pytest 8.3+ (industry standard, extensible plugin system)
- **Code Quality**: ruff 0.9+ (10x faster than pylint, includes formatting)
- **Type Checking**: mypy 1.15+ (catch bugs before runtime, better than pyright for large codebases)
- **Documentation**: mkdocs with material theme (cleaner than sphinx for most projects)
- **HTTP Requests**: httpx (async-first, modern replacement for requests)
- **Data Processing**: polars (10x faster than pandas for large datasets)

## 🚨 BANNED Legacy Libraries (DO NOT USE)

- **requests** → Use httpx (async-first, HTTP/2 support, cleaner API)
- **pip/pip-tools** → Use uv (10-100x faster, handles everything)
- **virtualenv/venv** → Use uv (automatic environment management)
- **setuptools directly** → Use pyproject.toml with uv
- **nose/unittest** → Use pytest (better fixtures, cleaner syntax)
- **pylint** → Use ruff (10x faster, includes formatting)

Migration: Run `uv init` in existing projects, then `uv add` for each requirement.

## Python Patterns I Prefer

**Always use f-strings** for string formatting (fastest, most readable):
```python
name = "world"
message = f"Hello, {name}!"  # Not .format() or %
```

**Use pathlib for file operations** (object-oriented, cross-platform):
```python
from pathlib import Path
config_file = Path("config") / "settings.json"  # Not os.path.join
```

**Type hints everywhere** (catch bugs early, better IDE support):
```python
def process_data(items: list[dict[str, Any]]) -> list[str]:
    return [item["name"] for item in items]
```

**Context managers for resources** (automatic cleanup):
```python
with open("file.txt") as f:  # Always use with statements
    content = f.read()
```

## My Workflow Standards

**Project Structure** (src/ layout prevents import issues):
```
my-project/
├── src/
│   └── my_project/
│       ├── __init__.py
│       └── main.py
├── tests/
├── pyproject.toml
└── README.md
```

**Daily Commands**:
- `uv run python -m my_project` - Run module safely
- `uv run pytest` - Run tests in correct environment  
- `uv add --group dev pytest black` - Add dev dependencies
- `uv sync` - Sync environment when switching projects
- `uv run ruff check .` - Lint code (fast)

**Dependency Groups** (keep production clean):
```toml
[dependency-groups]
dev = ["pytest", "black", "mypy"]
test = ["pytest-cov", "pytest-mock"]
```

## Environment Setup

**Python Installation**: Use uv to manage Python versions
```bash
uv python install 3.13  # Latest stable
uv python pin 3.13      # Pin for project
```

**New Project Setup**:
```bash
uv init my-project --python 3.13
cd my-project
uv add fastapi httpx polars  # Add dependencies
uv add --group dev pytest ruff mypy  # Dev tools
```

**VS Code Settings** (add to .vscode/settings.json):
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.terminal.activateEnvironment": false,
    "ruff.enable": true,
    "ruff.organizeImports": true
}
```

## My Code Review Standards

**Must Have**:
- Type hints on all public functions
- Docstrings for modules, classes, and public functions
- No bare `except:` clauses
- f-strings instead of .format() or %
- pathlib instead of os.path

**Performance Thresholds**:
- Functions >100ms need profiling comment
- Database queries must use connection pooling
- File operations must use context managers
- Large datasets require streaming/chunking

**Testing Requirements**:
- 80%+ test coverage (use `uv run pytest --cov`)
- Unit tests for business logic
- Integration tests for external dependencies
- Property-based testing for complex logic (use hypothesis)

## Quick Project Bootstrap

```bash
# New project from scratch
uv init my-project --python 3.13
cd my-project

# Add common dependencies
uv add httpx polars typer  # Core libraries
uv add --group dev pytest ruff mypy pytest-cov  # Dev tools
uv add --group test pytest-mock hypothesis  # Testing

# Setup project structure
mkdir -p src/my_project tests docs
touch src/my_project/__init__.py
touch tests/__init__.py

# Initialize git
git init
echo ".venv/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore

# Ready to code
uv run python -c "print('Hello, World!')"
```

## Python-Specific Gotchas to Avoid

**Mutable Default Arguments** (classic Python footgun):
```python
# 🛑 NEVER
def add_item(item, items=[]):  # Shared between calls!
    items.append(item)
    return items

# ✅ ALWAYS  
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

**Late Binding Closures** (lambda in loops):
```python
# 🛑 NEVER
funcs = [lambda: i for i in range(3)]  # All return 2!

# ✅ ALWAYS
funcs = [lambda x=i: x for i in range(3)]  # Capture variable
```

**Import from Current Directory** (Python 2 behavior):
```python
# 🛑 NEVER put scripts in package directories
# Python will import from local directory, not installed packages

# ✅ ALWAYS use src/ layout or run with -m flag
uv run python -m my_package.script
```

**Global Interpreter Lock (GIL)** confusion:
```python
# 🛑 NEVER use threading for CPU-bound tasks
import threading  # Only helps with I/O

# ✅ ALWAYS use multiprocessing for CPU work
import multiprocessing
# Or asyncio for I/O-bound tasks
import asyncio
```

## Preferred Debugging Tools

**Built-in Debugger** (no imports needed):
```python
breakpoint()  # Python 3.7+, better than pdb.set_trace()
```

**Rich for Beautiful Output** (10x better than print debugging):
```bash
uv add --group dev rich
```
```python
from rich import print
from rich.console import Console
console = Console()
console.print("Debug info", style="bold red")
```

**Icecream for Quick Debugging** (shows variable names):
```bash
uv add --group dev icecream
```
```python
from icecream import ic
ic(variable_name)  # Shows: variable_name: value
```

**Workflow Integration**:
- Use `uv run python -m pdb script.py` for command-line debugging
- Set up VS Code debugger with `.venv/bin/python` interpreter
- Add `--pdb` flag to pytest for test debugging: `uv run pytest --pdb`

## Documentation Standards

**Module Docstrings** (every module needs purpose):
```python
"""Utilities for processing customer data.

This module provides functions for cleaning, validating, and transforming
customer data from various sources.
"""
```

**Function Docstrings** (use Google style):
```python
def process_orders(orders: list[dict], min_amount: float = 0.0) -> list[dict]:
    """Process orders above minimum amount.
    
    Args:
        orders: List of order dictionaries with 'amount' key
        min_amount: Minimum order amount to include
        
    Returns:
        Filtered list of orders above minimum amount
        
    Raises:
        ValueError: If orders list is empty
    """
```

**README.md Template**:
```markdown
# Project Name

## Installation
```bash
uv sync
```

## Usage
```bash
uv run python -m project_name
```

## Development
```bash
uv run pytest  # Run tests
uv run ruff check .  # Lint
```

**API Documentation**: Use mkdocs with material theme, auto-generate from docstrings
