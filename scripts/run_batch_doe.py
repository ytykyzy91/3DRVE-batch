"""Run LHS DOE batch modelling.

Examples:
    python scripts/run_batch_doe.py --config configs/batch_doe.example.json

    python scripts/run_batch_doe.py \
        --rve-type orthogonal_weave_3d \
        --sample-count 5 \
        --seed 42 \
        --start-index 1 \
        --prefix case \
        --batch-name batch0001
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"
REPO_ROOT = PROJECT_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rve_batch.batch_calculation import run_lhs_batch, run_lhs_batch_from_config
from rve_batch.modelling import MODEL_TYPES


DEFAULT_TEXGEN_LIB_PATH = REPO_ROOT / "Texgen_source" / "texgen3.9" / "TexGen" / "Python" / "libxtra"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None, help="JSON config for DOE/batch run")
    parser.add_argument("--rve-type", default="orthogonal_weave_3d", choices=MODEL_TYPES)
    parser.add_argument("--sample-count", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--start-index", type=int, default=1)
    parser.add_argument("--end-index", type=int, default=None)
    parser.add_argument("--prefix", default="case")
    parser.add_argument("--batch-name", default=None)
    parser.add_argument("--output-root", default=PROJECT_DIR / "output")
    parser.add_argument("--type-dir", default=None, help="Upper output directory under output-root; use empty string to write directly under output-root")
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--no-skip-completed", action="store_true")
    parser.add_argument("--rerun-failed", action="store_true")
    parser.add_argument("--texgen-lib-path", default=DEFAULT_TEXGEN_LIB_PATH)
    args = parser.parse_args()

    if args.config:
        summary = run_lhs_batch_from_config(args.config, texgen_lib_path=args.texgen_lib_path)
    else:
        summary = run_lhs_batch(
            rve_type=args.rve_type,
            texgen_lib_path=Path(args.texgen_lib_path),
            output_root=Path(args.output_root),
            type_dir=args.type_dir,
            sample_count=args.sample_count,
            seed=args.seed,
            start_index=args.start_index,
            end_index=args.end_index,
            prefix=args.prefix,
            batch_name=args.batch_name,
            max_workers=args.max_workers,
            skip_completed=not args.no_skip_completed,
            rerun_failed=args.rerun_failed,
        )

    print(json.dumps(summary, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    main()
