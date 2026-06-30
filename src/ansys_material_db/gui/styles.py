"""Ansys Workbench-inspired dark theme stylesheet for PyQt6."""

from __future__ import annotations

ANSYS_COLORS: dict[str, str] = {
    "bg_primary": "#1e1e2e",
    "bg_secondary": "#2a2a3e",
    "bg_tertiary": "#353550",
    "accent_blue": "#1a73e8",
    "accent_light": "#4a9eff",
    "text_primary": "#e0e0e0",
    "text_secondary": "#a0a0b0",
    "border": "#3a3a50",
    "success": "#4caf50",
    "warning": "#ff9800",
    "error": "#f44336",
}

_C = ANSYS_COLORS


def get_ansys_stylesheet() -> str:
    """Return a complete QSS stylesheet emulating an Ansys Workbench dark theme."""
    return f"""
    /* ---- Global ---- */
    QWidget {{
        background-color: {_C["bg_primary"]};
        color: {_C["text_primary"]};
        font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        font-size: 13px;
    }}

    /* ---- QMainWindow ---- */
    QMainWindow {{
        background-color: {_C["bg_primary"]};
    }}

    /* ---- QMenuBar ---- */
    QMenuBar {{
        background-color: {_C["bg_secondary"]};
        color: {_C["text_primary"]};
        border-bottom: 1px solid {_C["border"]};
        padding: 2px 0;
    }}
    QMenuBar::item {{
        padding: 4px 12px;
        background: transparent;
    }}
    QMenuBar::item:selected {{
        background-color: {_C["accent_blue"]};
        border-radius: 3px;
    }}
    QMenuBar::item:pressed {{
        background-color: {_C["accent_light"]};
    }}

    /* ---- QMenu ---- */
    QMenu {{
        background-color: {_C["bg_secondary"]};
        color: {_C["text_primary"]};
        border: 1px solid {_C["border"]};
        padding: 4px 0;
    }}
    QMenu::item {{
        padding: 6px 28px 6px 16px;
    }}
    QMenu::item:selected {{
        background-color: {_C["accent_blue"]};
    }}
    QMenu::separator {{
        height: 1px;
        background: {_C["border"]};
        margin: 4px 8px;
    }}

    /* ---- QToolBar ---- */
    QToolBar {{
        background-color: {_C["bg_secondary"]};
        border-bottom: 1px solid {_C["border"]};
        spacing: 4px;
        padding: 2px;
    }}
    QToolBar::separator {{
        width: 1px;
        background: {_C["border"]};
        margin: 4px 6px;
    }}
    QToolButton {{
        background: transparent;
        color: {_C["text_primary"]};
        border: 1px solid transparent;
        border-radius: 3px;
        padding: 4px 8px;
        font-size: 13px;
    }}
    QToolButton:hover {{
        background-color: {_C["bg_tertiary"]};
        border-color: {_C["border"]};
    }}
    QToolButton:pressed {{
        background-color: {_C["accent_blue"]};
        border-color: {_C["accent_light"]};
    }}

    /* ---- QStatusBar ---- */
    QStatusBar {{
        background-color: {_C["bg_secondary"]};
        color: {_C["text_secondary"]};
        border-top: 1px solid {_C["border"]};
        font-size: 12px;
    }}
    QStatusBar::item {{
        border: none;
    }}

    /* ---- QDockWidget ---- */
    QDockWidget {{
        color: {_C["text_primary"]};
        font-weight: bold;
    }}
    QDockWidget::title {{
        background-color: {_C["bg_secondary"]};
        padding: 6px 8px;
        border-bottom: 1px solid {_C["border"]};
    }}

    /* ---- QTabWidget ---- */
    QTabWidget::pane {{
        border: 1px solid {_C["border"]};
        background-color: {_C["bg_primary"]};
    }}
    QTabBar::tab {{
        background-color: {_C["bg_secondary"]};
        color: {_C["text_secondary"]};
        padding: 8px 16px;
        border: 1px solid {_C["border"]};
        border-bottom: none;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background-color: {_C["bg_primary"]};
        color: {_C["text_primary"]};
        border-bottom: 2px solid {_C["accent_blue"]};
    }}
    QTabBar::tab:hover {{
        background-color: {_C["bg_tertiary"]};
    }}

    /* ---- QTableWidget / QTableView ---- */
    QTableWidget, QTableView {{
        background-color: {_C["bg_primary"]};
        alternate-background-color: {_C["bg_secondary"]};
        color: {_C["text_primary"]};
        gridline-color: {_C["border"]};
        border: 1px solid {_C["border"]};
        selection-background-color: {_C["accent_blue"]};
        selection-color: {_C["text_primary"]};
        outline: none;
    }}
    QTableWidget::item, QTableView::item {{
        padding: 4px 6px;
    }}
    QHeaderView::section {{
        background-color: {_C["bg_secondary"]};
        color: {_C["text_primary"]};
        border: 1px solid {_C["border"]};
        padding: 5px 8px;
        font-weight: bold;
    }}

    /* ---- QTreeView / QListView ---- */
    QTreeView, QListView {{
        background-color: {_C["bg_primary"]};
        color: {_C["text_primary"]};
        border: 1px solid {_C["border"]};
        outline: none;
        alternate-background-color: {_C["bg_secondary"]};
    }}
    QTreeView::item, QListView::item {{
        padding: 4px 6px;
    }}
    QTreeView::item:selected, QListView::item:selected {{
        background-color: {_C["accent_blue"]};
        color: {_C["text_primary"]};
    }}
    QTreeView::item:hover, QListView::item:hover {{
        background-color: {_C["bg_tertiary"]};
    }}
    QTreeView::branch:has-children:!has-siblings:closed,
    QTreeView::branch:closed:has-children:has-siblings {{
        border-image: none;
    }}

    /* ---- QTextEdit / QPlainTextEdit ---- */
    QTextEdit, QPlainTextEdit {{
        background-color: {_C["bg_primary"]};
        color: {_C["text_primary"]};
        border: 1px solid {_C["border"]};
        border-radius: 3px;
        padding: 4px;
        selection-background-color: {_C["accent_blue"]};
    }}

    /* ---- QLineEdit ---- */
    QLineEdit {{
        background-color: {_C["bg_tertiary"]};
        color: {_C["text_primary"]};
        border: 1px solid {_C["border"]};
        border-radius: 3px;
        padding: 5px 8px;
        selection-background-color: {_C["accent_blue"]};
    }}
    QLineEdit:focus {{
        border-color: {_C["accent_blue"]};
    }}

    /* ---- QSpinBox / QDoubleSpinBox ---- */
    QSpinBox, QDoubleSpinBox {{
        background-color: {_C["bg_tertiary"]};
        color: {_C["text_primary"]};
        border: 1px solid {_C["border"]};
        border-radius: 3px;
        padding: 4px 6px;
        selection-background-color: {_C["accent_blue"]};
    }}
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {_C["accent_blue"]};
    }}
    QSpinBox::up-button, QDoubleSpinBox::up-button,
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        background-color: {_C["bg_secondary"]};
        border: 1px solid {_C["border"]};
        width: 18px;
    }}
    QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
    QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
        background-color: {_C["bg_tertiary"]};
    }}

    /* ---- QComboBox ---- */
    QComboBox {{
        background-color: {_C["bg_tertiary"]};
        color: {_C["text_primary"]};
        border: 1px solid {_C["border"]};
        border-radius: 3px;
        padding: 5px 8px;
        min-width: 80px;
    }}
    QComboBox:hover {{
        border-color: {_C["accent_blue"]};
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 24px;
        border-left: 1px solid {_C["border"]};
    }}
    QComboBox QAbstractItemView {{
        background-color: {_C["bg_secondary"]};
        color: {_C["text_primary"]};
        border: 1px solid {_C["border"]};
        selection-background-color: {_C["accent_blue"]};
        outline: none;
    }}

    /* ---- QPushButton ---- */
    QPushButton {{
        background-color: {_C["bg_tertiary"]};
        color: {_C["text_primary"]};
        border: 1px solid {_C["border"]};
        border-radius: 3px;
        padding: 6px 16px;
        font-size: 13px;
        min-height: 20px;
    }}
    QPushButton:hover {{
        background-color: {_C["accent_blue"]};
        border-color: {_C["accent_light"]};
        color: white;
    }}
    QPushButton:pressed {{
        background-color: {_C["accent_light"]};
    }}
    QPushButton:disabled {{
        background-color: {_C["bg_secondary"]};
        color: {_C["text_secondary"]};
        border-color: {_C["border"]};
    }}
    QPushButton:default {{
        background-color: {_C["accent_blue"]};
        color: white;
        border-color: {_C["accent_light"]};
    }}
    QPushButton:default:hover {{
        background-color: {_C["accent_light"]};
    }}

    /* ---- QScrollBar ---- */
    QScrollBar:vertical {{
        background: {_C["bg_primary"]};
        width: 12px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background-color: {_C["bg_tertiary"]};
        min-height: 30px;
        border-radius: 4px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {_C["accent_blue"]};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QScrollBar:horizontal {{
        background: {_C["bg_primary"]};
        height: 12px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {_C["bg_tertiary"]};
        min-width: 30px;
        border-radius: 4px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {_C["accent_blue"]};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}

    /* ---- QSplitter ---- */
    QSplitter::handle {{
        background-color: {_C["border"]};
    }}
    QSplitter::handle:horizontal {{
        width: 3px;
    }}
    QSplitter::handle:vertical {{
        height: 3px;
    }}
    QSplitter::handle:hover {{
        background-color: {_C["accent_blue"]};
    }}

    /* ---- QGroupBox ---- */
    QGroupBox {{
        border: 1px solid {_C["border"]};
        border-radius: 4px;
        margin-top: 12px;
        padding-top: 12px;
        font-weight: bold;
        color: {_C["text_primary"]};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        padding: 0 6px;
        color: {_C["accent_light"]};
    }}

    /* ---- QProgressBar ---- */
    QProgressBar {{
        background-color: {_C["bg_secondary"]};
        border: 1px solid {_C["border"]};
        border-radius: 3px;
        text-align: center;
        color: {_C["text_primary"]};
        height: 18px;
    }}
    QProgressBar::chunk {{
        background-color: {_C["accent_blue"]};
        border-radius: 2px;
    }}

    /* ---- QLabel (status) ---- */
    QLabel {{
        color: {_C["text_primary"]};
        background: transparent;
    }}

    /* ---- QToolTip ---- */
    QToolTip {{
        background-color: {_C["bg_secondary"]};
        color: {_C["text_primary"]};
        border: 1px solid {_C["border"]};
        padding: 4px 6px;
    }}
    """


# Alias used by other modules
get_stylesheet = get_ansys_stylesheet


def apply_theme(app):
    """Apply the Ansys dark theme to a QApplication instance."""
    app.setStyleSheet(get_ansys_stylesheet())
