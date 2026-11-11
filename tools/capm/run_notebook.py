"""Execute the standalone Stata notebook with project-only kernel configuration."""
from pathlib import Path
from datetime import datetime
import asyncio
import hashlib
import json
import os
import re
import sys
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'logs/capm'
RUNTIME=RUN/'runtime'
NOTEBOOK=ROOT/'notebooks/capm/capm-stata.ipynb'

FRONT_MATTER='''---
number-sections: false
execute:
  enabled: false
---'''

INTRO=r'''<!-- Keep the unnumbered chapter heading for book metadata. -->
# CAPM：Stata 完整实验 {.unnumbered}

[理论讲义](../../lectures/capm.qmd) · [数据说明](../../data/capm/README.md) · [项目仓库](https://github.com/lianxhcn/FinEco)

## 实验说明 {#sec-capm-lab .unnumbered}

理论讲义中的代码片段用于解释关键运算和图表来源；本 Notebook 将数据核对、估计、循环和绘图串成完整执行流程，读取同样的两份冻结输入。

本实验用同源美国十行业组合、市场超额收益与月度无风险收益，估计市场风险暴露和风险调整收益，再比较滚动窗口和已知参数的模拟。固定样本为 1990 年 1 月至 2025 年 12 月，共 432 个月。

收益单位为每月百分数，β 无单位，α 的单位为每月百分数。Mkt-RF 已是超额收益，不能再减 RF。真实行业组合、市场代理和模拟分别说明，不与首讲 A 股篮子混用。

从 FinEco 根目录启用项目环境后运行 `python tools/capm/run_notebook.py`。运行器设置根目录、Stata 内核和图片时间戳，从第一个单元开始执行；不依赖旧电脑或先前交互状态。本页保存实际输出，网页渲染不取数、不执行代码。

图形部分单列 `%set graph_height` 显示设置，只控制本 Notebook 的画布高度；随后执行的 Stata 代码与 `capm.do` 一致，不修改全局配置或估计条件。

两个固定输入为 [industry_monthly.dta 的说明](../../data/capm/industry_monthly-README.md) (真实行业数据) 和 [beta_sim.dta 的说明](../../data/capm/beta_sim-README.md) (教学模拟)。各次分析只读这两份数据；本地重跑所需文件见 [运行说明](../../tools/capm/README.md)，仓库中的通用入口见 [notebooks 目录](https://github.com/lianxhcn/FinEco/tree/main/notebooks) 与 [tools 目录](https://github.com/lianxhcn/FinEco/tree/main/tools)。本页可以独立阅读已保存的代码与输出，重新执行仍需完整项目环境与输入。

结果整理使用 `estout` 包中的外部命令 `esttab`，首次使用前可在 Stata 运行 `ssc install estout`。本 Notebook 不自动安装或更新命令；开始前请用 `which esttab` 核对。参数表仍读取 `newey` 的 HAC(6) 估计，分别显示标准误、95% 置信区间，并导出 `logs/capm/regression.rtf`；RTF 可用 Word 打开。

## 模型与变量

记行业与市场的超额收益分别为 $r_{i,t}=R_{i,t}-R_{f,t}$ 和 $r_{m,t}=R_{m,t}-R_{f,t}$。其中 $i$ 表示行业，$t$ 表示月份，$R_{f,t}$ 为同月无风险收益。带截距的市场回归为

$$
r_{i,t}=\alpha_{i}+\beta_{i}r_{m,t}+\varepsilon_{i,t}.
$$

$\alpha_{i}$ 是截距，$\beta_{i}$ 衡量对市场共同波动的暴露，$\varepsilon_{i,t}$ 是单一市场因素未解释的随机干扰项。β 是资产与市场超额收益协方差除以市场超额收益方差，不衡量资产的全部波动。CAPM 在相应均衡与稳定参数条件下增加零截距限制；能估出 β，不等于定价关系已成立。

实验依次核对数据、比较点估计与推断、观察行业差异、检查组合恒等式，最后比较滚动窗口和模拟真值。改变一个设置时，先说明其他哪些条件保持不变。
'''

