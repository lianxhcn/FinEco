"""构建课堂 Notebook；源码与实际执行分开，输出由 run_notebook.py 产生。"""
from pathlib import Path
import nbformat as nbf

root=Path(__file__).resolve().parents[2]
target=root/'notebooks/financial-data/financial-data.ipynb'
nb=nbf.read(target,as_version=4)
cells=[]
def md(text): cells.append(nbf.v4.new_markdown_cell(text))
def code(text): cells.append(nbf.v4.new_code_cell(text))

md('''# CSMAR 实战：用 Codex 从 ZIP 建立年度数据库 {#sec-csmar-case}

这是数据工作流单元的完整案例。先阅读[流程与获取](../../lectures/financial-data.qmd)、[数据管理](../../lectures/financial-data-management.qmd)和[清洗与审计](../../lectures/financial-data-cleaning.qmd)。本案例重点是把研究规则变成 Agent 可以执行的任务，再用实际输出核验。

学生可以 clone [FinEco 仓库](https://github.com/lianxhcn/FinEco)，按[运行说明](../../data/financial-data/README.md)配置环境与授权数据，在本地运行这份 Notebook。没有 CSMAR 数据也能单独运行末尾的[教学小表](#sec-csmar-mini)。

本实验从授权 ZIP 开始，逐步建立标准化表、候选年度底表、变量比较与审计结果。输出仅包含汇总统计；完整记录留在本地。当前数据中的公司身份、上市日期及历史状态还有待核对，**候选底表不等于可直接用于论文的最终样本**。

依次运行 00–11。教师提供的坚果云下载入口、校验值和解压步骤见 [CSMAR 数据获取](../../data/financial-data/DATA_ACCESS.md)。仓库不附原始数据，请在已有授权范围内使用。''')
md('''## 00. Setup：把数据和代码的位置分开

将环境变量 `FINECO_CSMAR_ROOT` 设置为含 `raw-zip/` 的授权目录，随后重启内核。请阅读 `data/financial-data/README.md`。本实验不会访问实时 API，不需要账号或密钥。

下面从当前工作目录向上寻找课程根目录，保持路径可迁移。依赖已有环境中的 pandas、numpy、pyarrow、nbformat、nbclient、ipykernel。''')
code('''from pathlib import Path
import sys, json, hashlib
from datetime import datetime
import pandas as pd
from IPython.display import display

# 可从仓库根目录或 Notebook 所在目录启动。
PROJECT = next((p for p in [Path.cwd(), *Path.cwd().parents]
                if (p / "tools/financial-data/pipeline.py").is_file()), None)
if PROJECT is None:
    raise FileNotFoundError("请在 FinEco 仓库内部运行 Notebook。")
sys.path.insert(0, str(PROJECT / "tools/financial-data"))
from pipeline import (data_root, source_inventory, standardize, annual_views,
                      build_master, construct_variables, audit_master,
                      require_key, dump_json)
ROOT = data_root()
RUN = ROOT / "financial-data-v2/runs" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
for folder in ["interim", "processed", "audit"]:
    (RUN / folder).mkdir(parents=True, exist_ok=False)
print("输入目录已验证；每轮执行使用独立运行目录。")
print("pandas:", pd.__version__)''')
md('''## 01. Source inventory：先确认拿到的是哪一批数据

文件名相同不保证内容相同。SHA256 是文件内容的指纹；manifest 记录来源 ZIP、成员和大小。学生复跑时应比较指纹，不把不同批次输出直接对比。''')
code('''manifest = source_inventory(ROOT)
dump_json(manifest, RUN / "audit/source_manifest.json")
display(pd.DataFrame(manifest)[["file", "size_bytes", "sha256"]])''')
md('''## 02. Schema audit：先读字段说明，再认识一行记录

`standardize` 读取 ZIP 内 TXT，并对每个 CSV 字段确认说明存在。股东数据的两个分片都必须读取。日期转换失败会计数；原文保留在受限解压目录。标准化层不筛样本。

这里同时执行标准化，以避免为课堂展示重复读入约数百万条记录；下一节单独检查转换规则。''')
code('''tables, schemas, fields = standardize(ROOT, RUN)
dump_json(schemas, RUN / "audit/schema.json")
dump_json(fields, RUN / "audit/field_dictionary.json")
schema_table = pd.DataFrame(schemas)
display(schema_table[["table", "rows", "columns", "company_coverage",
                      "candidate_keys", "duplicate_key_rows"]])''')
