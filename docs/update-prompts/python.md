# Python Standards Update Prompt for claudex-guard

Use this prompt when updating the Python enforcer code after changes to `~/.claudex/standards/claudex-python.md`.

## Context and Purpose

You are updating the Python enforcer code in claudex-guard to reflect changes in the Python standards file. The standards file (`claudex-python.md`) contains development preferences, banned practices, and patterns, but the enforcer code requires custom AST analysis, regex patterns, and fix suggestions.

## Key Principle

**Standards are data, enforcers are logic.** You cannot auto-generate sophisticated AST analysis from markdown, but you can extract the rules, patterns, and guidance to implement in code.

## File Structure to Update

```
src/claudex_guard/standards/python_patterns.py
├── BANNED_IMPORTS dict           # Extract from standards
├── REQUIRED_PATTERNS dict        # Extract from standards  
├── ANTIPATTERNS list             # Extract from standards
├── analyze_ast() method          # Custom logic implementing standards
├── analyze_patterns() method     # Custom logic implementing standards
├── analyze_imports() method      # Custom logic implementing standards
└── analyze_development_patterns() # Custom logic implementing standards
```

## Current Architecture

The Python enforcer uses a modular composition pattern:

**Main Entry Point:**
- `src/claudex_guard/scripts/python.py` - 89 lines, orchestrates analysis
- Delegates to `PythonPatterns` class for all detection logic

**Pattern Detection:**
- `src/claudex_guard/standards/python_patterns.py` - 295 lines, all patterns and analysis
- Contains both data (banned imports, regexes) and logic (AST analysis)

**Auto-Fixing:**
- `src/claudex_guard/scripts/python_auto_fixer.py` - 82 lines
- Handles ruff formatting, linting, and mypy integration

## Update Process

### Step 1: Read the Updated Standards
```bash
# Read the updated standards file
cat ~/.claudex/standards/claudex-python.md
```

### Step 2: Extract Updateable Data

Look for these sections in the standards file:

**Banned Libraries/Imports:**
```markdown
## Banned Legacy Libraries
- `requests` → Use httpx (async-first, HTTP/2 support)
- `pip/pip-tools` → Use uv (10-100x faster, handles everything)
- `virtualenv/venv` → Use uv (automatic environment management)
```

**Required Patterns:**
```markdown
## Python Patterns I Prefer
- Always use f-strings for string formatting
- Use pathlib for file operations
- Type hints everywhere
- Context managers for resources
```

**Anti-patterns to Detect:**
```markdown
## Python-Specific Gotchas to Avoid
- Mutable Default Arguments (classic Python footgun)
- Late Binding Closures (lambda in loops)
- Global Interpreter Lock (GIL) confusion
```

### Step 3: Update PythonPatterns Class

**Location:** `src/claudex_guard/standards/python_patterns.py`

**What to Update (Data from Standards):**

```python
# Update these based on standards file
self.BANNED_IMPORTS = {
    "requests": "Use httpx (async-first, HTTP/2 support)",
    "pip": "Use uv (10-100x faster, handles everything)",
    # ... extract more from standards
}

self.ANTIPATTERNS = [
    (r"def\s+\w+\([^)]*=\s*\[\]", "Mutable default argument (classic Python gotcha)"),
    (r"except\s*:", "Bare except clause (violates error handling standards)"),
    # ... extract more patterns from standards
]
```

**What NOT to Change (Custom Logic):**
- AST visitor classes (`PhilosophyVisitor`) and traversal logic
- Complex import analysis in `analyze_imports()`
- Method signatures and class structure
- Error handling and validation logic

### Step 4: Implementation Guidelines

**For New Banned Imports:**
1. Add to `BANNED_IMPORTS` dict with fix suggestion
2. The existing `analyze_imports()` method automatically checks them using:
   ```python
   if import_name == banned or import_name.startswith(banned + "."):
   ```

**For New Anti-patterns:**
1. Add regex pattern and message to `ANTIPATTERNS` list
2. The existing `analyze_patterns()` method automatically checks them
3. Consider if pattern needs special handling (like `print()` statements use global reminders)

**For Complex New Standards:**
1. Determine what type of analysis is needed:
   - **Simple text patterns** → Add to `ANTIPATTERNS`
   - **Import checking** → Add to `BANNED_IMPORTS` 
   - **AST analysis** → Add to `analyze_ast()` method
   - **Project structure** → Add to `analyze_development_patterns()`

**For AST-based Standards:**
1. Understand what AST nodes to examine:
   - `FunctionDef` - function definitions and arguments
   - `Import`/`ImportFrom` - import statements
   - `Call` - function calls like `eval()`, `exec()`
   - `Lambda` - lambda functions and closures
