# FinEco 当前交接入口

更新：2026-10-29。本文件是当前新机继续工作的入口，不代替 RULES 或全书规划。教师已要求以 `D:/github_lianxh/FinEco` 为唯一日常工作主目录，后续从这里写作并发布；旧机迁移目录、旧 worktree 和旧聊天保留为按具体缺口查阅的备份。S1–S4 已完成；S5 已接回验收候选并重建，精确提交及发布核验正在进行。

## S5 最新状态

2026-10-29 教师明确要求进入 S5。MC/OLS 执行输出和共享 CSS 修复已按指纹接回正式文件，原件均有备份；代码、模型、样本和教学内容未改。6 张当前线性回归原图进入源资产范围。重新构建 26 页、4,579 项引用通过；实际发布快照保留已发布 CSMAR 页面，4,578 项引用通过，线性回归搜索/导航及下载一致。CSMAR 待整理工作区、历史分册/ZIP、印刷图与草稿继续保留。

正在按规则/环境与网站/输出两组精确提交。本机原生 Git 尚未认证，推送及 Pages 需要登录后继续核验；应用内 GitHub 连接已确认仓库写权限，不能据此宣称本机推送成功。当前清单与证据见 `logs/migration-20261028/s5-release-20261029/`。以下 S1–S4 表格和维护边界为阶段记录；其中未接回、HEAD/暂存区及禁止本次维护发布等旧状态，以本节为准。

## 新会话如何继续

先读 AGENTS、RULES、PROJECT_PLAN、README、_quarto.yml、repo-plan.yml，再按任务读取写作索引、GUIDE、FORMAT 和本章任务/正文。环境见 resources/new-computer-environment.md，迁移收尾顺序见 [新机承接计划](resources/writing-tasks/new-machine-continuity-plan.md)。教师只需描述教学内容；角色、验收与发布按 RULES“新会话默认工作流”。不以访问旧聊天或迁移包作为开工条件。

CSMAR 当前由 `D:/github_lianxh/dsed-data` 整理；FinEco 相关文件、未提交修改与执行暂缓，保留现有静态教学内容，不阻止其他章节。未来具体章节需要时再接入数据项目的已确认版本，不能假定整理中数据已就绪。本会话不修改数据项目或管理其他会话/进程。

## 当前可核实状态

| 范围 | 状态和有效入口 |
|---|---|
| 网站构建 | S4 隔离构建 26 页成功，4,579 项本地引用和下载检查通过；七个代表页桌面/窄屏检查通过，未逐页走读 26 页。输出与日志见 logs/migration-20261028/s4-case-site-validation-20261028/ |
| 原 docs | 31 个 HTML，比当前导航多五个历史 MC 分册页面；新构建 26 页不表示漏编当前导航。不为对齐数量而删除历史文件 |
| 金融数据 | 三篇理论、一篇 CSMAR 实验已在导航；历史上线依据见 logs/financial-data/publish-result.md。10 月 28 日 RAW 入口修订另见 logs/financial-data/raw-entry-review-20261028.md，未发布；后续 CSMAR 工作按教师最新要求暂缓，最终数据仍未批准 |
| OLS | S4 原运行器副本执行通过，N=428、系数/SE/代数检查及独立 NumPy 复算一致；代码未改、正式 Notebook 未覆盖。历史发布见 logs/ols/handoff.md |
| 线性回归 | 独立正文与 Stata 实验，保留原 OLS；logs/linear-regression/quality_report.md、handoff.md |
| Bootstrap | 正文和 Python/Stata 实验在导航，本机静态渲染通过；版本化交接 logs/bootstrap/published-v10-72fd19b/handoff.md 末尾记录 2026-09-15 执行/发布。顶层统一 handoff 缺失不等于无历史证据，新机案例执行仍待核验 |
| Monte Carlo | 当前统一 Notebook 的 66 原代码单元在 S4 最小副本从头执行，31 张表格和关键结果一致；正式 Notebook 未覆盖。发布基线仍为 2026-10-19 b6d0f76，旧五份实验保留 |
| 写作与格式 | resources/writing/ 为唯一规范入口；FORMAT 和 WORD-STYLES 已确认，完整模板/CSS 实施及 60%/150% 调整不能仅凭规范文件登记为已验收 |
| 环境 | 项目 .venv 已建立：Python 3.12.16，12 项根版本与 84 项完整锁定包匹配，启动通过；S4 已运行代表性 MC 和 OLS/Stata，不再依赖迁移环境 |
| Git/公网 | 本地 main/HEAD 保持 b6d0f76；S3 已只读查询公开远端 main，同样为该提交。未 fetch、验证写权限或重新检查网页部署；旧修改数量仅为历史基线，当前需重查，暂存区仍为空 |
| 发布相关遗留 | 隔离站点已恢复搜索/站点地图/导航，正式 docs 尚未接回；窄屏共享 CSS 修复只在隔离候选通过，正式 styles 未动。历史 MC 附件差异不纳入当前主入口，不能整包发布现有 docs |
| S2 变更归类 | 完成 255 项逐文件分类：非 CSMAR 218 项，CSMAR 37 项仅路径登记；首次规则/承接候选 29 项，原文件保留，未暂存/提交。证据见 logs/migration-20261028/s2-change-classification-20261028/S2_REPORT.md |

