# 项目 Agent 规则

先阅读 `RULES.md`、`PROJECT_PLAN.md`、`README.md`、`_quarto.yml` 、`repo-plan.yml` 和 `PROJECT_HANDOFF.md`。用户最新明确要求优先。

- 当前任务为金融计量经济学在线讲义，保持 Quarto Book 和稳定的主题文件名。
- `.qmd` 用于理论，`.ipynb` 用于执行代码与保存输出；修改代码后从头重跑。
- 网页渲染禁止执行代码和实时取数，发布已检查的 `docs/`。
- 原始资料只读。禁止读取 `009-temp-not-for-codex/`。根目录 `00#-` 区域不提交、不复制进网站。
- 保留来源、日期、口径及模拟标记。不得将教学模拟解释为真实政策效果。
- 不修改来源项目，不读取密钥。提交前核对范围，禁止无差别 `git add .`。
- 复杂任务记录于 `logs/quality_report.md`。图片遵循 `RULES.md` 中的 PicGo 规则。

- 并行写作前确认本章文件所有权。章节窗口不修改共享导航、样式、依赖和 docs，不在共享目录全书渲染或推送；由整合窗口统一接入与发布。
- 已确认写法与章节规划以 RULES.md、PROJECT_PLAN.md 为准；待讨论项不得擅自视作教师决定。

- 收到网页章节交接包时先读 `ASSET_MANIFEST.md`、`HANDOFF.md`，核对正文依赖；关键资产缺失时标记未就绪，不根据描述重造已确认但漏交的资产。
- 网页项目规则快照不自动同步，也不覆盖当前本地规则；教学决定须有教师确认依据。考虑最终交付和上下游依赖不扩大章节窗口权限，共享变更仍交整合窗口处理。
- 章节交接遵循 [交接标准](resources/chapter-handoff-standard.md) 与 [交付检查表](resources/chapter-delivery-checklist.md)，章级任务继续规定本章文件所有权。

## 书稿写作规则读取入口

- 全书规划、章节设计、正文写作、润色、公式/图形/实验整合及审阅开始时，实际读取 [写作索引](resources/writing/README.md) 与 [综合指南](resources/writing/GUIDE.md)，再按索引任务表读取材料。
- 各章格式、Callout、图表及导出遵守 [全书排版规范](resources/writing/FORMAT.md)；Word 导出另读 [样式清单](resources/writing/WORD-STYLES.md)，统一采用 `L-类别-用途`。这是后续章节默认要求，不自动触发已有章节重排或全站样式修改。
- 设计或重组章节使用 `resources/writing/CHAPTER-PLAN.md`；实质修改后使用 `resources/writing/REVIEW.md`。计划放入既有 `resources/writing-tasks/`，验收记录放入 `logs/<topic>/`，不混入教材正文。
- 新来源与规则更新按 `resources/writing/UPDATE.md` 执行。来源卡片记录依据，GUIDE 是 S01–S03 编辑规范的唯一有效版本；RULES、总规划与已确认章级任务优先。试用规则和候选建议不自动成为教师决定。
- 工作记录注明实际读取的规则版本、样章确认依据与关键验收位置。规则更新后显式重读。规则源文件位于 `resources/writing/`，不得在网站输出 `docs/` 中维护。

## 新会话默认承接

- 按 RULES 的“新会话默认工作流”执行：教师只需交代内容；单会话默认负责本章和后续整合，多会话仍由唯一整合窗口发布。先核实共享文件占用情况。
- 教师确认内容可整合/发布后，技术验收、精确提交、推送和部署核验沿用已有约定，不重复询问常规发布授权；本次明确的暂停/禁止发布指令优先。
- 环境入口为 resources/new-computer-environment.md。格式规范与模板实现分开核验；不将静态编译通过当作代码复现通过。
- 新机后续工作以当前 FinEco 主目录为唯一日常入口，承接步骤见 resources/writing-tasks/new-machine-continuity-plan.md。旧机迁移包、旧 worktree 和旧聊天只按明确缺口查阅；CSMAR 整理交由当前 dsed-data 项目，FinEco 相关修改/执行暂缓，不阻止其他章节推进。
