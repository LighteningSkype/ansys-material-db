"""ChatBubble - a styled frame for displaying a single chat message."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ansys_material_db.gui.styles import ANSYS_COLORS


class ChatBubble(QFrame):
    """Displays a single chat message with user/assistant styling."""

    def __init__(
        self,
        role: str = "user",
        content: str = "",
        sources: Optional[list[str]] = None,
        timestamp: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._role = role
        self._content = content
        self._sources = sources or []
        self._timestamp = timestamp or datetime.now().strftime("%H:%M")
        self._init_ui()

    def _init_ui(self) -> None:
        is_user = self._role == "user"

        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(4, 2, 4, 2)

        bubble = QFrame()
        bubble.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        bubble.setMaximumWidth(520)

        if is_user:
            bg = ANSYS_COLORS["accent_blue"]
            text_color = "#ffffff"
            outer.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            bg = ANSYS_COLORS["bg_tertiary"]
            text_color = ANSYS_COLORS["text_primary"]
            outer.setAlignment(Qt.AlignmentFlag.AlignLeft)

        bubble.setStyleSheet(
            "QFrame {"
            "  background-color: " + bg + ";"
            "  border-radius: 10px;"
            "  padding: 8px 12px;"
            "}"
        )

        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(4)

        role_label = QLabel("You" if is_user else "Assistant")
        role_label.setStyleSheet(
            "color: " + ANSYS_COLORS["text_secondary"] + "; font-weight: bold; border: none;"
        )
        bubble_layout.addWidget(role_label)

        content_label = QTextEdit()
        content_label.setPlainText(self._content)
        content_label.setReadOnly(True)
        content_label.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content_label.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content_label.setFrameShape(QFrame.Shape.NoFrame)
        content_label.setStyleSheet(
            "QTextEdit {"
            "  background-color: transparent;"
            "  color: " + text_color + ";"
            "  border: none;"
            "  font-size: 13px;"
            "}"
        )
        content_label.document().contentsChanged.connect(
            lambda: self._auto_resize_textedit(content_label)
        )
        bubble_layout.addWidget(content_label)

        if not is_user and self._sources:
            sources_text = "\n".join("\u2022 " + s for s in self._sources)
            sources_label = QLabel("Sources:\n" + sources_text)
            sources_label.setWordWrap(True)
            sources_label.setStyleSheet(
                "QLabel {"
                "  color: " + ANSYS_COLORS["text_secondary"] + ";"
                "  font-size: 11px;"
                "  font-style: italic;"
                "  border: none;"
                "  padding-top: 4px;"
                "  margin-top: 2px;"
                "  border-top: 1px solid " + ANSYS_COLORS["border"] + ";"
                "}"
            )
            bubble_layout.addWidget(sources_label)

        ts_label = QLabel(self._timestamp)
        ts_label.setStyleSheet(
            "color: " + ANSYS_COLORS["text_secondary"] + "; font-size: 10px; border: none;"
        )
        ts_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        bubble_layout.addWidget(ts_label)

        outer.addWidget(bubble)

    @staticmethod
    def _auto_resize_textedit(text_edit: QTextEdit) -> None:
        doc = text_edit.document()
        doc.setTextWidth(text_edit.viewport().width())
        h = int(doc.size().height()) + 8
        text_edit.setFixedHeight(max(h, 24))
