# Day 2: Database Schema & File Scanner Implementation

## 🎯 Day 2 Objectives

Transform your working GTK4 interface into a functional file discovery system by implementing:
1. **SQLite Database Schema** - Structured file metadata storage
2. **File Scanner Engine** - Recursive directory traversal with progress reporting
3. **Basic Search Functionality** - Query the database and display results
4. **Integration** - Connect the UI to the backend systems

## 📋 Implementation Plan

### Phase 1: Database Foundation (90 minutes)
- Create SQLite schema with proper indexing
- Implement database manager with CRUD operations
- Add database initialization and migration support
- Create comprehensive tests

### Phase 2: File Scanner Engine (120 minutes)
- Build recursive file discovery system
- Implement exclude pattern matching
- Add progress reporting and cancellation
- Handle file system errors gracefully

### Phase 3: Search Engine (60 minutes)
- Create search query builder
- Implement filtering by file type, size, date
- Add regex and path-based searching
- Optimize query performance

### Phase 4: UI Integration (90 minutes)
- Connect database to UI components
- Implement progress indicators
- Wire up search functionality
- Add basic file operations

---

## 🗄️ Phase 1: Database Implementation

### Step 1: Create the Database Schema

```bash
# Create the database module
cat > src/isearch/core/database.py << 'EOF'
"""Database management for file metadata storage."""

import logging
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from isearch.utils.constants import DATA_DIR, DEFAULT_DB_PATH


class DatabaseManager:
    """Manages SQLite database operations for file metadata."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize database with schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create main files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL UNIQUE,
                    filename TEXT NOT NULL,
                    directory TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    modified_date REAL NOT NULL,
                    created_date REAL,
                    file_type TEXT NOT NULL,
                    extension TEXT,
                    hash TEXT,
                    is_hidden BOOLEAN DEFAULT 0,
                    is_symlink BOOLEAN DEFAULT 0,
                    scan_date REAL DEFAULT (datetime('now')),
                    created_at REAL DEFAULT (datetime('now')),
                    updated_at REAL DEFAULT (datetime('now'))
                )
            """)

            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_filename
                ON files(filename)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_path
                ON files(path)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_directory
                ON files(directory)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_type
                ON files(file_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_size
                ON files(size)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_modified
                ON files(modified_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_extension
                ON files(extension)
            """)

            # Create scan_sessions table for tracking scan operations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scan_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time REAL NOT NULL,
                    end_time REAL,
                    status TEXT DEFAULT 'running',
                    files_scanned INTEGER DEFAULT 0,
                    files_added INTEGER DEFAULT 0,
                    files_updated INTEGER DEFAULT 0,
                    files_removed INTEGER DEFAULT 0,
                    directories_scanned TEXT,
                    error_message TEXT,
                    created_at REAL DEFAULT (datetime('now'))
                )
            """)

            conn.commit()
            self.logger.info("Database initialized successfully")

    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper locking."""
        with self._lock:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row  # Enable column access by name
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent access
            try:
                yield conn
            finally:
                conn.close()

    def add_file(self, file_info: Dict[str, Any]) -> int:
        """Add a file record to the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO files (
                    path, filename, directory, size, modified_date,
                    created_date, file_type, extension, hash,
                    is_hidden, is_symlink, scan_date, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                str(file_info['path']),
                file_info['filename'],
                str(file_info['directory']),
                file_info['size'],
                file_info['modified_date'],
                file_info.get('created_date'),
                file_info['file_type'],
                file_info.get('extension', ''),
                file_info.get('hash'),
                file_info.get('is_hidden', False),
                file_info.get('is_symlink', False)
            ))

            conn.commit()
            return cursor.lastrowid

    def get_file_by_path(self, path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Get file record by path."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE path = ?", (str(path),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def search_files(self, query: str = "",
                    file_type: Optional[str] = None,
                    directory: Optional[str] = None,
                    min_size: Optional[int] = None,
                    max_size: Optional[int] = None,
                    modified_after: Optional[float] = None,
                    modified_before: Optional[float] = None,
                    use_regex: bool = False,
                    search_path: bool = False,
                    limit: int = 10000) -> List[Dict[str, Any]]:
        """Search files with various filters."""

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic query
            conditions = []
            params = []

            # Text search
            if query:
                if use_regex:
                    # SQLite doesn't support regex directly, use LIKE with wildcards
                    search_field = "path" if search_path else "filename"
                    conditions.append(f"{search_field} LIKE ?")
                    params.append(f"%{query}%")
                else:
                    search_field = "path" if search_path else "filename"
                    conditions.append(f"{search_field} LIKE ? COLLATE NOCASE")
                    params.append(f"%{query}%")

            # File type filter
            if file_type:
                conditions.append("file_type = ?")
                params.append(file_type)

            # Directory filter
            if directory:
                conditions.append("directory LIKE ?")
                params.append(f"{directory}%")

            # Size filters
            if min_size is not None:
                conditions.append("size >= ?")
                params.append(min_size)

            if max_size is not None:
                conditions.append("size <= ?")
                params.append(max_size)

            # Date filters
            if modified_after is not None:
                conditions.append("modified_date >= ?")
                params.append(modified_after)

            if modified_before is not None:
                conditions.append("modified_date <= ?")
                params.append(modified_before)

            # Build final query
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            sql = f"""
                SELECT * FROM files
                WHERE {where_clause}
                ORDER BY filename ASC
                LIMIT ?
            """
            params.append(limit)

            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_file_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total files
            cursor.execute("SELECT COUNT(*) as total FROM files")
            total_files = cursor.fetchone()['total']

            # Total size
            cursor.execute("SELECT SUM(size) as total_size FROM files")
            total_size = cursor.fetchone()['total_size'] or 0

            # File type breakdown
            cursor.execute("""
                SELECT file_type, COUNT(*) as count, SUM(size) as size
                FROM files
                GROUP BY file_type
                ORDER BY count DESC
            """)
            file_types = [dict(row) for row in cursor.fetchall()]

            # Recent files
            cursor.execute("""
                SELECT COUNT(*) as recent_count
                FROM files
                WHERE scan_date >= datetime('now', '-7 days')
            """)
            recent_files = cursor.fetchone()['recent_count']

            return {
                'total_files': total_files,
                'total_size': total_size,
                'file_types': file_types,
                'recent_files': recent_files,
                'database_path': str(self.db_path)
            }

    def remove_missing_files(self, scanned_paths: set) -> int:
        """Remove files that no longer exist from the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get all current file paths
            cursor.execute("SELECT id, path FROM files")
            all_files = cursor.fetchall()

            removed_count = 0
            for file_record in all_files:
                if file_record['path'] not in scanned_paths:
                    cursor.execute("DELETE FROM files WHERE id = ?",
                                 (file_record['id'],))
                    removed_count += 1

            conn.commit()
            if removed_count > 0:
                self.logger.info(f"Removed {removed_count} missing files")

            return removed_count

    def start_scan_session(self, directories: List[str]) -> int:
        """Start a new scan session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scan_sessions (start_time, directories_scanned)
                VALUES (datetime('now'), ?)
            """, ("|".join(directories),))
            conn.commit()
            return cursor.lastrowid

    def update_scan_session(self, session_id: int,
                           files_scanned: int = 0,
                           files_added: int = 0,
                           files_updated: int = 0,
                           status: str = "running") -> None:
        """Update scan session progress."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE scan_sessions
                SET files_scanned = ?, files_added = ?, files_updated = ?,
                    status = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (files_scanned, files_added, files_updated, status, session_id))
            conn.commit()

    def finish_scan_session(self, session_id: int,
                           files_removed: int = 0,
                           error_message: Optional[str] = None) -> None:
        """Complete a scan session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            status = "error" if error_message else "completed"
            cursor.execute("""
                UPDATE scan_sessions
                SET end_time = datetime('now'), status = ?,
                    files_removed = ?, error_message = ?
                WHERE id = ?
            """, (status, files_removed, error_message, session_id))
            conn.commit()

    def vacuum_database(self) -> None:
        """Optimize database by running VACUUM."""
        with self._get_connection() as conn:
            conn.execute("VACUUM")
            self.logger.info("Database vacuumed")

    def get_database_size(self) -> int:
        """Get database file size in bytes."""
        return self.db_path.stat().st_size if self.db_path.exists() else 0
EOF
```

