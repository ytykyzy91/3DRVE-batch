"""DOE sampling utilities for RVE batch modelling."""

from __future__ import annotations

from copy import deepcopy
import math
import random
import re

from rve_batch.modelling import init_model_params

INT_FIELDS = {
    "warp_count",
    "weft_count",
    "warp_ratio",
    "binder_ratio",
    "warp_layer",
    "weft_layer",
    "layer_count",
    "x_voxel",
    "y_voxel",
    "z_voxel",
}

SAFE_MATH = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "log": math.log,
    "exp": math.exp,
    "abs": abs,
    "min": min,
    "max": max,
    "pi": math.pi,
}

POSITIVE_FIELDS = {
    "warp_count",
    "weft_count",
    "warp_spacing",
    "weft_spacing",
    "spacing",
    "warp_height",
    "weft_height",
    "thick",
    "width",
    "warp_yarn_width",
    "weft_yarn_width",
    "binder_yarn_width",
    "binder_yarn_height",
    "binder_yarn_spacing",
    "warp_ratio",
    "binder_ratio",
    "warp_layer",
    "weft_layer",
    "x_voxel",
    "y_voxel",
    "z_voxel",
    "E",
}


def deep_update(base, updates):
    """Recursively merge updates into base, including nested list entries."""
    if isinstance(base, dict) and isinstance(updates, dict):
        for key, value in updates.items():
            if key in base and isinstance(base[key], (dict, list)) and isinstance(value, type(base[key])):
                deep_update(base[key], value)
            else:
                base[key] = value
        return base
    if isinstance(base, list) and isinstance(updates, list):
        for i, value in enumerate(updates):
            while len(base) <= i:
                base.append(None)
            if isinstance(base[i], (dict, list)) and isinstance(value, type(base[i])):
                deep_update(base[i], value)
            else:
                base[i] = value
        return base
    return updates


def parse_path(path):
    """Parse dotted/list paths like geometry.swap[0][1]."""
    tokens = []
    for part in path.split("."):
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)(.*)$", part)
        if not match:
            raise ValueError(f"Invalid path segment: {part}")
        tokens.append(match.group(1))
        rest = match.group(2)
        for idx in re.findall(r"\[(\d+)\]", rest):
            tokens.append(int(idx))
    return tokens


def get_nested(data, path, default=None):
    """Read a dotted/list path from nested structures."""
    cur = data
    for token in parse_path(path):
        if isinstance(token, int):
            if not isinstance(cur, list) or token >= len(cur):
                return default
            cur = cur[token]
        else:
            if not isinstance(cur, dict) or token not in cur:
                return default
            cur = cur[token]
    return cur


def set_nested(data, path, value):
    """Set a dotted/list path in nested structures."""
    cur = data
    tokens = parse_path(path)
    for i, token in enumerate(tokens[:-1]):
        next_token = tokens[i + 1]
        if isinstance(token, int):
            while len(cur) <= token:
                cur.append([] if isinstance(next_token, int) else {})
            if cur[token] is None:
                cur[token] = [] if isinstance(next_token, int) else {}
            cur = cur[token]
        else:
            cur = cur.setdefault(token, [] if isinstance(next_token, int) else {})
    last = tokens[-1]
    if isinstance(last, int):
        while len(cur) <= last:
            cur.append(None)
        cur[last] = value
    else:
        cur[last] = value


def _cast_sample_value(path, value, spec):
    name = path.split(".")[-1]
    value_type = spec.get("type")
    if value_type == "int" or name in INT_FIELDS:
        return int(round(value))
    if value_type == "choice":
        choices = spec["choices"]
        idx = min(int(value * len(choices)), len(choices) - 1)
        return choices[idx]
    return float(value)


