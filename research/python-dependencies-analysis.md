# Python Dependencies Analysis

**Research Task**: R.1 - Analyze Monolithic Script Dependencies  
**Purpose**: Map class dependencies and data flow in `src/claudex_guard/scripts/python.py` to understand extraction strategy for modular architecture  
**Date**: 2025-07-03  

---

## Executive Summary

The monolithic `python.py` script (598 lines) contains 4 main classes and 1 orchestration function that need to be refactored into the existing modular architecture. Analysis reveals significant overlap with existing base classes and clear extraction paths for composition-based refactoring.

**Key Findings**:
- 85% of hook integration logic already exists in `BaseEnforcer`
- 90% of violation reporting logic already exists in `ViolationReporter`
- `PythonQualityViolation` can be replaced with enhanced `Violation` class
- `WorkflowContextAwareness` partially duplicates `WorkflowContext`
- Clear extraction path for `PythonPhilosophyEnforcer` and `AutomaticQualityFixer`

---

## Class Dependency Analysis

### Monolithic Classes (598 lines total)

#### 1. PythonQualityViolation (lines 24-46, 23 lines)
```python
class PythonQualityViolation:
    def __init__(self, file_path, line_num, violation_type, message, fix_suggestion="", severity="error")
    def __str__(self) -> str  # Format for Claude Code display
```

**Dependencies**: None (pure data structure)  
**Usage**: Created by `PythonPhilosophyEnforcer`, consumed by `main()` for reporting  
**Base Class Overlap**: 95% identical to existing `Violation` class

#### 2. PythonPhilosophyEnforcer (lines 49-335, 287 lines)
```python
class PythonPhilosophyEnforcer:
    BANNED_IMPORTS = {...}      # Static patterns
    REQUIRED_PATTERNS = {...}   # Static patterns  
    ANTIPATTERNS = [...]        # Static patterns
    
    def __init__(self)
    def analyze_file(self, file_path: Path) -> List[PythonQualityViolation]
    def _analyze_ast(self, tree: ast.AST, file_path: Path)        # AST visitor
    def _analyze_patterns(self, lines: List[str], file_path: Path)  # Regex patterns
    def _analyze_imports(self, content: str, file_path: Path)     # Import analysis
    def _analyze_development_patterns(self, content: str, lines: List[str], file_path: Path)
```

**Dependencies**: 
- Creates `PythonQualityViolation` objects
- Uses `ast` module for Python parsing
- Contains all Python-specific violation patterns

**Base Class Overlap**: Implements same interface as `BaseEnforcer.analyze_file()`

#### 3. AutomaticQualityFixer (lines 337-414, 78 lines)
```python
class AutomaticQualityFixer:
    def __init__(self)
    def apply_automatic_fixes(self, file_path: Path) -> List[str]
    def _run_ruff_format(self, file_path: Path) -> bool
    def _run_ruff_check_fix(self, file_path: Path) -> bool
    def _run_mypy_check(self, file_path: Path) -> List[str]
```

**Dependencies**: 
- External subprocess calls to `ruff` and `mypy`
- Maintains `fixes_applied` list for reporting

**Base Class Overlap**: Implements same interface as `BaseEnforcer.apply_automatic_fixes()`

#### 4. WorkflowContextAwareness (lines 417-487, 71 lines)
```python
class WorkflowContextAwareness:
    def __init__(self, file_path: Path)
    def _find_project_root(self) -> Optional[Path]
    def _is_development_project(self) -> bool
    def _get_iteration_context(self) -> Dict[str, Any]
    def should_enforce_strict_quality(self) -> bool
    def get_context_message(self) -> str
```

**Dependencies**: 
- File system inspection for project markers
- No external dependencies

**Base Class Overlap**: 80% overlaps with existing `WorkflowContext` class

#### 5. main() Function (lines 489-597, 109 lines)
```python
def main():
    # Hook context extraction (lines 496-523)
    # File processing orchestration (lines 525-557)
    # Results reporting (lines 558-592)
```

**Dependencies**: 
- Uses all 4 classes above
- Handles stdin/stderr for Claude Code integration
- Orchestrates entire workflow

