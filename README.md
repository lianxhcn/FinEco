# 金融计量经济学在线讲义

[阅读课程网站](https://lianxhcn.github.io/FinEco/) · [开始第一讲](https://lianxhcn.github.io/FinEco/lectures/intro.html)

中山大学岭南学院，连玉君，LN429，2 学分、36 学时。面向金融学、经济与金融等专业高年级本科生。Stata 为主要计量软件，Python 用于数据获取、处理与必要分析。

本版包含研究流程、金融数据工作流、条件期望与 OLS、Bootstrap、Monte Carlo 及已执行实验，并提供环境配置、研究计划作业和参考资料。后续章节随授课加入。

金融数据单元：[流程与获取](https://lianxhcn.github.io/FinEco/lectures/financial-data.html) → [数据管理](https://lianxhcn.github.io/FinEco/lectures/financial-data-management.html) → [清洗与审计](https://lianxhcn.github.io/FinEco/lectures/financial-data-cleaning.html) → [CSMAR 实战](https://lianxhcn.github.io/FinEco/notebooks/financial-data/financial-data.html)。运行与数据下载见 [学生说明](data/financial-data/README.md)。

## 学员入口

第一次使用请读[讲义与仓库使用指南](https://lianxhcn.github.io/FinEco/getting-started.html)：提供 GitHub Desktop 与 Agent 两条可选路线。第一次课可直接读网页，之后克隆一次、课前更新。教师课件副本与个人作业仓库分开保存；一学期一个个人仓库，各次作业使用 hw-01 等目录。

## 执行与网站维护

网页自带代码和执行结果，无需现场运行。股票案例使用 AKShare 获取的腾讯后复权行情快照；政策案例使用明确标注的模拟面板。

1. 学员按网站环境准备页面配置软件；维护者按[本机环境说明](resources/new-computer-environment.md)使用项目 `.venv`，PowerShell 中运行 `. .\tools\Use-FinEcoEnvironment.ps1` 启用当前进程。
2. 在仓库根目录运行 `python tools/run_notebooks.py`，从头执行首讲两个 Notebook；其他章节按各自工具说明运行。启动脚本提供 `STATA_EXE`，网页渲染本身不执行案例。
3. 运行 `powershell -ExecutionPolicy Bypass -File tools/build_book.ps1` 构建静态网站；渲染不执行代码。首页发布日期由 `_quarto.yml` 中的 `book.date: today` 自动生成；每次发布须在发布当天重新构建，使日期对应本次发布。
4. 检查 `docs/` 后提交并推送。GitHub Pages 从 `main` 分支的 `/docs` 发布。

数据获取脚本为 `tools/fetch_intro_prices.py`，重复获取会更新快照，常规复现无需联网取数。数据说明见 `data/intro/README.md`。

## 维护约定

理论与交叉引用放 `.qmd`，代码及实际输出放 `.ipynb`。正式目录为 `lectures/`、`notebooks/`、`data/`、`exercises/` 和 `resources/`；网页输出为 `docs/`。本地规划、教材与草稿所在的 `00#-` 目录不公开。

稳定规则见 `RULES.md` 与 `AGENTS.md`。第三方数据与文献仍受原来源的使用条件约束；本项目许可证待确认。

各章格式统一遵守[全书排版规范](resources/writing/FORMAT.md)，Word 导出遵守[样式命名与结构清单](resources/writing/WORD-STYLES.md)。规则与模板实施状态分开维护，不在章节中复制一套排版规定。

## 后续章节与并行写作

新窗口先读 [项目规则](RULES.md) 和 [总规划与交接](PROJECT_PLAN.md)。总规划包含 20 章状态、文件命名、未决事项与可复制的启动提示词。章节窗口只改自己负责的文件，公共导航、依赖与网站构建由整合窗口统一处理。

OLS 单元：[条件期望与线性投影](https://lianxhcn.github.io/FinEco/lectures/ols.html) · [Stata 实验](https://lianxhcn.github.io/FinEco/notebooks/ols/ols-stata.html)。运行说明见 [OLS 工具说明](tools/ols/README.md)。

Monte Carlo 单元：[理论正文](lectures/monte-carlo.qmd)与[统一案例 Notebook](notebooks/monte-carlo/monte-carlo-cases.ipynb)。基础抽样和四个案例集中展示，包含组合多日区块抽样与路径风险。案例页不占正式章号，网页沿用已执行输出，不实时取数。本地复现使用仓库中的 Notebook 和处理后数据，无需另行下载 ZIP。运行说明见 [Monte Carlo 工具说明](tools/monte-carlo/README.md)。

## 书稿写作与审阅入口

统一读取 [写作规范索引](resources/writing/README.md) 和 [综合指南](resources/writing/GUIDE.md)。S01–S03 编辑建议按试用和候选状态采用，已确认教学要求优先；规则源文件使用 `resources/writing/`，不放在网站输出 `docs/`。

线性回归新章：[理论讲义](https://lianxhcn.github.io/FinEco/lectures/linear-regression.html) · [Stata 实验](https://lianxhcn.github.io/FinEco/notebooks/linear-regression/linear-regression-stata.html)。保留原 OLS 章，运行与数据说明见 `tools/linear-regression/README.md`。

## 新会话与新电脑继续写作

新会话先读 [当前交接入口](PROJECT_HANDOFF.md)。教师通常只需说明章节内容要求；Agent 按 RULES 承担格式、环境检查、执行与页面验收，并在内容确认后完成整合发布。多会话由唯一整合窗口发布。新电脑路径和已验证范围见 [环境说明](resources/new-computer-environment.md)。旧聊天和大型交接包按缺口检索，不是每章开工的必读全集。

自 2026-10-28 起，以当前 FinEco 目录为日常工作主目录，迁移收尾步骤与验收条件见 [新机承接计划](resources/writing-tasks/new-machine-continuity-plan.md)。CSMAR 数据整理暂由当前 `dsed-data` 项目推进，FinEco 相关修改与执行暂缓；其他章节正常规划和写作。后续需要时只接入数据项目的已确认版本，不以整理中数据替换已有教学结果。

项目环境已在 `.venv` 建立，完整依赖锁为 `requirements-lock.txt`。重建用 `tools/Initialize-FinEcoEnvironment.ps1`，启用后可运行 `python -B tools/check_environment.py` 自检。2026-10-29 已完成 MC/OLS 代表性执行、静态构建、本机精确提交推送与 Pages 发布验收；后续具体章节继续按任务核验，不使用旧机迁移环境作为日常入口。最新发布与保留范围见 [当前交接入口](PROJECT_HANDOFF.md)。
