"""Ansys Engineering Data XML generation and parsing (2021 R1 schema)."""



from __future__ import annotations



import logging

import uuid

from datetime import datetime

from pathlib import Path

from typing import Optional

from xml.etree import ElementTree as ET



from ansys_material_db.models.material import (

    Material,

    MaterialProperty,

    TemperaturePoint,

    THERMAL_PROPERTIES,

)



logger = logging.getLogger(__name__)



# Ansys 2021 R1 Engineering Data schema constants

_ROOT_TAG = "EngineeringData"

_MATERIALS_TAG = "Materials"

_MATML_DOC_TAG = "MatML_Doc"

_MATERIAL_TAG = "Material"

_GLOSSARY_TAG = "Glossary"

_TERM_TAG = "Term"

_NAME_TAG = "Name"

_SYNONYM_TAG = "Synonym"

_BULK_DETAILS_TAG = "BulkDetails"

_DESCRIPTION_TAG = "Description"

_CLASS_TAG = "Class"

_PROPERTY_DATA_TAG = "PropertyData"

_DATA_TAG = "Data"

_QUALIFIER_TAG = "Qualifier"

_PARAMETER_VALUE_TAG = "ParameterValue"

_METADATA_TAG = "Metadata"

_PARAMETER_DETAILS_TAG = "ParameterDetails"

_PROPERTY_DETAILS_TAG = "PropertyDetails"

_UNITS_TAG = "Units"

_UNIT_TAG = "Unit"



# Ansys property/parameter ID mappings

ANSYS_PROPERTY_MAP: dict[str, str] = {

    "thermal_conductivity": "pr0",
    "density": "pr1",
    "specific_heat": "pr2",
    "thermal_expansion": "pr6",
    "poisson_ratio": "pr7",
}



# pa0 = Options Variable (always present)

# pa1 = Thermal Conductivity value

# pa2 = Temperature

# pa3 = Density value

# pa4 = Specific Heat value

# pa5 = Red (color)

# pa6 = Green (color)

# pa7 = Blue (color)

# pa8 = Material Property (Appearance)

ANSYS_PARAM_MAP: dict[str, str] = {
    "thermal_conductivity": "pa1",
    "density": "pa3",
    "specific_heat": "pa4",
    "thermal_expansion": "pa5",
    "poisson_ratio": "pa9",
}



# Metadata definitions for ParameterDetails

_METADATA_PARAMS: dict[str, dict] = {

    "pa0": {

        "name": "Options Variable",

        "units": None,  # Unitless

    },

    "pa1": {

        "name": "Thermal Conductivity",

        "units": {"name": "Thermal Conductivity", "entries": [("W", None), ("m", -1), ("C", -1)]},

    },

    "pa2": {

        "name": "Temperature",

        "units": {"name": "Temperature", "entries": [("C", None)]},

    },

    "pa3": {

        "name": "Density",

        "units": {"name": "Density", "entries": [("kg", None), ("m", -3)]},

    },

    "pa4": {

        "name": "Specific Heat",

        "units": {"name": "Specific Heat Capacity", "entries": [("J", None), ("kg", -1), ("C", -1)]},

    },

    "pa5": {"name": "Red", "units": None},

    "pa6": {"name": "Green", "units": None},

    "pa7": {"name": "Blue", "units": None},

    "pa8": {"name": "Material Property", "units": None},

    "pa9": {"name": "Relative Permeability", "units": None},

}



# Metadata definitions for PropertyDetails

_METADATA_PROPERTIES: dict[str, str] = {

    "pr0": "Thermal Conductivity",

    "pr1": "Density",

    "pr2": "Specific Heat",

    "pr3": "Material Unique Id",

    "pr4": "Color",

    "pr5": "Relative Permeability",

}





