# 架构说明

## 分层原则

项目按“输入参数 -> 建模 -> 预处理 -> 求解 -> 采样/汇总 -> 数据集/训练”的数据流分层。

每一层只关心自己的输入输出，避免把 TexGen、VTU 修正、求解器命令、批量调度全部写在一个脚本里。

## 模块职责

### `config`

- 加载 `configs/project.yaml`。
- 管理外部依赖路径，例如 TexGen Python API、求解器 exe、Plexian config。
- 管理默认输出路径和命名规则。
- 校验参数文件。

### `modelling`

- 封装 TexGen API。
- 提供不同 RVE 类型的建模器，例如 orthogonal weave、angle interlock weave。
- 输出原始 VTU/STEP 等几何或网格文件。

### `preprocessing`

- 修正 VTU 节点顺序。
- 增加 `Material` CellData 字段。
- 检查 VTU 是否包含 `YarnIndex`、`Material` 等必须字段。
- 未来可加入网格质量检查、体积分数统计。

### `solver`

- 基于模板生成每个 case 的求解 JSON。
- 封装 `vg_solver.exe` 调用。
- 记录 stdout/stderr、返回码、运行时间。

### `sampling`

- 近期：参数采样，例如网格尺寸、纱线间距、纱线宽高、材料参数。
- 近期：结果采样，例如从 VTU/日志中提取等效模量、强度、体积分数等指标。

### `batch`

- 根据采样结果或参数表创建 case。
- 为每个 case 创建独立目录。
- 串联流水线并记录状态。
- 支持失败重试、跳过已完成 case、并行执行。

### `ml`

- 后续：从 `data/results` 构建机器学习数据集。
- 后续：训练、评估、推理。

## Case 目录建议

每个 case 使用独立目录，避免批量计算时文件覆盖。

```text
data/results/case_000001/
├── params.yaml
├── model_raw.vtu
├── model_fixed.vtu
├── analysis.json
├── solver.log
├── status.json
└── summary.json
```

`status.json` 建议记录：

- `case_id`
- `stage`
- `status`: pending/running/succeeded/failed/skipped
- `start_time`
- `end_time`
- `error_message`
- 关键输出文件路径

## 文件命名建议

- 原始 TexGen 输出：`model_raw.vtu`
- 节点顺序修正后：`model_fixed.vtu`
- 增加 Material 后：如果覆盖修正文件，仍为 `model_fixed.vtu`；如果保留中间态，则为 `model_material.vtu`
- 求解配置：`analysis.json`
- 求解日志：`solver.log`
- 汇总指标：`summary.json`
