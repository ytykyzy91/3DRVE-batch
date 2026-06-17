"""VTU visualization helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pyvista as pv


def save_vtu_isometric_screenshot(
    vtu_path,
    screenshot_path,
    hide_yarn_index=0,
    window_size=(1200, 900),
    background="white",
    scalars="YarnIndex",
    parallel_projection=True,
    show_edges=False,
    show_scalar_bar=False,
):
    """Save an isometric screenshot of a VTU mesh.

    Cells with YarnIndex == hide_yarn_index are hidden before rendering.
    The cloud map defaults to YarnIndex and the camera defaults to orthographic
    isometric view.
    """
    vtu_path = Path(vtu_path)
    screenshot_path = Path(screenshot_path)
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)

    mesh = pv.read(vtu_path)
    if "YarnIndex" in mesh.cell_data and hide_yarn_index is not None:
        mask = np.asarray(mesh.cell_data["YarnIndex"]) != hide_yarn_index
        mesh = mesh.extract_cells(mask)

    active_scalars = scalars if scalars in mesh.cell_data else None

    plotter = pv.Plotter(off_screen=True, window_size=window_size)
    plotter.set_background(background)
    plotter.add_mesh(mesh, scalars=active_scalars, show_edges=show_edges, show_scalar_bar=show_scalar_bar)
    plotter.camera_position = "iso"
    if parallel_projection:
        plotter.enable_parallel_projection()
    plotter.reset_camera()
    plotter.show(screenshot=str(screenshot_path), auto_close=True)
    return screenshot_path
