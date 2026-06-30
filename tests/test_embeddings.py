"""Tests for ansys_material_db.data.embeddings."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from ansys_material_db.data.embeddings import EmbeddingService


class TestCosineSimilarity:
    """Test cosine similarity calculations."""

    def test_cosine_similarity_identical(self):
        vec = [1.0, 0.0, 0.0]
        sim = EmbeddingService.cosine_similarity(vec, vec)
        assert abs(sim - 1.0) < 1e-6

    def test_cosine_similarity_different(self):
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        sim = EmbeddingService.cosine_similarity(a, b)
        assert abs(sim) < 1e-6

    def test_cosine_similarity_opposite(self):
        a = [1.0, 0.0, 0.0]
        b = [-1.0, 0.0, 0.0]
        sim = EmbeddingService.cosine_similarity(a, b)
        assert abs(sim - (-1.0)) < 1e-6

    def test_cosine_similarity_zero_vector(self):
        a = [0.0, 0.0, 0.0]
        b = [1.0, 0.0, 0.0]
        sim = EmbeddingService.cosine_similarity(a, b)
        assert sim == 0.0


class TestEmbedTextDimension:
    """Test embedding dimension (MiniLM returns 384)."""

    def test_embed_text_dimension(self):
        svc = EmbeddingService()
        # Mock the SentenceTransformer to avoid loading the real model
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_embedding = np.random.rand(384).astype(np.float32)
        mock_model.encode.return_value = mock_embedding
        svc._model = mock_model
        vec = svc.embed_text("thermal conductivity of copper")
        assert len(vec) == 384
        mock_model.encode.assert_called_once()

    def test_embed_batch(self):
        svc = EmbeddingService()
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        embeddings = [np.random.rand(384).astype(np.float32) for _ in range(3)]
        mock_model.encode.return_value = np.array(embeddings)
        svc._model = mock_model
        results = svc.embed_batch(["steel", "aluminum", "titanium"])
        assert len(results) == 3
        assert all(len(v) == 384 for v in results)

    def test_embed_batch_empty(self):
        svc = EmbeddingService()
        results = svc.embed_batch([])
        assert results == []