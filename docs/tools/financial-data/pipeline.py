"""CSMAR 教学流水线：原始文件只读，记录级输出只写受限数据根目录。

运行：python tools/financial-data/pipeline.py
先设置 FINECO_CSMAR_ROOT，使其指向含 raw-zip/ 的目录。
"""
from __future__ import annotations
import hashlib
import io
import json
import os
import re
import zipfile
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd

TABLES = {
    'STK_LISTEDCOINFOANL': ('annual_info', 'Symbol', 'EndDate'),
    'CG_Co': ('company', 'Stkcd', None),
    'FS_Combas': ('balance', 'Stkcd', 'Accper'),
    'FS_Comins': ('income', 'Stkcd', 'Accper'),
    'FS_Comscfd': ('cashflow', 'Stkcd', 'Accper'),
    'CG_Sharehold': ('shareholders', 'Stkcd', 'Reptdt'),
    'CG_Ybasic': ('governance', 'Stkcd', 'Reptdt'),
    'EN_EquityNatureAll': ('ownership', 'Symbol', 'EndDate'),
    'TRD_Year': ('market', 'Stkcd', 'Trdynt'),
    'IAR_Forecdt': ('disclosure', 'Stkcd', 'Accper'),
}
MAPPING = {
    'A001000000':'total_assets','A002000000':'total_liabilities',
    'A003000000':'total_equity','A003100000':'parent_equity',
    'A001100000':'current_assets','A002100000':'current_liabilities',
    'A001101000':'cash','A001123000':'inventory','A001212000':'fixed_assets',
    'B001101000':'revenue','B001300000':'operating_profit',
    'B001000000':'total_profit','B002000000':'net_income',
    'B002000101':'parent_net_income','B001216000':'rd_expense',
    'C001000000':'operating_cash_flow','C002000000':'investing_cash_flow',
    'C003000000':'financing_cash_flow','S0501b':'holder_rank',
    'S0301b':'top_holder_pct','S0201b':'shares_held',
    'ListedCoID':'firm_id','SecurityID':'security_id',
    'IndustryCode':'industry_code','IndustryName':'industry_name',
    'LISTINGDATE':'listing_date','ListedDate':'listing_date_company',
    'DelistedDate':'delisting_date','LISTINGSTATE':'listing_state_source',
    'Firforecdt':'predisclosure_date','Actudt':'actual_announcement_date',
    'EquityNature':'ownership_nature','EquityNatureID':'ownership_code',
    'ActualControllerName':'ultimate_controller','LargestHolderRate':'top1_ownership_pct',
    'Yretwd':'annual_stock_return','Ysmvttl':'market_value_thousand',
    'Yarkettype':'market_type','Y0601b':'employees','Y1001b':'chair_ceo_code',
}
NUMERIC = {v for k,v in MAPPING.items() if k.startswith(('A00','B00','C00'))} | {
    'holder_rank','top_holder_pct','shares_held','top1_ownership_pct',
    'annual_stock_return','market_value_thousand','market_type','employees','chair_ceo_code'}
KEY = ['stock_code','fiscal_year']

def dump_json(obj, path):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

def data_root():
    value = os.environ.get('FINECO_CSMAR_ROOT')
    if not value:
        raise RuntimeError('请设置 FINECO_CSMAR_ROOT，指向教师授权数据目录 (内含 raw-zip/)。')
    p = Path(value).expanduser().resolve()
    if not (p/'raw-zip').is_dir():
        raise FileNotFoundError('FINECO_CSMAR_ROOT 下未找到 raw-zip/。请按学生数据说明配置。')
    # 项目公共 data 目录不能被误设为记录级导出位置。
    project = Path(__file__).resolve().parents[2]
    if p.is_relative_to(project) and not p.is_relative_to(project/'005-data-temp'):
        raise ValueError('项目内的 CSMAR 根目录必须位于受限的 005-data-temp/。')
    return p

def require_key(d, keys, label):
    """键缺失或不唯一就中止，不自动删除或选第一条。"""
    if d[keys].isna().any().any() or d.duplicated(keys).any():
        raise ValueError(f'HUMAN REVIEW REQUIRED: {label} 主键缺失或不唯一: {keys}')