md('''读表时比较 `candidate_keys`，而不只看“重复数是 0”。财务表需要证券代码、报表日和报表类型；股东表还需要排名。较细粒度的键唯一，不意味着公司年度键唯一。

## 03. Standardization：字段名变了，经济含义不能变

证券代码保留字符串，避免丢失前导零；财务金额保留原始数值单位。市值字段说明明确使用“千”，年度层才转换为元。股东比例原值是百分数，`top1` 才转为 0–1 比例。

 supplied 财务 TXT 没有明确标出各金额的币种与单位，跨表 ROA/ROE 暂为条件性候选；应补核财务数据库说明或导出设置。原始空白值不会填成零。'''.replace('supplied ', '本批'))
code('''# 展示字段类型和缺失率，不展示任何公司记录。
balance = tables["balance"]
display(pd.DataFrame({"dtype": balance.dtypes.astype(str),
                      "missing_rate": balance.isna().mean()}).loc[
    ["stock_code", "report_date", "Typrep", "total_assets", "total_equity"]])
assert len(balance) == next(s["rows"] for s in schemas if s["table"] == "balance")''')
md('''## 04. Merge planning：年度筛选和删除重复是不同操作

财务数据包含季度末、年末、1 月 1 日和 A/B 报表。年度视图保留 2014–2025 年 12 月 31 日，A/B 继续分别保存。其他行仍在 interim，未被销毁。

下面的样本流描述“原表到年度视图”的行数变化，并非论文研究样本排除。''')
code('''views, flow = annual_views(tables)
display(pd.DataFrame(flow))
# 验证同一日下合并报表与母公司报表是两种口径。
display(views["balance"].groupby("Typrep").agg(
    rows=("stock_code", "size"), securities=("stock_code", "nunique")))''')
