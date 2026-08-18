---
type: project
domain: technical
status: active
started: 2025-07-04
---
# claudex-guard - Core Idea

## The Problem

**What specific problem does this solve?**

AI coding assistants repeatedly forget your development standards and waste time with basic quality violations, forcing developers to constantly re-explain preferences and manually catch violations after they're written. This creates:

- Repetitive quality discussions in every AI conversation
- AI assistants making the same mistakes repeatedly (mutable defaults, banned imports, etc.)
- No learning from past violations - same patterns emerge week after week
- Manual post-hoc code review catching violations after they're written
- Massive CLAUDE.local.md files that AI assistants often ignore
- No adaptive feedback loop to improve AI assistant behavior over time

**Who has this problem?**

Software developers using AI coding assistants who want their AI to actually learn and internalize their specific coding patterns and preferences, rather than starting from scratch every conversation.

**How do they solve it today?**

Manual repetition and prayer:

- Copy-pasting coding standards into every AI conversation
- Massive CLAUDE.local.md files with every possible rule
- Manual post-hoc linting and code review
- Repeatedly explaining the same violations (mutable defaults, banned imports)
- No system to track what violations keep happening
- No way for AI to learn from past mistakes

## The Solution

**Core Value Proposition**

A complete AI-assisted development workflow orchestration system that creates an adaptive learning loop: violations are caught automatically, patterns are learned, and AI assistants receive targeted context injection before coding, eliminating repetitive explanations and progressively improving code quality.

**Key Differentiators**

- **Adaptive Learning**: AI gets smarter about YOUR specific patterns over time
- **PreToolUse Context Injection**: Recent violation patterns injected before coding starts
- **PostToolUse Enforcement**: Comprehensive violation detection and automatic fixes
- **Lean Configuration**: Small, focused CLAUDE.local.md files that work with automation
- **Complete Workflow Integration**: Handles both prevention (context) and detection (enforcement)
- **Language-Agnostic Architecture**: Extensible to any programming language

## User Experience Vision

**The Complete Learning Loop**

1. **Before Coding**: AI receives targeted reminders ("You've used mutable defaults 3x this week")
2. **During Coding**: AI codes with awareness of your recent patterns
3. **After Coding**: Violations caught automatically, logged for learning
4. **Over Time**: AI progressively learns your patterns, makes fewer repeat mistakes

**Success Criteria**

- Zero repeated explanations of the same coding violations
- AI assistants progressively internalize your specific patterns
- Dramatic reduction in repeat violations over time
- Lean, focused CLAUDE.local.md files that AI actually follows
- Development velocity maintained while quality improves exponentially

## Features Status

**Status Legend:**

- 📋 **Planned** - Feature defined and ready for iteration planning
- 🔄 **In Progress** - Feature currently being developed
- ✅ **Built** - Feature completed and shipped

### Core Enforcement System (Built)

- ✅ **Python quality enforcement** with comprehensive AST pattern detection
- ✅ **Claude Code PostToolUse integration** with hook system
- ✅ **Automatic fixes** via ruff formatting and linting
- ✅ **Modular architecture** (661→89 lines, 87% code reduction)
- ✅ **Security violation detection** (eval, exec patterns)
- ✅ **Modern Python pattern enforcement** (f-strings, pathlib, type hints)
- ✅ **Environment management standards** (uv over pip/poetry)
- ✅ **Comprehensive testing** (27 tests: integration + unit)
- 🔄 **Universal router system** - Single hook entry point that detects file types and routes to appropriate enforcers

### Learning System (New Evolution)

- 📋 **PreToolUse context injection system** - Inject recent violation patterns before coding
- 📋 **Violation pattern learning** - Track and analyze your specific mistakes over time
- 📋 **Adaptive reminder system** - Context-aware reminders based on recent patterns
- 📋 **Learning loop integration** - Complete violation → pattern → injection cycle

### Configuration Evolution

