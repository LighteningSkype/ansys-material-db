"""QAChatPanel — dockable Q&A chat interface for the knowledge base."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from ansys_material_db.gui.styles import ANSYS_COLORS
from ansys_material_db.gui.widgets.chat_bubble import ChatBubble
from ansys_material_db.i18n import t as _t


class _LoadingIndicator(QWidget):
    """Animated loading dots shown while the LLM is processing."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 6, 20, 6)
        self.label = QLabel(_t("chat.thinking"))
        self.label.setStyleSheet(
            f"color: {ANSYS_COLORS['text_secondary']}; font-style: italic;"
        )
        layout.addWidget(self.label)
        self._dot_count = 0
        self._timer: Optional[QTimer] = None

    def start(self) -> None:
        self._dot_count = 0
        self.show()
        if self._timer is None:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._tick)
        self._timer.start(500)

    def stop(self) -> None:
        if self._timer:
            self._timer.stop()
        self.hide()

    def _tick(self) -> None:
        self._dot_count = (self._dot_count + 1) % 4
        self.label.setText("Thinking" + "." * self._dot_count)


class QAChatPanel(QDockWidget):
    """Dockable Q&A chat panel for querying the knowledge base.

    Features:
      - Scrollable chat area with :class:`ChatBubble` widgets.
      - Text input with Send button; Enter key sends.
      - Loading indicator during LLM processing.
      - Clear history button.
    """

    question_asked = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(_t("panel.chat"), parent)
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self._init_ui()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ---- Header row with clear button ----
        header_row = QHBoxLayout()
        header = QLabel(_t("chat.header"))
        header.setStyleSheet(
            f"color: {ANSYS_COLORS['text_secondary']}; font-weight: bold;"
        )
        header_row.addWidget(header)
        header_row.addStretch()

        self.clear_btn = QPushButton(_t("chat.clear_history"))
        self.clear_btn.setFixedWidth(110)
        self.clear_btn.clicked.connect(self._clear_history)
        header_row.addWidget(self.clear_btn)
        layout.addLayout(header_row)

        # ---- Chat scroll area ----
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(4, 4, 4, 4)
        self.chat_layout.setSpacing(6)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Spacer at bottom so messages stay near top
        self._bottom_spacer = QSpacerItem(
            20, 40,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
        )
        self.chat_layout.addSpacerItem(self._bottom_spacer)

        self.scroll_area.setWidget(self.chat_container)
        layout.addWidget(self.scroll_area)

        # ---- Loading indicator ----
        self.loading = _LoadingIndicator()
        self.loading.hide()
        layout.addWidget(self.loading)

        # ---- Input row ----
        input_row = QHBoxLayout()
        input_row.setSpacing(6)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(_t("chat.placeholder"))
        self.input_field.returnPressed.connect(self._on_send)
        input_row.addWidget(self.input_field)

        self.send_btn = QPushButton(_t("chat.send"))
        self.send_btn.setFixedWidth(80)
        self.send_btn.clicked.connect(self._on_send)
        input_row.addWidget(self.send_btn)

        layout.addLayout(input_row)

        self.setWidget(container)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_message(
        self,
        role: str,
        content: str,
        sources: Optional[list[str]] = None,
    ) -> None:
        """Append a chat bubble to the conversation area."""
        bubble = ChatBubble(role=role, content=content, sources=sources)

        # Insert before the bottom spacer
        idx = self.chat_layout.count() - 1
        self.chat_layout.insertWidget(idx, bubble)

        # Scroll to bottom
        QTimer.singleShot(50, self._scroll_to_bottom)

    def display_response(self, text: str) -> None:
        """Convenience: add an assistant message to the chat."""
        self.add_message("assistant", text)

    def load_material(self, material) -> None:
        """Display material context in the chat panel."""
        props = material.properties if material.properties else []
        if props:
            lines = [f"- {p.display_name}: {p.value} {p.unit}" if p.value else f"- {p.display_name}: (no value)" for p in props]
            props_text = chr(10).join(lines)
        else:
            props_text = "(no properties)"

        summary = (
            f"Material loaded: {material.name}"
            + (f" ({material.category})" if material.category else "")
            + chr(10) + chr(10) + "Properties:" + chr(10) + props_text
        )
        self.add_message("system", summary)

    def show_loading(self, visible: bool = True) -> None:
        """Show or hide the loading indicator."""
        if visible:
            self.loading.start()
        else:
            self.loading.stop()

    def hide_loading(self) -> None:
        """Hide the loading indicator."""
        self.loading.stop()

    # ------------------------------------------------------------------
    # Internal slots
    # ------------------------------------------------------------------

    def _on_send(self) -> None:
        text = self.input_field.text().strip()
        if not text:
            return
        self.add_message("user", text)
        self.input_field.clear()
        self.question_asked.emit(text)

    def _clear_history(self) -> None:
        """Remove all chat bubbles."""
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget and widget is not self.loading:
                widget.deleteLater()
        # Re-add spacer
        self.chat_layout.addSpacerItem(self._bottom_spacer)

    def _scroll_to_bottom(self) -> None:
        sb = self.scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())

