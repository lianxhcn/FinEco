# 金融计量经济学在线讲义

[阅读课程网站](https://lianxhcn.github.io/FinEco/) · [开始第一讲](https://lianxhcn.github.io/FinEco/lectures/intro.html)

中山大学岭南学院，连玉君，LN429，2 学分、36 学时。面向金融学、经济与金融等专业高年级本科生。Stata 为主要计量软件，Python 用于数据获取、处理与必要分析。

本版包含课程首页、课程简介与完整主题安排、第一讲理论篇、两个已执行的实验、环境配置、研究计划作业和参考资料。后续章节随授课加入。

## 学员入口

第一次使用请读[讲义与仓库使用指南](https://lianxhcn.github.io/FinEco/getting-started.html)：提供手动下载、Agent 准备提示词、基准复现、小实验和 Issue 反馈方法。可以直接读网页，无需先掌握 Git 或构建网站。

## 执行与网站维护

网页自带代码和执行结果，无需现场运行。股票案例使用 AKShare 获取的腾讯后复权行情快照；政策案例使用明确标注的模拟面板。

1. 按网站的环境准备页面配置 Python 和 Stata。
2. 在仓库根目录运行 `python tools/run_notebooks.py`，重新执行两个 Notebook。Stata 路径通过 `STATA_EXE` 环境变量提供。
3. 运行 `powershell -ExecutionPolicy Bypass -File tools/build_book.ps1` 构建静态网站；渲染不执行代码。
4. 检查 `docs/` 后提交并推送。GitHub Pages 从 `main` 分支的 `/docs` 发布。

数据获取脚本为 `tools/fetch_intro_prices.py`，重复获取会更新快照，常规复现无需联网取数。数据说明见 `data/intro/README.md`。

## 维护约定

理论与交叉引用放 `.qmd`，代码及实际输出放 `.ipynb`。正式目录为 `lectures/`、`notebooks/`、`data/`、`exercises/` 和 `resources/`；网页输出为 `docs/`。本地规划、教材与草稿所在的 `00#-` 目录不公开。

稳定规则见 `RULES.md` 与 `AGENTS.md`。第三方数据与文献仍受原来源的使用条件约束；本项目许可证待确认。
