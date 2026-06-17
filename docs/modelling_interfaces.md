# 建模脚本接口与类关系

## 目录位置

所有 TexGen 建模相关代码位于：

```text
3DRVE_batch/src/rve_batch/modelling/
```

当前包含：

```text
modelling/
├── __init__.py
├── models.py              # 顶层建模接口：参数初始化、模型创建、统一调用
├── texgen_utils.py         # TexGen API 路径设置、VTU/STEP 导出工具
├── woven_weave.py          # 从 API_modelling/Woven_RVE/Woven_RVE.py 迁入
├── orthogonal_weave.py     # 3D 正交编织
└── angle_interlock.py      # 3D 角联锁编织
```

## 类关系

```text
models.py
├── NormalWeave2D              -> woven_weave.py
│   ├── woven_weave_2d          标准二维编织，angle = 0, layer_count = 0
│   ├── sheared_woven_weave_2d  剪切二维编织，angle != 0
│   └── layered_woven_weave_2d  多层二维编织，layer_count > 0
│
├── OrthoWeave3D               -> orthogonal_weave.py
│   └── orthogonal_weave_3d     三维正交编织
│
└── AngleInterlockWeave3D      -> angle_interlock.py
    └── angle_interlock_weave_3d 三维角联锁编织
```

说明：

- `NormalWeave2D` 一个类覆盖标准 2D、剪切 2D、多层 2D 三种形式；由参数 `angle` 和 `layer_count` 决定实际 TexGen 对象。
- `OrthoWeave3D` 对应 `CTextileOrthogonal`。
- `AngleInterlockWeave3D` 对应 `CTextileOffsetAngleInterlock`。
- `models.py` 是推荐的顶层入口，后续批量建模、采样、流水线都应优先调用它，而不是直接调用底层类。

## 支持的 rve_type

```python
from rve_batch.modelling import MODEL_TYPES

print(MODEL_TYPES)
```

当前支持：

```text
woven_weave_2d
sheared_woven_weave_2d
layered_woven_weave_2d
orthogonal_weave_3d
angle_interlock_weave_3d
```

## 参数初始化接口

```python
from rve_batch.modelling import default_model_params, init_model_params

params = default_model_params("orthogonal_weave_3d")

params = init_model_params(
    "orthogonal_weave_3d",
    {
        "geometry": {
            "warp_count": 6,
            "weft_count": 7,
        },
        "mesh": {
            "x_voxel": 80,
            "y_voxel": 80,
            "z_voxel": 80,
        },
    },
)
```

- `default_model_params(rve_type)`：返回完整默认参数。
- `init_model_params(rve_type, overrides)`：在默认参数基础上递归覆盖用户参数。

## 模型对象创建接口

```python
from rve_batch.modelling import create_model

model = create_model("woven_weave_2d")
textile_name = model.generate()
```

`create_model` 只创建底层模型对象，不导出 VTU，适合调试 TexGen 或做自定义导出。

## 建模并导出 VTU 的统一接口

```python
from pathlib import Path
from rve_batch.modelling import build_model, init_model_params

texgen_lib_path = Path("../Texgen_source/texgen3.9/TexGen/Python/libxtra")
output_dir = Path("data/intermediate")

params = init_model_params(
    "orthogonal_weave_3d",
    {
        "mesh": {
            "filename": "Voxel_ortho.vtu",
            "x_voxel": 50,
            "y_voxel": 50,
            "z_voxel": 50,
        }
    },
)

raw_vtu = build_model("orthogonal_weave_3d", output_dir, texgen_lib_path, params)
```

`build_model` 会完成：

```text
初始化参数 -> 初始化底层类 -> TexGen generate -> export voxel VTU
```

## 命令行调用示例

从 `3DRVE_batch` 目录运行：

```bash
conda activate py39
python scripts/run_current_pipeline.py --rve-type orthogonal_weave_3d
```

可替换为：

```bash
python scripts/run_current_pipeline.py --rve-type woven_weave_2d
python scripts/run_current_pipeline.py --rve-type sheared_woven_weave_2d
python scripts/run_current_pipeline.py --rve-type layered_woven_weave_2d
python scripts/run_current_pipeline.py --rve-type angle_interlock_weave_3d
```
