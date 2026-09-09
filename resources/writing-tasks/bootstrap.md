# 写作任务：Bootstrap

状态：已选定、待启动。主题标识：bootstrap。

请在本任务的独立 worktree 中完成本章。先阅读 AGENTS.md、RULES.md、PROJECT_PLAN.md、_quarto.yml 和 lectures/intro.qmd。报告实际工作目录和起始提交，确认没有在主目录直接写作。

## 目标与范围

采用固定种子的独立模拟或自带数据，讲清重复抽样思想、经验分布、标准误和置信区间，用 Stata 优先实现。区分 bootstrap 重抽样与蒙特卡洛重复生成数据；说明普通 iid 重抽样不适合直接套用有序金融时间序列。

按本科生可自学的讲义撰写：每节先说明问题与目标，再展开细节；公式解释全部新符号、单位和界定方法，案例结果指向实际表格和图形。章末列完整参考文献和数据来源。

## 文件所有权

只负责 lectures/bootstrap.qmd、notebooks/bootstrap/、data/bootstrap/、tools/bootstrap/、figs/raw/bootstrap-*、figs/bootstrap-uploaded-images.md 和 logs/bootstrap/。这些路径均相对于本 worktree。已有首讲数据只读，衍生结果保存到本章目录。你并非唯一工作窗口，不撤销其他窗口改动，不接管其他章节。

不要修改 _quarto.yml、styles.css、RULES.md、PROJECT_PLAN.md、首页、作业总览、公共书目、公共依赖、公共运行器和主网站 docs。所需公共变更写在交接报告，由整合窗口处理；不要创建或推送公共网站。

## 执行与交付

1. 先拟定简短任务书并保存到 logs/bootstrap/handoff.md，随后继续完成已明确的写作和实验，不止于提交提纲。关键数据或目标缺失时提出具体问题，同时继续独立部分。
2. 理论使用 qmd，代码及真实执行输出用 ipynb。检查可用内核和软件路径，最小示例通过后再运行本章完整案例；遇到 Stata 并发冲突排队，不关闭其他任务进程。
3. 在本 worktree 的隔离预览中检查页面，不能覆盖主工作目录 docs，不提交预览生成目录。缺少忽略目录的材料或环境时如实记录。
4. 交付完整讲义、已执行 Notebook、可公开的数据与来源说明，以及交接报告。汇报修改路径、执行命令、结果和未决事项。报告放在 logs，不能遗漏其移交。
5. 不推送，不合并 main，不删 worktree。完成后给教师简短摘要和当前工作目录；由整合窗口检查、接入和发布。
