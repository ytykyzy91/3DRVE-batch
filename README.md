# 3DRVE_batch

复材 RVE 批量建模与计算项目。

当前已完成的核心流程：

```text
TexGen 参数化建模
  -> VTU 节点顺序修正
  -> 增加 Material CellData
  -> 检查 YarnIndex / Material 字段
```

求解器计算步骤已预留，但当前脚本默认不执行最后求解。

## 边界约定

- `../Texgen_source`：TexGen 主程序与库，作为外部依赖使用，不在本项目内修改。
- `src/rve_batch/modelling`：本项目自己的建模脚本目录。
- `src/rve_batch/preprocessing`：VTU 修正、Material CellData 生成、字段检查。
- `configs/solver/user_RVE_analysis.json`：本项目内的求解模板副本。运行建模预处理后，会把 `Defs.Composite.Settings.rvePath` 更新为最终 VTU 文件名。

## 目录结构

```text
3DRVE_batch/
├── configs/
│   ├── model_params.example.json      # 各建模类型的 JSON 参数覆盖示例
│   ├── batch_doe.example.json         # LHS DOE 批量建模配置示例
│   ├── project.yaml
│   ├── parameters.example.yaml
│   └── solver/
│       └── user_RVE_analysis.json     # 本地分析模板副本
├── data/
│   ├── inputs/
│   ├── intermediate/                  # 建模和预处理输出
│   ├── results/
│   ├── logs/
│   ├── datasets/
│   └── models/
├── docs/
│   ├── architecture.md
│   ├── pipeline.md
│   └── modelling_interfaces.md
├── scripts/
│   ├── run_current_pipeline.py         # 单个样本建模预处理入口
│   ├── run_batch_doe.py                # LHS DOE 批量建模入口
│   ├── run_single.py
│   ├── run_batch.py
│   └── build_dataset.py
└── src/rve_batch/
    ├── modelling/
    │   ├── models.py                   # 顶层建模接口
    │   ├── texgen_utils.py
    │   ├── woven_weave.py
    │   ├── orthogonal_weave.py
    │   └── angle_interlock.py
    ├── preprocessing/
    │   ├── vtu_order.py
    │   ├── material_cell_data.py
    │   └── quality.py
    ├── solver/
    ├── sampling/
    ├── batch/
    ├── ml/
    └── utils/
```

## 支持的建模类型

当前支持 5 类：

```text
woven_weave_2d              -> NormalWeave2D
sheared_woven_weave_2d      -> NormalWeave2D
layered_woven_weave_2d      -> NormalWeave2D
orthogonal_weave_3d         -> OrthoWeave3D
angle_interlock_weave_3d    -> AngleInterlockWeave3D
```

类关系和接口说明详见：

```text
docs/modelling_interfaces.md
```

## 运行环境

运行前进入 `3DRVE_batch` 并激活 `py39`：

```bash
cd D:/ClaudeCode/3DRVE_projects/3DRVE_batch
conda activate py39
```

如果在 Git Bash 中不想使用 `conda activate`，也可以直接使用环境解释器：

```bash
/c/Users/Tianyu.Yu/AppData/Local/miniconda3/envs/py39/python.exe scripts/run_current_pipeline.py
```

## Windows 双击运行

项目根目录提供两个可双击执行的 BAT 文件：

```text
run_json_single_case.bat   # 单个样本，通过 configs/model_params.example.json 覆盖初始化参数
run_lhs_doe_batch.bat      # LHS DOE 批量建模，通过 configs/batch_doe.example.json 执行
run_batch_solver.bat       # 对已生成 batch 中的样本逐个执行求解器计算
```

使用方式：

1. 进入 `3DRVE_batch` 文件夹。
2. 双击对应 `.bat` 文件。
3. 脚本会自动切到项目目录并激活 `conda` 环境 `py39`。

如需修改单样本建模类型，可编辑：

```text
run_json_single_case.bat
```

其中：

```bat
set RVE_TYPE=orthogonal_weave_3d
set PARAMS_JSON=configs\model_params.example.json
set OUTPUT_DIR=data\intermediate\json_single_case
```

