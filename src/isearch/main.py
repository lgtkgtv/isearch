#!/usr/bin/env python3
"""
isearch - Intelligent File Search and Organization Tool

A GTK4-based application for managing, searching, and organizing
large collections of files across multiple directories.
"""

import sys
import logging
from typing import Optional

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio  # noqa: E402

from isearch.ui.main_window import MainWindow  # noqa: E402
from isearch.utils.config_manager import ConfigManager  # noqa: E402
from isearch.utils.constants import APP_ID, APP_NAME, APP_VERSION  # noqa: E402


class ISearchApplication(Gtk.Application):
    """Main application class for isearch."""

    def __init__(self) -> None:
        super().__init__(
            application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )

        self.config_manager: Optional[ConfigManager] = None
        self.main_window: Optional[MainWindow] = None

        # Set up logging
        self._setup_logging()

        logging.info(f"Starting {APP_NAME} v{APP_VERSION}")

    def _setup_logging(self) -> None:
        """Configure application logging."""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
            ],
        )

    def do_activate(self) -> None:
        """Activate the application."""
        if not self.main_window:
            # Initialize configuration manager
            self.config_manager = ConfigManager()

            # Create and show main window
            self.main_window = MainWindow(self)
            self.main_window.present()
        else:
            self.main_window.present()

    def do_startup(self) -> None:
        """Initialize the application."""
        Gtk.Application.do_startup(self)

        # Set up application-wide accelerators
        self._setup_accelerators()

    def _setup_accelerators(self) -> None:
        """Set up keyboard shortcuts."""
        # Ctrl+Shift+R for refresh
        self.set_accels_for_action("win.refresh_db", ["<Ctrl><Shift>R"])

        # Ctrl+Q for quit
        self.set_accels_for_action("app.quit", ["<Ctrl>Q"])

        # Ctrl+, for preferences
        self.set_accels_for_action("win.preferences", ["<Ctrl>comma"])

    def get_config_manager(self) -> ConfigManager:
        """Get the configuration manager instance."""
        if not self.config_manager:
            self.config_manager = ConfigManager()
        return self.config_manager


def main() -> int:
    """Main entry point for the application."""
    app = ISearchApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
