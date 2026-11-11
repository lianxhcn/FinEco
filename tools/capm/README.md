# CAPM 运行说明

正文为 `lectures/capm.qmd`，独立实验为 `notebooks/capm/capm-stata.ipynb`。两份固定输入为 `data/capm/industry_monthly.dta` 和 `data/capm/beta_sim.dta`，数据说明和来源指纹与它放在同一目录。正常执行使用冻结输入，不联网取数，不访问旧机迁移目录或 CSMAR。

## 本机执行

在 FinEco 根目录的 PowerShell 中运行：

```powershell
. .\tools\Use-FinEcoEnvironment.ps1
python tools/capm/run_notebook.py
python tools/capm/validate_results.py
```

需要项目 `.venv` 中已经验收的 Python 依赖、可用的 Stata 19 MP 及其许可。环境重建沿用 `resources/new-computer-environment.md`，模拟数据已冻结，各次演示不重新生成随机数。本章没有增加根依赖。Stata 安装位置可通过当前进程的 `STATA_EXE` 指定；运行器核验该路径，只在本章日志内配置内核，不安装用户级 Jupyter 内核或修改全局 PATH。更换系统、Stata 版本或版本类型后应重新验收。

运行器先核验冻结输入指纹，再由 `capm.do` 构造七个代码单元，从头执行并保存真实输出。它将旧 Notebook 备份到 `logs/capm/backups/`；每轮图形用新的时间戳，旧图保留。相同种子和输入下统计结果应一致，图片元数据、运行时间与文件指纹可能变化。

结果位于 `logs/capm/`：十行业结果、滚动结果、模拟输入及结果的 DTA/CSV，另有 `execution.json` 和 `validation.json`。独立核验器用 NumPy 复算 OLS、Newey–West 方差、过去窗口和模拟斜率；Stata 是正式实验，不以 Python 替代其输出。

单独下载 ipynb 可以阅读已经保存的输出；重新执行仍需同一项目内的数据与工具。建议由运行器启动，保证工作目录、内核、图片时间戳和输入检查完整。正文只引用选定的一轮图；日后重新执行后，应确认图表与正文结果一致，再更新正文引用。

## 隔离预览

```powershell
python tools/capm/build_preview.py --format typst
python tools/capm/build_preview.py --format html
```

需要已安装的 Quarto，本机入口见环境说明；可用当前进程 `QUARTO_EXE` 指定。Typst 随 Quarto 提供，不需要另装 TeX。本机使用宋体、Times New Roman 和 Consolas；字体不同的电脑需要重新检查分页和缺字。

预览复制本章的明确资产到 `logs/capm/preview-project/`，所有渲染都禁用执行，不接触根 `_quarto.yml` 或 `docs/`。网页使用同源 SVG；A4 与网页使用同源 SVG 矢量图，保留空心圆路径；原生 Stata PDF 导出也保存在源资产中。纸面副本按 12 pt、A4、23 mm 页边距排版，并将公式引导段与公式绑定，避免浮动图将它们拆开。阅读入口分别为 `preview/lectures/capm.html`、`capm.pdf` 和 `preview/notebooks/capm/capm-stata.html`。

配色取自 FORMAT 1.0，仅在隔离预览中实现。代码和主案例不套满 Callout。Word 模板、全站 Callout 样式和规定的列表 60%/150% 相对间距尚未由本章升级；预览不能充当这些共享实现的验收。

## 来源更新

`fetch_sources.py` 是显式联网获取工具，保存来源、日期与失败记录，不由上述执行或渲染调用。`prepare_data.py` 从已保存 ZIP 生成分析输入，冻结输入存在时拒绝覆盖。更新数据应建立新版本、记录修订并重跑分析，不直接覆盖本次快照。公开再分发数据及正式网站接入另行按来源条件和项目发布流程处理。

独立预览不依赖全书的链接改写。构建器将实验 HTML 中的理论回链指向已生成的 `capm.html`；供下载的 ipynb 保留原始字节，其 QMD 链接适合从本地 Jupyter 访问源稿。正式接入全书时仍需检查理论/实验的往返链接。

两份输入各有完整的 README，见 data/capm/README.md。旧 monthly 名称退入本轮私有备份。单独更新真实数据用 prepare_data.py 并生成 industry_monthly-source.json；单独建立模拟新版本用 make_beta_sim.do，目标存在即拒绝覆盖。两者均不由课堂分析或网页构建调用，更新来源版本后再核对统一 source.json 指纹清单。