def source_inventory(root):
    manifest = []
    for p in sorted((root/'raw-zip').glob('*.zip')):
        with zipfile.ZipFile(p) as z:
            names = z.namelist()
            manifest.append({'file':p.name,'size_bytes':p.stat().st_size,
                'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'members':names})
    if len(manifest) != 10:
        raise ValueError('预期 10 个 ZIP；输入清单改变，请先重新审计。')
    return manifest

def standardize(root, run):
    """逐表保留全部行，转换可验证类型，并保存未经改动的解压文件。"""
    tables, schemas, fields = {}, [], []
    for p in sorted((root/'raw-zip').glob('*.zip')):
        with zipfile.ZipFile(p) as z:
            csvs = [n for n in z.namelist() if n.endswith('.csv')]
            prefix = next(k for k in TABLES if csvs[0].startswith(k))
            name, code, date = TABLES[prefix]
            dictionary = next(n for n in z.namelist() if n.endswith('.txt'))
            desc = z.read(dictionary).decode('utf-8-sig')
            parts = []
            for member in z.namelist():
                # 防止 ZIP 路径穿越；按数据集分目录保留同名版权文件。
                dest = (root/'financial-data-v2/raw-extracted'/name/member).resolve()
                base = (root/'financial-data-v2/raw-extracted'/name).resolve()
                if not dest.is_relative_to(base):
                    raise ValueError('ZIP 成员路径越界')
                content = z.read(member)
                if dest.exists():
                    if hashlib.sha256(dest.read_bytes()).digest() != hashlib.sha256(content).digest():
                        raise ValueError('已有解压文件与原始 ZIP 不一致，禁止覆盖。')
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(content)
                if member in csvs:
                    part = pd.read_csv(io.BytesIO(content), dtype='string', encoding='utf-8-sig')
                    part['_source_member'] = member
                    parts.append(part)
            d = pd.concat(parts, ignore_index=True)
            original_cols = [c for c in d if not c.startswith('_')]
            defs = {}
            for line in desc.splitlines():
                match = re.match(r'(\w+) \[(.*?)\] - (.*)', line)
                if match:
                    defs[match[1]] = (match[2], match[3])
            for c in original_cols:
                if c not in defs:
                    raise ValueError(f'字段说明缺失: {name}/{c}')
                fields.append({'table':name,'source_field':c,'field':MAPPING.get(c,c),
                               'label':defs[c][0],'definition':defs[c][1]})
            rawkey = [code]+([date] if date else [])+(['Typrep'] if 'Typrep' in d else [])
            if name == 'shareholders':
                rawkey += ['S0501b']
            schema = {'table':name,'rows':len(d),'columns':len(original_cols),
                'company_coverage':int(d[code].nunique()), 'source_columns':original_cols,
                'candidate_keys':rawkey,'duplicate_key_rows':int(d.duplicated(rawkey,keep=False).sum()),
                'exact_duplicate_rows':int(d.duplicated(original_cols).sum()),
                'missingness':d[original_cols].isna().mean().to_dict()}
            if date:
                schema['date_min'],schema['date_max']=str(d[date].min()),str(d[date].max())
            if 'Typrep' in d:
                schema['statement_types']=d.Typrep.value_counts().to_dict()
            d = d.rename(columns={**MAPPING, code:'stock_code'})
            if not d.stock_code.str.fullmatch(r'\d{6}').all():
                raise ValueError('证券代码格式发生变化；请人工核验，不自动补零。')
            if date == 'Trdynt':
                d['fiscal_year']=pd.to_numeric(d[date],errors='raise').astype('int64')
            elif date:
                d['report_date']=pd.to_datetime(d[date],errors='coerce')
                schema['invalid_report_dates']=int((d[date].notna() & d.report_date.isna()).sum())
                d['fiscal_year']=d.report_date.dt.year.astype('Int64')
            for c in ['listing_date','listing_date_company','delisting_date','predisclosure_date','actual_announcement_date']:
                if c in d:
                    raw=d[c].copy()
                    d[c]=pd.to_datetime(raw,errors='coerce')
                    schema[c+'_invalid']=int((raw.notna() & d[c].isna()).sum())
                    # 原字段的文本在解压文件中保留；失效日期不伪造。
            for c in NUMERIC.intersection(d.columns):
                d[c]=pd.to_numeric(d[c],errors='raise').astype('float64')
            schema['column_types']={c:str(t) for c,t in d.dtypes.items()}
            schemas.append(schema)
            d.to_parquet(run/'interim'/f'{name}.parquet',index=False)
            tables[name]=d
    return tables, schemas, fields

def annual_views(tables):
    views, flow = {}, []
    for name,d in tables.items():
        if name == 'company':
            require_key(d,['stock_code'],name)
            views[name]=d
            continue
        keep=d.fiscal_year.between(2014,2025)
        if 'report_date' in d:
            keep &= d.report_date.dt.month.eq(12) & d.report_date.dt.day.eq(31)
        x=d.loc[keep.fillna(False)].copy()
        flow.append({'step':name+':年度视图','N_before':len(d),'Removed':len(d)-len(x),
                     'N_after':len(x),'Reason':'保留 2014–2025 年末；其余行仍保存在 interim'})
        keys=KEY+(['Typrep'] if 'Typrep' in x else [])+(['holder_rank'] if name=='shareholders' else [])
        require_key(x,keys,name)
        views[name]=x
    return views,flow

def merge_checked(master, using, label, audit, breakdown):
    require_key(master,KEY,'master before '+label)
    require_key(using,KEY,label)
    joined=master.merge(using,on=KEY,how='outer',validate='one_to_one',indicator=True)
    counts=joined['_merge'].value_counts()
    audit.append({'table':label,'N_before':len(master),'N_after':len(joined),
        'matched':int(counts.get('both',0)),'master_only':int(counts.get('left_only',0)),
        'using_only':int(counts.get('right_only',0)),'duplicates':0})
    groups=joined.groupby(['fiscal_year','_merge'],observed=True).size()
    breakdown.extend({'table':label,'fiscal_year':int(y),'match':str(m),'N':int(n)} for (y,m),n in groups.items())
    joined['has_'+label]=joined['_merge'].ne('left_only')
    return joined.drop(columns='_merge')

def build_master(views):
    """使用各年度表键的并集，避免把某张财务表的覆盖范围当总体。"""
    audit,breakdown=[],[]
    info=views['annual_info']
    base=info[KEY+['firm_id','security_id','ShortName','industry_code','industry_name','listing_date','listing_state_source']].copy()
    base=base.rename(columns={'ShortName':'security_short_name'})
    base['has_annual_info']=True
    for name in ['balance','income','cashflow']:
        source=views[name]
        cols=[c for c in source if c in NUMERIC and c not in KEY]
        # A/B 分别并入，保留两个口径；主案例指标名明确标注 consolidated。
        for typ in ['A','B']:
            d=source.loc[source.Typrep.eq(typ),KEY+cols].copy()
            if typ=='B':
                d=d.rename(columns={c:c+'_parent_statement' for c in cols})
            base=merge_checked(base,d,name+'_'+typ,audit,breakdown)
    selections={
        'market':['annual_stock_return','market_value_thousand','market_type'],
        'ownership':['ownership_nature','ownership_code','ultimate_controller','top1_ownership_pct'],
        'governance':['employees','chair_ceo_code'],
        'disclosure':['predisclosure_date','actual_announcement_date'],
    }
    for name,cols in selections.items():
        base=merge_checked(base,views[name][KEY+cols],name,audit,breakdown)
    top=views['shareholders'].loc[views['shareholders'].holder_rank.eq(1),KEY+['top_holder_pct','shares_held']]
    base=merge_checked(base,top.rename(columns={'top_holder_pct':'top1_pct'}),'top1',audit,breakdown)
    company=views['company'][['stock_code','listing_date_company','delisting_date']]
    base=base.merge(company,on='stock_code',how='left',validate='many_to_one')
    # 日期映射只在同一证券的已知值唯一时使用，不倒填行业和历史状态。
    cross=info[['stock_code','firm_id','listing_date']].drop_duplicates()
    conflicts=cross.groupby('stock_code').size().gt(1)
    if conflicts.any():
        raise ValueError('公司 ID/上市日期存在多版本，请先确认映射。')
    base=base.merge(cross.rename(columns={'firm_id':'mapped_firm_id','listing_date':'mapped_listing_date'}),
                    on='stock_code',how='left',validate='many_to_one')
    base['listing_date_resolved']=base.listing_date.combine_first(base.mapped_listing_date).combine_first(base.listing_date_company)
    base['firm_id']=base.firm_id.combine_first(base.mapped_firm_id)
    base['listing_date_conflict']=(base.mapped_listing_date.notna() & base.listing_date_company.notna()
                                  & base.mapped_listing_date.ne(base.listing_date_company))
    base['firm_year_conflict']=base.firm_id.notna() & base.duplicated(['firm_id','fiscal_year'],keep=False)
    a_codes=set(views['market'].loc[views['market'].market_type.isin([1,4,16,32,64]),'stock_code'])
    base['a_share_ever_confirmed']=base.stock_code.isin(a_codes)
    end=pd.to_datetime(base.fiscal_year.astype(str)+'-12-31')
    start=pd.to_datetime(base.fiscal_year.astype(str)+'-01-01')
    base['pre_listing']=base.listing_date_resolved.gt(end)
    base['post_delisting']=base.delisting_date.lt(start)
    base['eligible_known']=base.a_share_ever_confirmed & base.listing_date_resolved.notna() & ~base.pre_listing & ~base.post_delisting
    # 空白退市日期不等同于已证实未退市，eligible_known 是候选状态。
    base['financial_industry']=base.industry_code.str.startswith('J').astype('boolean')
    base['st_source']=base.listing_state_source.isin(['ST','*ST']).astype('boolean').mask(base.listing_state_source.isna())
    base['pt_source']=base.listing_state_source.eq('PT').astype('boolean').mask(base.listing_state_source.isna())
    base['soe']=base.ownership_code.map({'1':True,'2':False,'3':False,'4':False}).astype('boolean')
    base['ownership_mixed_code']=base.ownership_code.str.contains(',',regex=False).fillna(False)
    base['top1_difference_pp']=base.top1_pct-base.top1_ownership_pct
    base['top1']=base.top1_pct/100
    base['market_value']=base.market_value_thousand*1000
    base['report_date']=end
    base['industry_standard']=np.where(base.fiscal_year.ge(2023),'中国上市公司协会','证监会2012版')
    base.loc[base.industry_code.isna(),'industry_standard']=pd.NA
    # 市场类型为当年已观测分类；无当年市场记录不前填交易所/板块。
    base['exchange']=base.market_type.map({1:'SSE',4:'SZSE',16:'SZSE',32:'SSE',64:'BSE'})
    base['board']=base.market_type.map({1:'SSE main',4:'SZSE main',16:'ChiNext',32:'STAR',64:'BSE'})
    require_key(base,KEY,'candidate master')
    return base.sort_values(KEY).reset_index(drop=True),audit,breakdown

def construct_variables(base):
    """精确按 t-1 合并分母，避免把不相邻年度 shift 当上一年。"""
    stocks=['total_assets','total_equity','parent_equity']
    lag=base[KEY+stocks].copy()
    lag['fiscal_year']+=1
    lag=lag.rename(columns={c:c+'_lag' for c in stocks})
    base=base.merge(lag,on=KEY,how='left',validate='one_to_one')
    for c in stocks:
        base[c+'_avg']=(base[c]+base[c+'_lag'])/2
    def ratio(numerator,denominator,name):
        base[name]=base[numerator]/base[denominator].where(base[denominator].ne(0))
    ratio('total_liabilities','total_assets','leverage_consolidated')
    for suffix,den in [('eop','total_assets'),('avg','total_assets_avg')]:
        ratio('net_income',den,'roa_'+suffix+'_consolidated')
        ratio('parent_net_income',den,'roa_parent_income_'+suffix+'_candidate')
    for suffix,den in [('eop','total_equity'),('avg','total_equity_avg')]:
        ratio('net_income',den,'roe_'+suffix+'_consolidated')
    for suffix,den in [('eop','parent_equity'),('avg','parent_equity_avg')]:
        ratio('parent_net_income',den,'roe_parent_'+suffix+'_consolidated')
    return base

def audit_master(base,schemas,merge,breakdown,flow,run):
    # 保留候选并集和 2014 分母支持层；单独提供可证实范围内的研究期视图。
    candidate=base[base.fiscal_year.between(2015,2025)].copy()
    master=candidate[candidate.eligible_known].copy()
    flow.append({'step':'2015–2025 候选年度并集','N_before':len(base),'Removed':len(base)-len(candidate),
                 'N_after':len(candidate),'Reason':'2014 留在支持层'})
    flow.append({'step':'候选 A 股上市期间视图','N_before':len(candidate),'Removed':len(candidate)-len(master),
                 'N_after':len(master),'Reason':'A 股身份或上市日期未证实、上市前/已知退市后；未纳入行保留在 candidate'})
    for name,d in [('master_with_support',base),('candidate_2015_2025',candidate),('master_2015_2025',master)]:
        d.to_parquet(run/'processed'/f'{name}.parquet',index=False)
    # 不擅自解决公司身份冲突；专门导出待核对记录，仅留受限本地。
    master.loc[master.firm_year_conflict | master.listing_date_conflict].to_parquet(
        run/'processed/human_review_identity.parquet',index=False)
    ratios=[c for c in master if c.startswith(('roa_','roe_','leverage_'))]
    # 核心原始量和全部候选比率均进入缺失与分布审计。
    cols=ratios+sorted((NUMERIC.intersection(master.columns)-{'holder_rank','top_holder_pct'}))+['top1']
    dist=master[cols].describe(percentiles=[.01,.25,.5,.75,.99]).T.reset_index(names='variable')
    dist=dist.rename(columns={'count':'N','std':'sd','1%':'p1','25%':'p25','50%':'p50','75%':'p75','99%':'p99'})
    dist.to_csv(run/'audit/distribution.csv',index=False,encoding='utf-8-sig')
    missing=master.groupby('fiscal_year')[cols+['actual_announcement_date','firm_id','industry_code']].agg(lambda s:s.isna().mean())
    missing.to_csv(run/'audit/missingness_by_year.csv',encoding='utf-8-sig')
    master.groupby('fiscal_year').agg(N=('stock_code','size'),firms=('stock_code','nunique')).to_csv(run/'audit/year_coverage.csv',encoding='utf-8-sig')
    pd.DataFrame(merge).to_csv(run/'audit/merge.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(breakdown).to_csv(run/'audit/merge_by_year.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(flow).to_csv(run/'audit/sample_flow.csv',index=False,encoding='utf-8-sig')
    master[ratios].corr().to_csv(run/'audit/ratio_correlations.csv',encoding='utf-8-sig')
    # 统一样本比较分母定义，避免把可用样本改变误当公式改变。
    common=[]
    for family in ['roa','roe']:
        left,right=family+'_eop_consolidated',family+'_avg_consolidated'
        both=master[[left,right]].dropna()
        common.append({'family':family,'N_common':len(both),'mean_eop':both[left].mean(),
                       'mean_avg':both[right].mean(),'median_eop':both[left].median(),
                       'median_avg':both[right].median(),'correlation':both[left].corr(both[right])})
    pd.DataFrame(common).to_csv(run/'audit/ratio_common_sample.csv',index=False,encoding='utf-8-sig')
    denominators=['total_assets','total_assets_avg','total_equity','total_equity_avg',
                  'parent_equity','parent_equity_avg']
    pd.DataFrame([{'variable':c,'N':len(master),'missing':int(master[c].isna().sum()),
                   'zero':int(master[c].eq(0).sum()),'negative':int(master[c].lt(0).sum())}
                  for c in denominators]).to_csv(run/'audit/denominator_checks.csv',index=False,encoding='utf-8-sig')
    # 非匹配检查以主库是否有该来源记录标记为准，按可观察群体分组。
    group=master.assign(newly_listed=master.listing_date_resolved.dt.year.eq(master.fiscal_year),
                        delisted_in_year=master.delisting_date.dt.year.eq(master.fiscal_year))
    group_audit=[]
    for col in ['newly_listed','delisted_in_year','financial_industry','st_source']:
        for val,g in group.groupby(col,dropna=False):
            for source in ['market','disclosure','top1','balance_A','income_A','cashflow_A']:
                group_audit.append({'group':col,'value':str(val),'source':source,'N':len(g),
                    'unmatched':int((~g['has_'+source].astype('boolean').fillna(False)).sum())})
    pd.DataFrame(group_audit).to_csv(run/'audit/unmatched_groups.csv',index=False,encoding='utf-8-sig')
    residual=master.total_assets-master.total_liabilities-master.total_equity
    tolerance=np.maximum(1,master.total_assets.abs()*1e-8)
    actual=master.actual_announcement_date
    comparable=master[['top1_pct','top1_ownership_pct']].notna().all(axis=1)
    summary={
        'candidate_rows':len(candidate),'master_rows':len(master),'securities':int(master.stock_code.nunique()),
        'firm_ids':int(master.firm_id.nunique()),'missing_firm_id':int(master.firm_id.isna().sum()),
        'firm_year_duplicate_rows':int(master.loc[master.firm_id.notna()].duplicated(['firm_id','fiscal_year'],keep=False).sum()),
        'unresolved_candidate_rows':int((~candidate.eligible_known).sum()),
        'pre_listing_rows':int(candidate.pre_listing.sum()),'post_delisting_rows':int(candidate.post_delisting.sum()),
        'a_share_identity_unconfirmed_rows':int((~candidate.a_share_ever_confirmed).sum()),
        'listing_date_missing_rows':int(candidate.listing_date_resolved.isna().sum()),
        'listing_date_conflicts':int(master.listing_date_conflict.sum()),
        'financial_rows':int(master.financial_industry.fillna(False).sum()),
        'st_source_rows':int(master.st_source.fillna(False).sum()),
        'known_delisted_securities':int(master.loc[master.delisting_date.notna(),'stock_code'].nunique()),
        'actual_announcement_missing':int(actual.isna().sum()),
        'actual_before_report_date':int((actual<master.report_date).sum()),
        'predisclosure_actual_differ':int((actual.notna() & master.predisclosure_date.notna() & actual.ne(master.predisclosure_date)).sum()),
        'accounting_comparable':int(residual.notna().sum()),
        'accounting_outside_tolerance':int((residual.abs()>tolerance).sum()),
        'accounting_tolerance':'max(1 original unit, abs(assets)*1e-8); diagnostic, not exclusion',
        'leverage_gt_one':int(master.leverage_consolidated.gt(1).sum()),
        'equity_nonpositive':int(master.total_equity.le(0).sum()),
        'equity_near_zero_relative':int((master.total_equity.abs()/master.total_assets.abs()).lt(.01).sum()),
        'extreme_roe_abs_gt_one':int(master.roe_eop_consolidated.abs().gt(1).sum()),
        'near_zero_and_extreme_roe':int(((master.total_equity.abs()/master.total_assets.abs()).lt(.01)&master.roe_eop_consolidated.abs().gt(1)).sum()),
        'top1_comparable':int(comparable.sum()),
        'top1_difference_gt_001pp':int((comparable & master.top1_difference_pp.abs().gt(.01+1e-9)).sum()),
        'top1_outside_0_100':int((master.top1_pct.lt(0)|master.top1_pct.gt(100)).sum()),
        'mixed_ownership_codes':int(master.ownership_mixed_code.sum()),
        'duplicate_stock_year':int(master.duplicated(KEY).sum()),
        'financial_unit_status':'source units unchanged; currency/unit metadata not explicit in supplied field TXT; ratios provisional pending cross-table unit confirmation',
        'historical_state_status':'LISTINGSTATE definition says latest state for issued annual report; point-in-time historical ST/PT not verified',
        'population_status':'provisional observed-union; complete historical A-share universe and delisting coverage not certified',
    }
    dump_json(summary,run/'audit/summary.json')
    return summary

def run_pipeline(root=None):
    root=data_root() if root is None else Path(root).resolve()
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    run=root/'financial-data-v2/runs'/stamp
    for folder in ['interim','processed','audit']:
        (run/folder).mkdir(parents=True,exist_ok=False)
    manifest=source_inventory(root)
    tables,schemas,fields=standardize(root,run)
    views,flow=annual_views(tables)
    base,merge,breakdown=build_master(views)
    base=construct_variables(base)
    summary=audit_master(base,schemas,merge,breakdown,flow,run)
    dump_json(manifest,run/'audit/source_manifest.json')
    dump_json(schemas,run/'audit/schema.json')
    dump_json(fields,run/'audit/field_dictionary.json')
    dump_json({'executed_at':datetime.now().isoformat(),'pandas':pd.__version__,'numpy':np.__version__,
               'pipeline_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},run/'audit/execution.json')
    (root/'financial-data-v2/latest-run.txt').write_text(str(run),encoding='utf-8')
    return run,summary

if __name__=='__main__':
    run,summary=run_pipeline()
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print('受限运行目录:',run)
