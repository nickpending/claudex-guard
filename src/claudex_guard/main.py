#!/usr/bin/env python3
"""
claudex-guard - Universal code quality enforcer with learning capabilities

Main entry point that routes to different modes:
- post: PostToolUse enforcement (default)
- pre: PreToolUse context injection
"""

import sys
import argparse


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
        help="Mode: 'post' for violation detection (default), 'pre' for context injection",
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
        # PostToolUse enforcement (default)
        try:
            from .enforcers.python import main as python_main

            return python_main()
        except ImportError as e:
            print(f"Error: Python enforcer not available: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error: Python enforcer execution failed: {e}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    sys.exit(main())