md('''### 小型合并实验：同样能运行，行数却不同

以下为明确虚构的教学数据。一家公司一年的资产不能通过只按公司连接而变成两条独立年度观测。先把日度量聚合为研究所需的年度量，才有共同粒度。这里示范年均换手率，不把日收益的算术均值误称年度持有收益率。''')
code('''# 改编自《数据分析与经济决策》课程 data_manage，全部为教学数值。
annual_demo = pd.DataFrame({"firm": ["A", "B"], "year": [2020, 2020], "assets": [100, 200]})
daily_demo = pd.DataFrame({"firm": ["A", "A", "B"], "year": [2020]*3,
                           "turnover": [1., 3., 2.]})
wrong = annual_demo.merge(daily_demo, on=["firm", "year"])
aggregated = daily_demo.groupby(["firm", "year"], as_index=False).turnover.mean()
correct = annual_demo.merge(aggregated, on=["firm", "year"], validate="one_to_one")
print({"原年度行数": len(annual_demo), "直接合并行数": len(wrong), "聚合后行数": len(correct)})
display(correct)
assert len(correct) == 2 and len(wrong) == 3''')
md('''## 05. Firm-year master：先保留覆盖差异，再核查公司身份

流水线使用年度表键的并集，防止选某一张财务表作为母表时静默丢失其他表的公司。A/B 财务列分开，所有合并使用 `validate="one_to_one"`。

合并成功仅证明证券代码—年度键没有膨胀。公司 ID 可能对应不同证券代码，还必须另外审计。存在冲突时不自行选代码、相加或取均值。''')
code('''base, merge_audit, merge_by_year = build_master(views)
display(pd.DataFrame(merge_audit))
require_key(base, ["stock_code", "fiscal_year"], "年度候选底表")
print("公司年度冲突行数 (含 2014 支持层):", int(base.firm_year_conflict.sum()))''')
md('''## 06. Variable construction：每个比率都保留分子和分母

Leverage 使用合并报表的负债/资产。ROA 同时计算净利润/期末资产、净利润/平均资产，以及归母净利润的候选口径；ROE 区分总净利润/总权益和归母净利润/归母权益。负权益不删，零分母返回缺失。

平均资产必须使用相邻年度。缺少 t−1 时不把更早一年当作上一年。2014 数据供 2015 分母使用。以下计算结果仍依赖跨表币种与单位确认。''')
code('''base = construct_variables(base)
ratio_cols = [c for c in base if c.startswith(("roa_", "roe_", "leverage_"))]
print("候选比率：", ratio_cols)
assert not base.duplicated(["stock_code", "fiscal_year"]).any()''')
md('''## 07. Missing / duplicate / outlier：诊断之后才决定

研发费用字段从 2018 年起使用，早期缺失不能自动解读为没有研发。极端 ROE 可能来自接近零的权益，也可能来自分子异常；诊断阈值不是删除规则。源上市状态字段的定义不能支持完整历史 ST/PT 路径，因此标识保留 `_source` 后缀。

下面只显示汇总，不输出公司名称、证券代码或真实单行数据。''')
code('''research = base[base.fiscal_year.between(2015, 2025) & base.eligible_known]
display(research.groupby("fiscal_year").rd_expense.agg(
    N="size", nonmissing="count"))
print("权益绝对值不足资产 1% 的行数:",
      int((research.total_equity.abs() / research.total_assets.abs()).lt(.01).sum()))
print("Leverage 大于 1 的行数:", int(research.leverage_consolidated.gt(1).sum()))''')
md('''## 08. Data Audit：让结果接受反向检查

会计检查使用 max(1 个原始单位, 资产绝对值×10⁻⁸) 作为诊断容差；不符合时保留记录供追查。日期审计检查实际披露是否早于报表日，但不能证明下载的是当时可得版本；财报更正历史仍需单独获取。

报告中的 `master_rows` 是程序候选视图行数，程序文件名里的 master 不代表已经通过公司年度身份审核。''')
code('''summary = audit_master(base, schemas, merge_audit, merge_by_year, flow, RUN)
display(pd.DataFrame([summary]).T.rename(columns={0: "value"}))
display(pd.read_csv(RUN / "audit/ratio_common_sample.csv"))
display(pd.read_csv(RUN / "audit/distribution.csv").round(5))''')
md('''看 `ratio_common_sample` 的 `N_common`：只有使用同一批可用观测，均值差异才主要反映分母定义的变化。全样本描述统计同时混入缺失造成的样本变化。相关系数高也不代表两种定义可互换。

## 09. Agent workflow：先写任务边界，再运行验证

可复制任务：读取标准化资产负债表；按证券代码、日期和报表类型检查键；允许统计和列出本地待核对记录；禁止删除、填补、缩尾或选择报表类型；输出键检查、缺失率及重复组数；发现非唯一键时标记 HUMAN REVIEW REQUIRED。

完整规则见 [DATA_PROTOCOL.md](../../data/financial-data/DATA_PROTOCOL.md)，分阶段提示词见 [PROMPTS.md](../../data/financial-data/agent-project/PROMPTS.md)。下面的 verification cells 是学生核验 Agent 的最小起点，不能代替全部审计。''')
code('''require_key(views["balance"], ["stock_code", "fiscal_year", "Typrep"], "年度财务")
assert all(x["N_after"] == x["matched"] + x["master_only"] + x["using_only"]
           for x in merge_audit)
assert summary["duplicate_stock_year"] == 0
# 不把已知待审事项伪装为通过的断言。
print("HUMAN REVIEW REQUIRED:",
      {"公司年度重复行": summary["firm_year_duplicate_rows"],
       "上市日期冲突行": summary["listing_date_conflicts"],
       "实际披露缺失行": summary["actual_announcement_missing"]})''')
