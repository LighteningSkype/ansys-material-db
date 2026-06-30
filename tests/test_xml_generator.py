"""Tests for ansys_material_db.core.xml_generator (Ansys 2021 R1 schema)."""

from __future__ import annotations

import os
import tempfile

import pytest

from ansys_material_db.core.xml_generator import XMLGenerator
from ansys_material_db.models.material import Material, MaterialProperty, TemperaturePoint


@pytest.fixture
def generator():
    return XMLGenerator()


@pytest.fixture
def simple_material():
    return Material(
        name="Copper C11000",
        category="Metal",
        description="Thermal Properties for Copper C11000",
        properties=[
            MaterialProperty(
                name="thermal_conductivity",
                display_name="Thermal Conductivity",
                value=385.0,
                unit="W/(m*K)",
            ),
            MaterialProperty(
                name="density",
                display_name="Density",
                value=8960.0,
                unit="kg/m^3",
            ),
            MaterialProperty(
                name="specific_heat",
                display_name="Specific Heat Capacity",
                value=385.0,
                unit="J/(kg*K)",
            ),
        ],
    )


@pytest.fixture
def temp_dependent_material():
    return Material(
        name="Steel AISI 304",
        category="Metal",
        description="Thermal Properties for Steel AISI 304",
        properties=[
            MaterialProperty(
                name="thermal_conductivity",
                display_name="Thermal Conductivity",
                is_temp_dependent=True,
                temperature_table=[
                    TemperaturePoint(temperature=25.0, value=16.2),
                    TemperaturePoint(temperature=100.0, value=17.3),
                    TemperaturePoint(temperature=500.0, value=23.8),
                ],
            ),
        ],
    )


class TestXMLGeneration:
    def test_generate_single_material(self, generator: XMLGenerator, simple_material: Material):
        xml = generator.generate([simple_material])
        assert '<?xml version="1.0" encoding="UTF-8"?>' in xml
        assert '<EngineeringData version="21.1.0.231"' in xml
        assert "<Materials>" in xml
        assert "<MatML_Doc>" in xml
        assert "<Material>" in xml
        assert "Copper C11000" in xml
        assert "Metal" in xml
        assert ">385.0<" in xml
        assert ">8960.0<" in xml

    def test_generate_multiple_materials(self, generator: XMLGenerator):
        mat1 = Material(
            name="Copper",
            category="Metal",
            properties=[
                MaterialProperty(name="thermal_conductivity", display_name="Thermal Conductivity", value=385.0),
            ],
        )
        mat2 = Material(
            name="Aluminum",
            category="Metal",
            properties=[
                MaterialProperty(name="thermal_conductivity", display_name="Thermal Conductivity", value=237.0),
            ],
        )
        xml = generator.generate([mat1, mat2])
        assert "Copper" in xml
        assert "Aluminum" in xml
        # Both materials should be inside MatML_Doc
        assert xml.count("<Material>") == 2

    def test_temperature_dependent_properties(self, generator: XMLGenerator, temp_dependent_material: Material):
        xml = generator.generate([temp_dependent_material])
        assert "<PropertyData" in xml
        assert 'property="pr0"' in xml
        assert ">16.2<" in xml
        assert ">23.8<" in xml

    def test_generate_includes_metadata(self, generator: XMLGenerator, simple_material: Material):
        xml = generator.generate([simple_material])
        assert "<Metadata>" in xml
        assert 'id="pr0"' in xml
        assert 'id="pr1"' in xml
        assert 'id="pr2"' in xml
        assert 'id="pa0"' in xml
        assert 'id="pa1"' in xml
        assert 'id="pa2"' in xml

    def test_generate_includes_color(self, generator: XMLGenerator, simple_material: Material):
        xml = generator.generate([simple_material])
        assert 'property="pr4"' in xml
        assert 'parameter="pa5"' in xml
        assert 'parameter="pa6"' in xml
        assert 'parameter="pa7"' in xml

    def test_generate_includes_guid(self, generator: XMLGenerator, simple_material: Material):
        xml = generator.generate([simple_material])
        assert 'property="pr3"' in xml
        assert 'name="guid"' in xml

    def test_generate_includes_relative_permeability(self, generator: XMLGenerator, simple_material: Material):
        xml = generator.generate([simple_material])
        assert 'property="pr5"' in xml

    def test_generate_material_has_glossary(self, generator: XMLGenerator, simple_material: Material):
        xml = generator.generate([simple_material])
        assert "<Glossary>" in xml
        assert "<Term>" in xml
        assert "<BulkDetails>" in xml


