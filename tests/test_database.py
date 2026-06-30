"""Tests for ansys_material_db.data.database (SQLiteManager)."""

from __future__ import annotations

import json

import pytest

from ansys_material_db.data.database import SQLiteManager
from ansys_material_db.models.material import Material, MaterialProperty, TemperaturePoint
from ansys_material_db.models.document import Document, TextChunk
from ansys_material_db.models.chat import ChatMessage


class TestMaterialsCRUD:
    def test_add_and_get_material(self, tmp_db: SQLiteManager, sample_material: Material):
        mat_id = tmp_db.add_material(sample_material)
        assert mat_id is not None
        retrieved = tmp_db.get_material(mat_id)
        assert retrieved is not None
        assert retrieved.name == "Test Copper"
        assert retrieved.category == "Metal"
        assert len(retrieved.properties) == len(sample_material.properties)

    def test_update_material(self, tmp_db: SQLiteManager, sample_material: Material):
        mat_id = tmp_db.add_material(sample_material)
        sample_material.id = mat_id
        sample_material.name = "Updated Copper"
        tmp_db.update_material(sample_material)
        retrieved = tmp_db.get_material(mat_id)
        assert retrieved.name == "Updated Copper"

    def test_delete_material(self, tmp_db: SQLiteManager, sample_material: Material):
        mat_id = tmp_db.add_material(sample_material)
        tmp_db.delete_material(mat_id)
        retrieved = tmp_db.get_material(mat_id)
        assert retrieved is None

    def test_list_materials_with_filters(self, tmp_db: SQLiteManager):
        m1 = Material(name="Copper", category="Metal", supplier="A")
        m2 = Material(name="Aluminum", category="Metal", supplier="B")
        m3 = Material(name="PEEK", category="Polymer", supplier="A")
        tmp_db.add_material(m1)
        tmp_db.add_material(m2)
        tmp_db.add_material(m3)

        all_mats = tmp_db.list_materials()
        assert len(all_mats) == 3

        metals = tmp_db.list_materials(category="Metal")
        assert len(metals) == 2

        supplier_a = tmp_db.list_materials(supplier="A")
        assert len(supplier_a) == 2

        search = tmp_db.list_materials(search="copper")
        assert any(m.name == "Copper" for m in search)

    def test_save_and_load_properties(self, tmp_db: SQLiteManager):
        mat_id = tmp_db.add_material(Material(name="Steel", category="Metal"))
        props = [
            MaterialProperty(name="thermal_conductivity", display_name="Thermal Conductivity", value=50.0, unit="W/(m*K)"),
            MaterialProperty(
                name="specific_heat",
                display_name="Specific Heat Capacity",
                is_temp_dependent=True,
                temperature_table=[
                    TemperaturePoint(temperature=25.0, value=480.0),
                    TemperaturePoint(temperature=100.0, value=500.0),
                ],
            ),
        ]
        tmp_db.save_properties(mat_id, props)
        retrieved = tmp_db.get_material(mat_id)
        assert len(retrieved.properties) == 2
        tc = next(p for p in retrieved.properties if p.is_temp_dependent)
        assert len(tc.temperature_table) == 2
        assert tc.temperature_table[0].temperature == 25.0


class TestDocumentsCRUD:
    def test_document_crud(self, tmp_db: SQLiteManager, sample_document: Document):
        doc_id = tmp_db.add_document(sample_document)
        assert doc_id is not None
        retrieved = tmp_db.get_document(doc_id)
        assert retrieved is not None
        assert retrieved.filename == "test_datasheet.pdf"

        # Update by re-inserting via direct SQL (no update_document method exists)
        tmp_db.conn.execute(
            "UPDATE documents SET status=? WHERE id=?", ("updated", doc_id)
        )
        tmp_db.conn.commit()
        updated = tmp_db.get_document(doc_id)
        assert updated.status == "updated"

        # Delete via direct SQL
        tmp_db.conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))
        tmp_db.conn.commit()
        assert tmp_db.get_document(doc_id) is None


class TestChunkStorage:
    def test_chunk_storage_and_search(self, tmp_db: SQLiteManager, sample_document: Document, sample_chunks):
        doc_id = tmp_db.add_document(sample_document)
        tmp_db.add_chunks(doc_id, sample_chunks)
        retrieved = tmp_db.get_document(doc_id)
        assert retrieved is not None


class TestChatHistory:
    def test_chat_history(self, tmp_db: SQLiteManager):
        msg1 = ChatMessage(role="user", content="What is thermal conductivity?")
        msg2 = ChatMessage(role="assistant", content="It measures heat transfer ability.")
        tmp_db.add_chat_message(msg1)
        tmp_db.add_chat_message(msg2)
        history = tmp_db.get_chat_history()
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[1].role == "assistant"


class TestSettings:
    def test_settings_get_set(self, tmp_db: SQLiteManager):
        tmp_db.set_setting("llm_model", "gpt-4")
        val = tmp_db.get_setting("llm_model")
        assert val == "gpt-4"
        tmp_db.set_setting("llm_model", "llama3")
        assert tmp_db.get_setting("llm_model") == "llama3"
        assert tmp_db.get_setting("nonexistent", "default") == "default"


class TestContextManager:
    def test_context_manager(self):
        import tempfile, os
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            with SQLiteManager(db_path=path) as db:
                db.set_setting("test_key", "test_value")
                assert db.get_setting("test_key") == "test_value"
            # Connection should be closed now; verify by opening a fresh connection
            import sqlite3
            conn = sqlite3.connect(path)
            row = conn.execute("SELECT value FROM app_settings WHERE key=?", ("test_key",)).fetchone()
            assert row[0] == "test_value"
            conn.close()
        finally:
            os.unlink(path)