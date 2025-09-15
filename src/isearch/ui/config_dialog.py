"""Configuration dialog for directory management."""

import logging
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from isearch.utils.config_manager import ConfigManager  # noqa: E402


class ConfigDialog(Gtk.Dialog):
    """Configuration dialog for scan directories and settings."""

    def __init__(self, parent: Gtk.Window, config_manager: ConfigManager) -> None:
        super().__init__(title="Configuration", transient_for=parent, modal=True)

        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.parent_window = parent

        # Track original directories for change detection
        self.original_directories = set(self.config_manager.get_scan_directories())

        # Dialog properties
        self.set_default_size(600, 400)

        # Create UI
        self._setup_ui()

        # Load current settings
        self._load_settings()

    def _setup_ui(self) -> None:
        """Create the dialog UI."""
        # Get dialog content area
        content_area = self.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_start(20)
        content_area.set_margin_end(20)
        content_area.set_margin_top(20)
        content_area.set_margin_bottom(20)

        # Create notebook for tabs
        notebook = Gtk.Notebook()
        content_area.append(notebook)

        # Directories tab
        dirs_page = self._create_directories_page()
        notebook.append_page(dirs_page, Gtk.Label(label="Directories"))

        # Exclude patterns tab
        patterns_page = self._create_patterns_page()
        notebook.append_page(patterns_page, Gtk.Label(label="Exclude Patterns"))

        # Options tab
        options_page = self._create_options_page()
        notebook.append_page(options_page, Gtk.Label(label="Options"))

        # Dialog buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save", Gtk.ResponseType.OK)

    def _create_directories_page(self) -> Gtk.Widget:
        """Create directories configuration page."""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        # Label
        label = Gtk.Label(label="Directories to scan:")
        label.set_halign(Gtk.Align.START)
        page.append(label)

        # Directory list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        self.dirs_store = Gtk.ListStore(str)
        self.dirs_tree = Gtk.TreeView(model=self.dirs_store)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Directory Path", renderer, text=0)
        self.dirs_tree.append_column(column)

        scrolled.set_child(self.dirs_tree)
        page.append(scrolled)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        add_btn = Gtk.Button(label="Add Directory")
        add_btn.connect("clicked", self._on_add_directory)
        button_box.append(add_btn)

        remove_btn = Gtk.Button(label="Remove Selected")
        remove_btn.connect("clicked", self._on_remove_directory)
        button_box.append(remove_btn)

        page.append(button_box)

        return page

    def _create_patterns_page(self) -> Gtk.Widget:
        """Create exclude patterns page."""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        # Label
        label = Gtk.Label(label="Exclude patterns (one per line):")
        label.set_halign(Gtk.Align.START)
        page.append(label)

        # Text view for patterns
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        self.patterns_view = Gtk.TextView()
        self.patterns_view.set_monospace(True)
        scrolled.set_child(self.patterns_view)
        page.append(scrolled)

        # Help text
        help_label = Gtk.Label()
        help_label.set_markup(
            "<small>Examples:\n"
            "*.tmp - exclude all .tmp files\n"
            "*/.git/* - exclude .git directories\n"
            "*/node_modules/* - exclude node_modules</small>"
        )
        help_label.set_halign(Gtk.Align.START)
        page.append(help_label)

        return page

    def _create_options_page(self) -> Gtk.Widget:
        """Create scan options page."""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        # Scan options
        self.follow_symlinks_check = Gtk.CheckButton(label="Follow symbolic links")
        page.append(self.follow_symlinks_check)

        self.scan_hidden_check = Gtk.CheckButton(
            label="Scan hidden files and directories"
        )
        page.append(self.scan_hidden_check)

        self.calculate_hashes_check = Gtk.CheckButton(
            label="Calculate file hashes (slower)"
        )
        page.append(self.calculate_hashes_check)

        return page

    def _load_settings(self) -> None:
        """Load current settings into the dialog."""
        # Load directories
        directories = self.config_manager.get_scan_directories()
        for directory in directories:
            self.dirs_store.append([directory])

        # Load exclude patterns
        patterns = self.config_manager.get_exclude_patterns()
        patterns_text = "\n".join(patterns)

        buffer = self.patterns_view.get_buffer()
        buffer.set_text(patterns_text, -1)

        # Load options
        self.follow_symlinks_check.set_active(
            self.config_manager.get("scan_options.follow_symlinks", True)
        )
        self.scan_hidden_check.set_active(
            self.config_manager.get("scan_options.scan_hidden", False)
        )
        self.calculate_hashes_check.set_active(
            self.config_manager.get("scan_options.calculate_hashes", False)
        )

    def _save_settings(self) -> None:
        """Save settings from dialog and synchronize database."""
        # Get new directories from dialog
        new_directories = []
        iter = self.dirs_store.get_iter_first()
        while iter:
            directory = self.dirs_store.get_value(iter, 0)
            new_directories.append(directory)
            iter = self.dirs_store.iter_next(iter)

        new_directories_set = set(new_directories)

        # Detect changes
        added_directories = new_directories_set - self.original_directories
        removed_directories = self.original_directories - new_directories_set

        print("📂 Directory changes detected:")
        print(f"   ➕ Added: {list(added_directories)}")
        print(f"   ➖ Removed: {list(removed_directories)}")

        # Save configuration first
        self.config_manager.set_scan_directories(new_directories)

        # Save exclude patterns
        buffer = self.patterns_view.get_buffer()
        start_iter = buffer.get_start_iter()
        end_iter = buffer.get_end_iter()
        patterns_text = buffer.get_text(start_iter, end_iter, False)

        patterns = [p.strip() for p in patterns_text.split("\n") if p.strip()]
        self.config_manager.set_exclude_patterns(patterns)

        # Save options
        self.config_manager.set(
            "scan_options.follow_symlinks", self.follow_symlinks_check.get_active()
        )
        self.config_manager.set(
            "scan_options.scan_hidden", self.scan_hidden_check.get_active()
        )
        self.config_manager.set(
            "scan_options.calculate_hashes", self.calculate_hashes_check.get_active()
        )

        # Save to file
        self.config_manager.save_config()

        # Synchronize database if directories changed
        if added_directories or removed_directories:
            self._synchronize_database(added_directories, removed_directories)

    def _on_add_directory(self, button: Gtk.Button) -> None:
        """Handle add directory button."""
        dialog = Gtk.FileChooserDialog(
            title="Select Directory",
            transient_for=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Select", Gtk.ResponseType.OK)

        def on_response(dialog: Gtk.FileChooserDialog, response: int) -> None:
            if response == Gtk.ResponseType.OK:
                folder = dialog.get_file()
                if folder:
                    path = folder.get_path()
                    if path:
                        self.dirs_store.append([path])
            dialog.destroy()

        dialog.connect("response", on_response)
        dialog.show()

    def _on_remove_directory(self, button: Gtk.Button) -> None:
        """Handle remove directory button."""
        selection = self.dirs_tree.get_selection()
        model, iter = selection.get_selected()
        if iter:
            model.remove(iter)

    def _synchronize_database(
        self, added_directories: set, removed_directories: set
    ) -> None:
        """Synchronize database with directory changes."""
        print("🔄 Synchronizing database with directory changes...")

        try:
            # Get database manager from parent window
            if (
                hasattr(self.parent_window, "db_manager")
                and self.parent_window.db_manager
            ):
                db_manager = self.parent_window.db_manager
            else:
                print("   ❌ No database manager available")
                return

            # Remove files from removed directories
            if removed_directories:
                print(
                    f"   🗑️  Removing files from {len(removed_directories)} "
                    f"directories..."
                )
                for removed_dir in removed_directories:
                    try:
                        # Remove files that start with this directory path
                        removed_count = db_manager.remove_files_by_directory(
                            removed_dir
                        )
                        print(
                            f"   ✅ Removed {removed_count} files from: {removed_dir}"
                        )
                    except Exception as e:
                        print(f"   ❌ Error removing files from {removed_dir}: {e}")

            # Scan new directories
            if added_directories:
                print(f"   📂 Scanning {len(added_directories)} new directories...")

                # Import scanner here to avoid circular imports
                from isearch.core.file_scanner import FileScanner

                scanner = FileScanner(db_manager)

                # Get scan options
                follow_symlinks = self.follow_symlinks_check.get_active()
                scan_hidden = self.scan_hidden_check.get_active()
                exclude_patterns = [
                    p.strip()
                    for p in self.patterns_view.get_buffer()
                    .get_text(
                        self.patterns_view.get_buffer().get_start_iter(),
                        self.patterns_view.get_buffer().get_end_iter(),
                        False,
                    )
                    .split("\n")
                    if p.strip()
                ]

                for added_dir in added_directories:
                    try:
                        print(f"   🔍 Scanning directory: {added_dir}")
                        results = scanner.scan_directories(
                            directories=[added_dir],
                            exclude_patterns=exclude_patterns,
                            follow_symlinks=follow_symlinks,
                            scan_hidden=scan_hidden,
                        )

                        files_added = results.get("files_added", 0)
                        files_updated = results.get("files_updated", 0)
                        print(
                            f"   ✅ Added {files_added} files, updated "
                            f"{files_updated} from: {added_dir}"
                        )

                    except Exception as e:
                        print(f"   ❌ Error scanning {added_dir}: {e}")

            # Update parent window status
            if (
                hasattr(self.parent_window, "status_label")
                and self.parent_window.status_label
            ):
                total_changes = len(added_directories) + len(removed_directories)
                self.parent_window.status_label.set_text(
                    f"Database synchronized: {total_changes} directory changes "
                    f"processed"
                )

            print("   🎉 Database synchronization completed!")

        except Exception as e:
            print(f"   ❌ Database synchronization failed: {e}")
            if (
                hasattr(self.parent_window, "status_label")
                and self.parent_window.status_label
            ):
                self.parent_window.status_label.set_text(f"Database sync failed: {e}")

    def run_and_save(self) -> bool:
        """Run dialog and save if OK was clicked."""

        def on_response(dialog: Gtk.Dialog, response: int) -> None:
            if response == Gtk.ResponseType.OK:
                self._save_settings()
            dialog.destroy()

        self.connect("response", on_response)
        self.show()
        return True
