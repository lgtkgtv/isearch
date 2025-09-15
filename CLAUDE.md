# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

iSearch is a GTK4-based intelligent file search and organization tool for Linux. It provides fast file discovery, flexible search capabilities, and duplicate detection across large collections of files.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment with uv
uv venv .venv
source .venv/bin/activate

# Install dependencies (PyGObject uses system package)
uv pip install -r requirements.txt

# Alternative: Install development dependencies only
# uv sync --dev

# Set up pre-commit hooks
uv run pre-commit install
```

**System Dependencies Required:**
- `python3-gi` (PyGObject - GTK4 Python bindings)
- `gir1.2-gtk-4.0` (GTK4 introspection data)
- These should be installed via system package manager, not pip/uv

### Running the Application
```bash
# Run the main application
python -m isearch.main

# Alternative: Run directly
python src/isearch/main.py
```

### Testing
```bash
# Run all tests with coverage
uv run pytest tests/ -v --cov=src/isearch --cov-report=html --cov-report=term-missing

# Run specific test file
uv run pytest tests/unit/test_database.py -v

# Run specific test
uv run pytest tests/unit/test_database.py::TestDatabaseManager::test_initialization -v

# Quick test run without coverage
uv run pytest tests/ -v
```

### Code Quality
```bash
# Format code with Black
uv run black src/ tests/

# Check formatting without changes
uv run black --check src/ tests/

# Run linting with flake8
uv run flake8 src/ tests/

# Type checking with mypy
uv run mypy src/

# Run all pre-commit hooks manually
uv run pre-commit run --all-files
```

## Architecture Overview

### Core Components

1. **Database Layer** (`src/isearch/core/database.py`)
   - SQLite-based metadata storage
   - Thread-safe operations with context managers
   - Stores file metadata: path, size, dates, type, hash
   - Supports duplicate detection via file hashes

2. **File Scanner** (`src/isearch/core/file_scanner.py`)
   - Recursively scans directories
   - Builds searchable database of file metadata
   - Excludes patterns configurable
   - Progress callbacks for UI updates

3. **Search Engine** (`src/isearch/core/search_engine.py`)
   - Supports substring, regex, and path-based searching
   - File type filtering (images, videos, documents)
   - SearchFilters class for query parameters

4. **Duplicate Detector** (`src/isearch/core/duplicate_detector.py`)
   - Hash-based duplicate identification
   - Groups duplicates by content hash
   - Supports bulk operations on duplicate sets

### UI Architecture

- **Main Window** (`src/isearch/ui/main_window.py`): Primary application interface with search, scan controls, and results display
- **Duplicate Window** (`src/isearch/ui/duplicate_window.py`): Specialized interface for duplicate file management
- **Config Dialog** (`src/isearch/ui/config_dialog.py`): Settings management interface
- **Search Panel** (`src/isearch/ui/search_panel.py`): Search input and filter controls
- **Results View** (`src/isearch/ui/results_view.py`): File results display component

### Configuration

- **Config Manager** (`src/isearch/utils/config_manager.py`): JSON-based configuration persistence
- Default config location: `~/.config/isearch/config.json`
- Stores scan directories, exclude patterns, UI preferences

## Key Dependencies

- **PyGObject**: GTK4 Python bindings (system package: `python3-gi`)
- **GTK4**: Modern GUI toolkit (system package: `gir1.2-gtk-4.0`)
- **SQLite3**: Built-in database for metadata storage

## Testing Strategy

- **Unit Tests** (`tests/unit/`): Test individual components in isolation
- **Integration Tests** (`tests/integration/`): Test component interactions
- **Fixtures** (`tests/fixtures/`): Shared test data and mock objects
- Tests use pytest with coverage reporting

## Development Workflow

1. Always run tests before committing changes
2. Use pre-commit hooks to ensure code quality
3. Follow Black formatting (88 char line length)
4. Type hints required (enforced by mypy strict mode)
5. Flake8 for linting with E203, W503, E402 exceptions

## GTK4 Considerations

- Requires `gi.require_version("Gtk", "4.0")` before imports
- Use GLib.idle_add() for thread-safe UI updates
- Application ID: `com.lgtkgtv.isearch`
- WSL2 users need X11 forwarding or WSLg for GUI

## Database Schema

Primary table: `files`
- id: Primary key
- path: Unique file path
- filename, directory, size, modified_date
- file_type, extension, hash (for duplicates)
- scan_date, created_at, updated_at

Indexes on: filename, directory, extension, hash, size

## Common Development Tasks

### Adding a New Feature
1. Create feature branch from main
2. Implement with tests
3. Run full test suite
4. Check formatting and linting
5. Update documentation if needed

### Debugging GTK4 Issues
```bash
# Check GTK4 availability
python -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk; print('GTK4 ready')"

# Enable GTK debug output
GTK_DEBUG=all python -m isearch.main
```

### Building for Distribution
```bash
# Build package with setuptools
python -m build

# Install locally for testing
pip install -e .
```
