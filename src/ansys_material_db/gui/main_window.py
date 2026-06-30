"""Main application window with left Toolbox navigation and right stacked content pages.

Ansys Workbench-inspired single-page switching layout.
"""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ansys_material_db.gui.styles import ANSYS_COLORS, get_ansys_stylesheet
from ansys_material_db.i18n import init_translator, t

logger = logging.getLogger(__name__)

_C = ANSYS_COLORS

# Toolbox navigation items: (key, icon, label_key)
_NAV_ITEMS: list[tuple[str, str, str]] = [
    ("materials", "\U0001f4e6", "nav.materials"),
    ("documents", "\U0001f4c4", "nav.documents"),
    # ("qa", "\U0001f4ac", "nav.qa"),  # removed
    ("xml", "\U0001f4cb", "nav.xml"),
    ("export", "\U0001f4e4", "nav.export"),
    ("settings", "\u2699\ufe0f", "nav.settings"),
]


class _ToolboxNav(QWidget):
    """Left sidebar navigation widget."""

    page_changed = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel(t("nav.toolbox"))
        header.setStyleSheet(
            f"color: {_C['text_secondary']}; font-size: 11px; "
            f"text-transform: uppercase; letter-spacing: 1px; "
            f"padding: 12px 16px; background: {_C['bg_secondary']}; "
            f"border-bottom: 1px solid {_C['border']};"
        )
        layout.addWidget(header)

        # Nav list
        self._list = QListWidget()
        self._list.setFrameShape(QListWidget.Shape.NoFrame)
        self._list.setSpacing(0)
        self._list.currentRowChanged.connect(self._on_current_changed)
        layout.addWidget(self._list)

        self._populate()
        self._list.setCurrentRow(0)

    def _populate(self) -> None:
        style_base = (
            f"QListWidget {{ background: {_C['bg_secondary']}; border: none; outline: none; }}"
            f"QListWidget::item {{ padding: 10px 16px; color: {_C['text_secondary']}; "
            f"font-size: 13px; border-left: 3px solid transparent; }}"
            f"QListWidget::item:hover {{ background: {_C['bg_tertiary']}; color: {_C['text_primary']}; }}"
            f"QListWidget::item:selected {{ background: {_C['bg_tertiary']}; color: #fff; "
            f"border-left: 3px solid {_C['accent_blue']}; }}"
        )
        self._list.setStyleSheet(style_base)

        for key, icon, label_key in _NAV_ITEMS:
            item = QListWidgetItem(f"  {icon}  {t(label_key)}")
            item.setData(Qt.ItemDataRole.UserRole, key)
            self._list.addItem(item)

    def _on_current_changed(self, row: int) -> None:
        if row >= 0:
            self.page_changed.emit(row)

    def refresh_labels(self) -> None:
        """Refresh all item labels for i18n."""
        for i, (key, icon, label_key) in enumerate(_NAV_ITEMS):
            item = self._list.item(i)
            if item:
                item.setText(f"  {icon}  {t(label_key)}")

    def set_current(self, index: int) -> None:
        self._list.setCurrentRow(index)


