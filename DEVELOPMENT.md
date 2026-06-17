# 3DRVE Batch - 开发技术文档

## 项目定位

3DRVE Batch 是一个**复合材料代表性体积单元（RVE）批量参数化建模工具**。

**核心能力：** 参数化建模 + LHS 拉丁超立方采样 + 批量 VTU 网格生成

**求解计算：** 由外部独立项目负责，本项目输出建模后的 VTU 网格与求解器配置模板

---

## Batch Modeling Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BATCH MODELING WORKFLOW                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐       │
│  │  DOE Config  │────▶│  LHS Sampling│────▶│ Const. Check │       │
│  │   JSON File  │     │ Generate  N  │     │ Filter Invalid│       │
│  └──────────────┘     └──────────────┘     └──────────────┘       │
│         │                      │                      │             │
│         ▼                      ▼                      ▼             │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                   batch_config.json                          │  │
│  │  Metadata + Sampling Space + Constraints + All Sample Params  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│              ┌───────────────┴───────────────┐                       │
│              │                               │                       │
│              ▼                               ▼                       │
│     ┌────────────────┐            ┌────────────────┐                │
│     │   Case 0001    │            │   Case NNNN    │                │
│     │  Param Override│     ...    │  Param Override│                │
│     └────────────────┘            └────────────────┘                │
│              │                               │                       │
│              ▼                               ▼                       │
│     ┌────────────────┐            ┌────────────────┐                │
│     │  TexGen Build  │            │  TexGen Build  │                │
│     │  Initial VTU   │            │  Initial VTU   │                │
│     └────────────────┘            └────────────────┘                │
│              │                               │                       │
│              ▼                               ▼                       │
│     ┌────────────────┐            ┌────────────────┐                │
│     │  VTU PostProc  │            │  VTU PostProc  │                │
│     │ ─────────────  │            │ ─────────────  │                │
│     │ ✓ Material     │            │ ✓ Material     │                │
│     │ ✓ YarnIndex    │            │ ✓ YarnIndex    │                │
│     └────────────────┘            └────────────────┘                │
│              │                               │                       │
│              ▼                               ▼                       │
│     ┌─────────────────────────┐  ┌─────────────────────────┐        │
│     │   Case Directory        │  │   Case Directory        │        │
│     │ ─────────────────────   │  │ ─────────────────────   │        │
│     │ • input_params.json     │  │ • input_params.json     │        │
│     │ • sampled_overrides.json│  │ • sampled_overrides.json│        │
│     │ • geometry.vtu          │  │ • geometry.vtu          │        │
│     │ • solver_config.json    │  │ • solver_config.json    │        │
│     └─────────────────────────┘  └─────────────────────────┘        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. 支持的 RVE 类型

### 1.1 二维编织（2D Woven）
**代码映射：** `woven_weave_2d`

| 特征 | 说明 |
|------|------|
| 基本形式 | 平纹（Plain Weave） |
| 扩展形式 | 剪切编织、多层编织 |
| 纱线方向 | 经纱（Warp）× 纬纱（Weft） |
| 典型应用 | GFRP、CFRP 薄层板 |

**派生类型：**
- `sheared_woven_weave_2d` - 剪切二维编织
- `layered_woven_weave_2d` - 多层二维编织

### 1.2 三维正交编织（3D Orthogonal Weave）
**代码映射：** `orthogonal_weave_3d`

| 特征 | 说明 |
|------|------|
| 纱线系统 | 经纱 + 纬纱 + Z 向接结纱（Binder） |
| 结构特点 | 纱线正交排列，厚度方向强度高 |
| 典型应用 | 航空航天、汽车结构件 |

### 1.3 三维角联锁编织（3D Angle Interlock Weave）
**代码映射：** `angle_interlock_weave_3d`

| 特征 | 说明 |
|------|------|
| 特点 | 经纱在厚度方向呈角状交织 |
| 优势 | 层间剪切强度高、抗分层性能好 |
| 典型应用 | 防弹装甲、高载荷结构件 |

---

## 2. 各 RVE 类型参数说明

### 2.1 网格通用参数（mesh）

| 参数 | 类型 | 默认值 | 范围建议 | 说明 | 备注 |
|------|------|--------|----------|------|------|
| `x_voxel` | int | 80-100 | 80-100 | X 方向体素数 | 建议保持默认 |
| `y_voxel` | int | 80-100 | 80-100 | Y 方向体素数 | 建议保持默认 |
| `z_voxel` | int | 80-100 | 80-100 | Z 方向体素数 | 建议保持默认 |

### 2.2 二维编织几何参数（woven_weave_2d）