md('''## 10. Export：冻结输入、代码与执行证据

完整 interim、候选底表、待审记录已经写入授权数据根目录下的独立运行目录；它们不随 GitHub 或网页分发。保存脚本哈希和版本后，才能知道本次结果对应哪段代码。

本 Notebook 不自动发布汇总文件；维护脚本只按固定允许清单复制已检查的汇总表到公开目录。''')
code('''import numpy as np
dump_json({"executed_at": datetime.now().isoformat(), "pandas": pd.__version__, "numpy": np.__version__,
           "pipeline_sha256": hashlib.sha256((PROJECT / "tools/financial-data/pipeline.py").read_bytes()).hexdigest()},
          RUN / "audit/execution.json")
(ROOT / "financial-data-v2/latest-run.txt").write_text(str(RUN), encoding="utf-8")
print("候选版本与执行证据已保存；最终公司年度数据尚待人工裁定。")''')
md('''## 11. Exercises：把运行成功转成判断依据

1. 找到一种原表键唯一、公司年度键却不唯一的情况，解释为什么不能 `drop_duplicates`。
2. 使用 `merge_by_year.csv` 和 `unmatched_groups.csv`，比较新上市与其他公司的未匹配率。分母必须使用组内样本数。
3. 解释 ROA 平均资产口径为什么少于期末口径；在共同样本上比较两者。
4. 如果想删除 ST，当前 `_source` 标识是否足够？写出缺少的资料与审计规则。
5. 将真实极端 ROE 的诊断改写成一个全新教学数值例子，明确标记教学示例，不公开原始行。

练习完成后交付修改过的 Task Rules、汇总审计和解释；不上传 CSMAR 数据。''')
code('''# 练习起点：先比较未匹配率，再讨论原因；本单元格只读汇总表。
groups = pd.read_csv(RUN / "audit/unmatched_groups.csv")
groups["unmatched_rate"] = groups["unmatched"] / groups["N"]
display(groups[groups["group"].eq("newly_listed")].round(4))''')
# 为跨章引用提供稳定 ID；编号改变也不依赖自动生成的中文锚点。
import re
prompt_text=(root/'data/financial-data/agent-project/PROMPTS.md').read_text(encoding='utf-8')
prompt_parts={m.group(1):m.group(2).strip() for m in re.finditer(
    r"^## (P[0-9]+)[^\n]*\n(.*?)(?=^## |\Z)",prompt_text,re.M|re.S)}
stage_prompt={'00':'P00','01':'P01','03':'P02','05':'P03','06':'P04','08':'P05','09':'P06','10':'P07'}
for cell in cells:
    if cell.cell_type!='markdown':
        continue
    match=re.search(r'^## (\d{2})\. [^\n]+',cell.source,re.M)
    if match:
        stage=match.group(1)
        cell.source=cell.source.replace(match.group(0),match.group(0)+' {#sec-csmar-'+stage+' .unnumbered}',1)
        if stage in stage_prompt:
            cell.source+='\n\n### 本阶段给 Codex 的任务\n\n以下为教学任务模板。先核对路径和本项目规则，再复制使用；后续代码和输出展示本案例的实现。\n\n'+prompt_parts[stage_prompt[stage]]

# 把整套规则放在执行之前，避免将 Agent 边界作为最后才补的说明。
rules=(root/'data/financial-data/agent-project/AGENTS.example.md').read_text(encoding='utf-8')
protocol=(root/'data/financial-data/DATA_PROTOCOL.md').read_text(encoding='utf-8')
plan=(root/'data/financial-data/agent-project/PROJECT_PLAN.md').read_text(encoding='utf-8')
rules_intro="""## 开始执行前：建立规则文件 {#sec-csmar-rules}

本案例从一组真实授权 ZIP 出发。给 Agent 一句清洗数据还不足以开始，需要先明确它能读写哪里、哪些口径已有依据、遇到什么情况必须报告。

课程仓库现有根规则继续有效。下面模板供学生自己的独立项目使用，不能覆盖教师仓库规则。将 AGENTS.example.md 在学生项目另存为 AGENTS.md，将 DECISIONS.template.md 另存为 DECISIONS.md，再核对项目路径。项目计划说明阶段，数据协议说明含义与允许动作，提示词只安排本次任务。

| 文档 | 下载与用途 |
|---|---|
| Agent 工作规则 | [AGENTS.example.md](../../data/financial-data/agent-project/AGENTS.example.md)，规定工作边界 |
| 数据协议 | [DATA_PROTOCOL.md](../../data/financial-data/DATA_PROTOCOL.md)，定义四层规则 |
| 项目阶段 | [PROJECT_PLAN.md](../../data/financial-data/agent-project/PROJECT_PLAN.md)，列交付和验收 |
| 全套任务提示词 | [PROMPTS.md](../../data/financial-data/agent-project/PROMPTS.md)，P00–P07 |
| 人工决策 | [DECISIONS.template.md](../../data/financial-data/agent-project/DECISIONS.template.md)，待决与批准分开 |

这些提示词是依据已执行工作编写的教学模板，后面的程序是本案例实际实现，不能据此声称复制同一句提示词必然生成完全相同代码。

### 工作规则模板全文

```markdown
"""+rules+"""
```

### 项目计划

"""+re.sub(r'^# .*\n','',plan,count=1)+"""

### 本案例的数据协议

下面给出完整协议，课堂可按需讲授，学生不用跳到另一份讲义寻找关键边界。

"""+re.sub(r'^(#{1,3}) ',lambda m:'#'*(len(m.group(1))+2)+' ',protocol,flags=re.M)
cells.insert(1,nbf.v4.new_markdown_cell(rules_intro))

