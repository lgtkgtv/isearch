# Day 1: Project Setup Guide for isearch

## Environment Setup for Ubuntu 24.04 WSL2

### Step 1: Install System Dependencies

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install GTK4 development libraries
sudo apt install -y \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-4.0 \
    libgtk-4-dev \
    libgirepository1.0-dev \
    libcairo2-dev \
    pkg-config \
    python3-dev

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Verify uv installation
uv --version
```

### Step 2: Clone Repository and Setup Virtual Environment

```bash
# Clone your repository
git clone https://github.com/lgtkgtv/isearch.git
cd isearch

# Create virtual environment with uv
uv venv venv

# Activate virtual environment
source venv/bin/activate

# Verify Python version
python --version
```

### Step 3: Create Project Structure

```bash
# Create main source directories
mkdir -p src/isearch/{ui,core,utils,resources/{icons,ui}}
mkdir -p tests/{unit,integration,fixtures/sample_files}
mkdir -p docs
mkdir -p scripts

# Create __init__.py files
touch src/__init__.py
touch src/isearch/__init__.py
touch src/isearch/ui/__init__.py
touch src/isearch/core/__init__.py
touch src/isearch/utils/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py

# Create main application files
touch src/isearch/main.py
touch src/isearch/ui/main_window.py
touch src/isearch/ui/config_dialog.py
touch src/isearch/ui/search_panel.py
touch src/isearch/ui/results_view.py
touch src/isearch/core/database.py
touch src/isearch/core/file_scanner.py
touch src/isearch/core/search_engine.py
touch src/isearch/utils/config_manager.py
touch src/isearch/utils/file_utils.py
touch src/isearch/utils/constants.py

# Create test files
touch tests/unit/test_database.py
touch tests/unit/test_file_scanner.py
touch tests/unit/test_search_engine.py
touch tests/unit/test_config_manager.py
touch tests/integration/test_full_workflow.py

# Create documentation files
touch docs/README.md
touch docs/ARCHITECTURE.md
touch docs/API_REFERENCE.md
touch docs/USER_GUIDE.md

# Create script files
touch scripts/setup_dev.py
touch scripts/run_tests.py
```

### Step 4: Create Configuration Files

#### pyproject.toml
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "isearch"
version = "0.1.0"
description = "A GTK4-based file organizer and search utility"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Desktop Environment :: File Managers",
    "Topic :: System :: Filesystems",
]
dependencies = [
    "PyGObject>=3.42.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "flake8>=4.0.0",
    "mypy>=1.0.0",
    "pre-commit>=2.20.0",
]

[project.urls]
Homepage = "https://github.com/lgtkgtv/isearch"
Repository = "https://github.com/lgtkgtv/isearch"
Issues = "https://github.com/lgtkgtv/isearch/issues"

[project.scripts]
isearch = "isearch.main:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 88
target-version = ['py310']
include = '\.pyi?$'

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src/isearch --cov-report=html --cov-report=term-missing"
```

#### requirements.txt (for uv)
```txt
# Core dependencies
PyGObject>=3.42.0

# Development dependencies (optional)
pytest>=7.0.0
pytest-cov>=4.0.0
black>=22.0.0
flake8>=4.0.0
mypy>=1.0.0
pre-commit>=2.20.0
```

#### .gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/

# OS
.DS_Store
Thumbs.db

# Application specific
*.db
*.sqlite
*.sqlite3
config.json
logs/
cache/

# WSL specific
.wslconfig
```

#### .pre-commit-config.yaml
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-toml

  - repo: https://github.com/psf/black
    rev: 22.10.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 5.0.4
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.991
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Step 5: Install Dependencies with uv

```bash
# Install core dependencies
uv pip install PyGObject

# Install development dependencies
uv pip install pytest pytest-cov black flake8 mypy pre-commit

# Verify GTK4 installation
python -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk; print('GTK4 installed successfully')"