2. Add visitor logic to the `PhilosophyVisitor` class in `analyze_ast()`
3. Use `Violation.from_ast_node()` for violations with line numbers

## Example Updates

**Standards file says:**
```markdown
## Banned Legacy Libraries
- `pandas` → Use polars (10x faster for large datasets)
```

**Code update:**
```python
# Add to BANNED_IMPORTS dict in __init__()
"pandas": "Use polars (10x faster for large datasets)",
```

**Standards file says:**
```markdown
## Python-Specific Gotchas to Avoid
- Never use `print()` for debugging → Use rich.print() or icecream.ic()
```

**Code update:**
```python
# Add to ANTIPATTERNS list in __init__()
(r"print\s*\(", "Use rich.print() or icecream.ic() for better debugging output"),
```

**Note:** `print()` detection uses global reminders to avoid spam. Check existing implementation.

**Standards file says:**
```markdown
## Security Fundamentals
- Never use `subprocess.call()` with shell=True → Use shell=False and list args
```

**Code update requires AST analysis:**
```python
# Add to PhilosophyVisitor class in analyze_ast()
def visit_Call(self, node):
    if (isinstance(node.func, ast.Attribute) and 
        getattr(node.func.value, 'id', None) == 'subprocess'):
        # Check for shell=True in keywords
        for keyword in node.keywords:
            if keyword.arg == 'shell' and isinstance(keyword.value, ast.Constant):
                if keyword.value.value is True:
                    self.enforcer.violations.append(
                        Violation.from_ast_node(
                            str(self.file_path),
                            node,
                            "security_violation", 
                            "subprocess with shell=True is dangerous",
                            "Use shell=False and pass command as list"
                        )
                    )
    self.generic_visit(node)
```

## Testing Your Changes

After updating the code:

```bash
# Test with known violation files
cd claudex-guard
uv run claudex-guard-python research/test-scenarios/violations.py

# Test with clean files
uv run claudex-guard-python research/test-scenarios/clean.py

# Verify specific patterns work
uv run claudex-guard-python test_file.py
```

Create test files to validate new patterns:
```python
# test_new_patterns.py
import pandas as pd  # Should trigger new banned import

def bad_func(items=[]):  # Should trigger mutable default
    print("debug")  # Should trigger print warning
    return items
```

## Current Special Handling

**Print Statements:** Use global reminders instead of individual violations to reduce spam:
```python
# In analyze_patterns() - check existing implementation
if pattern == r"print\s*\(":
    has_print_usage = True
    continue  # Don't add as individual violation

if has_print_usage and reporter:
    reporter.add_global_reminder(
        "💡 Consider logging for production code or rich.print() for enhanced output"
    )
```

**Import Analysis:** Uses exact matching to avoid false positives:
```python
# Fixed bug - only matches exact imports, not substrings
if import_name == banned or import_name.startswith(banned + "."):
```

## Common Mistakes to Avoid

1. **Don't break existing AST logic** - Only add to visitor methods
2. **Don't change method signatures** - Maintain compatibility with main enforcer
3. **Don't remove existing patterns** without understanding their purpose
4. **Don't add overly broad regex patterns** - They cause false positives
5. **Do test with real files** - Standards updates can break detection
6. **Do preserve fix suggestion quality** - Make them specific and actionable
7. **Do consider performance** - Complex analysis can slow enforcement

## Success Criteria

✅ New standards from `claudex-python.md` are enforced by the code
✅ Existing standards still work correctly
✅ Fix suggestions are specific and actionable  
✅ No false positives on legitimate code
✅ No performance regressions
✅ Test files validate the changes work correctly

## File Locations Reference

- **Standards Source**: `~/.claudex/standards/claudex-python.md`
- **Main Code to Update**: `src/claudex_guard/standards/python_patterns.py`
- **Orchestration Code**: `src/claudex_guard/scripts/python.py` (usually no changes)
- **Auto-Fixer Code**: `src/claudex_guard/scripts/python_auto_fixer.py` (usually no changes)
- **Test Files**: `research/test-scenarios/violations.py`, `research/test-scenarios/clean.py`

## Integration Notes

The Python enforcer integrates with:
- **ruff** for formatting and linting (via PythonAutoFixer)
- **mypy** for type checking (via PythonAutoFixer)  
- **Claude Code hooks** for real-time enforcement
- **ViolationReporter** for formatted output to AI assistants

Changes to pattern detection won't affect these integrations - they're handled by separate components.

Remember: You're translating human-readable Python standards into executable code that can detect violations and provide helpful guidance to both developers and AI assistants.