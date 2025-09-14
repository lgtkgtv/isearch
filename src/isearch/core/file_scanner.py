"""File system scanning and discovery functionality."""

import fnmatch
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

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

    def scan_directories(
        self,
        directories: List[str],
        exclude_patterns: Optional[List[str]] = None,
        follow_symlinks: bool = True,
        scan_hidden: bool = False,
        calculate_hashes: bool = False,
    ) -> Dict[str, Any]:
        """
        Scan directories and update database.

        Returns:
            Dictionary with scan statistics
        """
        self._should_stop = False
        exclude_patterns = exclude_patterns or []

        # Start scan session
        session_id = self.db_manager.start_scan_session(directories)

        stats: Dict[str, Any] = {
            "files_scanned": 0,
            "files_added": 0,
            "files_updated": 0,
            "files_removed": 0,
            "directories_scanned": 0,
            "errors": 0,
            "start_time": time.time(),
            "scanned_paths": set(),
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
                    stats,
                )

                stats["directories_scanned"] += 1

                # Update progress
                if self._progress_callback:
                    self._progress_callback(
                        stats["files_scanned"],
                        0,  # Total unknown during scan
                        f"Scanned {stats['files_scanned']} files",
                    )

            # Remove missing files if scan completed
            if not self._should_stop:
                removed = self.db_manager.remove_missing_files(stats["scanned_paths"])
                stats["files_removed"] = removed

            # Finish scan session
            stats["end_time"] = time.time()
            stats["duration"] = stats["end_time"] - stats["start_time"]

            self.db_manager.update_scan_session(
                session_id,
                stats["files_scanned"],
                stats["files_added"],
                stats["files_updated"],
                "completed" if not self._should_stop else "cancelled",
            )

            self.db_manager.finish_scan_session(session_id, stats["files_removed"])

            self.logger.info(f"Scan completed: {stats}")
            return stats

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Scan failed: {error_msg}")
            self.db_manager.finish_scan_session(session_id, error_message=error_msg)
            stats["error"] = error_msg
            return stats

    def _scan_directory(
        self,
        directory: Path,
        exclude_patterns: List[str],
        follow_symlinks: bool,
        scan_hidden: bool,
        calculate_hashes: bool,
        stats: Dict[str, Any],
    ) -> None:
        """Recursively scan a directory."""

        try:
            for item in directory.iterdir():
                if self._should_stop:
                    break

                # Skip hidden files/directories if not requested
                if not scan_hidden and item.name.startswith("."):
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
                            stats,
                        )

                except (OSError, PermissionError) as e:
                    self.logger.debug(f"Cannot access {item}: {e}")
                    stats["errors"] += 1
                    continue

        except (OSError, PermissionError) as e:
            self.logger.warning(f"Cannot scan directory {directory}: {e}")
            stats["errors"] += 1

    def _process_file(
        self, file_path: Path, calculate_hashes: bool, stats: Dict[str, Any]
    ) -> None:
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
                "path": str(file_path),
                "filename": file_path.name,
                "directory": str(file_path.parent),
                "size": file_stat.st_size,
                "modified_date": file_stat.st_mtime,
                "created_date": getattr(file_stat, "st_birthtime", file_stat.st_ctime),
                "file_type": get_file_type(file_path.suffix),
                "extension": file_path.suffix.lower(),
                "is_hidden": file_path.name.startswith("."),
                "is_symlink": file_path.is_symlink(),
            }

            # Calculate hash if requested
            if calculate_hashes:
                file_info["hash"] = self._calculate_file_hash(file_path)

            # Check if file already exists in database
            existing = self.db_manager.get_file_by_path(str(file_path))

            if existing is None:
                # New file
                self.db_manager.add_file(file_info)
                stats["files_added"] += 1
            elif (
                existing["modified_date"] != file_stat.st_mtime
                or existing["size"] != file_stat.st_size
            ):
                # File was modified
                self.db_manager.add_file(file_info)
                stats["files_updated"] += 1

            # Track scanned paths for cleanup
            stats["scanned_paths"].add(str(file_path))
            stats["files_scanned"] += 1

        except (OSError, PermissionError) as e:
            self.logger.debug(f"Cannot process file {file_path}: {e}")
            stats["errors"] += 1

    def _should_exclude(self, path: Path, exclude_patterns: List[str]) -> bool:
        """Check if path should be excluded based on patterns."""
        path_str = str(path)

        for pattern in exclude_patterns:
            # Support both filename and full path matching
            if fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(
                path_str, pattern
            ):
                return True

        return False

    def _calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """Calculate SHA-256 hash of file (placeholder for now)."""
        # TODO: Implement actual hashing in a future phase
        # For now, return None to avoid performance impact
        return None

    def quick_scan_directory(self, directory: Path) -> Dict[str, Any]:
        """Perform a quick scan to count files (for progress estimation)."""
        stats = {"total_files": 0, "total_dirs": 0}

        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    stats["total_files"] += 1
                elif item.is_dir():
                    stats["total_dirs"] += 1

                # Don't spend too long on this
                if stats["total_files"] > 10000:
                    break

        except (OSError, PermissionError):
            pass

        return stats
