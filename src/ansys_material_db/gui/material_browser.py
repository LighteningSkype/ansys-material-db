"""MaterialBrowser — dockable panel for browsing the material library."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QSortFilterProxyModel, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from ansys_material_db.gui.styles import ANSYS_COLORS
from ansys_material_db.i18n import t as _t
from ansys_material_db.models.material import Material

_CATEGORIES = ["Metal", "Polymer", "Ceramic", "Composite", "Other"]
_ROLE_MATERIAL_ID = Qt.ItemDataRole.UserRole + 1


class MaterialBrowser(QDockWidget):
    """Dockable material library browser with tree view, search, and filters."""

    material_selected = pyqtSignal(int)  # material id
    material_double_clicked = pyqtSignal(int)  # material id
    materials_deleted = pyqtSignal(list)  # list of material ids to delete
    material_edit_requested = pyqtSignal(int)  # edit material
    material_delete_requested = pyqtSignal(int)  # delete single material
    material_export_requested = pyqtSignal(int)  # export single material

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(_t("panel.browser"), parent)
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self._materials: list[Material] = []
        self._init_ui()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(_t("browser.search_placeholder"))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search_input)

        # Supplier filter
        filter_row = QHBoxLayout()
        filter_label = QLabel(_t("browser.supplier") + ":")
        filter_label.setStyleSheet(f"color: {ANSYS_COLORS['text_secondary']};")
        filter_row.addWidget(filter_label)

        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem(_t("browser.all_suppliers"))
        self.supplier_combo.currentTextChanged.connect(self._apply_filter)
        filter_row.addWidget(self.supplier_combo)

        self.btn_find_dupes = QPushButton(_t("browser.find_duplicates"))
        self.btn_find_dupes.setFixedHeight(28)
        self.btn_find_dupes.clicked.connect(self._find_duplicates)
        filter_row.addWidget(self.btn_find_dupes)

        layout.addLayout(filter_row)

        # Tree view
        self.tree = QTreeView()
        self.tree.setHeaderHidden(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setExpandsOnDoubleClick(True)
        self.tree.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.doubleClicked.connect(self._on_double_clicked)
        self.tree.clicked.connect(self._on_clicked)

        # Model + proxy
        self._source_model = QStandardItemModel()
        self._proxy_model = QSortFilterProxyModel()
        self._proxy_model.setSourceModel(self._source_model)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy_model.setFilterKeyColumn(-1)  # search all columns
        self.tree.setModel(self._proxy_model)

        layout.addWidget(self.tree)
        self.setWidget(container)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_materials(self, materials: list[Material]) -> None:
        """Populate the tree from a list of :class:`Material` objects."""
        self._materials = materials
        self._source_model.clear()
        self._rebuild_supplier_list()

        # Group by category
        groups: dict[str, list[Material]] = {cat: [] for cat in _CATEGORIES}
        for m in materials:
            cat = m.category if m.category in _CATEGORIES else "Other"
            groups[cat].append(m)

        for cat in _CATEGORIES:
            items = groups[cat]
            if not items:
                continue
            cat_item = QStandardItem(cat)
            cat_item.setSelectable(False)
            cat_item.setForeground(QColor(ANSYS_COLORS["accent_light"]))
            bold_font = cat_item.font()
            bold_font.setBold(True)
            cat_item.setFont(bold_font)

            for m in sorted(items, key=lambda x: x.name.lower()):
                child = QStandardItem(m.name)
                detail = f"{m.supplier}" if m.supplier else ""
                if m.product_name:
                    detail = f"{detail} — {m.product_name}" if detail else m.product_name
                if detail:
                    child.setToolTip(detail)
                child.setData(m.id, _ROLE_MATERIAL_ID)
                cat_item.appendRow(child)

            self._source_model.appendRow(cat_item)

        self.tree.expandAll()

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def _rebuild_supplier_list(self) -> None:
        suppliers = sorted({m.supplier for m in self._materials if m.supplier})
        current = self.supplier_combo.currentText()
        self.supplier_combo.blockSignals(True)
        self.supplier_combo.clear()
        self.supplier_combo.addItem(_t("browser.all_suppliers"))
        self.supplier_combo.addItems(suppliers)
        idx = self.supplier_combo.findText(current)
        if idx >= 0:
            self.supplier_combo.setCurrentIndex(idx)
        self.supplier_combo.blockSignals(False)

    def _apply_filter(self, *_args: object) -> None:
        text = self.search_input.text().strip()
        supplier = self.supplier_combo.currentText()

        # If supplier filter is active, do client-side filtering on the model
        # because the proxy model only filters text.  We rebuild when supplier changes.
        self._source_model.clear()
        groups: dict[str, list[Material]] = {cat: [] for cat in _CATEGORIES}
        for m in self._materials:
            if supplier != _t("browser.all_suppliers") and m.supplier != supplier:
                continue
            cat = m.category if m.category in _CATEGORIES else "Other"
            groups[cat].append(m)

        for cat in _CATEGORIES:
            items = groups[cat]
            if not items:
                continue
            cat_item = QStandardItem(cat)
            cat_item.setSelectable(False)
            cat_item.setForeground(QColor(ANSYS_COLORS["accent_light"]))
            bold_font = cat_item.font()
            bold_font.setBold(True)
            cat_item.setFont(bold_font)
            for m in sorted(items, key=lambda x: x.name.lower()):
                child = QStandardItem(m.name)
                child.setData(m.id, _ROLE_MATERIAL_ID)
                cat_item.appendRow(child)
            self._source_model.appendRow(cat_item)

        self.tree.expandAll()

        # Apply text search through proxy
        self._proxy_model.setFilterFixedString(text)

    # ------------------------------------------------------------------
    # Duplicate detection
    # ------------------------------------------------------------------

    def _find_duplicates(self) -> None:
        """Find materials with duplicate names and offer to delete them."""
        name_map: dict[str, list[int]] = {}
        for m in self._materials:
            key = m.name.strip().lower()
            if key not in name_map:
                name_map[key] = []
            if m.id is not None:
                name_map[key].append(m.id)

        dupes = {k: ids for k, ids in name_map.items() if len(ids) > 1}
        if not dupes:
            QMessageBox.information(
                self,
                _t("browser.find_duplicates"),
                _t("browser.no_duplicates"),
            )
            return

        total = sum(len(ids) - 1 for ids in dupes.values())
        msg = _t("browser.dupes_found", count=total) + "\n\n"
        for name, ids in sorted(dupes.items()):
            msg += f"- {name} ({len(ids)} copies)\n"
        msg += "\n" + _t("browser.confirm_delete_dupes")

        reply = QMessageBox.question(
            self,
            _t("browser.find_duplicates"),
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Keep the first occurrence, delete the rest
        ids_to_delete = []
        for name, ids in dupes.items():
            ids_to_delete.extend(ids[1:])  # keep first, delete rest

        self.materials_deleted.emit(ids_to_delete)

    # ------------------------------------------------------------------
    # Selection & context menu
    # ------------------------------------------------------------------

    def _on_clicked(self, index) -> None:  # noqa: ANN001
        mid = self._proxy_model.data(index, _ROLE_MATERIAL_ID)
        if mid is not None:
            self.material_selected.emit(int(mid))

    def _on_double_clicked(self, index) -> None:  # noqa: ANN001
        mid = self._proxy_model.data(index, _ROLE_MATERIAL_ID)
        if mid is not None:
            self.material_double_clicked.emit(int(mid))

    def _show_context_menu(self, pos) -> None:  # noqa: ANN001
        index = self.tree.indexAt(pos)
        mid = self._proxy_model.data(index, _ROLE_MATERIAL_ID)
        if mid is None:
            return

        menu = QMenu(self)
        edit_action = QAction(_t("browser.edit"), self)
        delete_action = QAction(_t("browser.delete"), self)
        export_action = QAction(_t("browser.export_xml"), self)
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.addSeparator()
        menu.addAction(export_action)

        # Connect actions (separate signals for each)
        edit_action.triggered.connect(lambda: self.material_edit_requested.emit(int(mid)))
        delete_action.triggered.connect(lambda: self.material_delete_requested.emit(int(mid)))
        export_action.triggered.connect(lambda: self.material_export_requested.emit(int(mid)))

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def get_selected_ids(self) -> list[int]:
        """Return list of material IDs for all selected items."""
        ids = []
        for index in self.tree.selectedIndexes():
            mid = self._proxy_model.data(index, _ROLE_MATERIAL_ID)
            if mid is not None:
                ids.append(int(mid))
        return ids

    def delete_selected(self) -> None:
        """Delete all selected materials with confirmation."""
        ids = self.get_selected_ids()
        if not ids:
            return
        reply = QMessageBox.question(
            self,
            _t("browser.delete"),
            _t("browser.delete_selected", count=len(ids)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.materials_deleted.emit(ids)
