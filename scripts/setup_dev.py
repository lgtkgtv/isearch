#!/usr/bin/env python3
"""Development environment setup script."""

import subprocess
import sys


def run_command(command: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"Running: {description}")
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e.stderr}")
        return False


def main() -> int:
    """Set up development environment."""
    print("Setting up isearch development environment...")

    # Check if we're in a uv-managed project
    tasks = [
        (
            [
                "uv",
                "add",
                "--dev",
                "pytest",
                "pytest-cov",
                "black",
                "flake8",
                "mypy",
                "pre-commit",
            ],
            "Installing dev dependencies with uv",
        ),
        (["uv", "run", "pre-commit", "install"], "Installing pre-commit hooks"),
        (["uv", "run", "pytest", "--version"], "Verifying pytest installation"),
        (["uv", "run", "black", "--version"], "Verifying black installation"),
        (["uv", "run", "flake8", "--version"], "Verifying flake8 installation"),
        (["uv", "run", "mypy", "--version"], "Verifying mypy installation"),
        (
            [
                "python3",
                "-c",
                "import gi; gi.require_version('Gtk', '4.0'); "
                "from gi.repository import Gtk; print('GTK4 working')",
            ],
            "Verifying GTK4 system installation",
        ),
    ]

    success_count = 0
    for command, description in tasks:
        if run_command(command, description):
            success_count += 1

    print(f"\nSetup completed: {success_count}/{len(tasks)} tasks successful")

    if success_count == len(tasks):
        print("\n🎉 Development environment ready!")
        print("You can now run: uv run python -m isearch.main")
        return 0
    else:
        print("\n⚠️  Some tasks failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
