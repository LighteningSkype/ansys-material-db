"""TempCurveWidget — editor for temperature-dependent property curves."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ansys_material_db.gui.styles import ANSYS_COLORS
from ansys_material_db.models.material import TemperaturePoint


class TempCurveWidget(QWidget):
    """Table editor for temperature–value pairs.

    Shown when a property is marked as temperature-dependent.
    """

    table_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._init_ui()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header = QLabel("Temperature-Dependent Curve")
        header.setStyleSheet(
            f"color: {ANSYS_COLORS['text_secondary']}; font-weight: bold; padding: 4px 0;"
        )
        layout.addWidget(header)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Temperature (°C)", "Value"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.cellChanged.connect(self._on_cell_changed)
        layout.addWidget(self.table)

        btn_row = QVBoxLayout()
        add_btn = QPushButton("+ Add Point")
        add_btn.setFixedWidth(110)
        add_btn.clicked.connect(self._add_row)
        btn_row.addWidget(add_btn)

        remove_btn = QPushButton("? Remove Point")
        remove_btn.setFixedWidth(130)
        remove_btn.clicked.connect(self._remove_row)
        btn_row.addWidget(remove_btn)
        btn_row.addStretch()

        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_table(self, points: list[TemperaturePoint]) -> None:
        """Populate the table from a list of :class:`TemperaturePoint`."""
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for pt in points:
            self._insert_row(pt.temperature, pt.value)
        self.table.blockSignals(False)

    def get_temperature_table(self) -> list[TemperaturePoint]:
        """Read current table contents and return a list of :class:`TemperaturePoint`."""
        points: list[TemperaturePoint] = []
        for row in range(self.table.rowCount()):
            temp_item = self.table.item(row, 0)
            val_item = self.table.item(row, 1)
            if not temp_item or not val_item:
                continue
            try:
                temp = float(temp_item.text())
                val = float(val_item.text())
                points.append(TemperaturePoint(temperature=temp, value=val))
            except ValueError:
                continue
        points.sort(key=lambda p: p.temperature)
        return points

    def clear_table(self) -> None:
        """Remove all rows."""
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.table.blockSignals(False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _insert_row(self, temperature: float = 0.0, value: float = 0.0) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(temperature)))
        self.table.setItem(row, 1, QTableWidgetItem(str(value)))

    def _add_row(self) -> None:
        self.table.blockSignals(True)
        self._insert_row()
        self.table.blockSignals(False)
        self.table_changed.emit()

    def _remove_row(self) -> None:
        current = self.table.currentRow()
        if current >= 0:
            self.table.blockSignals(True)
            self.table.removeRow(current)
            self.table.blockSignals(False)
            self.table_changed.emit()

    def _on_cell_changed(self, _row: int, _col: int) -> None:
        self.table_changed.emit()
