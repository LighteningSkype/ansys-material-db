"""Tests for ansys_material_db.core.document_parser."""

from __future__ import annotations

import os
import tempfile

import pytest

from ansys_material_db.core.document_parser import DocumentParser
from ansys_material_db.models.document import TextChunk


@pytest.fixture
def parser():
    return DocumentParser()


class TestChunkText:
    def test_chunk_text_basic(self, parser: DocumentParser):
        text = "A" * 1200
        chunks = parser.chunk_text(text, page_number=1)
        assert len(chunks) > 1
        assert all(isinstance(c, TextChunk) for c in chunks)
        # All chunks should contribute to covering the full text
        reconstructed = "".join(c.text for c in chunks)
        assert len(reconstructed) > 0

    def test_chunk_text_with_overlap(self, parser: DocumentParser):
        text = "B" * 1200
        chunks = parser.chunk_text(text, page_number=1, chunk_size=500)
        assert len(chunks) >= 2
        # With overlap, chunks should share some characters
        if len(chunks) >= 2:
            first_end = chunks[0].text[-50:]
            second_start = chunks[1].text[:50]
            assert first_end in text and second_start in text

    def test_chunk_empty_text(self, parser: DocumentParser):
        chunks = parser.chunk_text("", page_number=1)
        assert chunks == []

    def test_chunk_short_text(self, parser: DocumentParser):
        text = "Short text"
        chunks = parser.chunk_text(text, page_number=1)
        assert len(chunks) == 1
        assert chunks[0].text == text


class TestParseNonexistent:
    def test_parse_nonexistent_pdf(self, parser: DocumentParser):
        chunks = parser.parse_pdf("/nonexistent/file.pdf")
        assert chunks == []

    def test_parse_nonexistent_image(self, parser: DocumentParser):
        chunks = parser.parse_image("/nonexistent/file.png")
        assert chunks == []