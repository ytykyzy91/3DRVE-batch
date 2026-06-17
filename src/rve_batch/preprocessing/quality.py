"""Mesh and field-data quality checks."""

from __future__ import annotations

from pathlib import Path

import pyvista as pv


def check_required_cell_data(vtu_path, required_fields=None):
    """Check whether a VTU file contains required CellData fields."""
    required_fields = required_fields or ["YarnIndex", "Material"]
    mesh = pv.read(Path(vtu_path))
    missing = [field for field in required_fields if field not in mesh.cell_data]
    return {
        "path": str(vtu_path),
        "n_points": mesh.n_points,
        "n_cells": mesh.n_cells,
        "cell_data": list(mesh.cell_data.keys()),
        "missing": missing,
        "ok": not missing,
    }
