"""Bootstrap 讲义 v05：仅负责计算，不依赖 Stata 或联网数据。

所有示例均为教学构造或明确给定 DGP 的模拟，不冒充实证数据。
"""
from __future__ import annotations
from itertools import product
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[2]
X_TINY = np.array([2., 4., 5., 7., 12.])
SEED = 12345
B = 9999

def ecdf_quantile(values: np.ndarray, probs: list[float]) -> np.ndarray:
    """经验分布的广义逆：最小的、累计概率至少为 p 的观测值。不作线性插值。"""
    a = np.sort(np.asarray(values, dtype=float))
    if a.ndim != 1 or a.size == 0 or not np.isfinite(a).all():
        raise ValueError('values 必须是非空且有限的一维数组')
    p = np.asarray(probs, dtype=float)
    if np.any((p <= 0) | (p > 1)):
        raise ValueError('分位点应在 (0, 1] 内')
    return a[np.maximum(0, np.ceil(p * a.size).astype(int) - 1)]

def tiny_example(B: int = B, seed: int = SEED) -> tuple[dict, dict[str, np.ndarray]]:
    """同时穷举全部有序样本与随机模拟；精确分布用总体标准差，随机重复用样本标准差。"""
    if B < 2:
        raise ValueError('B 至少为 2')
    x = X_TINY.copy()
    n = x.size
    all_samples = np.array(list(product(x, repeat=n)))
    means_exact = all_samples.mean(axis=1)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, n, size=(B, n))
    means_mc = x[indices].mean(axis=1)
    # H0: mu = 4，预先指定 H1: mu > 4。
    # 平移样本再重抽，与将每次均值减去原样本均值，完全等价。
    mu0 = 4.0
    obs = x.mean() - mu0
    errors_exact = means_exact - x.mean()
    errors_mc = means_mc - x.mean()
    tail_exact = int(np.count_nonzero(errors_exact >= obs - 1e-12))
    tail_mc = int(np.count_nonzero(errors_mc >= obs - 1e-12))
    se_exact = means_exact.std(ddof=0)
    se_mc = means_mc.std(ddof=1)
    res = {
        'n': n, 'B': B, 'seed': seed, 'K': len(means_exact),
        'mean': float(x.mean()), 'sample_variance': float(x.var(ddof=1)),
        'analytical_se_estimate': float(x.std(ddof=1)/np.sqrt(n)),
        'exact_boot_mean': float(means_exact.mean()), 'exact_boot_se': float(se_exact),
        'exact_boot_bias': float(means_exact.mean()-x.mean()),
        'exact_percentile_ci': ecdf_quantile(means_exact, [.025,.975]).tolist(),
        'normal_boot_ci': (x.mean()+norm.ppf([.025,.975])*se_exact).tolist(),
        'mc_boot_mean': float(means_mc.mean()), 'mc_boot_se': float(se_mc),
        'mc_boot_bias': float(means_mc.mean()-x.mean()),
        'mc_percentile_ci': ecdf_quantile(means_mc,[.025,.975]).tolist(),
        'null_mu': mu0, 'observed_error': float(obs), 'exact_tail_count': tail_exact,
        'exact_boot_p': tail_exact/len(means_exact), 'mc_tail_count': tail_mc,
        'mc_boot_p_plus1': (tail_mc+1)/(B+1),
        'mc_tail_mcse': float(np.sqrt((tail_mc/B)*(1-tail_mc/B)/B)),
        'oob_probability_n5': float((1-1/n)**n)
    }
    assert np.isclose(se_exact, np.sqrt((n-1)/n)*res['analytical_se_estimate'])
    assert np.isclose(res['exact_boot_mean'], x.mean())
    assert np.allclose(ecdf_quantile(means_exact,[.025,.975]), [3.4,9.2])
    return res, {'all_samples': all_samples, 'means_exact': means_exact,
                 'means_mc': means_mc, 'errors_exact': errors_exact, 'errors_mc': errors_mc}

