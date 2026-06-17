"""Batch DOE modelling and preprocessing runner."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import shutil
import traceback
from pathlib import Path

from rve_batch.doe import generate_lhs_cases
from rve_batch.modelling import build_model
from rve_batch.preprocessing.material_cell_data import add_material_cell_data
from rve_batch.solver.analysis_config import render_analysis_config
from rve_batch.preprocessing.quality import check_required_cell_data
from rve_batch.preprocessing.vtu_order import fix_vtu_node_order
from rve_batch.visualization import save_vtu_isometric_screenshot


def write_json(path, data):
    """Write JSON with stable UTF-8 formatting."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")


def read_json(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def default_batch_name(start_index):
    return f"batch{start_index:04d}"


def cleanup_case_files(case_dir, final_vtu):
    """Keep only final *_fix.vtu plus JSON metadata in a case directory."""
    case_dir = Path(case_dir)
    final_vtu = Path(final_vtu).resolve() if final_vtu else None
    for path in case_dir.glob("*.vtu"):
        if final_vtu and path.resolve() == final_vtu:
            continue
        path.unlink(missing_ok=True)


def _resolve_case_output(case_dir, output_path):
    if not output_path:
        return None
    path = Path(output_path)
    if path.is_absolute():
        return path
    direct = case_dir / path
    if direct.exists():
        return direct
    return case_dir / path.name


def inspect_existing_case(case, case_dir, screenshot_config=None, analysis_template=None):
    """Inspect whether an existing case can be skipped."""
    case_dir = Path(case_dir)
    status_path = case_dir / "status.json"
    if not status_path.exists():
        return {"status": "missing", "reason": "missing status.json"}

    try:
        status = read_json(status_path)
    except Exception as exc:
        return {"status": "invalid", "reason": f"cannot read status.json: {exc}"}

    existing_status = status.get("status")
    if existing_status == "fail":
        return {"status": "failed", "reason": "existing status is fail", "existing": status}
    if existing_status != "success":
        return {"status": "incomplete", "reason": f"existing status is {existing_status}", "existing": status}

    input_path = case_dir / "input_params.json"
    if not input_path.exists():
        return {"status": "incomplete", "reason": "missing input_params.json", "existing": status}
    try:
        existing_params = read_json(input_path)
    except Exception as exc:
        return {"status": "invalid", "reason": f"cannot read input_params.json: {exc}", "existing": status}
    if existing_params != case["params"]:
        return {"status": "stale", "reason": "input_params.json differs from current sampled params", "existing": status}

    final_vtu = _resolve_case_output(case_dir, status.get("outputs", {}).get("final_vtu"))
    if not final_vtu or not final_vtu.exists():
        return {"status": "incomplete", "reason": "missing final VTU", "existing": status}

    if analysis_template and not (case_dir / "user_RVE_analysis.json").exists():
        return {"status": "incomplete", "reason": "missing user_RVE_analysis.json", "existing": status}

    screenshot_config = screenshot_config or {}
    if screenshot_config.get("enabled", False):
        screenshot_name = screenshot_config.get("filename", f"{case['case_id']}_iso.png")
        if not (case_dir / screenshot_name).exists():
            return {"status": "incomplete", "reason": "missing screenshot", "existing": status}

    return {"status": "completed", "reason": "existing case is complete", "existing": status}


def skipped_case_status(case, reason, existing=None):
    return {
        "case_id": case["case_id"],
        "rve_type": case["rve_type"],
        "status": "skipped",
        "stage": "skip",
        "valid": case["valid"],
        "issues": case["issues"],
        "reason": reason,
        "outputs": (existing or {}).get("outputs", {}),
    }


def run_one_case(case, case_dir, texgen_lib_path, screenshot_config=None, analysis_template=None):
    """Run modelling + VTU fix + Material CellData for one sampled case."""
    case_dir = Path(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)

    write_json(case_dir / "input_params.json", case["params"])
    write_json(case_dir / "sampled_overrides.json", case.get("sampled_overrides", {}))

    status = {
        "case_id": case["case_id"],
        "rve_type": case["rve_type"],
        "status": "pending",
        "valid": case["valid"],
        "issues": case["issues"],
        "outputs": {},
    }
    print("*"*50, "\n", "Running case:", case["case_id"], "Valid:", case["valid"], "Issues:", case["issues"])
    if not case["valid"]:
        status["status"] = "fail"
        status["stage"] = "validate"
        write_json(case_dir / "status.json", status)
        return status

    try:
        status["status"] = "running"
        status["stage"] = "model"
        write_json(case_dir / "status.json", status)

        params = case["params"]
        params.setdefault("mesh", {})["filename"] = f"{case['case_id']}.vtu"
        raw_vtu = build_model(case["rve_type"], case_dir, texgen_lib_path, params)
        status["outputs"]["raw_vtu"] = str(raw_vtu)

        status["stage"] = "fix_vtu"
        final_vtu = case_dir / f"{raw_vtu.stem}_fix.vtu"
        fix_stats = fix_vtu_node_order(raw_vtu, final_vtu, binary=True)
        status["outputs"]["fix_stats"] = fix_stats
        status["outputs"]["final_vtu"] = str(final_vtu)

        status["stage"] = "material_cell_data"
        add_material_cell_data(final_vtu, final_vtu)

        status["stage"] = "quality"
        quality = check_required_cell_data(final_vtu, ["YarnIndex", "Material"])
        status["outputs"]["quality"] = quality
        if not quality["ok"]:
            raise RuntimeError(f"Missing CellData fields: {quality['missing']}")

        if analysis_template:
            status["stage"] = "analysis_config"
            analysis_json = case_dir / "user_RVE_analysis.json"
            render_analysis_config(
                analysis_template,
                analysis_json,
                {
                    "rve_path": final_vtu.name,
                    "material_overrides": params.get("materials", {}),
                },
            )
            status["outputs"]["analysis_json"] = str(analysis_json)

        screenshot_config = screenshot_config or {}
        if screenshot_config.get("enabled", False):
            status["stage"] = "screenshot"
            screenshot_path = case_dir / screenshot_config.get("filename", f"{case['case_id']}_iso.png")
            save_vtu_isometric_screenshot(
                final_vtu,
                screenshot_path,
                hide_yarn_index=screenshot_config.get("hide_yarn_index", 0),
                window_size=tuple(screenshot_config.get("window_size", [1200, 900])),
                background=screenshot_config.get("background", "white"),
                scalars=screenshot_config.get("scalars", "YarnIndex"),
                parallel_projection=screenshot_config.get("parallel_projection", True),
                show_edges=screenshot_config.get("show_edges", False),
                show_scalar_bar=screenshot_config.get("show_scalar_bar", False),
            )
            status["outputs"]["screenshot"] = str(screenshot_path)

        cleanup_case_files(case_dir, final_vtu)
        status["status"] = "success"
        status["stage"] = "done"
        write_json(case_dir / "status.json", status)
        return status

    except Exception as exc:
        status["status"] = "fail"
        status["error"] = str(exc)
        status["traceback"] = traceback.format_exc()
        cleanup_case_files(case_dir, None)
        write_json(case_dir / "status.json", status)
        return status


def run_lhs_batch(
    rve_type,
    texgen_lib_path,
    output_root="output",
    type_dir=None,
    sample_count=1,
    seed=None,
    start_index=1,
    end_index=None,
    prefix="case",
    batch_name=None,
    base_overrides=None,
    space=None,
    constraints=None,
    screenshot_config=None,
    max_sampling_iterations=100,
    analysis_template=None,
    max_workers=1,
    skip_completed=True,
    rerun_failed=False,
):
    """Generate LHS cases and run batch modelling.

    Output layout defaults to:
        output/<type_dir>/<batch_name>/<case_id>/
    Set type_dir to "" to use:
        output/<batch_name>/<case_id>/
    """
    output_root = Path(output_root)
    batch_name = batch_name or default_batch_name(start_index)
    if type_dir is None:
        type_dir = rve_type
    batch_dir = output_root / batch_name if type_dir == "" else output_root / type_dir / batch_name
    batch_dir.mkdir(parents=True, exist_ok=True)

    cases = generate_lhs_cases(
        rve_type=rve_type,
        sample_count=sample_count,
        seed=seed,
        start_index=start_index,
        end_index=end_index,
        prefix=prefix,
        base_overrides=base_overrides,
        space=space,
        constraints=constraints,
        max_sampling_iterations=max_sampling_iterations,
    )

    batch_config = {
        "rve_type": rve_type,
        "sample_count": len(cases),
        "seed": seed,
        "start_index": start_index,
        "end_index": end_index,
        "prefix": prefix,
        "batch_name": batch_name,
        "output_root": str(output_root),
        "type_dir": type_dir,
        "batch_dir": str(batch_dir),
        "base_overrides": base_overrides or {},
        "space": space,
        "constraints": constraints or [],
        "screenshot": screenshot_config or {},
        "max_sampling_iterations": max_sampling_iterations,
        "analysis_template": str(analysis_template) if analysis_template else None,
        "max_workers": max_workers,
        "skip_completed": skip_completed,
        "rerun_failed": rerun_failed,
    }
    write_json(batch_dir / "batch_config.json", batch_config)

    def run_or_skip_case(case):
        case_dir = batch_dir / case["case_id"]
        existing = inspect_existing_case(
            case,
            case_dir,
            screenshot_config=screenshot_config,
            analysis_template=analysis_template,
        )
        if skip_completed and existing["status"] == "completed":
            return skipped_case_status(case, existing["reason"], existing.get("existing"))
        if not rerun_failed and existing["status"] == "failed":
            return skipped_case_status(case, existing["reason"], existing.get("existing"))
        return run_one_case(
            case,
            case_dir,
            texgen_lib_path,
            screenshot_config=screenshot_config,
            analysis_template=analysis_template,
        )

    statuses = []
    max_workers = max(1, int(max_workers or 1))
    if max_workers == 1:
        for case in cases:
            statuses.append(run_or_skip_case(case))
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_case = {executor.submit(run_or_skip_case, case): case for case in cases}
            for future in as_completed(future_to_case):
                statuses.append(future.result())
        statuses.sort(key=lambda item: item.get("case_id", ""))

    summary = {
        "rve_type": rve_type,
        "batch_name": batch_name,
        "sample_count": len(cases),
        "success": sum(1 for s in statuses if s["status"] == "success"),
        "fail": sum(1 for s in statuses if s["status"] == "fail"),
        "skipped": sum(1 for s in statuses if s["status"] == "skipped"),
        "cases": [
            {
                "case_id": s["case_id"],
                "status": s["status"],
                "issues": s.get("issues", []),
                "final_vtu": s.get("outputs", {}).get("final_vtu"),
                "reason": s.get("reason"),
                "error": s.get("error"),
            }
            for s in statuses
        ],
    }
    write_json(batch_dir / "batch_summary.json", summary)
    return summary


def run_lhs_batch_from_config(config_path, texgen_lib_path=None):
    """Run LHS batch from JSON config."""
    config_path = Path(config_path)
    config = read_json(config_path)
    if texgen_lib_path is None:
        texgen_lib_path = config.get("texgen_lib_path")
    if texgen_lib_path is None:
        raise ValueError("texgen_lib_path must be provided by config or CLI")

    return run_lhs_batch(
        rve_type=config["rve_type"],
        texgen_lib_path=Path(texgen_lib_path),
        output_root=config.get("output_root", "output"),
        type_dir=config.get("type_dir", config["rve_type"]),
        sample_count=config.get("sample_count", 1),
        seed=config.get("seed"),
        start_index=config.get("start_index", 1),
        end_index=config.get("end_index", config.get("start_index", 1)),
        prefix=config.get("prefix", "case"),
        batch_name=config.get("batch_name"),
        base_overrides=config.get("base_overrides"),
        space=config.get("lhs_space"),
        constraints=config.get("constraints"),
        screenshot_config=config.get("screenshot"),
        max_sampling_iterations=config.get("max_sampling_iterations", 100),
        analysis_template=config.get("analysis_template", "configs/solver/user_RVE_analysis.json"),
        max_workers=config.get("max_workers", 1),
        skip_completed=config.get("skip_completed", True),
        rerun_failed=config.get("rerun_failed", False),
    )
