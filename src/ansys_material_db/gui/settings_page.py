"""Inline settings page for the main window."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ansys_material_db.config.settings import AppSettings
from ansys_material_db.i18n import SUPPORTED_LANGUAGES, t

_C_DICT = {
    "bg_primary": "#1e1e2e",
    "text_primary": "#e0e0e0",
    "text_secondary": "#a0a0b0",
    "accent_blue": "#1a73e8",
    "success": "#4caf50",
    "error": "#f44336",
}


class _ConnectionTestWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(
        self, base_url: str, api_key: str, model: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model

    def run(self) -> None:
        import urllib.request
        import urllib.error

        url = f"{self._base_url}/models"
        headers = {"Authorization": f"Bearer {self._api_key}"}
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    self.finished.emit(True, f"Connected (HTTP {resp.status})")
                    return
                self.finished.emit(False, f"Unexpected status: {resp.status}")
        except urllib.error.HTTPError as exc:
            self.finished.emit(False, f"HTTP {exc.code}: {exc.reason}")
        except Exception as exc:
            self.finished.emit(False, f"Connection failed: {exc}")


class SettingsPage(QWidget):
    """Inline settings page for LLM, embedding, and UI configuration."""

    settings_saved = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._app_settings: Optional[AppSettings] = None
        self._worker: Optional[_ConnectionTestWorker] = None
        self._setup_ui()

    def set_app_settings(self, app_settings: AppSettings) -> None:
        self._app_settings = app_settings
        self._load_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Scrollable content via style
        self.setStyleSheet(
            f"QWidget {{ background: {_C_DICT['bg_primary']}; color: {_C_DICT['text_primary']}; }}"
        )

        # LLM Configuration
        llm_group = QGroupBox(t("settings.llm_group"))
        llm_form = QFormLayout(llm_group)

        self._llm_base_url = QLineEdit()
        self._llm_base_url.setPlaceholderText("https://api.openai.com/v1")
        llm_form.addRow(t("settings.base_url"), self._llm_base_url)

        self._llm_api_key = QLineEdit()
        self._llm_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._llm_api_key.setPlaceholderText("sk-...")
        llm_form.addRow(t("settings.api_key"), self._llm_api_key)

        self._llm_model = QLineEdit()
        self._llm_model.setPlaceholderText("gpt-4o")
        llm_form.addRow(t("settings.model"), self._llm_model)

        self._llm_temperature = QDoubleSpinBox()
        self._llm_temperature.setRange(0.0, 2.0)
        self._llm_temperature.setSingleStep(0.1)
        llm_form.addRow(t("settings.temperature"), self._llm_temperature)

        self._llm_max_tokens = QSpinBox()
        self._llm_max_tokens.setRange(256, 128000)
        self._llm_max_tokens.setSingleStep(256)
        llm_form.addRow(t("settings.max_tokens"), self._llm_max_tokens)
        layout.addWidget(llm_group)

        # Embedding Configuration
        embed_group = QGroupBox(t("settings.embed_group"))
        embed_form = QFormLayout(embed_group)

        self._embed_model = QLineEdit()
        self._embed_model.setPlaceholderText("all-MiniLM-L6-v2")
        embed_form.addRow(t("settings.embed_model"), self._embed_model)

        self._embed_backend = QComboBox()
        self._embed_backend.addItems(["local", "openai"])
        embed_form.addRow(t("settings.embed_backend"), self._embed_backend)
        layout.addWidget(embed_group)

        # Test connection
        test_row = QHBoxLayout()
        self._btn_test = QPushButton(t("settings.test_connection"))
        self._btn_test.clicked.connect(self._on_test_connection)
        test_row.addWidget(self._btn_test)

        self._test_status = QLabel("")
        test_row.addWidget(self._test_status)
        test_row.addStretch()
        layout.addLayout(test_row)

        # Language
        lang_group = QGroupBox(t("settings.ui_group"))
        lang_form = QFormLayout(lang_group)
        self._lang_combo = QComboBox()
        for code, name in SUPPORTED_LANGUAGES.items():
            self._lang_combo.addItem(name, code)
        lang_form.addRow(t("settings.language"), self._lang_combo)
        layout.addWidget(lang_group)

        # Save button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_save = QPushButton(t("save"))
        btn_save.setFixedWidth(120)
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        layout.addStretch()

    def _load_settings(self) -> None:
        if self._app_settings is None:
            return

        llm = self._app_settings.get_llm_config()
        self._llm_base_url.setText(str(llm.get("base_url", "")))
        self._llm_api_key.setText(str(llm.get("api_key", "")))
        self._llm_model.setText(str(llm.get("model", "")))
        self._llm_temperature.setValue(float(llm.get("temperature", 0.7)))
        self._llm_max_tokens.setValue(int(llm.get("max_tokens", 4096)))

        embed = self._app_settings.get_embedding_config()
        self._embed_model.setText(str(embed.get("model", "")))
        idx = self._embed_backend.findText(str(embed.get("backend", "local")))
        if idx >= 0:
            self._embed_backend.setCurrentIndex(idx)

        lang = self._app_settings.get_ui_settings().get("language", "en")
        lang_idx = self._lang_combo.findData(lang)
        if lang_idx >= 0:
            self._lang_combo.setCurrentIndex(lang_idx)

    def _on_save(self) -> None:
        if self._app_settings is None:
            return

        self._app_settings.set_llm_config(
            {
                "base_url": self._llm_base_url.text().strip(),
                "api_key": self._llm_api_key.text(),
                "model": self._llm_model.text().strip(),
                "temperature": self._llm_temperature.value(),
                "max_tokens": self._llm_max_tokens.value(),
            }
        )
        self._app_settings.set_embedding_config(
            {
                "model": self._embed_model.text().strip(),
                "backend": self._embed_backend.currentText(),
            }
        )
        lang_code = self._lang_combo.currentData()
        if lang_code:
            self._app_settings.set_ui_settings({"language": lang_code})

        self.settings_saved.emit()

    def _on_test_connection(self) -> None:
        if self._worker and self._worker.isRunning():
            return

        self._test_status.setText(t("settings.testing"))
        self._btn_test.setEnabled(False)

        self._worker = _ConnectionTestWorker(
            base_url=self._llm_base_url.text().strip(),
            api_key=self._llm_api_key.text(),
            model=self._llm_model.text().strip(),
            parent=self,
        )
        self._worker.finished.connect(self._on_test_result)
        self._worker.start()

    def _on_test_result(self, success: bool, message: str) -> None:
        self._btn_test.setEnabled(True)
        if success:
            self._test_status.setText(t("settings.test_ok", msg=message))
            self._test_status.setStyleSheet(f"color: {_C_DICT['success']};")
        else:
            self._test_status.setText(t("settings.test_failed", msg=message))
            self._test_status.setStyleSheet(f"color: {_C_DICT['error']};")
