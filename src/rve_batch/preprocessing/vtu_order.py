"""VTU cell node-order correction."""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pyvista as pv
import vtk


def vtu_to_64bit_ascii(input_vtu, output_vtu=None):
    """Convert VTU arrays to 64-bit where needed and save as ASCII VTU."""
    input_vtu = Path(input_vtu)
    output_vtu = Path(output_vtu) if output_vtu else input_vtu.with_name(input_vtu.stem + "_ascii.vtu")

    mesh = pv.read(input_vtu)
    if mesh.points.dtype != np.float64:
        mesh.points = mesh.points.astype(np.float64)

    ugrid = mesh.cast_to_unstructured_grid()
    old_cells = ugrid.GetCells()
    old_conn = old_cells.GetConnectivityArray()
    old_offs = old_cells.GetOffsetsArray()
    cell_types = ugrid.GetCellTypesArray()

    conn64 = vtk.vtkIdTypeArray()
    conn64.DeepCopy(old_conn)
    offs64 = vtk.vtkIdTypeArray()
    offs64.DeepCopy(old_offs)

    new_cells = vtk.vtkCellArray()
    new_cells.SetData(offs64, conn64)
    ugrid.SetCells(cell_types, new_cells)

    writer = vtk.vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(output_vtu))
    writer.SetInputData(ugrid)
    writer.SetDataModeToAscii()
    writer.Write()
    return output_vtu


def signed_tet_det(p0, p1, p2, p3):
    """Six times the signed tetrahedron volume."""
    j = np.column_stack((p1 - p0, p2 - p0, p3 - p0))
    return np.linalg.det(j)


def fix_tet4(node_ids, coords, eps=1e-15):
    """Fix 4-node tetrahedron orientation so det > 0."""
    if len(node_ids) != 4:
        return node_ids

    det = signed_tet_det(coords[0], coords[1], coords[2], coords[3])
    if det < -eps:
        return [node_ids[0], node_ids[2], node_ids[1], node_ids[3]]
    return node_ids


def order_quad_counterclockwise(node_ids, coords):
    """Order four coplanar points counter-clockwise from lower-left point."""
    start_idx = min(range(4), key=lambda i: (coords[i, 0], coords[i, 1]))
    angles = []
    for i in range(4):
        if i == start_idx:
            angles.append(-np.pi)
        else:
            v = coords[i] - coords[start_idx]
            angles.append(np.arctan2(v[1], v[0]))
    return [node_ids[i] for i in sorted(range(4), key=lambda i: angles[i])]


def fix_hex(node_ids, coords):
    """Fix 8-node hexahedron node order."""
    z_vals = coords[:, 2]
    if len(np.unique(z_vals)) < 2:
        return node_ids

    z_sorted = sorted(z_vals)
    z_threshold = (z_sorted[3] + z_sorted[4]) / 2

    bottom_idx = [i for i in range(8) if z_vals[i] <= z_threshold]
    top_idx = [i for i in range(8) if z_vals[i] > z_threshold]
    if len(bottom_idx) != 4 or len(top_idx) != 4:
        return node_ids

    bottom_nodes = [node_ids[i] for i in bottom_idx]
    bottom_coords = np.array([coords[i] for i in bottom_idx])
    top_nodes = [node_ids[i] for i in top_idx]
    top_coords = np.array([coords[i] for i in top_idx])

    bottom_order = order_quad_counterclockwise(bottom_nodes, bottom_coords)

    top_order = []
    for bn in bottom_order:
        bn_idx = bottom_nodes.index(bn)
        bn_coord = bottom_coords[bn_idx]
        best_match = None
        best_dist = float("inf")
        for tn, tc in zip(top_nodes, top_coords):
            dist_xy = np.sqrt((tc[0] - bn_coord[0]) ** 2 + (tc[1] - bn_coord[1]) ** 2)
            if dist_xy < best_dist:
                best_dist = dist_xy
                best_match = tn
        top_order.append(best_match)

    return bottom_order + top_order


