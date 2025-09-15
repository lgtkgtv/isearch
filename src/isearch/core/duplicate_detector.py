"""Advanced duplicate detection algorithms."""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from isearch.core.database import DatabaseManager
from isearch.utils.file_utils import calculate_file_hash, string_similarity


class DuplicateDetector:
    """Advanced duplicate detection with multiple algorithms."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)

    def find_duplicates(
        self,
        method: str = "size_name",
        min_file_size: int = 1024,
        size_tolerance: float = 0.05,
        filter_directories: Optional[List[str]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find duplicates using various methods.

        Args:
            method: Detection method ("size_name", "hash", "smart", "exact_content")
            min_file_size: Minimum file size to consider
            size_tolerance: Size difference tolerance (0.0 to 1.0)
            filter_directories: List of directories to limit search to

        Returns:
            Dictionary mapping group keys to lists of duplicate files
        """

        # Get all files above minimum size
        all_files = self.db_manager.search_files(min_size=min_file_size)

        # Filter by directories if specified
        if filter_directories is not None:
            filtered_files = self._filter_files_by_directories(
                all_files, filter_directories
            )
            print(
                f"🔍 Filtered {len(all_files)} files to {len(filtered_files)} "
                f"files in configured directories"
            )
            all_files = filtered_files

        if method == "size_name":
            return self._find_by_size_and_name(all_files)
        elif method == "hash":
            return self._find_by_hash(all_files)
        elif method == "smart":
            return self._find_smart_duplicates(all_files, size_tolerance)
        elif method == "exact_content":
            return self._find_by_content_hash(all_files)
        else:
            raise ValueError(f"Unknown detection method: {method}")

    def _find_by_size_and_name(
        self, files: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Find duplicates by matching size and filename."""
        groups: Dict[Any, List[Dict[str, Any]]] = {}

        for file_record in files:
            key = (file_record["size"], file_record["filename"])
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

    def _find_by_hash(
        self, files: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Find duplicates by file hash (optimized to use database hashes)."""

        # First, group files that already have hashes in the database
        files_with_hashes = []
        files_needing_hashes = []

        for file_record in files:
            if file_record.get("hash"):
                files_with_hashes.append(file_record)
            else:
                files_needing_hashes.append(file_record)

        self.logger.info(
            f"Using {len(files_with_hashes)} pre-computed hashes, "
            f"calculating {len(files_needing_hashes)} new hashes"
        )

        # Calculate hashes for files that don't have them (with progress feedback)
        total_to_hash = len(files_needing_hashes)
        for i, file_record in enumerate(files_needing_hashes):
            if i % 10 == 0:  # Log progress every 10 files
                self.logger.debug(f"Calculating hashes: {i+1}/{total_to_hash}")

            hash_value = self._calculate_file_hash(file_record["path"])
            if hash_value:
                file_record["hash"] = hash_value
                files_with_hashes.append(file_record)

                # Update database with calculated hash for future use
                try:
                    self.db_manager.update_file_hash(file_record["path"], hash_value)
                except Exception as e:
                    self.logger.debug(f"Failed to update hash in database: {e}")

        # Group by hash
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for file_record in files_with_hashes:
            hash_key = file_record["hash"]
            if hash_key not in groups:
                groups[hash_key] = []
            groups[hash_key].append(file_record)

        # Filter to only groups with multiple files
        duplicates = {
            hash_key: file_list
            for hash_key, file_list in groups.items()
            if len(file_list) > 1
        }

        self.logger.info(f"Found {len(duplicates)} hash-based duplicate groups")
        return duplicates

    def _find_smart_duplicates(
        self, files: List[Dict[str, Any]], size_tolerance: float
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Find duplicates using smart algorithms with size tolerance."""

        # Group files by similar characteristics
        potential_groups: Dict[str, List[Dict[str, Any]]] = {}

        for file_record in files:
            # Create a smart key based on multiple factors
            base_name = self._get_base_filename(file_record["filename"])
            file_type = file_record["file_type"]
            size_bucket = self._get_size_bucket(file_record["size"], size_tolerance)

            smart_key = f"{base_name}_{file_type}_{size_bucket}"

            if smart_key not in potential_groups:
                potential_groups[smart_key] = []
            potential_groups[smart_key].append(file_record)

        # Refine groups using similarity scoring
        refined_duplicates = {}
        group_id = 0

        for group_files in potential_groups.values():
            if len(group_files) < 2:
                continue

            # Calculate similarity matrix
            duplicate_clusters = self._cluster_similar_files(
                group_files, size_tolerance
            )

            for cluster in duplicate_clusters:
                if len(cluster) > 1:
                    group_id += 1
                    refined_duplicates[f"smart_group_{group_id}"] = cluster

        return refined_duplicates

    def _find_by_content_hash(
        self, files: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Find duplicates by calculating content hashes."""
        content_hashes: Dict[str, List[Dict[str, Any]]] = {}

        for file_record in files:
            # Skip very large files to avoid performance issues
            if file_record["size"] > 100 * 1024 * 1024:  # 100MB limit
                continue

            content_hash = self._calculate_file_hash(file_record["path"])
            if content_hash:
                if content_hash not in content_hashes:
                    content_hashes[content_hash] = []
                content_hashes[content_hash].append(file_record)

        # Filter to groups with duplicates
        duplicates = {
            f"content_{hash_key[:8]}": file_list
            for hash_key, file_list in content_hashes.items()
            if len(file_list) > 1
        }

        return duplicates

    def _get_base_filename(self, filename: str) -> str:
        """Extract base filename for comparison."""
        # Remove common suffixes and prefixes
        base = filename.lower()

        # Remove copy indicators
        copy_patterns = [
            r" \(\d+\)",  # (1), (2), etc.
            r" - copy",
            r"_copy",
            r" copy",
            r"\.bak$",
            r"\.backup$",
        ]

        import re

        for pattern in copy_patterns:
            base = re.sub(pattern, "", base)

        # Remove extension for comparison
        return Path(base).stem

    def _get_size_bucket(self, size: int, tolerance: float) -> str:
        """Get size bucket for grouping similar-sized files."""
        # Create size buckets with tolerance
        bucket_size = max(1024, int(size * tolerance))  # At least 1KB bucket
        bucket = size // bucket_size
        return f"size_{bucket}"

    def _cluster_similar_files(
        self, files: List[Dict[str, Any]], tolerance: float
    ) -> List[List[Dict[str, Any]]]:
        """Cluster files into similarity groups."""
        clusters: List[List[Dict[str, Any]]] = []

        for file_record in files:
            # Find best matching cluster
            best_cluster = None
            best_score = 0.0

            for cluster in clusters:
                score = self._calculate_cluster_similarity(file_record, cluster)
                if score > best_score and score > 0.7:  # 70% similarity threshold
                    best_score = score
                    best_cluster = cluster

            if best_cluster:
                best_cluster.append(file_record)
            else:
                # Create new cluster
                clusters.append([file_record])

        return clusters

    def _calculate_cluster_similarity(
        self, file_record: Dict[str, Any], cluster: List[Dict[str, Any]]
    ) -> float:
        """Calculate similarity between a file and a cluster."""
        if not cluster:
            return 0.0

        # Compare with cluster representative (first file)
        representative = cluster[0]

        name_similarity = self._string_similarity(
            file_record["filename"], representative["filename"]
        )

        size_similarity = self._size_similarity(
            file_record["size"], representative["size"]
        )

        type_similarity = (
            1.0 if file_record["file_type"] == representative["file_type"] else 0.0
        )

        # Weighted average
        return name_similarity * 0.5 + size_similarity * 0.3 + type_similarity * 0.2

    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity using unified utility."""
        return string_similarity(s1, s2)

    def _size_similarity(self, size1: int, size2: int) -> float:
        """Calculate size similarity."""
        if size1 == size2:
            return 1.0

        if size1 == 0 or size2 == 0:
            return 0.0

        ratio = min(size1, size2) / max(size1, size2)
        return ratio

    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA-256 hash of file content using unified utility."""
        return calculate_file_hash(file_path)

    def _filter_files_by_directories(
        self, files: List[Dict[str, Any]], directories: List[str]
    ) -> List[Dict[str, Any]]:
        """Filter files to only include those in specified directories."""
        if not directories:
            return []  # No directories configured = no files to search

        filtered_files = []
        normalized_dirs = [d.rstrip("/") for d in directories]

        for file_record in files:
            file_path = file_record.get("path", "")
            file_directory = file_record.get("directory", "")

            # Check if file is in any of the configured directories
            for config_dir in normalized_dirs:
                if (
                    file_path.startswith(config_dir + "/")
                    or file_path.startswith(config_dir)
                    or file_directory.startswith(config_dir)
                ):
                    filtered_files.append(file_record)
                    break

        return filtered_files

    def analyze_duplicate_group(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a duplicate group and provide recommendations."""
        if len(files) < 2:
            return {"recommendation": "no_action", "reason": "Not a duplicate group"}

        # Score each file
        scored_files = []
        for file_record in files:
            score = self._score_file_quality(file_record, files)
            scored_files.append((score, file_record))

        # Sort by score (highest first)
        scored_files.sort(key=lambda x: x[0], reverse=True)

        best_file = scored_files[0][1]
        duplicates = [item[1] for item in scored_files[1:]]

        return {
            "recommendation": "keep_best",
            "keep_file": best_file,
            "remove_files": duplicates,
            "reason": f"Best file has score {scored_files[0][0]:.2f}",
            "total_savings": sum(f["size"] for f in duplicates),
        }

    def _score_file_quality(
        self, file_record: Dict[str, Any], group: List[Dict[str, Any]]
    ) -> float:
        """Score file quality within a duplicate group."""
        score = 0.0

        # Size score (larger is usually better for media files)
        max_size = max(f["size"] for f in group)
        if max_size > 0:
            score += (file_record["size"] / max_size) * 30

        # Name descriptiveness score
        name_score = self._score_filename_descriptiveness(file_record["filename"])
        score += name_score * 25

        # Location score (prefer organized directories)
        location_score = self._score_file_location(file_record["path"])
        score += location_score * 20

        # Recency score (newer files might be better)
        max_modified = max(f["modified_date"] for f in group)
        if max_modified > 0:
            recency = file_record["modified_date"] / max_modified
            score += recency * 15

        # Extension preference (prefer common formats)
        ext_score = self._score_file_extension(file_record.get("extension", ""))
        score += ext_score * 10

        return score

    def _score_filename_descriptiveness(self, filename: str) -> float:
        """Score how descriptive a filename is."""
        name = filename.lower()

        # Penalize generic names
        generic_patterns = [
            "img_",
            "dsc_",
            "image",
            "photo",
            "pic",
            "screenshot",
            "untitled",
            "new",
            "copy",
            "temp",
        ]

        penalty = 0.0
        for pattern in generic_patterns:
            if pattern in name:
                penalty += 0.2

        # Reward descriptive elements
        reward = 0.0
        if len(name) > 10:  # Longer names are often more descriptive
            reward += 0.3

        if any(char.isdigit() for char in name):  # Dates/numbers add context
            reward += 0.2

        if "_" in name or "-" in name:  # Structured naming
            reward += 0.1

        return max(0, min(1.0, 0.5 + reward - penalty))

    def _score_file_location(self, file_path: str) -> float:
        """Score file location quality."""
        path_lower = file_path.lower()

        # Prefer organized directories
        good_locations = [
            "documents",
            "pictures",
            "photos",
            "images",
            "videos",
            "music",
            "downloads",
            "projects",
        ]

        # Penalize temporary/system locations
        bad_locations = [
            "temp",
            "tmp",
            "cache",
            "trash",
            "recycle",
            "desktop",
            "downloads",
        ]

        score = 0.5  # Base score

        for good in good_locations:
            if good in path_lower:
                score += 0.2
                break

        for bad in bad_locations:
            if bad in path_lower:
                score -= 0.3
                break

        return max(0, min(1.0, score))

    def _score_file_extension(self, extension: str) -> float:
        """Score file extension preference."""
        ext_lower = extension.lower()

        # Prefer common, standard formats
        good_extensions = {
            ".jpg": 0.9,
            ".jpeg": 0.9,
            ".png": 0.8,
            ".gif": 0.7,
            ".mp4": 0.9,
            ".avi": 0.7,
            ".mkv": 0.8,
            ".pdf": 0.9,
            ".docx": 0.8,
            ".txt": 0.7,
            ".mp3": 0.9,
            ".flac": 0.8,
            ".wav": 0.7,
        }

        return good_extensions.get(ext_lower, 0.5)
