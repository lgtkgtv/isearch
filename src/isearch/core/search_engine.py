"""Advanced search functionality for file database."""

import logging
import re
from typing import Any, Dict, List, Optional
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
                        limit=filters.limit,
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
                    limit=filters.limit,
                )

            # Post-process results for additional filtering
            filtered_results = self._post_filter_results(results, filters)

            # Remove duplicates (can happen with multiple file type searches)
            seen_paths = set()
            unique_results = []
            for result in filtered_results:
                if result["path"] not in seen_paths:
                    seen_paths.add(result["path"])
                    unique_results.append(result)

            # Apply limit
            unique_results = unique_results[: filters.limit]

            self.logger.info(f"Search returned {len(unique_results)} results")
            return unique_results

        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []

    def _post_filter_results(
        self, results: List[Dict[str, Any]], filters: SearchFilters
    ) -> List[Dict[str, Any]]:
        """Apply additional filtering that couldn't be done at DB level."""

        filtered = results

        # Regex filtering (more precise than DB LIKE)
        if filters.query and filters.use_regex:
            try:
                pattern = re.compile(
                    filters.query, 0 if filters.case_sensitive else re.IGNORECASE
                )
                search_field = "path" if filters.search_path else "filename"
                filtered = [r for r in filtered if pattern.search(r[search_field])]
            except re.error:
                # Fallback to original results if regex fails
                filtered = []

        # Directory filtering
        if filters.directories:
            filtered = [
                r
                for r in filtered
                if any(r["directory"].startswith(d) for d in filters.directories)
            ]

        # Case sensitive filtering (if regex is not used)
        if filters.query and not filters.use_regex and filters.case_sensitive:
            search_field = "path" if filters.search_path else "filename"
            filtered = [r for r in filtered if filters.query in r[search_field]]

        return filtered

    def search_similar_files(
        self, reference_file_path: str, similarity_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
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
        candidates = self.db_manager.search_files(file_type=reference_file["file_type"])

        similar_files = []
        ref_name = reference_file["filename"]
        ref_size = reference_file["size"]

        for candidate in candidates:
            if candidate["path"] == reference_file_path:
                continue

            # Calculate similarity score
            score = self._calculate_similarity(
                ref_name, candidate["filename"], ref_size, candidate["size"]
            )

            if score >= similarity_threshold:
                candidate["similarity_score"] = score
                similar_files.append(candidate)

        # Sort by similarity score (descending)
        similar_files.sort(key=lambda x: x["similarity_score"], reverse=True)

        return similar_files

    def _calculate_similarity(
        self, name1: str, name2: str, size1: int, size2: int
    ) -> float:
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

    def get_search_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on partial query."""

        if len(partial_query) < 2:
            return []

        # Get filenames that start with or contain the query
        files = self.db_manager.search_files(
            query=partial_query, limit=limit * 3  # Get more to filter
        )

        suggestions = set()

        for file_record in files:
            filename = file_record["filename"]

            # Add filename if it starts with query
            if filename.lower().startswith(partial_query.lower()):
                suggestions.add(filename)

            # Add words that start with query
            words = (
                filename.replace(".", " ").replace("_", " ").replace("-", " ").split()
            )
            for word in words:
                if word.lower().startswith(partial_query.lower()) and len(word) > len(
                    partial_query
                ):
                    suggestions.add(word)

        return sorted(list(suggestions))[:limit]

    def search_duplicates(
        self, method: str = "size_name", min_file_size: int = 1024
    ) -> Dict[str, List[Dict[str, Any]]]:
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

    def _find_duplicates_by_size_name(
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

    def _find_duplicates_by_hash(
        self, files: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Find duplicates by file hash."""

        # Filter files that have hashes
        hashed_files = [f for f in files if f.get("hash")]

        groups: Dict[Any, List[Dict[str, Any]]] = {}
        for file_record in hashed_files:
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

        return duplicates

    def _find_duplicates_by_name(
        self, files: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Find duplicates by filename only."""

        groups: Dict[Any, List[Dict[str, Any]]] = {}

        for file_record in files:
            filename = file_record["filename"]
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