- 📋 **Lean CLAUDE.local.md system** - Focused workflow files that work with automation
- 📋 **CLAUDE.local.md templates** - Language-specific lean configuration templates
- 📋 **Documentation refactoring** - Massive standards files → automated enforcement

### Language Expansion

- 📋 **JavaScript/TypeScript enforcement** with ESLint integration
- 📋 **Rust enforcement** with clippy integration
- 📋 **Go enforcement** with standard toolchain integration
- 📋 **Universal learning system** - Pattern learning across all languages

### Advanced Features

- 📋 **Project-specific rule customization** via .claudex.yaml
- 📋 **VS Code extension** for real-time enforcement
- 📋 **Team learning** - Shared violation patterns across team members

## Technical Approach

**Architecture Decision: Adaptive Learning Ecosystem**

A two-phase system that both prevents and learns from violations:

**Phase 1: PreToolUse Context Injection**

- Analyze recent violation patterns from logs
- Generate targeted, specific reminders
- Inject context before AI coding begins
- Combine with "Actually Works" protocol for comprehensive guidance

**Phase 2: PostToolUse Enforcement & Learning**

- Comprehensive violation detection and automatic fixes
- Log violations to `~/.claude/violation_history.jsonl`
- Pattern analysis for future context injection
- Standards enforcement with educational guidance

**Why this approach?**

Creates a complete learning loop where AI assistants actually improve over time rather than repeating the same mistakes. Combines immediate enforcement with predictive prevention.

## System Architecture

```
claudex-guard Ecosystem:
├── Router System (NEW)
│   └── claudex-guard.py           # Universal entry point, detects file types
├── PreToolUse System (PLANNED)
│   ├── python_pre.py             # Context injection before coding
│   ├── pattern_analyzer.py       # Analyze violation patterns
│   └── context_injector.py       # Generate targeted reminders
├── PostToolUse System (BUILT)
│   ├── python.py                 # Comprehensive enforcement (89 lines)
│   ├── python_patterns.py        # Pattern detection logic
│   └── python_auto_fixer.py      # Automatic fixing via ruff/mypy
├── Learning System (PLANNED)
│   ├── violation_tracker.py      # Log and analyze violations
│   ├── pattern_recognition.py    # Identify recurring patterns
│   └── learning_loop.py          # Complete learning cycle
├── Configuration System (PLANNED)
│   ├── claude_local_templates/   # Lean CLAUDE.local.md templates
│   └── template_generator.py     # Generate language-specific configs
└── Core Infrastructure (BUILT)
    ├── base_enforcer.py          # Foundation for all enforcers
    ├── violation.py              # Enhanced violation reporting
    └── utils.py                  # Shared utilities
```

## The Learning Loop Architecture

**Data Flow:**

1. **Violation Logging**: PostToolUse logs violations to `~/.claude/violation_history.jsonl`
2. **Pattern Analysis**: PreToolUse analyzes recent patterns (last week/month)
3. **Context Generation**: Smart reminders generated based on your specific patterns
4. **Context Injection**: Targeted context injected before AI codes
5. **Improved Coding**: AI codes with awareness of your recent mistakes
6. **Reduced Violations**: Fewer repeat violations logged over time

**Example Learning Cycle:**

```
Week 1: Claude uses mutable defaults 4x → PostToolUse catches all
Week 2: PreToolUse injects "You've used mutable defaults 4x this week" 
Week 3: Claude codes with awareness → Only 1 mutable default
Week 4: Pattern learned → Zero mutable defaults
```

## Configuration Philosophy Evolution

**OLD Approach**: Massive CLAUDE.local.md files with every rule  
**NEW Approach**: Lean configuration + smart automation

**Lean CLAUDE.local.md contains:**

- Critical workflow blockers (environment hell prevention)
- High-level development philosophy
- Developer identity ("Call me Mate")
- Emergency debugging workflows
- Reference to automated enforcement ("claudex-guard handles syntax automatically")

**Automated System handles:**

- All detailed syntax and pattern rules
- Specific violation detection and fixes
- Learning from past mistakes
- Adaptive context injection

## Implementation Strategy

