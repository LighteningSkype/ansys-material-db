"""Tests for ansys_material_db.core.property_extractor."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ansys_material_db.core.property_extractor import PropertyExtractor
from ansys_material_db.models.material import Material


class MockLLMClient:
    """Minimal mock LLM client with a `chat` method."""

    def __init__(self, response_text: str = "") -> None:
        self._response = response_text

    async def chat(self, messages: list[dict[str, str]]) -> str:
        return self._response


@pytest.fixture
def extractor():
    return PropertyExtractor(llm_client=MagicMock())


class TestParseLLMResponse:
    def test_parse_valid_json(self, extractor: PropertyExtractor, mock_llm_response: str):
        materials = extractor._parse_llm_response(mock_llm_response)
        assert len(materials) == 1
        mat = materials[0]
        assert mat.name == "Copper C11000"
        assert mat.category == "Metal"
        assert len(mat.properties) == 2
        tc = next(p for p in mat.properties if p.name == "thermal_conductivity")
        assert tc.value == 385.0

    def test_parse_json_in_markdown_fences(self, extractor: PropertyExtractor, mock_llm_response: str):
        fenced = f"Here is the extracted data:\n```json\n{mock_llm_response}\n```\nDone."
        materials = extractor._parse_llm_response(fenced)
        assert len(materials) == 1
        assert materials[0].name == "Copper C11000"

    def test_parse_malformed_response(self, extractor: PropertyExtractor):
        # Completely garbled text
        result = extractor._parse_llm_response("this is not json at all")
        assert result == []

    def test_parse_empty_response(self, extractor: PropertyExtractor):
        result = extractor._parse_llm_response("")
        assert result == []


class TestBuildExtractionPrompt:
    def test_build_extraction_prompt(self, extractor: PropertyExtractor):
        text = "Copper thermal conductivity: 385 W/(m*K)"
        prompt = extractor._build_extraction_prompt(text)
        assert text in prompt
        assert len(prompt) > 10


class TestExtractFromText:
    @pytest.mark.asyncio
    async def test_extract_from_text(self, mock_llm_response: str):
        mock_client = MockLLMClient(response_text=mock_llm_response)
        extractor = PropertyExtractor(llm_client=mock_client)
        materials = await extractor.extract_from_text("Copper thermal data...")
        assert len(materials) == 1
        assert materials[0].name == "Copper C11000"

    @pytest.mark.asyncio
    async def test_extract_empty_text(self):
        mock_client = MockLLMClient(response_text="")
        extractor = PropertyExtractor(llm_client=mock_client)
        materials = await extractor.extract_from_text("")
        assert materials == []