# Install pre-commit hooks
pre-commit install
```

### Step 6: Create Initial Application Structure

#### src/isearch/main.py
```python
#!/usr/bin/env python3
"""
isearch - Intelligent File Search and Organization Tool

A GTK4-based application for managing, searching, and organizing
large collections of files across multiple directories.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gio

from isearch.ui.main_window import MainWindow
from isearch.utils.config_manager import ConfigManager
from isearch.utils.constants import APP_ID, APP_NAME, APP_VERSION


class ISearchApplication(Gtk.Application):
    """Main application class for isearch."""

    def __init__(self) -> None:
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )

        self.config_manager: Optional[ConfigManager] = None
        self.main_window: Optional[MainWindow] = None

        # Set up logging
        self._setup_logging()

        logging.info(f"Starting {APP_NAME} v{APP_VERSION}")

    def _setup_logging(self) -> None:
        """Configure application logging."""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
            ]
        )

    def do_activate(self) -> None:
        """Activate the application."""
        if not self.main_window:
            # Initialize configuration manager
            self.config_manager = ConfigManager()

            # Create and show main window
            self.main_window = MainWindow(self)
            self.main_window.present()
        else:
            self.main_window.present()

    def do_startup(self) -> None:
        """Initialize the application."""
        Gtk.Application.do_startup(self)

        # Set up application-wide accelerators
        self._setup_accelerators()

    def _setup_accelerators(self) -> None:
        """Set up keyboard shortcuts."""
        # Ctrl+Shift+R for refresh
        self.set_accels_for_action("win.refresh_db", ["<Ctrl><Shift>R"])

        # Ctrl+Q for quit
        self.set_accels_for_action("app.quit", ["<Ctrl>Q"])

        # Ctrl+, for preferences
        self.set_accels_for_action("win.preferences", ["<Ctrl>comma"])

    def get_config_manager(self) -> ConfigManager:
        """Get the configuration manager instance."""
        if not self.config_manager:
            self.config_manager = ConfigManager()
        return self.config_manager


def main() -> int:
    """Main entry point for the application."""
    app = ISearchApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
```

#### src/isearch/utils/constants.py
```python
"""Application constants and configuration."""

from pathlib import Path

# Application metadata
APP_ID = "com.github.lgtkgtv.isearch"
APP_NAME = "iSearch"
APP_VERSION = "0.1.0"

# File paths
HOME_DIR = Path.home()
CONFIG_DIR = HOME_DIR / ".config" / "isearch"
CACHE_DIR = HOME_DIR / ".cache" / "isearch"
DATA_DIR = HOME_DIR / ".local" / "share" / "isearch"

# Database
DEFAULT_DB_PATH = DATA_DIR / "files.db"

# Configuration
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.json"

# File type categories
IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
    '.webp', '.svg', '.ico', '.raw', '.cr2', '.nef', '.arw'
}

VIDEO_EXTENSIONS = {
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
    '.m4v', '.3gp', '.ogv', '.ts', '.m2ts', '.mts'
}

DOCUMENT_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.ods',
    '.odp', '.xls', '.xlsx', '.ppt', '.pptx', '.csv'
}

# UI constants
WINDOW_DEFAULT_WIDTH = 1200
WINDOW_DEFAULT_HEIGHT = 800
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600

# Search constants
SEARCH_DEBOUNCE_MS = 300
MAX_SEARCH_RESULTS = 10000
```

#### src/isearch/utils/config_manager.py
```python
"""Configuration management for isearch application."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from isearch.utils.constants import (
    CONFIG_DIR,
    DEFAULT_CONFIG_PATH,
    WINDOW_DEFAULT_WIDTH,
    WINDOW_DEFAULT_HEIGHT,
)


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.logger = logging.getLogger(__name__)
        self._config: Dict[str, Any] = {}

        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Load configuration
        self.load_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "version": "1.0",
            "scan_directories": [
                str(Path.home() / "Pictures"),
                str(Path.home() / "Documents"),
            ],
            "exclude_patterns": [
                "*.tmp",
                "*.log",
                "*/.git/*",
                "*/node_modules/*",
                "*/__pycache__/*",
                "*.pyc",
            ],
            "scan_options": {
                "follow_symlinks": True,
                "scan_hidden": False,
                "calculate_hashes": False,
                "max_file_size_mb": 1000,
            },
            "ui_preferences": {
                "window_width": WINDOW_DEFAULT_WIDTH,
                "window_height": WINDOW_DEFAULT_HEIGHT,
                "thumbnail_size": 150,
                "show_hidden_files": False,
                "remember_window_state": True,
            },
            "search_options": {
                "case_sensitive": False,
                "regex_enabled": False,
                "search_content": False,
                "max_results": 10000,
            }
        }

    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)

                # Merge with defaults to ensure all keys exist
                self._config = self.get_default_config()
                self._deep_update(self._config, loaded_config)

                self.logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self._config = self.get_default_config()
                self.save_config()
                self.logger.info("Created default configuration")

        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Error loading config: {e}")
            self._config = self.get_default_config()

    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Configuration saved to {self.config_path}")
        except IOError as e:
            self.logger.error(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key path (e.g., 'ui_preferences.window_width')."""
        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key path."""
        keys = key.split('.')
        config = self._config

        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the value
        config[keys[-1]] = value

    def get_scan_directories(self) -> List[str]:
        """Get list of directories to scan."""
        return self.get("scan_directories", [])

    def set_scan_directories(self, directories: List[str]) -> None:
        """Set list of directories to scan."""
        self.set("scan_directories", directories)

    def get_exclude_patterns(self) -> List[str]:
        """Get list of exclude patterns."""
        return self.get("exclude_patterns", [])

    def set_exclude_patterns(self, patterns: List[str]) -> None:
        """Set list of exclude patterns."""
        self.set("exclude_patterns", patterns)

    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
        """Deep update base_dict with update_dict."""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
```

### Step 7: Create Development Scripts

#### scripts/setup_dev.py
```python
#!/usr/bin/env python3
"""Development environment setup script."""

import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e.stderr}")
        return False