class _PageHeader(QWidget):
    """Page header bar."""

    def __init__(self, icon: str, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(38)
        self.setStyleSheet(
            f"background: {_C['bg_secondary']}; border-bottom: 1px solid {_C['border']};"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 14px; background: transparent;")
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {_C['text_primary']}; background: transparent;"
        )
        layout.addWidget(title_label)
        layout.addStretch()


class MainWindow(QMainWindow):
    """Top-level window with Toolbox navigation and stacked content pages."""

    MIN_WIDTH = 1200
    MIN_HEIGHT = 800

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("app.title"))
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.resize(1400, 900)

        # Backend references
        self._database = None
        self._knowledge_base = None
        self._llm_client = None
        self._embedding_service = None
        self._property_extractor = None
        self._qa_engine = None
        self._app_settings = None

        # Child widget references
        self._material_browser = None
        self._property_editor = None
        self._document_manager = None
        self._qa_chat = None
        self._xml_viewer = None
        self._export_page = None
        self._settings_page = None

        self._toolbox: Optional[_ToolboxNav] = None
        self._stack: Optional[QStackedWidget] = None
        self._page_headers: list[_PageHeader] = []

        self._setup_menubar()
        self._setup_toolbar()
        self._setup_central_area()
        self._setup_statusbar()
        self._connect_signals()
        self.apply_stylesheet()

    # ------------------------------------------------------------------
    # Central Area: Toolbox + Stacked Pages
    # ------------------------------------------------------------------

    def _setup_central_area(self) -> None:
        """Create left toolbox nav + right stacked widget."""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left toolbox
        self._toolbox = _ToolboxNav()
        layout.addWidget(self._toolbox)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: {_C['border']};")
        layout.addWidget(sep)

        # Right stacked pages
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {_C['bg_primary']};")
        layout.addWidget(self._stack)

        # Build pages
        self._build_pages()

        self._toolbox.page_changed.connect(self._on_page_changed)

    def _on_page_changed(self, index: int) -> None:
        """Refresh page data when switching tabs."""
        self._stack.setCurrentIndex(index)
        # Page 3 = Export page — refresh material list on switch
        if index == 3 and self._export_page is not None:
            self._export_page.refresh()

    def _build_pages(self) -> None:
        """Create all content pages."""
        self._build_materials_page()
        self._build_documents_page()
        # self._build_qa_page()  # removed
        self._build_xml_page()
        self._build_export_page()
        self._build_settings_page()

    def _wrap_page(self, content: QWidget, header_icon: str, header_title: str) -> QWidget:
        """Wrap content in a page with header."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        hdr = _PageHeader(header_icon, header_title)
        self._page_headers.append(hdr)
        layout.addWidget(hdr)
        layout.addWidget(content, 1)

        self._stack.addWidget(page)
        return page

    # --- Materials Page (index 0) ---

    def _build_materials_page(self) -> None:
        from ansys_material_db.gui.material_browser import MaterialBrowser
        from ansys_material_db.gui.property_editor import PropertyEditor

        content = QWidget()
        layout = QHBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(3)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {_C['border']}; }}")

        self._material_browser = MaterialBrowser()
        self._material_browser.setFeatures(
            self._material_browser.features()
            & ~self._material_browser.DockWidgetFeature.DockWidgetClosable
        )
        # Hide title bar when embedded
        empty_title = QWidget()
        self._material_browser.setTitleBarWidget(empty_title)
        splitter.addWidget(self._material_browser)

        self._property_editor = PropertyEditor()
        self._property_editor.setFeatures(
            self._property_editor.features()
            & ~self._property_editor.DockWidgetFeature.DockWidgetClosable
        )
        empty_title2 = QWidget()
        self._property_editor.setTitleBarWidget(empty_title2)
        self._property_editor.setMinimumWidth(300)
        splitter.addWidget(self._property_editor)

        splitter.setSizes([320, 700])
        layout.addWidget(splitter)

        self._wrap_page(content, "\U0001f4e6", t("nav.materials"))

    # --- Documents Page (index 1) ---

    def _build_documents_page(self) -> None:
        from ansys_material_db.gui.document_manager import DocumentManager

        self._document_manager = DocumentManager(self._database, self._knowledge_base)
        empty_title3 = QWidget()
        self._document_manager.setTitleBarWidget(empty_title3)
        self._wrap_page(self._document_manager, "\U0001f4c4", t("nav.documents"))

    # --- QA Page (index 2) ---

    # QA page removed

    # --- XML Page (index 3) ---

    def _build_xml_page(self) -> None:
        from ansys_material_db.gui.xml_viewer_page import XMLViewerPage

        self._xml_viewer = XMLViewerPage()
        self._wrap_page(self._xml_viewer, "\U0001f4cb", t("nav.xml"))

    # --- Export Page (index 4) ---

    def _build_export_page(self) -> None:
        from ansys_material_db.gui.export_page import ExportPage

        self._export_page = ExportPage()
        self._wrap_page(self._export_page, "\U0001f4e4", t("nav.export"))

    # --- Settings Page (index 5) ---

    def _build_settings_page(self) -> None:
        from ansys_material_db.gui.settings_page import SettingsPage

        self._settings_page = SettingsPage()
        self._wrap_page(self._settings_page, "\u2699\ufe0f", t("nav.settings"))

    # ------------------------------------------------------------------
    # Backend Initialization
    # ------------------------------------------------------------------

    def init_backend(
        self,
        database,
        knowledge_base,
        llm_client,
        embedding_service,
        property_extractor,
        qa_engine,
        app_settings,
    ) -> None:
        """Wire up backend components after construction."""
        self._database = database
        self._knowledge_base = knowledge_base
        self._llm_client = llm_client
        self._embedding_service = embedding_service
        self._property_extractor = property_extractor
        # self._qa_engine = qa_engine
        self._app_settings = app_settings

        init_translator(self._database)
        self._refresh_ui_text()

        # Wire document manager
        if self._document_manager is not None:
            self._document_manager.set_llm_client(self._llm_client)
            self._document_manager.set_knowledge_base(self._knowledge_base)
            self._document_manager.set_database(self._database)
            self._document_manager.extraction_completed.connect(self._refresh_materials)
            # Use knowledge_base's database if available, else main database
            self._document_manager._database = self._database
            self._document_manager._knowledge_base = self._knowledge_base
            self._document_manager.refresh_documents()

        # Wire embedding service
        if self._embedding_service is not None:
            self._embedding_service.set_llm_client(self._llm_client)

        # Wire export page
        if self._export_page is not None:
            self._export_page.set_database(self._database)

        # Wire settings page
        if self._settings_page is not None:
            self._settings_page.set_app_settings(self._app_settings)
            self._settings_page.settings_saved.connect(self._on_settings_saved)

        # Connect MaterialBrowser signals
        if self._material_browser is not None:
            self._material_browser.material_selected.connect(self._on_material_clicked)
            self._material_browser.material_double_clicked.connect(self._on_material_double_clicked)
            self._material_browser.materials_deleted.connect(self._on_materials_deleted)
            self._material_browser.material_edit_requested.connect(self._on_material_clicked)
            self._material_browser.material_delete_requested.connect(
                self._on_material_delete_single
            )
            self._material_browser.material_export_requested.connect(
                self._on_material_export_single
            )
            self._material_browser.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        # Delete key shortcut for material browser
        from PyQt6.QtGui import QKeySequence
        from PyQt6.QtGui import QShortcut

        delete_shortcut = QShortcut(QKeySequence.StandardKey.Delete, self)
        delete_shortcut.activated.connect(self._on_delete_selected)

        # Connect PropertyEditor save
        if self._property_editor is not None:
            self._property_editor.material_saved.connect(self._on_material_saved)

        # QAChat removed

        self._refresh_materials()
        self._update_status_bar()

    # ------------------------------------------------------------------
    # Menu Bar
    # ------------------------------------------------------------------

    def _setup_menubar(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu(t("menu.file"))

        self._action_import = QAction(t("menu.import_documents"), self)
        self._action_import.setShortcut("Ctrl+I")
        file_menu.addAction(self._action_import)

        self._action_export = QAction(t("menu.export_xml"), self)
        self._action_export.setShortcut("Ctrl+E")
        file_menu.addAction(self._action_export)

        self._action_import_xml = QAction(t("menu.import_xml"), self)
        self._action_import_xml.setShortcut("Ctrl+Shift+I")
        file_menu.addAction(self._action_import_xml)

        file_menu.addSeparator()

        self._action_exit = QAction(t("menu.exit"), self)
        self._action_exit.setShortcut("Ctrl+Q")
        self._action_exit.triggered.connect(self.close)
        file_menu.addAction(self._action_exit)

        tools_menu = menubar.addMenu(t("menu.tools"))
        self._action_settings = QAction(t("menu.settings"), self)
        tools_menu.addAction(self._action_settings)

        self._action_extract = QAction(t("menu.extract"), self)
        tools_menu.addAction(self._action_extract)

        help_menu = menubar.addMenu(t("menu.help"))
        self._action_about = QAction(t("menu.about"), self)
        help_menu.addAction(self._action_about)

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar(t("toolbar.main"), self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self._btn_import = QAction(t("toolbar.import"), self)
        self._btn_import.setToolTip(t("toolbar.import_tip"))
        toolbar.addAction(self._btn_import)

        self._btn_export = QAction(t("toolbar.export"), self)
        self._btn_export.setToolTip(t("toolbar.export_tip"))
        toolbar.addAction(self._btn_export)

        self._btn_import_xml = QAction(t("toolbar.import_xml"), self)
        self._btn_import_xml.setToolTip(t("toolbar.import_xml_tip"))
        toolbar.addAction(self._btn_import_xml)

        toolbar.addSeparator()

        self._btn_settings = QAction(t("toolbar.settings"), self)
        self._btn_settings.setToolTip(t("toolbar.settings_tip"))
        toolbar.addAction(self._btn_settings)

        self._btn_extract = QAction(t("toolbar.extract"), self)
        self._btn_extract.setToolTip(t("toolbar.extract_tip"))
        toolbar.addAction(self._btn_extract)

    # ------------------------------------------------------------------
    # Status Bar
    # ------------------------------------------------------------------

    def _setup_statusbar(self) -> None:
        statusbar = self.statusBar()
        self._material_count_label = QLabel(t("status.materials", count=0))
        statusbar.addPermanentWidget(self._material_count_label)

        self._llm_status_label = QLabel(t("status.llm_not_configured"))
        statusbar.addPermanentWidget(self._llm_status_label)

    # ------------------------------------------------------------------
    # Signal connections
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._action_import.triggered.connect(self.on_import_documents)
        self._action_export.triggered.connect(self.on_export_xml)
        self._action_import_xml.triggered.connect(self.on_import_xml)
        self._action_settings.triggered.connect(self.on_open_settings)
        self._action_extract.triggered.connect(self.on_extract_all)
        self._action_about.triggered.connect(self.on_about)

        self._btn_import.triggered.connect(self.on_import_documents)
        self._btn_export.triggered.connect(self.on_export_xml)
        self._btn_import_xml.triggered.connect(self.on_import_xml)
        self._btn_settings.triggered.connect(self.on_open_settings)
        self._btn_extract.triggered.connect(self.on_extract_all)

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    def on_import_documents(self) -> None:
        """Open the import wizard."""
        from ansys_material_db.gui.import_wizard import ImportWizard

        wizard = ImportWizard(self._knowledge_base, self)
        wizard.import_completed.connect(self._on_import_completed)
        wizard.exec()

    def _on_import_completed(self, doc_ids: list) -> None:
        if self._document_manager:
            self._document_manager.refresh_documents()
        self._stack.setCurrentIndex(1)
        logger.info("Import completed: %d documents", len(doc_ids))

    def on_export_xml(self) -> None:
        """Switch to export page and refresh."""
        self._stack.setCurrentIndex(3)
        if self._export_page:
            self._export_page.refresh()

    def on_import_xml(self) -> None:
        """Open XML viewer dialog as a separate window."""
        from ansys_material_db.gui.xml_import_dialog import XMLImportDialog

        dialog = XMLImportDialog(self)
        dialog.show()

    def on_open_settings(self) -> None:
        """Switch to settings page."""
        self._stack.setCurrentIndex(4)

    def on_extract_all(self) -> None:
        """Trigger extract on all unprocessed documents."""
        if self._document_manager:
            self._stack.setCurrentIndex(1)
            docs = self._database.list_documents() if self._database else []
            for doc in docs:
                if doc.status not in ("vectorized", "completed"):
                    self._document_manager._on_extract(doc.id)

    def on_about(self) -> None:
        QMessageBox.about(
            self,
            t("about.title"),
            t("about.text", version="1.0.0"),
        )

    def on_material_selected(self, material_id: int) -> None:
        """Handle material selection from browser."""
        self._stack.setCurrentIndex(0)
        if self._property_editor and self._database:
            mat = self._database.get_material(material_id)
            if mat:
                self._property_editor.load_material(mat)

    def _on_settings_saved(self) -> None:
        """Handle settings saved."""
        init_translator(self._database)
        self._refresh_ui_text()
        self._refresh_ui_text()

        if self._app_settings:
            from ansys_material_db.data.llm_client import LLMClient
            from ansys_material_db.core.property_extractor import PropertyExtractor

            llm_config = self._app_settings.get_llm_config()
            if llm_config.get("base_url") and llm_config.get("api_key"):
                self._llm_client = LLMClient(
                    base_url=llm_config["base_url"],
                    api_key=llm_config["api_key"],
                    model=llm_config.get("model", "gpt-4o"),
                    temperature=llm_config.get("temperature", 0.3),
                    max_tokens=llm_config.get("max_tokens", 4096),
                )
                self._property_extractor = PropertyExtractor(self._llm_client)
            else:
                self._llm_client = None
                self._property_extractor = None

            if self._document_manager:
                self._document_manager.set_llm_client(self._llm_client)

        self._update_status_bar()

    # ------------------------------------------------------------------
    # Material Browser handlers
    # ------------------------------------------------------------------

    def _on_material_clicked(self, material_id: int) -> None:
        """Show material properties when clicked in browser."""
        if self._property_editor is not None and self._database is not None:
            mat = self._database.get_material(material_id)
            if mat:
                self._property_editor.load_material(mat)
                # Switch to materials page
                self._stack.setCurrentIndex(0)

    def _on_material_double_clicked(self, material_id: int) -> None:
        """Double-click: show material and switch to QA page with context."""
        self._on_material_clicked(material_id)
        if self._qa_chat is not None and self._database is not None:
            mat = self._database.get_material(material_id)
            if mat:
                self._qa_chat.load_material(mat)

    def _on_materials_deleted(self, material_ids: list) -> None:
        """Delete materials from database."""
        if self._database is None:
            return
        for mid in material_ids:
            self._database.delete_material(mid)
        self._refresh_materials()

    def _on_material_saved(self, material) -> None:
        """Save edited material to database."""
        if self._database is None:
            return
        self._database.save_material(material)
        self._refresh_materials()

    def _on_delete_selected(self) -> None:
        """Handle Delete key: batch delete selected materials."""
        if self._material_browser is None or self._database is None:
            return
        self._material_browser.delete_selected()

    def _on_material_delete_single(self, material_id: int) -> None:
        if self._database is None:
            return
        mat = self._database.get_material(material_id)
        name = mat.name if mat else str(material_id)
        reply = QMessageBox.question(
            self,
            t("browser.delete"),
            t("docmgr.confirm_delete", name=name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._database.delete_material(material_id)
            self._refresh_materials()

    def _on_material_export_single(self, material_id: int) -> None:
        if self._database is None:
            return
        mat = self._database.get_material(material_id)
        if mat is None:
            return
        from ansys_material_db.core.xml_generator import XMLGenerator
        from PyQt6.QtWidgets import QFileDialog
        from pathlib import Path

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            t("export.export_btn"),
            str(Path.home() / f"{mat.name.replace(' ', '_')}.xml"),
            "XML (*.xml)",
        )
        if file_path:
            gen = XMLGenerator()
            gen.generate_file([mat], file_path)
            self._stack.setCurrentIndex(4)
            if self._export_page:
                self._export_page.refresh()

    # ------------------------------------------------------------------
    # QA Chat handler
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _refresh_ui_text(self) -> None:
        """Refresh all user-visible text for current language."""
        self.setWindowTitle(t("app.title"))

        if self._toolbox:
            self._toolbox.refresh_labels()

        # Menu bar
        menubar = self.menuBar()
        actions = menubar.actions()
        for i, key in enumerate(["menu.file", "menu.tools", "menu.help"]):
            if i < len(actions):
                actions[i].setText(t(key))

        self._action_import.setText(t("menu.import_documents"))
        self._action_export.setText(t("menu.export_xml"))
        self._action_exit.setText(t("menu.exit"))
        self._action_import_xml.setText(t("menu.import_xml"))
        self._action_settings.setText(t("menu.settings"))
        self._action_extract.setText(t("menu.extract"))
        self._action_about.setText(t("menu.about"))

        self._btn_import.setText(t("toolbar.import"))
        self._btn_import.setToolTip(t("toolbar.import_tip"))
        self._btn_export.setText(t("toolbar.export"))
        self._btn_export.setToolTip(t("toolbar.export_tip"))
        self._btn_import_xml.setText(t("toolbar.import_xml"))
        self._btn_import_xml.setToolTip(t("toolbar.import_xml_tip"))
        self._btn_settings.setText(t("toolbar.settings"))
        self._btn_settings.setToolTip(t("toolbar.settings_tip"))
        self._btn_extract.setText(t("toolbar.extract"))
        self._btn_extract.setToolTip(t("toolbar.extract_tip"))

    def _refresh_materials(self) -> None:
        if self._database is None or self._material_browser is None:
            return
        materials = self._database.list_materials()
        self._material_browser.load_materials(materials)
        self._material_count_label.setText(t("status.materials", count=len(materials)))

    def _update_status_bar(self) -> None:
        if self._app_settings:
            config = self._app_settings.get_llm_config()
            if config.get("base_url") and config.get("api_key"):
                self._llm_status_label.setText(
                    f"LLM: {config.get('model', 'unknown')} @ {config.get('base_url', '')[:30]}"
                )
            else:
                self._llm_status_label.setText(t("status.llm_not_configured"))

    def apply_stylesheet(self) -> None:
        self.setStyleSheet(get_ansys_stylesheet())
