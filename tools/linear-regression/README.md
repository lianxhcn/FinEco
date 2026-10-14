# 线性回归章运行说明

从仓库根目录运行 `python tools/linear-regression/run_notebook.py`。使用已配置 `STATA_EXE` 和含 `nbstata` 的 Python 环境。本机使用环境变量 `PYTHON_EXE` 指向的 Python；不需要修改系统 PATH。

- 数据来源与哈希：`data/linear-regression/source-manifest.json`。
- 执行源：`linear-regression.do`；Notebook 按顺序在同一 Stata 内核执行。
- 真实输出：`notebooks/linear-regression/linear-regression-stata.ipynb`。
- 核对值与失败证据：`logs/linear-regression/`，不公开到网页。
- SSC 命令 `estout`、`binscatter`、`ftools`、`reghdfe` 只在缺失时安装；本次环境已具备这些命令。
- FWL、去均值、类别参数化和中心化用 Stata `assert` 核对。FWL 仅核对系数，正式推断仍看完整模型。
- 二维聚类实际产生非半正定/高度奇异警告及缺失标准误，保留为失败边界演示，不能据此检验显著性。`binscatter` 因工时离散，仅生成 11 个分箱，不能将分箱点当作总体 CEF。

网页渲染不执行 Notebook，也不实时获取数据。数据文件缺失或哈希不匹配时先核对快照；内核无法启动时核对 nbstata 环境和 STATA_EXE，不改写全局配置。
