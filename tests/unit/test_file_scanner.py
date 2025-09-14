"""Tests for file scanner functionality."""

import pytest
import tempfile
from pathlib import Path

from isearch.core.database import DatabaseManager
from isearch.core.file_scanner import FileScanner


@pytest.fixture
def temp_scanner():
    """Create a temporary file scanner for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_manager = DatabaseManager(db_path)
        scanner = FileScanner(db_manager)
        yield scanner, Path(tmpdir)


def test_scanner_initialization(temp_scanner):
    """Test scanner initialization."""
    scanner, _ = temp_scanner
    assert scanner.db_manager is not None
    assert scanner._should_stop is False


def test_scan_empty_directory(temp_scanner):
    """Test scanning an empty directory."""
    scanner, temp_dir = temp_scanner

    # Create empty subdirectory
    empty_dir = temp_dir / "empty"
    empty_dir.mkdir()

    results = scanner.scan_directories([str(empty_dir)])

    assert results["files_scanned"] == 0
    assert results["files_added"] == 0
    assert results["directories_scanned"] == 1


def test_scan_directory_with_files(temp_scanner):
    """Test scanning directory with files."""
    scanner, temp_dir = temp_scanner

    # Create test files
    test_dir = temp_dir / "test"
    test_dir.mkdir()

    (test_dir / "file1.txt").write_text("test content 1")
    (test_dir / "file2.jpg").write_text("test content 2")

    results = scanner.scan_directories([str(test_dir)])

    assert results["files_scanned"] == 2
    assert results["files_added"] == 2

    # Verify files in database
    files = scanner.db_manager.search_files()
    assert len(files) == 2

    filenames = [f["filename"] for f in files]
    assert "file1.txt" in filenames
    assert "file2.jpg" in filenames


def test_exclude_patterns(temp_scanner):
    """Test file exclusion patterns."""
    scanner, temp_dir = temp_scanner

    # Create test files
    test_dir = temp_dir / "test"
    test_dir.mkdir()

    (test_dir / "file1.txt").write_text("content")
    (test_dir / "file2.tmp").write_text("content")  # Should be excluded
    (test_dir / "file3.log").write_text("content")  # Should be excluded

    exclude_patterns = ["*.tmp", "*.log"]
    results = scanner.scan_directories([str(test_dir)], exclude_patterns)

    assert results["files_scanned"] == 1
    assert results["files_added"] == 1

    # Verify only .txt file is in database
    files = scanner.db_manager.search_files()
    assert len(files) == 1
    assert files[0]["filename"] == "file1.txt"


def test_progress_callback(temp_scanner):
    """Test progress callback functionality."""
    scanner, temp_dir = temp_scanner

    # Create test files
    test_dir = temp_dir / "test"
    test_dir.mkdir()

    for i in range(5):
        (test_dir / f"file{i}.txt").write_text(f"content {i}")

    # Set up progress callback
    progress_calls = []

    def progress_callback(scanned, total, message):
        progress_calls.append((scanned, total, message))

    scanner.set_progress_callback(progress_callback)
    results = scanner.scan_directories([str(test_dir)])

    assert len(progress_calls) >= 1
    assert results["files_scanned"] == 5


def test_stop_scan(temp_scanner):
    """Test scan stopping functionality."""
    scanner, temp_dir = temp_scanner

    # Create many test files
    test_dir = temp_dir / "test"
    test_dir.mkdir()

    for i in range(100):
        (test_dir / f"file{i}.txt").write_text(f"content {i}")

    # Mock the scan to stop after a few files
    original_process = scanner._process_file
    call_count = 0

    def mock_process_file(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count >= 3:
            scanner.stop_scan()
        return original_process(*args, **kwargs)

    scanner._process_file = mock_process_file

    results = scanner.scan_directories([str(test_dir)])

    # Should have stopped early
    assert results["files_scanned"] < 100


def test_file_type_detection(temp_scanner):
    """Test file type detection."""
    scanner, temp_dir = temp_scanner

    # Create files with different extensions
    test_files = [
        ("document.txt", "document"),
        ("image.jpg", "image"),
        ("video.mp4", "video"),
        ("audio.mp3", "audio"),
        ("archive.zip", "archive"),
        ("code.py", "code"),
        ("unknown.xyz", "other"),
    ]

    for filename, expected_type in test_files:
        (temp_dir / filename).write_text("content")

    scanner.scan_directories([str(temp_dir)])

    # Check file types in database
    for filename, expected_type in test_files:
        file_record = scanner.db_manager.get_file_by_path(str(temp_dir / filename))
        assert file_record["file_type"] == expected_type
