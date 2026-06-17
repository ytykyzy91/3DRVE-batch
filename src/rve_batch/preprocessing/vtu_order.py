"""VTU cell node-order correction."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pyvista as pv
import vtk


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


def fix_vtu_node_order(input_vtu, output_vtu, binary=True):
    """Fix VTU element node order and write corrected VTU.

    Optimized version: all processing done in memory, no intermediate ASCII files.
    Reduces IO from 3 writes + 2 reads to 1 read + 1 write.
    """
    input_vtu = Path(input_vtu)
    output_vtu = Path(output_vtu)

    # 1. Read binary VTU directly into memory using pyvista/VTK
    mesh = pv.read(input_vtu)
    if mesh.points.dtype != np.float64:
        mesh.points = mesh.points.astype(np.float64)

    ugrid = mesh.cast_to_unstructured_grid()
    points = ugrid.GetPoints()
    n_cells = ugrid.GetNumberOfCells()

    # 2. Get cell arrays directly from VTK objects
    cell_types = ugrid.GetCellTypesArray()

    # 3. Prepare new connectivity for in-place modification
    new_cell_array = vtk.vtkCellArray()

    # Pre-allocate arrays
    n_points_per_cell = np.zeros(n_cells, dtype=np.int64)
    for i in range(n_cells):
        cell = ugrid.GetCell(i)
        n_points_per_cell[i] = cell.GetNumberOfPoints()

    total_conn_size = np.sum(n_points_per_cell)
    new_connectivity = vtk.vtkIdTypeArray()
    new_connectivity.SetNumberOfValues(int(total_conn_size))
    new_offsets = vtk.vtkIdTypeArray()
    new_offsets.SetNumberOfValues(n_cells + 1)
    new_offsets.SetValue(0, 0)

    fixed_count = 0
    pos = 0

    # 4. Process each cell entirely in memory
    for cell_id in range(n_cells):
        cell = ugrid.GetCell(cell_id)
        n_points = cell.GetNumberOfPoints()
        point_ids = cell.GetPointIds()
        ctype = cell_types.GetValue(cell_id)

        node_ids = [point_ids.GetId(i) for i in range(n_points)]

        # Get coordinates directly from VTK points
        coords = np.zeros((n_points, 3), dtype=np.float64)
        for i in range(n_points):
            p = points.GetPoint(node_ids[i])
            coords[i] = [p[0], p[1], p[2]]

        # Fix node ordering in memory
        if ctype == 12 and n_points == 8:  # VTK_HEXAHEDRON
            fixed = fix_hex(node_ids, coords)
        elif ctype == 10 and n_points == 4:  # VTK_TETRA
            fixed = fix_tet4(node_ids, coords)
        else:
            fixed = node_ids

        if fixed != node_ids:
            fixed_count += 1

        # Write to new connectivity array
        for i, nid in enumerate(fixed):
            new_connectivity.SetValue(pos + i, nid)
        pos += n_points
        new_offsets.SetValue(cell_id + 1, pos)

    # 5. Update cell connectivity and write directly to output (binary)
    new_cell_array.SetData(new_offsets, new_connectivity)
    ugrid.SetCells(cell_types, new_cell_array)

    writer = vtk.vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(output_vtu))
    writer.SetInputData(ugrid)
    if binary:
        writer.SetDataModeToAppended()
        writer.EncodeAppendedDataOn()
    else:
        writer.SetDataModeToAscii()
    ok = writer.Write()
    if ok != 1:
        raise RuntimeError(f"Failed to write VTU: {output_vtu}")

    # 6. Quick verification (sample 100 cells for positive volume)
    verify_positive = 0
    sample_size = min(100, n_cells)
    for i in range(sample_size):
        cell = ugrid.GetCell(i)
        if cell.GetCellType() == 12 and cell.GetNumberOfPoints() == 8:
            pts = cell.GetPoints()
            # Simple check: compute signed volume for first tet of hex
            p0 = pts.GetPoint(0)
            p1 = pts.GetPoint(1)
            p2 = pts.GetPoint(2)
            p3 = pts.GetPoint(4)
            p0_arr = np.array([p0[0], p0[1], p0[2]])
            p1_arr = np.array([p1[0], p1[1], p1[2]])
            p2_arr = np.array([p2[0], p2[1], p2[2]])
            p3_arr = np.array([p3[0], p3[1], p3[2]])
            if signed_tet_det(p0_arr, p1_arr, p2_arr, p3_arr) >= 0:
                verify_positive += 1

    return {
        "output": str(output_vtu),
        "fixed_count": fixed_count,
        "verify": {
            "samples": sample_size,
            "positive": verify_positive,
            "zero": 0,
            "negative": sample_size - verify_positive,
        },
    }
