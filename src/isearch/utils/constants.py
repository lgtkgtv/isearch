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
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp",
    ".svg",
    ".ico",
    ".raw",
    ".cr2",
    ".nef",
    ".arw",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mkv",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".m4v",
    ".3gp",
    ".ogv",
    ".ts",
    ".m2ts",
    ".mts",
}

DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".txt",
    ".rtf",
    ".odt",
    ".ods",
    ".odp",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".csv",
}

# UI constants
WINDOW_DEFAULT_WIDTH = 1200
WINDOW_DEFAULT_HEIGHT = 800
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600

# Search constants
SEARCH_DEBOUNCE_MS = 300
MAX_SEARCH_RESULTS = 10000


# File type detection
def get_file_type(extension: str) -> str:
    """Determine file type from extension."""
    ext_lower = extension.lower()

    if ext_lower in IMAGE_EXTENSIONS:
        return "image"
    elif ext_lower in VIDEO_EXTENSIONS:
        return "video"
    elif ext_lower in DOCUMENT_EXTENSIONS:
        return "document"
    elif ext_lower in {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}:
        return "audio"
    elif ext_lower in {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"}:
        return "archive"
    elif ext_lower in {".py", ".js", ".html", ".css", ".cpp", ".c", ".java"}:
        return "code"
    else:
        return "other"
