"""Generate DOE config templates for all supported modelling types."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from rve_batch.modelling import default_model_params

OUT_DIR = Path("configs/doe_templates")

COMMON = {
    "output_root": "output",
    "type_dir": "",
    "batch_name": "batch0001",
    "sample_count": 10,
    "seed": 42,
    "start_index": 1,
    "end_index": 10,
    "prefix": "case",
    "max_sampling_iterations": 10000,
    "max_workers": 1,
    "skip_completed": True,
    "rerun_failed": False,
    "analysis_template": "configs/tools/user_RVE_analysis.json",
    "screenshot": {
        "enabled": True,
        "filename": "iso_yarn_visible.png",
        "hide_yarn_index": -1,
        "window_size": [1200, 900],
        "background": "white",
        "scalars": "YarnIndex",
        "parallel_projection": True,
        "show_edges": False,
        "show_scalar_bar": False,
    },
}

MATERIAL_DEFAULTS = {
    "material_0": {"E": 69000000000.0, "nu": 0.2},
    "material_1": {"E": 4800000000.0, "nu": 0.34},
}

MATERIAL_SPACE = {
    "materials.material_0.E": {"min": 60000000000.0, "max": 80000000000.0},
    "materials.material_0.nu": {"min": 0.18, "max": 0.25},
    "materials.material_1.E": {"min": 3000000000.0, "max": 6000000000.0},
    "materials.material_1.nu": {"min": 0.30, "max": 0.38},
}

MATERIAL_CONSTRAINTS = [
    "material_0_E > 0",
    "material_1_E > 0",
    "0 < material_0_nu < 0.5",
    "0 < material_1_nu < 0.5",
]


def range_spec(value, rel=0.25, floor=None, as_int=False):
    if as_int or isinstance(value, int):
        lo = max(0 if floor is None else int(floor), int(round(value * (1 - rel))))
        hi = max(lo, int(round(value * (1 + rel))))
        return {"min": lo, "max": hi, "type": "int"}
    lo = value * (1 - rel)
    hi = value * (1 + rel)
    if floor is not None:
        lo = max(floor, lo)
    return {"min": lo, "max": hi}


def mesh_space(mesh):
    return {
        "mesh.x_voxel": range_spec(mesh.get("x_voxel", 80), rel=0.5, floor=2, as_int=True),
        "mesh.y_voxel": range_spec(mesh.get("y_voxel", 80), rel=0.5, floor=2, as_int=True),
        "mesh.z_voxel": range_spec(mesh.get("z_voxel", 80), rel=0.5, floor=2, as_int=True),
    }


def swap_space(swap, first_max, second_max):
    space = {}
    for i, _ in enumerate(swap or []):
        space[f"geometry.swap[{i}][0]"] = {"min": 0, "max": max(0, first_max), "type": "int"}
        space[f"geometry.swap[{i}][1]"] = {"min": 0, "max": max(0, second_max), "type": "int"}
    return space


def swap_constraints(swap):
    constraints = []
    for i, _ in enumerate(swap or []):
        constraints.append(f"swap_{i}_0 < weft_count")
        constraints.append(f"swap_{i}_1 < warp_count")
    return constraints


def with_common(rve_type, params, lhs_space, constraints):
    cfg = deepcopy(COMMON)
    cfg["rve_type"] = rve_type
    cfg["batch_name"] = f"{rve_type}_batch0001"
    cfg["base_overrides"] = deepcopy(params)
    cfg["base_overrides"]["materials"] = deepcopy(MATERIAL_DEFAULTS)
    cfg["lhs_space"] = lhs_space
    cfg["constraints"] = constraints
    return cfg


def woven_config(rve_type):
    params = default_model_params(rve_type)
    geometry = params["geometry"]
    lhs = mesh_space(params["mesh"])
    lhs.update({
        "geometry.warp_count": range_spec(geometry["warp_count"], rel=0.5, floor=1, as_int=True),
        "geometry.weft_count": range_spec(geometry["weft_count"], rel=0.5, floor=1, as_int=True),
        "geometry.spacing": range_spec(geometry["spacing"], rel=0.3, floor=0.01),
        "geometry.thick": range_spec(geometry["thick"], rel=0.4, floor=0.01),
        "geometry.width": range_spec(geometry["width"], rel=0.3, floor=0.01),
        "geometry.gapsize": {"min": 0.0, "max": max(0.05, geometry.get("gapsize", 0.0) + 0.05)},
        "geometry.angle": {"min": max(0.0, geometry.get("angle", 0.0) - 10.0), "max": geometry.get("angle", 0.0) + 10.0},
        "geometry.layer_count": {"min": max(0, geometry.get("layer_count", 0) - 1), "max": geometry.get("layer_count", 0) + 1, "type": "int"},
    })
    lhs.update(swap_space(geometry.get("swap"), max(0, geometry["weft_count"] - 1), max(0, geometry["warp_count"] - 1)))
    lhs.update(MATERIAL_SPACE)
    constraints = ["width < 0.95 * spacing", "thick < spacing"] + swap_constraints(geometry.get("swap")) + MATERIAL_CONSTRAINTS
    if rve_type == "sheared_woven_weave_2d":
        constraints.append("angle != 0")
    if rve_type == "layered_woven_weave_2d":
        constraints.append("layer_count > 0")
    return with_common(rve_type, params, lhs, constraints)


def orthogonal_config():
    rve_type = "orthogonal_weave_3d"
    params = default_model_params(rve_type)
    geometry = params["geometry"]
    lhs = mesh_space(params["mesh"])
    lhs.update({
        "geometry.warp_count": range_spec(geometry["warp_count"], rel=0.35, floor=1, as_int=True),
        "geometry.weft_count": range_spec(geometry["weft_count"], rel=0.35, floor=1, as_int=True),
        "geometry.warp_spacing": range_spec(geometry["warp_spacing"], rel=0.35, floor=0.01),
        "geometry.weft_spacing": range_spec(geometry["weft_spacing"], rel=0.35, floor=0.01),
        "geometry.warp_height": range_spec(geometry["warp_height"], rel=0.5, floor=0.01),
        "geometry.weft_height": range_spec(geometry["weft_height"], rel=0.5, floor=0.01),
        "geometry.warp_ratio": {"min": max(1, geometry["warp_ratio"]), "max": max(1, geometry["warp_ratio"] + 1), "type": "int"},
        "geometry.binder_ratio": {"min": max(1, geometry["binder_ratio"]), "max": max(1, geometry["binder_ratio"] + 1), "type": "int"},
        "geometry.warp_yarn_width": range_spec(geometry["warp_yarn_width"], rel=0.35, floor=0.01),
        "geometry.weft_yarn_width": range_spec(geometry["weft_yarn_width"], rel=0.35, floor=0.01),
        "geometry.binder_yarn_width": range_spec(geometry["binder_yarn_width"], rel=0.5, floor=0.01),
        "geometry.binder_yarn_height": range_spec(geometry["binder_yarn_height"], rel=0.5, floor=0.01),
        "geometry.binder_yarn_spacing": range_spec(geometry["binder_yarn_spacing"], rel=0.35, floor=0.01),
        "geometry.warp_layer": {"min": max(1, geometry["warp_layer"] - 2), "max": geometry["warp_layer"] + 2, "type": "int"},
        "geometry.weft_layer": {"min": max(1, geometry["weft_layer"] - 1), "max": geometry["weft_layer"] + 3, "type": "int"},
        "geometry.gap_size": {"min": 0.0, "max": max(0.05, geometry.get("gap_size", 0.0) + 0.05)},
        "geometry.warp_yarn_power": range_spec(geometry["warp_yarn_power"], rel=0.25, floor=0.01),
        "geometry.weft_yarn_power": range_spec(geometry["weft_yarn_power"], rel=0.25, floor=0.01),
        "geometry.binder_yarn_power": range_spec(geometry["binder_yarn_power"], rel=0.25, floor=0.01),
    })
    lhs.update(swap_space(geometry.get("swap"), max(0, geometry["weft_count"] - 1), max(0, geometry["warp_count"] - 1)))
    lhs.update(MATERIAL_SPACE)
    constraints = [
        "warp_yarn_width < 0.95 * warp_spacing",
        "weft_yarn_width < 0.95 * weft_spacing",
        "binder_yarn_width < 0.95 * binder_yarn_spacing",
        "warp_height < warp_spacing",
        "weft_height < weft_spacing",
        "binder_yarn_height < binder_yarn_spacing",
        "warp_layer < weft_layer",
    ] + swap_constraints(geometry.get("swap")) + MATERIAL_CONSTRAINTS
    return with_common(rve_type, params, lhs, constraints)


def angle_config():
    rve_type = "angle_interlock_weave_3d"
    params = default_model_params(rve_type)
    geometry = params["geometry"]
    lhs = mesh_space(params["mesh"])
    lhs.update({
        "geometry.warp_count": range_spec(geometry["warp_count"], rel=0.35, floor=1, as_int=True),
        "geometry.weft_count": range_spec(geometry["weft_count"], rel=0.25, floor=3, as_int=True),
        "geometry.warp_spacing": range_spec(geometry["warp_spacing"], rel=0.35, floor=0.01),
        "geometry.weft_spacing": range_spec(geometry["weft_spacing"], rel=0.35, floor=0.01),
        "geometry.warp_height": range_spec(geometry["warp_height"], rel=0.5, floor=0.01),
        "geometry.weft_height": range_spec(geometry["weft_height"], rel=0.5, floor=0.01),
        "geometry.warp_ratio": {"min": max(1, geometry["warp_ratio"]), "max": max(1, geometry["warp_ratio"] + 1), "type": "int"},
        "geometry.binder_ratio": {"min": max(1, geometry["binder_ratio"]), "max": max(1, geometry["binder_ratio"] + 1), "type": "int"},
        "geometry.warp_yarn_width": range_spec(geometry["warp_yarn_width"], rel=0.35, floor=0.01),
        "geometry.weft_yarn_width": range_spec(geometry["weft_yarn_width"], rel=0.35, floor=0.01),
        "geometry.binder_yarn_width": range_spec(geometry["binder_yarn_width"], rel=0.5, floor=0.01),
        "geometry.binder_yarn_height": range_spec(geometry["binder_yarn_height"], rel=0.5, floor=0.01),
        "geometry.binder_yarn_spacing": range_spec(geometry["binder_yarn_spacing"], rel=0.35, floor=0.01),
        "geometry.gap_size": {"min": 0.0, "max": max(0.05, geometry.get("gap_size", 0.0) + 0.05)},
        "geometry.warp_yarn_power": range_spec(geometry["warp_yarn_power"], rel=0.25, floor=0.01),
        "geometry.weft_yarn_power": range_spec(geometry["weft_yarn_power"], rel=0.25, floor=0.01),
        "geometry.binder_yarn_power": range_spec(geometry["binder_yarn_power"], rel=0.25, floor=0.01),
    })
    lhs.update(swap_space(geometry.get("swap"), max(0, geometry["weft_count"] - 1), max(0, geometry["warp_count"] - 1)))
    lhs.update(MATERIAL_SPACE)
    constraints = [
        "warp_yarn_width < 0.95 * warp_spacing",
        "weft_yarn_width < 0.95 * weft_spacing",
        "binder_yarn_width < 0.95 * binder_yarn_spacing",
        "warp_height < warp_spacing",
        "weft_height < weft_spacing",
        "binder_yarn_height < binder_yarn_spacing",
        "weft_count >= 3",
    ] + swap_constraints(geometry.get("swap")) + MATERIAL_CONSTRAINTS
    return with_common(rve_type, params, lhs, constraints)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    configs = {
        "woven_weave_2d": woven_config("woven_weave_2d"),
        "sheared_woven_weave_2d": woven_config("sheared_woven_weave_2d"),
        "layered_woven_weave_2d": woven_config("layered_woven_weave_2d"),
        "orthogonal_weave_3d": orthogonal_config(),
        "angle_interlock_weave_3d": angle_config(),
    }
    for rve_type, cfg in configs.items():
        path = OUT_DIR / f"{rve_type}_doe.json"
        path.write_text(json.dumps(cfg, indent=4, ensure_ascii=False), encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
