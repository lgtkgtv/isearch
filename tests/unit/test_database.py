"""Tests for database functionality."""

import pytest
import tempfile
from pathlib import Path
import time

from isearch.core.database import DatabaseManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield DatabaseManager(db_path)


def test_database_initialization(temp_db):
    """Test database initialization."""
    assert temp_db.db_path.exists()

    # Check that tables were created
    stats = temp_db.get_file_stats()
    assert stats["total_files"] == 0


def test_add_and_get_file(temp_db):
    """Test adding and retrieving a file."""
    file_info = {
        "path": "/test/file.txt",
        "filename": "file.txt",
        "directory": "/test",
        "size": 1024,
        "modified_date": time.time(),
        "file_type": "document",
        "extension": ".txt",
    }

    # Add file
    file_id = temp_db.add_file(file_info)
    assert file_id > 0

    # Retrieve file
    retrieved = temp_db.get_file_by_path("/test/file.txt")
    assert retrieved is not None
    assert retrieved["filename"] == "file.txt"
    assert retrieved["size"] == 1024


def test_search_files(temp_db):
    """Test file searching functionality."""
    # Add test files
    files = [
        {
            "path": "/test/document.txt",
            "filename": "document.txt",
            "directory": "/test",
            "size": 1024,
            "modified_date": time.time(),
            "file_type": "document",
            "extension": ".txt",
        },
        {
            "path": "/test/image.jpg",
            "filename": "image.jpg",
            "directory": "/test",
            "size": 2048,
            "modified_date": time.time(),
            "file_type": "image",
            "extension": ".jpg",
        },
    ]

    for file_info in files:
        temp_db.add_file(file_info)

    # Test filename search
    results = temp_db.search_files("document")
    assert len(results) == 1
    assert results[0]["filename"] == "document.txt"

    # Test file type filter
    results = temp_db.search_files(file_type="image")
    assert len(results) == 1
    assert results[0]["file_type"] == "image"

    # Test size filter
    results = temp_db.search_files(min_size=2000)
    assert len(results) == 1
    assert results[0]["size"] == 2048


def test_file_stats(temp_db):
    """Test database statistics."""
    # Add test file
    file_info = {
        "path": "/test/file.txt",
        "filename": "file.txt",
        "directory": "/test",
        "size": 1024,
        "modified_date": time.time(),
        "file_type": "document",
        "extension": ".txt",
    }

    temp_db.add_file(file_info)

    stats = temp_db.get_file_stats()
    assert stats["total_files"] == 1
    assert stats["total_size"] == 1024
    assert len(stats["file_types"]) == 1
    assert stats["file_types"][0]["file_type"] == "document"


def test_scan_session_tracking(temp_db):
    """Test scan session tracking."""
    # Start scan session
    session_id = temp_db.start_scan_session(["/test/dir"])
    assert session_id > 0

    # Update session
    temp_db.update_scan_session(session_id, files_scanned=10, files_added=5)

    # Finish session
    temp_db.finish_scan_session(session_id)
