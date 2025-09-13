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

* Code Quality: Black formatting, flake8 linting, mypy type checking
* Testing: Comprehensive test suite with pytest
* Architecture: Clean separation of concerns with modular design
* Security: Safe file operations and input validation

## License
MIT License - see LICENSE file for details.


### Final Verification

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

## Commit Initial Structure

```
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

```
# If GTK4 import fails, reinstall packages
sudo apt install --reinstall python3-gi gir1.2-gtk-4.0

# Check GI_TYPELIB_PATH
echo $GI_TYPELIB_PATH
```

### WSL2 Display Issues

```
# Ensure X11 forwarding is enabled
export DISPLAY=:0
# Or install WSLg for better GUI support
```
