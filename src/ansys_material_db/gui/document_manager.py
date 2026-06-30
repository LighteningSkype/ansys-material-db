"""Document Manager dock widget -browse and manage imported documents."""

from __future__ import annotations


import asyncio

import logging


from PyQt6.QtCore import Qt, QThread, pyqtSignal

from PyQt6.QtGui import QColor

from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QDockWidget,
)


from ansys_material_db.gui.styles import ANSYS_COLORS

from ansys_material_db.i18n import t


_C = ANSYS_COLORS


logger = logging.getLogger(__name__)


class _ExtractWorker(QThread):
    """Background thread for extracting properties from a document."""

    finished = pyqtSignal(int, dict)  # document_id, result

    def __init__(self, knowledge_base, document_id: int, llm_client, parent=None):

        super().__init__(parent)

        self._kb = knowledge_base

        self._document_id = document_id

        self._llm_client = llm_client

    def run(self):

        loop = asyncio.new_event_loop()

        try:
            result = loop.run_until_complete(
                self._kb.extract_properties_from_document(self._document_id, self._llm_client)
            )

        except Exception as exc:
            logger.exception("Extract failed for document %d", self._document_id)

            result = {"status": "error", "error": str(exc)}

        finally:
            loop.close()

        self.finished.emit(self._document_id, result)