如需修改 DOE 批量参数，编辑：

```text
configs/batch_doe.example.json
```

## 基本执行方式

默认运行 `orthogonal_weave_3d`：

```bash
python scripts/run_current_pipeline.py
```

指定建模类型：

```bash
python scripts/run_current_pipeline.py --rve-type orthogonal_weave_3d
python scripts/run_current_pipeline.py --rve-type woven_weave_2d
python scripts/run_current_pipeline.py --rve-type sheared_woven_weave_2d
python scripts/run_current_pipeline.py --rve-type layered_woven_weave_2d
python scripts/run_current_pipeline.py --rve-type angle_interlock_weave_3d
```

指定输出目录，避免文件覆盖：

```bash
python scripts/run_current_pipeline.py \
  --rve-type orthogonal_weave_3d \
  --output-dir data/intermediate/case_000001
```

执行成功后会生成：

```text
<output-dir>/<raw_name>.vtu
<output-dir>/<raw_name>_ascii.vtu
<output-dir>/<raw_name>_fixed.vtu
```

其中最终可用于后续计算的是：

```text
<output-dir>/<raw_name>_fixed.vtu
```

该文件已完成：

- VTU 节点顺序修正。
- 添加 `Material` CellData。
- 检查 `YarnIndex` 和 `Material` 字段存在。

## LHS DOE 批量建模

批量建模入口：

```text
scripts/run_batch_doe.py
```

示例配置：

```text
configs/batch_doe.example.json
```

五种建模类型的完整 DOE 模板位于：

```text
configs/doe_templates/woven_weave_2d_doe.json
configs/doe_templates/sheared_woven_weave_2d_doe.json
configs/doe_templates/layered_woven_weave_2d_doe.json
configs/doe_templates/orthogonal_weave_3d_doe.json
configs/doe_templates/angle_interlock_weave_3d_doe.json
```

这些模板都包含完整默认初始化参数 `base_overrides`、所有主要可调参数的 `lhs_space`、材料参数采样项和约束表达式。

运行示例：

```bash
python scripts/run_batch_doe.py --config configs/batch_doe.example.json
```

也可以不使用配置文件，直接通过命令行指定：

```bash
python scripts/run_batch_doe.py \
  --rve-type orthogonal_weave_3d \
  --sample-count 5 \
  --seed 42 \
  --start-index 1 \
  --end-index 5 \
  --prefix case \
  --batch-name batch0001 \
  --output-root output \
  --type-dir "" \
  --max-workers 1
```

命令行默认会跳过已完成样本；如需强制不跳过可加：

```bash
--no-skip-completed
```

如需重跑已有失败样本可加：

```bash
--rerun-failed
```

### 批量输出目录规则

批量输出目录由 `type_dir` 配置控制：

```json
"type_dir": ""              // 直接输出到 output/<batch_name>/<case_id>/
"type_dir": "woven_weave_2d" // 输出到 output/woven_weave_2d/<batch_name>/<case_id>/
```

默认（不设置 `type_dir` 时）行为等同于 `type_dir` = `<rve_type>`，即：

```text
output/<rve_type>/<batch_name>/<case_id>/
```

因此以下三种写法都可以：

1. 不写 `type_dir` — 默认使用 `<rve_type>` 作为中间目录
2. `"type_dir": ""` — 不使用中间目录，直接输出到 `<output_root>/<batch_name>/`
3. `"type_dir": "自定义目录名"` — 使用自定义中间目录

例如：

```text
output/orthogonal_weave_3d/batch0001/case0001/
├── input_params.json        # 该样本完整建模输入参数
├── sampled_overrides.json   # LHS 实际采样覆盖项
├── case0001_fix.vtu         # 最终保留的 VTU
├── user_RVE_analysis.json   # 该样本计算用分析 JSON，含 rvePath 和材料参数
└── status.json              # success/fail、错误信息、校验信息
```

批次级文件：

```text
output/orthogonal_weave_3d/batch0001/
├── batch_config.json
└── batch_summary.json
```

