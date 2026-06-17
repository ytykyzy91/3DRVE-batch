"""Solver analysis JSON rendering."""

from __future__ import annotations

import json
from pathlib import Path


MATERIAL_PARAM_PATHS = {
    "material_0_E": (0, "E"),
    "material_0_nu": (0, "nu"),
    "material_1_E": (1, "E"),
    "material_1_nu": (1, "nu"),
}


def read_json(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")


def _set_isotropic_value(material, key, value):
    isotropic = material["Mechanical"]["LinearElastic"]["Isotropic"]
    str_value = str(value)
    isotropic[key] = str_value
    for param in isotropic.get("params", []):
        if key in param:
            param[key] = str_value


def apply_material_overrides(analysis_data, material_overrides):
    """Apply material E/nu overrides to Defs.Analysis.Materials[0/1].

    Supported material_overrides format:
        {
            "material_0": {"E": 69000000000.0, "nu": 0.2},
            "material_1": {"E": 4800000000.0, "nu": 0.34}
        }
    """
    if not material_overrides:
        return analysis_data

    materials = analysis_data["Defs"]["Analysis"]["Materials"]
    for material_key, values in material_overrides.items():
        if not material_key.startswith("material_"):
            continue
        try:
            material_index = int(material_key.split("_", 1)[1])
        except ValueError:
            continue
        if material_index >= len(materials):
            raise IndexError(f"Material index out of range: {material_index}")
        for prop_key, prop_value in values.items():
            if prop_key not in ("E", "nu"):
                continue
            _set_isotropic_value(materials[material_index], prop_key, prop_value)
    return analysis_data


def render_analysis_config(template_path, output_path, case_context):
    """Render a case-specific analysis JSON from a template.

    case_context supports:
        rve_path: final VTU filename/path used by Defs.Composite.Settings.rvePath
        material_overrides: material_0/material_1 E/nu overrides
    """
    data = read_json(template_path)

    rve_path = case_context.get("rve_path")
    if rve_path:
        data["Defs"]["Composite"]["Settings"]["rvePath"] = str(rve_path)

    apply_material_overrides(data, case_context.get("material_overrides"))
    write_json(output_path, data)
    return Path(output_path)