**Base Class Overlap**: 85% of logic already exists in `BaseEnforcer.run()`

---

## Data Flow Analysis

### Current Monolithic Data Flow

```mermaid
graph TD
    A[Claude Code Hook] --> B[main() stdin parsing]
    B --> C[WorkflowContextAwareness]
    B --> D[AutomaticQualityFixer]
    B --> E[PythonPhilosophyEnforcer]
    
    D --> F[ruff/mypy subprocess]
    F --> G[List of fixes applied]
    
    E --> H[AST Analysis]
    E --> I[Pattern Analysis]
    E --> J[Import Analysis]
    H --> K[List of PythonQualityViolation]
    I --> K
    J --> K
    
    C --> L[Context filtering]
    L --> M[Filtered violations]
    
    G --> N[stderr reporting]
    M --> N
    N --> O[Exit code to Claude]
```

### Target Modular Data Flow

```mermaid
graph TD
    A[Claude Code Hook] --> B[BaseEnforcer.run()]
    B --> C[BaseEnforcer.get_file_path_from_hook_context()]
    B --> D[PythonEnforcer.apply_automatic_fixes()]
    B --> E[PythonEnforcer.analyze_file()]
    
    D --> F[PythonAutoFixer.apply_fixes()]
    F --> G[ViolationReporter.add_fix()]
    
    E --> H[PythonPatterns analysis]
    H --> I[List of Violation objects]
    I --> J[ViolationReporter.add_violation()]
    
    G --> K[ViolationReporter.report()]
    J --> K
    K --> L[Exit code to Claude]
```

---

## Hook Integration Touch Points

### Claude Code Integration Analysis

**Stdin JSON Parsing (lines 496-523)**:
```python
# Current monolithic implementation
stdin_data = sys.stdin.read()
if stdin_data.strip():
    hook_data = json.loads(stdin_data)
    tool_input = hook_data.get("tool_input", {})
    file_path = Path(tool_input.get("file_path", ""))
    # ... fallback chain
```

**Existing BaseEnforcer implementation (lines 30-62)**:
```python
# Already implemented in BaseEnforcer
def get_file_path_from_hook_context(self) -> Optional[Path]:
    # Same logic as monolithic version
```

**Status**: ✅ **Hook context extraction already implemented in BaseEnforcer**

**Stderr Reporting (lines 558-592)**:
```python
# Current monolithic implementation
if all_fixes:
    print("\n✅ Automatic fixes applied:", file=sys.stderr)
    for fix in all_fixes:
        print(f"  • {fix}", file=sys.stderr)

if all_violations:
    print("🚨 Quality violations found:", file=sys.stderr)
    for violation in all_violations:
        print(f"  {violation}", file=sys.stderr)
    # ... context messages and exit codes
```

**Existing ViolationReporter implementation (lines 53-82)**:
```python
# Already implemented in ViolationReporter
def report(self) -> int:
    # Same emoji formatting and exit codes
```

**Status**: ✅ **Violation reporting already implemented in ViolationReporter**

**Exit Code Handling**:
- `0`: Success (no violations)
- `1`: Analysis failure (exception)
- `2`: Blocking violations found

**Status**: ✅ **Exit codes already handled in ViolationReporter**

---

## Shared vs Language-Specific Logic Breakdown

### Shared Logic (Already Extracted)

| Component | Monolithic Location | Base Class Location | Overlap % |
|-----------|-------------------|-------------------|-----------|
| Hook context parsing | lines 496-523 | BaseEnforcer:30-62 | 95% |
| Violation reporting | lines 558-592 | ViolationReporter:53-82 | 90% |
| Workflow detection | lines 417-487 | WorkflowContext:99-137 | 80% |
| Main orchestration | lines 489-597 | BaseEnforcer:73-96 | 85% |

### Language-Specific Logic (Python-Only)

| Component | Monolithic Location | Lines | Extraction Target |
|-----------|-------------------|--------|------------------|
| Banned imports patterns | lines 57-67 | 11 | PythonPatterns class |
| Anti-patterns regex | lines 78-128 | 51 | PythonPatterns class |
| AST analysis visitor | lines 179-243 | 65 | PythonEnforcer method |
| Pattern analysis | lines 245-294 | 50 | PythonEnforcer method |
| Import analysis | lines 265-294 | 30 | PythonEnforcer method |
| ruff/mypy integration | lines 368-414 | 47 | PythonAutoFixer class |

