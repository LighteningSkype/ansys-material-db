"""Multi-step document import wizard."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QFileInfo
from PyQt6.QtGui import QColor, QFont, QTextCursor
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QProgressBar,
    QRadioButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWizard,
    QWizardPage,
    QWidget,
    QHeaderView,
    QAbstractItemView,
)

from ansys_material_db.gui.styles import ANSYS_COLORS
from ansys_material_db.i18n import t

_C = ANSYS_COLORS

logger = logging.getLogger(__name__)

_IMPORT_FILTERS = "Documents (*.pdf *.png *.jpg *.jpeg *.tiff *.tif *.bmp);;All Files (*)"


class _ImportWorker(QThread):
    """Background thread that processes documents through the knowledge base."""

    progress_updated = pyqtSignal(str, float, float)
    file_completed = pyqtSignal(str, dict)
    all_completed = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        file_paths: list[str],
        supplier: str,
        page_range: Optional[tuple[int, int]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.file_paths = file_paths
        self.supplier = supplier
        self.page_range = page_range
        self._knowledge_base = None
        self._cancelled = False

    def set_knowledge_base(self, kb) -> None:
        self._knowledge_base = kb

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        import asyncio

        total = len(self.file_paths)
        results: list[dict] = []

        for idx, file_path in enumerate(self.file_paths):
            if self._cancelled:
                break

            fname = Path(file_path).name
            self.progress_updated.emit("Processing: " + fname, float(idx), float(total))

            result: dict = {
                "file_path": file_path,
                "filename": fname,
                "status": "pending",
                "chunk_count": 0,
                "document_id": None,
            }

            if self._knowledge_base is not None:
                try:

                    def _progress_cb(
                        step: str,
                        cur: float,
                        tot: float,
                        _idx: int = idx,
                        _total: int = total,
                        _fp: str = file_path,
                    ) -> None:
                        fraction = (
                            (float(_idx) + cur / tot) / float(_total)
                            if tot
                            else float(_idx) / float(_total)
                        )
                        self.progress_updated.emit(step + ": " + Path(_fp).name, fraction, 1.0)

                    loop = asyncio.new_event_loop()
                    try:
                        kb_result = loop.run_until_complete(
                            self._knowledge_base.import_document(
                                file_path=file_path,
                                supplier=self.supplier,
                                page_range=self.page_range,
                                progress_callback=_progress_cb,
                                deferred=True,
                            )
                        )
                    finally:
                        loop.close()

                    result["status"] = kb_result.get("status", "unknown")
                    result["chunk_count"] = kb_result.get("chunk_count", 0)
                    result["document_id"] = kb_result.get("document_id")
                    if "error" in kb_result:
                        result["error"] = kb_result["error"]
                except Exception as exc:
                    logger.exception("Import failed for %s", file_path)
                    result["status"] = "error"
                    result["error"] = str(exc)
            else:
                result["status"] = "completed"
                result["chunk_count"] = 0
                result["document_id"] = None
                time.sleep(0.05)

            self.file_completed.emit(file_path, result)
            results.append(result)

        self.progress_updated.emit(t("wiz.done"), 1.0, 1.0)
        self.all_completed.emit(results)


class _FileSelectionPage(QWizardPage):
    """Step 1 - Select files for import."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTitle(t("wiz.select_docs"))
        self.setSubTitle(t("wiz.select_hint"))

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.file_list.setMinimumHeight(200)
        self.file_list.currentRowChanged.connect(self._on_selection_changed)
        layout.addWidget(self.file_list)

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton(t("wiz.add_files"))
        self.btn_add.clicked.connect(self._on_add_files)
        btn_row.addWidget(self.btn_add)

        self.btn_remove = QPushButton(t("wiz.remove_selected"))
        self.btn_remove.clicked.connect(self._on_remove_selected)
        self.btn_remove.setEnabled(False)
        btn_row.addWidget(self.btn_remove)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.preview_label = QLabel(t("wiz.no_file"))
        self.preview_label.setStyleSheet(
            "color: "
            + _C["text_secondary"]
            + "; padding: 6px; border: 1px solid "
            + _C["border"]
            + "; border-radius: 3px;"
        )
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)

    def _on_add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Documents to Import",
            "",
            _IMPORT_FILTERS,
        )
        for f in files:
            if not self._find_item(f):
                item = QListWidgetItem(Path(f).name)
                item.setData(Qt.ItemDataRole.UserRole, f)
                item.setToolTip(f)
                self.file_list.addItem(item)
        self._update_preview()

    def _on_remove_selected(self) -> None:
        for item in reversed(self.file_list.selectedItems()):
            self.file_list.takeItem(self.file_list.row(item))
        self._update_preview()

    def _on_selection_changed(self, _row: int) -> None:
        self.btn_remove.setEnabled(len(self.file_list.selectedItems()) > 0)
        self._update_preview()

    def _update_preview(self) -> None:
        selected = self.file_list.selectedItems()
        if not selected:
            self.preview_label.setText(t("wiz.no_file"))
            return
        file_path = selected[0].data(Qt.ItemDataRole.UserRole)
        info = QFileInfo(file_path)
        size_mb = info.size() / (1024 * 1024)
        suffix = info.suffix().upper()
        self.preview_label.setText(
            "<b>"
            + info.fileName()
            + "</b><br>"
            + "Type: "
            + suffix
            + " | Size: "
            + "{:.2f}".format(size_mb)
            + " MB<br>"
            + "Path: "
            + file_path
        )

    def _find_item(self, file_path: str) -> QListWidgetItem | None:
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == file_path:
                return item
        return None

    def get_file_paths(self) -> list[str]:
        paths = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            paths.append(item.data(Qt.ItemDataRole.UserRole))
        return paths

    def validatePage(self) -> bool:
        return self.file_list.count() > 0