### 批量文件清理规则

批量建模中每个样本目录只保留：

- `*_fix.vtu`
- `user_RVE_analysis.json`
- `input_params.json`
- `sampled_overrides.json`
- `status.json`

原始 `*.vtu` 和中间 `*_ascii.vtu` 会自动删除。

### LHS 可控项

`configs/batch_doe.example.json` 中可控制：

```json
{
    "rve_type": "orthogonal_weave_3d",
    "output_root": "output",
    "type_dir": "",
    "batch_name": "batch0001",
    "sample_count": 3,
    "seed": 42,
    "start_index": 1,
    "end_index": 3,
    "prefix": "case",
    "max_sampling_iterations": 100,
    "max_workers": 1,
    "skip_completed": true,
    "rerun_failed": false,
    "analysis_template": "configs/solver/user_RVE_analysis.json"
}
```

含义：

- `sample_count`：采样数量。若配置了 `end_index`，实际样本数由 `start_index ~ end_index` 决定。
- `seed`：随机种子，保证 LHS 可复现。
- `start_index`：样本起始编号。
- `type_dir`：输出根目录下的中间目录名。设为空字符串 `""` 时直接输出到 `<output_root>/<batch_name>/`；不设置时默认使用 `<rve_type>`。
- `end_index`：样本终止编号，采样到该编号停止；配置读取时未填写则默认为 `start_index`。
- `prefix`：样本名前缀，例如 `case0001`。
- `batch_name`：批次目录名。
- `output_root`：输出根目录。
- `max_sampling_iterations`：约束不满足时继续重采样的最大迭代次数。
- `max_workers`：批量建模/预处理的线程数。建议先用 `1`；确认 TexGen 稳定后再增大。
- `skip_completed`：若已有样本 `status.json` 为 `success` 且关键输出存在、输入参数一致，则跳过。
- `rerun_failed`：若已有样本为 `fail`，是否重新运行。
- `analysis_template`：每个样本生成 `user_RVE_analysis.json` 所用模板。

### LHS 采样空间

在配置文件中通过 `lhs_space` 定义，例如：

```json
"lhs_space": {
    "geometry.warp_count": {"min": 4, "max": 5, "type": "int"},
    "geometry.weft_count": {"min": 4, "max": 5, "type": "int"},
    "geometry.warp_spacing": {"min": 0.9, "max": 1.1},
    "geometry.warp_yarn_width": {"min": 0.35, "max": 0.65}
}
```

支持字段路径形式：

```text
geometry.xxx
mesh.xxx
```

也支持列表索引路径，因此 `swap` 中的经纬纱交换位置也可以参与 LHS 采样：

```json
"lhs_space": {
    "geometry.swap[0][0]": {"min": 0, "max": 4, "type": "int"},
    "geometry.swap[0][1]": {"min": 0, "max": 3, "type": "int"},
    "geometry.swap[1][0]": {"min": 0, "max": 4, "type": "int"},
    "geometry.swap[1][1]": {"min": 0, "max": 3, "type": "int"}
}
```

其中 `swap[i] = [a, b]` 表示一处经纬纱交换位置，`a` 和 `b` 均为整数。

材料参数也可以加入 LHS 采样空间。当前支持写入每个样本自己的 `user_RVE_analysis.json`，位置对应模板中的：

```text
Defs.Analysis.Materials[0].Mechanical.LinearElastic.Isotropic.E
Defs.Analysis.Materials[0].Mechanical.LinearElastic.Isotropic.nu
Defs.Analysis.Materials[1].Mechanical.LinearElastic.Isotropic.E
Defs.Analysis.Materials[1].Mechanical.LinearElastic.Isotropic.nu
```

JSON 路径写法为：

```json
"lhs_space": {
    "materials.material_0.E": {"min": 60000000000.0, "max": 80000000000.0},
    "materials.material_0.nu": {"min": 0.18, "max": 0.25},
    "materials.material_1.E": {"min": 3000000000.0, "max": 6000000000.0},
    "materials.material_1.nu": {"min": 0.30, "max": 0.38}
}
```

支持类型：