def ols_slope(x: np.ndarray, y: np.ndarray) -> float:
    """带截距的一元 OLS 斜率；设计退化时显式报错，不静默丢弃失败抽样。"""
    xc = x - x.mean()
    den = np.dot(xc, xc)
    if den <= 1e-15:
        raise ValueError('重抽样样本解释变量没有有效变异')
    return float(np.dot(xc,y-y.mean())/den)

def group_example(B: int = B) -> tuple[dict, pd.DataFrame, np.ndarray]:
    """两组独立横截面教学数据。组别、设计分布、误差尺度和系数均明确给定。"""
    rng = np.random.default_rng(24680)
    frames=[]
    # cash 与 invest 均可读作比率；不赋予模拟系数因果识别含义。
    for g, beta, sigma, lo, hi in [(0,.30,.035,.02,.20),(1,.60,.055,.04,.26)]:
        x = rng.uniform(lo,hi,size=80)
        y = .04 + beta*x + rng.normal(0,sigma,size=80)
        frames.append(pd.DataFrame({'group':g,'cash':x,'invest':y}))
    df = pd.concat(frames, ignore_index=True)
    x0,y0 = df.loc[df.group==0,['cash','invest']].to_numpy().T
    x1,y1 = df.loc[df.group==1,['cash','invest']].to_numpy().T
    b0,b1=ols_slope(x0,y0),ols_slope(x1,y1)
    rng = np.random.default_rng(SEED)
    d=np.empty(B)
    for b in range(B):
        i0=rng.integers(0,len(x0),len(x0)); i1=rng.integers(0,len(x1),len(x1))
        d[b]=ols_slope(x0[i0],y0[i0])-ols_slope(x1[i1],y1[i1])
    result={'n0':len(x0),'n1':len(x1),'B':B,'seed':SEED,
            'beta0':b0,'beta1':b1,'difference':b0-b1,'bootstrap_se':float(d.std(ddof=1)),
            'percentile_ci':ecdf_quantile(d,[.025,.975]).tolist(),
            'true_beta0':.30,'true_beta1':.60,'data_seed':24680,'failures':0}
    return result,df,d

def validation_example() -> tuple[dict, np.ndarray, np.ndarray]:
    """另设已知正态 DGP 作检验工具：真分布用解析正态密度，不冒称 MC 为真值。"""
    mu=6.; sigma=np.sqrt(14.5); n=80; b=9999
    rng=np.random.default_rng(97531)
    x=rng.normal(mu,sigma,size=n)
    indices=rng.integers(0,n,size=(b,n))
    err=x[indices].mean(axis=1)-x.mean()
    return {'mu':mu,'sigma':float(sigma),'n':n,'B':b,'seed':97531,
            'sample_mean':float(x.mean()),'true_se':float(sigma/np.sqrt(n)),
            'bootstrap_se':float(err.std(ddof=1))}, x, err

def write_outputs() -> dict:
    for d in ['data/bootstrap','logs/bootstrap/v10']:
        (ROOT/d).mkdir(parents=True, exist_ok=True)
    tiny, arr=tiny_example()
    group,df,diff=group_example()
    validation,x,err=validation_example()
    pd.DataFrame({'boot_mean':arr['means_exact']}).to_csv(ROOT/'data/bootstrap/tiny_exact_means.csv',index=False)
    pd.DataFrame({'boot_mean':arr['means_mc']}).to_csv(ROOT/'data/bootstrap/tiny_mc_means.csv',index=False)
    pd.DataFrame({'value':X_TINY}).to_csv(ROOT/'data/bootstrap/tiny_sample.csv',index=False)
    df.to_csv(ROOT/'data/bootstrap/two_groups_teaching.csv',index=False,float_format='%.17g')
    pd.DataFrame({'difference':diff}).to_csv(ROOT/'data/bootstrap/group_boot_differences.csv',index=False)
    result={'tiny':tiny,'group':group,'validation':validation}
    (ROOT/'logs/bootstrap/v10/numerical-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    print(json.dumps(write_outputs(),ensure_ascii=False,indent=2))
