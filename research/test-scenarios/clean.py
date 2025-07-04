#!/usr/bin/env python3
"""
Clean test file with no violations for hook integration testing.

This file follows all claudex-guard-python standards and should
pass without any violations reported.
"""

from pathlib import Path
from typing import Optional

import httpx


def process_file(file_path: Path) -> Optional[str]:
    """Process a file and return its contents."""
    if not file_path.exists():
        return None

    return file_path.read_text(encoding="utf-8")


def format_message(name: str) -> str:
    """Format a greeting message using f-strings."""
    return f"Hello, {name}!"


def safe_operation() -> bool:
    """Perform operation with proper error handling."""
    try:
        result = 1 / 1
        return True
    except ZeroDivisionError as e:
        # Proper exception handling with logging context
        print(f"Division error: {e}")
        return False


async def fetch_data(url: str) -> dict[str, str]:
    """Fetch data using modern httpx library."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()


def main() -> None:
    """Main entry point."""
    config_path = Path("config.json")
    content = process_file(config_path)

    if content:
        message = format_message("World")
        print(message)


if __name__ == "__main__":
    main()