本轮按教师批注将三组双面板图改为一行两列，绘图区设置 aspectratio(1)，散点使用空心圆。Notebook 运行器只在本章隔离配置里设置 SVG 输出；独立区间图画布为 6.4×4.5 英寸，双面板为 6.4×3.2 英寸，绘图区仍近方形。Notebook 单列 4 个 `%set graph_height` 显示设置单元，8 个 Stata 分析单元与 master do-file 完全一致；全部 12 个代码单元从头执行。不使用 graph set window 或其他全局图形设置。纸面独立图为正文宽度的 86%，标注约 9.8–10.7 pt，与 10 pt 图注相当；图形上方为 8 pt (半行)、表格上方为 16 pt (一行)；图表注释下方均留一行净空，由末尾 20 pt 不可合并留白实现。图表标题与注释分段，正文 12 pt、标题 11 pt、注释 10 pt；自动图表编号加粗，列宽按表头和内容配置。节和小节标题上下均至少一行可见净空，纸面用各 20 pt 不可合并留白实现；参考文献自然衔接，不强制换页，单一整数编号后带点，多级小节仍为 6.1 等格式。


## 正文片段与完整实验

理论页包含 11 个已执行验证的短片段和 5 个输入明确的提示词，片段按正文顺序承接变量；完整执行顺序仍见原 Notebook。正文命令与选项为 12 pt，代码块仍为 8.5 pt；图表题居中、注释左对齐，注释后留一行可见净空。印刷预览将实验网页链接指向可下载的 ipynb；阅读版保存在 preview/lectures/ 下，以保留相对数据与 Notebook 链接。当前 GUIDE 0.2.4-fineco、FORMAT 1.5。


## esttab 与本轮 PDF 设置

2026-10-29 当前预览为 revised6。保留手动区间端点，新增 esttab 两行业并列的标准误与 95% 区间输出，完整 Notebook 另导出 logs/capm/regression.rtf。外部依赖 estout，本机实际命令 D:/stata/plus/e/esttab.ado，版本 2.1.1 (10jun2022)，沿用已安装版本，无安装或升级；首次使用可执行 ssc install estout，运行器只检查不自动安装。完整 Notebook 本轮从头执行 12 个代码单元，其中 8 个来自 master do-file、4 个为画布显示设置。独立核验器按实际代码单元检查顺序，不再写死原 11 单元数量。

按教师最新要求，本章 PDF 普通正文改为两端对齐，提示词段落及其行内命令为 11 pt，正常正文 12 pt、代码块 8.5 pt；框内和图表注释仍左对齐，图表题居中。本章例外取代此前本章 PDF 正文左对齐记录；FORMAT 1.5 的全书默认不在本轮扩改，网页正文保持左对齐。当前报告 logs/capm/review-20261029-esttab/REVISION_REPORT.md。


## 六项返修当前状态

2026-10-29 revised7 为 18 页。全部十个 Callout 标题、正文及行内代码统一为 10.5 pt，替代本章此前提示词 11 pt/标题 12 pt 的记录；正常正文仍为 12 pt 且 PDF 两端对齐，图表短题 11 pt、注释 10 pt、代码块 8.5 pt 不变。网页按 10.5/12 比例适配，标题和正文相同字号。前述 esttab 修订为历史，现行设置以本段与章级任务为准。

所有 11 个正文片段重新执行，display 的系数、标准误、均值/标准差、R2、区间和组合结果均带标签与固定精度；原多表达式语法有效，但无分隔输出不适于讲义。Notebook 12 单元重跑，master do-file 与固定数据均未改。六篇文献说明同步更新，原文证据见 logs/capm/review-20261029-six-points/literature-evidence.json。在线数据仅作评估，两份 raw 地址当前返回 404；正式发布时再添加固定版本在线入口，不让完整实验依赖逐次联网。本轮无安装或发布。


## 2026-11-11 课堂批注：实验支撑

本轮保留理论正文与可独立阅读的 Notebook 两个文档。运行器持久生成不编号的实验标题和 `number-sections: false`，参照现有 Monte Carlo 实验的首 Markdown 单元 YAML；同时设置渲染禁用执行。Notebook 的数据定义、模型、推断边界、六篇应用论文联系及完整实验均保留，理论页、数据说明、运行说明采用相对链接，另提供 GitHub 项目和通用目录入口。新 CAPM 文件尚未发布时，不提供尚不存在的 raw 数据执行地址。

主 do-file 新增行业文件前六行的真实列表、样本协方差矩阵 `V` 的 `matrix list V` 和协方差比值算出的 `beta` 输出；该 `V` 不等于系数估计的 `e(V)`。在完整滚动循环前，另显示以 2025 年 12 月为目标、仅用此前 60 个月的单次回归。短回归命令写为一行，全部 Stata 行仍不超过 76 列。样本、模型、HAC(6)、完整滚动窗口与固定数据均未改变。

本轮从头执行和独立复算的记录、正文可复制的矩阵与前六行表，见 `logs/capm/review-20261111-20comments/execution/`；运行器的常规执行和验证 JSON 仍写入 `logs/capm/`。覆盖前的四个工作文件及已有结果备份集中在本轮 `before/`，并保存 SHA256 清单。运行后由整合窗口单独检查理论页和实验 HTML 的编号、往返链接与显示，不以执行通过替代页面验收。