class XMLGenerator:

    """Generate Ansys 2021 R1 Engineering Data XML from Material objects and vice-versa."""



    # ------------------------------------------------------------------

    # Generation

    # ------------------------------------------------------------------



    def generate(self, materials: list[Material]) -> str:

        """Generate an Ansys 2021 R1 Engineering Data XML string."""

        root = ET.Element(_ROOT_TAG)

        root.set("version", "21.1.0.231")

        now = datetime.now()

        root.set("versiondate", now.strftime("%Y/%m/%d %H:%M:%S"))



        # Notes element

        ET.SubElement(root, "Notes")



        # Materials > MatML_Doc

        materials_elem = ET.SubElement(root, _MATERIALS_TAG)

        matml_doc = ET.SubElement(materials_elem, _MATML_DOC_TAG)



        for mat in materials:

            mat_elem = self._material_to_xml(mat)

            matml_doc.append(mat_elem)



        # Metadata section

        metadata = ET.SubElement(matml_doc, _METADATA_TAG)

        self._build_metadata(metadata)



        return self._to_pretty_string(root)



    def generate_file(

        self,

        materials: list[Material],

        output_path: str | Path,

    ) -> str:

        """Write XML to output_path and return the path as a string."""

        output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        xml_string = self.generate(materials)

        output_path.write_text(xml_string, encoding="utf-8")

        return str(output_path.resolve())



    def _material_to_xml(self, material: Material) -> ET.Element:

        """Convert a Material to an Ansys 2021 R1 Material XML element."""

        mat_elem = ET.Element(_MATERIAL_TAG)



        # Glossary

        glossary = ET.SubElement(mat_elem, _GLOSSARY_TAG)

        term = ET.SubElement(glossary, _TERM_TAG)

        name_elem = ET.SubElement(term, _NAME_TAG)

        name_elem.text = material.name

        if material.supplier:

            synonym = ET.SubElement(term, _SYNONYM_TAG)

            synonym.text = material.supplier

        elif material.product_name:

            synonym = ET.SubElement(term, _SYNONYM_TAG)

            synonym.text = material.product_name



        # BulkDetails

        bulk = ET.SubElement(mat_elem, _BULK_DETAILS_TAG)

        bulk_name = ET.SubElement(bulk, _NAME_TAG)

        bulk_name.text = material.name



        if material.description:

            desc = ET.SubElement(bulk, _DESCRIPTION_TAG)

            desc.text = material.description

        elif material.category:

            desc = ET.SubElement(bulk, _DESCRIPTION_TAG)

            desc.text = f"Thermal Properties for {material.name}"



        # Class (from category)

        class_elem = ET.SubElement(bulk, _CLASS_TAG)

        class_name = ET.SubElement(class_elem, _NAME_TAG)

        class_name.text = material.category if material.category else "Other"



        # Build property lookup from Material's properties list

        prop_map: dict[str, MaterialProperty] = {}

        for prop in material.properties:

            if prop.name in ANSYS_PROPERTY_MAP:

                prop_map[prop.name] = prop



        # Helper: build constant property (temperature-independent)

        def _add_constant_property(

            parent: ET.Element,

            prop_id: str,

            param_id: str,

            value: float,

            extra_qualifiers: list[tuple[str, str]] | None = None,

        ) -> None:

            prop_data = ET.SubElement(parent, _PROPERTY_DATA_TAG)

            prop_data.set("property", prop_id)



            data = ET.SubElement(prop_data, _DATA_TAG)

            data.set("format", "string")

            data.text = "-"



            # Behavior qualifier (Isotropic) for thermal properties

            if prop_id in ("pr0", "pr5"):

                q = ET.SubElement(prop_data, _QUALIFIER_TAG)

                q.set("name", "Behavior")

                q.text = "Isotropic"



            # Field Variable Compatible for temp-based properties
            if prop_id in ("pr0", "pr1", "pr2"):
                q = ET.SubElement(prop_data, _QUALIFIER_TAG)
                q.set("name", "Field Variable Compatible")
                q.text = "Temperature"

            # Extra qualifiers (after Field Variable Compatible)
            if extra_qualifiers:
                for qname, qval in extra_qualifiers:
                    q = ET.SubElement(prop_data, _QUALIFIER_TAG)
                    q.set("name", qname)
                    q.text = qval



            # Options Variable (pa0)

            pv_pa0 = ET.SubElement(prop_data, _PARAMETER_VALUE_TAG)

            pv_pa0.set("parameter", "pa0")

            pv_pa0.set("format", "string")

            pv_data = ET.SubElement(pv_pa0, _DATA_TAG)

            pv_data.text = "Interpolation Options"

            q = ET.SubElement(pv_pa0, _QUALIFIER_TAG)
            q.set("name", "AlgorithmType")
            q.text = "Linear Multivariate"

            q2 = ET.SubElement(pv_pa0, _QUALIFIER_TAG)
            q2.set("name", "Normalized")
            q2.text = "True"

            q3 = ET.SubElement(pv_pa0, _QUALIFIER_TAG)
            q3.set("name", "Cached")
            q3.text = "True"

            q4 = ET.SubElement(pv_pa0, _QUALIFIER_TAG)
            q4.set("name", "BETA")
            q4.text = "AlgorithmType$$Linear Multivariate (CGAL)$$EngineeringData.CGAL"



            # Dependent value parameter

            pv_val = ET.SubElement(prop_data, _PARAMETER_VALUE_TAG)

            pv_val.set("parameter", param_id)

            pv_val.set("format", "float")

            val_data = ET.SubElement(pv_val, _DATA_TAG)

            val_data.text = str(value)

            vt = ET.SubElement(pv_val, _QUALIFIER_TAG)

            vt.set("name", "Variable Type")

            vt.text = "Dependent"



            # Temperature parameter (pa2) — constant means near-zero temp

            pv_temp = ET.SubElement(prop_data, _PARAMETER_VALUE_TAG)

            pv_temp.set("parameter", "pa2")

            pv_temp.set("format", "float")

            temp_data = ET.SubElement(pv_temp, _DATA_TAG)

            temp_data.text = "7.88860905221012e-31"

            vt2 = ET.SubElement(pv_temp, _QUALIFIER_TAG)

            vt2.set("name", "Variable Type")

            vt2.text = "Independent"

            fv = ET.SubElement(pv_temp, _QUALIFIER_TAG)

            fv.set("name", "Field Variable")

            fv.text = "Temperature"

            dd = ET.SubElement(pv_temp, _QUALIFIER_TAG)

            dd.set("name", "Default Data")

            dd.text = "22"

            fu = ET.SubElement(pv_temp, _QUALIFIER_TAG)
            fu.set("name", "Field Units")
            fu.text = "C"

            ul = ET.SubElement(pv_temp, _QUALIFIER_TAG)
            ul.set("name", "Upper Limit")
            ul.text = "Program Controlled"

            ll = ET.SubElement(pv_temp, _QUALIFIER_TAG)
            ll.set("name", "Lower Limit")
            ll.text = "Program Controlled"



        # Helper: build temperature-dependent property

        def _add_temp_dependent_property(

            parent: ET.Element,

            prop_id: str,

            param_id: str,

            temp_table: list[TemperaturePoint],

        ) -> None:

            prop_data = ET.SubElement(parent, _PROPERTY_DATA_TAG)

            prop_data.set("property", prop_id)



            data = ET.SubElement(prop_data, _DATA_TAG)

            data.set("format", "string")

            data.text = "-"



            if prop_id in ("pr0", "pr5"):

                q = ET.SubElement(prop_data, _QUALIFIER_TAG)

                q.set("name", "Behavior")

                q.text = "Isotropic"



            if prop_id in ("pr0", "pr1", "pr2"):

                q = ET.SubElement(prop_data, _QUALIFIER_TAG)

                q.set("name", "Field Variable Compatible")

                q.text = "Temperature"



            # Options Variable (pa0)

            pv_pa0 = ET.SubElement(prop_data, _PARAMETER_VALUE_TAG)

            pv_pa0.set("parameter", "pa0")

            pv_pa0.set("format", "string")

            pv_data = ET.SubElement(pv_pa0, _DATA_TAG)

            pv_data.text = "Interpolation Options"

            q = ET.SubElement(pv_pa0, _QUALIFIER_TAG)
            q.set("name", "AlgorithmType")
            q.text = "Linear Multivariate"

            q2 = ET.SubElement(pv_pa0, _QUALIFIER_TAG)
            q2.set("name", "Normalized")
            q2.text = "True"

            q3 = ET.SubElement(pv_pa0, _QUALIFIER_TAG)
            q3.set("name", "Cached")
            q3.text = "True"

            q4 = ET.SubElement(pv_pa0, _QUALIFIER_TAG)
            q4.set("name", "BETA")
            q4.text = "AlgorithmType$$Linear Multivariate (CGAL)$$EngineeringData.CGAL"



            # For temperature-dependent, we store multiple data points.

            # The Ansys schema stores them as a table-like structure inside the property.

            # We create a Table-like structure with Data entries for each temp point.

            for i, tp in enumerate(temp_table):

                # Dependent value

                pv_val = ET.SubElement(prop_data, _PARAMETER_VALUE_TAG)

                pv_val.set("parameter", param_id)

                pv_val.set("format", "float")

                val_data = ET.SubElement(pv_val, _DATA_TAG)

                val_data.text = str(tp.value)

                vt = ET.SubElement(pv_val, _QUALIFIER_TAG)

                vt.set("name", "Variable Type")

                vt.text = "Dependent"



                # Temperature

                pv_temp = ET.SubElement(prop_data, _PARAMETER_VALUE_TAG)

                pv_temp.set("parameter", "pa2")

                pv_temp.set("format", "float")

                temp_data = ET.SubElement(pv_temp, _DATA_TAG)

                temp_data.text = str(tp.temperature)

                vt2 = ET.SubElement(pv_temp, _QUALIFIER_TAG)

                vt2.set("name", "Variable Type")

                vt2.text = "Independent"

                fv = ET.SubElement(pv_temp, _QUALIFIER_TAG)

                fv.set("name", "Field Variable")

                fv.text = "Temperature"

                dd = ET.SubElement(pv_temp, _QUALIFIER_TAG)

                dd.set("name", "Default Data")

                dd.text = "22"

                fu = ET.SubElement(pv_temp, _QUALIFIER_TAG)

                fu.set("name", "Field Units")

                fu.text = "C"

                ul = ET.SubElement(pv_temp, _QUALIFIER_TAG)
                ul.set("name", "Upper Limit")
                ul.text = "Program Controlled"

                ll = ET.SubElement(pv_temp, _QUALIFIER_TAG)
                ll.set("name", "Lower Limit")
                ll.text = "Program Controlled"


        # Thermal Conductivity (pr0 / pa1)

        if "thermal_conductivity" in prop_map:

            p = prop_map["thermal_conductivity"]

            if p.is_temp_dependent and p.temperature_table:

                _add_temp_dependent_property(bulk, "pr0", "pa1", p.temperature_table)

            else:

                value = p.value if p.value is not None else 0.0

                _add_constant_property(bulk, "pr0", "pa1", value)



        # Density (pr1 / pa3)

        if "density" in prop_map:

            p = prop_map["density"]

            if p.is_temp_dependent and p.temperature_table:

                _add_temp_dependent_property(bulk, "pr1", "pa3", p.temperature_table)

            else:

                value = p.value if p.value is not None else 0.0

                _add_constant_property(bulk, "pr1", "pa3", value)



        # Specific Heat (pr2 / pa4)

        if "specific_heat" in prop_map:

            p = prop_map["specific_heat"]

            if p.is_temp_dependent and p.temperature_table:

                _add_temp_dependent_property(bulk, "pr2", "pa4", p.temperature_table)

            else:

                value = p.value if p.value is not None else 0.0

                _add_constant_property(bulk, "pr2", "pa4", value)
                # Add pr2-specific qualifiers in reference order:
                # Definition -> Field Variable Compatible (already added) -> Symbol
                last_pd = bulk.findall("PropertyData")[-1]
                # Insert Definition before Field Variable Compatible
                fv_elem = None
                for child in last_pd:
                    if child.tag == _QUALIFIER_TAG and child.get("name") == "Field Variable Compatible":
                        fv_elem = child
                        break
                q_def = ET.Element(_QUALIFIER_TAG)
                q_def.set("name", "Definition")
                q_def.text = "Constant Pressure"
                if fv_elem is not None:
                    last_pd.insert(list(last_pd).index(fv_elem), q_def)
                else:
                    last_pd.append(q_def)
                # Symbol after Field Variable Compatible
                q_sym = ET.Element(_QUALIFIER_TAG)
                q_sym.set("name", "Symbol")
                q_sym.text = "Cᵨ"
                # Insert after Field Variable Compatible
                for idx, child in enumerate(last_pd):
                    if child.tag == _QUALIFIER_TAG and child.get("name") == "Field Variable Compatible":
                        last_pd.insert(idx + 1, q_sym)
                        break




        # Relative Permeability (pr5 / pa9)

        self._add_relative_permeability(bulk)



        # Material Unique Id (pr3)

        self._add_guid(bulk)



        # Color (pr4) — default gray

        self._add_color(bulk)



        return mat_elem



    def _add_relative_permeability(self, parent: ET.Element) -> None:

        """Add Relative Permeability property (pr5) with default value 1."""

        prop_data = ET.SubElement(parent, _PROPERTY_DATA_TAG)

        prop_data.set("property", "pr5")



        data = ET.SubElement(prop_data, _DATA_TAG)

        data.set("format", "string")

        data.text = "-"



        q = ET.SubElement(prop_data, _QUALIFIER_TAG)

        q.set("name", "Behavior")

        q.text = "Isotropic"



        pv = ET.SubElement(prop_data, _PARAMETER_VALUE_TAG)

        pv.set("parameter", "pa9")

        pv.set("format", "float")

        val_data = ET.SubElement(pv, _DATA_TAG)

        val_data.text = "1"

        vt = ET.SubElement(pv, _QUALIFIER_TAG)

        vt.set("name", "Variable Type")

        vt.text = "Dependent"



    def _add_guid(self, parent: ET.Element) -> None:

        """Add Material Unique Id (pr3) with a generated GUID."""

        prop_data = ET.SubElement(parent, _PROPERTY_DATA_TAG)

        prop_data.set("property", "pr3")



        data = ET.SubElement(prop_data, _DATA_TAG)

        data.set("format", "string")

        data.text = "-"



        guid_q = ET.SubElement(prop_data, _QUALIFIER_TAG)

        guid_q.set("name", "guid")

        guid_q.text = str(uuid.uuid4())



        display_q = ET.SubElement(prop_data, _QUALIFIER_TAG)

        display_q.set("name", "Display")

        display_q.text = "False"



    def _add_color(self, parent: ET.Element, r: int = 222, g: int = 222, b: int = 222) -> None:

        """Add Color property (pr4) with RGB values."""

        prop_data = ET.SubElement(parent, _PROPERTY_DATA_TAG)

        prop_data.set("property", "pr4")



        data = ET.SubElement(prop_data, _DATA_TAG)

        data.set("format", "string")

        data.text = "-"



        # Red

        pv_r = ET.SubElement(prop_data, _PARAMETER_VALUE_TAG)

        pv_r.set("parameter", "pa5")

        pv_r.set("format", "float")

        r_data = ET.SubElement(pv_r, _DATA_TAG)

        r_data.text = str(r)

        vt = ET.SubElement(pv_r, _QUALIFIER_TAG)

        vt.set("name", "Variable Type")

        vt.text = "Dependent"



        # Green

        pv_g = ET.SubElement(prop_data, _PARAMETER_VALUE_TAG)

        pv_g.set("parameter", "pa6")

        pv_g.set("format", "float")

        g_data = ET.SubElement(pv_g, _DATA_TAG)

        g_data.text = str(g)

        vt = ET.SubElement(pv_g, _QUALIFIER_TAG)

        vt.set("name", "Variable Type")

        vt.text = "Dependent"



        # Blue

        pv_b = ET.SubElement(prop_data, _PARAMETER_VALUE_TAG)

        pv_b.set("parameter", "pa7")

        pv_b.set("format", "float")

        b_data = ET.SubElement(pv_b, _DATA_TAG)

        b_data.text = str(b)

        vt = ET.SubElement(pv_b, _QUALIFIER_TAG)

        vt.set("name", "Variable Type")

        vt.text = "Dependent"



        # Material Property (Appearance)

        pv_app = ET.SubElement(prop_data, _PARAMETER_VALUE_TAG)

        pv_app.set("parameter", "pa8")

        pv_app.set("format", "string")

        app_data = ET.SubElement(pv_app, _DATA_TAG)

        app_data.text = "Appearance"



    def _build_metadata(self, metadata: ET.Element) -> None:

        """Build the Metadata section with ParameterDetails and PropertyDetails."""

        for pid, pinfo in _METADATA_PARAMS.items():

            pd = ET.SubElement(metadata, _PARAMETER_DETAILS_TAG)

            pd.set("id", pid)

            pd_name = ET.SubElement(pd, _NAME_TAG)

            pd_name.text = pinfo["name"]

            if pinfo["units"] is not None:

                units_elem = ET.SubElement(pd, _UNITS_TAG)

                units_elem.set("name", pinfo["units"]["name"])

                for unit_name, power in pinfo["units"]["entries"]:

                    unit_elem = ET.SubElement(units_elem, _UNIT_TAG)

                    if power is not None:

                        unit_elem.set("power", str(power))

                    un = ET.SubElement(unit_elem, _NAME_TAG)

                    un.text = unit_name

            else:

                ET.SubElement(pd, "Unitless")



        for pid, pname in _METADATA_PROPERTIES.items():

            pd = ET.SubElement(metadata, _PROPERTY_DETAILS_TAG)

            pd.set("id", pid)

            ET.SubElement(pd, "Unitless")

            pd_name = ET.SubElement(pd, _NAME_TAG)

            pd_name.text = pname



    # ------------------------------------------------------------------

    # Validation

    # ------------------------------------------------------------------



    def validate(self, xml_string: str) -> tuple[bool, list[str]]:

        """Validate an XML string against the Ansys 2021 R1 schema.



        Returns

        -------

        tuple[bool, list[str]]

            (is_valid, error_messages)

        """

        errors: list[str] = []



        try:

            root = ET.fromstring(xml_string)

        except ET.ParseError as exc:

            return False, [f"XML parse error: {exc}"]



        if root.tag != _ROOT_TAG:

            errors.append(f"Root element must be '{_ROOT_TAG}', got '{root.tag}'")



        # Check version attribute

        if root.get("version") != "21.1.0.231":

            errors.append(f"Expected version '21.1.0.231', got '{root.get('version')}'")



        # Materials > MatML_Doc > Material

        materials_elem = root.find(_MATERIALS_TAG)

        if materials_elem is None:

            errors.append("Missing <Materials> element")

            return (len(errors) == 0, errors)



        matml_doc = materials_elem.find(_MATML_DOC_TAG)

        if matml_doc is None:

            errors.append("Missing <MatML_Doc> element")

            return (len(errors) == 0, errors)



        material_elems = matml_doc.findall(_MATERIAL_TAG)

        if not material_elems:

            errors.append("No <Material> elements found")

            return (len(errors) == 0, errors)



        for mat_elem in material_elems:

            # Check Glossary

            glossary = mat_elem.find(_GLOSSARY_TAG)

            if glossary is None:

                errors.append("Material missing <Glossary> element")

                continue

            term = glossary.find(_TERM_TAG)

            if term is None:

                errors.append("Glossary missing <Term> element")

                continue

            name_elem = term.find(_NAME_TAG)

            if name_elem is None or not name_elem.text:

                errors.append("Term missing <Name> element")



            # Check BulkDetails

            bulk = mat_elem.find(_BULK_DETAILS_TAG)

            if bulk is None:

                errors.append("Material missing <BulkDetails> element")

                continue



            bulk_name = bulk.find(_NAME_TAG)

            if bulk_name is None or not bulk_name.text:

                errors.append("BulkDetails missing <Name> element")



            # Check PropertyData elements

            prop_data_elems = bulk.findall(_PROPERTY_DATA_TAG)

            for pd_elem in prop_data_elems:

                prop_id = pd_elem.get("property", "")

                if not prop_id:

                    errors.append("PropertyData missing 'property' attribute")

                    continue



                # Check Data element exists

                data_elem = pd_elem.find(_DATA_TAG)

                if data_elem is None:

                    errors.append(f"PropertyData '{prop_id}' missing <Data> element")



        # Check Metadata section

        metadata = matml_doc.find(_METADATA_TAG)

        if metadata is None:

            errors.append("MatML_Doc missing <Metadata> element")



        return (len(errors) == 0, errors)



    # ------------------------------------------------------------------

    # Parsing (import real Ansys 2021 R1 XML)

    # ------------------------------------------------------------------



    def parse_ansys_xml(self, file_path: str | Path) -> list[Material]:

        """Parse a real Ansys 2021 R1 Engineering Data XML file."""

        file_path = Path(file_path)

        if not file_path.exists():

            logger.warning("XML file not found: %s", file_path)

            return []



        try:

            tree = ET.parse(str(file_path))

        except ET.ParseError:

            logger.exception("Failed to parse XML: %s", file_path)

            return []



        root = tree.getroot()

        return self._parse_root(root)



    def parse_ansys_xml_string(self, xml_string: str) -> list[Material]:

        """Parse an Ansys 2021 R1 Engineering Data XML string."""

        if not xml_string or not xml_string.strip():

            return []

        try:

            root = ET.fromstring(xml_string)

        except ET.ParseError:

            logger.exception("Failed to parse XML string")

            return []

        return self._parse_root(root)



    def _parse_root(self, root: ET.Element) -> list[Material]:

        """Parse material elements from an Ansys 2021 R1 XML root."""

        materials: list[Material] = []



        # Navigate: EngineeringData > Materials > MatML_Doc > Material

        materials_elem = root.find(_MATERIALS_TAG)

        if materials_elem is None:

            return materials



        matml_doc = materials_elem.find(_MATML_DOC_TAG)

        if matml_doc is None:

            return materials



        # Parse metadata first (for property/parameter name resolution)

        metadata = matml_doc.find(_METADATA_TAG)

        metadata_map = self._parse_metadata(metadata)



        for mat_elem in matml_doc.findall(_MATERIAL_TAG):

            mat = self._parse_material_element(mat_elem, metadata_map)

            if mat is not None:

                materials.append(mat)



        return materials



    def _parse_metadata(self, metadata: ET.Element | None) -> dict:

        """Parse the Metadata section into lookup maps."""

        result: dict[str, dict[str, str]] = {"params": {}, "properties": {}}



        if metadata is None:

            return result



        for pd in metadata.findall(_PARAMETER_DETAILS_TAG):

            pid = pd.get("id", "")

            name_elem = pd.find(_NAME_TAG)

            name = name_elem.text if name_elem is not None and name_elem.text else ""

            result["params"][pid] = name



        for pd in metadata.findall(_PROPERTY_DETAILS_TAG):

            pid = pd.get("id", "")

            name_elem = pd.find(_NAME_TAG)

            name = name_elem.text if name_elem is not None and name_elem.text else ""

            result["properties"][pid] = name



        return result



    def _parse_material_element(

        self,

        elem: ET.Element,

        metadata_map: dict,

    ) -> Optional[Material]:

        """Parse a single Material element from Ansys 2021 R1 XML."""

        # Extract name from Glossary > Term > Name or BulkDetails > Name

        name = ""

        glossary = elem.find(_GLOSSARY_TAG)

        if glossary is not None:

            term = glossary.find(_TERM_TAG)

            if term is not None:

                name_elem = term.find(_NAME_TAG)

                if name_elem is not None and name_elem.text:

                    name = name_elem.text



        # Category from BulkDetails > Class > Name

        category = ""

        description = ""

        bulk = elem.find(_BULK_DETAILS_TAG)

        if bulk is not None:

            bulk_name = bulk.find(_NAME_TAG)

            if bulk_name is not None and bulk_name.text:

                name = name or bulk_name.text



            desc_elem = bulk.find(_DESCRIPTION_TAG)

            if desc_elem is not None and desc_elem.text:

                description = desc_elem.text



            class_elem = bulk.find(_CLASS_TAG)

            if class_elem is not None:

                cn = class_elem.find(_NAME_TAG)

                if cn is not None and cn.text:

                    category = cn.text



        if not name:

            return None



        properties: list[MaterialProperty] = []



        if bulk is not None:

            for pd_elem in bulk.findall(_PROPERTY_DATA_TAG):

                prop_id = pd_elem.get("property", "")

                prop = self._parse_property_data(pd_elem, prop_id, metadata_map)

                if prop is not None:

                    properties.append(prop)



        return Material(

            name=name,

            category=category,

            description=description,

            properties=properties,

        )



    def _parse_property_data(

        self,

        pd_elem: ET.Element,

        prop_id: str,

        metadata_map: dict,

    ) -> Optional[MaterialProperty]:

        """Parse a PropertyData element into a MaterialProperty."""

        # Determine which Ansys property this is

        reverse_prop_map = {v: k for k, v in ANSYS_PROPERTY_MAP.items()}
        prop_name = reverse_prop_map.get(prop_id)

        # Resolve display name from metadata map (covers all property IDs)
        display_name = metadata_map.get("properties", {}).get(prop_id, prop_id)
        unit = ""

        if prop_name is not None:
            meta = THERMAL_PROPERTIES.get(prop_name, {})
            display_name = meta.get("display", display_name)
            unit = meta.get("unit", "")



        # Collect ParameterValue elements

        param_values: dict[str, list[dict]] = {}

        for pv in pd_elem.findall(_PARAMETER_VALUE_TAG):

            pid = pv.get("parameter", "")

            data_elem = pv.find(_DATA_TAG)

            raw_value = data_elem.text if data_elem is not None and data_elem.text else ""



            qualifiers: dict[str, str] = {}

            for q in pv.findall(_QUALIFIER_TAG):

                qname = q.get("name", "")

                qval = q.text if q.text else ""

                qualifiers[qname] = qval



            param_values.setdefault(pid, []).append({

                "value": raw_value,

                "qualifiers": qualifiers,

            })



        # Determine the dependent parameter ID for this property

        dep_param_id = ANSYS_PARAM_MAP.get(prop_name, "") if prop_name else ""



        # Check if it has a temperature-independent constant value

        # by looking for a pa2 with Independent type and near-zero value

        is_temp_dependent = False

        temperature_table: list[TemperaturePoint] = []

        value: Optional[float] = None



        # Collect all dependent values (pa1, pa3, pa4 etc.)

        dep_values = param_values.get(dep_param_id, [])

        temp_values = param_values.get("pa2", [])



        # For unmapped properties (pr5/pr3/pr4 etc), try to get value from any parameter
        if not dep_values and not prop_name:
            for pid, pv_list in param_values.items():
                for pv_entry in pv_list:
                    raw = pv_entry.get("value", "")
                    quals = pv_entry.get("qualifiers", {})
                    if quals.get("Variable Type") == "Dependent":
                        try:
                            value = float(raw) if raw else None
                        except (ValueError, TypeError):
                            value = None
                        break
                if value is not None:
                    break

        if len(dep_values) > 1:

            # Multiple data points = temperature-dependent

            is_temp_dependent = True

            for i, dep_pv in enumerate(dep_values):

                try:

                    val = float(dep_pv["value"]) if dep_pv["value"] else 0.0

                except (ValueError, TypeError):

                    continue

                # Get corresponding temperature

                if i < len(temp_values):

                    temp_raw = temp_values[i]["value"]

                    try:

                        temp = float(temp_raw) if temp_raw else 0.0

                    except (ValueError, TypeError):

                        temp = 0.0

                else:

                    temp = 0.0

                temperature_table.append(TemperaturePoint(temperature=temp, value=val))

        elif len(dep_values) == 1:

            try:

                value = float(dep_values[0]["value"]) if dep_values[0]["value"] else None

            except (ValueError, TypeError):

                value = None



        return MaterialProperty(

            name=prop_name or prop_id,

            display_name=display_name,

            value=value,

            unit=unit,

            source="",

            temperature_table=temperature_table,

            is_temp_dependent=is_temp_dependent,

        )



    # ------------------------------------------------------------------

    # XML formatting helpers

    # ------------------------------------------------------------------



    @staticmethod
    def _to_pretty_string(element: ET.Element, indent: str = "  ") -> str:
        """Return a pretty-printed XML declaration + tree string."""
        ET.indent(element, space=indent)
        declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        raw = ET.tostring(element, encoding="unicode")
        # Ansys requires <Notes>\n  </Notes> not self-closing <Notes />
        raw = raw.replace("<Notes />", "<Notes>\n  </Notes>")
        return declaration + raw