### Language-Specific Enhancement Needs

**Violation Class Enhancement**:
```python
# Current: PythonQualityViolation
# Target: Enhanced Violation with optional fields

class Violation:
    def __init__(self, ..., ast_node=None, function_name=None, language_context=None):
        # Add Python-specific context fields
```

**Status**: ✅ **Enhancement path identified in SPEC**

---

## Comparison with Existing Base Classes

### BaseEnforcer vs Monolithic main()

| Feature | Monolithic | BaseEnforcer | Action Needed |
|---------|------------|--------------|---------------|
| Hook context extraction | ✅ | ✅ | None - identical |
| File path validation | ✅ | ✅ | None - identical |
| Workflow orchestration | ✅ | ✅ | None - identical |
| Exception handling | ✅ | ✅ | None - identical |
| Abstract methods | ❌ | ✅ | Implement in PythonEnforcer |

### Violation vs PythonQualityViolation

| Feature | PythonQualityViolation | Violation | Action Needed |
|---------|----------------------|-----------|---------------|
| Data fields | 6 fields | 6 fields | None - identical |
| __str__ formatting | ✅ | ✅ | None - identical |
| Severity levels | ✅ | ✅ | None - identical |
| Language context | ❌ | ❌ | Add optional fields |

### ViolationReporter vs Monolithic Reporting

| Feature | Monolithic | ViolationReporter | Action Needed |
|---------|------------|------------------|---------------|
| Emoji formatting | ✅ | ✅ | None - identical |
| Exit codes | ✅ | ✅ | None - identical |
| Context messages | ✅ | ✅ | None - identical |
| Fix reporting | ✅ | ✅ | None - identical |

---

## Extraction Strategy Recommendations

### Phase 1: Direct Replacements (Low Risk)

**Replace PythonQualityViolation with Violation**:
```python
# Current:
violation = PythonQualityViolation(file_path, line_num, type, message, fix, severity)

# Target:
violation = Violation(file_path, line_num, type, message, fix, severity)
```

**Risk**: ⚠️ **Low** - Identical interfaces, no breaking changes

**Replace main() with BaseEnforcer composition**:
```python
# Current: 109 lines of orchestration
def main():
    # Complex hook parsing and orchestration

# Target: 3 lines of composition
def main() -> int:
    enforcer = PythonEnforcer()
    return enforcer.run()
```

**Risk**: ⚠️ **Low** - BaseEnforcer already handles all orchestration

### Phase 2: Class Extractions (Medium Risk)

**Extract PythonAutoFixer**:
```python
# Current: Embedded in PythonPhilosophyEnforcer
class AutomaticQualityFixer:
    def apply_automatic_fixes(self, file_path: Path) -> List[str]

# Target: Standalone composition
class PythonAutoFixer:
    def apply_fixes(self, file_path: Path) -> List[str]
```

**Risk**: ⚠️ **Medium** - Requires interface standardization

**Extract PythonPatterns**:
```python
# Current: Class constants in PythonPhilosophyEnforcer
BANNED_IMPORTS = {...}
ANTIPATTERNS = [...]

# Target: Standalone patterns class
class PythonPatterns:
    @property
    def banned_imports(self) -> Dict[str, str]
    @property  
    def antipatterns(self) -> List[Tuple[str, str]]
```

**Risk**: ⚠️ **Medium** - Pure data extraction, minimal risk

### Phase 3: Core Refactoring (High Complexity)

**Create PythonEnforcer inheriting from BaseEnforcer**:
```python
# Current: PythonPhilosophyEnforcer (287 lines)
class PythonPhilosophyEnforcer:
    def analyze_file(self, file_path: Path) -> List[PythonQualityViolation]

# Target: PythonEnforcer (estimated ~100 lines)
class PythonEnforcer(BaseEnforcer):
    def analyze_file(self, file_path: Path) -> List[Violation]
    def apply_automatic_fixes(self, file_path: Path) -> List[str]
```

