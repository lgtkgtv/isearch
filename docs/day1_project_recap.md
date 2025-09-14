## 🎯 **What Day 1 Accomplishes:**

1. **Complete Project Structure** - Modular, professional layout
2. **GTK4 Environment** - Properly configured for WSL2
3. **Virtual Environment** - Using `uv` as requested
4. **Development Tools** - Black, flake8, mypy, pytest with pre-commit hooks
5. **Application Skeleton** - Basic GTK4 app structure ready for development
6. **Configuration System** - JSON-based config manager with defaults

## 🚀 **Ready to Execute?**

You can run these commands in sequence to get your development environment ready:

```bash
# Start from your desired directory
git clone https://github.com/lgtkgtv/isearch.git
cd isearch

# Follow the setup guide step by step
```

The setup includes:
- **System dependencies** for GTK4 on Ubuntu 24.04
- **Virtual environment** creation with `uv`
- **Complete project structure** with proper Python packaging
- **Development scripts** for automation
- **Quality tools** configured and ready

## 🔧 **Key Features Implemented:**

- **Professional Architecture**: Clean separation with ui/, core/, utils/ modules
- **Type Safety**: Full mypy typing throughout
- **Code Quality**: Black formatting, flake8 linting, pre-commit hooks
- **Testing Ready**: Pytest with coverage reporting configured
- **Configuration Management**: JSON-based settings with defaults

## 📋 **Next Steps After Day 1:**

Once you complete this setup, we'll be ready for:
- **Day 2**: Database schema and file scanner implementation
- **Day 3**: Configuration system completion
- **Days 4-6**: GTK4 UI implementation

Would you like me to:
1. **Walk through any specific part** of the setup in more detail?
2. **Create additional helper scripts** for your development workflow?
3. **Move ahead to Day 2** planning once you complete the setup?

The setup guide is comprehensive but let me know if you encounter any issues with the WSL2 GTK4 setup or `uv` configuration!

===
"uv pip install PyGObject" is failing. what is the right way to add python packages to the venv managed by uv?
===

🧪 Search Method if you want to find the right package names:

```bash
# Search for PyGObject-related packages
apt search pygobject
apt search python3-gi

# Or check what's available
apt list --available | grep -i pygobject
```
🚨 WSL2 Specific Notes:

1. Update package lists first:
```bash
sudo apt update && sudo apt upgrade -y
```

2. Install build essentials if missing:
```bash
sudo apt install build-essential
```

🔧 Fix the Virtual Environment:
Create the uv environment with system packages access

```bash
# Remove the current venv
rm -rf ven

# Create new .venv with system packages access
uv venv .venv --python python3.12 --system-site-packages

source .venv/bin/activate

python -c 'import gi; gi.require_version("Gtk", "4.0"); from gi.repository import Gtk; print("✅ GTK4 working with .venv!")'
    ✅ GTK4 working with .venv!
```

🎯 Why --system-site-packages Helps:

- Allows access to system-installed packages like PyGObject
- Still maintains isolation for packages you install via uv
- Best of both worlds for GUI applications that need system libraries

===
I've updated the setup guide with the correct `uv` syntax and a better approach for handling PyGObject in WSL2. Here's the corrected approach:

## 🔧 **Correct uv Usage:**

**For adding packages:**
```bash
# Add regular dependencies
uv add package-name

# Add development dependencies
uv add --dev package-name

# Run commands in the uv-managed environment
uv run python script.py
uv run pytest
```