SECTIONS={
'setup':('数据核对','先确认冻结输入、月份连续性、样本量和收益单位，再列出原始行业文件的前六行。mdate 是月份；hitec、utils 是尚未扣除无风险收益的行业收益；mktrf 已是市场超额收益；rf 是同月无风险收益。行业列减 rf 一次生成 ex_hitec、ex_utils，mktrf 不再扣减。所有收益列均以每月百分数存储。'),
'estimates':('估计与推断','先显示 ex_hitec 与 mktrf 的样本协方差矩阵 V，再用 V[1,2]/V[2,2] 算出斜率。V 的顺序与 correlate 中的变量顺序相同；它不是回归系数估计的方差矩阵 e(V)。相同样本与解释变量下，三种方差估计的 α、β 应相同，标准误可以不同。HAC 最大滞后 6 个月仅为本例教学选择，不是所有月度数据的固定规则。分别检验 α=0 和 β=1。'),
'result_tables':('整理回归结果','先用 newey 估计并保存两个行业，再用 esttab 分别报告系数与标准误、系数与 95% 置信区间。它读取已保存的系数、方差和自由度，不改变估计方法。区间仍用自由度 430 的 t 临界值，与后面的手动端点计算一致。最后导出 RTF 文件，便于继续整理实证结果。'),
'industries':('行业比较','比较均值、波动、β 与拟合优度的不同含义。下表各行业均用 432 个月、相同市场代理和 HAC(6) 口径。十个单独检验不等于联合模型检验，也未作多重检验校正。'),
'market_graph':('市场回归图','两幅图横纵坐标口径相同。散点是每月已实现超额收益，拟合线斜率为样本 β，不是证券市场线。图中所有月份保留，不裁掉极端值。'),
'portfolio':('组合风险','两行业每月各占一半，相当于按月恢复固定权重，尚未扣除交易成本。在线性回归使用同一样本与截距项时，组合 β 等于成分 β 的加权和。这是线性代数性质，不是 CAPM 定价关系成立的独立证据。'),
'rolling':('滚动估计','先以 2025 年 12 月为目标月，显示只使用此前 60 个月的单次回归；随后循环构造两条序列。目标月 $t$ 的 β 只用此前 36 或 60 个月。两窗口统一从 1995 年 1 月开始比较，末次输入为 $t-1$。窗口重叠造成相邻估计相关，曲线波动不能独自证明真实 β 在变。'),
'simulation':('参数变化与估计噪声','读取固定文件 beta_sim.dta。数据在首次生成时包含 240 个月的模拟市场超额收益 $x=0.5+4z$，随机干扰项 $u=4v$，$z$、$v$ 独立标准正态。第一条序列 α=0、β=1 始终固定；第二条 β 前 120 月为 1，之后为 1.8。每次演示只读取固定文件；两条序列共用 $x$ 和 $u$，只改变斜率规则。滚动估计均只用过去 60 月。真实参数已知，便于分辨估计波动与参数变化；这不是实际市场的历史结果。')}


def math_prose(text):
 protected=r'(```[\s\S]*?```|`[^`\n]+`|\$\$[\s\S]*?\$\$|\$[^$\n]+\$)'
 pieces=re.split(protected,text)
 for i in range(0,len(pieces),2):
  s=pieces[i]
  for letter,latex in [('β',r'\beta'),('α',r'\alpha'),('ε',r'\varepsilon')]:
   s=re.sub(letter+r'\s*=\s*([−–-]?\d+(?:\.\d+)?)',
    lambda m:'$'+latex+'='+m[1]+'$',s)
   s=s.replace(letter,'$'+latex+'$')
  s=s.replace('R²',r'$R^{2}$')
  s=re.sub(r'(?<![A-Za-z])t (?=分布|临界值)',r'$t$ ',s)
  s=s.replace('检验 p 值',r'检验 $p$ 值')
  pieces[i]=s
 return ''.join(pieces)


