"""Settings dialog for LLM and embedding configuration."""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
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
from ansys_material_db.gui.styles import get_ansys_stylesheet


class _ConnectionTestWorker(QThread):
    """Background thread that attempts a lightweight API call to verify connectivity."""

    finished = pyqtSignal(bool, str)  # (success, message)

    def __init__(self, base_url: str, api_key: str, model: str, parent: QWidget | None = None) -> None:
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
                    self.finished.emit(True, f"Connected successfully (HTTP {resp.status})")
                    return
                self.finished.emit(False, f"Unexpected status: {resp.status}")
        except urllib.error.HTTPError as exc:
            self.finished.emit(False, f"HTTP {exc.code}: {exc.reason}")
        except Exception as exc:
            self.finished.emit(False, f"Connection failed: {exc}")


class SettingsDialog(QDialog):
    settings_saved = pyqtSignal()
    """Modal dialog for editing LLM, embedding, and UI settings."""

    def __init__(self, app_settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._app_settings = app_settings
        self._worker: _ConnectionTestWorker | None = None
        self.setWindowTitle(t("settings.title"))
        self.setMinimumWidth(520)
        self._build_ui()
        self._load_settings()
        self.setStyleSheet(get_ansys_stylesheet())

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)

        # -- LLM Configuration --
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

        root_layout.addWidget(llm_group)

        # -- Embedding Configuration --
        embed_group = QGroupBox(t("settings.embed_group"))
        embed_form = QFormLayout(embed_group)

        self._embed_model = QLineEdit()
        self._embed_model.setPlaceholderText("all-MiniLM-L6-v2")
        embed_form.addRow(t("settings.embed_model"), self._embed_model)

        self._embed_backend = QComboBox()
        self._embed_backend.addItems(["local", "openai"])
        self._embed_backend.setCurrentIndex(0)  # default to local
        embed_form.addRow(t("settings.embed_backend"), self._embed_backend)

        root_layout.addWidget(embed_group)

        # -- Test Connection --
        test_row = QHBoxLayout()
        self._btn_test = QPushButton(t("settings.test_connection"))
        test_row.addWidget(self._btn_test)
        self._test_status_label = QLabel("")
        test_row.addWidget(self._test_status_label)
        test_row.addStretch()
        root_layout.addLayout(test_row)

        # -- Interface Language --
        lang_group = QGroupBox(t("settings.ui_group"))
        lang_form = QFormLayout(lang_group)
        self._lang_combo = QComboBox()
        for code, name in SUPPORTED_LANGUAGES.items():
            self._lang_combo.addItem(name, code)
        lang_form.addRow(t("settings.language"), self._lang_combo)
        root_layout.addWidget(lang_group)

        # -- Save / Cancel --
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.accepted.connect(self._on_save)
        self._button_box.rejected.connect(self.reject)
        root_layout.addWidget(self._button_box)

        # Connect test button
        self._btn_test.clicked.connect(self._on_test_connection)

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------

    def _load_settings(self) -> None:
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
        self._app_settings.set_llm_config({
            "base_url": self._llm_base_url.text().strip(),
            "api_key": self._llm_api_key.text(),
            "model": self._llm_model.text().strip(),
            "temperature": self._llm_temperature.value(),
            "max_tokens": self._llm_max_tokens.value(),
        })
        self._app_settings.set_embedding_config({
            "model": self._embed_model.text().strip(),
            "backend": self._embed_backend.currentText(),
        })
        lang_code = self._lang_combo.currentData()
        if lang_code:
            self._app_settings.set_ui_settings({"language": lang_code})
        self.settings_saved.emit()
        self.accept()

    # ------------------------------------------------------------------
    # Connection test
    # ------------------------------------------------------------------

    def _on_test_connection(self) -> None:
        if self._worker and self._worker.isRunning():
            return

        self._test_status_label.setText(t("settings.testing"))
        self._test_status_label.setStyleSheet("")
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
            self._test_status_label.setText(t("settings.test_ok", msg=message))
            self._test_status_label.setStyleSheet("color: #4caf50;")
        else:
            self._test_status_label.setText(t("settings.test_failed", msg=message))
            self._test_status_label.setStyleSheet("color: #f44336;")
