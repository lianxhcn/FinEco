# 金融数据章工具

- `pipeline.py`：从 ZIP 生成标准化表、候选年度底表和审计汇总。无实时取数。
- `test_pipeline.py`：检查重复键拒绝、相邻年度分母、零分母和 outer merge 行数。
- `build_notebook.py`：维护 Notebook 源码，运行会重建 Notebook 并清空旧输出；随后必须执行。
- `run_notebook.py`：用当前 Python 的临时本地内核执行并保存 Notebook，不修改全局内核。
- `publish_metadata.py`：仅复制固定允许清单中的汇总，并生成字典、来源清单和报告；不复制公司记录。
- `config.example.ps1`：可迁移数据路径示例。
- `teaching_examples.py`：三章理论的小表验证，全部为虚构数据，可独立运行。
- `case-background.md`：Notebook 构建所需的本批数据背景，不依赖被忽略的日志目录。

规则模板与 P00–P07 提示词位于 `data/financial-data/agent-project/`。

运行方式与数据权限见 `data/financial-data/README.md`。共享依赖和全书渲染由整合窗口处理。
