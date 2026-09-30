# OLS 复现

使用已有 Python、nbstata 与 Stata 安装。从仓库根目录运行：

```powershell
& $env:PYTHON_EXE tools/ols/run_notebook.py
```

脚本通过 `STATA_EXE` 定位 Stata，创建项目内临时 Jupyter 配置，从头执行 Notebook，保留真实输出。无需修改全局内核配置。也可在 Stata 中将当前目录设为仓库根，再执行 `do tools/ols/ols_ch1_run.do`。

使用冻结数据，不联网取数。输出写入 `output/ols/`，图形写入 `figs/raw/`；输出日志只保存在本地。主线为教育分组均值、个体层面 OLS、残差正交和均值点性质。Notebook 展示与 do-file 相同的分析代码，省去文件日志开关；执行器核验样本与系数。

网站渲染不执行代码：先运行上述命令保存输出，再运行 `powershell -ExecutionPolicy Bypass -File tools/build_book.ps1`。
