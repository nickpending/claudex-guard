"""Rust pattern definitions and analysis logic.

This module defines AI antipatterns specific to Rust,
including banned crates, .unwrap() abuse, and outdated dependencies.
"""

import json
import re
import subprocess
from pathlib import Path

from ..core.violation import Violation


class RustPatterns:
    """Rust-specific pattern definitions and analysis logic."""

    def __init__(self) -> None:
        """Initialize Rust pattern definitions."""
        # Banned crates from AI training data (deprecated/outdated versions)
        self.BANNED_CRATES: dict[str, str] = {
            "time": "Use chrono (maintained, feature-rich) or std::time (built-in)",
            "rand": "Use rand 0.8+ (current version, not 0.7 or older)",
            "tempdir": "Use tempfile crate (tempdir is deprecated)",
            "error-chain": "Use thiserror or anyhow (modern error handling)",
        }

    def run_clippy(self, file_path: Path) -> list[Violation]:
        """Run Clippy and parse JSON output into Violation objects.

        Args:
            file_path: Path to file to analyze

        Returns:
            List of Violation objects from Clippy
        """
        violations: list[Violation] = []

        try:
            result = subprocess.run(
                [
                    "cargo",
                    "clippy",
                    "--message-format=json",
                    "--",
                    "-Dwarnings",
                ],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=file_path.parent,
            )

            # Parse Clippy JSON output (one JSON object per line)
            if result.stdout:
                for line in result.stdout.splitlines():
                    if not line.strip():
                        continue
                    try:
                        message = json.loads(line)
                        # Clippy messages have reason "compiler-message"
                        if message.get("reason") != "compiler-message":
                            continue

                        compiler_message = message.get("message", {})
                        if compiler_message.get("level") not in {"error", "warning"}:
                            continue

                        # Extract span information (file location)
                        spans = compiler_message.get("spans", [])
                        if not spans:
                            continue

                        primary_span = spans[0]
                        span_file = primary_span.get("file_name", "")

                        # Only report violations for the file being analyzed
                        if not span_file.endswith(file_path.name):
                            continue

                        line_num = primary_span.get("line_start", 0)
                        code = compiler_message.get("code", {})
                        code_str = code.get("code", "unknown") if code else "unknown"

                        violations.append(
                            Violation(
                                file_path=str(file_path),
                                line_num=line_num,
                                violation_type=f"clippy_{code_str}",
                                message=compiler_message.get("message", "Clippy error"),
                                fix_suggestion="",
                                severity=(
                                    "error"
                                    if compiler_message.get("level") == "error"
                                    else "warning"
                                ),
                                language_context={
                                    "code": code_str,
                                    "column": primary_span.get("column_start"),
                                },
                            )
                        )
                    except json.JSONDecodeError:
                        # Invalid JSON line - skip
                        continue

        except subprocess.TimeoutExpired:
            violations.append(
                Violation(
                    file_path=str(file_path),
                    line_num=0,
                    violation_type="clippy_timeout",
                    message="Clippy timed out after 30 seconds",
                    severity="error",
                )
            )
        except FileNotFoundError:
            # Cargo/Clippy not installed - fail with clear error per user decision
            violations.append(
                Violation(
                    file_path=str(file_path),
                    line_num=0,
                    violation_type="clippy_missing",
                    message=(
                        "Clippy not found. Install Rust toolchain: https://rustup.rs"
                    ),
                    severity="error",
                )
            )

        return violations

    def check_banned_crates(self, content: str, file_path: Path) -> list[Violation]:
        """Check for banned crate usage from AI training data.

        Args:
            content: File content as string
            file_path: Path to file being analyzed

        Returns:
            List of Violation objects for banned crates
        """
        violations: list[Violation] = []

        for line_num, line in enumerate(content.splitlines(), start=1):
            # Check for use statements
            use_match = re.match(r"^\s*use\s+([a-zA-Z_][a-zA-Z0-9_]*)", line)
            if use_match:
                crate_name = use_match.group(1)

                if crate_name in self.BANNED_CRATES:
                    violations.append(
                        Violation(
                            file_path=str(file_path),
                            line_num=line_num,
                            violation_type="banned_crate_usage",
                            message=(
                                f"Banned crate '{crate_name}' from AI training data"
                            ),
                            fix_suggestion=self.BANNED_CRATES[crate_name],
                            severity="error",
                            language_context={"crate": crate_name},
                        )
                    )

        return violations

    def check_unwrap_usage(self, lines: list[str], file_path: Path) -> list[Violation]:
        """Check for .unwrap() abuse (AI error handling laziness).

        Args:
            lines: File content as list of lines
            file_path: Path to file being analyzed

        Returns:
            List of Violation objects for .unwrap() usage
        """
        violations: list[Violation] = []

        # Match .unwrap() but not .unwrap_or() or .unwrap_or_else()
        unwrap_pattern = re.compile(r"\.unwrap\(\)(?!\w)")

        for line_num, line in enumerate(lines, start=1):
            if unwrap_pattern.search(line):
                violations.append(
                    Violation(
                        file_path=str(file_path),
                        line_num=line_num,
                        violation_type="unwrap_abuse",
                        message=".unwrap() detected (AI error handling laziness)",
                        fix_suggestion=(
                            "Use ? operator, .unwrap_or(), .unwrap_or_else(), "
                            "or proper error handling with match/if let"
                        ),
                        severity="error",
                        language_context={"line_content": line.strip()},
                    )
                )

        return violations