class DocumentManager(QDockWidget):
    """Dockable panel showing all imported documents with per-file actions."""

    document_selected = pyqtSignal(int)
    extraction_completed = pyqtSignal()  # document_id

    _STATUS_KEYS = {
        "pending": "docmgr.status_pending",
        "processing": "docmgr.status_pending",
        "extraction_failed": "docmgr.status_failed",
        "completed": "docmgr.status_completed",
        "vectorized": "docmgr.status_completed",
    }

    def __init__(self, database, knowledge_base, parent=None):

        super().__init__(t("docmgr.title"), parent)

        self._database = database

        self._knowledge_base = knowledge_base

        self._llm_client = None

        self._workers: list[QThread] = []

        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )

        self._init_ui()

        if self._database is not None:
            self.refresh_documents()

    # ------------------------------------------------------------------

    # Public API

    # ------------------------------------------------------------------

    def set_database(self, database):

        self._database = database

        self.refresh_documents()

    def set_llm_client(self, llm_client):
        """Set the LLM client for property extraction."""

        self._llm_client = llm_client

    def set_knowledge_base(self, kb):
        """Set the knowledge base for document operations."""

        self._knowledge_base = kb

    def refresh_documents(self):
        """Reload document list from database and rebuild the table."""

        if self._database is None:
            return

        documents = self._database.list_documents()

        self._populate_table(documents)

        self._update_status_labels(documents)

    # ------------------------------------------------------------------

    # UI setup

    # ------------------------------------------------------------------

    def _init_ui(self):

        container = QWidget()

        layout = QVBoxLayout(container)

        layout.setContentsMargins(6, 6, 6, 6)

        layout.setSpacing(6)

        # --- Top toolbar ---

        toolbar = QHBoxLayout()

        toolbar.setSpacing(6)

        self._btn_refresh = QPushButton(t("docmgr.refresh"))

        self._btn_refresh.setFixedHeight(28)

        self._btn_refresh.clicked.connect(self.refresh_documents)

        toolbar.addWidget(self._btn_refresh)

        self._search_input = QLineEdit()

        self._search_input.setPlaceholderText(t("docmgr.search_placeholder"))

        self._search_input.setFixedHeight(28)

        self._search_input.setStyleSheet(
            "QLineEdit { padding: 2px 8px; background-color: %s; color: %s; "
            "border: 1px solid %s; border-radius: 3px; }"
            % (_C["bg_primary"], _C["text_primary"], _C["border"])
        )

        self._search_input.textChanged.connect(self._apply_search)

        toolbar.addWidget(self._search_input)

        toolbar.addStretch()

        layout.addLayout(toolbar)

        # --- Table ---

        self._table = QTableWidget(0, 6)

        self._table.setHorizontalHeaderLabels(
            [
                t("docmgr.col_filename"),
                t("docmgr.col_type"),
                t("docmgr.col_pages"),
                t("docmgr.col_status"),
                t("docmgr.col_date"),
                t("docmgr.col_actions"),
            ]
        )

        for col in range(6):
            if col == 5:
                self._table.horizontalHeader().setSectionResizeMode(
                    col, QHeaderView.ResizeMode.Stretch
                )
            else:
                self._table.horizontalHeader().setSectionResizeMode(
                    col, QHeaderView.ResizeMode.Interactive
                )
        self._table.setColumnWidth(0, 220)
        self._table.setColumnWidth(1, 80)
        self._table.setColumnWidth(2, 60)
        self._table.setColumnWidth(3, 80)
        self._table.setColumnWidth(4, 150)

        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self._table.verticalHeader().setVisible(False)

        self._table.setStyleSheet(
            "QTableWidget { background-color: %s; color: %s; gridline-color: %s; }"
            "QTableWidget::item:selected { background-color: %s; color: %s; }"
            % (
                _C["bg_secondary"],
                _C["text_primary"],
                _C["border"],
                _C["accent_blue"],
                _C["bg_primary"],
            )
        )

        layout.addWidget(self._table)

        # --- Bottom status bar ---

        self._status_label = QLabel()

        self._status_label.setStyleSheet("color: %s; padding: 2px 8px;" % _C["text_secondary"])

        layout.addWidget(self._status_label)

        self.setWidget(container)

    # ------------------------------------------------------------------

    # Table population

    # ------------------------------------------------------------------

    def _populate_table(self, documents):

        self._table.setRowCount(0)

        self._table.setRowCount(len(documents))

        for row, doc in enumerate(documents):
            # Filename

            item_filename = QTableWidgetItem(doc.filename)

            self._table.setItem(row, 0, item_filename)

            # Type

            item_type = QTableWidgetItem(doc.file_type or "-")

            self._table.setItem(row, 1, item_type)

            # Size

            size_str = str(doc.page_count) if doc.page_count else "-"

            item_size = QTableWidgetItem(size_str)

            self._table.setItem(row, 2, item_size)

            # Status

            status_key = self._STATUS_KEYS.get(doc.status, "docmgr.status_pending")

            item_status = QTableWidgetItem(t(status_key))

            if doc.status == "completed":
                item_status.setForeground(QColor(_C["success"]))

            elif doc.status == "extraction_failed":
                item_status.setForeground(QColor(_C["error"]))

            else:
                item_status.setForeground(QColor(_C["text_secondary"]))

            self._table.setItem(row, 3, item_status)

            # Date

            date_str = doc.created_at[:16] if doc.created_at else "-"

            item_date = QTableWidgetItem(date_str)

            self._table.setItem(row, 4, item_date)

            # Actions

            document_id = doc.id

            actions_widget = QWidget()

            actions_layout = QHBoxLayout(actions_widget)

            actions_layout.setContentsMargins(2, 2, 2, 2)

            actions_layout.setSpacing(4)

            btn_extract = QPushButton(t("docmgr.btn_extract"))

            btn_extract.setFixedHeight(24)

            btn_extract.setStyleSheet(
                "QPushButton { padding: 2px 8px; background-color: %s; color: %s; border: 1px solid %s; border-radius: 3px; }"
                "QPushButton:hover { background-color: %s; color: white; }"
                % (_C["bg_tertiary"], _C["text_primary"], _C["border"], _C["accent_blue"])
            )

            btn_extract.clicked.connect(
                lambda _, did=document_id, b=btn_extract: self._on_extract(did, b)
            )

            actions_layout.addWidget(btn_extract)

            btn_delete = QPushButton(t("docmgr.btn_delete"))

            btn_delete.setFixedHeight(24)

            btn_delete.setStyleSheet(
                "QPushButton { padding: 2px 8px; background-color: %s; color: %s; border: 1px solid %s; border-radius: 3px; }"
                "QPushButton:hover { background-color: %s; color: white; }"
                % (_C["bg_tertiary"], _C["text_primary"], _C["border"], _C["error"])
            )

            btn_delete.clicked.connect(lambda _, did=document_id: self._on_delete(did))

            actions_layout.addWidget(btn_delete)

            actions_layout.addStretch()

            self._table.setCellWidget(row, 5, actions_widget)

    @staticmethod
    def _format_size(size_bytes: float) -> str:

        for unit in ("B", "KB", "MB", "GB"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"

            size_bytes /= 1024

        return f"{size_bytes:.1f} TB"

    # ------------------------------------------------------------------

    # Status labels

    # ------------------------------------------------------------------

    def _update_status_labels(self, documents):

        total = len(documents)
        self._status_label.setText(t("docmgr.total_docs", count=total))

    # ------------------------------------------------------------------

    # Search filtering

    # ------------------------------------------------------------------

    def _apply_search(self, text):

        text = text.strip().lower()

        for row in range(self._table.rowCount()):
            filename_item = self._table.item(row, 0)

            if filename_item is None:
                self._table.setRowHidden(row, False)

                continue

            match = text in filename_item.text().lower() if text else True

            self._table.setRowHidden(row, not match)

    # ------------------------------------------------------------------

    # Action handlers

    # ------------------------------------------------------------------

    def _on_extract(self, document_id: int, btn=None):

        if self._knowledge_base is None or self._llm_client is None:
            logger.warning(
                "Extract requested but backend not ready (kb=%s, llm=%s)",
                self._knowledge_base is not None,
                self._llm_client is not None,
            )

            QMessageBox.warning(
                self.window(),
                t("docmgr.title"),
                t("chat.not_configured"),
            )

            return

        if btn:
            try:
                btn.setEnabled(False)

                btn.setText(t("docmgr.extract_started"))

            except RuntimeError:
                pass

        worker = _ExtractWorker(self._knowledge_base, document_id, self._llm_client, self)

        worker.finished.connect(self._on_extract_done)

        self._workers.append(worker)

        worker.start()

    def _on_extract_done(self, document_id, result):

        if result.get("status") == "completed":
            count = result.get("materials_found", 0)

            self._update_status_tip(t("docmgr.extract_done", count=count))

        elif result.get("error"):
            logger.error("Extract failed for doc %d: %s", document_id, result["error"])

            self._update_status_tip(t("docmgr.status_failed") + ": " + result["error"])

        self.refresh_documents()

        # Notify MainWindow to refresh material browser after extraction
        if result.get("status") == "completed":
            self.extraction_completed.emit()

    def _on_delete(self, document_id: int):

        doc = self._database.get_document(document_id) if self._database else None

        name = doc.filename if doc else str(document_id)

        reply = QMessageBox.question(
            self,
            t("docmgr.title"),
            t("docmgr.confirm_delete", name=name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        if self._knowledge_base:
            self._knowledge_base.delete_document(document_id)

        elif self._database:
            self._database.conn.execute(
                "DELETE FROM text_chunks WHERE document_id = ?", (document_id,)
            )

            self._database.conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))

            self._database.conn.commit()

        self.refresh_documents()

    def _update_status_tip(self, msg: str):
        """Show a transient message in the status label, auto-clear after 5s."""

        self._status_label.setText(msg)

        from PyQt6.QtCore import QTimer

        QTimer.singleShot(5000, self._refresh_status_clear)

    def _refresh_status_clear(self):

        self.refresh_documents()
