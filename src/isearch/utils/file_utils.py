"""Unified file utility functions to eliminate code duplication."""

import hashlib
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def calculate_file_hash(
    file_path: str, max_size: Optional[int] = None
) -> Optional[str]:
    """
    Calculate SHA-256 hash of file content.

    Args:
        file_path: Path to file to hash
        max_size: Optional maximum file size to hash (bytes). Skip if file is larger.

    Returns:
        SHA-256 hash as hex string, or None if file cannot be read
    """
    try:
        path = Path(file_path)

        # Check file size if limit specified
        if max_size is not None:
            file_size = path.stat().st_size
            if file_size > max_size:
                logger.debug(
                    f"Skipping hash for large file {file_path}: "
                    f"{file_size} > {max_size}"
                )
                return None

        hash_sha256 = hashlib.sha256()

        with open(path, "rb") as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)

        return hash_sha256.hexdigest()

    except (OSError, PermissionError) as e:
        logger.debug(f"Cannot hash file {file_path}: {e}")
        return None


def string_similarity(s1: str, s2: str) -> float:
    """
    Calculate string similarity using character set intersection.

    Args:
        s1, s2: Strings to compare

    Returns:
        Similarity score between 0.0 and 1.0 (1.0 = identical)
    """
    if s1 == s2:
        return 1.0

    s1_lower = s1.lower()
    s2_lower = s2.lower()

    # Handle empty strings
    if not s1_lower and not s2_lower:
        return 1.0
    if not s1_lower or not s2_lower:
        return 0.0

    # Calculate Jaccard similarity (intersection over union)
    set1 = set(s1_lower)
    set2 = set(s2_lower)

    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    return intersection / union if union > 0 else 0.0
