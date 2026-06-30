"""XML export dialog with material selection, preview, and validation."""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QDialog,
    QWidget,
)

from ansys_material_db.gui.styles import ANSYS_COLORS
from ansys_material_db.models.material import Material

_C = ANSYS_COLORS

logger = logging.getLogger(__name__)


class ExportDialog(QDialog):
    """Dialog for exporting materials to Ansys Engineering Data XML.

    Provides material selection, XML preview, validation feedback,
    and export configuration.

    Signals
    -------
    export_completed(list[str])
        Emitted with the list of exported file paths when the export
        finishes successfully.
    """

    export_completed = pyqtSignal(list)

    def __init__(
        self,
        materials: list[Material] | None = None,
        xml_generator=None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Export Materials to XML")
        self.setMinimumSize(720, 580)

        self._materials = materials or []
        self._xml_generator = xml_generator
        self._exported_paths: list[str] = []

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        self._populate_materials()
        self._update_preview()

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # Top area: material selection + export options (side by side)
        top_layout = QHBoxLayout()

        # -- Material selection (left) --
        left_panel = QVBoxLayout()
        left_panel.setSpacing(6)

        sel_label = QLabel("Select Materials to Export:")
        sel_label.setStyleSheet("font-weight: bold;")
        left_panel.addWidget(sel_label)

        self.material_list = QListWidget()
        self.material_list.setSelectionMode(
            QListWidget.SelectionMode.NoSelection
        )
        left_panel.addWidget(self.material_list)

        sel_btn_row = QHBoxLayout()
        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.clicked.connect(self._on_select_all)
        sel_btn_row.addWidget(self.btn_select_all)

        self.btn_deselect_all = QPushButton("Deselect All")
        self.btn_deselect_all.clicked.connect(self._on_deselect_all)
        sel_btn_row.addWidget(self.btn_deselect_all)

        sel_btn_row.addStretch()
        left_panel.addLayout(sel_btn_row)

        top_layout.addLayout(left_panel, 1)

        # -- Export options (right) --
        right_panel = QVBoxLayout()
        right_panel.setSpacing(8)

        opt_label = QLabel("Export Options:")
        opt_label.setStyleSheet("font-weight: bold;")
        right_panel.addWidget(opt_label)

        # Radio: single file vs per-material
        self.radio_single = QRadioButton("Single XML file")
        self.radio_single.setChecked(True)
        right_panel.addWidget(self.radio_single)

        self.radio_per_material = QRadioButton("One file per material")
        right_panel.addWidget(self.radio_per_material)

        # Output directory
        dir_label = QLabel("Output Directory:")
        right_panel.addWidget(dir_label)

        dir_row = QHBoxLayout()
        self.dir_edit = QLineEdit()
        self.dir_edit.setPlaceholderText("Select output directory...")
        dir_row.addWidget(self.dir_edit)

        self.btn_browse_dir = QPushButton("Browse...")
        self.btn_browse_dir.clicked.connect(self._on_browse_directory)
        dir_row.addWidget(self.btn_browse_dir)
        right_panel.addLayout(dir_row)

        # Filename prefix
        prefix_label = QLabel("Filename Prefix:")
        right_panel.addWidget(prefix_label)
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText("e.g. ansys_materials")
        right_panel.addWidget(self.prefix_edit)

        right_panel.addStretch()
        top_layout.addLayout(right_panel, 1)

        main_layout.addLayout(top_layout)

        # -- XML Preview --
        preview_label = QLabel("XML Preview:")
        preview_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(preview_label)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.preview_text.setFont(font)
        self.preview_text.setMaximumHeight(220)
        main_layout.addWidget(self.preview_text)

        # -- Validation status --
        self.validation_label = QLabel("Ready")
        self.validation_label.setStyleSheet(
            "color: " + _C["text_secondary"] + "; padding: 4px;"
        )
        main_layout.addWidget(self.validation_label)

        # -- Buttons --
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_export = QPushButton("Export")
        self.btn_export.setDefault(True)
        self.btn_export.clicked.connect(self._on_export)
        btn_row.addWidget(self.btn_export)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_cancel)

        main_layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    def _apply_styles(self) -> None:
        bg = _C["bg_primary"]
        bg2 = _C["bg_secondary"]
        bg3 = _C["bg_tertiary"]
        txt = _C["text_primary"]
        txt2 = _C["text_secondary"]
        brd = _C["border"]
        acc = _C["accent_blue"]

        self.setStyleSheet(
            "QDialog { background-color: %s; color: %s; }" % (bg, txt)
            + " QListWidget { background-color: %s; border: 1px solid %s; border-radius: 3px; color: %s; padding: 4px; }" % (bg2, brd, txt)
            + " QListWidget::item { padding: 4px 8px; border-radius: 2px; }"
            + " QListWidget::item:selected { background-color: %s; color: white; }" % acc
            + " QListWidget::item:hover { background-color: %s; }" % bg3
            + " QLineEdit, QTextEdit { background-color: %s; color: %s; border: 1px solid %s; border-radius: 3px; padding: 5px 8px; }" % (bg3, txt, brd)
            + " QLineEdit:focus, QTextEdit:focus { border-color: %s; }" % acc
            + " QPushButton { background-color: %s; color: %s; border: 1px solid %s; border-radius: 3px; padding: 6px 16px; }" % (bg3, txt, brd)
            + " QPushButton:hover { background-color: %s; color: white; }" % acc
            + " QPushButton:disabled { background-color: %s; color: %s; }" % (bg2, txt2)
            + " QPushButton:default { background-color: %s; color: white; border-color: %s; }" % (acc, _C["accent_light"])
            + " QRadioButton { color: %s; spacing: 6px; }" % txt
            + " QRadioButton::indicator { width: 14px; height: 14px; }"
            + " QLabel { color: %s; background: transparent; }" % txt
        )

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self.material_list.itemChanged.connect(self._on_material_toggled)
        self.radio_single.toggled.connect(self._update_preview)
        self.radio_per_material.toggled.connect(self._update_preview)
        self.prefix_edit.textChanged.connect(self._update_preview)

    # ------------------------------------------------------------------
    # Material list
    # ------------------------------------------------------------------

    def _populate_materials(self) -> None:
        self.material_list.blockSignals(True)
        self.material_list.clear()
        for mat in self._materials:
            item = QListWidgetItem(mat.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            item.setData(Qt.ItemDataRole.UserRole, mat)
            tooltip = (
                mat.name
                + " (" + mat.category + ")"
            )
            if mat.supplier:
                tooltip += " - " + mat.supplier
            item.setToolTip(tooltip)
            self.material_list.addItem(item)
        self.material_list.blockSignals(False)

    def _on_material_toggled(self, _item: QListWidgetItem) -> None:
        self._update_preview()

    def _on_select_all(self) -> None:
        self.material_list.blockSignals(True)
        for i in range(self.material_list.count()):
            self.material_list.item(i).setCheckState(Qt.CheckState.Checked)
        self.material_list.blockSignals(False)
        self._update_preview()

    def _on_deselect_all(self) -> None:
        self.material_list.blockSignals(True)
        for i in range(self.material_list.count()):
            self.material_list.item(i).setCheckState(Qt.CheckState.Unchecked)
        self.material_list.blockSignals(False)
        self._update_preview()

    def _get_checked_materials(self) -> list[Material]:
        checked: list[Material] = []
        for i in range(self.material_list.count()):
            item = self.material_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                mat = item.data(Qt.ItemDataRole.UserRole)
                if mat is not None:
                    checked.append(mat)
        return checked

    # ------------------------------------------------------------------
    # Directory browse
    # ------------------------------------------------------------------

    def _on_browse_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.dir_edit.text()
        )
        if directory:
            self.dir_edit.setText(directory)
            self._update_preview()

    # ------------------------------------------------------------------
    # Preview & Validation
    # ------------------------------------------------------------------

    def _update_preview(self) -> None:
        selected = self._get_checked_materials()

        if not selected:
            self.preview_text.clear()
            self.validation_label.setText("No materials selected.")
            self.validation_label.setStyleSheet(
                "color: " + _C["text_secondary"] + "; padding: 4px;"
            )
            self.btn_export.setEnabled(False)
            return

        self.btn_export.setEnabled(True)

        if self._xml_generator is not None:
            try:
                xml_string = self._xml_generator.generate(selected)
                self.preview_text.setPlainText(xml_string)
                is_valid, errors = self._xml_generator.validate(xml_string)
                if is_valid:
                    self.validation_label.setText(
                        "Validation: PASS - XML is valid (%d material(s))" % len(selected)
                    )
                    self.validation_label.setStyleSheet(
                        "color: " + _C["success"] + "; padding: 4px; font-weight: bold;"
                    )
                else:
                    error_text = "; ".join(errors[:3])
                    self.validation_label.setText(
                        "Validation: FAIL - " + error_text
                    )
                    self.validation_label.setStyleSheet(
                        "color: " + _C["error"] + "; padding: 4px; font-weight: bold;"
                    )
            except Exception as exc:
                logger.exception("XML generation failed")
                self.preview_text.setPlainText("Error generating XML preview: " + str(exc))
                self.validation_label.setText("Validation: ERROR - " + str(exc))
                self.validation_label.setStyleSheet(
                    "color: " + _C["error"] + "; padding: 4px; font-weight: bold;"
                )
        else:
            # No generator available, show placeholder
            self.preview_text.setPlainText(
                "<!-- XML preview unavailable (no generator configured) -->\n"
                "<EngineeringData>\n"
            )
            for mat in selected:
                self.preview_text.append(
                    '  <Material name="' + mat.name + '" type="' + mat.category + '">'
                )
                self.preview_text.append("  </Material>")
            self.preview_text.append("</EngineeringData>")
            self.validation_label.setText(
                "Preview mode (no generator) - %d material(s) selected" % len(selected)
            )
            self.validation_label.setStyleSheet(
                "color: " + _C["text_secondary"] + "; padding: 4px;"
            )

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _on_export(self) -> None:
        selected = self._get_checked_materials()
        if not selected:
            return

        output_dir = self.dir_edit.text().strip()
        if not output_dir:
            self.validation_label.setText("Please select an output directory.")
            self.validation_label.setStyleSheet(
                "color: " + _C["warning"] + "; padding: 4px; font-weight: bold;"
            )
            return

        prefix = self.prefix_edit.text().strip() or "ansys_materials"
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        self._exported_paths = []

        if self._xml_generator is not None:
            try:
                if self.radio_single.isChecked():
                    filename = prefix + ".xml"
                    file_path = output_path / filename
                    self._xml_generator.generate_file(selected, str(file_path))
                    self._exported_paths.append(str(file_path.resolve()))
                else:
                    for mat in selected:
                        safe_name = mat.name.replace(" ", "_").replace("/", "_")
                        filename = prefix + "_" + safe_name + ".xml"
                        file_path = output_path / filename
                        self._xml_generator.generate_file([mat], str(file_path))
                        self._exported_paths.append(str(file_path.resolve()))

                self.validation_label.setText(
                    "Export complete: %d file(s) written" % len(self._exported_paths)
                )
                self.validation_label.setStyleSheet(
                    "color: " + _C["success"] + "; padding: 4px; font-weight: bold;"
                )
                self.export_completed.emit(self._exported_paths)
                self.accept()

            except Exception as exc:
                logger.exception("Export failed")
                self.validation_label.setText("Export failed: " + str(exc))
                self.validation_label.setStyleSheet(
                    "color: " + _C["error"] + "; padding: 4px; font-weight: bold;"
                )
        else:
            # No generator - write raw XML from preview
            xml_content = self.preview_text.toPlainText()
            try:
                if self.radio_single.isChecked():
                    filename = prefix + ".xml"
                    file_path = output_path / filename
                    file_path.write_text(xml_content, encoding="utf-8")
                    self._exported_paths.append(str(file_path.resolve()))
                else:
                    for mat in selected:
                        safe_name = mat.name.replace(" ", "_").replace("/", "_")
                        filename = prefix + "_" + safe_name + ".xml"
                        file_path = output_path / filename
                        # Generate minimal XML for single material
                        single_xml = (
                            '<?xml version="1.0" encoding="utf-8"?>\n'
                            "<EngineeringData>\n"
                            '  <Material name="' + mat.name + '" type="' + mat.category + '">\n'
                            "  </Material>\n"
                            "</EngineeringData>\n"
                        )
                        file_path.write_text(single_xml, encoding="utf-8")
                        self._exported_paths.append(str(file_path.resolve()))

                self.validation_label.setText(
                    "Export complete: %d file(s) written" % len(self._exported_paths)
                )
                self.validation_label.setStyleSheet(
                    "color: " + _C["success"] + "; padding: 4px; font-weight: bold;"
                )
                self.export_completed.emit(self._exported_paths)
                self.accept()

            except Exception as exc:
                logger.exception("Export failed")
                self.validation_label.setText("Export failed: " + str(exc))
                self.validation_label.setStyleSheet(
                    "color: " + _C["error"] + "; padding: 4px; font-weight: bold;"
                )