| 参数 | 类型 | 默认值 | 范围建议 | 说明 | 备注 |
|------|------|--------|----------|------|------|
| `warp_count` | int | 3 | 2-8 | 经纱根数 | 批次参数，不进采样空间 |
| `weft_count` | int | 2 | 2-8 | 纬纱根数 | 批次参数，不进采样空间 |
| `spacing` | float | 1.0 | 0.5-2.0 | 纱线间距 | |
| `thick` | float | 0.5 | 0.1-1.0 | 纱线厚度 | |
| `width` | float | 0.8 | 0.3-1.5 | 纱线宽度 | |
| `gapsize` | float | 0.0 | 0-0.2 | 纱线间隙 | |
| `angle` | float | 0.0 | 0-60 | 剪切角（仅剪切型） | |
| `layer_count` | int | 0 | 0-5 | 层数（仅多层型） | 批次参数，不进采样空间 |
| `swap` | list[list] | [[0,1],[1,0]] | - | 纱线交叉位置 | 批次参数，不进采样空间 |

### 2.3 三维正交编织几何参数（orthogonal_weave_3d）

| 参数 | 类型 | 默认值 | 范围建议 | 说明 | 备注 |
|------|------|--------|----------|------|------|
| `warp_count` | int | 6 | 2-12 | 经纱根数 | 批次参数，不进采样空间 |
| `weft_count` | int | 4 | 2-12 | 纬纱根数 | 批次参数，不进采样空间 |
| `warp_spacing` | float | 1.0 | 0.5-3.0 | 经纱间距 | |
| `weft_spacing` | float | 1.0 | 0.5-3.0 | 纬纱间距 | |
| `warp_height` | float | 0.1 | 0.05-0.3 | 经纱高度 | |
| `weft_height` | float | 0.1 | 0.05-0.3 | 纬纱高度 | |
| `warp_ratio` | int | 1 | 1-3 | 经纱与接结纱比例 | 根据批次区分，不进采样空间 |
| `binder_ratio` | int | 1 | 1-3 | 接结纱比例 | |
| `warp_yarn_width` | float | 0.85 | 0.3-1.5 | 经纱宽度 | |
| `weft_yarn_width` | float | 0.85 | 0.3-1.5 | 纬纱宽度 | |
| `binder_yarn_width` | float | 0.4 | 0.1-0.8 | 接结纱宽度 | |
| `binder_yarn_height` | float | 0.1 | 0.05-0.3 | 接结纱高度 | |
| `binder_yarn_spacing` | float | 0.5 | 0.2-1.0 | 接结纱间距 | |
| `warp_layer` | int | 4 | 1-8 | 经纱层数 | |
| `weft_layer` | int | 4 | 1-8 | 纬纱层数 | |
| `gap_size` | float | 0.0 | 0-0.2 | 纱线间隙 | |
| `swap` | list[list] | - | - | 接结纱交叉位置 | 批次参数，不进采样空间 |

### 2.4 三维角联锁编织几何参数（angle_interlock_weave_3d）

| 参数 | 类型 | 默认值 | 范围建议 | 说明 | 备注 |
|------|------|--------|----------|------|------|
| `warp_count` | int | 5 | 2-12 | 经纱根数 | 批次参数，不进采样空间 |
| `weft_count` | int | 8 | 3-16 | 纬纱根数 | 批次参数，不进采样空间 |
| `warp_spacing` | float | 1.0 | 0.5-3.0 | 经纱间距 | |
| `weft_spacing` | float | 1.0 | 0.5-3.0 | 纬纱间距 | |
| `warp_height` | float | 0.1 | 0.05-0.3 | 经纱高度 | |
| `weft_height` | float | 0.1 | 0.05-0.3 | 纬纱高度 | |
| `warp_ratio` | int | 1 | 1-3 | 经纱与接结纱比例 | |
| `binder_ratio` | int | 1 | 1-3 | 接结纱比例 | |
| `warp_yarn_width` | float | 0.8 | 0.3-1.5 | 经纱宽度 | |
| `weft_yarn_width` | float | 0.8 | 0.3-1.5 | 纬纱宽度 | |
| `binder_yarn_width` | float | 0.4 | 0.1-0.8 | 接结纱宽度 | |
| `binder_yarn_height` | float | 0.05 | 0.05-0.2 | 接结纱高度 | |
| `binder_yarn_spacing` | float | 0.5 | 0.2-1.0 | 接结纱间距 | |
| `gap_size` | float | 0.0 | 0-0.2 | 纱线间隙 | |

### 2.5 材料参数

| 材料 | 杨氏模量 E (Pa) | 泊松比 ν | 说明 |
|------|----------------|---------|------|
| Glass（玻璃纤维） | 69e9 | 0.2 | material_0 / 纤维相 |
| Epoxy（环氧树脂） | 4.8e9 | 0.34 | material_1 / 基体相 |