def main():
    RUN.mkdir(parents=True,exist_ok=True)
    source=json.loads((ROOT/'data/capm/source.json').read_text(encoding='utf-8'))
    for name,row in source['files'].items():
        assert hashlib.sha256((ROOT/'data/capm'/name).read_bytes()).hexdigest()==row['sha256']
    stata=Path(os.environ.get('STATA_EXE','D:/stata19/StataMP-64.exe'))
    assert stata.is_file()
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
    os.environ.update(FINECO_ROOT=str(ROOT),CAPM_RUN_STAMP=stamp,
        IPYTHONDIR=str(RUNTIME/'ipython'),JUPYTER_RUNTIME_DIR=str(RUNTIME/'jupyter'),
        XDG_CONFIG_HOME=str(RUNTIME/'config'),PYTHONIOENCODING='utf-8')
    for rel in ['ipython','jupyter','config/nbstata','kernels/capm-stata']:
        (RUNTIME/rel).mkdir(parents=True,exist_ok=True)
    (RUNTIME/'config/nbstata/nbstata.conf').write_text(
        f'[nbstata]\nstata_dir = {stata.parent.as_posix()}\nedition = mp\nsplash = False\n'
    'graph_format = svg\ngraph_width = 6.4in\ngraph_height = 4.5in\n',encoding='utf-8')
    spec={'argv':[sys.executable,'-m','nbstata','-f','{connection_file}'],
          'display_name':'CAPM Stata','language':'stata'}
    (RUNTIME/'kernels/capm-stata/kernel.json').write_text(json.dumps(spec),encoding='utf-8')
    code=(ROOT/'tools/capm/capm.do').read_text(encoding='utf-8')
    assert max(map(len,code.splitlines()))<=76,'Stata lines exceed 76 columns'
    chunks=code.split('* SECTION ')
    nb=nbformat.v4.new_notebook(metadata={
        'number-sections':False,
        'execute':{'enabled':False},'kernelspec':{
        'name':'capm-stata','display_name':'CAPM Stata','language':'stata'}})
    nb.cells=[nbformat.v4.new_markdown_cell(FRONT_MATTER),
              nbformat.v4.new_markdown_cell(INTRO)]
    for block in chunks[1:]:
        key,body=block.split('\n',1)
        title,explanation=SECTIONS[key.strip()]
        if key.strip() in ['industries','market_graph','rolling','simulation']:
            height='4.5' if key.strip()=='industries' else '3.2'
            nb.cells.append(nbformat.v4.new_code_cell(
                f'%set graph_height = {height}in',
                metadata={'tags':['capm-display-settings']}))
        nb.cells.extend([nbformat.v4.new_markdown_cell(f'## {title}\n\n{explanation}'),
                         nbformat.v4.new_code_cell(body)])
        if key.strip()=='industries':
            nb.cells.append(nbformat.v4.new_markdown_cell('''科技行业 β 约为 1.317，公用事业行业约为 0.439。它们的原始月均收益分别约为 1.317% 和 0.830%，但截距分别约为每月 0.121% 和 0.282%。β 与均值的数字恰好接近，不代表两者具有相同单位或含义。

两行业 α 的 HAC 标准误分别约为 0.184、0.179，双侧检验 p 值约为 0.510、0.115。因此，这组样本与推断设置未在 5% 水平拒绝零截距。公用事业截距点估计较高，不能据此直接断言其具有稳定的超额表现。行业表中的 R² 说明拟合程度，也不检验定价关系。'''))
        if key.strip()=='industries':
            nb.cells.append(nbformat.v4.new_markdown_cell(r"""95% 置信区间采用

$$
\mathrm{CI}_{95}=\widehat{\beta}\pm c\cdot \operatorname{se}(\widehat{\beta}).
$$

这里省略当前行业的下标。$\widehat{\beta}$ 为斜率估计，$\operatorname{se}(\widehat{\beta})$ 为 HAC(6) 标准误，$c$ 为自由度 $T-2=430$ 的 $t$ 分布的 97.5% 分位数；减号和加号分别给出区间下限与上限。$\alpha$ 的区间同理。该推断依赖大样本近似，不保证任意相关误差下的精确小样本覆盖率。"""))
        if key.strip()=='simulation':
            nb.cells.append(nbformat.v4.new_markdown_cell('''左图真值始终为 1，估计仍约在 0.607 至 1.193 之间变化。这是固定参数下的一条模拟路径，说明滚动曲线波动可以由估计噪声产生；它不是所有模型下误差范围的一般结论。

右图真值在第 121 月跳到 1.8。目标月只用过去 60 月估计，旧状态观测逐步退出窗口，因此估计对变化有滞后。日期从 2000 年开始仅为展示时间轴，不对应真实市场事件。真实行业数据没有可直接观察的 β 真值，不能仅凭曲线把参数变化和估计噪声区分开。'''))
    nb.cells.append(nbformat.v4.new_markdown_cell('''## 习题

回到行业表，分别用均值、波动、β、α 区间和 R² 写出一句有明确口径的判断。β 不衡量全部风险，α 的解释依赖市场代理、样本与模型。α 不显著不等于模型已被证明。

固定模型与样本，改变 HAC 最大滞后；再固定数据，改变滚动窗口。运行前先说明预计哪些结果不变，哪些可能变化。模拟中真值已知，真实行业数据中真值未知。

## 文献联系

1. Fama and French (1992) 研究了股票平均收益差异。在其 1963—1990 年样本与检验设计下，市场 β 的解释力很弱，规模和账面市值比则能共同解释主要差异。其组合 β 用于个股横截面定价检验，不是历史时点均可获得的风险预测。[论文](https://doi.org/10.1111/j.1540-6261.1992.tb04398.x)
2. Baker et al. (2011) 发现了低波动、低 β 组合相对高风险组合的收益优势，并用风险偏好和基准考核约束提出解释。历史收益证据与解释机制应分别理解。[论文](https://doi.org/10.2469/faj.v67.n1.4)
3. Frazzini and Pedersen (2014) 用事前 β 调整多空规模，构建近似市场中性的 BAB 因子，发现其具有正的风险调整收益，且在融资条件收紧时表现较差。β 的估计直接影响头寸规模。[论文](https://doi.org/10.1016/j.jfineco.2013.10.005)
4. Ang and Chen (2007) 估计了长期样本中的条件 CAPM，发现所设定模型下价值策略的条件 α 缺乏显著异于零的证据。该推断依赖完整条件模型，不等于简单滚动 OLS。[论文](https://doi.org/10.1016/j.jempfin.2005.12.001)
5. Gormsen and Jensen (2024) 发现条件风险能够解释多项股票策略的部分无条件 α，但仍不足以解释全部异常收益，条件 CAPM 仍被拒绝。[论文](https://doi.org/10.1016/j.jfineco.2024.103933)
6. Drobetz et al. (2025) 发现机器学习 β 预测在统计和投资组合应用中优于所比较的传统基准，其中随机森林总体最好；非线性和交互关系有助于预测。[论文](https://doi.org/10.1017/S0022109024000036)

这些是不同研究用途的例子，本实验没有复现六篇论文的完整设计。完整文献信息见理论讲义；输入与处理见数据说明。不要将本例行业结果外推为 A 股个股结论。
'''))
    # Prose uses the same mathematical notation as the displayed equations.
    for cell in nb.cells:
        if cell.cell_type=='markdown':
            cell.source=math_prose(cell.source)
            # Link the narrative year itself, preserving author and DOI.
            pattern=r'(?m)^(\d+\. [A-Za-z][^\n]+?) \((\d{4})\)([^\n]*?)\s*\[论文\]\((https://doi\.org/[^)]+)\)'
            cell.source=re.sub(pattern,lambda m:m[1]+' (['+m[2]+']('+m[4]+'))'+m[3].rstrip(),cell.source)
    if NOTEBOOK.exists():
        backup=RUN/'backups'/f'capm-stata-{stamp}.ipynb';backup.parent.mkdir(parents=True,exist_ok=True)
        backup.write_bytes(NOTEBOOK.read_bytes())
    if sys.platform=='win32':asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    manager=KernelManager(kernel_name='capm-stata',kernel_spec_manager=
        KernelSpecManager(kernel_dirs=[str(RUNTIME/'kernels')]))
    NotebookClient(nb,km=manager,timeout=240,
        resources={'metadata':{'path':str(ROOT)}}).execute()
    errors=[o for c in nb.cells if c.cell_type=='code' for o in c.outputs if o.output_type=='error']
    assert not errors
    for name,row in source['files'].items():
        assert hashlib.sha256((ROOT/'data/capm'/name).read_bytes()).hexdigest()==row['sha256'],name+' modified by analysis'
    NOTEBOOK.parent.mkdir(parents=True,exist_ok=True);nbformat.write(nb,NOTEBOOK)
    report={'status':'PASS','stamp':stamp,'code_cells':sum(c.cell_type=='code' for c in nb.cells),
        'execution_counts':[c.execution_count for c in nb.cells if c.cell_type=='code'],
        'notebook_sha256':hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest(),
        'figures':[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'figs/raw').glob(f'capm-*-{stamp}.png'))]}
    (RUN/'execution.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
