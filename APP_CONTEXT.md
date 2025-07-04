# claudex-guard Application Context

**Project Type**: Python CLI Tool & Code Quality Enforcement System  
**Tech Stack**: Python 3.9-3.13, AST Analysis, Claude Code Integration  
**Generated**: 2025-07-03  
**Version**: 0.1.0

## Table of Contents

1. [Application Overview](#application-overview)
2. [Architecture & Design](#architecture--design)
3. [Codebase Navigation](#codebase-navigation)
4. [Core Functionality](#core-functionality)
5. [Development Setup](#development-setup)
6. [Usage Patterns](#usage-patterns)
7. [Integration Details](#integration-details)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)

---

## Application Overview

### Purpose
claudex-guard is an automated code quality enforcement system designed specifically for AI-assisted development workflows. It provides real-time code quality enforcement integrated with AI coding assistants like Claude Code, eliminating the need to repeatedly explain coding standards to AI assistants.

### Key Value Proposition
- **Real-time Quality Enforcement**: Immediate feedback during coding without breaking flow
- **AI Integration**: Seamless integration with Claude Code hooks to teach AI assistants your preferences
- **Standards-Based**: Built on systematic development standards from the claudex philosophy
- **Automatic Fixes**: Integration with ruff for formatting and linting
- **Sophisticated Analysis**: Goes beyond basic linting to validate development philosophy and workflow patterns

### Current Status
- ✅ **Python Enforcement**: Full modular implementation (661→89 lines, 87% reduction)
- ✅ **Global Reminder System**: Soft violations for better UX
- ✅ **Comprehensive Testing**: Integration + unit tests (15/15 passing)
- ✅ **Standards Integration**: References ~/.claudex/standards/claudex-python.md
- 📋 **JavaScript/TypeScript**: Ready for BaseEnforcer implementation
- 📋 **Rust**: Ready for BaseEnforcer implementation  
- 📋 **Go**: Ready for BaseEnforcer implementation

### Architecture Achievements (2025-07-04)
- **87% Code Reduction**: Monolithic 661 lines → Modular 89 lines
- **Composition Over Inheritance**: Clean BaseEnforcer + component architecture
- **Enhanced Testing**: 8 integration tests + 7 component unit tests
- **Global Reminder System**: Non-spammy soft violation guidance
- **Standards File Integration**: Dynamic reference to external standards

---

## Architecture & Design

### Design Philosophy
Based on **Composition Over Monoliths** principle:
- **Tool boundaries first**: Focused, single-purpose enforcers
- **Data contracts as APIs**: Standard violation/fix reporting formats
- **Unix philosophy**: Do one thing well, expect composition
- **Progressive enhancement**: Core tools handle 80% of cases

### Component Architecture

```
claudex-guard/
├── src/claudex_guard/
│   ├── core/                    # Shared infrastructure
│   │   ├── base_enforcer.py     # Abstract base class for all enforcers
│   │   ├── violation.py         # Enhanced violation data structures & reporting
│   │   └── utils.py             # Shared utilities
│   ├── standards/               # NEW: Pattern definitions and analysis
│   │   └── python_patterns.py   # Extracted Python pattern detection logic
│   ├── scripts/                 # Language-specific enforcers (now modular)
│   │   ├── python.py            # Refactored Python enforcer (89 lines, was 661)
│   │   └── python_auto_fixer.py # Extracted automatic fixing logic
│   └── install.py               # Claude Code integration installer
├── configs/                     # Language standards documentation
│   └── claudex-python.md        # Python development standards
└── tests/                       # Comprehensive test suite
    ├── test_python_patterns.py          # Pattern detection tests
    ├── test_python_enforcer_integration.py # End-to-end integration tests
    └── test_core_components.py          # Component unit tests
```

### Core Classes

#### BaseEnforcer (src/claudex_guard/core/base_enforcer.py)
Abstract base class defining the enforcer interface:
- `analyze_file()`: Analyze file and return violations
- `apply_automatic_fixes()`: Apply safe automatic fixes  
- `get_file_path_from_hook_context()`: Enhanced Claude hook context extraction
- `run()`: Main entry point with ViolationReporter integration

#### Enhanced Violation (src/claudex_guard/core/violation.py)
Enhanced data structure with language-specific context:
- Standard fields: file path, line number, violation type, severity
- NEW: Optional AST node context for Python analysis
- NEW: Function name and language-specific metadata
- Factory method: `from_ast_node()` for convenient creation

#### ViolationReporter (src/claudex_guard/core/violation.py)
Centralized violation reporting with AI assistant formatting:
- Claude Code emoji formatting (`🚨`, `✅`, `📍`, `💡`)
- Global reminder system for soft violations (like print usage)
- Context-aware messaging and standards file references
- Exit code management (0=success, 2=blocking violations)

#### PythonEnforcer (src/claudex_guard/scripts/python.py)
**Refactored from 661 → 89 lines using composition**:
- Inherits from BaseEnforcer for hook integration
- Composes PythonPatterns for violation detection
- Composes PythonAutoFixer for ruff/mypy integration
- Clean orchestration without monolithic complexity

#### PythonPatterns (src/claudex_guard/standards/python_patterns.py)
**Extracted pattern definition and analysis logic**:
- Banned imports detection (requests→httpx, pip→uv, etc.)
- AST-based analysis (mutable defaults, missing type hints)
- Pattern-based detection (eval, bare except, old formatting)
- Global reminder integration for soft violations

#### PythonAutoFixer (src/claudex_guard/scripts/python_auto_fixer.py)
**Extracted automatic fixing logic**:
- ruff formatting and linting integration
- mypy type checking integration  
- Graceful handling of missing tools

---

## Codebase Navigation

### Key Files and Their Purposes

#### Core Infrastructure
- **`src/claudex_guard/__init__.py`**: Package metadata and version info
- **`src/claudex_guard/core/base_enforcer.py`**: Enhanced foundation for all language enforcers
- **`src/claudex_guard/core/violation.py`**: Enhanced violation reporting with global reminders
- **`src/claudex_guard/install.py`**: Claude Code integration setup

#### Modular Python Enforcer (Refactored Architecture)
- **`src/claudex_guard/scripts/python.py`**: Clean composition-based enforcer (89 lines)
  - Lines 31-49: `PythonEnforcer` class using composition
  - Lines 25-28: Simple main() delegation to enforcer.run()
- **`src/claudex_guard/standards/python_patterns.py`**: Extracted pattern detection logic
  - Lines 16-32: Pattern definitions (banned imports, antipatterns)
  - Lines 113-187: AST analysis with PhilosophyVisitor
  - Lines 189-221: Pattern analysis with global reminder system
- **`src/claudex_guard/scripts/python_auto_fixer.py`**: Extracted automatic fixing logic
  - Lines 14-52: ruff formatting, linting, and mypy integration

#### Configuration
- **`configs/claudex-python.md`**: Comprehensive Python development standards
- **`pyproject.toml`**: Project configuration and dependencies

#### Entry Points
- **`claudex-guard-install`**: CLI command for setting up Claude Code integration
- **`claudex-guard-python`**: CLI command for Python enforcement (typically called by hooks)

### Code Organization Patterns

#### Modular Violation Detection Strategy
1. **AST Analysis** (PythonPatterns.analyze_ast): Sophisticated pattern detection using Python's AST
   - Mutable default argument detection
   - Missing type hint detection  
   - Banned import detection via ImportFrom nodes
2. **Pattern Matching** (PythonPatterns.analyze_patterns): Regex-based anti-pattern detection
   - Global reminder system for soft violations (print usage)
   - Hard violations for serious issues (eval, bare except)
3. **Import Analysis** (PythonPatterns.analyze_imports): Context-aware import validation
4. **Development Patterns** (PythonPatterns.analyze_development_patterns): Workflow standards

#### Composition-Based Architecture
- **PythonEnforcer**: Orchestrates all analysis via composition
- **PythonPatterns**: Handles all violation detection logic
- **PythonAutoFixer**: Handles all automatic fixing logic
- **ViolationReporter**: Handles all output formatting and global reminders

---

## Core Functionality

### Python Quality Enforcement

#### Banned Libraries Detection
The system enforces modern Python practices by detecting and flagging banned legacy libraries:

```python
# Detected as violation
import requests  # → Use httpx (async-first, HTTP/2 support)
import os.path   # → Use pathlib (object-oriented, cross-platform)
import unittest # → Use pytest (better fixtures, cleaner syntax)
```

#### Anti-Pattern Detection
Classic Python gotchas and anti-patterns:

```python
# Mutable default arguments
def bad_function(items=[]):  # VIOLATION
    return items

# Bare except clauses  
try:
    risky_operation()
except:  # VIOLATION
    pass

# Old string formatting
name = "world"
message = "Hello %s!" % name  # VIOLATION → Use f-strings
```

#### Type Hint Enforcement
Requires type hints on all public functions:

```python
# VIOLATION: Missing return type
def process_data(items):
    return [item.upper() for item in items]

# CORRECT: Proper type hints
def process_data(items: list[str]) -> list[str]:
    return [item.upper() for item in items]
```

#### Modern Python Standards
Enforces contemporary Python practices:
- f-strings for formatting
- pathlib for file operations
- Context managers for resources
- uv for package management
- Python 3.9+ built-in types (list, dict vs typing.List, typing.Dict)

### Automatic Fixes

#### ruff Integration
Automatically applies:
- Code formatting (PEP 8 compliance)
- Import sorting and organization
- Basic linting corrections
- Safe refactoring patterns

#### Type Checking
Runs mypy for type validation but reports issues rather than auto-fixing to avoid breaking changes.

### Workflow Context Awareness

The system understands development context:
- **Development Projects**: Detected by presence of `.claude/`, `CLAUDE.md`, `pyproject.toml`
- **Strict Enforcement**: Applied during active development iterations
- **Relaxed Mode**: For non-development files or casual editing

---

## Development Setup

### Prerequisites
- Python 3.9-3.13
- uv package manager (modern Python tooling)
- Claude Code (for integration)

### Installation

#### Standard Installation
```bash
# Install with uv (recommended)
uv add claudex-guard

# Set up Claude Code integration
claudex-guard-install
```

#### Development Setup
```bash
# Clone repository
git clone https://github.com/nickpending/claudex-guard.git
cd claudex-guard

# Install in development mode
uv sync

# Install Claude Code hooks
uv run claudex-guard-install
```

### Development Commands

#### Testing
```bash
# Run test suite
uv run pytest

# Test Python enforcer directly
uv run python -m claudex_guard.scripts.python test_files/bad_python.py

# Run with coverage
uv run pytest --cov=claudex_guard tests/
```

#### Code Quality
```bash
# Lint code
uv run ruff check .

# Format code  
uv run ruff format .

# Type check
uv run mypy src/
```

#### Building and Distribution
```bash
# Build package
uv build

# Install locally
uv pip install -e .
```

### Project Structure Standards
Follows src/ layout to prevent import issues:
```
claudex-guard/
├── src/claudex_guard/     # Source code
├── tests/                 # Test files
├── configs/              # Language standards
├── pyproject.toml        # Project configuration
└── README.md            # Documentation
```

---

## Usage Patterns

### Automatic Integration (Recommended)
Once installed, claudex-guard runs automatically when editing Python files in Claude Code:

```python
# This triggers automatic enforcement
def bad_function(items=[]):  # Mutable default
    result = "Hello %s!" % "world"  # Old formatting
    return result
```

**Output:**
```
✅ Automatic fixes applied:
  • Applied ruff formatting
🚨 Quality violations found:
  📍 example.py:1 - Mutable default argument in function 'bad_function'
  💡 Fix: Use None default, check inside function (classic Python gotcha)
  📍 example.py:2 - Use f-strings instead of % formatting (modern Python)
```

### Manual Usage
Can be used standalone for batch processing:

```bash
# Check single file
claudex-guard-python your_file.py

# Process multiple files
find . -name "*.py" -exec claudex-guard-python {} \;
```

### CI/CD Integration
Include in continuous integration:

```yaml
# .github/workflows/quality.yml
- name: Run claudex-guard
  run: |
    find . -name "*.py" -exec claudex-guard-python {} \;
```

---

## Integration Details

### Claude Code Hook System

claudex-guard integrates with Claude Code's PostToolUse hook system. The installation creates:

**Hook Configuration**: `~/.claude/hooks/languages/claudex-guard-python.py`
```python
#!/usr/bin/env python3
"""Claude Code hook wrapper for claudex-guard Python enforcer."""

import sys
from claudex_guard.scripts.python import main

if __name__ == "__main__":
    sys.exit(main())
```

**Hook Context Processing** (src/claudex_guard/core/base_enforcer.py:30-62):
The enforcer reads Claude Code hook context from:
1. stdin JSON data (primary method)
2. Environment variables (`CLAUDE_FILE_PATHS`) 
3. Command line arguments (fallback)

### Exit Codes
- **0**: Success, no issues found
- **1**: Analysis failed (non-blocking)
- **2**: Quality violations found (blocking)

### Error Handling
Designed to never break the development workflow:
- Analysis failures return exit code 1 but don't block
- Graceful degradation when tools are unavailable
- Comprehensive exception handling

---

## Configuration

### Global Configuration
Standard files are copied to `~/.claudex-guard/configs/` during installation:
- `claudex-python.md`: Complete Python development standards

### Project-Specific Configuration
Copy standards to your project:
```bash
cp ~/.claudex-guard/configs/claudex-python.md your-project/
```

### Planned Configuration (Future)
`.claudex.yaml` in project root:
```yaml
python:
  enforce_type_hints: true
  allow_print_statements: false  
  security_level: strict
  banned_imports:
    - requests: "Use httpx instead"
```

### Environment Variables
- `CLAUDE_FILE_PATHS`: Space-separated file paths for processing
- Standard Python environment variables respected

---

## Troubleshooting

### Common Issues

#### Hook Not Running
**Symptoms**: No quality enforcement when editing files in Claude Code

**Solutions**:
1. Verify installation: `ls ~/.claude/hooks/languages/`
2. Re-run installer: `claudex-guard-install`
3. Check Claude Code hook configuration
4. Ensure file is a `.py` file

#### Missing Tools Warnings
**Symptoms**: "Missing optional dependencies" during installation

**Solution**:
```bash
# Install missing tools
uv add --group dev ruff mypy

# Or install globally
uv tool install ruff mypy
```

#### Type Hints Flooding
**Symptoms**: Too many type hint violations

**Context**: This is intentional behavior enforcing modern Python standards. Options:
1. Add type hints (recommended for development projects)
2. Use relaxed enforcement by moving files outside development project structure
3. Focus on error-level violations first

#### Performance Issues
**Symptoms**: Slow analysis on large files

**Solutions**:
1. Exclude generated files from analysis
2. Use `.gitignore` patterns to skip problematic files
3. Consider file size limits in future configuration

### Debug Mode
Run enforcer directly for debugging:

```bash
# Debug single file
uv run python -m claudex_guard.scripts.python --debug your_file.py

# Check hook context
echo '{"tool_input": {"file_path": "test.py"}}' | claudex-guard-python
```

### Log Analysis
Enforcement logs are written to stderr for Claude Code integration. To capture:

```bash
claudex-guard-python test.py 2> enforcement.log
```

### Integration Testing
Test Claude Code integration:

1. Create test Python file with violations
2. Edit file in Claude Code
3. Observe enforcement output in Claude Code interface
4. Verify automatic fixes were applied

### Recovery from Broken State
If enforcement breaks your workflow:

1. **Temporary disable**: Remove hook file temporarily
   ```bash
   mv ~/.claude/hooks/languages/claudex-guard-python.py ~/.claude/hooks/languages/claudex-guard-python.py.disabled
   ```

2. **Reinstall clean**: 
   ```bash
   claudex-guard-install
   ```

3. **Verify tool versions**:
   ```bash
   ruff --version
   mypy --version
   python --version
   ```

---

## Advanced Usage

### Adding New Language Support

1. **Create enforcer script**:
   ```bash
   cp src/claudex_guard/scripts/python.py src/claudex_guard/scripts/newlang.py
   ```

2. **Create language standards**:
   ```bash
   cp configs/claudex-python.md configs/claudex-newlang.md
   ```

3. **Implement language-specific patterns** in the enforcer script

4. **Add to pyproject.toml**:
   ```toml
   [project.scripts]
   claudex-guard-newlang = "claudex_guard.scripts.newlang:main"
   ```

### Custom Violation Types
Extend the base enforcer for domain-specific rules:

```python
from claudex_guard.core.base_enforcer import BaseEnforcer
from claudex_guard.core.violation import Violation

class CustomEnforcer(BaseEnforcer):
    def analyze_file(self, file_path: Path) -> List[Violation]:
        violations = []
        # Add custom analysis logic
        return violations
```

### Workflow Integration Examples

#### Pre-commit Hook
```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: claudex-guard
        name: claudex-guard
        entry: claudex-guard-python
        language: system
        files: \.py$
```

#### VS Code Integration
Add to `.vscode/tasks.json`:
```json
{
    "label": "Run claudex-guard",
    "type": "shell", 
    "command": "claudex-guard-python",
    "args": ["${file}"],
    "group": "build"
}
```

---

*This context was auto-generated by the `/create-app-context` command. For updates or corrections, please modify this file directly or regenerate using the command.*