### Step 2: Create Database Tests

```bash
# Create test file for database
cat > tests/unit/test_database.py << 'EOF'
"""Tests for database functionality."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
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
    assert stats['total_files'] == 0


def test_add_and_get_file(temp_db):
    """Test adding and retrieving a file."""
    file_info = {
        'path': '/test/file.txt',
        'filename': 'file.txt',
        'directory': '/test',
        'size': 1024,
        'modified_date': time.time(),
        'file_type': 'document',
        'extension': '.txt'
    }

    # Add file
    file_id = temp_db.add_file(file_info)
    assert file_id > 0

    # Retrieve file
    retrieved = temp_db.get_file_by_path('/test/file.txt')
    assert retrieved is not None
    assert retrieved['filename'] == 'file.txt'
    assert retrieved['size'] == 1024


def test_search_files(temp_db):
    """Test file searching functionality."""
    # Add test files
    files = [
        {
            'path': '/test/document.txt',
            'filename': 'document.txt',
            'directory': '/test',
            'size': 1024,
            'modified_date': time.time(),
            'file_type': 'document',
            'extension': '.txt'
        },
        {
            'path': '/test/image.jpg',
            'filename': 'image.jpg',
            'directory': '/test',
            'size': 2048,
            'modified_date': time.time(),
            'file_type': 'image',
            'extension': '.jpg'
        }
    ]

    for file_info in files:
        temp_db.add_file(file_info)

    # Test filename search
    results = temp_db.search_files("document")
    assert len(results) == 1
    assert results[0]['filename'] == 'document.txt'

    # Test file type filter
    results = temp_db.search_files(file_type="image")
    assert len(results) == 1
    assert results[0]['file_type'] == 'image'

    # Test size filter
    results = temp_db.search_files(min_size=2000)
    assert len(results) == 1
    assert results[0]['size'] == 2048


def test_file_stats(temp_db):
    """Test database statistics."""
    # Add test file
    file_info = {
        'path': '/test/file.txt',
        'filename': 'file.txt',
        'directory': '/test',
        'size': 1024,
        'modified_date': time.time(),
        'file_type': 'document',
        'extension': '.txt'
    }

    temp_db.add_file(file_info)

    stats = temp_db.get_file_stats()
    assert stats['total_files'] == 1
    assert stats['total_size'] == 1024
    assert len(stats['file_types']) == 1
    assert stats['file_types'][0]['file_type'] == 'document'


def test_scan_session_tracking(temp_db):
    """Test scan session tracking."""
    # Start scan session
    session_id = temp_db.start_scan_session(['/test/dir'])
    assert session_id > 0

    # Update session
    temp_db.update_scan_session(session_id, files_scanned=10, files_added=5)

    # Finish session
    temp_db.finish_scan_session(session_id)
EOF
```