class _ImportOptionsPage(QWizardPage):
    """Step 2 - Configure import options."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTitle(t("wiz.options"))
        self.setSubTitle(t("wiz.options_hint"))

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        supplier_label = QLabel(t("wiz.supplier_name"))
        layout.addWidget(supplier_label)
        self.supplier_edit = QLineEdit()
        self.supplier_edit.setPlaceholderText("e.g. DuPont, BASF, 3M...")
        layout.addWidget(self.supplier_edit)

        page_group_layout = QVBoxLayout()

        range_label = QLabel(t("wiz.page_range"))
        page_group_layout.addWidget(range_label)

        self.radio_all = QRadioButton(t("wiz.all_pages"))
        self.radio_all.setChecked(True)
        page_group_layout.addWidget(self.radio_all)

        range_row = QHBoxLayout()
        self.radio_custom = QRadioButton(t("wiz.custom_range"))
        range_row.addWidget(self.radio_custom)

        self.spin_start = QSpinBox()
        self.spin_start.setRange(1, 99999)
        self.spin_start.setValue(1)
        self.spin_start.setEnabled(False)
        range_row.addWidget(QLabel(t("wiz.from")))
        range_row.addWidget(self.spin_start)

        self.spin_end = QSpinBox()
        self.spin_end.setRange(1, 99999)
        self.spin_end.setValue(100)
        self.spin_end.setEnabled(False)
        range_row.addWidget(QLabel(t("wiz.to")))
        range_row.addWidget(self.spin_end)

        range_row.addStretch()
        page_group_layout.addLayout(range_row)

        self.radio_custom.toggled.connect(self.spin_start.setEnabled)
        self.radio_custom.toggled.connect(self.spin_end.setEnabled)

        layout.addLayout(page_group_layout)

        notes_label = QLabel(t("wiz.notes"))
        layout.addWidget(notes_label)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText(t("wiz.notes_hint"))
        self.notes_edit.setMaximumHeight(120)
        layout.addWidget(self.notes_edit)

        layout.addStretch()

    def get_supplier(self) -> str:
        return self.supplier_edit.text().strip()

    def get_page_range(self) -> Optional[tuple[int, int]]:
        if self.radio_custom.isChecked():
            return (self.spin_start.value(), self.spin_end.value())
        return None

    def get_notes(self) -> str:
        return self.notes_edit.toPlainText().strip()


class _ProcessingPage(QWizardPage):
    """Step 3 - Show import progress."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTitle(t("wiz.importing"))
        self.setSubTitle(t("wiz.parsing_hint"))

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel(t("wiz.waiting"))
        self.status_label.setStyleSheet("color: " + _C["accent_light"] + "; font-weight: bold;")
        layout.addWidget(self.status_label)

        log_label = QLabel(t("wiz.import_log"))
        layout.addWidget(log_label)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.log_text.setFont(font)
        self.log_text.setStyleSheet(
            "background-color: " + _C["bg_secondary"] + "; border: 1px solid " + _C["border"] + ";"
        )
        layout.addWidget(self.log_text)

        self._worker: _ImportWorker | None = None

    def initializePage(self) -> None:
        wizard = self.wizard()
        if not isinstance(wizard, ImportWizard):
            return

        file_paths = wizard.file_selection_page.get_file_paths()
        supplier = wizard.options_page.get_supplier()
        page_range = wizard.options_page.get_page_range()

        self.progress_bar.setValue(0)
        self.log_text.clear()
        self._append_log(t("wiz.starting_import", count=len(file_paths)))

        self._worker = _ImportWorker(file_paths, supplier, page_range, self)
        self._worker.progress_updated.connect(self._on_progress)
        self._worker.file_completed.connect(self._on_file_completed)
        self._worker.all_completed.connect(self._on_all_completed)
        self._worker.set_knowledge_base(wizard.knowledge_base)
        self._worker.start()

    def _on_progress(self, status_text: str, current: float, total: float) -> None:
        if total > 0:
            pct = int((current / total) * 100)
            self.progress_bar.setValue(min(pct, 100))
        self.status_label.setText(status_text)

    def _on_file_completed(self, file_path: str, result: dict) -> None:
        filename = Path(file_path).name
        status = result.get("status", "unknown")
        chunks = result.get("chunk_count", 0)
        if status == "completed":
            icon = "\u2713"
        elif status == "error":
            icon = "\u2717"
        else:
            icon = "\u2798"
        chunk_word = ""
        self._append_log(
            icon + " " + filename + ": " + status + " (" + str(chunks) + " " + chunk_word + ")"
        )
        if result.get("error"):
            self._append_log("  Error: " + result["error"])

    def _on_all_completed(self, results: list) -> None:
        self.progress_bar.setValue(100)
        completed = sum(1 for r in results if r.get("status") == "completed")
        errors = sum(1 for r in results if r.get("status") == "error")
        self.status_label.setText(
            t("wiz.import_complete", done=completed, fail=errors) + str(errors) + " failed"
        )
        total = len(results)
        self._append_log(
            "\n--- Import finished: " + str(completed) + "/" + str(total) + " files imported ---"
        )
        self._append_log(t("wiz.use_docmgr"))
        wizard = self.wizard()
        if isinstance(wizard, ImportWizard):
            wizard._import_results = results

    def _append_log(self, text: str) -> None:
        self.log_text.append(text)
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def validatePage(self) -> bool:
        if self._worker and self._worker.isRunning():
            self._worker.wait(5000)
        return True


