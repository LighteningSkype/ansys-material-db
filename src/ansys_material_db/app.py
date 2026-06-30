"""QApplication setup, backend initialization, and startup."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _get_database_path(args: argparse.Namespace) -> str:
    """Determine the database file path."""
    if args.database:
        return args.database

    app_dir = Path(os.environ.get("APPDATA", Path.home())) / "AnsysMaterialDB"
    app_dir.mkdir(parents=True, exist_ok=True)
    return str(app_dir / "materials.db")


def run(args: argparse.Namespace) -> int:
    """Launch the Qt application with full backend wiring."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName("Ansys Material Database")
    app.setApplicationVersion("0.1.0")

    # Initialize backend
    from ansys_material_db.data.database import SQLiteManager
    from ansys_material_db.data.embeddings import EmbeddingService
    from ansys_material_db.data.llm_client import LLMClient
    from ansys_material_db.core.document_parser import DocumentParser
    from ansys_material_db.core.knowledge_base import KnowledgeBaseManager
    from ansys_material_db.core.property_extractor import PropertyExtractor
    from ansys_material_db.core.qa_engine import QAEngine
    from ansys_material_db.config.settings import AppSettings

    db_path = _get_database_path(args)
    database = SQLiteManager(db_path)
    app_settings = AppSettings(database)

    # Initialize embedding service (lazy-loaded)
    emb_config = app_settings.get_embedding_config()
    embedding_service = EmbeddingService(
        model_name=emb_config.get("model", "all-MiniLM-L6-v2"),
        backend=emb_config.get("backend", "local"),
    )

    # Initialize document parser
    document_parser = DocumentParser()

    # Initialize knowledge base
    knowledge_base = KnowledgeBaseManager(
        database=database,
        document_parser=document_parser,
        embedding_service=embedding_service,
    )

    # Initialize LLM client (if configured)
    llm_config = app_settings.get_llm_config()
    llm_client = None
    property_extractor = None
    qa_engine = None

    if llm_config.get("base_url") and llm_config.get("api_key"):
        llm_client = LLMClient(
            base_url=llm_config["base_url"],
            api_key=llm_config["api_key"],
            model=llm_config.get("model", "gpt-3.5-turbo"),
            temperature=llm_config.get("temperature", 0.3),
            max_tokens=llm_config.get("max_tokens", 4096),
        )
        # Wire LLM client to embedding service for API-based embeddings
        embedding_service.set_llm_client(llm_client)
        property_extractor = PropertyExtractor(llm_client)
        qa_engine = QAEngine(
            llm_client=llm_client,
            embedding_service=embedding_service,
            database=database,
        )

    # Create and show main window
    from ansys_material_db.gui.main_window import MainWindow

    window = MainWindow()
    window.init_backend(
        database=database,
        knowledge_base=knowledge_base,
        llm_client=llm_client,
        embedding_service=embedding_service,
        property_extractor=property_extractor,
        qa_engine=qa_engine,
        app_settings=app_settings,
    )
    window.show()

    exit_code = app.exec()

    # Cleanup
    database.close()
    return exit_code