### Step 3: Update Constants for File Types

```bash
# Update constants with file type detection
cat >> src/isearch/utils/constants.py << 'EOF'

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
    elif ext_lower in {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac'}:
        return "audio"
    elif ext_lower in {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'}:
        return "archive"
    elif ext_lower in {'.py', '.js', '.html', '.css', '.cpp', '.c', '.java'}:
        return "code"
    else:
        return "other"
EOF
```

### Step 4: Test the Database Implementation

```bash
# Run the database tests
uv run python -m pytest tests/unit/test_database.py -v

# Test database creation manually
uv run python -c "
from isearch.core.database import DatabaseManager
db = DatabaseManager()
print('Database created successfully!')
print(f'Stats: {db.get_file_stats()}')
"
```

---

## 📁 Phase 2: File Scanner Implementation

### Step 5: Create the File Scanner

```bash
# Create the file scanner module
cat > src/isearch/core/file_scanner.py << 'EOF'
"""File system scanning and discovery functionality."""

import fnmatch
import logging
import os
import stat
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from isearch.core.database import DatabaseManager
from isearch.utils.constants import get_file_type


class FileScanner:
    """Scans directories and maintains file database."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self._should_stop = False
        self._progress_callback: Optional[Callable[[int, int, str], None]] = None

    def set_progress_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """Set callback for progress updates."""
        self._progress_callback = callback

    def stop_scan(self) -> None:
        """Request to stop the current scan."""
        self._should_stop = True
        self.logger.info("Scan stop requested")

    def scan_directories(self,
                        directories: List[str],
                        exclude_patterns: Optional[List[str]] = None,
                        follow_symlinks: bool = True,
                        scan_hidden: bool = False,
                        calculate_hashes: bool = False) -> Dict[str, Any]:
        """
        Scan directories and update database.

        Returns:
            Dictionary with scan statistics
        """
        self._should_stop = False
        exclude_patterns = exclude_patterns or []

        # Start scan session
        session_id = self.db_manager.start_scan_session(directories)

        stats = {
            'files_scanned': 0,
            'files_added': 0,
            'files_updated': 0,
            'files_removed': 0,
            'directories_scanned': 0,
            'errors': 0,
            'start_time': time.time(),
            'scanned_paths': set()
        }

        try:
            for directory in directories:
                if self._should_stop:
                    break

                dir_path = Path(directory)
                if not dir_path.exists():
                    self.logger.warning(f"Directory does not exist: {directory}")
                    continue

                self.logger.info(f"Scanning directory: {directory}")
                self._scan_directory(
                    dir_path,
                    exclude_patterns,
                    follow_symlinks,
                    scan_hidden,
                    calculate_hashes,
                    stats
                )

                stats['directories_scanned'] += 1

                # Update progress
                if self._progress_callback:
                    self._progress_callback(
                        stats['files_scanned'],
                        0,  # Total unknown during scan
                        f"Scanned {stats['files_scanned']} files"
                    )

            # Remove missing files if scan completed
            if not self._should_stop:
                removed = self.db_manager.remove_missing_files(stats['scanned_paths'])
                stats['files_removed'] = removed

            # Finish scan session
            stats['end_time'] = time.time()
            stats['duration'] = stats['end_time'] - stats['start_time']

            self.db_manager.update_scan_session(
                session_id,
                stats['files_scanned'],
                stats['files_added'],
                stats['files_updated'],
                "completed" if not self._should_stop else "cancelled"
            )

            self.db_manager.finish_scan_session(session_id, stats['files_removed'])

            self.logger.info(f"Scan completed: {stats}")
            return stats

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Scan failed: {error_msg}")
            self.db_manager.finish_scan_session(session_id, error_message=error_msg)
            stats['error'] = error_msg
            return stats

    def _scan_directory(self,
                       directory: Path,
                       exclude_patterns: List[str],
                       follow_symlinks: bool,
                       scan_hidden: bool,
                       calculate_hashes: bool,
                       stats: Dict[str, Any]) -> None:
        """Recursively scan a directory."""

        try:
            for item in directory.iterdir():
                if self._should_stop:
                    break

                # Skip hidden files/directories if not requested
                if not scan_hidden and item.name.startswith('.'):
                    continue

                # Check exclude patterns
                if self._should_exclude(item, exclude_patterns):
                    continue

                try:
                    if item.is_file():
                        self._process_file(item, calculate_hashes, stats)
                    elif item.is_dir():
                        # Handle symlinks
                        if item.is_symlink() and not follow_symlinks:
                            continue

                        # Recursively scan subdirectory
                        self._scan_directory(
                            item,
                            exclude_patterns,
                            follow_symlinks,
                            scan_hidden,
                            calculate_hashes,
                            stats
                        )

                except (OSError, PermissionError) as e:
                    self.logger.debug(f"Cannot access {item}: {e}")
                    stats['errors'] += 1
                    continue

        except (OSError, PermissionError) as e:
            self.logger.warning(f"Cannot scan directory {directory}: {e}")
            stats['errors'] += 1

    def _process_file(self,
                     file_path: Path,
                     calculate_hashes: bool,
                     stats: Dict[str, Any]) -> None:
        """Process a single file."""
        try:
            # Get file stats
            file_stat = file_path.stat()

            # Skip if file is too large (configurable limit)
            max_size = 10 * 1024 * 1024 * 1024  # 10GB default
            if file_stat.st_size > max_size:
                self.logger.debug(f"Skipping large file: {file_path}")
                return

            # Prepare file info
            file_info = {
                'path': str(file_path),
                'filename': file_path.name,
                'directory': str(file_path.parent),
                'size': file_stat.st_size,
                'modified_date': file_stat.st_mtime,
                'created_date': getattr(file_stat, 'st_birthtime', file_stat.st_ctime),
                'file_type': get_file_type(file_path.suffix),
                'extension': file_path.suffix.lower(),
                'is_hidden': file_path.name.startswith('.'),
                'is_symlink': file_path.is_symlink()
            }

            # Calculate hash if requested
            if calculate_hashes:
                file_info['hash'] = self._calculate_file_hash(file_path)

            # Check if file already exists in database
            existing = self.db_manager.get_file_by_path(str(file_path))

            if existing is None:
                # New file
                self.db_manager.add_file(file_info)
                stats['files_added'] += 1
            elif existing['modified_date'] != file_stat.st_mtime or existing['size'] != file_stat.st_size:
                # File was modified
                self.db_manager.add_file(file_info)
                stats['files_updated'] += 1

            # Track scanned paths for cleanup
            stats['scanned_paths'].add(str(file_path))
            stats['files_scanned'] += 1

        except (OSError, PermissionError) as e:
            self.logger.debug(f"Cannot process file {file_path}: {e}")
            stats['errors'] += 1

    def _should_exclude(self, path: Path, exclude_patterns: List[str]) -> bool:
        """Check if path should be excluded based on patterns."""
        path_str = str(path)

        for pattern in exclude_patterns:
            # Support both filename and full path matching
            if fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(path_str, pattern):
                return True

        return False

    def _calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """Calculate SHA-256 hash of file (placeholder for now)."""
        # TODO: Implement actual hashing in a future phase
        # For now, return None to avoid performance impact
        return None

    def quick_scan_directory(self, directory: Path) -> Dict[str, Any]:
        """Perform a quick scan to count files (for progress estimation)."""
        stats = {'total_files': 0, 'total_dirs': 0}

        try:
            for item in directory.rglob('*'):
                if item.is_file():
                    stats['total_files'] += 1
                elif item.is_dir():
                    stats['total_dirs'] += 1

                # Don't spend too long on this
                if stats['total_files'] > 10000:
                    break

        except (OSError, PermissionError):
            pass

        return stats
EOF
```

