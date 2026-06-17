"""Material CellData generation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pyvista as pv


def add_material_cell_data(input_vtu, output_vtu=None):
    """Create Material CellData from YarnIndex.

    YarnIndex == -1 -> Material = 1
    YarnIndex >= 0  -> Material = 2
    """
    input_vtu = Path(input_vtu)
    output_vtu = Path(output_vtu) if output_vtu is not None else input_vtu

    mesh = pv.read(input_vtu)
    if "YarnIndex" not in mesh.cell_data:
        raise KeyError(f"YarnIndex not found in CellData: {input_vtu}")

    yarn_index = mesh.cell_data["YarnIndex"]
    mesh.cell_data["Material"] = np.where(yarn_index == -1, 1, 2).astype(np.int32)

    mesh._association_bitarray_names = {}
    mesh._association_complex_names = {}
    mesh.save(output_vtu)
    return output_vtu
