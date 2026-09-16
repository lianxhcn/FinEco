"""从已完成运行发布允许清单内的汇总；不递归复制受限目录。"""
from pathlib import Path
import json, shutil, importlib.metadata, hashlib
import pandas as pd
from pipeline import data_root, TABLES, MAPPING

root=Path(__file__).resolve().parents[2]
private=data_root()
run=Path((private/'financial-data-v2/latest-run.txt').read_text(encoding='utf-8'))
public=root/'data/financial-data'
out=public/'audit'
out.mkdir(parents=True,exist_ok=True)
allowed=['distribution.csv','missingness_by_year.csv','year_coverage.csv','merge.csv',
         'merge_by_year.csv','sample_flow.csv','ratio_correlations.csv',
         'ratio_common_sample.csv','denominator_checks.csv','unmatched_groups.csv','summary.json','execution.json']
for name in allowed:
    shutil.copyfile(run/'audit'/name,out/name)
schemas=json.loads((run/'audit/schema.json').read_text(encoding='utf-8'))
manifest=json.loads((run/'audit/source_manifest.json').read_text(encoding='utf-8'))
fields=json.loads((run/'audit/field_dictionary.json').read_text(encoding='utf-8'))
summary=json.loads((run/'audit/summary.json').read_text(encoding='utf-8'))
execution=json.loads((run/'audit/execution.json').read_text(encoding='utf-8'))
schema_by={r['table']:r for r in schemas}
(out/'schema.json').write_text(json.dumps(schemas,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# CSMAR 来源清单','',f"执行时间：{execution['executed_at']}。来源为教师授权的 CSMAR 本地导出；原始下载日期 unknown，不能用执行日期冒充下载日期。",'',
       '原始文件仅供中山大学使用，清单不包含数据库记录。CSV 为 UTF-8-SIG，可验证字段文本为 UTF-8-SIG；股东数据两片追加。','']
for m in manifest:
    csvs=[n for n in m['members'] if n.endswith('.csv')]
    prefix=next(k for k in TABLES if csvs[0].startswith(k))
    name=TABLES[prefix][0]
    s=schema_by[name]
    lines += [f'## {name}', '',f"- 原文件：`{m['file']}`。",f"- 文件大小：{m['size_bytes']} bytes。",
              f"- SHA256：`{m['sha256']}`。",f"- 成员：{', '.join('`'+n+'`' for n in m['members'])}。",
              f"- 合并读取行数：{s['rows']}；字段数：{s['columns']}；证券数：{s['company_coverage']}。",
              f"- 观测日期范围：{s.get('date_min','N/A (公司静态表)')} 至 {s.get('date_max','N/A')}。",
              f"- 候选键：`{' + '.join(s['candidate_keys'])}`；重复键行：{s['duplicate_key_rows']}。",'']
manual=next((private/'raw-zip').glob('上市公司基本信息*.pdf'))
lines += ['## 数据库说明书','',f'`{manual.name}`，28 页，本轮已提取并读取有关状态与行业字段。',
          f'SHA256：`{hashlib.sha256(manual.read_bytes()).hexdigest()}`。原说明书留在受限目录，不随本章再分发。','']
(public/'SOURCE_MANIFEST.md').write_text('\n'.join(lines),encoding='utf-8')

lines=['# 字段字典与映射','', '依据：各 ZIP 配套 TXT 和基本信息数据库说明。此处提供字段标签、处理与边界；完整原说明仅保留在受限目录。', '',
       '| 表 | 原字段 | 标准字段 | 含义 |','|---|---|---|---|']
mapping_rows=[]
for f in fields:
    table=f['table']
    spec=next(v for v in TABLES.values() if v[0]==table)
    target='stock_code' if f['source_field']==spec[1] else f['field']
    label=f['label'].replace('|','/')
    lines.append(f"| {table} | `{f['source_field']}` | `{target}` | {label} |")
    mapping_rows.append({'table':table,'source_field':f['source_field'],'standard_field':target,'label':f['label']})
pd.DataFrame(mapping_rows).to_csv(public/'field_mapping.csv',index=False,encoding='utf-8-sig')
lines += ['', '## 日期、单位和派生列','',
    '- `report_date` 从 Accper/EndDate/Reptdt 解析；年度层使用年末日期，不表示公告日期。`fiscal_year` 为该日期年份，市场表来自 Trdynt。',
    '- `firm_id` 来自 ListedCoID。未把证券代码重命名为公司 ID；证券代码变更须另行审计。',
    '- `actual_announcement_date` 来自 Actudt；`predisclosure_date` 来自 Firforecdt。无效或空日期不相互填补。',
    '- 财务金额使用原始数值尺度。TXT 未提供足够的币种/单位证据，金额不声明为元；跨表 ROA/ROE 待确认。',
    '- `market_value_thousand` 在已确认 A 股市场使用人民币千元，`market_value = market_value_thousand * 1000`。',
    '- `annual_stock_return` 为考虑现金红利再投资的年回报率，按源值保留小数，不与未复权价格涨幅混用。',
    '- `top1_pct` 来自股东排名为 1 的 S0301b，单位为百分数；`top1 = top1_pct / 100`。`shares_held` 为该股东股数。',
    '- `top1_ownership_pct` 为股权性质表 LargestHolderRate。治理综合表本次未导出 Top1 字段，因此交叉核验对象为股权性质表。',
    '- `_parent_statement` 后缀表示 Typrep=B；无此后缀的财务金额来自 Typrep=A。归母权益/利润仍属于合并报表内部归属口径。',
    '- `_lag` 按证券代码匹配精确 t−1 年；`_avg` 为 (本年值 + 上年值)/2。公司代码迁移尚未裁定，不能跨代码拼接分母。',
    '- Leverage=负债/资产；ROA=净利润/期末或平均资产；ROE=净利润/期末或平均总权益。归母 ROE 用归母净利润和归母权益匹配。',
    '- 比率均为小数，0.05 表示 5%；零分母置为缺失，负分母保留。`roa_parent_income_*_candidate` 是另列候选，不能视作统一标准。',
    '- `financial_industry` 按本年行业 J 前缀诊断；`industry_standard` 标明 2023 年分类体系切换。行业缺失不前填。',
    '- `st_source`、`pt_source` 仅反映源状态标签，不表示完整年内历史；`soe` 仅映射单一性质码，复合码为缺失。',
    '- `has_*` 记录该来源是否存在对应行；字段本身仍可能缺失。`firm_year_conflict` 与 `listing_date_conflict` 提醒人工核查。',
    '- `eligible_known` 是候选规则：存在 A 股身份和上市日期证据、非已知上市前或退市后。不是对总体完备性和上市日期冲突的背书。','']
(public/'DATA_DICTIONARY.md').write_text('\n'.join(lines),encoding='utf-8')

dist=pd.read_csv(out/'distribution.csv')
def markdown_table(d):
    return '| '+' | '.join(d.columns)+' |\n|'+ '|'.join(['---']*len(d.columns))+'|\n'+ '\n'.join('| '+' | '.join(str(x) for x in row)+' |' for row in d.itertuples(index=False,name=None))
lines=['# Data Audit：本轮真实执行结果','',f"执行时间：{execution['executed_at']}。本报告与保存的 Notebook 对应。",'',
       '**结论：执行完成，候选证券年度表已建立；最终公司年度 master 为 NOT READY。**', '',
       '## 1. 结构与总体','',
       f"研究期候选并集 {summary['candidate_rows']:,} 行；候选上市期间视图 {summary['master_rows']:,} 行，覆盖 {summary['securities']:,} 个证券代码、{summary['firm_ids']:,} 个公司 ID。证券年度键唯一，公司年度有 {summary['firm_year_duplicate_rows']} 条冲突行，涉及 26 组。",'',
       f"未纳入候选上市期间视图的 {summary['unresolved_candidate_rows']:,} 行仍保留在 candidate；其中上市前标识 {summary['pre_listing_rows']:,} 行，缺少 A 股身份证据 {summary['a_share_identity_unconfirmed_rows']} 行，两类可重叠。没有删除金融、ST/PT、缺失值或极端值。",'',
       '## 2. 样本流与合并','',markdown_table(pd.read_csv(out/'sample_flow.csv')),'',
       markdown_table(pd.read_csv(out/'merge.csv')),'',
       '以上 outer merge 以年度来源并集逐步扩展。行数增加可来自 using-only，不等于重复膨胀。按年未匹配见 [merge_by_year.csv](audit/merge_by_year.csv)，群体诊断见 [unmatched_groups.csv](audit/unmatched_groups.csv)。', '',
       '## 3. 缺失与分布','',
       '完整缺失率按年度见 [missingness_by_year.csv](audit/missingness_by_year.csv)；N、mean、sd、min、p1/p25/p50/p75/p99/max 见 [distribution.csv](audit/distribution.csv)。金额单位尚未确认，不将这些金额直接解读为人民币元。','',
       markdown_table(dist.loc[dist.variable.str.startswith(('roa_','roe_','leverage_')),['variable','N','mean','p50','p1','p99']].round(6)),'',
       'ROA/ROE 的共同样本比较见 [ratio_common_sample.csv](audit/ratio_common_sample.csv)。本表为候选证券年度视图描述，包含身份冲突行；不能作为最终公司总体的估计。', '',
       '## 4. 经济与时间审计','',
       f"- 会计恒等式可比较 {summary['accounting_comparable']:,} 行，{summary['accounting_outside_tolerance']} 行超过 max(1 原始单位, |资产|×10⁻⁸)；这是诊断容差，不是排除标准。",
       f"- Leverage > 1 有 {summary['leverage_gt_one']} 行；权益非正有 {summary['equity_nonpositive']} 行。未自动删除。",
       f"- |ROE| > 1 有 {summary['extreme_roe_abs_gt_one']} 行；其中权益绝对值/资产绝对值 < 1% 的有 {summary['near_zero_and_extreme_roe']} 行。近零分母只能解释部分极端值。",
       f"- Top1 两来源可比较 {summary['top1_comparable']:,} 行，差值绝对值超过 0.01 个百分点的有 {summary['top1_difference_gt_001pp']} 行；不存在越出 0–100% 的已观测 Top1。这是相符证据，不是独立原始年报验证。",
       f"- 实际披露日期缺失 {summary['actual_announcement_missing']} 行；两种日期都非空且不相同 {summary['predisclosure_actual_differ']:,} 行；已观测实际披露早于报表日 {summary['actual_before_report_date']} 行。",
       '- 时间检查未覆盖财报更正版本、日内发布时间或交易时点，不能宣称完成全面前视偏误审计。','',
       '## 5. HUMAN REVIEW REQUIRED','',
       '公司与证券映射、上市日期冲突、完整退市总体、财务单位、历史状态、财报修订版本及最终 ROA/ROE 定义，详见 [DATA_GAPS.md](DATA_GAPS.md)。冲突行只在受限 human_review_identity.parquet 保留。', '',
       '## 6. 状态与复跑','',
       '输入 ZIP 均实际读取；标准化和年度候选表已执行。Notebook 从头执行状态由本地交接报告记录。网页渲染不执行代码。公共目录只从固定汇总允许清单复制，不包含原始或派生公司记录。', '',
       f"流水线 SHA256：`{execution['pipeline_sha256']}`。完整版本元数据见 [execution.json](audit/execution.json)。",'']
(public/'AUDIT_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
packages=['pandas','numpy','pyarrow','nbformat','nbclient','ipykernel']
(root/'tools/financial-data/requirements-chapter.txt').write_text('\n'.join(p+'=='+importlib.metadata.version(p) for p in packages)+'\n',encoding='utf-8')
print('公开元数据已生成；复制汇总文件数:',len(allowed)+1)
# 网页章节链接会转换为 HTML，另提供独立的原始 Notebook 下载副本。
# 该副本仅含同一份已审核 Notebook 的汇总与虚构教学小表。
shutil.copyfile(root/'notebooks/financial-data/financial-data.ipynb',
                public/'financial-data-source.ipynb')
