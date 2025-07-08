#!/usr/bin/env python3
"""
PreToolUse Hook for claudex-guard

Injects recent violation patterns as context before Claude starts coding.
This creates the learning loop where AI gets smarter about your patterns over time.

Usage: Called automatically by Claude Code PreToolUse hooks
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any


def find_project_memory() -> Path | None:
    """Find .claudex-guard directory by walking up from current directory."""
    current = Path.cwd()
    while current != current.parent:
        memory_dir = current / ".claudex-guard"
        if memory_dir.exists():
            return memory_dir
        current = current.parent
    return None


def get_memory_content(memory_dir: Path) -> str:
    """Get current violation memory content for context injection."""
    memory_file = memory_dir / "memory.md"
    if memory_file.exists():
        return memory_file.read_text(encoding="utf-8").strip()
    return ""


def should_inject_context(hook_data: Dict[str, Any]) -> bool:
    """Determine if we should inject context for this tool call."""
    tool_name = hook_data.get("tool_name", "")

    # Inject context for coding-related tools
    coding_tools = [
        "Write",
        "Edit",
        "MultiEdit",  # File editing
        "Task",  # Agent tasks that might involve coding
    ]

    return tool_name in coding_tools


def create_context_message(memory_content: str) -> str:
    """Create the context injection message for Claude."""
    if not memory_content:
        return ""

    return f"""🧠 **RECENT VIOLATION PATTERNS** (claudex-guard context injection):

{memory_content}

**Note**: These are patterns from your recent coding. Consider them while coding to reduce future violations.
---
"""


def main() -> None:
    """Main entry point for PreToolUse hook."""
    try:
        # Read hook input from stdin
        hook_data = json.load(sys.stdin)

        # Only inject context for coding-related tools
        if not should_inject_context(hook_data):
            sys.exit(0)  # No context injection needed

        # Find project memory
        memory_dir = find_project_memory()
        if not memory_dir:
            sys.exit(0)  # No memory found, continue normally

        # Get memory content
        memory_content = get_memory_content(memory_dir)
        if not memory_content:
            sys.exit(0)  # No violations logged yet

        # Create context message
        context_message = create_context_message(memory_content)

        # Output JSON response to inject context without blocking
        response = {
            "decision": "approve",
            "reason": context_message,
            "suppressOutput": False,
        }

        print(json.dumps(response))
        sys.exit(0)  # Exit code 0 with JSON decision

    except json.JSONDecodeError:
        # Invalid JSON input - just continue normally
        sys.exit(0)
    except Exception as e:
        # Don't break the workflow on any errors
        print(f"claudex-guard context injection failed: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
