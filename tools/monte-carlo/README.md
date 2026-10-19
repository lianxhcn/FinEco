# Monte Carlo 案例与代码

当前入口为 `notebooks/monte-carlo/monte-carlo-cases.ipynb`，将基础抽样与四个案例集中在同一页。在线阅读对应的 Quarto 网页即可查看已保存输出，页面不占正式章号，渲染不执行代码、不实时取数。

## 本地复现

克隆完整仓库后，在仓库内启动 Jupyter，打开统一 Notebook，从第一个单元依次运行。依赖 NumPy、pandas、Matplotlib、SciPy、statsmodels 和 IPython。仓库根目录或 Notebook 所在目录均可启动，不需要另行下载 ZIP。

案例三读取四份冻结数据：`data/monte-carlo/returns.csv`、`adjusted_prices.csv`、`stock_pool.csv` 和 `portfolio-results/portfolio_weights.csv`。机制图读取 `figs/raw/mc-valuation-fig01-mechanism-corrected-20261017-225145.png`。数据说明见 `data/monte-carlo/README.md`。不依赖教师本机的供应商缓存、`logs/` 或旧包的分析模块。

结果默认写入 `output/monte-carlo/cases/`，可通过环境变量 `FINECO_MC_OUTPUT` 指定另一输出目录。不会覆盖输入数据。案例三包含单日风险比较和 20 日买入持有的区块抽样，区块长度为 5、10、20 日；案例四以路径风险为主，期权定价折叠为扩展阅读。

## 维护与验收

构建器 `build_unified_notebook.py` 更新说明、图注和代码源，调用 `apply_patch`，需要 Codex 本地环境。它临时保留已有输出以便小范围修改，**不应在构建后直接渲染**；必须接着运行 `validate_unified_notebook.py`，从头执行并保存新输出。验收脚本需要本地历史核验基线，不是学生运行依赖。

旧五份 Notebook、ZIP 和旧运行器保留为历史材料，不再作为本章主入口。旧组合运行器的私有缓存限制不适用于当前统一 Notebook。图床映射见 `figs/monte-carlo-uploaded-images.md` 与 `figs/uploaded-images.md`。
