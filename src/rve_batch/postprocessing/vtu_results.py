"""Merge generated geometry with solver result VTU data."""

from __future__ import annotations

from pathlib import Path

import vtk


def _read_unstructured_grid(vtu_path):
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(str(vtu_path))
    reader.Update()
    return reader.GetOutput()


def _write_unstructured_grid(grid, vtu_path):
    writer = vtk.vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(vtu_path))
    writer.SetInputData(grid)
    writer.SetCompressorTypeToZLib()
    ok = writer.Write()
    if ok != 1:
        raise RuntimeError(f"Failed to write VTU: {vtu_path}")


def merge_geometry_material_to_result(geom_vtu, data_vtu, output_vtu=None):
    """Merge generated VTU geometry with solver result VTU data.

    This follows the verified add_geo_to_vtu.py workflow:
    - use geom_vtu as the base grid, preserving its nodes/cells/Material;
    - append PointData arrays from data_vtu to the geometry grid;
    - append CellData arrays from data_vtu to the geometry grid;
    - write the merged grid to output_vtu, defaulting to in-place data_vtu.
    """
    geom_vtu = Path(geom_vtu)
    data_vtu = Path(data_vtu)
    output_vtu = Path(output_vtu) if output_vtu is not None else data_vtu

    geom = _read_unstructured_grid(geom_vtu)
    data = _read_unstructured_grid(data_vtu)

    if geom.GetNumberOfPoints() != data.GetNumberOfPoints() or geom.GetNumberOfCells() != data.GetNumberOfCells():
        raise RuntimeError(
            "Point/Cell count mismatch: "
            f"geom=({geom.GetNumberOfPoints()}, {geom.GetNumberOfCells()}), "
            f"data=({data.GetNumberOfPoints()}, {data.GetNumberOfCells()})"
        )

    geom_point_data = geom.GetPointData()
    data_point_data = data.GetPointData()
    for i in range(data_point_data.GetNumberOfArrays()):
        arr = data_point_data.GetArray(i)
        if arr is not None:
            geom_point_data.AddArray(arr)

    geom_cell_data = geom.GetCellData()
    data_cell_data = data.GetCellData()
    for i in range(data_cell_data.GetNumberOfArrays()):
        arr = data_cell_data.GetArray(i)
        if arr is not None:
            geom_cell_data.AddArray(arr)

    _write_unstructured_grid(geom, output_vtu)
    return {
        "geom_vtu": str(geom_vtu),
        "data_vtu": str(data_vtu),
        "output_vtu": str(output_vtu),
        "points": geom.GetNumberOfPoints(),
        "cells": geom.GetNumberOfCells(),
        "point_data": [geom.GetPointData().GetArrayName(i) for i in range(geom.GetPointData().GetNumberOfArrays())],
        "cell_data": [geom.GetCellData().GetArrayName(i) for i in range(geom.GetCellData().GetNumberOfArrays())],
    }


def default_solver_result_vtu(case_dir):
    """Return the default solver result VTU path for a case directory."""
    return Path(case_dir) / "user_RVE_results" / "rve" / "data" / "user_RVE_step0000.vtu"
