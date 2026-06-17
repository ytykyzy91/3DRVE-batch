"""Angle-interlock 3D weave modelling with TexGen API."""

from __future__ import annotations

from pathlib import Path

from .texgen_utils import export_voxel, setup_texgen_api


class AngleInterlockWeave3D:
    """Generate angle-interlock 3D weave RVE."""

    def __init__(
        self,
        warp_count: int = 5,
        weft_count: int = 8,
        warp_spacing: float = 1,
        weft_spacing: float = 1,
        warp_height: float = 0.1,
        weft_height: float = 0.1,
        WarpRatio: int = 1,
        BinderRatio: int = 1,
        WarpYarnWidths: float = 0.8,
        WeftYarnWidths: float = 0.8,
        BinderYarnWidths: float = 0.4,
        BinderYarnHeight: float = 0.05,
        BinderYarnSpacing: float = 0.5,
        GapSize: float = 0,
        Swap: list | None = None,
        WarpYarnPower: float = 0.6,
        WeftYarnPower: float = 0.6,
        BinderYarnPower: float = 0.6,
        DefaultDomain: bool = True,
        DefalutDominHeight: bool = True,
    ):
        self.warp_count = warp_count
        self.weft_count = weft_count
        self.warp_spacing = warp_spacing
        self.weft_spacing = weft_spacing
        self.warp_height = warp_height
        self.weft_height = weft_height
        self.WarpYarnWidths = WarpYarnWidths
        self.WeftYarnWidths = WeftYarnWidths
        self.BinderYarnWidths = BinderYarnWidths
        self.BinderYarnHeight = BinderYarnHeight
        self.BinderYarnSpacing = BinderYarnSpacing
        self.WarpRatio = WarpRatio
        self.BinderRatio = BinderRatio
        self.WarpLayer = weft_count - 2
        self.WeftLayer = weft_count - 1
        self.GapSize = GapSize
        self.Swap = Swap or [(2, 1), (6, 3)]
        self.WarpYarnPower = WarpYarnPower
        self.WeftYarnPower = WeftYarnPower
        self.BinderYarnPower = BinderYarnPower
        self.DefaultDomain = DefaultDomain
        self.DefalutDominHeight = DefalutDominHeight

    def generate(self):
        from TexGen.Core import AddTextile, CTextileOffsetAngleInterlock

        weave = CTextileOffsetAngleInterlock(
            self.warp_count,
            self.weft_count,
            self.warp_spacing,
            self.warp_spacing,
            self.warp_height,
            self.weft_height,
        )

        weave.SetWarpRatio(self.WarpRatio)
        weave.SetBinderRatio(self.BinderRatio)
        weave.SetWarpYarnWidths(self.WarpYarnWidths)
        weave.SetYYarnWidths(self.WeftYarnWidths)
        weave.SetBinderYarnWidths(self.BinderYarnWidths)
        weave.SetupLayers(self.WarpLayer, self.WeftLayer)
        weave.SetGapSize(self.GapSize)

        weave.SetWarpYarnPower(self.WarpYarnPower)
        weave.SetWeftYarnPower(self.WeftYarnPower)
        weave.SetBinderYarnPower(self.BinderYarnPower)

        for i in self.Swap:
            weave.SetBinderYarnPositions(i[0], i[1])

        for i in range(self.weft_count * 2):
            weave.SetYYarnWidths(i, self.WeftYarnWidths)
            weave.SetYYarnHeights(i, self.weft_height)
            weave.SetYYarnSpacings(i, self.weft_spacing)

        total_ratio = self.WarpRatio + self.BinderRatio
        for i in range(self.warp_count):
            if i % total_ratio < self.WarpRatio:
                weave.SetXYarnWidths(i, self.WarpYarnWidths)
                weave.SetXYarnHeights(i, self.warp_height)
                weave.SetXYarnSpacings(i, self.warp_spacing)
            else:
                weave.SetXYarnWidths(i, self.BinderYarnWidths)
                weave.SetXYarnHeights(i, self.BinderYarnHeight)
                weave.SetXYarnSpacings(i, self.BinderYarnSpacing)

        if self.DefaultDomain:
            weave.AssignDefaultDomain(self.DefalutDominHeight)
        return AddTextile(weave)