```json
{"type": "int"}
```

如果未提供 `lhs_space`，程序会根据 `rve_type` 使用内置保守采样空间。

### 参数间相互约束

除内置约束外，`configs/batch_doe.example.json` 支持类似 `lhs_ref.py` 的表达式约束：

```json
"constraints": [
    "warp_yarn_width < 0.9 * warp_spacing",
    "weft_yarn_width < 0.9 * weft_spacing",
    "binder_yarn_width < 0.8 * binder_yarn_spacing",
    "warp_height < 0.6 * warp_spacing",
    "weft_height < 0.6 * weft_spacing",
    "binder_yarn_height < 0.5 * binder_yarn_spacing",
    "(warp_ratio + binder_ratio) < 4",
    "warp_count * weft_count < 32"
]
```

表达式环境会自动展开 `geometry` 和 `mesh` 中的参数，因此可直接使用：

```text
warp_count
weft_count
warp_spacing
warp_yarn_width
x_voxel
```

也可以使用带前缀的名称：

```text
geometry_warp_count
mesh_x_voxel
```

表达式中支持安全数学函数：

```text
sin, cos, tan, sqrt, log, exp, abs, min, max, pi
```

采样阶段如果表达式不满足，会丢弃该候选点并继续迭代采样，直到获得足够数量的有效样本；如果表达式写错或在最大迭代次数内仍无法凑够有效样本，则批次会报错退出。

`swap` 的表达式约束可以使用自动展开的变量名，例如：

```json
"constraints": [
    "swap_0_0 < weft_count",
    "swap_0_1 < warp_count",
    "swap_1_0 < weft_count",
    "swap_1_1 < warp_count",
    "material_0_E > 0",
    "material_1_E > 0",
    "0 < material_0_nu < 0.5",
    "0 < material_1_nu < 0.5"
]
```

### 每个样本输出轴测截图

批量配置支持 `screenshot` 控制项：

```json
"screenshot": {
    "enabled": true,
    "filename": "iso_yarn_visible.png",
    "hide_yarn_index": -1,
    "window_size": [1200, 900],
    "background": "white",
    "scalars": "YarnIndex",
    "parallel_projection": true,
    "show_edges": false,
    "show_scalar_bar": false
}
```

启用后，每个成功样本目录中会额外输出一张 PNG 轴测图。截图默认为正交投影轴测视图，并用 `YarnIndex` 显示云图，且默认不显示 color bar 图例。截图前会隐藏满足：

```text
YarnIndex == hide_yarn_index
```

的 cell。当前示例中 `hide_yarn_index = -1`，即隐藏 `YarnIndex=-1` 的 cell。

### 参数约束与重采样

DOE 采样阶段会先进行参数约束检查。若候选点不满足内置约束或 `constraints` 表达式，该候选点会被丢弃，并继续 LHS 重采样，直到获得 `sample_count` 个有效样本。

如果在 `max_sampling_iterations` 次迭代后仍无法获得足够有效样本，批次会报错退出，提示放宽 `lhs_space` 或 `constraints`。

注意：采样阶段的约束失败不会再作为样本返回；只有建模、VTU 修正、Material 生成、截图等后续执行阶段出错时，才会在该样本的 `status.json` 中标记：

```json
"status": "fail"
```

当前内置约束包括：

- `warp_count`、`weft_count`、`warp_ratio`、`binder_ratio`、`warp_layer`、`weft_layer`、`layer_count`、`x_voxel/y_voxel/z_voxel` 必须为整数。
- 尺寸类参数必须为正数。
- `warp_yarn_width < warp_spacing`。
- `weft_yarn_width < weft_spacing`。
- `binder_yarn_width < binder_yarn_spacing`。
- 2D 编织中 `width < spacing`。
- 2D 编织中 `thick < spacing`。
- `sheared_woven_weave_2d` 要求 `angle != 0`。
- `layered_woven_weave_2d` 要求 `layer_count > 0`。
- `orthogonal_weave_3d` 中建议 `warp_layer < weft_layer`。
- `swap[i]` 必须为两个整数。
- 按当前项目约定，`swap[i][0]` 满足 `0 <= value < weft_count`，`swap[i][1]` 满足 `0 <= value < warp_count`。

