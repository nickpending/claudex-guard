# claudex-guard

AI slop detection and code quality enforcement for AI-assisted development.

## Overview

claudex-guard detects and blocks "AI slop" - broken, unmaintainable, untestable code patterns from outdated AI training data. It enforces modern best practices and blocks real quality issues while educating AI assistants toward better patterns.

## Features

- **🎯 AI Slop Detection**: Blocks broken patterns from old AI training data (deprecated libs, old syntax)
- **⚖️ Smart Severity**: ERROR blocks real issues, WARNING educates toward better practices
- **🐍 Multi-Language**: Python, TypeScript/JavaScript, Rust, Go with consistent philosophy
- **🛡️ Mock Detection**: Enforces "Don't Mock What You Don't Own" (decorators + context managers)
- **🔧 Zero Duplication**: Delegates to existing linters (ruff, mypy, Clippy, ESLint) - no redundant checks
- **⚡ Performance**: 47% faster with SQLite storage and intelligent project root caching
- **🤖 AI Integration**: Claude Code hooks with JSON decision control
- **📊 Queryable History**: SQLite database for violation analytics
- **🧪 Comprehensive Testing**: 70 passing tests ensuring reliability

## Quick Start

### Installation

**For Universal CLI Access:**

```bash
# Clone and install globally (makes CLI commands available everywhere)
git clone https://github.com/your-username/claudex-guard.git
cd claudex-guard

# Build and install from wheel (ensures clean installation)
uv build
uv tool install dist/claudex_guard-*.whl

# Verify installation
which claudex-guard
# /Users/you/.local/bin/claudex-guard

# Manually add to Claude Code settings.json:
# Add this to your PostToolUse hooks for Python files
```

**Local Development:**

```bash
# Clone and install in development mode
git clone https://github.com/your-username/claudex-guard.git
cd claudex-guard
uv sync

# Run tests to verify everything works
uv run pytest tests/ -v

# Test the tool directly
echo 'print("hello")' > /tmp/test.py
CLAUDE_FILE_PATHS=/tmp/test.py uv run python -m src.claudex_guard.main --mode post

# When updating after code changes, rebuild and reinstall:
rm -rf dist/ && uv build && uv tool uninstall claudex-guard && uv tool install dist/claudex_guard-*.whl
```

### Usage

Once installed, claudex-guard automatically runs when you edit files in Claude Code.

**Example - ERROR (blocks execution):**
```python
import requests  # Banned import - old AI training data

def fetch_data():
    return requests.get("https://api.example.com")
```

```
Quality violations found (1 errors):
• example.py:1 - Banned import 'requests' - use 'httpx' instead
  Fix: Modern async HTTP client with better API
```

**Example - WARNING (educates):**
```python
import threading  # Suggests better alternatives

def worker():
    print("Working")  # Suggests rich.print()
```

```
Quality checks passed with suggestions:
• Consider asyncio instead of threading for modern concurrent code
• Use rich.print() for better console output
```

**Note**: If you see duplicate messages, run Claude Code from within a project directory rather than from `~/`.

## Supported Languages

All languages follow the same philosophy: block AI slop (ERROR), educate toward better (WARNING), delegate to linters.

- ✅ **Python** - AST analysis, ruff/mypy integration, banned imports (requests, pandas, pip)
- ✅ **JavaScript/TypeScript** - ESLint integration, banned packages (moment, axios), console.log warnings
- ✅ **Rust** - Clippy integration, outdated crates (time, chrono 0.3), panic() detection
- ✅ **Go** - golangci-lint integration, deprecated packages, error ignoring warnings

## Architecture

**Modular Composition Design** (Latest: 2025-11-13 - Major refactor for zero duplication):

```
claudex-guard/
├── src/claudex_guard/
│   ├── core/                    # Enhanced shared infrastructure
│   │   ├── base_enforcer.py     # Abstract base for all enforcers
│   │   ├── violation.py         # Enhanced reporting with global reminders
│   │   ├── violation_memory.py  # SQLite integration for violations
│   │   ├── violation_db.py      # SQLite database for queryable history
│   │   ├── project_cache.py     # Project root caching (47% perf boost)
│   │   └── utils.py             # Shared utilities
│   ├── standards/               # Extracted pattern definitions
│   │   └── python_patterns.py   # Python pattern detection logic
│   ├── enforcers/               # Language-specific enforcers
│   │   └── python.py            # Python enforcer (clean, modular)
│   ├── hooks/                   # Claude Code integration
│   │   └── pre_hook.py          # Hook integration logic
│   ├── services/                # Supporting services
│   │   └── auto_fixer.py        # Automatic code fixing
│   └── main.py                  # CLI entry point
└── tests/                       # 70 comprehensive tests
    ├── test_python_patterns.py         # Pattern detection tests
    ├── test_python_enforcer_integration.py # End-to-end tests
    ├── test_comprehensive_ast_detection.py # AST analysis tests
    ├── test_phase1_standards_coverage.py   # Standards coverage
    ├── test_phase2_comprehensive.py        # Advanced pattern tests
    └── test_core_components.py         # Component unit tests
```