### Step 6: Create File Scanner Tests

```bash
# Create test file for file scanner
cat > tests/unit/test_file_scanner.py << 'EOF'
"""Tests for file scanner functionality."""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

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

    assert results['files_scanned'] == 0
    assert results['files_added'] == 0
    assert results['directories_scanned'] == 1


def test_scan_directory_with_files(temp_scanner):
    """Test scanning directory with files."""
    scanner, temp_dir = temp_scanner

    # Create test files
    test_dir = temp_dir / "test"
    test_dir.mkdir()

    (test_dir / "file1.txt").write_text("test content 1")
    (test_dir / "file2.jpg").write_text("test content 2")

    results = scanner.scan_directories([str(test_dir)])

    assert results['files_scanned'] == 2
    assert results['files_added'] == 2

    # Verify files in database
    files = scanner.db_manager.search_files()
    assert len(files) == 2

    filenames = [f['filename'] for f in files]
    assert 'file1.txt' in filenames
    assert 'file2.jpg' in filenames


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

    assert results['files_scanned'] == 1
    assert results['files_added'] == 1

    # Verify only .txt file is in database
    files = scanner.db_manager.search_files()
    assert len(files) == 1
    assert files[0]['filename'] == 'file1.txt'


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
    assert results['files_scanned'] == 5


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
    assert results['files_scanned'] < 100


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
        ("unknown.xyz", "other")
    ]

    for filename, expected_type in test_files:
        (temp_dir / filename).write_text("content")

    scanner.scan_directories([str(temp_dir)])

    # Check file types in database
    for filename, expected_type in test_files:
        file_record = scanner.db_manager.get_file_by_path(str(temp_dir / filename))
        assert file_record['file_type'] == expected_type
EOF
```

