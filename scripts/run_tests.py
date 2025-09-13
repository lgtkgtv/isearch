#!/usr/bin/env python3
"""Test runner script with coverage reporting."""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run tests with coverage."""
    project_root = Path(__file__).parent.parent

    print("Running isearch test suite...")

    # Run tests with coverage
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/",
        "--cov=src/isearch",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--verbose",
    ]

    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1


if __name__ == "__main__":
    sys.exit(main())
