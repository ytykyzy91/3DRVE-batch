# 流水线设计

## 单个 RVE 流程

```text
1. load_config
2. load_case_params
3. build_texgen_model
4. export_raw_vtu
5. fix_vtu_node_order
6. add_material_cell_data
7. render_solver_config
8. run_solver
9. collect_outputs
10. write_summary
```

## 批量计算流程

```text
1. 读取参数表或调用采样器生成参数集
2. 为每组参数分配 case_id
3. 创建 data/results/<case_id>/
4. 对每个 case 运行单个 RVE 流程
5. 记录每个 case 的 status.json
6. 汇总所有 summary.json 到 data/datasets/
```

## 近期扩展点

### 参数采样

建议先支持三类来源：

- 手写 YAML/JSON 参数列表。
- CSV 参数表。
- 采样器自动生成，例如 full-factorial、Latin hypercube、随机采样。

### 批量计算

建议最小实现：

- 顺序执行。
- 每个 case 独立目录。
- 失败不中断整个批次。
- 已有 `status.json` 且成功的 case 默认跳过。

之后再加入：

- 多进程并行。
- 失败重试。
- 任务队列。
- 断点续算。

### 神经网络训练

后续可从 `data/results/*/summary.json` 与原始参数构建监督学习数据集：

```text
X = RVE 几何参数 + 材料参数 + 网格/体积分数特征
y = 等效性能或求解输出指标
```

训练相关代码放在 `src/rve_batch/ml`，训练产物放在 `data/models`。
