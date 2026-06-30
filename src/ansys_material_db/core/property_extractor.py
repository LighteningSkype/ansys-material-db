"""LLM-based property extraction engine."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional

from ansys_material_db.data.llm_client import LLMClient
from ansys_material_db.models.material import (
    Material,
    MaterialProperty,
    TemperaturePoint,
    THERMAL_PROPERTIES,
)
from ansys_material_db.models.document import TextChunk

logger = logging.getLogger(__name__)

_PROMPT_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "prompts"
    / "property_extraction.txt"
)


class PropertyExtractor:
    """Extract structured material data from free text using an LLM."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm = llm_client
        self._prompt_template = self._load_prompt_template()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def extract_from_text(self, text: str) -> list[Material]:
        """Extract materials directly from a plain-text string."""
        if not text or not text.strip():
            return []

        prompt = self._build_extraction_prompt(text)
        response = await self._llm.chat([{"role": "user", "content": prompt}])
        materials = self._parse_llm_response(response)
        for mat in materials:
            self._ensure_required_properties(mat)
        return materials

    async def extract_from_chunks(self, chunks: list[TextChunk]) -> list[Material]:
        """Extract materials from a list of text chunks.

        Each chunk is processed individually; duplicate materials are
        merged by name (properties are combined, non-empty fields win).
        """
        if not chunks:
            return []

        all_materials: dict[str, Material] = {}

        for chunk in chunks:
            if not chunk.text.strip():
                continue
            extracted = await self.extract_from_text(chunk.text)
            for mat in extracted:
                key = mat.name.lower().strip()
                if key in all_materials:
                    all_materials[key] = self._merge_materials(
                        all_materials[key], mat
                    )
                else:
                    all_materials[key] = mat

        return list(all_materials.values())


    async def extract_from_image(self, image_paths: list[str]) -> list[Material]:
        """Extract materials directly from image files using multimodal LLM.

        Sends the images directly to a vision-capable LLM with an
        extraction prompt, then parses the JSON response.
        """
        if not image_paths:
            return []

        prompt = self._load_image_prompt_template()

        try:
            response = await self._llm.chat_multimodal(prompt, image_paths)
        except Exception:
            logger.exception("Multimodal extraction failed")
            return []

        materials = self._parse_llm_response(response)
        for mat in materials:
            self._ensure_required_properties(mat)
        return materials

    def _load_image_prompt_template(self) -> str:
        """Load or default the image extraction prompt."""
        img_prompt_path = _PROMPT_TEMPLATE_PATH.parent / "image_property_extraction.txt"
        try:
            return img_prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return (
                "You are a material science expert. Look at this image of a material "
                "product manual or datasheet and extract all material specifications."
                "\n\n"
                "For each material found, return a JSON array of objects with these fields:\n"
                '  - "name": material name/designation\n'
                '  - "category": material category (Metal, Ceramic, Polymer, Composite, Other)\n'
                '  - "supplier": manufacturer or supplier name\n'
                '  - "properties": list of property objects with:\n'
                '    - "name": property key (one of: density, thermal_conductivity,'
                ' specific_heat, thermal_expansion, poisson_ratio)\n'
                '    - "value": numeric value (set to 0 if not found)\n'
                '    - "unit": SI unit string\n\n'
                "Return ONLY the JSON array, no other text.\n"
                'Example: [{"name": "Tungsten", "category": "Metal", '
                '"supplier": "Supplier Name", "properties": ['
                '{"name": "density", "value": 19300, "unit": "kg/m^3"}, '
                '{"name": "thermal_conductivity", "value": 174, "unit": "W/(m*K)"}]}]'
            )

    def _build_extraction_prompt(self, text: str) -> str:
        return self._prompt_template.replace("{text}", text)

    # ------------------------------------------------------------------
    # LLM response parsing
    # ------------------------------------------------------------------

    def _parse_llm_response(self, response: str) -> list[Material]:
        """Parse LLM output into Material objects with fallback strategies."""
        if not response or not response.strip():
            return []

        # Strategy 1: Direct JSON parse
        json_str = self._extract_json_block(response)
        materials = self._try_parse_json(json_str)
        if materials is not None:
            return materials

        # Strategy 2: Regex to find the outermost JSON array
        json_str = self._extract_json_array_regex(response)
        materials = self._try_parse_json(json_str)
        if materials is not None:
            return materials

        # Strategy 3: Try to fix common LLM JSON issues
        json_str = self._fix_common_json_issues(json_str)
        materials = self._try_parse_json(json_str)
        if materials is not None:
            return materials

        logger.warning("Failed to parse LLM response into materials")
        return []

    def _extract_json_block(self, text: str) -> str:
        """Extract content from ```json ... ``` fences."""
        pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()

    def _extract_json_array_regex(self, text: str) -> str:
        """Find the outermost JSON array using bracket matching."""
        start = text.find("[")
        if start == -1:
            return text
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "[":
                depth += 1
            elif text[i] == "]":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        return text

    def _fix_common_json_issues(self, text: str) -> str:
        """Attempt to repair common LLM JSON formatting problems."""
        # Remove trailing commas before ] or }
        fixed = re.sub(r",\s*([}\]])", r"\1", text)
        # Remove single-line comments
        fixed = re.sub(r"//.*$", "", fixed, flags=re.MULTILINE)
        # Remove control characters (except normal whitespace)
        fixed = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", fixed)
        return fixed

    def _try_parse_json(self, json_str: str) -> Optional[list[Material]]:
        """Try to parse a JSON string into Material objects."""
        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return None

        if not isinstance(data, list):
            return None

        materials = []
        for item in data:
            mat = self._dict_to_material(item)
            if mat is not None:
                materials.append(mat)
        return materials if materials else None

    def _dict_to_material(self, data: dict) -> Optional[Material]:
        """Convert a dictionary (from JSON) to a Material object."""
        if not isinstance(data, dict):
            return None

        name = data.get("name", "").strip()
        if not name:
            return None

        properties: list[MaterialProperty] = []
        for prop_data in data.get("properties", []):
            prop = self._dict_to_property(prop_data)
            if prop is not None:
                properties.append(prop)

        return Material(
            name=name,
            category=data.get("category", ""),
            supplier=data.get("supplier", ""),
            product_name=data.get("product_name", ""),
            description=data.get("description", ""),
            properties=properties,
        )

    def _dict_to_property(self, data: dict) -> Optional[MaterialProperty]:
        """Convert a dictionary to a MaterialProperty object."""
        if not isinstance(data, dict):
            return None

        name = data.get("name", "").strip()
        if not name:
            return None

        # Resolve display name and unit from registry if not provided
        meta = THERMAL_PROPERTIES.get(name, {})
        display_name = data.get("display_name") or meta.get("display", name)
        unit = data.get("unit") or meta.get("unit", "")

        is_temp_dependent = bool(data.get("is_temp_dependent", False))
        value = data.get("value")
        temperature_table: list[TemperaturePoint] = []

        if is_temp_dependent and data.get("temperature_table"):
            for tp in data["temperature_table"]:
                if isinstance(tp, dict):
                    temperature_table.append(
                        TemperaturePoint(
                            temperature=float(tp.get("temperature", 0)),
                            value=float(tp.get("value", 0)),
                        )
                    )

        # If temp-dependent, value should be None
        if is_temp_dependent:
            value = None
        elif value is not None:
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = None

        return MaterialProperty(
            name=name,
            display_name=display_name,
            value=value,
            unit=unit,
            source=data.get("source", ""),
            temperature_table=temperature_table,
            is_temp_dependent=is_temp_dependent,
        )

    # ------------------------------------------------------------------
    # Merging
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_required_properties(material: Material) -> None:
        """Ensure all 5 required thermal properties exist, fill missing with 0."""
        from ansys_material_db.models.material import MaterialProperty
        required = {
            "density": {"display_name": "Density", "unit": "kg/m^3"},
            "thermal_conductivity": {"display_name": "Thermal Conductivity", "unit": "W/(m*K)"},
            "specific_heat": {"display_name": "Specific Heat Capacity", "unit": "J/(kg*K)"},
            "thermal_expansion": {"display_name": "Thermal Expansion Coefficient", "unit": "1/K"},
            "poisson_ratio": {"display_name": "Poisson Ratio", "unit": ""},
        }
        existing = {p.name for p in material.properties}
        for prop_key, meta in required.items():
            if prop_key not in existing:
                material.properties.append(MaterialProperty(
                    name=prop_key,
                    display_name=meta["display_name"],
                    value=0.0,
                    unit=meta["unit"],
                ))

    @staticmethod
    def _merge_materials(existing: Material, new: Material) -> Material:
        """Merge two Material objects with the same name.

        Non-empty fields from new fill in blanks from existing.
        Properties are merged by name; new properties are appended.
        """
        merged = Material(
            name=existing.name,
            category=existing.category or new.category,
            supplier=existing.supplier or new.supplier,
            product_name=existing.product_name or new.product_name,
            description=existing.description or new.description,
            properties=list(existing.properties),
            source_document_id=existing.source_document_id or new.source_document_id,
        )

        existing_prop_names = {p.name for p in merged.properties}
        for prop in new.properties:
            if prop.name not in existing_prop_names:
                merged.properties.append(prop)

        return merged

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_prompt_template() -> str:
        try:
            return _PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning(
                "Prompt template not found at %s, using fallback", _PROMPT_TEMPLATE_PATH
            )
            return (
                "Extract materials and their thermal properties from the text below.\n"
                "Return a JSON array of material objects.\n\n"
                "{text}"
            )