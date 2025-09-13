"""Main application window for isearch."""

import logging
from typing import Optional, Any

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio  # noqa: E402

from isearch.utils.config_manager import ConfigManager  # noqa: E402
from isearch.utils.constants import (  # noqa: E402
    WINDOW_DEFAULT_WIDTH,
    WINDOW_DEFAULT_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_MIN_HEIGHT,
)


class MainWindow(Gtk.ApplicationWindow):
    """Main application window."""

    def __init__(self, app: Any) -> None:  # Use Any for Gtk.Application
        super().__init__(application=app)

        self.app = app
        self.config_manager: Optional[ConfigManager] = None
        self.logger = logging.getLogger(__name__)

        # UI components
        self.search_entry: Optional[Gtk.Entry] = None
        self.results_label: Optional[Gtk.Label] = None
        self.results_view: Optional[Gtk.TextView] = None
        self.status_label: Optional[Gtk.Label] = None
        self.progress_bar: Optional[Gtk.ProgressBar] = None
        self.regex_check: Optional[Gtk.CheckButton] = None
        self.fullpath_check: Optional[Gtk.CheckButton] = None
        self.images_check: Optional[Gtk.CheckButton] = None
        self.videos_check: Optional[Gtk.CheckButton] = None
        self.docs_check: Optional[Gtk.CheckButton] = None

        # Initialize window
        self._setup_window()
        self._setup_ui()
        self._setup_actions()

        self.logger.info("Main window initialized")

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.set_title("iSearch - File Organizer")
        self.set_default_size(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.set_size_request(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        # Get config manager from app
        if hasattr(self.app, "get_config_manager"):
            self.config_manager = self.app.get_config_manager()

    def _setup_ui(self) -> None:
        """Create the user interface."""
        # Create main vertical box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(main_box)

        # Create menu bar (placeholder)
        menu_bar = self._create_menu_bar()
        main_box.append(menu_bar)

        # Create toolbar
        toolbar = self._create_toolbar()
        main_box.append(toolbar)

        # Create search panel
        search_panel = self._create_search_panel()
        main_box.append(search_panel)

        # Create main content area
        content_area = self._create_content_area()
        main_box.append(content_area)

        # Create status bar
        status_bar = self._create_status_bar()
        main_box.append(status_bar)

    def _create_menu_bar(self) -> Gtk.Widget:
        """Create the menu bar."""
        # Simple label for now - will implement proper menu later
        menu_bar = Gtk.Label(label="File  Edit  View  Search  Tools  Help")
        menu_bar.set_halign(Gtk.Align.START)
        menu_bar.add_css_class("menu-bar")
        return menu_bar

    def _create_toolbar(self) -> Gtk.Widget:
        """Create the toolbar."""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(6)
        toolbar.set_margin_end(6)
        toolbar.set_margin_top(6)
        toolbar.set_margin_bottom(6)

        # Configure Paths button
        config_btn = Gtk.Button(label="Configure Paths")
        config_btn.connect("clicked", self._on_configure_paths_clicked)
        toolbar.append(config_btn)

        # Refresh DB button
        refresh_btn = Gtk.Button(label="Refresh DB (Ctrl+Shift+R)")
        refresh_btn.connect("clicked", self._on_refresh_db_clicked)
        toolbar.append(refresh_btn)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        toolbar.append(separator)

        # Analysis buttons
        duplicates_btn = Gtk.Button(label="Find Duplicates")
        toolbar.append(duplicates_btn)

        analysis_btn = Gtk.Button(label="Smart Analysis")
        toolbar.append(analysis_btn)

        empty_btn = Gtk.Button(label="Empty Folders")
        toolbar.append(empty_btn)

        return toolbar

    def _create_search_panel(self) -> Gtk.Widget:
        """Create the search panel."""
        search_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        search_box.set_margin_start(6)
        search_box.set_margin_end(6)
        search_box.set_margin_top(6)
        search_box.set_margin_bottom(6)

        # Search row
        search_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        search_label = Gtk.Label(label="Search:")
        search_row.append(search_label)

        # Search entry
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text(
            "Enter filename, path, or regex pattern..."
        )
        self.search_entry.set_hexpand(True)
        search_row.append(self.search_entry)

        # Search button
        search_btn = Gtk.Button(label="Search")
        search_btn.connect("clicked", self._on_search_clicked)
        search_row.append(search_btn)

        # Clear button
        clear_btn = Gtk.Button(label="Clear")
        clear_btn.connect("clicked", self._on_clear_clicked)
        search_row.append(clear_btn)

        search_box.append(search_row)

        # Filter checkboxes
        filter_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        self.regex_check = Gtk.CheckButton(label="Regex Mode")
        filter_row.append(self.regex_check)

        self.fullpath_check = Gtk.CheckButton(label="Full Path")
        filter_row.append(self.fullpath_check)

        self.images_check = Gtk.CheckButton(label="Images Only")
        filter_row.append(self.images_check)

        self.videos_check = Gtk.CheckButton(label="Videos Only")
        filter_row.append(self.videos_check)

        self.docs_check = Gtk.CheckButton(label="Documents Only")
        filter_row.append(self.docs_check)

        search_box.append(filter_row)

        return search_box

    def _create_content_area(self) -> Gtk.Widget:
        """Create the main content area."""
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        content_box.set_margin_start(6)
        content_box.set_margin_end(6)
        content_box.set_vexpand(True)

        # Results header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self.results_label = Gtk.Label(label="Search Results: 0 files found")
        self.results_label.set_halign(Gtk.Align.START)
        self.results_label.set_hexpand(True)
        header_box.append(self.results_label)

        # View mode buttons
        list_btn = Gtk.Button(label="List View")
        list_btn.add_css_class("suggested-action")
        header_box.append(list_btn)

        thumb_btn = Gtk.Button(label="Thumbnail View")
        header_box.append(thumb_btn)

        content_box.append(header_box)

        # Results area (placeholder)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        # Placeholder text view
        self.results_view = Gtk.TextView()
        self.results_view.set_editable(False)
        buffer = self.results_view.get_buffer()
        buffer.set_text(
            "No search performed yet.\n\n"
            "Try searching for files by entering a filename "
            "or pattern above."
        )

        scrolled.set_child(self.results_view)
        content_box.append(scrolled)

        return content_box

    def _create_status_bar(self) -> Gtk.Widget:
        """Create the status bar."""
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        status_box.set_margin_start(6)
        status_box.set_margin_end(6)
        status_box.set_margin_top(3)
        status_box.set_margin_bottom(3)

        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.set_hexpand(True)
        status_box.append(self.status_label)

        # Progress bar (hidden initially)
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_size_request(200, -1)
        self.progress_bar.set_visible(False)
        status_box.append(self.progress_bar)

        return status_box

    def _setup_actions(self) -> None:
        """Set up window actions."""
        # Refresh action
        refresh_action = Gio.SimpleAction.new("refresh_db", None)
        refresh_action.connect("activate", self._on_refresh_db_action)
        self.add_action(refresh_action)

        # Preferences action
        prefs_action = Gio.SimpleAction.new("preferences", None)
        prefs_action.connect("activate", self._on_preferences_action)
        self.add_action(prefs_action)

    def _on_configure_paths_clicked(self, button: Gtk.Button) -> None:
        """Handle configure paths button click."""
        if self.status_label:
            self.status_label.set_text("Configure paths - not implemented yet")
        self.logger.info("Configure paths clicked")

    def _on_refresh_db_clicked(self, button: Gtk.Button) -> None:
        """Handle refresh database button click."""
        if self.status_label:
            self.status_label.set_text("Refresh database - not implemented yet")
        self.logger.info("Refresh database clicked")

    def _on_search_clicked(self, button: Gtk.Button) -> None:
        """Handle search button click."""
        query = ""
        if self.search_entry:
            query = self.search_entry.get_text()
        if self.status_label:
            self.status_label.set_text(f"Search: '{query}' - not implemented yet")
        self.logger.info(f"Search clicked: {query}")

    def _on_clear_clicked(self, button: Gtk.Button) -> None:
        """Handle clear button click."""
        if self.search_entry:
            self.search_entry.set_text("")
        if self.status_label:
            self.status_label.set_text("Search cleared")
        self.logger.info("Search cleared")

    def _on_refresh_db_action(self, action: Gio.SimpleAction, parameter: None) -> None:
        """Handle refresh database action (keyboard shortcut)."""
        self._on_refresh_db_clicked(None)  # type: ignore

    def _on_preferences_action(self, action: Gio.SimpleAction, parameter: None) -> None:
        """Handle preferences action."""
        if self.status_label:
            self.status_label.set_text("Preferences - not implemented yet")
        self.logger.info("Preferences action")