## How It Works

### Severity Model

**ERROR (Blocks execution)** - Real AI slop that breaks code or architecture:
- Banned imports (requests→httpx, pandas→polars, old libraries from AI training data)
- Mock violations ("Don't Mock What You Don't Own" architecture enforcement)
- Path traversal security issues
- Identity comparison bugs (`is` vs `==` gotchas)

**WARNING (Educational)** - Steers AI toward better patterns without blocking:
- Documentation opportunities (missing/inadequate docstrings)
- Refactoring suggestions (dataclass, enum, match/case)
- Modern API usage (pathlib over os.path, os.getenv() over os.environ[])
- Code quality (test naming, error logging, composition over inheritance)
- Threading import (suggests async alternatives)

### No Duplicate Checks

claudex-guard delegates to existing linters instead of reimplementing:
- **Python**: ruff handles bare except (E722), mutable defaults (B006), type hints (via mypy)
- **TypeScript**: ESLint + tsc handle language issues
- **Rust**: Clippy handles .unwrap() abuse, deprecated patterns
- **Go**: golangci-lint handles language-specific issues

This means:
- Faster execution (no redundant analysis)
- Better accuracy (tools specialized for each language)
- Consistent with ecosystem standards

### Mock Detection System
Enforces the "Don't Mock What You Don't Own" principle to prevent brittle tests:

- **Comprehensive Detection**: Catches both decorator (`@patch`) and context manager (`with patch()`) patterns
- **Blocks Internal Mocking**: Prevents mocking your own code/services
- **Allows External APIs**: External services (OpenAI, Stripe, etc.) configurable as allowed
- **Test File Aware**: Strict enforcement in test files (`test_*.py`, `*_test.py`)
- **Configurable**: Use `.claudex-guard.yaml` to allow specific patterns
- **Escape Hatch**: Use `# claudex-guard: disable-mock` to allow specific lines

Example configuration (`.claudex-guard.yaml`):
```yaml
mock_detection:
  allowed_patterns:
    - "openai.*"      # Allow mocking OpenAI API
    - "stripe.*"      # Allow mocking Stripe API  
    - "requests.*"    # Allow mocking external HTTP requests
    - "boto3.*"       # Allow mocking AWS services
```

### Automatic Fixes
- ruff formatting and linting integration
- mypy type checking integration
- Graceful handling of missing tools

## Python Project Setup

For Python projects, claudex-guard requires minimal ruff configuration in your
`pyproject.toml` to properly handle test files:

```toml
[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "S"]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "S603", "S607"]
"test_*.py" = ["S101", "S603", "S607"]
"**/test_*.py" = ["S101", "S603", "S607"]
```

**What this does:**
- `S101` - Allows `assert` statements in test files (legitimate in pytest)
- `S603/S607` - Allows subprocess usage in test files (safe in tests)

**Why it's needed:**
claudex-guard extends ruff's security rules (`--extend-select=S`) to catch
AI-generated security issues. Without per-file-ignores, pytest tests with
`assert` statements would incorrectly trigger security warnings.

**Self-correcting:**
If you forget this config, claudex-guard will detect test file violations
and show you the exact pyproject.toml configuration to add.

## Configuration

### Project-Specific Rules
Create `.claudex-guard.yaml` in your project root:
```yaml
# Mock detection configuration (v0.3.4+)
mock_detection:
  allowed_patterns:
    - "openai.*"      # External API mocking allowed
    - "stripe.*"      # External service mocking allowed
    - "requests.*"    # HTTP library mocking allowed

# Python enforcement (planned)
python:
  enforce_type_hints: true
  allow_print_statements: false
  security_level: strict
```

## Data Storage & Analytics

### Storage Locations (XDG Compliant)
All data is centralized in `~/.config/claudex-guard/`:
- `project_roots.json` - Cached project root discoveries
- `violations.db` - SQLite database of all violations

