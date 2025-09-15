"""Main application window for isearch."""

import logging
import threading

from typing import Optional, Any, List, Dict

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib  # noqa: E402


from isearch.core.database import DatabaseManager  # noqa: E402
from isearch.core.file_scanner import FileScanner  # noqa: E402
from isearch.core.search_engine import SearchEngine, SearchFilters  # noqa: E402
from isearch.ui.duplicate_window import DuplicateWindow  # noqa: E402
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

        # Backend systems
        self.db_manager = DatabaseManager()
        self.file_scanner = FileScanner(self.db_manager)
        self.search_engine = SearchEngine(self.db_manager)

        # UI state
        self._scanning = False
        self._scan_thread: Optional[threading.Thread] = None

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
        self._setup_scanner_callbacks()
        self._refresh_stats()

        self.logger.info("Main window initialized with backend integration")

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
        self.refresh_btn = Gtk.Button(label="Refresh DB (Ctrl+Shift+R)")
        self.refresh_btn.connect("clicked", self._on_refresh_db_clicked)
        toolbar.append(self.refresh_btn)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        toolbar.append(separator)

        # Analysis buttons
        duplicates_btn = Gtk.Button(label="Find Duplicates")
        duplicates_btn.connect("clicked", self._on_find_duplicates_clicked)
        toolbar.append(duplicates_btn)

        analysis_btn = Gtk.Button(label="Smart Analysis")
        analysis_btn.connect("clicked", self._on_smart_analysis_clicked)
        toolbar.append(analysis_btn)

        empty_btn = Gtk.Button(label="Empty Folders")
        empty_btn.connect("clicked", self._on_empty_folders_clicked)
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

        # Results area with TreeView
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        # Create TreeView with columns
        self.results_store = Gtk.ListStore(
            str, str, str, str, str, str
        )  # filename, type, size, modified, path, extension
        self.results_tree = Gtk.TreeView(model=self.results_store)
        # Add columns
        columns = [
            ("Filename", 0),
            ("Type", 1),
            ("Size", 2),
            ("Modified", 3),
            ("Location", 4),
        ]
        for title, col_id in columns:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_resizable(True)
            column.set_sort_column_id(col_id)
            self.results_tree.append_column(column)

        # Connect double-click to open file
        self.results_tree.connect("row-activated", self._on_file_activated)

        scrolled.set_child(self.results_tree)
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

    def _setup_scanner_callbacks(self) -> None:
        """Set up file scanner progress callbacks."""

        def progress_callback(scanned: int, total: int, message: str) -> None:
            # Use GLib.idle_add to update UI from background thread
            GLib.idle_add(self._update_scan_progress, scanned, total, message)

        self.file_scanner.set_progress_callback(progress_callback)

    def _refresh_stats(self) -> None:
        """Refresh database statistics display."""
        stats = self.db_manager.get_file_stats()
        if self.status_label:
            self.status_label.set_text(
                f"Database: {stats['total_files']} files, "
                f"{stats['total_size'] // 1024} KB total"
            )

        # Event Handlers

    def _on_configure_paths_clicked(self, button: Gtk.Button) -> None:
        """Handle configure paths button click."""
        self._show_config_dialog()

    def _on_refresh_db_clicked(self, button: Gtk.Button) -> None:
        """Handle refresh database button click."""
        if self._scanning:
            self._stop_scan()
        else:
            self._start_scan()

    def _on_search_clicked(self, button: Gtk.Button) -> None:
        """Handle search button click."""
        self._perform_search()

    def _on_search_activate(self, entry: Gtk.Entry) -> None:
        """Handle Enter key in search entry."""
        self._perform_search()

    def _on_clear_clicked(self, button: Gtk.Button) -> None:
        """Handle clear button click."""
        if self.search_entry:
            self.search_entry.set_text("")
        self._clear_results()
        if self.status_label:
            self.status_label.set_text("Search cleared")

    def _on_find_duplicates_clicked(self, button: Gtk.Button) -> None:
        """Handle find duplicates button click."""
        duplicate_window = DuplicateWindow(self, self.db_manager)
        duplicate_window.show()

    def _on_smart_analysis_clicked(self, button: Gtk.Button) -> None:
        """Handle smart analysis button click."""
        if self.status_label:
            self.status_label.set_text("Smart analysis - not implemented yet")

    def _on_empty_folders_clicked(self, button: Gtk.Button) -> None:
        """Handle empty folders button click."""
        if self.status_label:
            self.status_label.set_text("Empty folder detection - not implemented yet")

    def _on_file_activated(
        self, tree_view: Gtk.TreeView, path: Gtk.TreePath, column: Gtk.TreeViewColumn
    ) -> None:
        """Handle double-click on file in results."""
        model = tree_view.get_model()
        iter = model.get_iter(path)
        file_path = model.get_value(iter, 4)  # Path column

        # Open file with default application
        self._open_file(file_path)

    def _on_refresh_db_action(self, action: Gio.SimpleAction, parameter: None) -> None:
        """Handle refresh database action (keyboard shortcut)."""
        self._on_refresh_db_clicked(None)  # type: ignore

    def _on_preferences_action(self, action: Gio.SimpleAction, parameter: None) -> None:
        """Handle preferences action."""
        self._show_config_dialog()

    # Core functionality methods
    def _perform_search(self) -> None:
        """Perform search with current filters."""
        if not self.search_entry:
            return

        query = self.search_entry.get_text().strip()

        # Build search filters
        file_types = []
        if self.images_check and self.images_check.get_active():
            file_types.append("image")
        if self.videos_check and self.videos_check.get_active():
            file_types.append("video")
        if self.docs_check and self.docs_check.get_active():
            file_types.append("document")

        filters = SearchFilters(
            query=query,
            file_types=file_types if file_types else None,
            use_regex=self.regex_check.get_active() if self.regex_check else False,
            search_path=(
                self.fullpath_check.get_active() if self.fullpath_check else False
            ),
        )

        # Perform search in background thread
        def search_worker():
            try:
                results = self.search_engine.search(filters)
                GLib.idle_add(self._display_search_results, results, query)
            except Exception as e:
                GLib.idle_add(self._show_error, f"Search failed: {e}")

        threading.Thread(target=search_worker, daemon=True).start()

        if self.status_label:
            self.status_label.set_text(f"Searching for '{query}'...")

    def _display_search_results(
        self, results: List[Dict[str, Any]], query: str
    ) -> None:
        """Display search results in the TreeView."""
        if not self.results_store or not self.results_label:
            return

        # Clear previous results
        self.results_store.clear()

        # Add new results
        for result in results:
            size_str = self._format_file_size(result["size"])
            modified_str = self._format_date(result["modified_date"])

            self.results_store.append(
                [
                    result["filename"],
                    result["file_type"].title(),
                    size_str,
                    modified_str,
                    result["path"],
                    result.get("extension", ""),
                ]
            )

        # Update results label
        self.results_label.set_text(f"Search Results: {len(results)} files found")

        if self.status_label:
            self.status_label.set_text(f"Found {len(results)} files matching '{query}'")

    def _clear_results(self) -> None:
        """Clear search results."""
        if self.results_store:
            self.results_store.clear()
        if self.results_label:
            self.results_label.set_text("Search Results: 0 files found")

    def _start_scan(self) -> None:
        """Start file system scan."""
        if self._scanning:
            return

        # Get scan directories from config
        config_manager = self.config_manager or ConfigManager()
        directories = config_manager.get_scan_directories()
        exclude_patterns = config_manager.get_exclude_patterns()

        if not directories:
            self._show_error(
                "No directories configured for scanning. Please configure paths first."
            )
            return

        self._scanning = True
        if self.refresh_btn:
            self.refresh_btn.set_label("Stop Scan")

        if self.progress_bar:
            self.progress_bar.set_visible(True)
            self.progress_bar.set_fraction(0.0)

        def scan_worker():
            try:
                results = self.file_scanner.scan_directories(
                    directories,
                    exclude_patterns,
                    follow_symlinks=True,
                    scan_hidden=False,
                )
                GLib.idle_add(self._scan_completed, results)
            except Exception as e:
                GLib.idle_add(self._scan_failed, str(e))

        self._scan_thread = threading.Thread(target=scan_worker, daemon=True)
        self._scan_thread.start()

    def _stop_scan(self) -> None:
        """Stop current scan."""
        if self.file_scanner:
            self.file_scanner.stop_scan()

    def _scan_completed(self, results: Dict[str, Any]) -> None:
        """Handle scan completion."""
        self._scanning = False
        if self.refresh_btn:
            self.refresh_btn.set_label("Refresh DB (Ctrl+Shift+R)")

        if self.progress_bar:
            self.progress_bar.set_visible(False)

        if self.status_label:
            self.status_label.set_text(
                f"Scan complete: {results['files_scanned']} files scanned, "
                f"{results['files_added']} added, "
                f"{results['files_updated']} updated in {results['duration']:.1f}s"
            )

        self._refresh_stats()

    def _scan_failed(self, error: str) -> None:
        """Handle scan failure."""
        self._scanning = False
        if self.refresh_btn:
            self.refresh_btn.set_label("Refresh DB (Ctrl+Shift+R)")

        if self.progress_bar:
            self.progress_bar.set_visible(False)

        self._show_error(f"Scan failed: {error}")

    def _update_scan_progress(self, scanned: int, total: int, message: str) -> None:
        """Update scan progress display."""
        if self.progress_bar and self.progress_bar.get_visible():
            if total > 0:
                fraction = min(scanned / total, 1.0)
                self.progress_bar.set_fraction(fraction)

        if self.status_label:
            self.status_label.set_text(f"Scanning: {message}")

    def _find_duplicates(self) -> None:
        """Find and display duplicate files."""

        def duplicate_worker():
            try:
                duplicates = self.search_engine.search_duplicates()
                GLib.idle_add(self._display_duplicates, duplicates)
            except Exception as e:
                GLib.idle_add(self._show_error, f"Duplicate search failed: {e}")

        threading.Thread(target=duplicate_worker, daemon=True).start()

        if self.status_label:
            self.status_label.set_text("Searching for duplicates...")

    def _display_duplicates(self, duplicates: Dict[str, List[Dict[str, Any]]]) -> None:
        """Display duplicate files."""
        if not self.results_store or not self.results_label:
            return

        self.results_store.clear()

        total_duplicates = 0
        for group_name, files in duplicates.items():
            total_duplicates += len(files)
            for file_info in files:
                size_str = self._format_file_size(file_info["size"])
                modified_str = self._format_date(file_info["modified_date"])

                self.results_store.append(
                    [
                        f"[DUP] {file_info['filename']}",
                        file_info["file_type"].title(),
                        size_str,
                        modified_str,
                        file_info["path"],
                        file_info.get("extension", ""),
                    ]
                )

        if self.results_label:
            self.results_label.set_text(
                f"Duplicates: {total_duplicates} files in {len(duplicates)} groups"
            )

        if self.status_label:
            self.status_label.set_text(
                (
                    f"Found {len(duplicates)} duplicate groups with "
                    f"{total_duplicates} files"
                )
            )

    def _open_file(self, file_path: str) -> None:
        """Open file with default application."""
        try:
            import subprocess

            subprocess.run(["xdg-open", file_path], check=False)
            if self.status_label:
                self.status_label.set_text(f"Opened: {file_path}")
        except Exception as e:
            self._show_error(f"Cannot open file: {e}")

    def _show_error(self, message: str) -> None:
        """Show error message."""
        self.logger.error(message)
        if self.status_label:
            self.status_label.set_text(f"Error: {message}")

    # Utility methods
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        size = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size = size / 1024.0
        return f"{size:.1f} TB"

    def _format_date(self, timestamp: float) -> str:
        """Format timestamp as readable date."""
        import datetime

        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")

    def _show_config_dialog(self) -> None:
        """Show configuration dialog."""
        from isearch.ui.config_dialog import ConfigDialog

        config_manager = self.config_manager or ConfigManager()
        dialog = ConfigDialog(self, config_manager)
        dialog.run_and_save()

        # Update our config manager reference
        self.config_manager = config_manager

        if self.status_label:
            self.status_label.set_text("Configuration updated")