## 对已生成 batch 执行批量计算（不建议使用）
**此方法调用vg_solver进行求解，效率很低且边界条件设置存在问题**

DOE 建模完成后，每个成功样本目录中都会包含：

```text
user_RVE_analysis.json
```

这个文件已经写入该样本自己的：

- `rvePath`
- 材料参数 `Materials[0/1].Mechanical.LinearElastic.Isotropic.E`
- 材料参数 `Materials[0/1].Mechanical.LinearElastic.Isotropic.nu`

因此可以用独立脚本对一个 batch 逐个样本执行求解器：

```bash
python scripts/run_batch_solver.py --batch-dir output/orthogonal_weave_3d/batch0003
```

可选参数：

```bash
python scripts/run_batch_solver.py \
  --batch-dir output/orthogonal_weave_3d/batch0003 \
  --solver-exe D:/Demx_softwares/2025b/Virgo_R2025b_win64/bin/vg_solver.exe \
  --solver-config D:/Demx_softwares/2025C/Plexian_R2025c_fixed_win64/res/PlexianConfig.json \
  --timeout 3600
```

默认情况下，单个样本求解成功后会自动后处理结果 VTU：

```text
user_RVE_results/rve/data/user_RVE_step0000.vtu
```

后处理会把该样本 `*_fix.vtu` 中的单元节点/几何和 `Material` 字段合并到计算结果 VTU 中，同时保留计算结果 VTU 的 PointData 和非 Material 的 CellData。这个步骤对应项目内模块：

```text
src/rve_batch/postprocessing/vtu_results.py
```

如果需要关闭这个后处理，可加：

```bash
--no-postprocess-results
```

如果结果 VTU 路径不同，可用相对样本目录的路径指定：

```bash
--result-vtu-relative user_RVE_results/rve/data/user_RVE_step0000.vtu
```

也可以双击：

```text
run_batch_solver.bat
```

需要计算不同 batch 时，编辑其中的：

```bat
set BATCH_DIR=output\orthogonal_weave_3d\batch0003
```

每个样本计算后会生成：

```text
solver.log
solver_status.json
user_RVE_results/rve/data/user_RVE_step0000.vtu  # 已合并几何/Material 后的结果 VTU
```

批次目录会生成：

```text
solver_batch_summary.json
```

默认行为：

- 只计算建模状态为 `success` 且存在 `user_RVE_analysis.json` 的样本。
- 如果已有 `solver_status.json` 且状态为 `success`，默认跳过。
- 使用 `--overwrite` 可以强制重算。
- 使用 `--stop-on-error` 可以遇到第一个失败样本时停止。

## 通过 JSON 修改初始化参数

推荐方式：**不要频繁修改源码中的默认参数函数，而是在调用时通过 JSON 覆盖参数。**

示例 JSON：

```text
configs/model_params.example.json
```

该文件按 `rve_type` 分组：

```json
{
    "orthogonal_weave_3d": {
        "mesh": {
            "filename": "Voxel_ortho.vtu",
            "x_voxel": 50,
            "y_voxel": 50,
            "z_voxel": 50
        },
        "geometry": {
            "warp_count": 4,
            "weft_count": 5,
            "warp_spacing": 1.0,
            "weft_spacing": 1.0
        }
    }
}
```

运行时指定：

```bash
python scripts/run_current_pipeline.py \
  --rve-type orthogonal_weave_3d \
  --params-json configs/model_params.example.json \
  --output-dir data/intermediate/json_ortho
```

脚本会：

```text
读取默认参数
  -> 读取 JSON 中当前 rve_type 对应的参数
  -> 用 JSON 参数覆盖默认参数
  -> 初始化模型并导出 VTU
```

### JSON 文件格式 1：多类型参数文件

适合批量维护所有建模类型：

