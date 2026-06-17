"""Shared TexGen API setup and export helpers."""

from __future__ import annotations

import sys
from pathlib import Path


def setup_texgen_api(texgen_lib_path):
    """Add TexGen Python API path to sys.path."""
    texgen_lib_path = str(Path(texgen_lib_path).resolve())
    if texgen_lib_path not in sys.path:
        sys.path.append(texgen_lib_path)


def export_voxel(textile_name: str, vtu_path, x_voxel: int = 80, y_voxel: int = 80, z_voxel: int = 80):
    """Export textile to a voxel VTU mesh."""
    from TexGen.Core import CRectangularVoxelMesh, GetTextile, VTU_EXPORT

    vtu_path = str(Path(vtu_path).resolve())
    vox = CRectangularVoxelMesh("CPeriodicBoundaries")
    vox.SaveVoxelMesh(GetTextile(textile_name.strip()), vtu_path, x_voxel, y_voxel, z_voxel, True, True, 0, 0, VTU_EXPORT)
    return Path(vtu_path)


def export_volume_mesh(textile_name: str, vtu_path, seed: float = 0.05, merge_tol: float = 0.001):
    """Export textile to a volume VTU mesh."""
    from TexGen.Core import CMesher

    vtu_path = str(Path(vtu_path).resolve())
    mesher = CMesher()
    mesher.SetSeed(seed)
    mesher.SetMergeTolerance(merge_tol)
    mesher.CreateMesh(textile_name)
    mesher.SaveVolumeMeshToVTK(vtu_path)
    return Path(vtu_path)


def export_step(textile_name: str, step_path):
    """Export textile geometry to STEP."""
    from TexGen.Export import CExporter

    step_path = str(Path(step_path).resolve())
    exporter = CExporter()
    exporter.SetFaceted(bool(1))
    exporter.SetExportDomain(bool(1))
    exporter.SetSubtractYarns(bool(0))
    exporter.SetJoinYarns(bool(1))
    exporter.OutputTextileToSTEP(step_path, textile_name.strip())
    return Path(step_path)
