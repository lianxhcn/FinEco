# FinEco 环境检查任务

先读 README 和 requirements.txt，检查已有的 Python、Jupyter、Stata 与内核。记录路径和版本，优先使用项目环境。不读取凭据，不先重装软件或改全局 PATH。Stata 路径通过检查确认。

提出最小修复方案，系统级变更由用户决定。用同一 Python 安装包与选择内核。分别运行 Python 均值示例和 Stata auto 回归，重启内核再从头运行并保存结果。错误保留原文，不把已安装等同于可复现。

需要批量执行本书案例时，确认 STATA_EXE 指向有效程序，再使用 tools/run_notebooks.py。运行时文件位于不发布的 002-working/runtime/。