```json
{
    "woven_weave_2d": {
        "mesh": {
            "filename": "Voxel_weave.vtu",
            "x_voxel": 80,
            "y_voxel": 80,
            "z_voxel": 80
        },
        "geometry": {
            "warp_count": 3,
            "weft_count": 2,
            "spacing": 1.0,
            "thick": 0.5,
            "width": 0.8
        }
    },
    "orthogonal_weave_3d": {
        "mesh": {
            "filename": "Voxel_ortho.vtu",
            "x_voxel": 50,
            "y_voxel": 50,
            "z_voxel": 50
        },
        "geometry": {
            "warp_count": 4,
            "weft_count": 5,
            "warp_height": 0.5,
            "weft_height": 0.5
        }
    }
}
```

调用时通过 `--rve-type` 选择其中一组。

### JSON 文件格式 2：单类型直接覆盖文件

也可以只写当前建模类型的覆盖项：

```json
{
    "mesh": {
        "filename": "case_0001_raw.vtu",
        "x_voxel": 80,
        "y_voxel": 80,
        "z_voxel": 80
    },
    "geometry": {
        "warp_count": 6,
        "weft_count": 7
    }
}
```

调用：

```bash
python scripts/run_current_pipeline.py \
  --rve-type orthogonal_weave_3d \
  --params-json configs/my_case.json \
  --output-dir data/intermediate/case_0001
```

## JSON 中常用参数位置

### 通用网格参数

```json
"mesh": {
    "filename": "Voxel_ortho.vtu",
    "x_voxel": 50,
    "y_voxel": 50,
    "z_voxel": 50
}
```

### `woven_weave_2d` / `sheared_woven_weave_2d` / `layered_woven_weave_2d`

```json
"geometry": {
    "warp_count": 3,
    "weft_count": 2,
    "spacing": 1.0,
    "thick": 0.5,
    "width": 0.8,
    "gapsize": 0.0,
    "angle": 0.0,
    "layer_count": 0,
    "swap": [[0, 1], [1, 0]]
}
```

说明：

- `angle != 0` 时为剪切二维编织。
- `layer_count > 0` 时为多层二维编织。

### `orthogonal_weave_3d`

```json
"geometry": {
    "warp_count": 4,
    "weft_count": 5,
    "warp_spacing": 1.0,
    "weft_spacing": 1.0,
    "warp_height": 0.5,
    "weft_height": 0.5,
    "warp_ratio": 1,
    "binder_ratio": 2,
    "warp_yarn_width": 0.5,
    "weft_yarn_width": 0.5,
    "binder_yarn_width": 0.05,
    "binder_yarn_height": 0.05,
    "binder_yarn_spacing": 0.5,
    "warp_layer": 3,
    "weft_layer": 4,
    "gap_size": 0.0,
    "swap": [[0, 1], [2, 1], [4, 1], [1, 2], [2, 2], [4, 2]],
    "warp_yarn_power": 0.6,
    "weft_yarn_power": 0.6,
    "binder_yarn_power": 0.6
}
```

### `angle_interlock_weave_3d`

```json
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
    "binder_yarn_power": 0.6
}
```

## 当前示例流程对应关系

现有流程：

```text
../API_modelling/Weave_3D/Ortho_Weave_3D.py
  -> ../Calculation/fix_vtu.py
  -> ../Calculation/generete_material_celldata.py
  -> ../Calculation/run_calc.bat
```

当前本项目内对应为：

```text
src/rve_batch/modelling/models.py
  -> src/rve_batch/preprocessing/vtu_order.py
  -> src/rve_batch/preprocessing/material_cell_data.py
  -> configs/solver/user_RVE_analysis.json
```

最后求解步骤暂未默认执行。

## 后续开发建议

1. 保持“默认参数 + JSON 覆盖”的方式，便于采样和批量计算。
2. 每个 case 使用独立输出目录，避免 VTU 文件互相覆盖。
3. 后续批量计算时，一组 JSON 参数对应一个 case。
4. 对每个 case 保存：输入 JSON、raw VTU、fixed VTU、分析模板、日志、结果摘要。
5. 训练数据只从已完成且校验通过的 case 生成，放入 `data/datasets/`。
