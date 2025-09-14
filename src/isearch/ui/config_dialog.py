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
        """Save settings from dialog."""
        # Save directories
        directories = []
        iter = self.dirs_store.get_iter_first()
        while iter:
            directory = self.dirs_store.get_value(iter, 0)
            directories.append(directory)
            iter = self.dirs_store.iter_next(iter)

        self.config_manager.set_scan_directories(directories)

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

    def run_and_save(self) -> bool:
        """Run dialog and save if OK was clicked."""

        def on_response(dialog: Gtk.Dialog, response: int) -> None:
            if response == Gtk.ResponseType.OK:
                self._save_settings()
            dialog.destroy()

        self.connect("response", on_response)
        self.show()
        return True
