# FinEco 写作规则索引

版本：0.2.0-fineco。日期：2026-10-20。状态：教学编辑的 S01–S03 增量仍为试用；全书格式与 Word 样式方案经教师认可，作为后续各章默认要求，实施和验收另记。

## 1. 入口、依据与唯一指南

根目录 [AGENTS](../../AGENTS.md) 负责读取入口；[RULES](../../RULES.md) 保存已确认约定，[PROJECT_PLAN](../../PROJECT_PLAN.md) 保存规划与状态。S01–S03 综合编辑规范唯一有效文件为 [GUIDE](GUIDE.md)。不建立平行 current/final/v2；来源、示范、模板不构成第二套权威指南。

全书格式的唯一维护文件为 [FORMAT](FORMAT.md)，Word 样式命名与继承关系的唯一维护文件为 [WORD-STYLES](WORD-STYLES.md)。二者专门约束版式与结构化交付，不另立教学写作指南；章级旧样张规范只保留历史依据，后续执行以这里为准。

本目录复用 `resources/` 学习与教学资源体系，章级设计继续使用 `resources/writing-tasks/`，工作证据使用 `logs/`。`docs/` 是可重建的网站输出，不作为规则源目录。原交接包 `003-tasks/daed-style-handoff/` 只作历史来源，不用于日常读取。规则历史见 [CHANGELOG](CHANGELOG.md)。

## 2. 按任务读取

| 任务 | 必读 | 按需读取 |
|---|---|---|
| 每次写作相关任务 | 本索引、GUIDE、FORMAT、相关章级任务 | 教师最新要求 |
| 首次整合 | 原包 INSTALL、全部来源卡片、EXAMPLES、REVIEW | 旧规范、样章与规则 |
| 全书或分部规划 | CHAPTER-PLAN 的问题与依赖部分、PROJECT_PLAN | S03、实际目录与前章状态 |
| 章节设计或结构改写 | CHAPTER-PLAN、EXAMPLES | 相关来源、确认参照 |
| 局部润色 | EXAMPLES 相关示范 | 无需重做全章计划 |
| Callout、图表及网页版式 | FORMAT、REVIEW 的版式项 | 公共样式由整合窗口处理，不直接套 A4 参数 |
| Word/PDF 导出或模板修改 | FORMAT、WORD-STYLES、相关导出 Skill | 样张与实施记录，按格式要求验收 |
| Stata/Python 实验 | GUIDE 代码与证据条款、REVIEW 相关项 | 数据、运行工具、环境 |
| 章节验收 | REVIEW、实际章节设计 | 数值、图形、执行和页面证据 |
| 新来源或规则更新 | UPDATE、CHANGELOG、RULE-MAP | 新来源与受影响章节 |

材料：[设计模板](CHAPTER-PLAN.md)、[原创示范](EXAMPLES.md)、[验收](REVIEW.md)、[来源映射](RULE-MAP.md)、[更新流程](UPDATE.md)。每次任务记录真实读取，不要求重复读三本 PDF。

## 3. 来源

- [S01](sources/S01-qiu.md)：连续比较、完整推理与条件。
- [S02](sources/S02-tigre.md)：分析困难、设计、估计与判断。
- [S03](sources/S03-islp.md)：共同评价、成组比较与解释型习题。

来源卡片保留上游阅读范围；本轮未重新阅读原书全文或访问外部链接，不把既有记录描述为本轮核验。新增 S04 使用 [来源模板](sources/SOURCE-TEMPLATE.md)。

## 4. 样章与参照登记

| 材料与路径 | 状态与确认依据 | 采用边界 |
|---|---|---|
| [首讲](../../lectures/intro.qmd) | RULES 的讲解与排版条款明确指定为参照；本次未取得独立逐段确认日期，不补造提交号 | 讲解深度、列表和公式释义；不强制全章结构 |
| [OLS](../../lectures/ols.qmd) | 本地已有正文，README 登记已上线；不据上线状态推断逐段样章确认 | 核对实际先修接口，不能用旧任务状态代替正文检查 |
| `lectures/model-specification.qmd` | 当前主目录未找到；章级任务已授权，确认样章缺失 | 不建立空样章，不标记 author-confirmed |
| [EXAMPLES](EXAMPLES.md) | 原包原创教学示范，未经教师逐段确认 | 解释规则功能；工资数值为设定，不能替换两章共同小表 |
| [本轮设计示例](../writing-tasks/model-specification-style-design.md) | draft，2026-10-14 模型自检，非教师确认 | 验证读取与讲述顺序，不是正文终稿 |
| MC A4 v3 与六页 Callout 样张 | 2026-10-20 教师综合认可格式方向，ACC-059 | 作为 FORMAT 的纸面参考；六页样张尚未实施随后提出的 60%/150% 列表间距，旧 Word 也未迁移到新命名样式 |

新增确认材料必须记录准确路径、确认日期及依据、适用范围和规则版本，保留正文原位置。

## 5. 工作记录

设计保存在 `resources/writing-tasks/`，审阅与交接保存于 `logs/<topic>/`。本次报告：`logs/writing-integration/RULE-INTEGRATION-REPORT.md`。状态区分 draft、reviewed、author-confirmed；模型自检不等于作者确认。版本变化同步更新本索引、GUIDE、CHANGELOG；AGENTS 入口变化后在新会话重新完成读取测试。
