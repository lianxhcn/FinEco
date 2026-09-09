# 课程主题与写作安排

本课程面向金融学、经济与金融等专业高年级本科生，共 36 学时。书稿包含完整主题，实际授课按课时选择；以下为全书写作安排，当前版本完整提供第一讲及配套实验。

## 第一讲

第一讲定位为“课程导览与实证金融研究流程”，通过两个案例讲解目标设定、数据、模型与评价：

- 10 只股票的组合：资金与期限、收益目标、波动与回撤、数据清洗、组合选择和样本外评价。
- 金融政策与融资成本：政策对象、样本构造、变量定义、对照组和因果解释。

学生提交一页研究计划。环境准备放独立页面，以 Agent 检查流程为主、传统分步操作为补充。

## 全书主题

| Part | 章节安排 |
|---|---|
| 研究基础 | 01 研究流程；02 金融数据；03 OLS；04 模型设定；05 Bootstrap；06 蒙特卡洛 |
| 收益与风险 | 07 CAPM；08 投资组合；09 ARMA；10 GARCH与VaR |
| 面板与因果 | 11 静态面板；12 DID；13 IV与GMM；14 动态面板 |
| 机器学习 | 15 Lasso与交叉验证；16 DDML |
| 扩展专题 | 17 离散选择；18 样本选择；19 合成控制；20 RDD |

CAPM 与投资组合分章；ARMA 与 GARCH/VaR 分讲。Lasso 和交叉验证为必讲内容，DDML 单列重点章。动态面板独立写章，由教师决定课堂时间。不安排事件研究法章节。

## 讲义形式

理论与交叉引用使用 `.qmd`，代码和执行结果使用 `.ipynb`。理论与实验并重时拆成同章两部分。Notebook 在课前运行并保存输出，课堂展示及网站阅读不依赖实时取数或现场执行。

当前版本包含首页、课程安排、第一讲、已执行实验、环境说明和作业入口。其余主题随后逐章加入。


## 网站模块与文件名

前置页面依次为 `index.qmd` (前言)、`resources.qmd` (课程资料)、`getting-started.qmd` (课件使用)、`syllabus.qmd` (课程安排)。环境配置 Part 包含 `settings.qmd` 与 `publishing.qmd`，先于正式讲义。`homework.qmd` 为作业总览，放在课程安排下方；各次作业分别使用 `exercises/hw-01.qmd` 等文件。附录 `resources/references.qmd` 保存公共书目与各章书目入口，具体引用在每章末尾维护。

未完成章节不加入公开导航。后续主题文件名依次规划为 `financial-data`、`ols`、`model-specification`、`bootstrap`、`monte-carlo`、`capm`、`portfolio`、`arma`、`garch-var`、`static-panel`、`did`、`iv-gmm`、`dynamic-panel`、`lasso-cv`、`ddml`、`discrete-choice`、`sample-selection`、`synthetic-control`、`rdd`，放入 `lectures/`。实验页使用主题短标题，不占理论章节编号。

学生每学期维护一个 `fineco-homework` 仓库，与教师课件副本平级。`hw-01` 暂不强制 Pages，原则上从 `hw-02` 过渡，具体启用时间由教师通知。