### Step 7: Test the File Scanner

```bash
# Run file scanner tests
uv run python -m pytest tests/unit/test_file_scanner.py -v

# Test scanner manually
uv run python -c "
from isearch.core.database import DatabaseManager
from isearch.core.file_scanner import FileScanner
import tempfile
from pathlib import Path

# Create test setup
with tempfile.TemporaryDirectory() as tmpdir:
    db = DatabaseManager(Path(tmpdir) / 'test.db')
    scanner = FileScanner(db)

    # Create some test files
    test_dir = Path(tmpdir) / 'test'
    test_dir.mkdir()
    (test_dir / 'test.txt').write_text('Hello World')
    (test_dir / 'image.jpg').write_text('fake image')

    # Scan the directory
    results = scanner.scan_directories([str(test_dir)])
    print(f'Scan results: {results}')

    # Search files
    files = db.search_files()
    print(f'Found {len(files)} files')
    for f in files:
        print(f'  - {f[\"filename\"]} ({f[\"file_type\"]}) - {f[\"size\"]} bytes')
"
```

---

## 🔍 Phase 3: Search Engine Implementation

### Step 8: Create Search Engine

```bash
# Create the search engine module
cat > src/isearch/core/search_engine.py << 'EOF'
"""Advanced search functionality for file database."""

import logging
import re
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

from isearch.core.database import DatabaseManager


@dataclass
class SearchFilters:
    """Search filter configuration."""
    query: str = ""
    file_types: Optional[List[str]] = None
    directories: Optional[List[str]] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    modified_after: Optional[float] = None
    modified_before: Optional[float] = None
    use_regex: bool = False
    search_path: bool = False
    case_sensitive: bool = False
    limit: int = 10000


class SearchEngine:
    """Advanced search engine for file database."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)

    def search(self, filters: SearchFilters) -> List[Dict[str, Any]]:
        """
        Perform advanced search with multiple filters.

        Args:
            filters: SearchFilters object with search criteria

        Returns:
            List of file records matching the criteria
        """
        try:
            # Validate regex pattern if using regex
            if filters.use_regex and filters.query:
                try:
                    re.compile(filters.query)
                except re.error as e:
                    self.logger.error(f"Invalid regex pattern: {filters.query} - {e}")
                    return []

            results = []

            # Handle multiple file types
            if filters.file_types:
                for file_type in filters.file_types:
                    type_results = self.db_manager.search_files(
                        query=filters.query,
                        file_type=file_type,
                        min_size=filters.min_size,
                        max_size=filters.max_size,
                        modified_after=filters.modified_after,
                        modified_before=filters.modified_before,
                        use_regex=filters.use_regex,
                        search_path=filters.search_path,
                        limit=filters.limit
                    )
                    results.extend(type_results)
            else:
                # Search without file type filter
                results = self.db_manager.search_files(
                    query=filters.query,
                    min_size=filters.min_size,
                    max_size=filters.max_size,
                    modified_after=filters.modified_after,
                    modified_before=filters.modified_before,
                    use_regex=filters.use_regex,
                    search_path=filters.search_path,
                    limit=filters.limit
                )

            # Post-process results for additional filtering
            filtered_results = self._post_filter_results(results, filters)

            # Remove duplicates (can happen with multiple file type searches)
            seen_paths = set()
            unique_results = []
            for result in filtered_results:
                if result['path'] not in seen_paths:
                    seen_paths.add(result['path'])
                    unique_results.append(result)

            # Apply limit
            unique_results = unique_results[:filters.limit]

            self.logger.info(f"Search returned {len(unique_results)} results")
            return unique_results

        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []

    def _post_filter_results(self, results: List[Dict[str, Any]],
                           filters: SearchFilters) -> List[Dict[str, Any]]:
        """Apply additional filtering that couldn't be done at DB level."""

        filtered = results

        # Directory filtering
        if filters.directories:
            filtered = [
                r for r in filtered
                if any(r['directory'].startswith(d) for d in filters.directories)
            ]

        # Case sensitive filtering (if regex is not used)
        if filters.query and not filters.use_regex and filters.case_sensitive:
            search_field = 'path' if filters.search_path else 'filename'
            filtered = [
                r for r in filtered
                if filters.query in r[search_field]
            ]

        # Regex filtering (more precise than DB LIKE)
        if filters.query and filters.use_regex:
            try:
                pattern = re.compile(
                    filters.query,
                    0 if filters.case_sensitive else re.IGNORECASE
                )
                search_field = 'path' if filters.search_path else 'filename'
                filtered = [
                    r for r in filtered
                    if pattern.search(r[search_field])
                ]
            except re.error:
                # Fallback to original results if regex fails
                pass

        return filtered

    def search_similar_files(self, reference_file_path: str,
                           similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Find files similar to a reference file.

        Args:
            reference_file_path: Path to reference file
            similarity_threshold: Minimum similarity score (0.0 to 1.0)

        Returns:
            List of similar files sorted by similarity score
        """
        reference_file = self.db_manager.get_file_by_path(reference_file_path)
        if not reference_file:
            return []

        # Get files of same type
        candidates = self.db_manager.search_files(
            file_type=reference_file['file_type']
        )

        similar_files = []
        ref_name = reference_file['filename']
        ref_size = reference_file['size']

        for candidate in candidates:
            if candidate['path'] == reference_file_path:
                continue

            # Calculate similarity score
            score = self._calculate_similarity(
                ref_name, candidate['filename'],
                ref_size, candidate['size']
            )

            if score >= similarity_threshold:
                candidate['similarity_score'] = score
                similar_files.append(candidate)

        # Sort by similarity score (descending)
        similar_files.sort(key=lambda x: x['similarity_score'], reverse=True)

        return similar_files

    def _calculate_similarity(self, name1: str, name2: str,
                            size1: int, size2: int) -> float:
        """Calculate similarity between two files."""

        # Name similarity (simple edit distance)
        name_similarity = self._string_similarity(name1.lower(), name2.lower())

        # Size similarity
        if size1 == size2:
            size_similarity = 1.0
        elif size1 == 0 or size2 == 0:
            size_similarity = 0.0
        else:
            size_ratio = min(size1, size2) / max(size1, size2)
            size_similarity = size_ratio

        # Weighted combination
        total_similarity = (name_similarity * 0.7) + (size_similarity * 0.3)

        return total_similarity

    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity using simple ratio."""
        if s1 == s2:
            return 1.0
        if len(s1) == 0 or len(s2) == 0:
            return 0.0

        # Simple character overlap ratio
        set1 = set(s1)
        set2 = set(s2)

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def get_search_suggestions(self, partial_query: str,
                             limit: int = 10) -> List[str]:
        """Get search suggestions based on partial query."""

        if len(partial_query) < 2:
            return []

        # Get filenames that start with or contain the query
        files = self.db_manager.search_files(
            query=partial_query,
            limit=limit * 3  # Get more to filter
        )

        suggestions = set()

        for file_record in files:
            filename = file_record['filename']

            # Add filename if it starts with query
            if filename.lower().startswith(partial_query.lower()):
                suggestions.add(filename)

            # Add words that start with query
            words = filename.replace('.', ' ').replace('_', ' ').replace('-', ' ').split()
            for word in words:
                if word.lower().startswith(partial_query.lower()) and len(word) > len(partial_query):
                    suggestions.add(word)

        return sorted(list(suggestions))[:limit]

    def search_duplicates(self,
                         method: str = "size_name",
                         min_file_size: int = 1024) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find potential duplicate files.

        Args:
            method: "size_name", "hash", or "name_only"
            min_file_size: Minimum file size to consider

        Returns:
            Dictionary mapping duplicate groups to file lists
        """

        # Get all files above minimum size
        all_files = self.db_manager.search_files(min_size=min_file_size)

        if method == "size_name":
            return self._find_duplicates_by_size_name(all_files)
        elif method == "hash":
            return self._find_duplicates_by_hash(all_files)
        elif method == "name_only":
            return self._find_duplicates_by_name(all_files)
        else:
            raise ValueError(f"Unknown duplicate detection method: {method}")

    def _find_duplicates_by_size_name(self, files: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Find duplicates by matching size and filename."""

        groups = {}

        for file_record in files:
            key = (file_record['size'], file_record['filename'])
            if key not in groups:
                groups[key] = []
            groups[key].append(file_record)

        # Filter to only groups with multiple files
        duplicates = {
            f"{size}_{filename}": file_list
            for (size, filename), file_list in groups.items()
            if len(file_list) > 1
        }

        return duplicates

    def _find_duplicates_by_hash(self, files: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Find duplicates by file hash."""

        # Filter files that have hashes
        hashed_files = [f for f in files if f.get('hash')]

        groups = {}
        for file_record in hashed_files:
            hash_key = file_record['hash']
            if hash_key not in groups:
                groups[hash_key] = []
            groups[hash_key].append(file_record)

        # Filter to only groups with multiple files
        duplicates = {
            hash_key: file_list
            for hash_key, file_list in groups.items()
            if len(file_list) > 1
        }

        return duplicates

    def _find_duplicates_by_name(self, files: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Find duplicates by filename only."""

        groups = {}

        for file_record in files:
            filename = file_record['filename']
            if filename not in groups:
                groups[filename] = []
            groups[filename].append(file_record)

        # Filter to only groups with multiple files
        duplicates = {
            filename: file_list
            for filename, file_list in groups.items()
            if len(file_list) > 1
        }

        return duplicates
EOF
```