def _verify_ascii(filepath, num_samples=100):
    tree = ET.parse(filepath)
    root = tree.getroot()
    piece = root.find("UnstructuredGrid").find("Piece")

    points_data = piece.find("Points").find("DataArray").text.strip().split()
    points_coords = np.array([float(x) for x in points_data]).reshape(-1, 3)

    cells_elem = piece.find("Cells")
    connectivity_values = [int(x) for x in cells_elem.find(".//DataArray[@Name='connectivity']").text.strip().split()]
    offsets_values = [int(x) for x in cells_elem.find(".//DataArray[@Name='offsets']").text.strip().split()]

    d_n = np.array([
        [-0.125, -0.125, -0.125],
        [0.125, -0.125, -0.125],
        [0.125, 0.125, -0.125],
        [-0.125, 0.125, -0.125],
        [-0.125, -0.125, 0.125],
        [0.125, -0.125, 0.125],
        [0.125, 0.125, 0.125],
        [-0.125, 0.125, 0.125],
    ])

    positive = negative = zero = 0
    cell_start = 0
    samples = min(num_samples, len(offsets_values))
    for i in range(samples):
        cell_end = offsets_values[i]
        cell_nodes = connectivity_values[cell_start:cell_end]
        if len(cell_nodes) == 8:
            coords = points_coords[cell_nodes]
            det = np.linalg.det(d_n.T @ coords)
            if det > 1e-12:
                positive += 1
            elif abs(det) < 1e-12:
                zero += 1
            else:
                negative += 1
        cell_start = cell_end

    return {"samples": samples, "positive": positive, "zero": zero, "negative": negative}


def fix_vtu_correct(input_file, output_file, binary=True, keep_tmp=False):
    """Fix hexahedron/tetrahedron node order using an ASCII VTU as input."""
    input_file = Path(input_file)
    output_file = Path(output_file)

    tree = ET.parse(input_file)
    root = tree.getroot()
    piece = root.find("UnstructuredGrid").find("Piece")

    points_data = piece.find("Points").find("DataArray").text.strip().split()
    points_coords = np.array([float(x) for x in points_data]).reshape(-1, 3)

    cells_elem = piece.find("Cells")
    connectivity = cells_elem.find(".//DataArray[@Name='connectivity']")
    offsets = cells_elem.find(".//DataArray[@Name='offsets']")
    types = cells_elem.find(".//DataArray[@Name='types']")

    connectivity_values = [int(x) for x in connectivity.text.strip().split()]
    offsets_values = [int(x) for x in offsets.text.strip().split()]
    types_values = [int(x) for x in types.text.strip().split()]

    new_connectivity = []
    cell_start = 0
    fixed_count = 0

    for i, cell_end in enumerate(offsets_values):
        cell_nodes = connectivity_values[cell_start:cell_end]
        ctype = types_values[i]

        if ctype == 12 and len(cell_nodes) == 8:
            fixed = fix_hex(cell_nodes, points_coords[cell_nodes])
        elif ctype == 10 and len(cell_nodes) == 4:
            fixed = fix_tet4(cell_nodes, points_coords[cell_nodes])
        else:
            fixed = cell_nodes

        if fixed != cell_nodes:
            fixed_count += 1
        new_connectivity.extend(fixed)
        cell_start = cell_end

    tmp_ascii = output_file if not binary else output_file.with_name(output_file.stem + "_tmp_ascii.vtu")
    connectivity.text = "\n          " + " ".join(
        " ".join(str(new_connectivity[j]) for j in range(k, min(k + 8, len(new_connectivity))))
        for k in range(0, len(new_connectivity), 8)
    ) + "\n        "
    tree.write(tmp_ascii, encoding="utf-8", xml_declaration=True)

    verify_stats = _verify_ascii(tmp_ascii, 100)

    if binary:
        reader = vtk.vtkXMLUnstructuredGridReader()
        reader.SetFileName(str(tmp_ascii))
        reader.Update()
        ugrid = reader.GetOutput()

        writer = vtk.vtkXMLUnstructuredGridWriter()
        writer.SetFileName(str(output_file))
        writer.SetInputData(ugrid)
        writer.SetDataModeToAppended()
        writer.EncodeAppendedDataOn()
        ok = writer.Write()
        if ok != 1:
            raise RuntimeError("Failed to write binary VTU")
        if not keep_tmp:
            try:
                os.remove(tmp_ascii)
            except OSError:
                pass

    return {"output": str(output_file), "fixed_count": fixed_count, "verify": verify_stats}


def fix_vtu_node_order(input_vtu, output_vtu, binary=True):
    """Fix VTU element node order and write corrected VTU."""
    input_vtu = Path(input_vtu)
    output_vtu = Path(output_vtu)
    ascii_vtu = vtu_to_64bit_ascii(input_vtu)
    return fix_vtu_correct(ascii_vtu, output_vtu, binary=binary)