def default_angle_interlock_params():
    """Return default parameters for angle-interlock 3D weave modelling."""
    return {
        "rve_type": "angle_interlock_weave_3d",
        "mesh": {"export_type": "voxel", "x_voxel": 80, "y_voxel": 80, "z_voxel": 80},
        "geometry": {
            "warp_count": 5,
            "weft_count": 8,
            "warp_spacing": 1.0,
            "weft_spacing": 1.0,
            "warp_height": 0.1,
            "weft_height": 0.1,
            "warp_ratio": 1,
            "binder_ratio": 1,
            "warp_yarn_width": 0.8,
            "weft_yarn_width": 0.8,
            "binder_yarn_width": 0.4,
            "binder_yarn_height": 0.05,
            "binder_yarn_spacing": 0.5,
            "gap_size": 0.0,
            "swap": [[2, 1], [6, 3]],
            "warp_yarn_power": 0.6,
            "weft_yarn_power": 0.6,
            "binder_yarn_power": 0.6,
            "default_domain": True,
            "default_domain_height": True,
        },
    }


def _model_kwargs_from_params(params):
    geometry = params.get("geometry", params)
    return {
        "warp_count": geometry.get("warp_count", 5),
        "weft_count": geometry.get("weft_count", 8),
        "warp_spacing": geometry.get("warp_spacing", 1),
        "weft_spacing": geometry.get("weft_spacing", 1),
        "warp_height": geometry.get("warp_height", 0.1),
        "weft_height": geometry.get("weft_height", 0.1),
        "WarpRatio": geometry.get("warp_ratio", geometry.get("WarpRatio", 1)),
        "BinderRatio": geometry.get("binder_ratio", geometry.get("BinderRatio", 1)),
        "WarpYarnWidths": geometry.get("warp_yarn_width", geometry.get("WarpYarnWidths", 0.8)),
        "WeftYarnWidths": geometry.get("weft_yarn_width", geometry.get("WeftYarnWidths", 0.8)),
        "BinderYarnWidths": geometry.get("binder_yarn_width", geometry.get("BinderYarnWidths", 0.4)),
        "BinderYarnHeight": geometry.get("binder_yarn_height", geometry.get("BinderYarnHeight", 0.05)),
        "BinderYarnSpacing": geometry.get("binder_yarn_spacing", geometry.get("BinderYarnSpacing", 0.5)),
        "GapSize": geometry.get("gap_size", geometry.get("GapSize", 0)),
        "Swap": geometry.get("swap", geometry.get("Swap")),
        "WarpYarnPower": geometry.get("warp_yarn_power", geometry.get("WarpYarnPower", 0.6)),
        "WeftYarnPower": geometry.get("weft_yarn_power", geometry.get("WeftYarnPower", 0.6)),
        "BinderYarnPower": geometry.get("binder_yarn_power", geometry.get("BinderYarnPower", 0.6)),
        "DefaultDomain": geometry.get("default_domain", geometry.get("DefaultDomain", True)),
        "DefalutDominHeight": geometry.get("default_domain_height", geometry.get("DefalutDominHeight", True)),
    }


def build_angle_interlock_weave(params, output_dir, texgen_lib_path):
    """Build and export an angle-interlock 3D weave RVE."""
    setup_texgen_api(texgen_lib_path)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    mesh = params.get("mesh", {})
    model = AngleInterlockWeave3D(**_model_kwargs_from_params(params))
    textile_name = model.generate()
    raw_vtu = output_dir / mesh.get("filename", "Voxel_ang.vtu")
    export_voxel(
        textile_name,
        raw_vtu,
        x_voxel=mesh.get("x_voxel", 80),
        y_voxel=mesh.get("y_voxel", 80),
        z_voxel=mesh.get("z_voxel", 80),
    )
    return raw_vtu
