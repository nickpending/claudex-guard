"""TypeScript/JavaScript pattern definitions and analysis logic.

This module defines AI antipatterns specific to TypeScript and JavaScript,
including banned packages, console.log abuse, and type laziness.
"""

import json
import re
import subprocess
from pathlib import Path

from ..core.violation import Violation


class TypeScriptPatterns:
    """TypeScript/JavaScript-specific pattern definitions and analysis logic."""

    def __init__(self) -> None:
        """Initialize TypeScript pattern definitions."""
        # Banned imports from AI training data (deprecated/outdated packages)
        self.BANNED_PACKAGES: dict[str, str] = {
            "moment": "Use date-fns (smaller, tree-shakeable, immutable)",
            "axios": "Use native fetch API (built-in, modern)",
            "lodash": "Use native ES6+ methods (map, filter, reduce)",
            "request": "Use native fetch API (request is deprecated)",
            "underscore": "Use native ES6+ methods",
        }

    def run_eslint(self, file_path: Path) -> list[Violation]:
        """Run ESLint and parse JSON output into Violation objects.

        Args:
            file_path: Path to file to analyze

        Returns:
            List of Violation objects from ESLint
        """
        violations: list[Violation] = []

        try:
            result = subprocess.run(  # noqa: S603, S607
                ["npx", "eslint", "--format", "json", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # ESLint returns exit code 1 when violations found
            if result.stdout:
                try:
                    eslint_results = json.loads(result.stdout)
                    for file_result in eslint_results:
                        for message in file_result.get("messages", []):
                            # Only report errors, skip warnings from ESLint
                            if message.get("severity") == 2:  # 2 = error in ESLint
                                rule_id = message.get("ruleId", "unknown")
                                violations.append(
                                    Violation(
                                        file_path=str(file_path),
                                        line_num=message.get("line", 0),
                                        violation_type=f"eslint_{rule_id}",
                                        message=message.get("message", "ESLint error"),
                                        fix_suggestion=message.get("fix", ""),
                                        severity="error",
                                        language_context={
                                            "rule_id": message.get("ruleId"),
                                            "column": message.get("column"),
                                        },
                                    )
                                )
                except json.JSONDecodeError:
                    # ESLint output not valid JSON - skip
                    pass

        except subprocess.TimeoutExpired:
            violations.append(
                Violation(
                    file_path=str(file_path),
                    line_num=0,
                    violation_type="eslint_timeout",
                    message="ESLint timed out after 30 seconds",
                    severity="error",
                )
            )
        except FileNotFoundError:
            # ESLint not installed - fail with clear error per user decision
            violations.append(
                Violation(
                    file_path=str(file_path),
                    line_num=0,
                    violation_type="eslint_missing",
                    message="ESLint not found. Install with: npm install -g eslint",
                    severity="error",
                )
            )

        return violations

    def run_tsc(self, file_path: Path) -> list[Violation]:
        """Run TypeScript compiler and parse errors into Violation objects.

        Args:
            file_path: Path to TypeScript file to analyze

        Returns:
            List of Violation objects from tsc
        """
        violations: list[Violation] = []

        try:
            result = subprocess.run(  # noqa: S603, S607
                ["tsc", "--noEmit", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Parse tsc output format: "file.ts(line,col): error TS#### message"
            if result.stdout:
                for line in result.stdout.splitlines():
                    match = re.match(
                        r".*\((\d+),(\d+)\):\s+error\s+(TS\d+):\s+(.+)", line
                    )
                    if match:
                        line_num, col, error_code, message = match.groups()
                        violations.append(
                            Violation(
                                file_path=str(file_path),
                                line_num=int(line_num),
                                violation_type=f"typescript_{error_code}",
                                message=f"TypeScript: {message}",
                                severity="error",
                                language_context={
                                    "error_code": error_code,
                                    "column": int(col),
                                },
                            )
                        )

        except subprocess.TimeoutExpired:
            violations.append(
                Violation(
                    file_path=str(file_path),
                    line_num=0,
                    violation_type="tsc_timeout",
                    message="TypeScript compiler timed out after 30 seconds",
                    severity="error",
                )
            )
        except FileNotFoundError:
            # tsc not installed - fail with clear error per user decision
            violations.append(
                Violation(
                    file_path=str(file_path),
                    line_num=0,
                    violation_type="tsc_missing",
                    message=(
                        "TypeScript compiler not found. "
                        "Install with: npm install -g typescript"
                    ),
                    severity="error",
                )
            )

        return violations

    def check_banned_imports(self, content: str, file_path: Path) -> list[Violation]:
        """Check for banned package imports from AI training data.

        Args:
            content: File content as string
            file_path: Path to file being analyzed

        Returns:
            List of Violation objects for banned imports
        """
        violations: list[Violation] = []

        for line_num, line in enumerate(content.splitlines(), start=1):
            # Check for import statements
            import_match = re.match(
                r"^\s*import\s+.*\s+from\s+['\"]([^'\"]+)['\"]", line
            )
            if import_match:
                package_name = import_match.group(1)
                # Extract base package name (e.g., "moment" from "moment/locale/en")
                base_package = package_name.split("/")[0]

                if base_package in self.BANNED_PACKAGES:
                    violations.append(
                        Violation(
                            file_path=str(file_path),
                            line_num=line_num,
                            violation_type="banned_package_import",
                            message=(
                                f"Banned package '{base_package}' from AI training data"
                            ),
                            fix_suggestion=self.BANNED_PACKAGES[base_package],
                            severity="error",
                            language_context={"package": base_package},
                        )
                    )

        return violations

    def check_console_usage(self, lines: list[str], file_path: Path) -> list[Violation]:
        """Check for console.log/warn/error usage (AI debug remnants).

        Args:
            lines: File content as list of lines
            file_path: Path to file being analyzed

        Returns:
            List of Violation objects for console usage
        """
        violations: list[Violation] = []

        console_pattern = re.compile(r"\bconsole\.(log|warn|error|debug|info)\(")

        for line_num, line in enumerate(lines, start=1):
            if console_pattern.search(line):
                violations.append(
                    Violation(
                        file_path=str(file_path),
                        line_num=line_num,
                        violation_type="console_usage",
                        message="Console statement detected (AI debug remnant)",
                        fix_suggestion=(
                            "Use proper logging library (e.g., winston, pino)"
                        ),
                        severity="warning",
                        language_context={"line_content": line.strip()},
                    )
                )

        return violations
