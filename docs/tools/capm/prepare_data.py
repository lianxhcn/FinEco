"""Build the frozen monthly teaching sample from previously acquired archives."""
from pathlib import Path
import hashlib
import io
import json
import re
import zipfile
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'logs/capm'
DATA=ROOT/'data/capm'


def monthly_block(path):
    with zipfile.ZipFile(path) as z:
        name=next(n for n in z.namelist() if n.lower().endswith('.csv'))
        lines=z.read(name).decode('utf-8-sig').splitlines()
    first=next(i for i,l in enumerate(lines) if re.match(r'^\s*\d{6},',l))
    header=lines[first-1]
    end=first
    while end<len(lines) and re.match(r'^\s*\d{6},',lines[end]):end+=1
    d=pd.read_csv(io.StringIO('\n'.join([header]+lines[first:end])),index_col=0)
    d.columns=d.columns.str.strip().str.lower()
    d.index=d.index.astype(int)
    assert d.index.is_unique
    return d,lines[:first]


def main():
    DATA.mkdir(parents=True,exist_ok=True)
    for p in [DATA/'industry_monthly.csv',DATA/'industry_monthly.dta']:
        assert not p.exists(),f'Frozen input already exists: {p}'
    factors,fh=monthly_block(RUN/'sources/factors.zip')
    industries,ih=monthly_block(RUN/'sources/industries.zip')
    assert 'Average Value Weighted Returns -- Monthly' in '\n'.join(ih)
    d=industries.join(factors[['mkt-rf','rf']],how='inner').loc[199001:202512].copy()
    assert len(d)==432 and not d.isna().any().any()
    assert not (d<=-99.99).any().any()
    periods=pd.PeriodIndex(d.index.astype(str),freq='M')
    assert periods.equals(pd.period_range('1990-01','2025-12',freq='M'))
    d=d.rename(columns={'mkt-rf':'mktrf'})
    d.insert(0,'mdate',(periods.year-1960)*12+periods.month-1)
    d.insert(0,'month',periods.astype(str))
    d=d.reset_index(drop=True)
    # All return fields retain the provider's percentage units; do not divide twice.
    d.to_csv(DATA/'industry_monthly.csv',index=False,encoding='utf-8-sig',float_format='%.10g')
    d.to_stata(DATA/'industry_monthly.dta',write_index=False,version=118,
               data_label='US monthly returns in percent, 1990-2025')
    acquisition=json.loads((RUN/'sources/acquisition.json').read_text(encoding='utf-8'))
    report={'retrieved_at':acquisition['retrieved_at'],'sample':['1990-01','2025-12'],
        'observations':len(d),'assets':'10 US value-weighted industry portfolios including dividends',
        'units':'Percent per month; beta dimensionless; alpha percent per month',
        'market':'Mkt-RF is already excess market return; do not subtract RF again',
        'rf':'Monthly RF from the same Fama/French factor file, not annual yield',
        'raw_headers':{'factors':fh,'industries':ih},
        'sources':[x for x in acquisition['downloads'] if x['file'] in ['factors.zip','industries.zip']],
        'files':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                         'bytes':p.stat().st_size} for p in [DATA/'industry_monthly.csv',DATA/'industry_monthly.dta']},
        'identity':'This is a US industry example, not the earlier A-share stock basket.',
        'point_in_time':'Latest downloaded historical vintage, not a reconstructed real-time vintage.',
        'rights':'Provider retains rights; local educational analysis. No claim of an open redistribution license.'}
    (DATA/'industry_monthly-source.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['sample','observations','units','market']},indent=2))


if __name__=='__main__':main()