**Risk**: ⚠️ **High** - Complex logic migration, requires careful testing

### Phase 4: Workflow Integration (Medium Risk)

**Merge WorkflowContextAwareness with WorkflowContext**:
```python
# Current: Two separate classes with overlapping logic
class WorkflowContextAwareness:  # 71 lines
class WorkflowContext:           # 39 lines

# Target: Enhanced WorkflowContext
class WorkflowContext:           # ~80 lines
    # Combined functionality
```

**Risk**: ⚠️ **Medium** - Logic consolidation, requires interface alignment

---

## Safe Extraction Order

### Recommended Migration Sequence

1. **Phase 1a**: Replace `PythonQualityViolation` with `Violation`
   - **Risk**: Low
   - **Validation**: String formatting tests
   - **Rollback**: Simple class name change

2. **Phase 1b**: Replace `main()` with `BaseEnforcer.run()`
   - **Risk**: Low  
   - **Validation**: Hook integration tests
   - **Rollback**: Restore original main()

3. **Phase 2a**: Extract `PythonAutoFixer`
   - **Risk**: Medium
   - **Validation**: Subprocess integration tests
   - **Rollback**: Inline methods back to main class

4. **Phase 2b**: Extract `PythonPatterns`
   - **Risk**: Medium
   - **Validation**: Pattern matching tests
   - **Rollback**: Inline constants back to main class

5. **Phase 3**: Create `PythonEnforcer(BaseEnforcer)`
   - **Risk**: High
   - **Validation**: Comprehensive integration tests
   - **Rollback**: Restore monolithic class

6. **Phase 4**: Merge workflow context classes
   - **Risk**: Medium
   - **Validation**: Project detection tests
   - **Rollback**: Keep separate classes

### Validation Requirements

**After Each Phase**:
- [ ] All existing tests pass
- [ ] Hook integration works identically
- [ ] Same violations detected on test files
- [ ] Same exit codes returned
- [ ] Performance within 10% of baseline

**Critical Integration Points**:
- [ ] stdin JSON parsing identical
- [ ] stderr formatting identical  
- [ ] Exit code behavior identical
- [ ] File path extraction identical
- [ ] Violation string formatting identical

---

## Risk Assessment

### Low Risk Extractions
- **PythonQualityViolation → Violation**: Identical interfaces
- **main() → BaseEnforcer.run()**: Logic already implemented
- **Hook context parsing**: Already extracted to BaseEnforcer

### Medium Risk Extractions  
- **PythonAutoFixer extraction**: Requires interface standardization
- **PythonPatterns extraction**: Pure data, minimal logic
- **WorkflowContextAwareness merge**: Logic consolidation needed

### High Risk Extractions
- **PythonEnforcer creation**: Complex AST analysis migration
- **Pattern analysis methods**: Sophisticated logic preservation

### Mitigation Strategies

**Incremental Validation**:
- Test hook integration after each phase
- Validate identical behavior with regression test suite
- Maintain monolithic version as fallback during migration

**Rollback Plan**:
- Each phase can be independently reverted
- Comprehensive test suite validates behavior preservation
- Git branching strategy for safe experimentation

---

## Success Metrics

### Quantitative Metrics
- **Code reduction**: 598 lines → ~100 lines (83% reduction)
- **Class count**: 4 classes → 1 primary class + 2 utilities
- **Dependency coupling**: Monolithic → Composition pattern
- **Test coverage**: Maintain >90% coverage through migration

### Qualitative Metrics  
- **Maintainability**: Clear separation of concerns
- **Extensibility**: Ready for JavaScript/Rust enforcers
- **Readability**: Composition over inheritance
- **Testability**: Independent component testing

---

## Next Steps

1. **Validate Analysis**: Review this analysis against HLD and SPEC requirements
2. **Create Test Suite**: Establish comprehensive regression tests for monolithic version
3. **Begin Phase 1**: Start with low-risk PythonQualityViolation replacement
4. **Incremental Migration**: Follow recommended extraction sequence
5. **Continuous Validation**: Test hook integration after each phase

---

*This analysis provides the foundation for safely migrating the monolithic Python enforcer to the modular architecture while preserving 100% functional compatibility with Claude Code hooks.*