"""Plexian/Virgo solver runner."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path


def run_solver(solver_exe, solver_config, analysis_json, workdir, log_file=None, timeout=None):
    """Run the solver for one case and return execution metadata.

    Equivalent to:
        vg_solver.exe -config PlexianConfig.json -comp user_RVE_analysis.json
    """
    solver_exe = Path(solver_exe)
    solver_config = Path(solver_config)
    analysis_json = Path(analysis_json)
    workdir = Path(workdir)
    log_file = Path(log_file) if log_file else workdir / "solver.log"

    command = [
        str(solver_exe),
        "-config",
        str(solver_config),
        "-comp",
        str(analysis_json.name),
    ]

    started = time.time()
    result = subprocess.run(
        command,
        cwd=workdir,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    elapsed = time.time() - started

    log_file.write_text(result.stdout or "", encoding="utf-8", errors="replace")

    return {
        "command": command,
        "workdir": str(workdir),
        "analysis_json": str(analysis_json),
        "log_file": str(log_file),
        "returncode": result.returncode,
        "elapsed_seconds": elapsed,
        "ok": result.returncode == 0,
    }
