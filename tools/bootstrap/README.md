# Bootstrap v10 实验

来自教师确认的 `v10-final / canonical-handoff-v01`。从 FinEco 根目录运行：

```powershell
& $env:PYTHON_EXE tools/bootstrap/bootstrap_core.py
& $env:PYTHON_EXE tools/bootstrap/make_figures.py
& $env:PYTHON_EXE tools/bootstrap/run_v10.py
```

`run_v10.py` 从头执行两个 Notebook，使用项目内临时内核配置，不修改全局内核。依赖 NumPy、pandas、SciPy、Matplotlib、nbformat、nbclient、jupyter-client、ipykernel、nbstata，并要求 `STATA_EXE` 指向可用的 Stata。已核验 Python 3.11.14 和 Stata 19.5。

- `bootstrap_core.py` 输出教学数据到 `data/bootstrap/`，数值结果到 `logs/bootstrap/v10/`。
- `make_figures.py` 输出五张核验图到 `logs/bootstrap/v10/recomputed/`。正式讲义保留包内原图。
- `01-tiny-bootstrap.do` 核验五点样本均值。
- `02-group-bootstrap.do` 在两组内部抽样；清除最后一组回归的 `e(sample)`，避免污染外层抽样母样本。
- `03-bdiff-interface-only.do` 仅核验接口，不能替代组内 Bootstrap。

真实输出保存在 `notebooks/bootstrap/bootstrap-demo.ipynb` 和 `bootstrap-stata.ipynb`。网页渲染禁用执行。整合时请按 `logs/bootstrap/handoff.md` 的清单移交，避免把历史版本和执行日志复制进网站。