## 当前执行顺序

1. S1：本轮固定规划文档基线并更新入口；不是已建立运行/发布基线。
2. S2：已完成非 CSMAR 变更分类与精确候选清单，原文件原位保留；本阶段没有 reset、clean、prune、暂存或提交。待核验项均有后续处理方式，不阻塞下一步。
3. S3：已完成；启动/重建/检查工具位于 tools，未修改全局环境。
4. S4：已完成代表性执行和隔离候选验收；接入前读取 logs/migration-20261028/s4-case-site-validation-20261028/S4_REPORT.md 及 pending-promotions.json。CSMAR 不执行，原 Notebook/styles/docs 未覆盖。
5. S5：候选范围验收后沿用项目授权精确提交、推送和核验 Pages；本次规划维护不执行发布。
6. S6：教师可以随时指定新章，先完成设计或理论稿；内容确认后按默认工作流整合发布。下一章题目未预设。

依赖、产物与验收表见新机承接计划。完成章级工作时记录内容与技术验收，整合后更新状态。旧材料不作为默认启动依赖；确有独有缺件时先说明文件、用途和影响，不重新通读整个迁移包。

## 历史记录的适用边界

- PROJECT_PLAN 的 a03536f/12 页为早期背景；当前 HEAD 与导航见上表。
- Bootstrap 版本报告与金融数据发布记录末尾的后续结果更新其前部的未发布状态。MC 以 10 月 19 日读者修订发布报告为当前发布依据。
- 迁移验收已记录当前文件保全、独立环境和七份旧 worktree 文件副本；不继续把早期“8 GB 包尚未检查”当作现状，也不据此宣称原生会话/工作树关联或全部业务复现已恢复。
- 旧 worktree 注册不自动代表本机可正常接管；无必要不接管，不把部分文件副本误记为完整 checkout。

## 本次维护边界

2026-10-28 教师要求依次执行 S2–S4。当前完成 MC/OLS 代表性执行、数值与隔离静态站点/样式候选验收；正式讲义、Notebook、styles 和 docs 未接回，未暂存提交。下一步 S5；当前候选及待接回项目见 logs/migration-20261028/s4-case-site-validation-20261028/current-commit-manifest.json 和 pending-promotions.json，不使用 S2/S3 的旧文档指纹直接提交。

S3 只读远端核验：公开 main 与本地 b6d0f76 一致，未 fetch 或验证写权限。正常启动只需当前项目和本机常规软件，不依赖旧机或迁移环境。CSMAR 保持暂缓。
