"""Tests for search engine functionality."""

import pytest
import tempfile
import time
from pathlib import Path

from isearch.core.database import DatabaseManager
from isearch.core.search_engine import SearchEngine, SearchFilters


@pytest.fixture
def search_setup():
    """Create search engine with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)
        search_engine = SearchEngine(db_manager)

        # Add test files
        test_files = [
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
            {
                "path": "/test/backup/duplicate.txt",
                "filename": "document.txt",  # Same name as first file
                "directory": "/test/backup",
                "size": 1024,
                "modified_date": time.time(),
                "file_type": "document",
                "extension": ".txt",
            },
        ]

        for file_info in test_files:
            db_manager.add_file(file_info)

        yield search_engine


def test_basic_search(search_setup):
    """Test basic search functionality."""
    search_engine = search_setup

    filters = SearchFilters(query="document")
    results = search_engine.search(filters)

    assert len(results) == 2  # Both document files
    filenames = [r["filename"] for r in results]
    assert "document.txt" in filenames


def test_file_type_filter(search_setup):
    """Test file type filtering."""
    search_engine = search_setup

    filters = SearchFilters(file_types=["image"])
    results = search_engine.search(filters)

    assert len(results) == 1
    assert results[0]["file_type"] == "image"


def test_size_filter(search_setup):
    """Test size filtering."""
    search_engine = search_setup

    filters = SearchFilters(min_size=2000)
    results = search_engine.search(filters)

    assert len(results) == 1
    assert results[0]["size"] == 2048


def test_regex_search(search_setup):
    """Test regex search."""
    search_engine = search_setup

    filters = SearchFilters(query=r".*\.txt$", use_regex=True)
    results = search_engine.search(filters)

    assert len(results) == 2  # Both .txt files


def test_path_search(search_setup):
    """Test path-based search."""
    search_engine = search_setup

    filters = SearchFilters(query="backup", search_path=True)
    results = search_engine.search(filters)

    assert len(results) == 1
    assert "backup" in results[0]["directory"]


def test_duplicate_detection(search_setup):
    """Test duplicate file detection."""
    search_engine = search_setup

    duplicates = search_engine.search_duplicates(method="size_name")

    # Should find one duplicate group (same name and size)
    assert len(duplicates) == 1

    # The duplicate group should have 2 files
    duplicate_group = list(duplicates.values())[0]
    assert len(duplicate_group) == 2


def test_similarity_search(search_setup):
    """Test similarity search."""
    search_engine = search_setup

    similar = search_engine.search_similar_files("/test/document.txt")

    # Should find the other document.txt as similar
    assert len(similar) >= 1
    similar_names = [f["filename"] for f in similar]
    assert "document.txt" in similar_names


def test_search_suggestions(search_setup):
    """Test search suggestions."""
    search_engine = search_setup

    suggestions = search_engine.get_search_suggestions("doc")

    assert len(suggestions) > 0
    assert any("document" in s.lower() for s in suggestions)


def test_invalid_regex(search_setup):
    """Test handling of invalid regex."""
    search_engine = search_setup

    filters = SearchFilters(query="[invalid", use_regex=True)
    results = search_engine.search(filters)

    # Should return empty results for invalid regex
    assert len(results) == 0


def test_empty_search(search_setup):
    """Test search with no results."""
    search_engine = search_setup

    filters = SearchFilters(query="nonexistent")
    results = search_engine.search(filters)

    assert len(results) == 0


def test_multiple_file_types(search_setup):
    """Test searching multiple file types."""
    search_engine = search_setup

    filters = SearchFilters(file_types=["document", "image"])
    results = search_engine.search(filters)

    assert len(results) == 3  # All test files

    types = [r["file_type"] for r in results]
    assert "document" in types
    assert "image" in types
