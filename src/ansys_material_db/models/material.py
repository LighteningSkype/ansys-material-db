"""Material, MaterialProperty, and TemperaturePoint data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TemperaturePoint:
    """A single (temperature, value) pair for temperature-dependent properties."""

    temperature: float  # in Celsius
    value: float

    def to_dict(self) -> dict[str, Any]:
        return {"temperature": self.temperature, "value": self.value}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TemperaturePoint:
        return cls(temperature=float(data["temperature"]), value=float(data["value"]))


@dataclass
class MaterialProperty:
    """A single physical property of a material."""

    name: str  # e.g. "thermal_conductivity"
    display_name: str  # e.g. "Thermal Conductivity"
    value: Optional[float] = None
    unit: str = ""
    source: str = ""  # which document/page extracted from
    temperature_table: list[TemperaturePoint] = field(default_factory=list)
    is_temp_dependent: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "value": self.value,
            "unit": self.unit,
            "source": self.source,
            "temperature_table": [tp.to_dict() for tp in self.temperature_table],
            "is_temp_dependent": self.is_temp_dependent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MaterialProperty:
        return cls(
            name=data["name"],
            display_name=data["display_name"],
            value=data.get("value"),
            unit=data.get("unit", ""),
            source=data.get("source", ""),
            temperature_table=[
                TemperaturePoint.from_dict(tp) for tp in data.get("temperature_table", [])
            ],
            is_temp_dependent=data.get("is_temp_dependent", False),
        )


@dataclass
class Material:
    """A complete material record with all its properties."""

    id: Optional[int] = None
    name: str = ""
    category: str = ""  # e.g. "Metal", "Polymer", "Ceramic"
    supplier: str = ""
    product_name: str = ""  # supplier product name/model
    description: str = ""
    properties: list[MaterialProperty] = field(default_factory=list)
    source_document_id: Optional[int] = None
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "supplier": self.supplier,
            "product_name": self.product_name,
            "description": self.description,
            "properties": [p.to_dict() for p in self.properties],
            "source_document_id": self.source_document_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Material:
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            category=data.get("category", ""),
            supplier=data.get("supplier", ""),
            product_name=data.get("product_name", ""),
            description=data.get("description", ""),
            properties=[MaterialProperty.from_dict(p) for p in data.get("properties", [])],
            source_document_id=data.get("source_document_id"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


THERMAL_PROPERTIES: dict[str, dict[str, str]] = {
    "density": {"display": "Density", "unit": "kg/m^3"},
    "thermal_conductivity": {"display": "Thermal Conductivity", "unit": "W/(m*K)"},
    "specific_heat": {"display": "Specific Heat Capacity", "unit": "J/(kg*K)"},
    "thermal_expansion": {"display": "Thermal Expansion Coefficient", "unit": "1/K"},
    "poisson_ratio": {"display": "Poisson's Ratio", "unit": ""},
    "emissivity": {"display": "Emissivity", "unit": ""},
    "melting_point": {"display": "Melting Point", "unit": "C"},
    "thermal_diffusivity": {"display": "Thermal Diffusivity", "unit": "m^2/s"},
}
