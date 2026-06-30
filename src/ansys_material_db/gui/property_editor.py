"""PropertyEditor — dockable panel for editing material properties."""

from __future__ import annotations

from typing import Any, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDockWidget,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ansys_material_db.gui.styles import ANSYS_COLORS
from ansys_material_db.gui.widgets.property_table import PropertyTable
from ansys_material_db.gui.widgets.temp_curve_widget import TempCurveWidget
from ansys_material_db.models.material import Material
from ansys_material_db.i18n import t as _t


class PropertyEditor(QDockWidget):
    """Dockable panel for editing material info and thermal properties.

    Features:
      - Editable header fields (name, category, supplier, product name).
      - PropertyTable for all thermal properties.
      - TempCurveWidget for the currently selected temperature-dependent property.
      - Save button emitting ``material_saved``.
    """

    material_saved = pyqtSignal(object)  # Material
    property_changed = pyqtSignal(str, object)  # (key, value)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(_t("panel.editor"), parent)
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self._material: Optional[Material] = None
        self._init_ui()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # ---- Material info header ----
        header_group = QGroupBox(_t("editor.material_info"))
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_edit = QLineEdit()
        self.category_edit = QLineEdit()
        self.supplier_edit = QLineEdit()
        self.product_name_edit = QLineEdit()

        label_style = f"color: {ANSYS_COLORS['text_secondary']};"
        for lbl_text, widget in [
            (_t("editor.name") + ":", self.name_edit),
            (_t("editor.category") + ":", self.category_edit),
            (_t("editor.supplier") + ":", self.supplier_edit),
            (_t("editor.product_name") + ":", self.product_name_edit),
        ]:
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet(label_style)
            form.addRow(lbl, widget)

        header_group.setLayout(form)
        layout.addWidget(header_group)

        # ---- Property table ----
        self.property_table = PropertyTable()
        self.property_table.property_changed.connect(self._on_property_changed)
        layout.addWidget(self.property_table)

        # ---- Temperature curve widget (hidden by default) ----
        self.temp_curve = TempCurveWidget()
        self.temp_curve.hide()
        layout.addWidget(self.temp_curve)

        # Watch for temp-dependent checkbox changes
        self.property_table.table.cellClicked.connect(self._on_row_selected)

        # ---- Save button ----
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.save_btn = QPushButton(_t("editor.save"))
        self.save_btn.setFixedWidth(140)
        self.save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

        layout.addStretch()

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)
        self.setWidget(outer)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_material(self, material: Material) -> None:
        """Load a material into the editor."""
        self._material = material
        self.name_edit.setText(material.name)
        self.category_edit.setText(material.category)
        self.supplier_edit.setText(material.supplier)
        self.product_name_edit.setText(material.product_name)
        self.property_table.load_material(material)
        self.temp_curve.hide()

    def get_material(self) -> Optional[Material]:
        """Build and return a :class:`Material` from current editor state.

        Returns ``None`` if no material has been loaded.
        """
        if self._material is None:
            return None

        props = self.property_table.get_properties()

        # Merge temperature tables from temp_curve if visible
        if not self.temp_curve.isHidden():
            # Find which property is currently being edited for temp data
            current_row = self.property_table.table.currentRow()
            if 0 <= current_row < len(props):
                tp = self.temp_curve.get_temperature_table()
                props[current_row].temperature_table = tp

        m = Material(
            id=self._material.id,
            name=self.name_edit.text().strip(),
            category=self.category_edit.text().strip(),
            supplier=self.supplier_edit.text().strip(),
            product_name=self.product_name_edit.text().strip(),
            description=self._material.description,
            properties=props,
            source_document_id=self._material.source_document_id,
            created_at=self._material.created_at,
            updated_at=self._material.updated_at,
        )
        return m

    # ------------------------------------------------------------------
    # Internal slots
    # ------------------------------------------------------------------

    def _on_property_changed(self, key: str, value: Any) -> None:
        self.property_changed.emit(key, value)

    def _on_row_selected(self, row: int, _col: int) -> None:
        """Show/hide TempCurveWidget based on checkbox state of the selected row."""
        checkbox_widget = self.property_table.table.cellWidget(row, 4)
        if checkbox_widget is None:
            self.temp_curve.hide()
            return
        checkbox_widget.findChild(type(self.property_table._checkboxes.get(0)))  # type: ignore[type-var]
        # Fall back: check the stored checkbox dict
        checkbox = self.property_table._checkboxes.get(row)
        if checkbox and checkbox.isChecked():
            # Load temperature data from the existing property
            props = self.property_table.get_properties()
            if row < len(props):
                self.temp_curve.load_table(props[row].temperature_table)
            self.temp_curve.show()
        else:
            self.temp_curve.hide()

    def _on_save(self) -> None:
        material = self.get_material()
        if material is not None:
            self.material_saved.emit(material)
