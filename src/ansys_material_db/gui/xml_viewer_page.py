"""Inline XML viewer page for the main window."""

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


class XMLViewerPage(QWidget):
    """Inline page for viewing materials from an Ansys 2021 R1 XML file."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._xml_generator = XMLGenerator()
        self._materials: list[Material] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Top bar
        top_bar = QHBoxLayout()
        self._file_label = QLabel(t("xml_import.file") + " --")
        self._file_label.setStyleSheet(f"color: {_C['text_secondary']}; font-size: 12px;")
        top_bar.addWidget(self._file_label)
        top_bar.addStretch()

        self._stats_label = QLabel("")
        self._stats_label.setStyleSheet(f"color: {_C['text_secondary']}; font-size: 12px;")
        top_bar.addWidget(self._stats_label)

        btn_open = QPushButton(t("xml_import.open_file"))
        btn_open.setFixedHeight(28)
        btn_open.clicked.connect(self._open_file_dialog)
        top_bar.addWidget(btn_open)
        layout.addLayout(top_bar)

        # Splitter: material list | property table
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_w = QWidget()
        left_l = QVBoxLayout(left_w)
        left_l.setContentsMargins(8, 0, 8, 0)
        left_lbl = QLabel(t("xml_import.materials"))
        left_lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
        left_l.addWidget(left_lbl)

        self._material_list = QListWidget()
        self._material_list.currentRowChanged.connect(self._on_material_selected)
        left_l.addWidget(self._material_list)
        splitter.addWidget(left_w)

        right_w = QWidget()
        right_l = QVBoxLayout(right_w)
        right_l.setContentsMargins(0, 0, 8, 0)
        self._detail_label = QLabel(t("xml_import.detail"))
        self._detail_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        right_l.addWidget(self._detail_label)

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
        right_l.addWidget(self._property_table)
        splitter.addWidget(right_w)

        splitter.setSizes([300, 600])
        layout.addWidget(splitter, 1)

    def _open_file_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t("xml_import.open_file"),
            "",
            "XML (*.xml);;" + t("xml_import.all_files"),
        )
        if file_path:
            self._load_xml(file_path)

    def _load_xml(self, path: str) -> None:
        try:
            self._materials = self._xml_generator.parse_ansys_xml(path)
        except Exception as exc:
            logger.exception("Failed to parse XML: %s", path)
            QMessageBox.warning(
                self, t("xml_import.title"), t("xml_import.parse_error", error=str(exc))
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

    def _on_material_selected(self, row: int) -> None:
        self._property_table.setRowCount(0)
        if row < 0 or row >= len(self._materials):
            return

        mat = self._materials[row]
        self._detail_label.setText(mat.name + "  -  " + t("xml_import.detail"))

        props = mat.properties
        if not props:
            # Show all possible ANSYS properties even if empty
            prop_names = [
                ("Density", "pr1"),
                ("Thermal Conductivity", "pr0"),
                ("Specific Heat", "pr2"),
                ("Thermal Expansion", "pr6"),
                ("Poisson Ratio", "pr7"),
                ("Elastic Modulus", ""),
                ("Yield Strength", ""),
                ("Tensile Strength", ""),
                ("Relative Permeability", "pr5"),
            ]
            self._property_table.setRowCount(len(prop_names))
            for i, (name, _pid) in enumerate(prop_names):
                self._property_table.setItem(i, 0, QTableWidgetItem(name))
                self._property_table.setItem(i, 1, QTableWidgetItem("-"))
                self._property_table.setItem(i, 2, QTableWidgetItem("-"))
            self._property_table.resizeColumnsToContents()
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
            self._property_table.setItem(i, 1, QTableWidgetItem(val_text))

            self._property_table.setItem(i, 2, QTableWidgetItem(prop.unit or "-"))

        self._property_table.resizeColumnsToContents()