def default_lhs_space(rve_type):
    """Return a conservative default LHS parameter space for an RVE type.

    Ranges are intentionally modest to improve robustness.
    Users can override this space from JSON.
    """
    if rve_type in ("woven_weave_2d", "sheared_woven_weave_2d", "layered_woven_weave_2d"):
        space = {
            "geometry.spacing": {"min": 0.8, "max": 1.2},
            "geometry.thick": {"min": 0.15, "max": 0.45},
            "geometry.width": {"min": 0.45, "max": 0.75},
            "geometry.gapsize": {"min": 0.0, "max": 0.05},
            "mesh.x_voxel": {"min": 40, "max": 80, "type": "int"},
            "mesh.y_voxel": {"min": 40, "max": 80, "type": "int"},
            "mesh.z_voxel": {"min": 40, "max": 80, "type": "int"},
        }
        if rve_type == "woven_weave_2d":
            space.update({
                "geometry.warp_count": {"min": 2, "max": 4, "type": "int"},
                "geometry.weft_count": {"min": 2, "max": 4, "type": "int"},
            })
        if rve_type == "sheared_woven_weave_2d":
            space.update({
                "geometry.warp_count": {"min": 3, "max": 5, "type": "int"},
                "geometry.weft_count": {"min": 3, "max": 5, "type": "int"},
                "geometry.angle": {"min": 10.0, "max": 35.0},
            })
        if rve_type == "layered_woven_weave_2d":
            space.update({
                "geometry.warp_count": {"min": 4, "max": 5, "type": "int"},
                "geometry.weft_count": {"min": 4, "max": 5, "type": "int"},
                "geometry.layer_count": {"min": 2, "max": 4, "type": "int"},
            })
        return space

    if rve_type == "orthogonal_weave_3d":
        return {
            "geometry.warp_count": {"min": 4, "max": 6, "type": "int"},
            "geometry.weft_count": {"min": 5, "max": 6, "type": "int"},
            "geometry.warp_spacing": {"min": 0.8, "max": 1.2},
            "geometry.weft_spacing": {"min": 0.8, "max": 1.2},
            "geometry.warp_height": {"min": 0.25, "max": 0.55},
            "geometry.weft_height": {"min": 0.25, "max": 0.55},
            "geometry.warp_ratio": {"min": 1, "max": 2, "type": "int"},
            "geometry.binder_ratio": {"min": 1, "max": 3, "type": "int"},
            "geometry.warp_yarn_width": {"min": 0.35, "max": 0.75},
            "geometry.weft_yarn_width": {"min": 0.35, "max": 0.75},
            "geometry.binder_yarn_width": {"min": 0.04, "max": 0.25},
            "geometry.binder_yarn_height": {"min": 0.04, "max": 0.18},
            "geometry.binder_yarn_spacing": {"min": 0.35, "max": 0.75},
            "geometry.warp_layer": {"min": 2, "max": 3, "type": "int"},
            "geometry.weft_layer": {"min": 4, "max": 5, "type": "int"},
            "mesh.x_voxel": {"min": 30, "max": 60, "type": "int"},
            "mesh.y_voxel": {"min": 30, "max": 60, "type": "int"},
            "mesh.z_voxel": {"min": 30, "max": 60, "type": "int"},
        }

    if rve_type == "angle_interlock_weave_3d":
        return {
            "geometry.warp_count": {"min": 4, "max": 6, "type": "int"},
            "geometry.weft_count": {"min": 7, "max": 8, "type": "int"},
            "geometry.warp_spacing": {"min": 0.8, "max": 1.2},
            "geometry.weft_spacing": {"min": 0.8, "max": 1.2},
            "geometry.warp_height": {"min": 0.08, "max": 0.25},
            "geometry.weft_height": {"min": 0.08, "max": 0.25},
            "geometry.warp_ratio": {"min": 1, "max": 2, "type": "int"},
            "geometry.binder_ratio": {"min": 1, "max": 2, "type": "int"},
            "geometry.warp_yarn_width": {"min": 0.45, "max": 0.8},
            "geometry.weft_yarn_width": {"min": 0.45, "max": 0.8},
            "geometry.binder_yarn_width": {"min": 0.2, "max": 0.45},
            "geometry.binder_yarn_height": {"min": 0.04, "max": 0.12},
            "geometry.binder_yarn_spacing": {"min": 0.35, "max": 0.75},
            "mesh.x_voxel": {"min": 40, "max": 70, "type": "int"},
            "mesh.y_voxel": {"min": 40, "max": 70, "type": "int"},
            "mesh.z_voxel": {"min": 40, "max": 70, "type": "int"},
        }

    raise ValueError(f"Unsupported rve_type: {rve_type}")


def latin_hypercube(space, sample_count, seed=None):
    """Generate LHS samples for a parameter space.

    space format:
        {"geometry.warp_count": {"min": 4, "max": 6, "type": "int"}}
    """
    rng = random.Random(seed)
    paths = list(space.keys())
    per_dim_values = {}

    for path in paths:
        spec = space[path]
        values = []
        for i in range(sample_count):
            u = (i + rng.random()) / sample_count
            if spec.get("type") == "choice":
                raw = u
            else:
                raw = spec["min"] + u * (spec["max"] - spec["min"])
            values.append(_cast_sample_value(path, raw, spec))
        rng.shuffle(values)
        per_dim_values[path] = values

    samples = []
    for i in range(sample_count):
        sample = {}
        for path in paths:
            set_nested(sample, path, per_dim_values[path][i])
        samples.append(sample)
    return samples


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _flatten_all(prefix, value, env):
    """Recursively flatten mixed dict/list to flat underscore names."""
    if isinstance(value, dict):
        for k, v in value.items():
            child = f"{prefix}_{k}" if prefix else k
            _flatten_all(child, v, env)
            env[child] = v
    elif isinstance(value, list):
        for i, v in enumerate(value):
            child = f"{prefix}_{i}" if prefix else f"{i}"
            env[child] = v
            _flatten_all(child, v, env)


