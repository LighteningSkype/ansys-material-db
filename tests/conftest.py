"""Shared fixtures for the test suite."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from ansys_material_db.data.database import SQLiteManager
from ansys_material_db.models.material import Material, MaterialProperty, TemperaturePoint, THERMAL_PROPERTIES
from ansys_material_db.models.document import Document, TextChunk


@pytest.fixture
def tmp_db():
    """Provide a SQLiteManager backed by a temporary file, closed after the test."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    manager = SQLiteManager(db_path=path)
    yield manager
    manager.close()
    os.unlink(path)


@pytest.fixture
def sample_material():
    """Return a Material with all THERMAL_PROPERTIES filled."""
    props = []
    for key, meta in THERMAL_PROPERTIES.items():
        if key == "emissivity":
            props.append(MaterialProperty(
                name=key,
                display_name=meta["display"],
                value=0.85,
                unit=meta["unit"],
                source="test_data.pdf",
            ))
        elif key == "melting_point":
            props.append(MaterialProperty(
                name=key,
                display_name=meta["display"],
                value=1085.0,
                unit=meta["unit"],
                source="test_data.pdf",
            ))
        else:
            props.append(MaterialProperty(
                name=key,
                display_name=meta["display"],
                value=100.0,
                unit=meta["unit"],
                source="test_data.pdf",
            ))

    return Material(
        name="Test Copper",
        category="Metal",
        supplier="TestSupplier",
        product_name="Copper-C11000",
        description="Test material",
        properties=props,
    )


@pytest.fixture
def sample_document():
    """Return a Document object."""
    return Document(
        filename="test_datasheet.pdf",
        file_path="/tmp/test_datasheet.pdf",
        file_type="pdf",
        page_count=3,
        status="completed",
        text_content="This is sample thermal property data.",
    )


@pytest.fixture
def sample_chunks():
    """Return a list of TextChunk objects."""
    return [
        TextChunk(
            chunk_index=0,
            page_number=1,
            text="Thermal conductivity of copper is 385 W/(m*K) at room temperature.",
            source_file="test.pdf",
        ),
        TextChunk(
            chunk_index=1,
            page_number=1,
            text="Density of copper is 8960 kg/m^3.",
            source_file="test.pdf",
        ),
        TextChunk(
            chunk_index=2,
            page_number=2,
            text="Melting point of copper is 1085 degrees Celsius.",
            source_file="test.pdf",
        ),
    ]


@pytest.fixture
def mock_llm_response():
    """Return a sample JSON response string for property extraction."""
    return json.dumps([
        {
            "name": "Copper C11000",
            "category": "Metal",
            "properties": [
                {
                    "name": "thermal_conductivity",
                    "display_name": "Thermal Conductivity",
                    "value": 385.0,
                    "unit": "W/(m*K)",
                },
                {
                    "name": "density",
                    "display_name": "Density",
                    "value": 8960.0,
                    "unit": "kg/m^3",
                },
            ],
        }
    ])