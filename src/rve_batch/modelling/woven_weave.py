"""2D woven RVE modelling with TexGen API."""

from __future__ import annotations

import math
from pathlib import Path

from .texgen_utils import export_voxel, setup_texgen_api


class NormalWeave2D:
    """Generate 2D woven RVE, including standard, sheared, and layered forms."""

    def __init__(
        self,
        warp_count: int = 2,
        weft_count: int = 2,
        spacing: float = 1,
        thick: float = 0.2,
        width: float = 0.8,
        gapsize: float = 0,
        angle: float = 0,
        layer_count: int = 0,
        swap: list | None = None,
        DefaultDomain: bool = True,
        DefalutDominHeight: bool = True,
    ):
        self.warp_count = warp_count
        self.weft_count = weft_count
        self.spacing = spacing
        self.thick = thick
        self.width = width
        self.gapsize = gapsize
        self.angle = angle
        self.layer_count = layer_count
        self.swap = swap or [(0, 1), (1, 0)]
        self.DefaultDomain = DefaultDomain
        self.DefalutDominHeight = DefalutDominHeight

    def generate(self):
        from TexGen.Core import AddTextile, CShearedTextileWeave2D, CTextileLayered, CTextileWeave2D, PLANE, XYZ

        if self.angle == 0:
            weave = CTextileWeave2D(self.warp_count, self.weft_count, self.spacing, self.thick, bool(1), bool(1))
        else:
            angle_rad = math.radians(self.angle)
            weave = CShearedTextileWeave2D(
                self.warp_count,
                self.weft_count,
                self.spacing,
                self.thick,
                angle_rad,
                bool(1),
                bool(1),
            )

        weave.SetGapSize(self.gapsize)
        weave.SetYarnWidths(self.width)
        for i in self.swap:
            weave.SwapPosition(i[0], i[1])

        for i in range(self.warp_count):
            weave.SetXYarnWidths(i, self.width)
            weave.SetXYarnHeights(i, self.thick / 2)
            weave.SetXYarnSpacings(i, self.spacing)

        for i in range(self.weft_count):
            weave.SetYYarnWidths(i, self.width)
            weave.SetYYarnHeights(i, self.thick / 2)
            weave.SetYYarnSpacings(i, self.spacing)

        if self.layer_count != 0:
            layered = CTextileLayered()
            offset = XYZ()
            for _ in range(self.layer_count):
                layered.AddLayer(weave, offset)
                offset.z += self.thick

            weave.AssignDefaultDomain()
            domain = weave.GetDefaultDomain()
            plane = PLANE()
            plane_index = domain.GetPlane(XYZ(0, 0, -1), plane)
            plane.d -= (self.layer_count - 1) * self.thick
            domain.SetPlane(plane_index, plane)
            layered.AssignDomain(domain)
            return AddTextile(layered)

        if self.DefaultDomain:
            weave.AssignDefaultDomain(self.DefalutDominHeight)
        return AddTextile(weave)


def default_woven_weave_params():
    """Return default parameters for 2D woven RVE modelling."""
    return {
        "rve_type": "woven_weave_2d",
        "mesh": {"export_type": "voxel", "x_voxel": 80, "y_voxel": 80, "z_voxel": 80},
        "geometry": {
            "warp_count": 3,
            "weft_count": 2,
            "spacing": 1.0,
            "thick": 0.5,
            "width": 0.8,
            "gapsize": 0.0,
            "angle": 0.0,
            "layer_count": 0,
            "swap": [[0, 1], [1, 0]],
            "default_domain": True,
            "default_domain_height": True,
        },
    }


def default_sheared_woven_weave_params():
    """Return default parameters for sheared 2D woven RVE modelling."""
    params = default_woven_weave_params()
    params["rve_type"] = "sheared_woven_weave_2d"
    params["geometry"].update(
        {
            "warp_count": 4,
            "weft_count": 4,
            "angle": 30.0,
            "swap": [[0, 0], [0, 2], [1, 1], [1, 3], [2, 2], [2, 0], [3, 3], [3, 1]],
        }
    )
    return params


def default_layered_woven_weave_params():
    """Return default parameters for layered 2D woven RVE modelling."""
    params = default_woven_weave_params()
    params["rve_type"] = "layered_woven_weave_2d"
    params["mesh"].update({"x_voxel": 100, "y_voxel": 100, "z_voxel": 100})
    params["geometry"].update(
        {
            "warp_count": 3,
            "weft_count": 4,
            "layer_count": 3,
            "swap": [[0, 1], [1, 0], [1, 3], [2, 1], [3, 0], [3, 2]],
        }
    )
    return params


def _model_kwargs_from_params(params):
    geometry = params.get("geometry", params)
    return {
        "warp_count": geometry.get("warp_count", 2),
        "weft_count": geometry.get("weft_count", 2),
        "spacing": geometry.get("spacing", 1),
        "thick": geometry.get("thick", 0.2),
        "width": geometry.get("width", 0.8),
        "gapsize": geometry.get("gapsize", geometry.get("gap_size", 0)),
        "angle": geometry.get("angle", 0),
        "layer_count": geometry.get("layer_count", 0),
        "swap": geometry.get("swap"),
        "DefaultDomain": geometry.get("default_domain", geometry.get("DefaultDomain", True)),
        "DefalutDominHeight": geometry.get("default_domain_height", geometry.get("DefalutDominHeight", True)),
    }


def build_woven_weave(params, output_dir, texgen_lib_path):
    """Build and export a 2D woven RVE."""
    setup_texgen_api(texgen_lib_path)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    mesh = params.get("mesh", {})
    model = NormalWeave2D(**_model_kwargs_from_params(params))
    textile_name = model.generate()
    raw_vtu = output_dir / mesh.get("filename", "Voxel_weave.vtu")
    export_voxel(
        textile_name,
        raw_vtu,
        x_voxel=mesh.get("x_voxel", 80),
        y_voxel=mesh.get("y_voxel", 80),
        z_voxel=mesh.get("z_voxel", 80),
    )
    return raw_vtu