def constraint_env(params):
    """Build a flat environment for lhs_ref-style constraint expressions."""
    env = {}
    for section in ("geometry", "mesh", "materials"):
        values = params.get(section, {})
        if isinstance(values, dict):
            env[section] = values
            for key, value in values.items():
                env[key] = value
                env[f"{section}_{key}"] = value
                _flatten_all(key, value, env)
                _flatten_all(f"{section}_{key}", value, env)
    for k, v in SAFE_MATH.items():
        env[k] = v
    return env


def validate_expression_constraints(params, constraints):
    """Validate safe expression constraints from JSON.

    Example:
        "warp_yarn_width < 0.8 * warp_spacing"
    """
    issues = []
    env = constraint_env(params)
    for expr in constraints or []:
        try:
            passed = bool(eval(expr, {"__builtins__": {}}, env))
        except Exception as exc:
            issues.append(f"constraint error `{expr}`: {exc}")
            continue
        if not passed:
            issues.append(f"constraint failed: {expr}")
    return issues


def validate_params(rve_type, params, constraints=None):
    """Validate sampled parameters.

    Returns:
        (ok, issues)

    Invalid samples should be marked failed by batch runner instead of aborting
    the whole DOE/batch calculation.
    """
    issues = []
    geometry = params.get("geometry", {})
    mesh = params.get("mesh", {})
    materials = params.get("materials", {})

    for source_name, source in (("geometry", geometry), ("mesh", mesh)):
        for key, value in source.items():
            if key in INT_FIELDS and not isinstance(value, int):
                issues.append(f"{source_name}.{key} must be int")
            if key in POSITIVE_FIELDS:
                if not _is_number(value) or value <= 0:
                    issues.append(f"{source_name}.{key} must be positive")

    for key in ("x_voxel", "y_voxel", "z_voxel"):
        value = mesh.get(key)
        if value is not None and (not isinstance(value, int) or value < 2):
            issues.append(f"mesh.{key} must be an int >= 2")

    _validate_materials(materials, issues)

    if rve_type in ("woven_weave_2d", "sheared_woven_weave_2d", "layered_woven_weave_2d"):
        spacing = geometry.get("spacing")
        width = geometry.get("width")
        thick = geometry.get("thick")
        if _is_number(spacing) and _is_number(width) and width >= spacing:
            issues.append("geometry.width must be < geometry.spacing")
        if _is_number(thick) and _is_number(spacing) and thick >= spacing:
            issues.append("geometry.thick should be < geometry.spacing")
        if rve_type == "sheared_woven_weave_2d" and geometry.get("angle", 0) == 0:
            issues.append("sheared_woven_weave_2d requires geometry.angle != 0")
        if rve_type == "layered_woven_weave_2d" and geometry.get("layer_count", 0) <= 0:
            issues.append("layered_woven_weave_2d requires geometry.layer_count > 0")
        _validate_swap(geometry, issues)

    if rve_type == "orthogonal_weave_3d":
        _validate_3d_common(geometry, issues)
        warp_layer = geometry.get("warp_layer")
        weft_layer = geometry.get("weft_layer")
        if isinstance(warp_layer, int) and isinstance(weft_layer, int) and warp_layer >= weft_layer:
            issues.append("geometry.warp_layer should be < geometry.weft_layer")
        _validate_swap(geometry, issues)

    if rve_type == "angle_interlock_weave_3d":
        _validate_3d_common(geometry, issues)
        weft_count = geometry.get("weft_count")
        if isinstance(weft_count, int) and weft_count < 3:
            issues.append("geometry.weft_count must be >= 3 for angle-interlock layers")
        _validate_swap(geometry, issues)

    issues.extend(validate_expression_constraints(params, constraints))
    return not issues, issues


def _validate_materials(materials, issues):
    if not isinstance(materials, dict):
        return
    for material_name, values in materials.items():
        if not isinstance(values, dict):
            issues.append(f"materials.{material_name} must be an object")
            continue
        E = values.get("E")
        nu = values.get("nu")
        if E is not None and (not _is_number(E) or E <= 0):
            issues.append(f"materials.{material_name}.E must be positive")
        if nu is not None and (not _is_number(nu) or not (0 < nu < 0.5)):
            issues.append(f"materials.{material_name}.nu must satisfy 0 < nu < 0.5")


