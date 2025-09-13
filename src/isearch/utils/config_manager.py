"""Configuration management for isearch application."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from isearch.utils.constants import (
    DEFAULT_CONFIG_PATH,
    WINDOW_DEFAULT_WIDTH,
    WINDOW_DEFAULT_HEIGHT,
)


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.logger = logging.getLogger(__name__)
        self._config: Dict[str, Any] = {}

        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Load configuration
        self.load_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "version": "1.0",
            "scan_directories": [
                str(Path.home() / "Pictures"),
                str(Path.home() / "Documents"),
            ],
            "exclude_patterns": [
                "*.tmp",
                "*.log",
                "*/.git/*",
                "*/node_modules/*",
                "*/__pycache__/*",
                "*.pyc",
            ],
            "scan_options": {
                "follow_symlinks": True,
                "scan_hidden": False,
                "calculate_hashes": False,
                "max_file_size_mb": 1000,
            },
            "ui_preferences": {
                "window_width": WINDOW_DEFAULT_WIDTH,
                "window_height": WINDOW_DEFAULT_HEIGHT,
                "thumbnail_size": 150,
                "show_hidden_files": False,
                "remember_window_state": True,
            },
            "search_options": {
                "case_sensitive": False,
                "regex_enabled": False,
                "search_content": False,
                "max_results": 10000,
            },
        }

    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)

                # Merge with defaults to ensure all keys exist
                self._config = self.get_default_config()
                self._deep_update(self._config, loaded_config)

                self.logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self._config = self.get_default_config()
                self.save_config()
                self.logger.info("Created default configuration")

        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Error loading config: {e}")
            self._config = self.get_default_config()

    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Configuration saved to {self.config_path}")
        except IOError as e:
            self.logger.error(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key path."""
        keys = key.split(".")
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key path."""
        keys = key.split(".")
        config = self._config

        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the value
        config[keys[-1]] = value

    def get_scan_directories(self) -> List[str]:
        """Get list of directories to scan."""
        dirs = self.get("scan_directories", [])
        return dirs if isinstance(dirs, list) else []

    def set_scan_directories(self, directories: List[str]) -> None:
        """Set list of directories to scan."""
        self.set("scan_directories", directories)

    def get_exclude_patterns(self) -> List[str]:
        """Get list of exclude patterns."""
        patterns = self.get("exclude_patterns", [])
        return patterns if isinstance(patterns, list) else []

    def set_exclude_patterns(self, patterns: List[str]) -> None:
        """Set list of exclude patterns."""
        self.set("exclude_patterns", patterns)

    def _deep_update(
        self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]
    ) -> None:
        """Deep update base_dict with update_dict."""
        for key, value in update_dict.items():
            if (
                key in base_dict
                and isinstance(base_dict[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
