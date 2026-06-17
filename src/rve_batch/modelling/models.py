"""Top-level modelling interface for all supported RVE builders.

Class/function relationship
---------------------------

Low-level TexGen wrapper classes:
    NormalWeave2D
        - standard 2D weave when geometry.angle == 0 and layer_count == 0
        - sheared 2D weave when geometry.angle != 0
        - layered 2D weave when geometry.layer_count != 0

    OrthoWeave3D
        - orthogonal 3D weave RVE

    AngleInterlockWeave3D
        - angle-interlock 3D weave RVE

Top-level interface:
    default_model_params(rve_type)
        -> returns a complete default parameter dictionary for one modelling type

    create_model(rve_type, params=None)
        -> returns an initialized low-level TexGen wrapper object

    build_model(rve_type, output_dir, texgen_lib_path, params=None)
        -> initializes the model, generates textile, exports VTU, returns raw VTU path

Typical use:
    params = default_model_params("orthogonal_weave_3d")
    params["geometry"]["warp_count"] = 6
    raw_vtu = build_model("orthogonal_weave_3d", output_dir, texgen_lib_path, params)
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from .angle_interlock import (
    AngleInterlockWeave3D,
    build_angle_interlock_weave,
    default_angle_interlock_params,
)
from .orthogonal_weave import OrthoWeave3D, build_orthogonal_weave, default_orthogonal_weave_params
from .woven_weave import (
    NormalWeave2D,
    build_woven_weave,
    default_layered_woven_weave_params,
    default_sheared_woven_weave_params,
    default_woven_weave_params,
)

WOVEN_2D = "woven_weave_2d"
SHEARED_WOVEN_2D = "sheared_woven_weave_2d"
LAYERED_WOVEN_2D = "layered_woven_weave_2d"
ORTHOGONAL_3D = "orthogonal_weave_3d"
ANGLE_INTERLOCK_3D = "angle_interlock_weave_3d"

MODEL_TYPES = (
    WOVEN_2D,
    SHEARED_WOVEN_2D,
    LAYERED_WOVEN_2D,
    ORTHOGONAL_3D,
    ANGLE_INTERLOCK_3D,
)

_DEFAULTS = {
    WOVEN_2D: default_woven_weave_params,
    SHEARED_WOVEN_2D: default_sheared_woven_weave_params,
    LAYERED_WOVEN_2D: default_layered_woven_weave_params,
    ORTHOGONAL_3D: default_orthogonal_weave_params,
    ANGLE_INTERLOCK_3D: default_angle_interlock_params,
}

_BUILDERS = {
    WOVEN_2D: build_woven_weave,
    SHEARED_WOVEN_2D: build_woven_weave,
    LAYERED_WOVEN_2D: build_woven_weave,
    ORTHOGONAL_3D: build_orthogonal_weave,
    ANGLE_INTERLOCK_3D: build_angle_interlock_weave,
}

_MODEL_CLASSES = {
    WOVEN_2D: NormalWeave2D,
    SHEARED_WOVEN_2D: NormalWeave2D,
    LAYERED_WOVEN_2D: NormalWeave2D,
    ORTHOGONAL_3D: OrthoWeave3D,
    ANGLE_INTERLOCK_3D: AngleInterlockWeave3D,
}


def _deep_update(base, updates):
    """Recursively merge user params into defaults."""
    for key, value in (updates or {}).items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def default_model_params(rve_type):
    """Return complete default parameters for a supported modelling type."""
    if rve_type not in _DEFAULTS:
        raise ValueError(f"Unsupported rve_type: {rve_type}. Supported: {', '.join(MODEL_TYPES)}")
    return deepcopy(_DEFAULTS[rve_type]())


def init_model_params(rve_type, overrides=None):
    """Return default parameters merged with user overrides."""
    params = default_model_params(rve_type)
    return _deep_update(params, overrides or {})


def create_model(rve_type, params=None):
    """Create an initialized low-level model object without exporting files."""
    params = init_model_params(rve_type, params)
    geometry = params.get("geometry", {})

    if rve_type in (WOVEN_2D, SHEARED_WOVEN_2D, LAYERED_WOVEN_2D):
        return NormalWeave2D(
            warp_count=geometry.get("warp_count", 2),
            weft_count=geometry.get("weft_count", 2),
            spacing=geometry.get("spacing", 1),
            thick=geometry.get("thick", 0.2),
            width=geometry.get("width", 0.8),
            gapsize=geometry.get("gapsize", geometry.get("gap_size", 0)),
            angle=geometry.get("angle", 0),
            layer_count=geometry.get("layer_count", 0),
            swap=geometry.get("swap"),
            DefaultDomain=geometry.get("default_domain", True),
            DefalutDominHeight=geometry.get("default_domain_height", True),
        )

    if rve_type == ORTHOGONAL_3D:
        return OrthoWeave3D(
            warp_count=geometry.get("warp_count", 4),
            weft_count=geometry.get("weft_count", 5),
            warp_spacing=geometry.get("warp_spacing", 1),
            weft_spacing=geometry.get("weft_spacing", 1),
            warp_height=geometry.get("warp_height", 0.5),
            weft_height=geometry.get("weft_height", 0.5),
            WarpRatio=geometry.get("warp_ratio", 1),
            BinderRatio=geometry.get("binder_ratio", 2),
            WarpYarnWidths=geometry.get("warp_yarn_width", 0.5),
            YYarnWidths=geometry.get("weft_yarn_width", 0.5),
            BinderYarnWidths=geometry.get("binder_yarn_width", 0.05),
            BinderYarnHeight=geometry.get("binder_yarn_height", 0.05),
            BinderYarnSpacing=geometry.get("binder_yarn_spacing", 0.5),
            WarpLayer=geometry.get("warp_layer", 3),
            WeftLayer=geometry.get("weft_layer", 4),
            GapSize=geometry.get("gap_size", 0),
            Swap=geometry.get("swap"),
            WarpYarnPower=geometry.get("warp_yarn_power", 0.6),
            WeftYarnPower=geometry.get("weft_yarn_power", 0.6),
            BinderYarnPower=geometry.get("binder_yarn_power", 0.6),
            DefaultDomain=geometry.get("default_domain", True),
            DefalutDominHeight=geometry.get("default_domain_height", True),
        )

    if rve_type == ANGLE_INTERLOCK_3D:
        return AngleInterlockWeave3D(
            warp_count=geometry.get("warp_count", 5),
            weft_count=geometry.get("weft_count", 8),
            warp_spacing=geometry.get("warp_spacing", 1),
            weft_spacing=geometry.get("weft_spacing", 1),
            warp_height=geometry.get("warp_height", 0.1),
            weft_height=geometry.get("weft_height", 0.1),
            WarpRatio=geometry.get("warp_ratio", 1),
            BinderRatio=geometry.get("binder_ratio", 1),
            WarpYarnWidths=geometry.get("warp_yarn_width", 0.8),
            WeftYarnWidths=geometry.get("weft_yarn_width", 0.8),
            BinderYarnWidths=geometry.get("binder_yarn_width", 0.4),
            BinderYarnHeight=geometry.get("binder_yarn_height", 0.05),
            BinderYarnSpacing=geometry.get("binder_yarn_spacing", 0.5),
            GapSize=geometry.get("gap_size", 0),
            Swap=geometry.get("swap"),
            WarpYarnPower=geometry.get("warp_yarn_power", 0.6),
            WeftYarnPower=geometry.get("weft_yarn_power", 0.6),
            BinderYarnPower=geometry.get("binder_yarn_power", 0.6),
            DefaultDomain=geometry.get("default_domain", True),
            DefalutDominHeight=geometry.get("default_domain_height", True),
        )

    raise ValueError(f"Unsupported rve_type: {rve_type}")


def build_model(rve_type, output_dir, texgen_lib_path, params=None):
    """Build and export a supported RVE model, returning the raw VTU path."""
    if rve_type not in _BUILDERS:
        raise ValueError(f"Unsupported rve_type: {rve_type}. Supported: {', '.join(MODEL_TYPES)}")
    merged_params = init_model_params(rve_type, params)
    return _BUILDERS[rve_type](merged_params, Path(output_dir), texgen_lib_path)


def describe_model_types():
    """Return a compact description of supported modelling classes and interfaces."""
    return {
        WOVEN_2D: {
            "class": "NormalWeave2D",
            "module": "woven_weave.py",
            "description": "2D standard weave; angle=0 and layer_count=0.",
        },
        SHEARED_WOVEN_2D: {
            "class": "NormalWeave2D",
            "module": "woven_weave.py",
            "description": "2D sheared weave; uses NormalWeave2D with non-zero angle.",
        },
        LAYERED_WOVEN_2D: {
            "class": "NormalWeave2D",
            "module": "woven_weave.py",
            "description": "2D layered weave; uses NormalWeave2D with layer_count > 0.",
        },
        ORTHOGONAL_3D: {
            "class": "OrthoWeave3D",
            "module": "orthogonal_weave.py",
            "description": "3D orthogonal weave with warp/weft/binder yarns.",
        },
        ANGLE_INTERLOCK_3D: {
            "class": "AngleInterlockWeave3D",
            "module": "angle_interlock.py",
            "description": "3D offset angle-interlock weave.",
        },
    }
