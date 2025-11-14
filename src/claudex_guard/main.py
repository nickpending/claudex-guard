#!/usr/bin/env python3
"""
claudex-guard - Universal code quality enforcer with learning capabilities

Main entry point that routes to different modes:
- post: PostToolUse enforcement (default)
- pre: PreToolUse context injection
"""

import argparse
import sys


def main() -> int:
    """Main entry point for claudex-guard."""
    parser = argparse.ArgumentParser(
        prog="claudex-guard",
        description="AI-assisted code quality enforcer with adaptive learning",
        # Allow unrecognized args to pass through to delegated modules
        add_help=False,
    )

    parser.add_argument(
        "--mode",
        default="post",
        choices=["post", "pre"],
        help=(
            "Mode: 'post' for violation detection (default), "
            "'pre' for context injection"
        ),
    )

    parser.add_argument(
        "-h", "--help", action="store_true", help="Show this help message and exit"
    )

    # Parse known args, leave unknown for the delegated module
    args, remaining = parser.parse_known_args()

    # Handle help specially to show our help, not the delegated module's
    if args.help:
        parser.print_help()
        return 0

    # Restore sys.argv for the delegated module (strip out --mode argument)
    sys.argv = [sys.argv[0]] + remaining

    if args.mode == "pre":
        # PreToolUse context injection
        try:
            from .hooks.pre_hook import main as pre_main

            pre_main()
            return 0
        except ImportError as e:
            print(f"Error: PreToolUse module not available: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error: PreToolUse execution failed: {e}", file=sys.stderr)
            return 1
    else:
        # PostToolUse enforcement (default) - multi-language via factory
        try:
            from .core.base_enforcer import BaseEnforcer

            # Extract file path from hook context
            file_path = BaseEnforcer.get_file_path_from_hook_context()

            if not file_path:
                return 0  # No file to analyze - skip gracefully

            # Use factory to route to appropriate enforcer
            # hook_mode=True enables JSON output for Claude Code integration
            return BaseEnforcer.run_for_file(file_path, hook_mode=True)
        except ImportError as e:
            print(f"Error: Enforcer not available: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error: Enforcer execution failed: {e}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    sys.exit(main())
