"""Duplicate file management window."""

import logging
from typing import Dict, List, Any, Optional
import threading

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Pango  # noqa: E402

from isearch.core.duplicate_detector import DuplicateDetector  # noqa: E402
from isearch.core.database import DatabaseManager  # noqa: E402
from isearch.core.file_scanner import FileScanner  # noqa: E402


class DuplicateWindow(Gtk.Window):
    """Window for managing duplicate files."""

    def __init__(self, parent: Gtk.Window, db_manager: DatabaseManager) -> None:
        super().__init__()

        self.set_transient_for(parent)
        self.set_title("Duplicate File Manager")
        self.set_default_size(1000, 700)

        self.db_manager = db_manager
        self.duplicate_detector = DuplicateDetector(db_manager)
        self.parent_window = parent
        self.logger = logging.getLogger(__name__)

        # Data
        self.duplicate_groups: Dict[str, List[Dict[str, Any]]] = {}
        self.selected_for_deletion: set = set()

        # UI components
        self.groups_store: Optional[Gtk.ListStore] = None
        self.files_store: Optional[Gtk.ListStore] = None
        self.groups_tree: Optional[Gtk.TreeView] = None
        self.files_tree: Optional[Gtk.TreeView] = None
        self.status_label: Optional[Gtk.Label] = None
        self.progress_bar: Optional[Gtk.ProgressBar] = None
        self.delete_button: Optional[Gtk.Button] = None
        self.scan_button: Optional[Gtk.Button] = None
        self.refresh_button: Optional[Gtk.Button] = None
        self.auto_select_button: Optional[Gtk.Button] = None
        self.files_header: Optional[Gtk.Label] = None
        self.method_combo: Optional[Gtk.ComboBoxText] = None

        # Operation state
        self._operation_running = False
        self._current_method = "size_name"  # Default method
        self._queued_method: Optional[str] = None
        self._queued_selection: Optional[str] = None

        self._setup_ui()
        self._load_duplicates()

    def _setup_ui(self) -> None:
        """Create the duplicate management interface."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        self.set_child(main_box)

        # Toolbar
        toolbar = self._create_toolbar()
        main_box.append(toolbar)

        # Main content (horizontal paned)
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_vexpand(True)
        main_box.append(paned)

        # Left side: Duplicate groups
        left_panel = self._create_groups_panel()
        paned.set_start_child(left_panel)

        # Right side: Files in selected group
        right_panel = self._create_files_panel()
        paned.set_end_child(right_panel)

        # Status bar
        status_bar = self._create_status_bar()
        main_box.append(status_bar)

    def _create_toolbar(self) -> Gtk.Widget:
        """Create toolbar with duplicate management actions."""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        # Detection method selection
        method_label = Gtk.Label(label="Method:")
        toolbar.append(method_label)

        # WORKAROUND: Use button-based method selector instead of problematic ComboBoxText
        method_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        # Create method buttons
        self.method_buttons = {}
        methods = [
            ("size_name", "Size + Name"),
            ("smart", "Smart Detection"),
            ("hash", "Content Hash"),
        ]

        print("🔧 Creating method button selector...")

        for method_id, method_text in methods:
            button = Gtk.ToggleButton(label=method_text)
            button.set_active(method_id == "size_name")  # Default selection
            button.connect("toggled", self._on_method_button_toggled, method_id)

            self.method_buttons[method_id] = button
            method_box.append(button)

            print(f"   📋 Added button: {method_text} ({method_id})")

        toolbar.append(method_box)
        print("   ✅ Method button selector complete")

        # Keep the combo box for compatibility but make it hidden for now
        self.method_combo = Gtk.ComboBoxText()
        self.method_combo.append("size_name", "Size + Name")
        self.method_combo.append("smart", "Smart Detection")
        self.method_combo.append("hash", "Content Hash")
        self.method_combo.set_active(0)
        self.method_combo.set_visible(False)  # Hide the problematic combo
        toolbar.append(self.method_combo)

        # Refresh button (re-runs duplicate detection)
        self.refresh_button = Gtk.Button(label="Refresh Results")
        self.refresh_button.connect("clicked", self._on_refresh_clicked)
        toolbar.append(self.refresh_button)

        # Scan button (scans filesystem to update database)
        self.scan_button = Gtk.Button(label="Scan Directories")
        self.scan_button.connect("clicked", self._on_scan_clicked)
        toolbar.append(self.scan_button)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        toolbar.append(separator)

        # Auto-select button
        self.auto_select_button = Gtk.Button(label="Auto-Select Duplicates")
        self.auto_select_button.connect("clicked", self._on_auto_select_clicked)
        toolbar.append(self.auto_select_button)

        # Clear selection button
        clear_btn = Gtk.Button(label="Clear Selection")
        clear_btn.connect("clicked", self._on_clear_selection_clicked)
        toolbar.append(clear_btn)

        # Delete button
        self.delete_button = Gtk.Button(label="Delete Selected")
        self.delete_button.add_css_class("destructive-action")
        self.delete_button.connect("clicked", self._on_delete_clicked)
        if self.delete_button:
            self.delete_button.set_sensitive(False)
        toolbar.append(self.delete_button)

        return toolbar

    def _create_groups_panel(self) -> Gtk.Widget:
        """Create duplicate groups panel."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        # Header
        header = Gtk.Label(label="Duplicate Groups")
        header.set_markup("<b>Duplicate Groups</b>")
        box.append(header)

        # Groups list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        self.groups_store = Gtk.ListStore(
            str, str, int, str
        )  # name, size_info, file_count, savings
        self.groups_tree = Gtk.TreeView(model=self.groups_store)

        # Columns
        columns = [
            ("Group", 0, 200),
            ("Total Size", 1, 100),
            ("Files", 2, 60),
            ("Potential Savings", 3, 120),
        ]

        for title, col_id, width in columns:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_min_width(width)
            column.set_resizable(True)
            self.groups_tree.append_column(column)

        # Selection handler
        selection = self.groups_tree.get_selection()
        selection.connect("changed", self._on_group_selected)

        scrolled.set_child(self.groups_tree)
        box.append(scrolled)

        return box

    def _create_files_panel(self) -> Gtk.Widget:
        """Create files panel for selected group."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        # Header
        self.files_header = Gtk.Label(label="Files in Group")
        self.files_header.set_markup("<b>Files in Group</b>")
        box.append(self.files_header)

        # Files list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        self.files_store = Gtk.ListStore(
            bool, str, str, str, str, str, str
        )  # selected, filename, size, modified, location, recommendation, path
        self.files_tree = Gtk.TreeView(model=self.files_store)

        # Enable row selection for better UX
        self.files_tree.set_activate_on_single_click(False)
        selection = self.files_tree.get_selection()
        selection.set_mode(Gtk.SelectionMode.SINGLE)

        # Connect double-click to open file
        self.files_tree.connect("row-activated", self._on_row_activated)

        # Checkbox column
        checkbox_renderer = Gtk.CellRendererToggle()
        checkbox_renderer.connect("toggled", self._on_file_toggled)
        checkbox_column = Gtk.TreeViewColumn("Delete", checkbox_renderer, active=0)
        self.files_tree.append_column(checkbox_column)

        # Text columns
        columns = [
            ("Filename", 1, 200),
            ("Size", 2, 80),
            ("Modified", 3, 120),
            ("Location", 4, 250),
            ("Recommendation", 5, 100),
        ]

        for title, col_id, width in columns:
            renderer = Gtk.CellRendererText()
            renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_min_width(width)
            column.set_resizable(True)
            self.files_tree.append_column(column)

        scrolled.set_child(self.files_tree)
        box.append(scrolled)

        # File actions
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        # Add instructions for user
        instructions = Gtk.Label()
        instructions.set_markup(
            "<small><i>Select a row or check a file, then:</i></small>"
        )
        actions_box.append(instructions)

        open_btn = Gtk.Button(label="Open File")
        open_btn.set_tooltip_text(
            "Open the selected file with default application (or double-click row)"
        )
        open_btn.connect("clicked", self._on_open_file_clicked)
        actions_box.append(open_btn)

        reveal_btn = Gtk.Button(label="Show in Folder")
        reveal_btn.set_tooltip_text("Open file manager to show the selected file")
        reveal_btn.connect("clicked", self._on_reveal_file_clicked)
        actions_box.append(reveal_btn)

        box.append(actions_box)

        return box

    def _create_status_bar(self) -> Gtk.Widget:
        """Create status bar."""
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_hexpand(True)
        self.status_label.set_halign(Gtk.Align.START)
        status_box.append(self.status_label)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_size_request(200, -1)
        self.progress_bar.set_visible(False)
        status_box.append(self.progress_bar)

        return status_box

    def _on_method_changed(self, combo: Gtk.ComboBoxText) -> None:
        """Handle detection method change."""
        method_id = combo.get_active_id()
        method_text = combo.get_active_text()
        active_index = combo.get_active()

        print(f"🔀 Method changed EVENT TRIGGERED:")
        print(f"   📋 Active Index: {active_index}")
        print(f"   🆔 Method ID: {method_id}")
        print(f"   📝 Method Text: {method_text}")
        print(f"   🎛️  Combo Sensitive: {combo.get_sensitive()}")
        print(f"   🔄 Operation Running: {getattr(self, '_operation_running', False)}")
        print(f"   📊 Current Method: {getattr(self, '_current_method', 'None')}")

        # Skip if this is a programmatic change (no method_id means loading state)
        if method_id is None:
            print("   ⚠️  Skipping programmatic combo box change (method_id is None)")
            return

        # Check if combo is in a valid state
        if active_index < 0:
            print("   ⚠️  Invalid combo state: active_index < 0")
            return

        # Check if operation is running, but don't block - let it queue instead
        if hasattr(self, "_operation_running") and self._operation_running:
            print("   ⚠️  Operation already running, QUEUING method change")
            print(f"   📋 Will switch to {method_id} after current operation completes")

            # Get current selection before queuing (with error handling)
            try:
                current_group = self._get_selected_group_name()
            except Exception as e:
                print(f"   ❌ Error getting selection for queue: {e}")
                current_group = None

            # Queue this method change for after the current operation
            self._queued_method = method_id
            self._queued_selection = current_group
            return

        # Skip if this change is the same as current method
        if hasattr(self, "_current_method") and self._current_method == method_id:
            print(f"   ✅ Method already set to {method_id}, skipping")
            return

        # Store the new method
        old_method = getattr(self, "_current_method", "None")
        self._current_method = method_id
        print(f"   🔄 Method transition: {old_method} → {method_id}")

        # Store current selection (with error handling)
        try:
            current_group = self._get_selected_group_name()
            print(f"   📝 Preserving selection: {current_group}")
        except Exception as e:
            print(f"   ❌ Error getting selection: {e}")
            current_group = None

        if self.status_label:
            self.status_label.set_text(f"Switching to {method_text}...")

        # Add a small delay to prevent rapid switching issues
        print(f"   ⏰ Scheduling duplicate loading in 100ms...")
        GLib.timeout_add(
            100, lambda: self._load_duplicates(preserve_selection=current_group)
        )

    def _on_method_activated(self, combo: Gtk.ComboBoxText) -> None:
        """Handle method activation (backup signal)."""
        method_id = combo.get_active_id()
        method_text = combo.get_active_text()
        print(f"🔄 Method ACTIVATED signal triggered: {method_id} ({method_text})")

        # For now, just log this - the changed signal should handle the logic
        # This helps debug if changed signals aren't firing properly

    def _on_combo_focus_changed(self, combo: Gtk.ComboBoxText, param) -> None:
        """Handle combo box focus changes."""
        has_focus = combo.get_property("has-focus")
        print(f"🎯 Combo focus changed: has_focus={has_focus}")

    def _on_combo_clicked(self, gesture, n_press, x, y) -> None:
        """Handle combo box mouse clicks."""
        print(f"🖱️  Combo clicked: n_press={n_press}, x={x}, y={y}")
        combo = gesture.get_widget()
        current_method = combo.get_active_id()
        is_sensitive = combo.get_sensitive()
        print(f"   📊 Click state: method='{current_method}', sensitive={is_sensitive}")

        if not is_sensitive:
            print("   ⚠️  Combo is not sensitive - click may be ignored")

        if hasattr(self, "_operation_running") and self._operation_running:
            print("   ⚠️  Operation running during click - this could cause issues")

        # WORKAROUND: Since GTK4 ComboBoxText changed signal isn't firing reliably,
        # let's implement a delayed check to see if the selection actually changed
        GLib.timeout_add(
            50, lambda: self._check_combo_change_after_click(combo, current_method)
        )

    def _check_combo_change_after_click(
        self, combo: Gtk.ComboBoxText, previous_method: str
    ) -> bool:
        """Check if combo selection changed after a click and manually trigger change if needed."""
        current_method = combo.get_active_id()
        print(f"🔍 Checking combo after click: {previous_method} → {current_method}")

        if current_method != previous_method:
            print(f"   ✅ Method changed detected: triggering manual change event")
            # Manually trigger the method change since the signal didn't fire
            self._manual_method_change(current_method)
        else:
            print(f"   📋 No method change detected")

        return False  # Don't repeat the timeout

    def _manual_method_change(self, method_id: str) -> None:
        """Manually trigger method change logic (workaround for GTK4 signal issues)."""
        print(f"🔧 Manual method change triggered: {method_id}")

        # Get the method text
        method_map = {
            "size_name": "Size + Name",
            "smart": "Smart Detection",
            "hash": "Content Hash",
        }
        method_text = method_map.get(method_id, method_id)

        # Skip if this is the same as current method
        if hasattr(self, "_current_method") and self._current_method == method_id:
            print(f"   ✅ Method already set to {method_id}, skipping")
            return

        # Check if operation is running, queue if needed
        if hasattr(self, "_operation_running") and self._operation_running:
            print("   ⚠️  Operation already running, QUEUING method change")
            print(f"   📋 Will switch to {method_id} after current operation completes")

            # Get current selection before queuing (with error handling)
            try:
                current_group = self._get_selected_group_name()
            except Exception as e:
                print(f"   ❌ Error getting selection for queue: {e}")
                current_group = None

            # Queue this method change
            self._queued_method = method_id
            self._queued_selection = current_group
            return

        # Store the new method
        old_method = getattr(self, "_current_method", "None")
        self._current_method = method_id
        print(f"   🔄 Method transition: {old_method} → {method_id}")

        # Store current selection (with error handling)
        try:
            current_group = self._get_selected_group_name()
            print(f"   📝 Preserving selection: {current_group}")
        except Exception as e:
            print(f"   ❌ Error getting selection: {e}")
            current_group = None

        if self.status_label:
            self.status_label.set_text(f"Switching to {method_text}...")

        # Trigger the duplicate loading
        print(f"   ⏰ Scheduling duplicate loading in 100ms...")
        GLib.timeout_add(
            100, lambda: self._load_duplicates(preserve_selection=current_group)
        )

    def _on_method_button_toggled(
        self, button: Gtk.ToggleButton, method_id: str
    ) -> None:
        """Handle method button toggle events."""
        if not button.get_active():
            # Button was deactivated, ignore
            return

        print(f"🔘 Method button toggled: {method_id}")

        # Deactivate other buttons (radio button behavior)
        for other_id, other_button in self.method_buttons.items():
            if other_id != method_id and other_button.get_active():
                print(f"   🔄 Deactivating {other_id} button")
                other_button.set_active(False)

        # Update the hidden combo box to stay in sync
        method_index_map = {"size_name": 0, "smart": 1, "hash": 2}
        if method_id in method_index_map and self.method_combo:
            self.method_combo.set_active(method_index_map[method_id])

        # Trigger the method change using our manual method
        self._manual_method_change(method_id)

    def _get_configured_directories(self) -> List[str]:
        """Get the list of directories configured for scanning."""
        try:
            if (
                hasattr(self.parent_window, "config_manager")
                and self.parent_window.config_manager
            ):
                directories = self.parent_window.config_manager.get_scan_directories()
                print(f"📂 Using configured directories: {directories}")
                return directories
            else:
                print("⚠️  No config manager available, scanning all files")
                return []
        except Exception as e:
            print(f"❌ Error getting configured directories: {e}")
            return []

    def _load_duplicates(self, preserve_selection: Optional[str] = None) -> None:
        """Load duplicate groups in background."""
        # Prevent multiple simultaneous operations
        if hasattr(self, "_operation_running") and self._operation_running:
            print("   ⚠️  Operation already running, skipping")
            return

        self._operation_running = True
        print(f"🔄 Loading duplicates (preserve_selection={preserve_selection})")

        # Disable UI controls during operation
        self._set_ui_enabled(False)

        if self.status_label:
            self.status_label.set_text("Loading duplicates...")

        if self.progress_bar:
            self.progress_bar.set_visible(True)
            self.progress_bar.pulse()

        def load_worker():
            try:
                # Get selected method from combo box
                active_id = self.method_combo.get_active_id()
                method = active_id if active_id else "size_name"
                print(f"   🔍 Using method: {method}")

                # Get configured directories to filter duplicates to only configured paths
                configured_dirs = self._get_configured_directories()
                duplicates = self.duplicate_detector.find_duplicates(
                    method=method, min_file_size=0, filter_directories=configured_dirs
                )
                print(f"   ✅ Found {len(duplicates)} groups")
                GLib.idle_add(
                    self._on_duplicates_loaded, duplicates, preserve_selection
                )
            except Exception as e:
                print(f"   ❌ Error: {e}")
                GLib.idle_add(self._on_load_error, str(e))

        threading.Thread(target=load_worker, daemon=True).start()

    def _on_duplicates_loaded(
        self,
        duplicates: Dict[str, List[Dict[str, Any]]],
        preserve_selection: Optional[str] = None,
    ) -> None:
        """Handle successful duplicate loading."""
        print(f"📊 Duplicates loaded, restoring selection: {preserve_selection}")
        self.duplicate_groups = duplicates

        if self.progress_bar:
            self.progress_bar.set_visible(False)

        self._populate_groups_list()

        # Restore selection if requested
        if preserve_selection:
            self._restore_group_selection(preserve_selection)

        total_groups = len(duplicates)
        total_files = sum(len(files) for files in duplicates.values())

        if self.status_label:
            self.status_label.set_text(
                f"Found {total_groups} duplicate groups with {total_files} files"
            )

        # Re-enable UI and mark operation complete
        self._set_ui_enabled(True)
        self._operation_running = False
        print("✅ Operation completed, UI re-enabled")

        # Process any queued method change
        if hasattr(self, "_queued_method") and self._queued_method:
            queued_method = self._queued_method
            queued_selection = getattr(self, "_queued_selection", None)

            print(f"🔄 Processing queued method change: {queued_method}")

            # Clear the queue
            self._queued_method = None
            self._queued_selection = None

            # Update the current method and trigger the change
            self._current_method = queued_method

            # Set the combo box to the queued method
            method_map = {"size_name": 0, "smart": 1, "hash": 2}
            if queued_method in method_map and self.method_combo:
                # Temporarily block handler to avoid recursion
                self.method_combo.handler_block_by_func(self._on_method_changed)
                self.method_combo.set_active(method_map[queued_method])
                self.method_combo.handler_unblock_by_func(self._on_method_changed)

                # Load duplicates with the new method
                GLib.timeout_add(
                    100,
                    lambda: self._load_duplicates(preserve_selection=queued_selection),
                )

    def _on_load_error(self, error: str) -> None:
        """Handle duplicate loading error."""
        print(f"❌ Load error: {error}")

        if self.progress_bar:
            self.progress_bar.set_visible(False)

        if self.status_label:
            self.status_label.set_text(f"Error loading duplicates: {error}")

        # Re-enable UI even on error
        self._set_ui_enabled(True)
        self._operation_running = False
        print("🔧 UI re-enabled after error")

        # Process any queued method change even after errors
        if hasattr(self, "_queued_method") and self._queued_method:
            queued_method = self._queued_method
            queued_selection = getattr(self, "_queued_selection", None)

            print(f"🔄 Processing queued method change after error: {queued_method}")

            # Clear the queue
            self._queued_method = None
            self._queued_selection = None

            # Update the current method and trigger the change
            self._current_method = queued_method

            # Set the combo box to the queued method
            method_map = {"size_name": 0, "smart": 1, "hash": 2}
            if queued_method in method_map and self.method_combo:
                # Temporarily block handler to avoid recursion
                self.method_combo.handler_block_by_func(self._on_method_changed)
                self.method_combo.set_active(method_map[queued_method])
                self.method_combo.handler_unblock_by_func(self._on_method_changed)

                # Load duplicates with the new method
                GLib.timeout_add(
                    100,
                    lambda: self._load_duplicates(preserve_selection=queued_selection),
                )

        self.logger.error(f"Failed to load duplicates: {error}")

    def _populate_groups_list(self) -> None:
        """Populate the groups list."""
        if not self.groups_store:
            return

        self.groups_store.clear()

        for group_name, files in self.duplicate_groups.items():
            total_size = sum(f["size"] for f in files)
            file_count = len(files)

            # Calculate potential savings (all but largest file)
            largest_size = max(f["size"] for f in files)
            potential_savings = total_size - largest_size

            size_str = self._format_size(total_size)
            savings_str = self._format_size(potential_savings)

            self.groups_store.append([group_name, size_str, file_count, savings_str])

    def _on_group_selected(self, selection: Gtk.TreeSelection) -> None:
        """Handle group selection."""
        model, iter = selection.get_selected()
        if not iter or not self.files_store:
            return

        group_name = model.get_value(iter, 0)
        files = self.duplicate_groups.get(group_name, [])

        self._populate_files_list(files)

        if self.files_header:
            self.files_header.set_markup(f"<b>Files in Group: {group_name}</b>")

    def _populate_files_list(self, files: List[Dict[str, Any]]) -> None:
        """Populate files list for selected group."""
        if not self.files_store:
            return

        self.files_store.clear()

        # Clear any previous selections from other groups
        self.selected_for_deletion.clear()

        # Get recommendations for this group
        analysis = self.duplicate_detector.analyze_duplicate_group(files)
        keep_file_path = analysis.get("keep_file", {}).get("path", "")

        print(f"   📋 Populating files list for group, keep_file: {keep_file_path}")

        for file_record in files:
            is_recommended_for_deletion = file_record["path"] != keep_file_path
            size_str = self._format_size(file_record["size"])
            modified_str = self._format_date(file_record["modified_date"])

            recommendation = "DELETE" if is_recommended_for_deletion else "KEEP"

            # Add to the visual list
            self.files_store.append(
                [
                    is_recommended_for_deletion,  # Default selection (checkbox state)
                    file_record["filename"],
                    size_str,
                    modified_str,
                    file_record["directory"],
                    recommendation,
                    file_record["path"],
                ]
            )

            # IMPORTANT: Also update the selected_for_deletion set for auto-selected files
            if is_recommended_for_deletion:
                self.selected_for_deletion.add(file_record["path"])
                print(f"   ✅ Auto-selected for deletion: {file_record['filename']}")

        # Update the delete button state based on actual selections
        self._update_delete_button()
        print(
            f"   📊 Total files selected for deletion: {len(self.selected_for_deletion)}"
        )

    def _on_file_toggled(self, renderer: Gtk.CellRendererToggle, path: str) -> None:
        """Handle file selection toggle."""
        if not self.files_store:
            return

        iter = self.files_store.get_iter(path)
        current_value = self.files_store.get_value(iter, 0)
        new_value = not current_value

        self.files_store.set_value(iter, 0, new_value)

        file_path = self.files_store.get_value(iter, 6)

        if new_value:
            self.selected_for_deletion.add(file_path)
        else:
            self.selected_for_deletion.discard(file_path)

        self._update_delete_button()

    def _update_delete_button(self) -> None:
        """Update delete button state."""
        if self.delete_button:
            has_selection = len(self.selected_for_deletion) > 0
            print(
                f"   🗑️  Updating delete button: {len(self.selected_for_deletion)} files selected, enabled={has_selection}"
            )

            self.delete_button.set_sensitive(has_selection)

            if has_selection:
                label = f"Delete {len(self.selected_for_deletion)} Files"
                self.delete_button.set_label(label)
                print(f"   📝 Delete button label: '{label}'")
            else:
                self.delete_button.set_label("Delete Selected")
                print(f"   📝 Delete button label: 'Delete Selected' (disabled)")

    # Event handlers
    def _on_refresh_clicked(self, button: Gtk.Button) -> None:
        """Handle refresh button click."""
        print("🔄 Refresh button clicked")
        if self.status_label:
            self.status_label.set_text("Refreshing duplicates...")

        # Store current selection to preserve it (with error handling)
        try:
            current_group = self._get_selected_group_name()
            print(f"   📝 Preserving selection: {current_group}")
        except Exception as e:
            print(f"   ❌ Error getting selection for refresh: {e}")
            current_group = None

        self._load_duplicates(preserve_selection=current_group)

    def _on_scan_clicked(self, button: Gtk.Button) -> None:
        """Handle scan button click - scans filesystem to update database."""
        print("📁 Scan Directories button clicked")

        if self.status_label:
            self.status_label.set_text("Scanning directories for new files...")

        # For now, use some default directories to scan
        # In a full implementation, this would get directories from config or show a dialog
        default_dirs = ["/tmp", "/home"]  # Safe directories for testing

        # Create file scanner
        file_scanner = FileScanner(self.db_manager)

        print(f"   📂 Scanning directories: {default_dirs}")

        # Run scan in background
        def scan_worker():
            try:
                results = file_scanner.scan_directories(
                    directories=default_dirs,
                    exclude_patterns=["*.tmp", "*.cache"],
                    follow_symlinks=False,
                    scan_hidden=False,
                )
                GLib.idle_add(self._on_scan_completed, results)
            except Exception as e:
                print(f"   ❌ Scan error: {e}")
                GLib.idle_add(self._on_scan_error, str(e))

        # Disable scan button during operation
        if self.scan_button:
            self.scan_button.set_sensitive(False)

        threading.Thread(target=scan_worker, daemon=True).start()

    def _on_scan_completed(self, results: dict) -> None:
        """Handle successful scan completion."""
        print(f"📊 Scan completed: {results}")

        if self.status_label:
            files_scanned = results.get("files_scanned", 0)
            files_added = results.get("files_added", 0)
            files_updated = results.get("files_updated", 0)
            duration = results.get("duration", 0)

            self.status_label.set_text(
                f"Scan complete: {files_scanned} files scanned, "
                f"{files_added} added, {files_updated} updated in {duration:.1f}s"
            )

        # Re-enable scan button
        if self.scan_button:
            self.scan_button.set_sensitive(True)

        # Automatically refresh duplicates with new data
        print("   🔄 Auto-refreshing duplicates after scan")
        try:
            current_group = self._get_selected_group_name()
        except Exception as e:
            print(f"   ❌ Error getting selection after scan: {e}")
            current_group = None

        self._load_duplicates(preserve_selection=current_group)

    def _on_scan_error(self, error: str) -> None:
        """Handle scan error."""
        print(f"❌ Scan error: {error}")

        if self.status_label:
            self.status_label.set_text(f"Scan failed: {error}")

        # Re-enable scan button
        if self.scan_button:
            self.scan_button.set_sensitive(True)

    def _on_auto_select_clicked(self, button: Gtk.Button) -> None:
        """Handle auto-select button click."""
        if not self.files_store:
            return

        self.selected_for_deletion.clear()

        # Select all files marked for deletion
        iter = self.files_store.get_iter_first()
        while iter:
            recommendation = self.files_store.get_value(iter, 5)
            should_select = recommendation == "DELETE"

            self.files_store.set_value(iter, 0, should_select)

            if should_select:
                file_path = self.files_store.get_value(iter, 6)
                self.selected_for_deletion.add(file_path)

            iter = self.files_store.iter_next(iter)

        self._update_delete_button()

    def _on_clear_selection_clicked(self, button: Gtk.Button) -> None:
        """Handle clear selection button click."""
        if not self.files_store:
            return

        self.selected_for_deletion.clear()

        iter = self.files_store.get_iter_first()
        while iter:
            self.files_store.set_value(iter, 0, False)
            iter = self.files_store.iter_next(iter)

        self._update_delete_button()

    def _on_delete_clicked(self, button: Gtk.Button) -> None:
        """Handle delete button click."""
        if not self.selected_for_deletion:
            return

        # Show confirmation dialog
        self._show_delete_confirmation()

    def _on_open_file_clicked(self, button: Gtk.Button) -> None:
        """Handle open file button click."""
        selected_path = self._get_selected_file_path()
        print(f"📂 Open File clicked: selected_path='{selected_path}'")

        if selected_path:
            self._open_file(selected_path)
        else:
            print("   ⚠️  No file selected")
            if self.status_label:
                self.status_label.set_text("No file selected")

    def _on_reveal_file_clicked(self, button: Gtk.Button) -> None:
        """Handle reveal file button click."""
        selected_path = self._get_selected_file_path()
        print(f"📁 Show in Folder clicked: selected_path='{selected_path}'")

        if selected_path:
            self._reveal_file(selected_path)
        else:
            print("   ⚠️  No file selected")
            if self.status_label:
                self.status_label.set_text("No file selected")

    def _get_selected_file_path(self) -> Optional[str]:
        """Get path of currently selected file."""
        if not self.files_tree or not self.files_store:
            print("   📋 No files tree or store available")
            return None

        # First, try to get the TreeView row selection
        selection = self.files_tree.get_selection()
        if selection:
            model, iter = selection.get_selected()
            if iter:
                file_path = model.get_value(iter, 6)  # Path column
                print(f"   📋 Selected file path (from row selection): '{file_path}'")
                return file_path

        print("   📋 No row selected in tree view, checking for checked files...")

        # If no row is selected, try to find a checked file (checkbox selection)
        # This handles the case where user checked a box but didn't select the row
        iter = self.files_store.get_iter_first()
        checked_files = []

        while iter:
            is_checked = self.files_store.get_value(iter, 0)  # Checkbox column
            if is_checked:
                file_path = self.files_store.get_value(iter, 6)  # Path column
                checked_files.append(file_path)
                print(f"   📋 Found checked file: '{file_path}'")
            iter = self.files_store.iter_next(iter)

        if len(checked_files) == 1:
            # If exactly one file is checked, use that
            print(f"   📋 Using single checked file: '{checked_files[0]}'")
            return checked_files[0]
        elif len(checked_files) > 1:
            # If multiple files are checked, use the first one but warn user
            print(
                f"   ⚠️  Multiple files checked ({len(checked_files)}), using first: '{checked_files[0]}'"
            )
            return checked_files[0]

        # If no files are checked either, try to get the first file in the list
        if self.files_store:
            iter = self.files_store.get_iter_first()
            if iter:
                file_path = self.files_store.get_value(iter, 6)
                print(f"   📋 No selection found, using first file: '{file_path}'")
                return file_path
            else:
                print("   📋 Files store exists but is empty")
        else:
            print("   📋 No files store available")

        print("   📋 No files available in the list")
        return None

    def _open_file(self, file_path: str) -> None:
        """Open file with default application."""
        print(f"   🔍 Attempting to open file: {file_path}")

        try:
            import subprocess
            import os

            if os.path.exists(file_path):
                print(f"   ✅ File exists, attempting to open")

                # Try multiple methods to open the file
                open_commands = ["xdg-open", "open", "start"]
                success = False

                for cmd in open_commands:
                    try:
                        result = subprocess.run(
                            [cmd, file_path],
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        if result.returncode == 0:
                            print(f"   ✅ Successfully opened file with {cmd}")
                            if self.status_label:
                                self.status_label.set_text(
                                    f"Opened: {os.path.basename(file_path)}"
                                )
                            success = True
                            break
                        else:
                            print(f"   ⚠️  {cmd} failed: {result.stderr}")
                    except FileNotFoundError:
                        print(f"   ⚠️  {cmd} not found")
                        continue

                if not success:
                    print(f"   ❌ No suitable file opener found")
                    message = f"File opener not available - file exists: {os.path.basename(file_path)}"
                    if self.status_label:
                        self.status_label.set_text(message)
            else:
                print(f"   ❌ File does not exist")
                message = f"File not found: {file_path}"
                print(f"   ⚠️  {message}")
                if self.status_label:
                    self.status_label.set_text(message)

        except Exception as e:
            print(f"   ❌ Exception opening file: {e}")
            if self.status_label:
                self.status_label.set_text(f"Failed to open file: {e}")
            self.logger.error(f"Failed to open file: {e}")

    def _is_test_data_path(self, file_path: str) -> bool:
        """Check if this is a test data path that doesn't actually exist."""
        if not file_path:
            return False

        test_indicators = [
            "/backup/",
            "/downloads/",
            "/documents/",
            "/tmp/test",
            "/photos/",
            "/backup/documents/",
            "/backup/vacation",
            "vacation_beach.jpg",
            "meeting_notes.txt",
            "unique_photo.jpg",
        ]

        is_test = any(indicator in file_path for indicator in test_indicators)

        # Also check if path starts with common test prefixes
        test_prefixes = ["/test/", "/demo/", "/sample/"]
        is_test = is_test or any(
            file_path.startswith(prefix) for prefix in test_prefixes
        )

        print(f"   🔍 Test data check: '{file_path}' -> {is_test}")
        return is_test

    def _reveal_file(self, file_path: str) -> None:
        """Reveal file in file manager."""
        print(f"   📁 Attempting to reveal file: {file_path}")

        try:
            import subprocess
            import os

            if os.path.exists(file_path):
                directory = os.path.dirname(file_path)
                print(f"   ✅ File exists, attempting to open directory: {directory}")

                # Try multiple methods to open the directory
                open_commands = ["xdg-open", "open", "start", "explorer"]
                success = False

                for cmd in open_commands:
                    try:
                        result = subprocess.run(
                            [cmd, directory],
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        if result.returncode == 0:
                            print(f"   ✅ Successfully opened folder with {cmd}")
                            if self.status_label:
                                self.status_label.set_text(
                                    f"Opened folder: {directory}"
                                )
                            success = True
                            break
                        else:
                            print(f"   ⚠️  {cmd} failed: {result.stderr}")
                    except FileNotFoundError:
                        print(f"   ⚠️  {cmd} not found")
                        continue

                if not success:
                    print(f"   ❌ No suitable folder opener found")
                    message = f"File manager not available - folder exists: {directory}"
                    if self.status_label:
                        self.status_label.set_text(message)
            else:
                print(f"   ❌ File does not exist")
                message = f"File not found: {file_path}"
                print(f"   ⚠️  {message}")
                if self.status_label:
                    self.status_label.set_text(message)

        except Exception as e:
            print(f"   ❌ Exception revealing file: {e}")
            if self.status_label:
                self.status_label.set_text(f"Failed to open folder: {e}")
            self.logger.error(f"Failed to reveal file: {e}")

    def _on_row_activated(
        self, tree_view: Gtk.TreeView, path: Gtk.TreePath, column: Gtk.TreeViewColumn
    ) -> None:
        """Handle double-click on tree view row - open the file."""
        print(f"   🖱️  Row double-clicked: path={path}")

        # Get the file path from the activated row
        model = tree_view.get_model()
        iter = model.get_iter(path)
        if iter:
            file_path = model.get_value(iter, 6)  # Path column
            print(f"   📂 Double-click opening file: {file_path}")
            self._open_file(file_path)
        else:
            print("   ❌ Could not get file path from activated row")

    def _show_test_data_info_dialog(
        self, action: str, file_path: str, description: str
    ) -> None:
        """Show informational dialog for test data operations."""
        print(f"   💬 Showing test data info dialog for {action}")

        try:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=f"Test Data - {action}",
            )

            secondary_text = (
                f"Selected file: {file_path}\n\n{description}\n\n"
                "This is test/demo data with fictional file paths. "
                "In a real application, this would work with actual files on your system."
            )

            # GTK4 way to set secondary text
            try:
                dialog.set_property("secondary-text", secondary_text)
            except Exception as e:
                print(f"   ⚠️  Could not set secondary text: {e}")
                # Fallback: add secondary text to the main text
                dialog.set_property(
                    "text", f"{dialog.get_property('text')}\n\n{secondary_text}"
                )

            # Add some styling to make it clear this is test data
            dialog.get_content_area().set_margin_start(10)
            dialog.get_content_area().set_margin_end(10)
            dialog.get_content_area().set_margin_top(10)
            dialog.get_content_area().set_margin_bottom(10)

            def on_response(dialog, response_id):
                print(f"   💬 Test data dialog closed with response: {response_id}")
                dialog.destroy()

            dialog.connect("response", on_response)
            dialog.present()

        except Exception as e:
            print(f"   ❌ Error showing test data dialog: {e}")
            # Fallback to console output if dialog fails
            print(f"   💬 Test Data Info - {action}:")
            print(f"      File: {file_path}")
            print(f"      {description}")

    def _show_delete_confirmation(self) -> None:
        """Show deletion confirmation dialog."""
        count = len(self.selected_for_deletion)

        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Confirm File Deletion",
            secondary_text=f"Are you sure you want to delete {count} duplicate files? "
            "This action cannot be undone.",
        )

        def on_response(dialog: Gtk.MessageDialog, response: int) -> None:
            if response == Gtk.ResponseType.YES:
                self._perform_deletion()
            dialog.destroy()

        dialog.connect("response", on_response)
        dialog.show()

    def _perform_deletion(self) -> None:
        """Perform actual file deletion."""
        import os

        if self.status_label:
            self.status_label.set_text("Deleting files...")

        deleted_count = 0
        failed_count = 0
        failed_files = []

        for file_path in list(self.selected_for_deletion):
            try:
                print(f"🗑️  Deleting file: {file_path}")

                # Check if file exists before attempting deletion
                if not os.path.exists(file_path):
                    print(f"   ⚠️  File not found: {file_path}")
                    # Still try to remove from database in case it's orphaned
                    self.db_manager.remove_file_by_path(file_path)
                    failed_count += 1
                    failed_files.append(f"{file_path} (not found)")
                    continue

                # Attempt to delete the file
                os.remove(file_path)
                print(f"   ✅ File deleted successfully: {file_path}")

                # Remove from database
                db_removed = self.db_manager.remove_file_by_path(file_path)
                if db_removed:
                    print(f"   ✅ Removed from database: {file_path}")
                else:
                    print(f"   ⚠️  File not found in database: {file_path}")

                deleted_count += 1

            except PermissionError as e:
                error_msg = (
                    f"Permission denied (readonly): {os.path.basename(file_path)}"
                )
                print(f"   🔒 {error_msg}")
                self.logger.info(f"Failed to delete readonly file {file_path}: {e}")
                failed_count += 1
                failed_files.append(error_msg)

            except OSError as e:
                error_msg = f"OS error for {os.path.basename(file_path)}: {str(e)}"
                print(f"   ❌ {error_msg}")
                self.logger.error(f"OS error deleting {file_path}: {e}")
                failed_count += 1
                failed_files.append(error_msg)

            except Exception as e:
                error_msg = (
                    f"Unexpected error for {os.path.basename(file_path)}: {str(e)}"
                )
                print(f"   ❌ {error_msg}")
                self.logger.error(f"Failed to delete {file_path}: {e}")
                failed_count += 1
                failed_files.append(error_msg)

        # Clear selection
        self.selected_for_deletion.clear()

        # Refresh the view
        self._load_duplicates()

        # Update status with results
        if self.status_label:
            status_msg = f"Deleted: {deleted_count} files"
            if failed_count > 0:
                status_msg += f", {failed_count} failed"

                # Show detailed error information for failed files
                if failed_files:
                    print(f"\n📋 Deletion Summary:")
                    print(f"   ✅ Successfully deleted: {deleted_count}")
                    print(f"   ❌ Failed to delete: {failed_count}")
                    if len(failed_files) <= 5:  # Show details for first 5 failures
                        for failure in failed_files:
                            print(f"      • {failure}")
                    else:
                        for failure in failed_files[:3]:
                            print(f"      • {failure}")
                        print(f"      ... and {len(failed_files) - 3} more")

            self.status_label.set_text(status_msg)

    def _format_size(self, size_bytes: float) -> str:
        """Format file size in human readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def _format_date(self, timestamp: float) -> str:
        """Format timestamp as readable date."""
        import datetime

        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")

    def _get_selected_group_name(self) -> Optional[str]:
        """Get the currently selected group name."""
        if not self.groups_tree:
            print("   ⚠️  groups_tree is None, returning None for selection")
            return None

        try:
            selection = self.groups_tree.get_selection()
            if not selection:
                print("   ⚠️  groups_tree has no selection object")
                return None

            model, iter = selection.get_selected()
            if iter:
                group_name = model.get_value(iter, 0)  # Group name column
                print(f"   📋 Current group selection: '{group_name}'")
                return group_name
            else:
                print("   📋 No group currently selected")
                return None
        except Exception as e:
            print(f"   ❌ Error getting group selection: {e}")
            return None

    def _restore_group_selection(self, group_name: str) -> None:
        """Restore selection to a specific group."""
        if not group_name or not self.groups_store:
            return

        print(f"   🔍 Looking for group: {group_name}")
        iter = self.groups_store.get_iter_first()
        while iter:
            if self.groups_store.get_value(iter, 0) == group_name and self.groups_tree:
                selection = self.groups_tree.get_selection()
                if selection:
                    selection.select_iter(iter)
                    print(f"   ✅ Restored selection to: {group_name}")
                return
            iter = self.groups_store.iter_next(iter)

        print(f"   ⚠️  Group not found: {group_name}")

    def _set_ui_enabled(self, enabled: bool) -> None:
        """Enable/disable UI controls during operations."""
        print(f"   🎛️  UI controls {'enabled' if enabled else 'disabled'}")

        # Don't disable method buttons - they should always be clickable
        # Method changes can be queued if operations are running
        for button in self.method_buttons.values():
            button.set_sensitive(True)

        # Scan and refresh buttons can be disabled during operations
        if self.scan_button:
            self.scan_button.set_sensitive(enabled)
        if self.refresh_button:
            self.refresh_button.set_sensitive(enabled)

        # Manage action buttons based on state and selections
        if enabled:
            # When UI is enabled, use the actual selection state for delete button
            self._update_delete_button()  # This will set delete button based on selections
            if self.auto_select_button:
                self.auto_select_button.set_sensitive(True)
        else:
            # When UI is disabled (during operations), disable action buttons
            if self.delete_button:
                self.delete_button.set_sensitive(False)
            if self.auto_select_button:
                self.auto_select_button.set_sensitive(False)