**Phase 1: PreToolUse Learning System** (Current Priority)

- Build violation pattern analyzer
- Implement context injection system
- Integrate with existing PostToolUse hooks
- Create learning loop infrastructure

**Phase 2: Configuration Refactoring**

- Create CLAUDE.local.md templates for each language
- Refactor existing massive configuration files
- Implement template generation system

**Phase 3: Language Expansion**

- Extend learning system to JavaScript/TypeScript
- Implement Rust and Go enforcers
- Create universal pattern learning across languages

**Phase 4: Advanced Features**

- Team learning and shared patterns
- VS Code extension integration
- Advanced customization and configuration

## Integration Points

**Claude Code Hook System:**

```json
{
  "hooks": {
    "PreToolUse": [{
      "hooks": [{"type": "command", "command": "claudex-guard-pre"}]
    }],
    "PostToolUse": [{
      "hooks": [{"type": "command", "command": "claudex-guard"}]
    }]
  }
}
```

**Note**: Claude Code hooks fire on all events without file filtering - the router system detects file types and routes to appropriate language enforcers.

**Learning Data Storage:**

- `~/.claude/violation_history.jsonl` - Timestamped violation logs
- `~/.claude/pattern_analysis.json` - Analyzed patterns and frequencies
- `~/.claude/context_cache.json` - Generated context for injection

## Success Metrics

**Learning Effectiveness:**

- Reduction in repeat violations over time (target: 80% reduction in 4 weeks)
- AI assistant adaptation rate to personal patterns
- Frequency of specific violation types decreasing

**Developer Experience:**

- Time spent explaining coding standards (target: near zero)
- Development velocity maintained or improved
- Code quality consistency across all AI-assisted sessions

**System Performance:**

- Context injection latency (<100ms)
- Pattern analysis accuracy (>90% relevant patterns)
- Learning loop effectiveness (patterns recognized within 1 week)

## Risks and Assumptions

**Key Assumptions:**

- AI assistants can effectively learn from structured, targeted context
- Pattern analysis can identify meaningful recurring violations
- Developers want adaptive learning over static rule enforcement
- PreToolUse context injection will improve coding behavior

**Primary Risks:**

- Context injection becoming too verbose or noisy
- Pattern analysis generating false positives
- Learning system creating feedback loops or bad patterns
- Performance impact from dual-phase enforcement

**Mitigation Strategies:**

- Smart context filtering (only top 3 recent patterns)
- Pattern validation and confidence scoring
- Manual override capabilities for all automated systems
- Performance monitoring and optimization
- Gradual rollout with extensive testing

## Open Questions

**Learning System Questions:**

- What's the optimal learning window? (1 week, 1 month, adaptive?)
- How to handle false positive patterns?
- Should learning be project-specific or global?
- How to handle edge cases where violations are intentional?

**Context Injection Questions:**

- What's the optimal context length for AI assistant attention?
- How to balance recent patterns vs. persistent issues?
- Should context be combined with other workflow reminders?
- How to prevent context injection from becoming noise?

**Evolution Questions:**

- How to migrate existing massive CLAUDE.local.md files?
- What's the best approach for team-shared learning?
- How to handle conflicting patterns across different projects?
- Should the system learn coding style preferences beyond violations?

---

## Current Status

**Built Foundation:**

- ✅ Comprehensive Python PostToolUse enforcement
- ✅ Modular architecture ready for extension
- ✅ 27 comprehensive tests ensuring reliability
- ✅ Production-ready violation detection and automatic fixes

**Next Major Evolution:**

- 🔄 **PreToolUse learning system** - Context injection based on violation patterns
- 🔄 **CLAUDE.local.md refactoring** - Lean configuration templates
- 🔄 **Learning loop integration** - Complete adaptive feedback system

**Vision Achieved:** Transform claudex-guard from "code quality enforcement tool" into "adaptive AI development workflow orchestration system" that creates AI assistants that actually learn and improve over time.

This represents a fundamental shift in AI-assisted development: from repetitive rule explanation to adaptive learning partnerships.