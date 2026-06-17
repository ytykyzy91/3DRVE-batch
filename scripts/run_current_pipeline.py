"""Run the current orthogonal 3D weave preprocessing pipeline inside 3DRVE_batch.

Success criterion for this stage:
    data/intermediate/Voxel_ortho_fixed.vtu exists and contains CellData fields
    YarnIndex and Material.

Run from 3DRVE_batch:
    conda activate py39
    python scripts/run_current_pipeline.py
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

from rve_batch.modelling import MODEL_TYPES, build_model, init_model_params
from rve_batch.preprocessing.material_cell_data import add_material_cell_data
from rve_batch.preprocessing.quality import check_required_cell_data
from rve_batch.preprocessing.vtu_order import fix_vtu_node_order


DEFAULT_TEXGEN_LIB_PATH = REPO_ROOT / "Texgen_source" / "texgen3.9" / "TexGen" / "Python" / "libxtra"


def load_param_overrides(params_json, rve_type):
    """Load modelling parameter overrides from JSON.

    JSON may be either:
    1. A mapping keyed by rve_type, e.g. {"orthogonal_weave_3d": {...}}
    2. A direct override object containing "mesh" and/or "geometry".
    """
    if not params_json:
        return {}

    params_json = Path(params_json)
    with params_json.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if rve_type in data:
        return data[rve_type]
    if "mesh" in data or "geometry" in data:
        return data
    return {}


def update_analysis_template_rve_path(vtu_name):
    """If a local copied analysis template exists, update its rvePath field."""
    analysis_json = PROJECT_DIR / "configs" / "tools" / "user_RVE_analysis.json"
    if not analysis_json.exists():
        return None

    with analysis_json.open("r", encoding="utf-8") as f:
        data = json.load(f)
    data["Defs"]["Composite"]["Settings"]["rvePath"] = vtu_name
    with analysis_json.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")
    return analysis_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rve-type", default="orthogonal_weave_3d", choices=MODEL_TYPES)
    parser.add_argument("--params-json", default=None, help="JSON file with parameter overrides for one or more rve_type values")
    parser.add_argument("--output-dir", default=PROJECT_DIR / "data" / "intermediate")
    parser.add_argument("--texgen-lib-path", default=DEFAULT_TEXGEN_LIB_PATH)
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    overrides = load_param_overrides(args.params_json, args.rve_type)
    params = init_model_params(args.rve_type, overrides)
    raw_vtu = build_model(args.rve_type, output_dir, Path(args.texgen_lib_path), params)
    print(f"Raw VTU: {raw_vtu}")

    fixed_vtu = output_dir / f"{raw_vtu.stem}_fix.vtu"
    stats = fix_vtu_node_order(raw_vtu, fixed_vtu, binary=True)
    print(f"Fixed VTU: {fixed_vtu}")
    print(f"Fix stats: {stats}")

    add_material_cell_data(fixed_vtu, fixed_vtu)
    print(f"Material CellData added: {fixed_vtu}")

    analysis_json = update_analysis_template_rve_path(fixed_vtu.name)
    if analysis_json:
        print(f"Updated local analysis template: {analysis_json}")

    quality = check_required_cell_data(fixed_vtu, ["YarnIndex", "Material"])
    print(f"Quality: {quality}")
    if not quality["ok"]:
        raise RuntimeError(f"Missing CellData fields: {quality['missing']}")

    print("Pipeline succeeded.")
    print(f"Final VTU: {fixed_vtu}")


if __name__ == "__main__":
    main()
