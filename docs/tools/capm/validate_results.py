"""Independently check Stata estimates, HAC SEs, rolling windows and simulation."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from scipy import stats

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'logs/capm'


def ols(y,x,hac=6):
    X=np.column_stack([np.ones(len(x)),x])
    b=np.linalg.lstsq(X,y,rcond=None)[0];e=y-X@b
    U=X*e[:,None];S=U.T@U
    for lag in range(1,hac+1):
        cov=U[lag:].T@U[:-lag]
        S+=(1-lag/(hac+1))*(cov+cov.T)
    inv=np.linalg.inv(X.T@X)
    V=inv@S@inv*len(x)/(len(x)-2)
    se=np.sqrt(np.diag(V));r2=1-e@e/np.sum((y-y.mean())**2)
    return b,se,r2


def main():
    d=pd.read_stata(ROOT/'data/capm/industry_monthly.dta',convert_categoricals=False,convert_dates=False)
    estimates=pd.read_stata(RUN/'estimates.dta',convert_categoricals=False,convert_dates=False)
    deltas=[]
    for row in estimates.itertuples():
        y=(d[row.industry]-d.rf).to_numpy(float)
        b,se,r2=ols(y,d.mktrf.to_numpy(float))
        expected=[b[0],b[1],se[0],se[1],r2]
        actual=[row.alpha,row.beta,row.se_alpha,row.se_beta,row.r2]
        deltas.extend(np.abs(np.array(expected)-actual))
        assert row.n==432
        assert abs(row.p_alpha-2*stats.t.sf(abs(b[0]/se[0]),430))<1e-10
        assert abs(row.p_beta1-2*stats.t.sf(abs((b[1]-1)/se[1]),430))<1e-10
        cv=stats.t.ppf(.975,430)
        assert np.max(np.abs([row.alpha_lo-(b[0]-cv*se[0]),
            row.alpha_hi-(b[0]+cv*se[0]),row.beta_lo-(b[1]-cv*se[1]),
            row.beta_hi-(b[1]+cv*se[1])]))<1e-10
    assert max(deltas)<1e-10
    rolling=pd.read_stata(RUN/'rolling.dta',convert_categoricals=False,convert_dates=False)
    rolling_delta=[]
    for row in rolling.itertuples():
        part=d[(d.mdate>=row.mdate-row.window)&(d.mdate<row.mdate)]
        assert len(part)==row.window and part.mdate.max()==row.end_used==row.mdate-1
        b,_,_=ols((part[row.industry]-part.rf).to_numpy(float),part.mktrf.to_numpy(float),0)
        rolling_delta.append(abs(b[1]-row.beta))
    assert max(rolling_delta)<1e-10 and len(rolling)==1488
    raw=pd.read_stata(RUN/'simulation-input.dta',convert_categoricals=False,convert_dates=False)
    sim=pd.read_stata(RUN/'simulation.dta',convert_categoricals=False,convert_dates=False)
    sim_delta=[]
    for row in sim.itertuples():
        part=raw[(raw.mdate>=row.mdate-60)&(raw.mdate<row.mdate)]
        assert len(part)==60
        for col,target in [('ex_fixed',row.b_fixed),('ex_change',row.b_change)]:
            b,_,_=ols(part[col].to_numpy(float),part.mktrf.to_numpy(float),0)
            sim_delta.append(abs(b[1]-target))
    assert max(sim_delta)<1e-10
    assert np.allclose(raw.ex_change-raw.ex_fixed,(raw.beta_true-1)*raw.mktrf)
    assert raw.beta_true.iloc[:120].eq(1).all() and raw.beta_true.iloc[120:].eq(1.8).all()
    execution=json.loads((RUN/'execution.json').read_text(encoding='utf-8'))
    notebook=json.loads((ROOT/'notebooks/capm/capm-stata.ipynb').read_text(encoding='utf-8'))
    all_cells=[c for c in notebook['cells'] if c['cell_type']=='code']
    settings=[c for c in all_cells if 'capm-display-settings' in c.get('metadata',{}).get('tags',[])]
    assert [''.join(c['source']) for c in settings]==[
        '%set graph_height = 4.5in']+['%set graph_height = 3.2in']*3
    cells=[c for c in all_cells if c not in settings]
    master=(ROOT/'tools/capm/capm.do').read_text(encoding='utf-8')
    expected=[block.split('\n',1)[1] for block in master.split('* SECTION ')[1:]]
    assert [''.join(c['source']) for c in cells]==expected
    assert execution['execution_counts']==list(range(1,len(all_cells)+1))
    assert [c['execution_count'] for c in all_cells]==execution['execution_counts']
    assert not [o for c in all_cells for o in c['outputs'] if o['output_type']=='error']
    summary={'status':'PASS','stata_hac_vs_numpy_max_difference':float(max(deltas)),
        'rolling_checks':len(rolling),'rolling_max_difference':float(max(rolling_delta)),
        'simulation_estimate_checks':len(sim_delta),'simulation_max_difference':float(max(sim_delta)),
        'constant_beta_estimate_range':[float(sim.b_fixed.min()),float(sim.b_fixed.max())],
        'data_months':len(d),'missing_values':int(d.isna().sum().sum()),
        'duplicate_months':int(d.mdate.duplicated().sum()),'all_windows_past_only':True,
        'notebook_matches_master_do':True,
        'master_do_sha256':hashlib.sha256((ROOT/'tools/capm/capm.do').read_bytes()).hexdigest(),
        'notebook_sha256':hashlib.sha256((ROOT/'notebooks/capm/capm-stata.ipynb').read_bytes()).hexdigest(),
        'figures':execution['figures'],'stamp':execution['stamp'],
        'estimates':estimates.to_dict(orient='records')}
    (RUN/'validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['estimates','figures']},indent=2))


if __name__=='__main__':main()