### Step 9: Create Search Engine Tests

```bash
# Create test file for search engine
cat > tests/unit/test_search_engine.py << 'EOF'
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
                'path': '/test/document.txt',
                'filename': 'document.txt',
                'directory': '/test',
                'size': 1024,
                'modified_date': time.time(),
                'file_type': 'document',
                'extension': '.txt'
            },
            {
                'path': '/test/image.jpg',
                'filename': 'image.jpg',
                'directory': '/test',
                'size': 2048,
                'modified_date': time.time(),
                'file_type': 'image',
                'extension': '.jpg'
            },
            {
                'path': '/test/duplicate.txt',
                'filename': 'document.txt',  # Same name as first file
                'directory': '/test/backup',
                'size': 1024,
                'modified_date': time.time(),
                'file_type': 'document',
                'extension': '.txt'
            }
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
    filenames = [r['filename'] for r in results]
    assert 'document.txt' in filenames


def test_file_type_filter(search_setup):
    """Test file type filtering."""
    search_engine = search_setup

    filters = SearchFilters(file_types=['image'])
    results = search_engine.search(filters)

    assert len(results) == 1
    assert results[0]['file_type'] == 'image'


def test_size_filter(search_setup):
    """Test size filtering."""
    search_engine = search_setup

    filters = SearchFilters(min_size=2000)
    results = search_engine.search(filters)

    assert len(results) == 1
    assert results[0]['size'] == 2048


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
    assert 'backup' in results[0]['directory']


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

    similar = search_engine.search_similar_files('/test/document.txt')

    # Should find the other document.txt as similar
    assert len(similar) >= 1
    similar_names = [f['filename'] for f in similar]
    assert 'document.txt' in similar_names


def test_search_suggestions(search_setup):
    """Test search suggestions."""
    search_engine = search_setup

    suggestions = search_engine.get_search_suggestions("doc")

    assert len(suggestions) > 0
    assert any('document' in s.lower() for s in suggestions)


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

    filters = SearchFilters(file_types=['document', 'image'])
    results = search_engine.search(filters)

    assert len(results) == 3  # All test files

    types = [r['file_type'] for r in results]
    assert 'document' in types
    assert 'image' in types
EOF
```

