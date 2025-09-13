# GTK 4 setup

GTK4 (PyGObject) has complex dependencies and can not be installed using UV python virtual environment
We need to install it using **apt**

# The correct packages for PyGObject on Ubuntu:

```
sudo apt update
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0
```

📦 Install Required Packages:
```
# Install PyGObject and GTK4 packages
sudo apt update
sudo apt install -y \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-4.0 \
    libgtk-4-dev \
    libgirepository1.0-dev \
    libcairo2-dev \
    pkg-config \
    python3-dev
```

🔍 Package Name Breakdown:
python3-gi - Python 3 GObject Introspection bindings (this IS PyGObject)
python3-gi-cairo - Cairo integration for drawing/graphics
gir1.2-gtk-4.0 - GTK4 type definitions for GObject Introspection

🧪 Verify Installation: Use Single Quotes (Recommended)
```
# Check if python3-gi is installed
dpkg -l | grep python3-gi

python3 -c 'import gi; gi.require_version("Gtk", "4.0"); from gi.repository import Gtk; print("✅ GTK4 + PyGObject working!")'
```

# Check system python version
```
python3 --version
    python3.12.3
```

# Create the uv environment with system packages access
```
uv venv .venv --python python3.12 --system-site-packages

source .venv/bin/activate

python -c 'import gi; gi.require_version("Gtk", "4.0"); from gi.repository import Gtk; print("✅ GTK4 working with .venv!")'
    ✅ GTK4 working with .venv!
```

# Add development dependencies
uv add --dev pytest pytest-cov black flake8 mypy pre-commit

uv run black --version
uv run pytest --version
uv run mypy --version