**NOT** `uv pip install` (that's the old syntax)

## 🎯 **PyGObject Solution for WSL2:**

Since PyGObject has complex system dependencies (GTK4, GObject Introspection, etc.), the recommended approach is:

1. **Install PyGObject via system packages** (apt)
2. **Use uv for other Python dependencies** (pytest, black, etc.)
3. **Use `uv run`** to execute Python commands in the managed environment

## 📋 **Updated Commands:**

```bash
# 1. System packages for GTK4/PyGObject
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0

    🔍 Package Name Breakdown:

    python3-gi - Python 3 GObject Introspection bindings (this IS PyGObject)
    python3-gi-cairo - Cairo integration for drawing/graphics
    gir1.2-gtk-4.0 - GTK4 type definitions for GObject Introspection

# 2. Create uv project and 📦 Add Development Dependencies:

cd isearch
uv init --python 3.10  # if not already initialized

# Add development tools with uv

uv add --dev pytest pytest-cov black flake8 mypy pre-commit

# Verify they're installed
uv run pytest --version
uv run black --version

# 3. Run your application
uv run python -m isearch.main

# 4. Run tests
uv run pytest

# 5. Format code
uv run black src/
```

## 🚀 **Why This Approach:**

- **System PyGObject**: More reliable for GUI apps in WSL2
- **uv for dev tools**: Clean dependency management for everything else
- **`uv run`**: Ensures you're using the managed environment

Try the updated setup and let me know if PyGObject imports work correctly now! The key is using the system package for PyGObject while letting uv manage the development tools.

🔍 Verify Installation:
```bash
python3 -c 'import gi; gi.require_version("Gtk", "4.0"); from gi.repository import Gtk; print("GTK4 + PyGObject working successfully")'
```

------------------------------------------------------------------------------------

🏗️ Create the Project Structure(files and directories from the Day 1 plan):

```bash
# Create the directory structure
mkdir -p src/isearch/{ui,core,utils,resources/{icons,ui}}
mkdir -p tests/{unit,integration,fixtures/sample_files}
mkdir -p docs scripts

# Create __init__.py files
ll src/__init__.py
ll src/isearch/__init__.py
ll src/isearch/ui/__init__.py
ll src/isearch/core/__init__.py
ll src/isearch/utils/__init__.py
ll tests/__init__.py

# Test that the basic structure works
python -c "print('Project structure ready!')"
# Test development tools
uv run black --check . || echo "Run 'uv run black .' to format code"
```

📄 Create Configuration Files:

**pyproject.toml**                      - Project configuration
**src/isearch/main.py**                 - Main application entry point
**src/isearch/utils/constants.py**      - Application constants
**src/isearch/utils/config_manager.py** - Configuration management

🔧 Fix the Dependency Issue:
Step 1: Update pyproject.toml to Exclude PyGObject

Create/update the pyproject.toml file:
```bash
cat > pyproject.toml << 'EOF'
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
requires-python = ">=3.12"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Topic :: Desktop Environment :: File Managers",
    "Topic :: System :: Filesystems",
]
dependencies = [
    # PyGObject provided by system package (python3-gi)
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
target-version = ['py312']
include = '\.pyi?$'

[tool.mypy]
python_version = "3.12"
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
EOF
```


## Fix tool issues  (flake, mypy, pre-commit)

### Configure `.flake8` to use 88 characters (Black's default)

```bash
cat > .flake8 << 'EOF'
[flake8]
max-line-length = 88
extend-ignore = E203, W503, E402
exclude = .git,__pycache__,docs/source/conf.py,old,build,dist,.venv,venv
EOF
```


### Configure **``mypy.ini``** to be more lenient for GTK4:

```bash
cat > mypy.ini << 'EOF'
[mypy]
python_version = 3.12
warn_return_any = false
warn_unused_configs = true
disallow_untyped_defs = false
ignore_missing_imports = true
show_error_codes = true

[mypy-gi.*]
ignore_missing_imports = true

[mypy-isearch.*]
disallow_untyped_defs = true
EOF
```


### Configure `.pre-commit-config.yaml` to use the new settings:

```bash
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-toml

  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 7.1.1
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        args: [--config-file=mypy.ini]
EOF
```

---------------------------------------------------------------------------------------


## At the end of Day1 we have created these main application files

```
src/isearch/main.py
src/isearch/ui/main_window.py
src/isearch/utils/constants.py
src/isearch/utils/config_manager.py
```

We have NOT yet created these application files
```
src/isearch/ui/config_dialog.py
src/isearch/ui/search_panel.py
src/isearch/ui/results_view.py
src/isearch/core/database.py
src/isearch/core/file_scanner.py
src/isearch/core/search_engine.py
src/isearch/utils/file_utils.py
```

---------------------------------------------------------------------------------------

## Code

### `src/isearch/main.py`

```bash
cat > src/isearch/main.py << 'EOF'
#!/usr/bin/env python3
"""
isearch - Intelligent File Search and Organization Tool

A GTK4-based application for managing, searching, and organizing
large collections of files across multiple directories.
"""

import sys
import logging
from typing import Optional

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio  # noqa: E402

from isearch.ui.main_window import MainWindow  # noqa: E402
from isearch.utils.config_manager import ConfigManager  # noqa: E402
from isearch.utils.constants import APP_ID, APP_NAME, APP_VERSION  # noqa: E402


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
EOF
```

### `src/isearch/ui/main_window.py`

```bash
cat > src/isearch/ui/main_window.py << 'EOF'
"""Main application window for isearch."""

import logging
from typing import Optional, Any

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio  # noqa: E402

from isearch.utils.config_manager import ConfigManager  # noqa: E402
from isearch.utils.constants import (  # noqa: E402
    WINDOW_DEFAULT_WIDTH,
    WINDOW_DEFAULT_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_MIN_HEIGHT,
)


class MainWindow(Gtk.ApplicationWindow):
    """Main application window."""

    def __init__(self, app: Any) -> None:  # Use Any for Gtk.Application
        super().__init__(application=app)

        self.app = app
        self.config_manager: Optional[ConfigManager] = None
        self.logger = logging.getLogger(__name__)

        # UI components
        self.search_entry: Optional[Gtk.Entry] = None
        self.results_label: Optional[Gtk.Label] = None
        self.results_view: Optional[Gtk.TextView] = None
        self.status_label: Optional[Gtk.Label] = None
        self.progress_bar: Optional[Gtk.ProgressBar] = None
        self.regex_check: Optional[Gtk.CheckButton] = None
        self.fullpath_check: Optional[Gtk.CheckButton] = None
        self.images_check: Optional[Gtk.CheckButton] = None
        self.videos_check: Optional[Gtk.CheckButton] = None
        self.docs_check: Optional[Gtk.CheckButton] = None

        # Initialize window
        self._setup_window()
        self._setup_ui()
        self._setup_actions()

        self.logger.info("Main window initialized")

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.set_title("iSearch - File Organizer")
        self.set_default_size(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.set_size_request(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        # Get config manager from app
        if hasattr(self.app, 'get_config_manager'):
            self.config_manager = self.app.get_config_manager()

    def _setup_ui(self) -> None:
        """Create the user interface."""
        # Create main vertical box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(main_box)

        # Create menu bar (placeholder)
        menu_bar = self._create_menu_bar()
        main_box.append(menu_bar)

        # Create toolbar
        toolbar = self._create_toolbar()
        main_box.append(toolbar)

        # Create search panel
        search_panel = self._create_search_panel()
        main_box.append(search_panel)

        # Create main content area
        content_area = self._create_content_area()
        main_box.append(content_area)

        # Create status bar
        status_bar = self._create_status_bar()
        main_box.append(status_bar)

    def _create_menu_bar(self) -> Gtk.Widget:
        """Create the menu bar."""
        # Simple label for now - will implement proper menu later
        menu_bar = Gtk.Label(label="File  Edit  View  Search  Tools  Help")
        menu_bar.set_halign(Gtk.Align.START)
        menu_bar.add_css_class("menu-bar")
        return menu_bar

    def _create_toolbar(self) -> Gtk.Widget:
        """Create the toolbar."""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(6)
        toolbar.set_margin_end(6)
        toolbar.set_margin_top(6)
        toolbar.set_margin_bottom(6)

        # Configure Paths button
        config_btn = Gtk.Button(label="Configure Paths")
        config_btn.connect("clicked", self._on_configure_paths_clicked)
        toolbar.append(config_btn)

        # Refresh DB button
        refresh_btn = Gtk.Button(label="Refresh DB (Ctrl+Shift+R)")
        refresh_btn.connect("clicked", self._on_refresh_db_clicked)
        toolbar.append(refresh_btn)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        toolbar.append(separator)

        # Analysis buttons
        duplicates_btn = Gtk.Button(label="Find Duplicates")
        toolbar.append(duplicates_btn)

        analysis_btn = Gtk.Button(label="Smart Analysis")
        toolbar.append(analysis_btn)

        empty_btn = Gtk.Button(label="Empty Folders")
        toolbar.append(empty_btn)

        return toolbar

    def _create_search_panel(self) -> Gtk.Widget:
        """Create the search panel."""
        search_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        search_box.set_margin_start(6)
        search_box.set_margin_end(6)
        search_box.set_margin_top(6)
        search_box.set_margin_bottom(6)

        # Search row
        search_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        search_label = Gtk.Label(label="Search:")
        search_row.append(search_label)

        # Search entry
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text(
            "Enter filename, path, or regex pattern...")
        self.search_entry.set_hexpand(True)
        search_row.append(self.search_entry)

        # Search button
        search_btn = Gtk.Button(label="Search")
        search_btn.connect("clicked", self._on_search_clicked)
        search_row.append(search_btn)

        # Clear button
        clear_btn = Gtk.Button(label="Clear")
        clear_btn.connect("clicked", self._on_clear_clicked)
        search_row.append(clear_btn)

        search_box.append(search_row)

        # Filter checkboxes
        filter_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        self.regex_check = Gtk.CheckButton(label="Regex Mode")
        filter_row.append(self.regex_check)

        self.fullpath_check = Gtk.CheckButton(label="Full Path")
        filter_row.append(self.fullpath_check)

        self.images_check = Gtk.CheckButton(label="Images Only")
        filter_row.append(self.images_check)

        self.videos_check = Gtk.CheckButton(label="Videos Only")
        filter_row.append(self.videos_check)

        self.docs_check = Gtk.CheckButton(label="Documents Only")
        filter_row.append(self.docs_check)

        search_box.append(filter_row)

        return search_box

    def _create_content_area(self) -> Gtk.Widget:
        """Create the main content area."""
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        content_box.set_margin_start(6)
        content_box.set_margin_end(6)
        content_box.set_vexpand(True)

        # Results header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self.results_label = Gtk.Label(label="Search Results: 0 files found")
        self.results_label.set_halign(Gtk.Align.START)
        self.results_label.set_hexpand(True)
        header_box.append(self.results_label)

        # View mode buttons
        list_btn = Gtk.Button(label="List View")
        list_btn.add_css_class("suggested-action")
        header_box.append(list_btn)

        thumb_btn = Gtk.Button(label="Thumbnail View")
        header_box.append(thumb_btn)

        content_box.append(header_box)

        # Results area (placeholder)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        # Placeholder text view
        self.results_view = Gtk.TextView()
        self.results_view.set_editable(False)
        buffer = self.results_view.get_buffer()
        buffer.set_text("No search performed yet.\n\n"
                       "Try searching for files by entering a filename "
                       "or pattern above.")

        scrolled.set_child(self.results_view)
        content_box.append(scrolled)

        return content_box

    def _create_status_bar(self) -> Gtk.Widget:
        """Create the status bar."""
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        status_box.set_margin_start(6)
        status_box.set_margin_end(6)
        status_box.set_margin_top(3)
        status_box.set_margin_bottom(3)

        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.set_hexpand(True)
        status_box.append(self.status_label)

        # Progress bar (hidden initially)
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_size_request(200, -1)
        self.progress_bar.set_visible(False)
        status_box.append(self.progress_bar)

        return status_box

    def _setup_actions(self) -> None:
        """Set up window actions."""
        # Refresh action
        refresh_action = Gio.SimpleAction.new("refresh_db", None)
        refresh_action.connect("activate", self._on_refresh_db_action)
        self.add_action(refresh_action)

        # Preferences action
        prefs_action = Gio.SimpleAction.new("preferences", None)
        prefs_action.connect("activate", self._on_preferences_action)
        self.add_action(prefs_action)

    def _on_configure_paths_clicked(self, button: Gtk.Button) -> None:
        """Handle configure paths button click."""
        if self.status_label:
            self.status_label.set_text("Configure paths - not implemented yet")
        self.logger.info("Configure paths clicked")

    def _on_refresh_db_clicked(self, button: Gtk.Button) -> None:
        """Handle refresh database button click."""
        if self.status_label:
            self.status_label.set_text("Refresh database - not implemented yet")
        self.logger.info("Refresh database clicked")

    def _on_search_clicked(self, button: Gtk.Button) -> None:
        """Handle search button click."""
        query = ""
        if self.search_entry:
            query = self.search_entry.get_text()
        if self.status_label:
            self.status_label.set_text(f"Search: '{query}' - not implemented yet")
        self.logger.info(f"Search clicked: {query}")

    def _on_clear_clicked(self, button: Gtk.Button) -> None:
        """Handle clear button click."""
        if self.search_entry:
            self.search_entry.set_text("")
        if self.status_label:
            self.status_label.set_text("Search cleared")
        self.logger.info("Search cleared")

    def _on_refresh_db_action(self, action: Gio.SimpleAction,
                             parameter: None) -> None:
        """Handle refresh database action (keyboard shortcut)."""
        self._on_refresh_db_clicked(None)  # type: ignore

    def _on_preferences_action(self, action: Gio.SimpleAction,
                              parameter: None) -> None:
        """Handle preferences action."""
        if self.status_label:
            self.status_label.set_text("Preferences - not implemented yet")
        self.logger.info("Preferences action")
EOF
```

### `src/isearch/utils/constants.py`

```bash
# Create constants.py with all the required constants
cat > src/isearch/utils/constants.py << 'EOF'
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
EOF
```


### `src/isearch/utils/config_manager.py`

```bash
cat > src/isearch/utils/config_manager.py << 'EOF'
"""Configuration management for isearch application."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from isearch.utils.constants import (
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
        """Get configuration value by key path."""
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
        dirs = self.get("scan_directories", [])
        return dirs if isinstance(dirs, list) else []

    def set_scan_directories(self, directories: List[str]) -> None:
        """Set list of directories to scan."""
        self.set("scan_directories", directories)

    def get_exclude_patterns(self) -> List[str]:
        """Get list of exclude patterns."""
        patterns = self.get("exclude_patterns", [])
        return patterns if isinstance(patterns, list) else []

    def set_exclude_patterns(self, patterns: List[str]) -> None:
        """Set list of exclude patterns."""
        self.set("exclude_patterns", patterns)

    def _deep_update(self, base_dict: Dict[str, Any],
                    update_dict: Dict[str, Any]) -> None:
        """Deep update base_dict with update_dict."""
        for key, value in update_dict.items():
            if (key in base_dict and isinstance(base_dict[key], dict) and
                isinstance(value, dict)):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
EOF
```

### `scripts/setup_dev.py`
```bash
cat > scripts/setup_dev.py << 'EOF'
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
        (["uv", "add", "--dev", "pytest", "pytest-cov", "black",
          "flake8", "mypy", "pre-commit"],
         "Installing dev dependencies with uv"),
        (["uv", "run", "pre-commit", "install"],
         "Installing pre-commit hooks"),
        (["uv", "run", "pytest", "--version"],
         "Verifying pytest installation"),
        (["uv", "run", "black", "--version"],
         "Verifying black installation"),
        (["uv", "run", "flake8", "--version"],
         "Verifying flake8 installation"),
        (["uv", "run", "mypy", "--version"],
         "Verifying mypy installation"),
        (["python3", "-c",
          "import gi; gi.require_version('Gtk', '4.0'); "
          "from gi.repository import Gtk; print('GTK4 working')"],
         "Verifying GTK4 system installation"),
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
EOF
```


---------------------------------------------------------------------------------------


## 🧪 Run the code quality checks
```bash
## Format the code with Black
uv run black src/ scripts/

## Check code quality
uv run flake8 src/ scripts/

## Check types (should be much cleaner now)
uv run mypy src/
```

## 🧪 Test the application
```bash
uv run python -m isearch.main
```