### Querying Violations
```bash
# View total violations
sqlite3 ~/.config/claudex-guard/violations.db "SELECT COUNT(*) FROM violations"

# Top violation types
sqlite3 ~/.config/claudex-guard/violations.db \
  "SELECT violation_type, COUNT(*) as count FROM violations \
   GROUP BY violation_type ORDER BY count DESC LIMIT 10"

# Most problematic files  
sqlite3 ~/.config/claudex-guard/violations.db \
  "SELECT file_name, COUNT(*) as count FROM violations \
   GROUP BY file_name ORDER BY count DESC LIMIT 10"

# Recent violations (last 7 days)
sqlite3 ~/.config/claudex-guard/violations.db \
  "SELECT * FROM violations \
   WHERE timestamp > datetime('now', '-7 days') \
   ORDER BY timestamp DESC LIMIT 20"
```

## Development

### Adding New Language Support

1. Create language-specific enforcer in `src/claudex_guard/enforcers/`:
```bash
cp src/claudex_guard/enforcers/python.py src/claudex_guard/enforcers/newlang.py
```

2. Create language pattern definitions in `src/claudex_guard/standards/`:
```bash
cp src/claudex_guard/standards/python_patterns.py src/claudex_guard/standards/newlang_patterns.py
```

3. Implement language-specific patterns and integrate with existing linters
4. Add file extension mapping to `BaseEnforcer.EXTENSION_MAP`
5. Write comprehensive tests in `tests/`

### Testing

**Comprehensive Test Suite (70 tests, 21 skipped)**:

```bash
# Run all tests
uv run pytest tests/ -v

# Test specific components
uv run pytest tests/test_mock_detection_integration.py -v  # Mock detection
uv run pytest tests/test_python_enforcer_integration.py -v # Integration
uv run pytest tests/test_multi_language_integration.py -v  # Multi-language

# Test enforcer directly
echo '{"tool_input": {"file_path": "your_file.py"}}' | uv run python -m claudex_guard.main
```

**Test Coverage**:
- Mock detection (decorator + context manager patterns)
- Multi-language integration (Python, TypeScript, Rust, Go)
- End-to-end hook scenarios
- AST analysis and pattern detection
- Standards coverage and performance tests

## Integration

### Claude Code Hooks

claudex-guard integrates with Claude Code's hook system in two modes:

#### PostToolUse (Working - Recommended)

**Add to your `~/.claude/settings.json`:**

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "claudex-guard --mode post"
      }]
    }]
  }
}
```

**How it works:**
- Hook triggers after any `Edit` or `Write` tool use
- Tool checks file extension (only processes .py files)
- If violations found, outputs JSON decision control to block Claude
- Claude receives detailed violation information and fix suggestions

#### PreToolUse (Experimental - Context Only)

**Add to your `~/.claude/settings.json`:**

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "claudex-guard --mode pre"
      }]
    }]
  }
}
```

**⚠️ Current Limitation**: PreToolUse hooks are designed for blocking/approval decisions, not context injection. Claude doesn't see the hook output content, so violation history context isn't available to Claude during tool use.

**Manual Workaround**: Use the generated `.claudex-guard/memory.md` file:

```bash
# View the violation memory file
cat .claudex-guard/memory.md

# Add its contents to your CLAUDE.md or CLAUDE.local.md for manual context
```

This file contains a summary of recent violations that helps Claude understand your coding patterns and preferences.

**Note**: After `uv tool install .`, the command is globally available.

## Troubleshooting

### Duplicate Messages
If you see duplicate violation messages, run Claude Code from within a project directory rather than from `~/`. This is due to how Claude Code handles hooks when launched from the home directory.

### Hook Not Running
- Verify global installation: `which claudex-guard`
- Check hook configuration in `~/.claude/settings.json`
- Restart Claude Code after configuration changes
- Ensure you're editing .py files (tool only processes Python files)

### Other AI Assistants

While built for Claude Code, the enforcers can be used standalone:

```bash
uv run python -m claudex_guard.main your_file.py
```

## Changelog

### v0.3.5 (2025-11-13) - Zero Duplication Refactor
- **Removed duplicate checks**: Bare except, subprocess shell=True, type hints, .unwrap() - linters handle these
- **Fixed severity model**: Clear ERROR (blocks) vs WARNING (educates) distinction
- **Closed mock detection gap**: Added context manager (`with patch()`) detection
- **Updated tests**: 70 passing tests, comprehensive coverage
- **Philosophy clarified**: AI slop detection, delegate to linters, consistent multi-language

### v0.3.4 (2025-08-14) - Performance Update
- SQLite violation storage
- Project root caching (47% faster)
- XDG-compliant data storage

### v0.3.0 - Multi-Language Support
- TypeScript/JavaScript enforcer
- Rust enforcer
- Go enforcer
- Consistent philosophy across languages

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-language`
3. Add language enforcer and standards
4. Test thoroughly
5. Submit pull request

## License

MIT License - see LICENSE file for details

## Credits

Built with [claudex](https://github.com/nickpending/claudex) - systematic development standards for AI-assisted workflows.