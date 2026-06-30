"""Inline export page for the main window."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from ansys_material_db.core.xml_generator import XMLGenerator
from ansys_material_db.gui.styles import ANSYS_COLORS
from ansys_material_db.i18n import t
from ansys_material_db.models.material import Material

logger = logging.getLogger(__name__)
_C = ANSYS_COLORS


class ExportPage(QWidget):
    """Inline page for exporting materials to Ansys Engineering Data XML."""

    export_completed = pyqtSignal(list)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._database = None
        self._materials: list[Material] = []
        self._xml_generator = XMLGenerator()
        self._checkboxes: dict[int, QCheckBox] = {}
        self._setup_ui()

    def set_database(self, db) -> None:
        self._database = db
        self.refresh()

    def refresh(self) -> None:
        if self._database is None:
            return
        self._materials = self._database.list_materials()
        self._populate_materials()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Options row
        opts_row = QHBoxLayout()
        opts_lbl = QLabel(t("export.options") + ":")
        opts_lbl.setStyleSheet("font-weight: bold;")
        opts_row.addWidget(opts_lbl)

        self._radio_single = QRadioButton(t("export.single_file"))
        self._radio_single.setChecked(True)
        opts_row.addWidget(self._radio_single)

        self._radio_per_mat = QRadioButton(t("export.per_material"))
        opts_row.addWidget(self._radio_per_mat)
        opts_row.addStretch()

        self._btn_select_all = QPushButton(t("export.select_all"))
        self._btn_select_all.clicked.connect(lambda: self._toggle_all(True))
        opts_row.addWidget(self._btn_select_all)

        self._btn_deselect_all = QPushButton(t("export.deselect_all"))
        self._btn_deselect_all.clicked.connect(lambda: self._toggle_all(False))
        opts_row.addWidget(self._btn_deselect_all)
        layout.addLayout(opts_row)

        # Material table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            [
                "",
                t("export.mat_name"),
                t("export.density"),
                t("export.thermal_cond"),
                t("export.specific_heat"),
                t("export.status"),
            ]
        )
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 30)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table, 1)

        # Bottom: output + export button
        bottom = QHBoxLayout()
        bottom.addWidget(QLabel(t("export.output_dir") + ":"))
        self._dir_edit = QLineEdit()
        self._dir_edit.setPlaceholderText(t("export.select_dir"))
        bottom.addWidget(self._dir_edit)

        btn_browse = QPushButton(t("export.browse"))
        btn_browse.clicked.connect(self._on_browse_dir)
        bottom.addWidget(btn_browse)

        bottom.addWidget(QLabel(t("export.prefix") + ":"))
        self._prefix_edit = QLineEdit("ansys_materials")
        self._prefix_edit.setFixedWidth(150)
        bottom.addWidget(self._prefix_edit)

        self._btn_export = QPushButton(t("export.export_btn"))
        self._btn_export.setStyleSheet(
            f"QPushButton {{ background-color: {_C['accent_blue']}; color: white; "
            f"border: 1px solid {_C['accent_light']}; border-radius: 3px; padding: 8px 24px; }}"
            f"QPushButton:hover {{ background-color: {_C['accent_light']}; }}"
        )
        self._btn_export.clicked.connect(self._on_export)
        bottom.addWidget(self._btn_export)
        layout.addLayout(bottom)

        # Status
        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"color: {_C['text_secondary']}; font-size: 12px;")
        layout.addWidget(self._status_label)

    def _get_prop_value(self, mat: Material, prop_name: str) -> str:
        if not mat.properties:
            return "-"
        for p in mat.properties:
            if p.name == prop_name:
                if p.value is not None:
                    return f"{p.value:g}"
                return "-"
        return "-"

    def _get_status(self, mat: Material) -> str:
        has_all = True
        required = [
            "density",
            "thermal_conductivity",
            "specific_heat",
            "thermal_expansion",
            "poisson_ratio",
        ]
        if not mat.properties:
            return "missing"
        names = {p.name for p in mat.properties}
        for r in required:
            if r not in names:
                has_all = False
                break
        return "complete" if has_all else "partial"

    def _populate_materials(self) -> None:
        self._table.setRowCount(0)
        self._checkboxes.clear()

        for i, mat in enumerate(self._materials):
            self._table.insertRow(i)
            cb = QCheckBox()
            cb.setChecked(True)
            self._checkboxes[mat.id] = cb
            self._table.setCellWidget(i, 0, cb)

            self._table.setItem(i, 1, QTableWidgetItem(mat.name))
            self._table.setItem(i, 2, QTableWidgetItem(self._get_prop_value(mat, "density")))
            self._table.setItem(
                i, 3, QTableWidgetItem(self._get_prop_value(mat, "thermal_conductivity"))
            )
            self._table.setItem(i, 4, QTableWidgetItem(self._get_prop_value(mat, "specific_heat")))
            status = self._get_status(mat)
            status_item = QTableWidgetItem(t(f"export.{status}"))
            if status == "complete":
                status_item.setForeground(QColor(_C["success"]))
            else:
                status_item.setForeground(QColor(_C["warning"]))
            self._table.setItem(i, 5, status_item)

        self._status_label.setText(t("export.materials_count", count=len(self._materials)))

    def _toggle_all(self, checked: bool) -> None:
        for cb in self._checkboxes.values():
            cb.setChecked(checked)

    def _get_checked_materials(self) -> list[Material]:
        selected: list[Material] = []
        for mat in self._materials:
            cb = self._checkboxes.get(mat.id)
            if cb and cb.isChecked():
                selected.append(mat)
        return selected

    def _on_browse_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, t("export.select_dir"))
        if d:
            self._dir_edit.setText(d)

    def _on_export(self) -> None:
        selected = self._get_checked_materials()
        if not selected:
            QMessageBox.warning(self, t("export.export_btn"), t("export.no_materials"))
            return

        output_dir = self._dir_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(self, t("export.export_btn"), t("export.no_output_dir"))
            return

        prefix = self._prefix_edit.text().strip() or "ansys_materials"
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        exported: list[str] = []
        try:
            if self._radio_single.isChecked():
                file_path = output_path / f"{prefix}.xml"
                self._xml_generator.generate_file(selected, str(file_path))
                exported.append(str(file_path.resolve()))
            else:
                for mat in selected:
                    safe_name = mat.name.replace(" ", "_").replace("/", "_")
                    file_path = output_path / f"{prefix}_{safe_name}.xml"
                    self._xml_generator.generate_file([mat], str(file_path))
                    exported.append(str(file_path.resolve()))

            self._status_label.setText(t("export.success", count=len(exported)))
            self._status_label.setStyleSheet(
                f"color: {_C['success']}; font-size: 12px; font-weight: bold;"
            )
            self.export_completed.emit(exported)
        except Exception as exc:
            logger.exception("Export failed")
            self._status_label.setText(t("export.failed", error=str(exc)))
            self._status_label.setStyleSheet(
                f"color: {_C['error']}; font-size: 12px; font-weight: bold;"
            )
