# 金融数据章 Data Agent Protocol

版本：v2 本地整合稿。retrieved_date: 2026-09-16。教师依据：本次任务书及当前对话确认。执行实现：`tools/financial-data/pipeline.py`；课堂入口：`notebooks/financial-data/financial-data.ipynb`。

## 1. Global Rules

1. 不修改、覆盖或重命名原始 ZIP；解压文件按数据集隔离，已有内容必须与原 ZIP 一致。
2. 不静默删除观测。标准化保留全部行，年度视图筛选必须记录前后行数和理由，未纳入行仍在支持层或候选层。
3. 不按变量代码猜定义。先读本批 TXT、数据库说明，再形成字段映射。
4. 单位改变须有字典依据，保留原值及转换式。财务金额单位未证实时不声明为人民币元。
5. 不自动填补缺失，不自动缩尾，不自行选择论文研究样本。
6. 合并前验证两侧粒度、键完整性及唯一性；不用未经说明的 many-to-many。
7. A/B 报表分开保存；指标命名标明口径。不能把归母净利润与全部权益的混合口径称为唯一 ROE。
8. 相邻年度滞后按明确的年度键匹配，不能跨断档顺序移位。
9. 程序运行成功只通过执行检查；经济逻辑、身份映射和时间信息另行审核。
10. 无法裁定的事项标为 HUMAN REVIEW REQUIRED，保留证据，不编造确认结果。
11. 记录级数据只写受限目录；公开输出实行文件允许清单，不展示真实公司行。
12. 冻结输入指纹、代码指纹、环境版本与执行时间；更新数据后重新运行审计。

## 2. Project Rules

| 项目 | 规则与当前实现 |
|---|---|
| Population | 目标为 2015–2025 年间曾上市的 A 股公司；当前下载是否覆盖完整历史总体尚待核验 |
| Raw period | 2014–2025 为年度视图；原文件还含 2026 季报及 1 月 1 日记录，标准化层完整保存 |
| Unit | 目标 firm-year；当前技术键 stock_code + fiscal_year，另检验 firm_id + fiscal_year |
| A 股身份 | TRD_Year 的市场编码 1、4、16、32、64 提供已观测身份；缺少证据的代码保留在 candidate |
| Listing | 年度表的首次上市日期为候选口径，与 CG_Co 的上市日期逐项比较；冲突标识不能视为已裁定 |
| Master | 年度来源键先 outer 合并；候选视图再限制研究年、可确认 A 股身份及已知上市期间；完整并集保留 |
| Financial industry | 根据年度行业 J 前缀标识，不删除；行业标准 2023 年发生变化 |
| ST/PT | 保留源状态及标识，不删除；源定义为已出年报最新状态，完整历史状态尚未核验 |
| Missing / winsor | 不填补，不缩尾；零分母比率缺失，负分母原样保留并诊断 |
| Statement type | A 合并报表与 B 母公司报表分别并入；主案例比较合并报表口径，母公司列保留 |
| Announcement | 使用 Actudt；Firforecdt 只作预约披露日期，不替代缺失 Actudt |
| Export | 环境变量 FINECO_CSMAR_ROOT；记录级输出进入根目录下 financial-data-v2/runs/ |
| Public status | Notebook 汇总输出可审核；最终公司年度 master 尚未验收，不宣称可直接做论文 |

这里的上市期间判定是可复现候选规则。上市日期冲突、退市覆盖不足及证券代码迁移均会影响最终总体，不能被候选视图的程序名掩盖。

## 3. Task Rules：可复制给 Agent 的五个任务

### 3.1 检查资产负债表的键

本任务解决“一行究竟代表什么”。

- Input：原始 FS_Combas CSV、同包 TXT。
- Goal：验证 Stkcd + Accper + Typrep，比较 Stkcd + 年度的重复情况。
- Allowed actions：读取、统计、保存受限重复组，形成汇总报告。
- Forbidden actions：删除重复、取第一条、选择 A/B、改变日期。
- Required checks：键缺失、重复、日期后缀、A/B 频数、原始行数。
- Expected outputs：schema.json、候选键结论、报告期分布。
- Human review conditions：字段无定义、完整键不唯一或日期无法解释。

### 3.2 标准化资产负债表

本任务解决字段类型和名称的一致性。

- Input：通过来源检查的 CSV 和字段映射。
- Goal：生成可复用 Parquet，保留每条记录。
- Allowed actions：改名、转换已验证类型、解析日期、记录解析失败。
- Forbidden actions：样本筛选、缺失填补、单位猜测、缩尾。
- Required checks：行数相同、六位证券代码不丢前导零、原始文件哈希不变。
- Expected outputs：interim/balance.parquet、字段类型与缺失率表。
- Human review conditions：非数字金额、无效日期、单位冲突或原始文件改变。

### 3.3 合并年末财务报表

本任务解决多表覆盖不一致及口径混入。

- Input：年度视图 balance、income、cashflow。
- Goal：A/B 分列合并，保留两侧未匹配记录。
- Allowed actions：按已确认年末规则取视图、验证键、outer merge、添加来源标记。
- Forbidden actions：inner merge 丢行、按公司名匹配、将 B 填进缺失 A。
- Required checks：每侧键唯一；N_after = matched + master_only + using_only；年度和群体未匹配分布。
- Expected outputs：候选底表、merge.csv、merge_by_year.csv。
- Human review conditions：键不唯一、样本异常膨胀、异常群体集中。

### 3.4 构造 Leverage 并比较盈利能力口径

本任务解决比率可以计算但定义不透明的问题。

- Input：保留分子分母及 A/B 区分的年度候选表。
- Goal：Leverage；ROA、ROE 期末/平均口径和归母口径候选。
- Allowed actions：按公式计算，零分母返回缺失，保留负权益，精确匹配 t−1。
- Forbidden actions：删除 Leverage > 1、替换极端 ROE、宣布一个口径为唯一正确。
- Required checks：币种/单位、相邻年度、零与近零分母、缺失率、共同样本比较、反算。
- Expected outputs：分子分母、distribution.csv、ratio_common_sample.csv、ratio_correlations.csv。
- Human review conditions：跨表单位不明、公司身份冲突、拟采用某一口径进入正式研究。

### 3.5 生成 Data Audit

本任务解决“怎样核实 Agent 没有把错误藏在处理过程里”。

- Input：冻结的原始指纹、代码、候选表与各步日志。
- Goal：形成可交给另一位研究者检查的证据包。
- Allowed actions：只读诊断、汇总、在受限目录保存异常行。
- Forbidden actions：边审计边自动修复、向公共 Notebook 输出真实公司记录。
- Required checks：结构、样本流、合并、缺失、分布、会计、时间、身份映射及公开范围。
- Expected outputs：AUDIT_REPORT.md、机器可读汇总、HUMAN REVIEW REQUIRED 清单。
- Human review conditions：任一关键数据定义未确认、审计失败、输入版本发生变化。

## 4. Audit Rules 与冻结条件

每次交付必须列输入、原始/输出行数、两个层级的主键检查、删除或未纳入理由、缺失率、合并分类、关键分布、会计与时间检查及人工待办。

执行验证通过不自动触发最终冻结：当前允许冻结“本次候选结果与审计证据”，不允许标记“完整 A 股公司年度研究库已验收”。人工裁定后应另起运行版本，不覆盖本轮证据。
