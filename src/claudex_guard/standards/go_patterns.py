"""Go pattern definitions and analysis logic.

This module defines AI antipatterns specific to Go,
including banned packages, panic abuse, and error ignoring.
"""

import json
import re
import subprocess
from pathlib import Path

from ..core.violation import Violation


class GoPatterns:
    """Go-specific pattern definitions and analysis logic."""

    def __init__(self) -> None:
        """Initialize Go pattern definitions."""
        # Banned packages from AI training data (deprecated)
        self.BANNED_PACKAGES: dict[str, str] = {
            "io/ioutil": (
                "Use io and os packages directly (io/ioutil deprecated in Go 1.16+)"
            ),
            "github.com/pkg/errors": (
                "Use fmt.Errorf with %w for error wrapping (Go 1.13+)"
            ),
        }

    def run_golangci_lint(self, file_path: Path) -> list[Violation]:
        """Run golangci-lint and parse JSON output into Violation objects.

        Args:
            file_path: Path to file to analyze

        Returns:
            List of Violation objects from golangci-lint
        """
        violations: list[Violation] = []

        try:
            result = subprocess.run(
                ["golangci-lint", "run", "--out-format=json", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=file_path.parent,
            )

            # Parse golangci-lint JSON output
            if result.stdout:
                try:
                    output = json.loads(result.stdout)
                    issues = output.get("Issues", [])

                    for issue in issues:
                        # Only report issues for the file being analyzed
                        pos = issue.get("Pos", {})
                        issue_file = pos.get("Filename", "")
                        if not issue_file.endswith(file_path.name):
                            continue

                        line_num = pos.get("Line", 0)
                        from_linter = issue.get("FromLinter", "unknown")

                        violations.append(
                            Violation(
                                file_path=str(file_path),
                                line_num=line_num,
                                violation_type=f"golangci_{from_linter}",
                                message=issue.get("Text", "golangci-lint error"),
                                fix_suggestion="",
                                severity="error",
                                language_context={
                                    "linter": from_linter,
                                    "column": pos.get("Column"),
                                },
                            )
                        )
                except json.JSONDecodeError:
                    # Invalid JSON - skip parsing
                    pass

        except subprocess.TimeoutExpired:
            violations.append(
                Violation(
                    file_path=str(file_path),
                    line_num=0,
                    violation_type="golangci_timeout",
                    message="golangci-lint timed out after 30 seconds",
                    severity="error",
                )
            )
        except FileNotFoundError:
            # golangci-lint not installed - fail with clear error per user decision
            violations.append(
                Violation(
                    file_path=str(file_path),
                    line_num=0,
                    violation_type="golangci_missing",
                    message=(
                        "golangci-lint not found. Install: https://golangci-lint.run/usage/install/"
                    ),
                    severity="error",
                )
            )

        return violations

    def check_banned_packages(self, content: str, file_path: Path) -> list[Violation]:
        """Check for banned package usage from AI training data.

        Args:
            content: File content as string
            file_path: Path to file being analyzed

        Returns:
            List of Violation objects for banned packages
        """
        violations: list[Violation] = []

        for line_num, line in enumerate(content.splitlines(), start=1):
            # Check for import statements
            import_match = re.search(r'import\s+"([^"]+)"', line)
            if import_match:
                package_name = import_match.group(1)

                if package_name in self.BANNED_PACKAGES:
                    violations.append(
                        Violation(
                            file_path=str(file_path),
                            line_num=line_num,
                            violation_type="banned_package_usage",
                            message=(
                                f"Banned package '{package_name}' from AI training data"
                            ),
                            fix_suggestion=self.BANNED_PACKAGES[package_name],
                            severity="error",
                            language_context={"package": package_name},
                        )
                    )

        return violations

    def check_panic_usage(self, lines: list[str], file_path: Path) -> list[Violation]:
        """Check for panic() abuse (AI error handling laziness).

        Args:
            lines: File content as list of lines
            file_path: Path to file being analyzed

        Returns:
            List of Violation objects for panic() usage
        """
        violations: list[Violation] = []

        # Match panic() calls
        panic_pattern = re.compile(r"\bpanic\s*\(")

        for line_num, line in enumerate(lines, start=1):
            if panic_pattern.search(line):
                violations.append(
                    Violation(
                        file_path=str(file_path),
                        line_num=line_num,
                        violation_type="panic_abuse",
                        message="panic() detected (AI error handling laziness)",
                        fix_suggestion=(
                            "Use proper error handling: return error values, "
                            "handle with if err != nil, or use log.Fatal in main()"
                        ),
                        severity="error",
                        language_context={"line_content": line.strip()},
                    )
                )

        return violations

    def check_error_ignoring(
        self, lines: list[str], file_path: Path
    ) -> list[Violation]:
        """Check for error ignoring with _ assignment (AI antipattern).

        Args:
            lines: File content as list of lines
            file_path: Path to file being analyzed

        Returns:
            List of Violation objects for error ignoring
        """
        violations: list[Violation] = []

        # Match patterns like: result, _ := function()
        # where the blank identifier is likely ignoring an error
        error_ignore_pattern = re.compile(r",\s*_\s*:=")

        for line_num, line in enumerate(lines, start=1):
            if error_ignore_pattern.search(line):
                violations.append(
                    Violation(
                        file_path=str(file_path),
                        line_num=line_num,
                        violation_type="error_ignoring",
                        message="Error value ignored with _ (AI antipattern)",
                        fix_suggestion=(
                            "Handle error explicitly: check with if err != nil, "
                            "or use named return value and handle properly"
                        ),
                        severity="warning",
                        language_context={"line_content": line.strip()},
                    )
                )

        return violations