def main() -> int:
    """Set up development environment."""
    project_root = Path(__file__).parent.parent

    print("Setting up isearch development environment...")

    # Check if we're in a uv-managed project
    tasks = [
        (["uv", "add", "--dev", "pytest", "pytest-cov", "black", "flake8", "mypy", "pre-commit"], "Installing dev dependencies with uv"),
        (["uv", "run", "pre-commit", "install"], "Installing pre-commit hooks"),
        (["uv", "run", "pytest", "--version"], "Verifying pytest installation"),
        (["uv", "run", "black", "--version"], "Verifying black installation"),
        (["uv", "run", "flake8", "--version"], "Verifying flake8 installation"),
        (["uv", "run", "mypy", "--version"], "Verifying mypy installation"),
        (["python3", "-c", "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk; print('GTK4 working')"], "Verifying GTK4 system installation"),
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
```

#### scripts/run_tests.py
```python
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
        "python", "-m", "pytest",
        "tests/",
        "--cov=src/isearch",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--verbose"
    ]

    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

### Step 8: Create README.md

```markdown
# iSearch - Intelligent File Search and Organization Tool

A GTK4-based application for managing, searching, and organizing large collections of files across multiple directories.

## Features

- **Fast File Discovery**: Recursively scan directories and build searchable database
- **Flexible Search**: Substring, regex, and path-based searching
- **File Type Filtering**: Quick filters for images, videos, and documents
- **Clean Interface**: Modern GTK4 interface optimized for productivity
- **Configurable**: Customizable scan directories and exclude patterns

## Development Status

🚧 **MVP Phase** - Core functionality under development

## Requirements

- Python 3.10+
- GTK4
- Ubuntu 24.04+ (primary target)

## Installation

### Development Setup

```bash
# Clone repository
git clone https://github.com/lgtkgtv/isearch.git
cd isearch

# Create virtual environment with uv
uv venv venv
source venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Set up development environment
python scripts/setup_dev.py

# Run the application
python -m isearch.main
```

## Project Structure

```
isearch/
├── src/isearch/          # Main application code
│   ├── ui/              # GTK4 user interface
│   ├── core/            # Business logic
│   └── utils/           # Utility functions
├── tests/               # Test suite
├── docs/                # Documentation
└── scripts/             # Development scripts
```

## Contributing

This project follows professional software development practices:

- **Code Quality**: Black formatting, flake8 linting, mypy type checking
- **Testing**: Comprehensive test suite with pytest
- **Architecture**: Clean separation of concerns with modular design
- **Security**: Safe file operations and input validation

## License

MIT License - see LICENSE file for details.
```

### Step 9: Final Verification

```bash
# Verify project structure
find . -type f -name "*.py" | head -10

# Test imports
python -c "from isearch.utils.constants import APP_NAME; print(f'✓ {APP_NAME} imports working')"

# Run basic tests (will mostly be empty for now)
python -m pytest tests/ -v

# Verify GTK4 is working
python -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk; print('✓ GTK4 ready')"

# Check code formatting
black --check src/ || echo "Run 'black src/' to format code"

# Run development setup
python scripts/setup_dev.py
```

### Step 10: Commit Initial Structure

```bash
# Add all files to git
git add .

# Commit initial structure
git commit -m "Initial project structure and Day 1 setup

- Created modular project structure with src/isearch layout
- Added GTK4 dependencies and uv virtual environment
- Implemented basic application skeleton and config manager
- Set up development tools (pytest, black, flake8, mypy)
- Added pre-commit hooks and code quality standards
- Created development scripts for setup and testing
- Configured project metadata in pyproject.toml"

# Push to GitHub
git push origin main
```

## Troubleshooting

### GTK4 Import Issues
```bash
# If GTK4 import fails, reinstall packages
sudo apt install --reinstall python3-gi gir1.2-gtk-4.0

# Check GI_TYPELIB_PATH
echo $GI_TYPELIB_PATH
```

### WSL2 Display Issues
```bash
# Ensure X11 forwarding is enabled
export DISPLAY=:0
# Or install WSLg for better GUI support
```

This completes Day 1 setup! You now have a professional, well-structured Python project ready for GTK4 development.
