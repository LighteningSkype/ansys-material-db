"""PropertyTable — editable QTableWidget for material thermal properties."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ansys_material_db.gui.styles import ANSYS_COLORS
from ansys_material_db.i18n import t
from ansys_material_db.i18n import pt
from ansys_material_db.models.material import (
    THERMAL_PROPERTIES,
    Material,
    MaterialProperty,
)

_COLUMNS_KEYS = ["prop_col.name", "prop_col.value", "prop_col.unit", "prop_col.source", "prop_col.temp_dep"]


class PropertyTable(QWidget):
    """Editable table for material thermal properties.

    Columns: Property Name | Value | Unit | Source | Temp Dependent
    """

    property_changed = pyqtSignal(str, object)  # (property_key, new_value)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._property_keys: list[str] = []
        self._checkboxes: dict[int, QCheckBox] = {}
        self._init_ui()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header_label = QLabel(t("prop_table.title"))
        header_label.setStyleSheet(
            f"color: {ANSYS_COLORS['text_secondary']}; font-weight: bold; padding: 4px 0;"
        )
        layout.addWidget(header_label)

        self.table = QTableWidget()
        self.table.setColumnCount(len(_COLUMNS_KEYS))
        self.table.setHorizontalHeaderLabels([t(k) for k in _COLUMNS_KEYS])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self.table.cellChanged.connect(self._on_cell_changed)
        layout.addWidget(self.table)

        # Bottom toolbar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.add_row_btn = QPushButton("+ Add Property")
        self.add_row_btn.setFixedWidth(130)
        btn_layout.addWidget(self.add_row_btn)
        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_material(self, material: Material) -> None:
        """Populate the table from a :class:`Material` instance."""
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self._property_keys.clear()
        self._checkboxes.clear()

        # Merge declared THERMAL_PROPERTIES with any extras on the material
        known_keys = list(THERMAL_PROPERTIES.keys())
        extra_keys = [
            p.name for p in material.properties if p.name not in known_keys
        ]
        all_keys = known_keys + extra_keys

        # Build lookup from material properties
        prop_map: dict[str, MaterialProperty] = {p.name: p for p in material.properties}

        for row_idx, key in enumerate(all_keys):
            info = THERMAL_PROPERTIES.get(key, {})
            display = pt(key)
            unit = info.get("unit", "")
            prop = prop_map.get(key)

            self._property_keys.append(key)

            self.table.insertRow(row_idx)

            # Column 0: Property Name (read-only)
            name_item = QTableWidgetItem(display)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setData(Qt.ItemDataRole.UserRole, key)
            self.table.setItem(row_idx, 0, name_item)

            # Column 1: Value (editable, numeric)
            val_str = ""
            if prop and prop.value is not None:
                val_str = str(prop.value)
            val_item = QTableWidgetItem(val_str)
            self.table.setItem(row_idx, 1, val_item)

            # Column 2: Unit (read-only)
            unit_str = unit or (prop.unit if prop else "")
            unit_item = QTableWidgetItem(unit_str)
            unit_item.setFlags(unit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 2, unit_item)

            # Column 3: Source (editable)
            source_str = prop.source if prop else ""
            source_item = QTableWidgetItem(source_str)
            self.table.setItem(row_idx, 3, source_item)

            # Column 4: Temp Dependent (checkbox)
            checkbox = QCheckBox()
            checkbox.setChecked(prop.is_temp_dependent if prop else False)
            check_widget = QWidget()
            check_layout = QHBoxLayout(check_widget)
            check_layout.addWidget(checkbox)
            check_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            check_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row_idx, 4, check_widget)
            self._checkboxes[row_idx] = checkbox
            checkbox.stateChanged.connect(
                lambda state, r=row_idx: self._on_temp_dependent_changed(r, state)
            )

        self.table.blockSignals(False)

    def get_properties(self) -> list[MaterialProperty]:
        """Read current table contents and return a list of :class:`MaterialProperty`."""
        props: list[MaterialProperty] = []
        for row_idx in range(self.table.rowCount()):
            key = self._property_keys[row_idx]
            info = THERMAL_PROPERTIES.get(key, {})
            display = pt(key)
            unit = info.get("unit", "")

            val_item = self.table.item(row_idx, 1)
            value: Optional[float] = None
            if val_item and val_item.text().strip():
                try:
                    value = float(val_item.text().strip())
                except ValueError:
                    value = None

            source_item = self.table.item(row_idx, 3)
            source = source_item.text() if source_item else ""

            checkbox = self._checkboxes.get(row_idx)
            is_temp = checkbox.isChecked() if checkbox else False

            props.append(
                MaterialProperty(
                    name=key,
                    display_name=display,
                    value=value,
                    unit=unit,
                    source=source,
                    is_temp_dependent=is_temp,
                )
            )
        return props

    # ------------------------------------------------------------------
    # Internal slots
    # ------------------------------------------------------------------

    def _on_cell_changed(self, row: int, column: int) -> None:
        key_item = self.table.item(row, 0)
        if not key_item:
            return
        key = key_item.data(Qt.ItemDataRole.UserRole) or self._property_keys[row]
        cell_item = self.table.item(row, column)
        new_value = cell_item.text() if cell_item else ""
        self.property_changed.emit(key, new_value)

    def _on_temp_dependent_changed(self, row: int, state: int) -> None:
        key = self._property_keys[row]
        self.property_changed.emit(key, {"is_temp_dependent": state == Qt.CheckState.Checked.value})

