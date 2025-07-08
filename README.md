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
- **🧪 Comprehensive Testing**: 43 tests (integration + unit) ensuring reliability

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
echo '{"tool_input": {"file_path": "your_file.py"}}' | uv run python -m claudex_guard.main
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

**Modular Composition Design** (Refactored 2025-07-08):

```
claudex-guard/
├── src/claudex_guard/
│   ├── core/                    # Enhanced shared infrastructure
│   │   ├── base_enforcer.py     # Abstract base for all enforcers
│   │   ├── violation.py         # Enhanced reporting with global reminders
│   │   ├── violation_memory.py  # Violation tracking and memory
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
├── configs/                     # External standards files
└── tests/                       # 43 comprehensive tests
    ├── test_python_patterns.py         # Pattern detection tests
    ├── test_python_enforcer_integration.py # End-to-end tests
    ├── test_comprehensive_ast_detection.py # AST analysis tests
    ├── test_phase1_standards_coverage.py   # Standards coverage
    ├── test_phase2_comprehensive.py        # Advanced pattern tests
    └── test_core_components.py         # Component unit tests
```

## Python Enforcer Features

### Modular Architecture (2025-07-08 Refactor)
- **Standard Package Structure**: Moved from non-standard scripts/ to proper Python modules
- **Clean Separation**: enforcers/, hooks/, services/, standards/ for clear responsibilities
- **BaseEnforcer Pattern**: Ready for JavaScript/Rust expansion  
- **Global Reminder System**: Non-spammy soft violation guidance
- **Comprehensive Testing**: 43 tests ensuring reliability (100% pass rate)

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

**Comprehensive Test Suite (43 tests)**:

```bash
# Run all tests
uv run pytest tests/ -v

# Test specific components
uv run python tests/test_core_components.py        # Unit tests
uv run python tests/test_python_enforcer_integration.py  # Integration tests

# Test enforcer directly
echo '{"tool_input": {"file_path": "your_file.py"}}' | uv run python -m claudex_guard.main
```

**Test Coverage**:
- 8 integration tests (end-to-end hook scenarios)
- 7 component unit tests (bug detection)
- 13 pattern detection tests (comprehensive violations)
- 15 standards coverage tests (Phase 1 & 2 patterns)
- AST analysis and performance tests

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