class TestXMLValidation:
    def test_validate_valid_xml(self, generator: XMLGenerator, simple_material: Material):
        xml = generator.generate([simple_material])
        valid, errors = generator.validate(xml)
        assert valid is True
        assert errors == []

    def test_validate_invalid_root(self, generator: XMLGenerator):
        valid, errors = generator.validate("<invalid>not ansys xml</invalid>")
        assert valid is False
        assert any("EngineeringData" in e for e in errors)

    def test_validate_wrong_version(self, generator: XMLGenerator, simple_material: Material):
        xml = generator.generate([simple_material])
        xml = xml.replace("21.1.0.231", "20.0.0.000")
        valid, errors = generator.validate(xml)
        assert valid is False
        assert any("version" in e.lower() for e in errors)

    def test_validate_no_materials(self, generator: XMLGenerator):
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<EngineeringData version="21.1.0.231"><Notes></Notes><Materials><MatML_Doc></MatML_Doc></Materials></EngineeringData>'
        valid, errors = generator.validate(xml)
        assert valid is False
        assert any("Material" in e for e in errors)


class TestXMLRoundTrip:
    def test_parse_constant_properties(self, generator: XMLGenerator, simple_material: Material):
        xml = generator.generate([simple_material])
        with tempfile.NamedTemporaryFile(suffix=".xml", mode="w", delete=False, encoding="utf-8") as f:
            f.write(xml)
            path = f.name
        try:
            materials = generator.parse_ansys_xml(path)
            assert len(materials) == 1
            mat = materials[0]
            assert mat.name == simple_material.name
            assert mat.category == simple_material.category
            tc_map = {p.name: p.value for p in mat.properties}
            assert tc_map.get("thermal_conductivity") == 385.0
            assert tc_map.get("density") == 8960.0
            assert tc_map.get("specific_heat") == 385.0
        finally:
            os.unlink(path)

    def test_parse_temperature_dependent(self, generator: XMLGenerator, temp_dependent_material: Material):
        xml = generator.generate([temp_dependent_material])
        with tempfile.NamedTemporaryFile(suffix=".xml", mode="w", delete=False, encoding="utf-8") as f:
            f.write(xml)
            path = f.name
        try:
            materials = generator.parse_ansys_xml(path)
            assert len(materials) == 1
            mat = materials[0]
            assert mat.name == "Steel AISI 304"
            tc = [p for p in mat.properties if p.name == "thermal_conductivity"][0]
            assert tc.is_temp_dependent is True
            assert len(tc.temperature_table) == 3
            assert tc.temperature_table[0].temperature == 25.0
            assert tc.temperature_table[0].value == 16.2
        finally:
            os.unlink(path)

    def test_parse_string(self, generator: XMLGenerator, simple_material: Material):
        xml = generator.generate([simple_material])
        materials = generator.parse_ansys_xml_string(xml)
        assert len(materials) == 1
        assert materials[0].name == simple_material.name

    def test_parse_string_empty(self, generator: XMLGenerator):
        assert generator.parse_ansys_xml_string("") == []
        assert generator.parse_ansys_xml_string("   ") == []


class TestXMLStructure:
    def test_xml_schema_elements(self, generator: XMLGenerator, simple_material: Material):
        xml = generator.generate([simple_material])
        # Verify core Ansys 2021 R1 schema elements are present
        for elem in [
            "<EngineeringData",
            "<Materials>",
            "<MatML_Doc>",
            "<Material>",
            "<Glossary>",
            "<BulkDetails>",
            "<PropertyData",
            "<ParameterDetails",
            "<PropertyDetails",
            "<Metadata>",
        ]:
            assert elem in xml, f"Missing element: {elem}"

    def test_constant_property_structure(self, generator: XMLGenerator, simple_material: Material):
        xml = generator.generate([simple_material])
        # Constant properties use the near-zero temperature trick
        assert "7.88860905221012e-31" in xml
        assert ">Interpolation Options<" in xml
        assert '>Linear Multivariate<' in xml