### Step 10: Test Search Engine

```bash
# Run search engine tests
uv run python -m pytest tests/unit/test_search_engine.py -v

# Test search engine manually
uv run python -c "
from isearch.core.database import DatabaseManager
from isearch.core.search_engine import SearchEngine, SearchFilters
import tempfile
import time
from pathlib import Path

# Create test setup
with tempfile.TemporaryDirectory() as tmpdir:
    db = DatabaseManager(Path(tmpdir) / 'test.db')
    search = SearchEngine(db)

    # Add test data
    test_files = [
        {'path': '/test/doc1.txt', 'filename': 'document1.txt', 'directory': '/test',
         'size': 1024, 'modified_date': time.time(), 'file_type': 'document', 'extension': '.txt'},
        {'path': '/test/img1.jpg', 'filename': 'image1.jpg', 'directory': '/test',
         'size': 2048, 'modified_date': time.time(), 'file_type': 'image', 'extension': '.jpg'},
    ]

    for f in test_files:
        db.add_file(f)

    # Test basic search
    filters = SearchFilters(query='document')
    results = search.search(filters)
    print(f'Found {len(results)} files matching \"document\"')

    # Test file type filter
    filters = SearchFilters(file_types=['image'])
    results = search.search(filters)
    print(f'Found {len(results)} image files')

    print('Search engine working correctly!')
"
```

This completes the first three phases of Day 2. You now have:

✅ **Complete Database System** with file metadata storage and indexing
✅ **File Scanner Engine** with recursive directory scanning and progress tracking
✅ **Advanced Search Engine** with filtering, regex support, and duplicate detection

Ready to proceed with **Phase 4: UI Integration** to connect everything to your GTK4 interface? 🚀
