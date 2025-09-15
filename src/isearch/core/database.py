"""Database management for file metadata storage."""

import logging
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from isearch.utils.constants import DEFAULT_DB_PATH


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
            cursor.execute(
                """
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
                    perceptual_hash TEXT,
                    average_hash TEXT,
                    difference_hash TEXT,
                    quality_score REAL DEFAULT 0.0,
                    is_ai_enhanced BOOLEAN DEFAULT 0,
                    ai_confidence REAL DEFAULT 0.0,
                    media_analysis TEXT,
                    is_hidden BOOLEAN DEFAULT 0,
                    is_symlink BOOLEAN DEFAULT 0,
                    scan_date REAL DEFAULT (datetime('now')),
                    created_at REAL DEFAULT (datetime('now')),
                    updated_at REAL DEFAULT (datetime('now'))
                )
            """
            )

            # Create indexes for performance
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_files_filename
                ON files(filename)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_files_path
                ON files(path)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_files_directory
                ON files(directory)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_files_type
                ON files(file_type)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_files_size
                ON files(size)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_files_modified
                ON files(modified_date)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_files_extension
                ON files(extension)
            """
            )

            # CRITICAL: Hash index for duplicate detection performance
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_files_hash
                ON files(hash)
            """
            )

            # Composite index for size+name duplicate detection
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_files_size_filename
                ON files(size, filename)
            """
            )

            # Create scan_sessions table for tracking scan operations
            cursor.execute(
                """
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
                    created_at REAL DEFAULT (datetime('now')),
                    updated_at REAL DEFAULT (datetime('now'))
                )
            """
            )

            conn.commit()
            self.logger.info("Database initialized successfully")

    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper locking."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
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

            cursor.execute(
                """
                INSERT OR REPLACE INTO files (
                    path, filename, directory, size, modified_date,
                    created_date, file_type, extension, hash,
                    perceptual_hash, average_hash, difference_hash,
                    quality_score, is_ai_enhanced, ai_confidence, media_analysis,
                    is_hidden, is_symlink, scan_date, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    datetime('now'), datetime('now'))
            """,
                (
                    str(file_info["path"]),
                    file_info["filename"],
                    str(file_info["directory"]),
                    file_info["size"],
                    file_info["modified_date"],
                    file_info.get("created_date"),
                    file_info["file_type"],
                    file_info.get("extension", ""),
                    file_info.get("hash"),
                    file_info.get("perceptual_hash"),
                    file_info.get("average_hash"),
                    file_info.get("difference_hash"),
                    file_info.get("quality_score", 0.0),
                    file_info.get("is_ai_enhanced", False),
                    file_info.get("ai_confidence", 0.0),
                    file_info.get("media_analysis"),
                    file_info.get("is_hidden", False),
                    file_info.get("is_symlink", False),
                ),
            )

            conn.commit()
            return cursor.lastrowid

    def get_file_by_path(self, path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Get file record by path."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE path = ?", (str(path),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_file_hash(self, path: Union[str, Path], hash_value: str) -> bool:
        """Update hash for an existing file."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE files SET hash = ?, updated_at = CURRENT_TIMESTAMP "
                    "WHERE path = ?",
                    (hash_value, str(path)),
                )
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Failed to update hash for {path}: {e}")
            return False

    def search_files(
        self,
        query: str = "",
        file_type: Optional[str] = None,
        directory: Optional[str] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        modified_after: Optional[float] = None,
        modified_before: Optional[float] = None,
        use_regex: bool = False,
        search_path: bool = False,
        limit: int = 10000,
    ) -> List[Dict[str, Any]]:
        """Search files with various filters."""

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic query
            conditions = []
            params: List[Union[str, int, float]] = []

            # Text search
            if query:
                if use_regex:
                    # For regex, we'll do post-processing in search engine
                    # Just do a broad search here to get candidates
                    search_field = "path" if search_path else "filename"
                    conditions.append(f"{search_field} IS NOT NULL")
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
            total_files = cursor.fetchone()["total"]

            # Total size
            cursor.execute("SELECT SUM(size) as total_size FROM files")
            total_size = cursor.fetchone()["total_size"] or 0

            # File type breakdown
            cursor.execute(
                """
                SELECT file_type, COUNT(*) as count, SUM(size) as size
                FROM files
                GROUP BY file_type
                ORDER BY count DESC
            """
            )
            file_types = [dict(row) for row in cursor.fetchall()]

            # Recent files
            cursor.execute(
                """
                SELECT COUNT(*) as recent_count
                FROM files
                WHERE scan_date >= datetime('now', '-7 days')
            """
            )
            recent_files = cursor.fetchone()["recent_count"]

            return {
                "total_files": total_files,
                "total_size": total_size,
                "file_types": file_types,
                "recent_files": recent_files,
                "database_path": str(self.db_path),
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
                if file_record["path"] not in scanned_paths:
                    cursor.execute(
                        "DELETE FROM files WHERE id = ?", (file_record["id"],)
                    )
                    removed_count += 1

            conn.commit()
            if removed_count > 0:
                self.logger.info(f"Removed {removed_count} missing files")

            return removed_count

    def remove_files_by_directory(self, directory_path: str) -> int:
        """Remove all files from a specific directory from the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Normalize directory path (ensure it ends with /)
            normalized_dir = directory_path.rstrip("/") + "/"

            # Count files that will be removed
            cursor.execute(
                "SELECT COUNT(*) as count FROM files WHERE path LIKE ? "
                "OR directory = ?",
                (f"{normalized_dir}%", directory_path),
            )
            count_result = cursor.fetchone()
            files_to_remove = count_result["count"] if count_result else 0

            # Remove files
            cursor.execute(
                "DELETE FROM files WHERE path LIKE ? OR directory = ?",
                (f"{normalized_dir}%", directory_path),
            )

            conn.commit()
            if files_to_remove > 0:
                self.logger.info(
                    f"Removed {files_to_remove} files from directory: {directory_path}"
                )

            return files_to_remove

    def remove_file_by_path(self, file_path: Union[str, Path]) -> bool:
        """Remove a single file from the database by its path."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Convert Path to string if needed
            path_str = str(file_path)

            # Remove the file
            cursor.execute("DELETE FROM files WHERE path = ?", (path_str,))

            conn.commit()
            removed = cursor.rowcount > 0

            if removed:
                self.logger.info(f"Removed file from database: {path_str}")

            return removed

    def start_scan_session(self, directories: List[str]) -> int:
        """Start a new scan session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO scan_sessions (start_time, directories_scanned)
                VALUES (datetime('now'), ?)
            """,
                ("|".join(directories),),
            )
            conn.commit()
            return cursor.lastrowid

    def update_scan_session(
        self,
        session_id: int,
        files_scanned: int = 0,
        files_added: int = 0,
        files_updated: int = 0,
        status: str = "running",
    ) -> None:
        """Update scan session progress."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE scan_sessions
                SET files_scanned = ?, files_added = ?, files_updated = ?,
                    status = ?, updated_at = datetime('now')
                WHERE id = ?
            """,
                (files_scanned, files_added, files_updated, status, session_id),
            )
            conn.commit()

    def finish_scan_session(
        self,
        session_id: int,
        files_removed: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        """Complete a scan session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            status = "error" if error_message else "completed"
            cursor.execute(
                """
                UPDATE scan_sessions
                SET end_time = datetime('now'), status = ?,
                    files_removed = ?, error_message = ?
                WHERE id = ?
            """,
                (status, files_removed, error_message, session_id),
            )
            conn.commit()

    def vacuum_database(self) -> None:
        """Optimize database by running VACUUM."""
        with self._get_connection() as conn:
            conn.execute("VACUUM")
            self.logger.info("Database vacuumed")

    def get_database_size(self) -> int:
        """Get database file size in bytes."""
        return self.db_path.stat().st_size if self.db_path.exists() else 0
