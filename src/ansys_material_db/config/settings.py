"""Application settings management backed by the SQLite app_settings table."""

from __future__ import annotations

import json
from typing import Any

from ansys_material_db.data.database import SQLiteManager

# Default values for all configuration groups.
_DEFAULT_LLM: dict[str, Any] = {
    "base_url": "https://api.openai.com/v1",
    "api_key": "",
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 4096,
}

_DEFAULT_EMBEDDING: dict[str, Any] = {
    "model": "text-embedding-ada-002",
    "backend": "local",
}

_DEFAULT_UI: dict[str, Any] = {
    "theme": "dark",
    "language": "en",
}


def _prefix(ns: str, key: str) -> str:
    return f"{ns}.{key}"


class AppSettings:
    """Thin facade over :class:`SQLiteManager` for reading / writing app settings.

    Each settings group is stored as individual key/value rows in the
    ``app_settings`` table using a ``<group>.<key>`` naming convention.

    Example::

        settings = AppSettings(database)
        settings.set_llm_config({"base_url": "http://localhost:11434/v1"})
        cfg = settings.get_llm_config()
    """

    def __init__(self, database: SQLiteManager) -> None:
        self._db = database

    # ------------------------------------------------------------------
    # LLM Configuration
    # ------------------------------------------------------------------

    def get_llm_config(self) -> dict[str, Any]:
        """Return the current LLM configuration, falling back to defaults."""
        return self._get_group("llm", _DEFAULT_LLM)

    def set_llm_config(self, config: dict[str, Any]) -> None:
        """Persist LLM configuration values."""
        self._set_group("llm", _DEFAULT_LLM, config)

    # ------------------------------------------------------------------
    # Embedding Configuration
    # ------------------------------------------------------------------

    def get_embedding_config(self) -> dict[str, Any]:
        """Return the current embedding configuration."""
        return self._get_group("embedding", _DEFAULT_EMBEDDING)

    def set_embedding_config(self, config: dict[str, Any]) -> None:
        """Persist embedding configuration values."""
        self._set_group("embedding", _DEFAULT_EMBEDDING, config)

    # ------------------------------------------------------------------
    # UI Settings
    # ------------------------------------------------------------------

    def get_ui_settings(self) -> dict[str, Any]:
        """Return the current UI settings."""
        return self._get_group("ui", _DEFAULT_UI)

    def set_ui_settings(self, config: dict[str, Any]) -> None:
        """Persist UI settings values."""
        self._set_group("ui", _DEFAULT_UI, config)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_group(self, ns: str, defaults: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, default_val in defaults.items():
            raw = self._db.get_setting(_prefix(ns, key))
            if raw is None:
                result[key] = default_val
            else:
                result[key] = self._deserialize(raw, default_val)
        return result

    def _set_group(self, ns: str, defaults: dict[str, Any], values: dict[str, Any]) -> None:
        for key in defaults:
            if key in values:
                self._db.set_setting(_prefix(ns, key), self._serialize(values[key]))

    @staticmethod
    def _serialize(value: Any) -> str:
        if isinstance(value, str):
            return value
        return json.dumps(value)

    @staticmethod
    def _deserialize(raw: str, default_val: Any) -> Any:
        if isinstance(default_val, str):
            return raw
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return default_val