---

## 3. 参数维度与采样空间设计

### 3.1 参数分类体系

| 分类 | 级别 | 描述 | 处理方式 |
|------|------|------|---------|
| **批次固定参数** | Batch Level | 批次内所有样本相同 | 直接写入 base_overrides |
| **几何可变参数** | Geometry Level | 影响细观结构的关键尺寸 | LHS 采样变量 |
| **材料可变参数** | Material Level | 材料属性的不确定性 | LHS 采样变量 |
| **网格分辨率** | Mesh Level | 体素网格密度 | 一般保持固定 |

### 3.2 LHS 拉丁超立方采样机制

**采样流程：**
```
1. 读取 lhs_space 配置（各参数 min/max 和类型 int/float）
2. 生成 N 维单位超立方样本点（N = 采样维度）
3. 拉丁超立方排列：每维度仅出现一次（无重复，无遗漏）
4. 线性映射到各参数的实际物理范围
5. 应用参数约束表达式，过滤无效样本
6. 约束满足 → 样本保留；不满足 → 补充采样直到凑够样本数
```

### 3.3 推荐采样空间示例

**二维平纹编织：**
```json
{
  "geometry.spacing":     {"min": 0.7, "max": 1.3},
  "geometry.thick":       {"min": 0.3, "max": 0.7},
  "geometry.width":       {"min": 0.5, "max": 1.0},
  "geometry.gapsize":     {"min": 0.0, "max": 0.1},
  "materials.material_0.E": {"min": 30e9, "max": 80e9},
  "materials.material_0.nu": {"min": 0.25, "max": 0.35}
}
```

**三维正交编织：**
```json
{
  "geometry.warp_spacing":   {"min": 0.5, "max": 2.0},
  "geometry.weft_spacing":   {"min": 0.5, "max": 2.0},
  "geometry.warp_height":    {"min": 0.05, "max": 0.2},
  "geometry.weft_height":    {"min": 0.05, "max": 0.2},
  "geometry.warp_yarn_width": {"min": 0.5, "max": 1.2},
  "geometry.weft_yarn_width": {"min": 0.5, "max": 1.2},
  "geometry.binder_yarn_width": {"min": 0.2, "max": 0.6}
}
```

### 3.4 参数约束表达式

**内置约束（自动应用）：**
- 几何可行性：`width < spacing`
- 纱线重叠避免：`thick < spacing`

**自定义约束（JSON 配置）：**
```json
"constraints": [
  "width < 0.95 * spacing",
  "thick < spacing",
  "material_0_E > 0",
  "0 < material_0_nu < 0.5",
  "warp_yarn_width < warp_spacing",
  "weft_yarn_width < weft_spacing"
]
```

---

## 4. 代码模块结构

### 4.1 核心模块

| 文件 | 职责 | 关键类/函数 |
|------|------|------------|
| `src/rve_batch/modelling/woven_weave.py` | 二维编织建模 | `NormalWeave2D` 类 |
| `src/rve_batch/modelling/orthogonal_weave.py` | 三维正交编织建模 | `OrthoWeave3D` 类 |
| `src/rve_batch/modelling/angle_interlock.py` | 三维角联锁建模 | `AngleInterlockWeave3D` 类 |
| `src/rve_batch/modelling/models.py` | 统一建模入口 | `default_model_params()`, `build_model()` |
| `src/rve_batch/batch_calculation.py` | 批量调度核心 | `run_lhs_batch()`, `run_lhs_batch_from_config()` |
| `src/rve_batch/doe.py` | LHS 采样与约束校验 | `generate_lhs_cases()` |

### 4.2 脚本入口

| 脚本 | 功能 | 调用方式 |
|------|------|---------|
| `scripts/run_batch_doe.py` | 批量 DOE 建模入口 | `--config xxx.json` 或 CLI 参数 |
| `scripts/generate_doe_templates.py` | 生成各 RVE 类型的配置模板 | 直接运行，输出到 `configs/doe_templates/` |

---

## 5. 后续扩展路线图

### Phase 1: 建模能力增强

- [ ] 界面相（Interphase）精细建模与 VTU 输出
- [ ] 孔隙率与缺陷分布统计建模（随机位置、随机尺寸）
- [ ] 多尺度嵌套 RVE 生成：纱线级 → 织物级 → 预制体级

### Phase 2: 采样与设计空间拓展

- [ ] 支持更多采样方法：Sobol 序列、Optimal LHS、自适应采样
- [ ] 参数敏感度分析工具（ANOVA /  Morris 法）
- [ ] 设计空间可视化（高维降维：PCA / t-SNE）
- [ ] 采样质量评估指标（空间填充度、分层均匀性）

---

**文档版本：2.0 | 最后更新：2025-06-17**