# 将原章批次说明迁入完整案例，并调整相对链接。
case=(root/'tools/financial-data/case-background.md').read_text(encoding='utf-8')
case=case.replace('../data/','../../data/').replace('../notebooks/financial-data/financial-data.ipynb','financial-data.ipynb')
cells.insert(2,nbf.v4.new_markdown_cell(case))

# 第 04 节增加与理论篇完全对应的 outer merge 检查。
where=next(i for i,c in enumerate(cells) if c.cell_type=='code' and 'views, flow = annual_views' in c.source)
cells.insert(where+1,nbf.v4.new_code_cell('''# 与数据管理讲义对应：只连接年度 A 口径，B 仍保留在 views。
left = views["balance"].query("Typrep == 'A'")
right = views["income"].query("Typrep == 'A'")
keys = ["stock_code", "fiscal_year"]
require_key(left, keys, "资产负债表 A")
require_key(right, keys, "利润表 A")
merged = left.merge(right, on=keys, how="outer", validate="one_to_one",
                    indicator=True, suffixes=("_balance", "_income"))
display(merged["_merge"].value_counts().rename("N").to_frame())
assert not merged.duplicated(keys).any()'''))
md("""## 教学小表：不依赖 CSMAR 的独立实验 {#sec-csmar-mini}

本节代码可以独立运行，数值全部为虚构教学例子。依次验证读取类型、错误/正确合并、追加、宽长往返、Parquet 类型保存、SQL/pandas 对照，以及缺失填零与比率手算。它对应前三章的小例子，不代表真实公司。

读取例子重点看证券代码的前导零；合并表比较 2→3 与 2→2；SQL 结果与 pandas 逐项相等；研发率两种均值显示填零改变了假设。每项均有可检查的断言。
""")
example=(root/'tools/financial-data/teaching_examples.py').read_text(encoding='utf-8')
example=example[:example.index("if __name__ == '__main__':")]+"\nrun_examples()\n"
code(example)
md("""## 如何阅读本轮结果与继续返修 {#sec-csmar-review}

第 08 节的 summary 表是验收入口。证券年度键唯一与公司年度键唯一分别检查：本批研究视图为 47,019 行，公司年度存在 26 组重复、52 行，涉及 6 个公司 ID。不能任意删除一条让唯一性通过。

上市日期冲突为 409 行，实际公告缺失为 314 行，会计差异超出容差为 24 行。它们属于不同问题：日期定义要查资料，会计差异要核原表，身份要补映射历史。源字段的最新上市状态不能自动解释为历年 ST/PT。

ratio_common_sample 表对同一批 44,383 行比较 ROA。期末与平均资产口径均值约 1.74% 与 2.59%，相关系数约 0.645。这是暂定证券年度视图的条件性比较，单位和身份仍未冻结。Top1 的 46,664 个可比记录没有超过 0.01 个百分点的差异；相符不等于独立年报验证。

返修时使用 P06：先追到最早出错步骤，再修改有证据的实现问题；缺少资料的事项进入 DECISIONS，不让 Agent 编造选择。P07 保存候选证据，并分别声明执行、研究数据、网页和发布状态。

学生最终提交规则、使用过的提示词、可执行代码、汇总审计和决策说明，不提交受限公司记录。完整未决项见 [DATA_GAPS](../../data/financial-data/DATA_GAPS.md)，本次汇总见 [AUDIT_REPORT](../../data/financial-data/AUDIT_REPORT.md)。
""")
nb.cells=cells
nb.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
             'language_info':{'name':'python'},'title':'CSMAR 实战：用 Codex 从 ZIP 建立年度数据库'}
nbf.validate(nb)
nbf.write(nb,target)
print('Notebook cells:',len(cells))
