"""Tests for ansys_material_db.core.qa_engine."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ansys_material_db.core.qa_engine import QAEngine
from ansys_material_db.models.document import TextChunk
from ansys_material_db.models.chat import ChatMessage


@pytest.fixture
def mock_llm():
    client = MagicMock()
    return client


@pytest.fixture
def mock_embeddings():
    svc = MagicMock()
    svc.embed = AsyncMock(return_value=[0.1] * 384)
    return svc


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.search_chunks_by_embedding = MagicMock(return_value=[])
    return db


@pytest.fixture
def sample_chunks_for_qa():
    chunks = [
        TextChunk(chunk_index=0, page_number=1, text="Thermal conductivity of copper is 385 W/(m*K)."),
        TextChunk(chunk_index=1, page_number=2, text="Density is 8960 kg/m^3."),
    ]
    chunks[0].source_file = "copper_datasheet.pdf"
    chunks[1].source_file = "copper_datasheet.pdf"
    return chunks


class TestBuildContext:
    def test_build_context(self, sample_chunks_for_qa):
        engine = QAEngine.__new__(QAEngine)
        engine._prompt_template = "test"
        context = engine._build_context("What is TC?", sample_chunks_for_qa)
        assert "copper_datasheet.pdf" in context
        assert "Page 1" in context
        assert "Page 2" in context
        assert "385" in context

    def test_build_context_empty(self):
        engine = QAEngine.__new__(QAEngine)
        engine._prompt_template = "test"
        context = engine._build_context("Q?", [])
        assert context == ""


class TestBuildQaPrompt:
    def test_build_qa_prompt(self):
        engine = QAEngine.__new__(QAEngine)
        engine._prompt_template = "Context:\n{context}\n\nQuestion:\n{question}"
        messages = engine._build_qa_prompt("What is TC?", "Some context about copper.")
        assert isinstance(messages, list)
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "What is TC?"
        system_content = messages[0]["content"]
        assert "Some context about copper." in system_content

    def test_build_qa_prompt_with_history(self):
        engine = QAEngine.__new__(QAEngine)
        engine._prompt_template = "Context:\n{context}\n\nQuestion:\n{question}"
        history = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi there!"),
        ]
        messages = engine._build_qa_prompt("Follow up?", "Context", history)
        # system + 2 history + 1 user = 4 messages
        assert len(messages) == 4
        assert messages[1]["content"] == "Hello"
        assert messages[2]["content"] == "Hi there!"

    def test_build_qa_prompt_truncates_long_history(self):
        engine = QAEngine.__new__(QAEngine)
        engine._prompt_template = "Context:\n{context}\n\nQuestion:\n{question}"
        history = [ChatMessage(role="user", content=f"msg{i}") for i in range(20)]
        messages = engine._build_qa_prompt("Q", "C", history)
        # system + 10 history + 1 user = 12 messages
        assert len(messages) == 12


from unittest.mock import AsyncMock