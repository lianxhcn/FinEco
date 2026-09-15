"""生成讲义中的五幅数值图；独立画布、无硬编号、默认 Matplotlib 配色。

运行位置无关：python code/make_figures.py
字体只调用本机已有字体，不随任务包分发。
"""
from pathlib import Path
import sys
import warnings
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from scipy.stats import norm
from bootstrap_core import ROOT, X_TINY, tiny_example, group_example, validation_example

def configure_font():
    """从跨平台候选中选择已有的中文字体；找不到时明确警告。"""
    installed={f.name for f in font_manager.fontManager.ttflist}
    candidates=['Noto Sans CJK SC','Microsoft YaHei','PingFang SC','SimHei','Arial Unicode MS','Noto Sans CJK JP','Noto Serif CJK JP','AR PL UMing CN']
    found=next((s for s in candidates if s in installed),None)
    if found is None:
        warnings.warn('没有找到中文字体；请安装中文字体后重新导出，数值计算不受影响。')
    else:
        plt.rcParams['font.family']=[found,'DejaVu Sans']
    plt.rcParams['axes.unicode_minus']=False
    plt.rcParams['font.size']=12
    return found

def frame(title,xlabel,ylabel):
    fig,ax=plt.subplots(figsize=(10,6.2),dpi=100)
    ax.set_title(title,pad=20,fontsize=16)
    ax.set_xlabel(xlabel,labelpad=11)
    ax.set_ylabel(ylabel,labelpad=11)
    ax.spines[['top','right']].set_visible(False)
    return fig,ax

def finish(fig,path):
    fig.tight_layout(pad=2)
    fig.savefig(path,dpi=100,metadata={'Software':'Bootstrap lecture v05: make_figures.py'})
    plt.close(fig)

def main():
    configure_font()
    dest=ROOT/'logs/bootstrap/v10/recomputed';dest.mkdir(parents=True, exist_ok=True)
    tiny,arr=tiny_example();group,df,d=group_example()
    fig,ax=frame('从五个观测值构造经验分布','数值 x','累计概率')
    x=X_TINY
    ax.step(np.r_[0,x,14],np.r_[0,np.arange(1,6)/5,1],where='post',linewidth=2)
    ax.scatter(x,np.arange(1,6)/5,s=36,label='样本点处的累计概率')
    ax.set_xlim(0,14);ax.set_ylim(-.04,1.08)
    ax.set_xticks([0,2,4,5,7,12,14]);ax.set_yticks(np.linspace(0,1,6))
    ax.annotate('不超过 5 的记录占 3/5 = 0.6',xy=(5,.6),xytext=(6.6,.37),
                arrowprops={'arrowstyle':'->','linewidth':1.0})
    ax.legend(loc='lower right',frameon=False)
    finish(fig,dest/'edf-tiny.png')

    means=arr['means_exact']; val,cnt=np.unique(means,return_counts=True);prob=cnt/len(means)
    fig,ax=frame('样本均值的精确 Bootstrap 分布','Bootstrap 均值','概率')
    ax.bar(val,prob,width=.16,label='全部 3125 份有序样本')
    ax.axvline(6,linestyle='-',linewidth=1.6,label='原均值 = 6')
    ax.axvline(3.4,linestyle='--',linewidth=1.4,label='2.5% 分位数 = 3.4')
    ax.axvline(9.2,linestyle=':',linewidth=1.8,label='97.5% 分位数 = 9.2')
    ax.set_xlim(1.6,12.4);ax.set_ylim(0,.088)
    ax.legend(loc='upper right',frameon=False,fontsize=11)
    finish(fig,dest/'mean-bootstrap-exact.png')

    err=arr['errors_exact'];val,cnt=np.unique(err,return_counts=True);prob=cnt/len(err)
    fig,ax=frame('把参考分布放到原假设下','中心化均值差', '概率')
    bars=ax.bar(val,prob,width=.16,label='平移后的 Bootstrap 参考分布')
    for v,bar in zip(val,bars):
        if v >= 2-1e-12:
            bar.set_hatch('///')
    ax.axvline(2,linestyle='--',linewidth=1.6,label='实际均值差 = 2')
    ax.text(.98,.84,'右尾概率 = 376 / 3125\n                = 0.12032',transform=ax.transAxes,
            ha='right',va='top',fontsize=12)
    ax.set_xlim(-4.4,6.4);ax.set_ylim(0,.088)
    ax.legend(loc='upper right',frameon=False,fontsize=11)
    finish(fig,dest/'null-mean-tail.png')

    fig,ax=frame('两组分别重抽样：斜率差的分布','斜率差：第 0 组减第 1 组','密度')
    ax.hist(d,bins=44,density=True,alpha=.75,label='9999 次组内 Bootstrap')
    ax.axvline(group['difference'],linewidth=1.7,label=f"原系数差 = {group['difference']:.4f}")
    ax.axvline(0,linestyle=':',linewidth=1.8,label='零差异')
    lo,hi=group['percentile_ci']
    ax.axvline(lo,linestyle='--',linewidth=1.2,label=f'百分位数端点：{lo:.4f}、{hi:.4f}')
    ax.axvline(hi,linestyle='--',linewidth=1.2)
    ax.legend(loc='upper left',frameon=False,fontsize=10.5)
    ax.set_ylim(0,4.3)
    finish(fig,dest/'group-difference.png')

    validation,x,err=validation_example()
    fig,ax=frame('已知总体下：比较中心化的估计误差','均值估计误差','密度')
    ax.hist(err,bins=40,density=True,alpha=.6,label='给定一次样本后的 Bootstrap')
    grid=np.linspace(-1.8,1.8,500)
    ax.plot(grid,norm.pdf(grid,scale=validation['true_se']),linewidth=2,
            label='已知正态总体下的解析密度')
    ax.set_xlim(-1.8,1.8);ax.set_ylim(0,1.45)
    ax.legend(loc='upper right',frameon=False,fontsize=11)
    ax.text(.98,.78,'n = 80\n真实 SE = 0.4257\nBootstrap SE = 0.3895',transform=ax.transAxes,
            ha='right',va='top',fontsize=11)
    finish(fig,dest/'known-dgp-validation.png')
    print('已生成五幅 PNG 数值图：')
    for p in sorted(dest.glob('*.png')):
        print(p.name, p.stat().st_size, 'bytes')

if __name__=='__main__':
    main()
