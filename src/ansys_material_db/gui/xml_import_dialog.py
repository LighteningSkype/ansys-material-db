"""XML Material Library viewer dialog for Ansys Engineering Data XML files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ansys_material_db.core.xml_generator import XMLGenerator
from ansys_material_db.gui.styles import ANSYS_COLORS
from ansys_material_db.i18n import t
from ansys_material_db.models.material import Material

logger = logging.getLogger(__name__)

_C = ANSYS_COLORS


class XMLImportDialog(QMainWindow):
    """Dialog for viewing materials from an Ansys 2021 R1 XML file.

    Left panel: material list.  Right panel: property detail table.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._xml_generator = XMLGenerator()
        self._materials: list[Material] = []

        self.setWindowTitle(t("xml_import.title"))
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)

        central = QWidget()
        self.setCentralWidget(central)
        self._setup_ui(central)
        self._apply_styles()
        self._open_file_dialog()

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------

    def _setup_ui(self, container: QWidget) -> None:
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # -- Top bar: file info + open button --
        top_bar = QHBoxLayout()
        self._file_label = QLabel(t("xml_import.file") + " --")
        self._file_label.setStyleSheet(f"color: {_C['text_secondary']}; font-size: 12px;")
        top_bar.addWidget(self._file_label)

        top_bar.addStretch()

        self._stats_label = QLabel()
        self._stats_label.setStyleSheet(f"color: {_C['text_secondary']}; font-size: 12px;")
        top_bar.addWidget(self._stats_label)

        self._btn_open = QPushButton(t("xml_import.open_file"))
        self._btn_open.setFixedHeight(28)
        self._btn_open.clicked.connect(self._open_file_dialog)
        top_bar.addWidget(self._btn_open)

        layout.addLayout(top_bar)

        # -- Main splitter: material list (left) + property table (right) --
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: material list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_label = QLabel(t("xml_import.materials"))
        left_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        left_layout.addWidget(left_label)

        self._material_list = QListWidget()
        self._material_list.currentRowChanged.connect(self._on_material_selected)
        left_layout.addWidget(self._material_list)
        splitter.addWidget(left_widget)

        # Right panel: property detail table
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self._detail_label = QLabel(t("xml_import.detail"))
        self._detail_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        right_layout.addWidget(self._detail_label)

        self._property_table = QTableWidget()
        self._property_table.setColumnCount(3)
        self._property_table.setHorizontalHeaderLabels(
            [t("xml_import.prop_name"), t("xml_import.value"), t("xml_import.unit")]
        )
        self._property_table.horizontalHeader().setStretchLastSection(True)
        self._property_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._property_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._property_table.setAlternatingRowColors(True)
        self._property_table.verticalHeader().setVisible(False)
        right_layout.addWidget(self._property_table)
        splitter.addWidget(right_widget)

        splitter.setSizes([300, 600])
        layout.addWidget(splitter)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            f"QWidget {{ background-color: {_C['bg_primary']}; color: {_C['text_primary']}; }}"
            f" QListWidget {{ background-color: {_C['bg_secondary']}; border: 1px solid {_C['border']};"
            f" border-radius: 3px; padding: 4px; }}"
            f" QListWidget::item:selected {{ background-color: {_C['accent_blue']}; color: white; }}"
            f" QListWidget::item:hover {{ background-color: {_C['bg_tertiary']}; }}"
            f" QTableWidget {{ background-color: {_C['bg_secondary']}; gridline-color: {_C['border']}; }}"
            f" QTableWidget::item:selected {{ background-color: {_C['accent_blue']}; color: white; }}"
            f" QHeaderView::section {{ background-color: {_C['bg_tertiary']}; color: {_C['text_primary']};"
            f" padding: 4px 8px; border: 1px solid {_C['border']}; font-weight: bold; }}"
            f" QPushButton {{ background-color: {_C['bg_tertiary']}; color: {_C['text_primary']};"
            f" border: 1px solid {_C['border']}; border-radius: 3px; padding: 6px 16px; }}"
            f" QPushButton:hover {{ background-color: {_C['accent_blue']}; color: white; }}"
        )

    # ------------------------------------------------------------------
    # File loading
    # ------------------------------------------------------------------

    def _open_file_dialog(self) -> None:
        """Open a file dialog and load the selected XML."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t("xml_import.open_file"),
            "",
            "XML (*.xml);;" + t("xml_import.all_files"),
        )
        if not file_path:
            return
        self._load_xml(file_path)

    def _load_xml(self, path: str) -> None:
        """Parse the XML file and populate the material list."""
        try:
            self._materials = self._xml_generator.parse_ansys_xml(path)
        except Exception as exc:
            logger.exception("Failed to parse XML: %s", path)
            QMessageBox.warning(
                self,
                t("xml_import.title"),
                t("xml_import.parse_error", error=str(exc)),
            )
            return

        self._file_label.setText(t("xml_import.file") + " " + str(Path(path).name))
        self._stats_label.setText(t("xml_import.materials_found", count=len(self._materials)))
        self._material_list.clear()
        self._property_table.setRowCount(0)

        for mat in self._materials:
            label = mat.name
            if mat.category:
                label += f"  [{mat.category}]"
            self._material_list.addItem(QListWidgetItem(label))

        if self._materials:
            self._material_list.setCurrentRow(0)

    # ------------------------------------------------------------------
    # Material selection
    # ------------------------------------------------------------------

    def _on_material_selected(self, row: int) -> None:
        """Display properties of the selected material."""
        self._property_table.setRowCount(0)
        if row < 0 or row >= len(self._materials):
            return

        mat = self._materials[row]
        self._detail_label.setText(mat.name + "  -  " + t("xml_import.detail"))

        props = mat.properties
        if not props:
            return

        self._property_table.setRowCount(len(props))
        for i, prop in enumerate(props):
            name_item = QTableWidgetItem(prop.display_name or prop.name)
            self._property_table.setItem(i, 0, name_item)

            if prop.value is not None:
                val_text = f"{prop.value:g}" if isinstance(prop.value, float) else str(prop.value)
            elif prop.temperature_table:
                val_text = f"[{len(prop.temperature_table)} points]"
            else:
                val_text = "-"
            val_item = QTableWidgetItem(val_text)
            self._property_table.setItem(i, 1, val_item)

            unit_item = QTableWidgetItem(prop.unit or "-")
            self._property_table.setItem(i, 2, unit_item)

        self._property_table.resizeColumnsToContents()
