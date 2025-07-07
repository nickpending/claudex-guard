# claudex-guard

Automated code quality enforcement for AI-assisted development workflows.

## Overview

claudex-guard provides real-time code quality enforcement integrated with AI coding assistants. Instead of repeatedly explaining your coding standards, let claudex-guard automatically enforce them and teach your AI assistant your preferences.

## Features

- **🐍 Python Enforcement**: Modular AST analysis (661→89 lines, 87% reduction)
- **🔧 Automatic Fixes**: Integration with ruff formatting/linting and mypy type checking
- **🤖 AI Integration**: Enhanced Claude Code hooks with global reminder system
- **📚 Standards-Based**: References `~/.claudex/standards/claudex-python.md`
- **⚡ Real-time**: Non-blocking soft violations for better UX
- **🧪 Comprehensive Testing**: 27 tests (integration + unit) ensuring reliability

## Quick Start

### Installation

**For Universal CLI Access:**

```bash
# Clone and install globally (makes CLI commands available everywhere)  
git clone https://github.com/your-username/claudex-guard.git
cd claudex-guard
uv tool install .

# Now claudex-guard-python is globally available
which claudex-guard-python
# /Users/you/.local/bin/claudex-guard-python

# Manually add to Claude Code settings.json:
# Add this to your PostToolUse hooks for Python files
```

**Development installation:**

```bash
# Clone and install in development mode
git clone https://github.com/your-username/claudex-guard.git
cd claudex-guard
uv sync

# Run tests to verify everything works
uv run pytest tests/ -v

# Test the tool directly
echo '{"tool_input": {"file_path": "your_file.py"}}' | uv run claudex-guard-python
```

### Usage

Once installed, claudex-guard automatically runs when you edit Python files in Claude Code:

```python
# This code will trigger quality enforcement
def bad_function(items=[]):  # Mutable default argument
    result = "Hello %s!" % "world"  # Old string formatting
    return result
```

Claude receives violation details via JSON decision control:
```
Quality violations found (2 errors):
• example.py:1 - Mutable default argument in function 'bad_function'
  Fix: Use None default, check inside function (classic Python gotcha)
• example.py:2 - Use f-strings instead of % formatting (modern Python)
  Fix: Replace with f"Hello {name}!" syntax
```

**Note**: If you see duplicate messages, run Claude Code from within a project directory rather than from `~/`.

## Supported Languages

- ✅ **Python** - Full enforcement with AST analysis
- 📋 **JavaScript/TypeScript** - Planned
- 📋 **Rust** - Planned
- 📋 **Go** - Planned

## Architecture

**Modular Composition Design** (Refactored 2025-07-04):

```
claudex-guard/
├── src/claudex_guard/
│   ├── core/                    # Enhanced shared infrastructure
│   │   ├── base_enforcer.py     # Abstract base for all enforcers
│   │   ├── violation.py         # Enhanced reporting with global reminders
│   │   └── utils.py             # Shared utilities
│   ├── standards/               # Extracted pattern definitions
│   │   └── python_patterns.py   # Python pattern detection logic
│   ├── scripts/                 # Modular language enforcers
│   │   ├── python.py            # Refactored enforcer (89 lines, was 661)
│   │   └── python_auto_fixer.py # Extracted automatic fixing
│   └── install.py               # Claude Code integration
├── configs/                     # External standards files
└── tests/                       # 27 comprehensive tests
    ├── test_python_patterns.py         # Pattern detection tests
    ├── test_python_enforcer_integration.py # End-to-end tests
    └── test_core_components.py         # Component unit tests
```

## Python Enforcer Features

### Modular Architecture (2025-07-04 Refactor)
- **87% Code Reduction**: 661 → 89 lines via composition
- **BaseEnforcer Pattern**: Ready for JavaScript/Rust expansion  
- **Global Reminder System**: Non-spammy soft violation guidance
- **Enhanced Testing**: 27 comprehensive tests ensuring reliability

### Pattern Detection
- **Security**: `eval()`, `exec()`, SQL injection patterns
- **Performance**: Inefficient loops, string concatenation
- **Modern Python**: f-strings, pathlib, type hints, banned legacy imports
- **Environment**: uv over pip/poetry, proper virtual environments
- **Anti-patterns**: Mutable defaults, bare except clauses, late binding closures

### Smart Violation System
- **Hard Violations**: Block development (mutable defaults, eval, bare except)
- **Soft Violations**: Show global reminders (print usage guidance)
- **Standards Integration**: Points to `~/.claudex/standards/claudex-python.md`

### Automatic Fixes
- ruff formatting and linting integration
- mypy type checking integration
- Graceful handling of missing tools

## Configuration

### Global Configuration
Copy standards files to your project:
```bash
cp configs/claudex-python.md your-project/
```

### Project-Specific Rules
(Planned) Create `.claudex.yaml` in your project:
```yaml
python:
  enforce_type_hints: true
  allow_print_statements: false
  security_level: strict
```

## Development

### Adding New Language Support

1. Create language-specific enforcer:
```bash
cp scripts/claudex-guard-python.py scripts/claudex-guard-newlang.py
```

2. Create language standards:
```bash
cp configs/claudex-python.md configs/claudex-newlang.md
```

3. Implement language-specific patterns in the enforcer script

### Testing

**Comprehensive Test Suite (27 tests)**:

```bash
# Run all tests
uv run pytest tests/ -v

# Test specific components
uv run python tests/test_core_components.py        # Unit tests
uv run python tests/test_python_enforcer_integration.py  # Integration tests

# Test enforcer directly
echo '{"tool_input": {"file_path": "your_file.py"}}' | claudex-guard-python
```

**Test Coverage**:
- 8 integration tests (end-to-end hook scenarios)
- 7 component unit tests (bug detection)
- 12 pattern detection tests (comprehensive violations)

## Integration

### Claude Code Hooks

claudex-guard integrates with Claude Code's PostToolUse hook system.

**Add to your `~/.claude/settings.json`:**

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "claudex-guard-python"
      }]
    }]
  }
}
```

**How it works:**
- Hook triggers on any `Edit` or `Write` tool use
- Tool checks file extension (only processes .py files)
- If violations found, outputs JSON decision control to block Claude
- Claude receives detailed violation information and fix suggestions

**Note**: After `uv tool install .`, the command is globally available.

## Troubleshooting

### Duplicate Messages
If you see duplicate violation messages, run Claude Code from within a project directory rather than from `~/`. This is due to how Claude Code handles hooks when launched from the home directory.

### Hook Not Running
- Verify global installation: `which claudex-guard-python`
- Check hook configuration in `~/.claude/settings.json`
- Restart Claude Code after configuration changes
- Ensure you're editing .py files (tool only processes Python files)

### Other AI Assistants

While built for Claude Code, the enforcers can be used standalone:

```bash
python scripts/claudex-guard-python.py your_file.py
```

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