class _SummaryPage(QWizardPage):
    """Step 4 - Show import summary."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTitle(t("wiz.summary"))
        self.setSubTitle(t("wiz.summary_hint"))
        self.setCommitPage(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        self._table_widget: QWidget | None = None

    def initializePage(self) -> None:
        wizard = self.wizard()
        if not isinstance(wizard, ImportWizard):
            return

        results = wizard._import_results
        if not results:
            self.summary_label.setText(t("wiz.no_results"))
            return

        completed = sum(1 for r in results if r.get("status") == "completed")
        skipped = sum(1 for r in results if r.get("status") == "skipped")
        errors = sum(1 for r in results if r.get("status") in ("error", "extraction_failed"))
        total_chunks = sum(r.get("chunk_count", 0) for r in results)
        doc_ids = [r["document_id"] for r in results if r.get("document_id")]

        summary_parts = [
            "<b>Files processed:</b> " + str(len(results)),
            "<b>Successfully imported:</b> " + str(completed) + " (pending vectorization)",
        ]
        if skipped:
            summary_parts.append("<b>Skipped (duplicates):</b> " + str(skipped))
        if errors:
            summary_parts.append("<b>Failed:</b> " + str(errors))
        summary_parts.append("<b>Total chunks created:</b> " + str(total_chunks))
        doc_ids_str = str(doc_ids) if doc_ids else "None"
        summary_parts.append("<b>Document IDs:</b> " + doc_ids_str)
        self.summary_label.setText("<br>".join(summary_parts))

        if self._table_widget is not None:
            self._table_widget.deleteLater()

        table = QTableWidget(len(results), 3)
        table.setHorizontalHeaderLabels(
            [t("wiz.result_file"), t("wiz.result_status"), t("wiz.result_chunks")]
        )
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        for row, result in enumerate(results):
            table.setItem(row, 0, QTableWidgetItem(result.get("filename", "")))
            status = result.get("status", "unknown")
            status_item = QTableWidgetItem(status)
            if status == "completed":
                status_item.setForeground(QColor(_C["success"]))
            elif status in ("error", "extraction_failed"):
                status_item.setForeground(QColor(_C["error"]))
            table.setItem(row, 1, status_item)
            table.setItem(row, 2, QTableWidgetItem(str(result.get("chunk_count", 0))))

        self._table_widget = table
        self.layout().addWidget(table)


class ImportWizard(QWizard):
    """Multi-step wizard for importing PDF and image documents.

    Signals
    -------
    import_completed(list[int])
        Emitted when the wizard finishes, carrying the list of
        successfully imported document database IDs.
    """

    import_completed = pyqtSignal(list)

    def __init__(self, knowledge_base=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("wiz.title"))
        self.setMinimumSize(640, 520)
        self.knowledge_base = knowledge_base
        self._import_results: list[dict] = []

        self._setup_pages()
        self._apply_styles()
        self._connect_signals()

    def _setup_pages(self) -> None:
        self.file_selection_page = _FileSelectionPage(self)
        self.options_page = _ImportOptionsPage(self)
        self.processing_page = _ProcessingPage(self)
        self.summary_page = _SummaryPage(self)

        self.addPage(self.file_selection_page)
        self.addPage(self.options_page)
        self.addPage(self.processing_page)
        self.addPage(self.summary_page)

    def _apply_styles(self) -> None:
        bg = _C["bg_primary"]
        bg2 = _C["bg_secondary"]
        bg3 = _C["bg_tertiary"]
        txt = _C["text_primary"]
        txt2 = _C["text_secondary"]
        brd = _C["border"]
        acc = _C["accent_blue"]
        _C["accent_light"]

        self.setStyleSheet(
            "QWizard { background-color: %s; color: %s; }" % (bg, txt)
            + " QWizardPage { background-color: %s; }" % bg
            + " QListWidget { background-color: %s; border: 1px solid %s; border-radius: 3px; color: %s; padding: 4px; }"
            % (bg2, brd, txt)
            + " QListWidget::item { padding: 4px 8px; border-radius: 2px; }"
            + " QListWidget::item:selected { background-color: %s; color: white; }" % acc
            + " QListWidget::item:hover { background-color: %s; }" % bg3
            + " QLineEdit, QTextEdit, QSpinBox { background-color: %s; color: %s; border: 1px solid %s; border-radius: 3px; padding: 5px 8px; }"
            % (bg3, txt, brd)
            + " QLineEdit:focus, QTextEdit:focus, QSpinBox:focus { border-color: %s; }" % acc
            + " QPushButton { background-color: %s; color: %s; border: 1px solid %s; border-radius: 3px; padding: 6px 16px; }"
            % (bg3, txt, brd)
            + " QPushButton:hover { background-color: %s; color: white; }" % acc
            + " QPushButton:disabled { background-color: %s; color: %s; }" % (bg2, txt2)
            + " QRadioButton { color: %s; spacing: 6px; }" % txt
            + " QRadioButton::indicator { width: 14px; height: 14px; }"
            + " QProgressBar { background-color: %s; border: 1px solid %s; border-radius: 3px; text-align: center; color: %s; height: 22px; }"
            % (bg2, brd, txt)
            + " QProgressBar::chunk { background-color: %s; border-radius: 2px; }" % acc
            + " QLabel { color: %s; background: transparent; }" % txt
            + " QTableWidget { background-color: %s; alternate-background-color: %s; color: %s; gridline-color: %s; border: 1px solid %s; }"
            % (bg, bg2, txt, brd, brd)
            + " QTableWidget::item { padding: 4px 6px; }"
            + " QHeaderView::section { background-color: %s; color: %s; border: 1px solid %s; padding: 5px 8px; font-weight: bold; }"
            % (bg2, txt, brd)
        )

    def _connect_signals(self) -> None:
        self.finished.connect(self._on_finished)

    def _on_finished(self, result: int) -> None:
        if result == 1:
            doc_ids = [
                r["document_id"] for r in self._import_results if r.get("document_id") is not None
            ]
            self.import_completed.emit(doc_ids)