def _validate_3d_common(geometry, issues):
    warp_spacing = geometry.get("warp_spacing")
    weft_spacing = geometry.get("weft_spacing")
    warp_yarn_width = geometry.get("warp_yarn_width")
    weft_yarn_width = geometry.get("weft_yarn_width")
    binder_yarn_width = geometry.get("binder_yarn_width")
    binder_yarn_spacing = geometry.get("binder_yarn_spacing")

    if _is_number(warp_yarn_width) and _is_number(warp_spacing) and warp_yarn_width >= warp_spacing:
        issues.append("geometry.warp_yarn_width must be < geometry.warp_spacing")
    if _is_number(weft_yarn_width) and _is_number(weft_spacing) and weft_yarn_width >= weft_spacing:
        issues.append("geometry.weft_yarn_width must be < geometry.weft_spacing")
    if _is_number(binder_yarn_width) and _is_number(binder_yarn_spacing) and binder_yarn_width >= binder_yarn_spacing:
        issues.append("geometry.binder_yarn_width must be < geometry.binder_yarn_spacing")


def _validate_swap(geometry, issues):
    swap = geometry.get("swap")
    if swap is None:
        return
    warp_count = geometry.get("warp_count")
    weft_count = geometry.get("weft_count")
    if not isinstance(swap, list):
        issues.append("geometry.swap must be a list")
        return
    for i, pair in enumerate(swap):
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            issues.append(f"geometry.swap[{i}] must be [index0, index1]")
            continue
        if not all(isinstance(v, int) for v in pair):
            issues.append(f"geometry.swap[{i}] values must be int")
            continue
        # For this project convention, pair[0] indexes weft-direction positions,
        # pair[1] indexes warp-direction positions.
        if isinstance(weft_count, int) and not (0 <= pair[0] < weft_count):
            issues.append(f"geometry.swap[{i}][0] must satisfy 0 <= value < weft_count")
        if isinstance(warp_count, int) and not (0 <= pair[1] < warp_count):
            issues.append(f"geometry.swap[{i}][1] must satisfy 0 <= value < warp_count")


def generate_lhs_cases(
    rve_type,
    sample_count,
    seed=None,
    start_index=1,
    end_index=None,
    prefix="case",
    base_overrides=None,
    space=None,
    constraints=None,
    max_sampling_iterations=100,
):
    """Generate valid case dictionaries with constrained LHS resampling.

    Candidates that fail built-in checks or expression constraints are rejected
    during sampling. Returned cases are therefore all valid. If not enough valid
    candidates can be found, RuntimeError is raised instead of returning a
    partial invalid batch.
    """
    if end_index is not None:
        if end_index < start_index:
            raise ValueError("end_index must be >= start_index")
        sample_count = end_index - start_index + 1

    space = space or default_lhs_space(rve_type)
    cases = []
    rejected = []
    width = max(4, len(str(start_index + sample_count - 1)))
    iteration = 0

    while len(cases) < sample_count and iteration < max_sampling_iterations:
        current_seed = None if seed is None else seed + iteration
        need = sample_count - len(cases)
        # Oversample each iteration so constrained spaces can still fill quickly.
        candidate_count = max(need, sample_count)
        lhs_samples = latin_hypercube(space, candidate_count, seed=current_seed)

        for sampled_overrides in lhs_samples:
            overrides = deepcopy(base_overrides or {})
            deep_update(overrides, sampled_overrides)
            params = init_model_params(rve_type, overrides)
            ok, issues = validate_params(rve_type, params, constraints=constraints)
            if not ok:
                rejected.append({"sampled_overrides": sampled_overrides, "issues": issues})
                continue

            index = start_index + len(cases)
            case_id = f"{prefix}{index:0{width}d}"
            cases.append({
                "case_id": case_id,
                "index": index,
                "rve_type": rve_type,
                "params": params,
                "sampled_overrides": sampled_overrides,
                "valid": True,
                "issues": [],
            })
            if len(cases) >= sample_count:
                break

        iteration += 1

    if len(cases) < sample_count:
        raise RuntimeError(
            f"Unable to generate {sample_count} valid LHS samples after "
            f"{max_sampling_iterations} iterations. Accepted={len(cases)}, "
            f"rejected={len(rejected)}. Last rejected={rejected[-3:]}"
        )

    return cases
