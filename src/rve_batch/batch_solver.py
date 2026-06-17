"""Run solver calculations for an existing generated batch."""

from __future__ import annotations

import json
import traceback
from pathlib import Path

from rve_batch.postprocessing.vtu_results import default_solver_result_vtu, merge_geometry_material_to_result
from rve_batch.solver.plexian_solver import run_solver


def read_json(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")


def discover_case_dirs(batch_dir):
    """Return case directories that contain input/status files."""
    batch_dir = Path(batch_dir)
    return sorted(
        p for p in batch_dir.iterdir()
        if p.is_dir() and (p / "status.json").exists()
    )


def _resolve_case_output(case_dir, output_path):
    if not output_path:
        return None
    path = Path(output_path)
    if path.is_absolute():
        return path
    direct = Path(case_dir) / path
    if direct.exists():
        return direct
    return Path(case_dir) / path.name


def is_case_ready_for_solver(case_dir):
    """Check whether a case has successful modelling outputs for calculation."""
    case_dir = Path(case_dir)
    status_path = case_dir / "status.json"
    analysis_json = case_dir / "user_RVE_analysis.json"
    if not status_path.exists():
        return False, "missing status.json"
    status = read_json(status_path)
    if status.get("status") != "success":
        return False, f"case status is {status.get('status')}"
    if not analysis_json.exists():
        return False, "missing user_RVE_analysis.json"
    final_vtu = _resolve_case_output(case_dir, status.get("outputs", {}).get("final_vtu"))
    if final_vtu and not final_vtu.exists():
        return False, "missing final VTU"
    return True, "ready"


def run_case_solver(
    case_dir,
    solver_exe,
    solver_config,
    timeout=None,
    overwrite=False,
    postprocess_results=True,
    result_vtu_relative=None,
):
    """Run solver for one generated case directory."""
    case_dir = Path(case_dir)
    solver_status_path = case_dir / "solver_status.json"
    if solver_status_path.exists() and not overwrite:
        existing = read_json(solver_status_path)
        if existing.get("status") == "success":
            if postprocess_results and "postprocess" not in existing:
                try:
                    case_status = read_json(case_dir / "status.json")
                    geom_vtu = _resolve_case_output(case_dir, case_status.get("outputs", {}).get("final_vtu"))
                    data_vtu = case_dir / result_vtu_relative if result_vtu_relative else default_solver_result_vtu(case_dir)
                    existing["postprocess"] = merge_geometry_material_to_result(geom_vtu, data_vtu, data_vtu)
                    write_json(solver_status_path, existing)
                    return {
                        "case_id": case_dir.name,
                        "status": "postprocessed",
                        "reason": "solver already success; postprocess added",
                        "postprocess": existing["postprocess"],
                    }
                except Exception as exc:
                    return {
                        "case_id": case_dir.name,
                        "status": "fail",
                        "reason": "solver already success but postprocess failed",
                        "error": str(exc),
                        "traceback": traceback.format_exc(),
                    }
            return {
                "case_id": case_dir.name,
                "status": "skipped",
                "reason": "solver_status.json already success",
            }

    ready, reason = is_case_ready_for_solver(case_dir)
    if not ready:
        result = {
            "case_id": case_dir.name,
            "status": "skipped",
            "reason": reason,
        }
        write_json(solver_status_path, result)
        return result

    try:
        meta = run_solver(
            solver_exe=solver_exe,
            solver_config=solver_config,
            analysis_json=case_dir / "user_RVE_analysis.json",
            workdir=case_dir,
            log_file=case_dir / "solver.log",
            timeout=timeout,
        )
        result = {
            "case_id": case_dir.name,
            "status": "success" if meta["ok"] else "fail",
            "solver": meta,
        }

        if meta["ok"] and postprocess_results:
            case_status = read_json(case_dir / "status.json")
            geom_vtu = _resolve_case_output(case_dir, case_status.get("outputs", {}).get("final_vtu"))
            data_vtu = case_dir / result_vtu_relative if result_vtu_relative else default_solver_result_vtu(case_dir)
            postprocess = merge_geometry_material_to_result(geom_vtu, data_vtu, data_vtu)
            result["postprocess"] = postprocess

        write_json(solver_status_path, result)
        return result
    except Exception as exc:
        result = {
            "case_id": case_dir.name,
            "status": "fail",
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        write_json(solver_status_path, result)
        return result


def run_batch_solver(
    batch_dir,
    solver_exe,
    solver_config,
    timeout=None,
    overwrite=False,
    continue_on_error=True,
    postprocess_results=True,
    result_vtu_relative=None,
):
    """Run solver for all ready cases in a batch directory."""
    batch_dir = Path(batch_dir)
    results = []
    for case_dir in discover_case_dirs(batch_dir):
        result = run_case_solver(
            case_dir=case_dir,
            solver_exe=solver_exe,
            solver_config=solver_config,
            timeout=timeout,
            overwrite=overwrite,
            postprocess_results=postprocess_results,
            result_vtu_relative=result_vtu_relative,
        )
        results.append(result)
        if result.get("status") == "fail" and not continue_on_error:
            break

    summary = {
        "batch_dir": str(batch_dir),
        "total": len(results),
        "success": sum(1 for r in results if r.get("status") == "success"),
        "fail": sum(1 for r in results if r.get("status") == "fail"),
        "skipped": sum(1 for r in results if r.get("status") == "skipped"),
        "postprocessed": sum(1 for r in results if r.get("status") == "postprocessed"),
        "cases": results,
    }
    write_json(batch_dir / "solver_batch_summary.json", summary)
    return summary
