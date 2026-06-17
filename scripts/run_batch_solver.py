"""Run solver calculations for all ready cases in an existing batch directory.

Example:
    python scripts/run_batch_solver.py --batch-dir output/orthogonal_weave_3d/batch0003
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rve_batch.batch_solver import run_batch_solver


DEFAULT_SOLVER_EXE = Path("D:/Demx_softwares/2025b/Virgo_R2025b_win64/bin/vg_solver.exe")
DEFAULT_SOLVER_CONFIG = Path("D:/Demx_softwares/2025C/Plexian_R2025c_fixed_win64/res/PlexianConfig.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-dir", required=True, help="Batch directory, e.g. output/orthogonal_weave_3d/batch0003")
    parser.add_argument("--solver-exe", default=DEFAULT_SOLVER_EXE)
    parser.add_argument("--solver-config", default=DEFAULT_SOLVER_CONFIG)
    parser.add_argument("--timeout", type=int, default=None, help="Timeout per case in seconds")
    parser.add_argument("--overwrite", action="store_true", help="Rerun cases even if solver_status.json already succeeded")
    parser.add_argument("--stop-on-error", action="store_true", help="Stop after first solver failure")
    parser.add_argument("--no-postprocess-results", action="store_true", help="Do not merge geometry/Material into solver result VTU")
    parser.add_argument(
        "--result-vtu-relative",
        default=None,
        help="Result VTU path relative to each case dir; default user_RVE_results/rve/data/user_RVE_step0000.vtu",
    )
    args = parser.parse_args()

    summary = run_batch_solver(
        batch_dir=Path(args.batch_dir),
        solver_exe=Path(args.solver_exe),
        solver_config=Path(args.solver_config),
        timeout=args.timeout,
        overwrite=args.overwrite,
        continue_on_error=not args.stop_on_error,
        postprocess_results=not args.no_postprocess_results,
        result_vtu_relative=args.result_vtu_relative,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    main()
