from pathlib import Path
import argparse
import difflib
import json
import re
import subprocess
import textwrap

import nbformat


ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / 'notebooks/monte-carlo/monte-carlo-cases.ipynb'
BOOKS = {
    name: nbformat.read(ROOT / f'notebooks/monte-carlo/{filename}', as_version=4)
    for name, filename in {
        'basics': '00-monte-carlo-basics.ipynb',
        'ols': '01-ols-iv-simulation.ipynb',
        'valuation': '02-project-valuation-monte-carlo.ipynb',
        'portfolio': '03-portfolio-risk-monte-carlo.ipynb',
        'process': '04-brownian-gbm-option.ipynb',
    }.items()
}
cells = []
mapping = []


def prose_spacing(source):
    if isinstance(source, list):
        return [prose_spacing(item) for item in source]
    protected = r'(`+[^`]*`+|\$[^\n$]*\$|\]\([^\n]*?\)|\{[^\n]*?\})'
    parts = re.split(protected, source)
    for index in range(0, len(parts), 2):
        parts[index] = re.sub(r'([\u4e00-\u9fff])([A-Za-z0-9])', r'\1 \2', parts[index])
        parts[index] = re.sub(r'([A-Za-z0-9%])([\u4e00-\u9fff])', r'\1 \2', parts[index])
    return ''.join(parts)


def markdown(source):
    cells.append(nbformat.v4.new_markdown_cell(prose_spacing(textwrap.dedent(source).strip())))


def code(source, origin='new', label=None, caption=None):
    source = textwrap.dedent(source).strip()
    if label:
        options = f'#| label: {label}\n'
        if caption:
            options += '#| fig-cap: ' + json.dumps(prose_spacing(caption), ensure_ascii=False) + '\n'
        source = options + source
    cells.append(nbformat.v4.new_code_cell(source))
    mapping.append({'cell': len(cells) - 1, 'origin': origin})


def old(book, index):
    return BOOKS[book].cells[index].source.strip()


def supplement(title):
    markdown(f'::: {{.callout-note collapse="true" title="{title}"}}')


def close_supplement():
    markdown(':::')


markdown(r'''
本页集中展示理论章中的基础抽样与四个案例，适合课堂查看保存的结果，也可以在本地从头运行。各节标题与理论正文对应，点击每个案例开头的链接即可返回相应位置。

## 阅读与运行说明 {.unnumbered #sec-mc-nb-guide}

从仓库根目录或本页所在目录启动 Jupyter，依次运行所有单元。所需环境包括 NumPy、pandas、Matplotlib、SciPy 和 statsmodels。公共设置只需运行一次，各案例随后设置自己的参数与随机数发生器。不要在没有初始化的情况下直接执行某个中间单元。

案例一、二、四使用教学模拟，不需要外部数据。案例三读取仓库 `data/monte-carlo/` 下已保存的处理后数据，不联网取数，也不读取教师本机的供应商缓存。运行结果默认写入仓库 `output/monte-carlo/cases/`，不会覆盖输入数据。

网页展示预先执行的输出，Quarto 编译不执行计算。补充核验在网页中折叠，Notebook 文件仍保留完整代码。本文使用案例一至四定位内容，不占用全书正式章节编号。
''')
code('''
from pathlib import Path
from math import log, sqrt, exp, erf
import json
import os
import platform
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm
import statsmodels.api as sm
from statsmodels.sandbox.regression.gmm import IV2SLS
from IPython.display import display, Image

def find_course_root():
    # 根据课程数据与目录识别仓库，不依赖本机绝对路径。
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if ((candidate / 'data/monte-carlo/returns.csv').is_file()
                and (candidate / 'notebooks/monte-carlo').is_dir()):
            return candidate
    raise FileNotFoundError('请在完整课程仓库内启动；需要 data/monte-carlo/returns.csv。')

ROOT = find_course_root()
OUTPUT = Path(os.environ.get('FINECO_MC_OUTPUT', ROOT / 'output/monte-carlo/cases'))
OUTPUT.mkdir(parents=True, exist_ok=True)
SEED = 20261001
plt.rcParams.update({'font.family': 'sans-serif',
                     'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'Noto Sans CJK SC', 'DejaVu Sans'],
                     'axes.unicode_minus': False, 'font.size': 11})
pd.set_option('display.max_columns', 16)
pd.set_option('display.width', 140)
case_results = {}
display(pd.Series({'Python': platform.python_version(), 'NumPy': np.__version__,
                   'pandas': pd.__version__, '主随机种子': SEED}, name='运行环境'))
''')
markdown(r'''
## 基础抽样与模拟设置 {.unnumbered #sec-mc-nb-basics}

[返回正文：几个基本概念](../../lectures/monte-carlo.qmd#sec-mc-basics)。

### 随机数、概率分布与抽样 {.unnumbered}

$U\sim U(0,1)$ 表示随机变量 $U$ 服从区间 $(0,1)$ 上的均匀分布，符号 $\sim$ 读作服从。均匀分布在区间内具有相同的概率密度，等长子区间获得相同的概率。下面分别抽取均匀、标准正态和均值为 1 的指数随机数，观察取值范围、对称性和右尾的区别。

每幅图均包含 10000 个抽样值，纵轴为概率密度。它们用于说明如何从给定概率分布抽样，尚不是一个完整的回归或金融决策案例。
''')
code('''
distribution_rng = np.random.default_rng(SEED)
distribution_samples = {
    '均匀分布 U(0,1)': distribution_rng.uniform(size=10000),
    '标准正态 N(0,1)': distribution_rng.normal(size=10000),
    '指数分布 (均值1)': distribution_rng.exponential(scale=1, size=10000),
}
fig, axes = plt.subplots(1, 3, figsize=(12, 3.7), layout='constrained')
for axis, (name, sample) in zip(axes, distribution_samples.items()):
    axis.hist(sample, bins=45, density=True, alpha=.65, color='#0072B2')
    axis.set(title=name, xlabel='取值', ylabel='概率密度')
    axis.grid(alpha=.15)
plt.show()
display(pd.DataFrame({name: {'样本均值': values.mean(), '样本标准差': values.std(ddof=1)}
                      for name, values in distribution_samples.items()}).T)
''', label='fig-mc-nb-three-distributions', caption='三种概率分布的抽样对照。各生成10000个值，保留各分布适合的横轴范围，不用图形宽度直接比较波动大小。')
markdown(r'''
### 从均匀随机数到目标分布 {.unnumbered}

对具有可用逆函数的连续累积分布函数 $F$，可以令 $X=F^{-1}(U)$。例如，均值为 1 的指数分布满足 $F(x)=1-e^{-x}$，因此 $X=-\log(1-U)$。下一段直接用均匀随机数作变换。

这只是逆分布函数抽样的一个例子。不同分布也可以使用其他抽样算法，不能把这个变换直接套到所有分布上。软件完成数值抽样，但需要模拟哪些变量、采用何种分布、参数如何确定，仍应根据分析问题设定。
''')
code('''
inverse_rng = np.random.default_rng(SEED)
uniform_values = inverse_rng.random(10000)
exponential_values = -np.log1p(-uniform_values)
assert np.isfinite(exponential_values).all() and (exponential_values >= 0).all()
display(pd.Series({'指数样本均值': exponential_values.mean(),
                   '指数样本标准差': exponential_values.std(ddof=1),
                   '理论均值': 1.0, '理论标准差': 1.0}))
''')
markdown(r'''
### 随机种子、DGP 与重复次数 {.unnumbered}

相同的发生器、种子和调用顺序可以产生相同序列。下面分别初始化两个发生器，比较它们生成的前五个标准正态数。

DGP 不仅包括分布，还包括变量之间的关系和依赖设定。案例一将完整演示如何生成解释变量、扰动项和因变量，并通过重复估计得到抽样分布。这里先区分：$n$ 是每次回归所用的样本量，$B$ 是重复生成样本并估计的次数。
''')
code(old('basics', 7), 'N00:7')
supplement('补充核验：用模拟均值近似一个已知期望')
markdown(r'设 $X\sim N(0,1)$，则 $E(X^{2})=1$。随着抽样数量增加，样本平方的平均值通常更接近该期望，单条随机序列不要求误差单调下降。')
code(old('basics', 9), 'N00:9')
code(old('basics', 10), 'N00:10', 'fig-mc-nb-running-mean', '标准正态平方的累计平均值与理论期望1。')
close_supplement()


markdown(r'''
## 案例一：用模拟理解计量性质 {.unnumbered #sec-mc-nb-econometrics}

[返回正文：案例一](../../lectures/monte-carlo.qmd#sec-mc-econometrics)。

本例在已知参数真值的 DGP 中比较估计结果。OLS 部分采用 $Y_{i}=1+2X_{i}+u_{i}$，解释变量与扰动项相互独立且均服从标准正态分布。每次都重新生成整个样本，再估计和保存斜率。

### OLS 的无偏性 {.unnumbered}

固定 $n=100$，重复 $B=5000$ 次。输出均值与真值 2 的差作为 MC 偏差，不能把一次估计或有限次均值当作无偏性的证明。
''')
code(old('ols', 4), 'N01:4')
code(old('ols', 5), 'N01:5', 'fig-mc-nb-ols-unbiased', 'OLS无偏性：估计分布、参数真值与MC均值。')
markdown(r'''
按这些设定，保存结果中的估计均值约为 2.001526，与真值 2 接近。图中真值线应与估计分布共同观察。

### OLS 的一致性 {.unnumbered}

保持 DGP 不变，改变每次回归的样本量，各组重复 3000 次。左图比较估计分布，右图和表比较经验标准差。图形只使用统一显示窗口，没有将窗口外的估计值从统计量中删除。
''')
code(old('ols', 7), 'N01:7')
code(old('ols', 8), 'N01:8', 'fig-mc-nb-ols-consistency', 'OLS一致性：不同样本量下的估计分布与经验标准差。')
code('display(ols_summary)', 'N01:23 summary')
markdown(r'''
### IV：内生性与弱工具变量 {.unnumbered}

本例生成 $Y=\beta X+\gamma W+u$ 和 $X=\pi Z+\delta u+v$。独立标准正态变量 $Z,W,u,v$ 用于生成样本，$\delta$ 控制内生性，$\pi$ 控制工具变量与解释变量的相关性。每个样本同时计算 OLS 和 IV，结构参数真值均为 1。

#### 改变内生性 {.unnumbered}

固定 $n=500$、$B=1200$ 和 $\pi=1$，改变 $\delta$。下面先定义生成与估计函数，再比较两种估计均值。
''')
code(old('ols', 10), 'N01:10')
code(old('ols', 12), 'N01:12')
code(old('ols', 13), 'N01:13', 'fig-mc-nb-iv-endogeneity', '固定工具变量相关性，比较内生性变化下的OLS与IV均值。')
markdown(r'''
#### 减弱工具变量相关性 {.unnumbered}

固定内生性参数，依次降低 $\pi$，其余设置不变。两幅 ECDF 都以全部 1200 次估计为分母，左图保留极端估计，右图只放大真值附近，不重新归一化。
''')
code(old('ols', 15), 'N01:15')
code(old('ols', 16), 'N01:16', 'fig-mc-nb-iv-weak', '弱工具变量的完整经验分布及局部放大。')
markdown('工具较弱时，IV 估计更容易出现远离真值的结果。应结合完整分布和分位数阅读，不能只用一个平均值概括。')
supplement('案例一结果核对与导出')
source = old('ols', 23).replace("Path(os.environ.get('FINECO_CASE1_EXPORT', 'output/monte-carlo/case1'))", "OUTPUT / 'case1'")
code(source, 'N01:23 export')
code("case_results['case1'] = {'mean': float(bhat_100.mean()), 'bias': float(bhat_100.mean()-2), 'arrays': len(arrays)}")
close_supplement()

markdown(r'''
## 案例二：项目估值 {.unnumbered #sec-mc-nb-valuation}

[返回正文：案例二](../../lectures/monte-carlo.qmd#sec-mc-valuation)。

企业选择价格后，由年度需求冲击生成市场份额，再沿销量、收入和现金流关系计算项目 NPV。价格是决策变量，需求冲击和贴现率是不确定性因素，市场份额及 NPV 是模型计算结果。

本例期限为 10 年，年度潜在市场规模为 100 万件，初始投资 3500 万元，年度固定支出 600 万元，现金流转化比例为 0.28。需求冲击标准差为 0.55。贴现率设为 $r=0.05+0.07X_{r}$，其中 $X_{r}\sim Beta(3,4)$。每个情景使用一个贴现率，需求冲击按年独立抽取。金额计算使用元，NPV 表和图使用百万元。

实际应用中，市场规模可结合行业资料与市场调研估算，现金流比例与固定支出需参考财务记录，价格敏感性则需要历史销售或试销资料支持。本页参数为教学设定，不是这些资料的实证估计。

### 经营关系与参数 {.unnumbered}

现金流采用 $FCF_{t}=mpQ_{0}s_{t}-F$，NPV 为未来十年各年末现金流的现值之和减去初始投资。代码中的 `p_ref` 对应正文的市场参考价格 $\bar p=100$，`simulate_project` 内部独立初始化发生器，比较价格时保留共同随机输入。
''')
source = old('valuation', 3)
source = '\n'.join(line for line in source.splitlines() if not line.startswith('import '))
code(source, 'N02:3')
code(old('valuation', 4), 'N02:4')
code("display(Image(filename=str(ROOT / 'figs/raw/mc-valuation-fig01-mechanism-corrected-20261017-225145.png')))", 'accepted conceptual figure', 'fig-mc-nb-valuation-mechanism', '经营关系：现金流转化比例与固定支出作用于自由现金流。')
markdown(r'''
### 从一个情景到 NPV 分布 {.unnumbered}

在价格 80 元下生成 20000 个十年经营情景。核心数组每行对应一个情景，每列对应一年。沿年份折现汇总现金流后，每个情景得到一个 NPV。均值说明预期价值，正 NPV 比例与 5% 分位数分别反映满足投资标准的概率及下行损失。
''')
code(old('valuation', 6), 'N02:6')
code(old('valuation', 7), 'N02:7', 'fig-mc-nb-valuation-npv', '价格80元下的NPV分布与经验累积分布。')
markdown(r'''
### 从 NPV 分布进入价格决策 {.unnumbered}

候选价格从55到160元，间隔5元。每个价格使用同样的模拟次数和随机输入，以便比较价格改变后的经营结果。结果缓存只避免重复计算，不改变抽样顺序或算法。
''')
source = old('valuation', 9).replace('rows = []', 'valuation_cache = {float(price): simulate_project(price) for price in price_grid}\nrows = []').replace('result = simulate_project(p)', 'result = valuation_cache[float(p)]')
code(source, 'N02:9, cache only')
code('''
fig, value_axis = plt.subplots(figsize=(8.4, 4.8), layout='constrained')
probability_axis = value_axis.twinx()
value_line, = value_axis.plot(price_results['price'], price_results['mean_npv_million'],
                            marker='o', color='#0072B2', label='平均 NPV (左轴)')
probability_line, = probability_axis.plot(price_results['price'], price_results['prob_positive'] * 100,
                                        marker='s', linestyle='--', color='#D55E00',
                                        label='NPV 为正的概率 (右轴)')
value_axis.axhline(0, color='#666666', linewidth=.8, linestyle=':')
value_axis.set(xlabel='产品价格 p (元)', ylabel='平均 NPV (百万元)',
               xlim=(price_grid.min(), price_grid.max()))
probability_axis.set(ylabel='NPV 为正的概率 (%)', ylim=(0, 100))
value_axis.tick_params(axis='y', colors='#0072B2')
probability_axis.tick_params(axis='y', colors='#D55E00')
value_axis.yaxis.label.set_color('#0072B2')
probability_axis.yaxis.label.set_color('#D55E00')
value_axis.grid(alpha=.15)
value_axis.legend(handles=[value_line, probability_line], loc='lower left', frameon=False)
plt.show()
''', 'N02:10 data; accepted dual-axis presentation', 'fig-mc-nb-valuation-prices',
     '候选价格下的平均 NPV 与正 NPV 概率。左轴为平均 NPV (百万元)，右轴为正 NPV 概率 (%)，虚线水平线表示左轴 NPV 为零。两条曲线的交点没有经济含义。')
markdown('本组网格中，80元的平均NPV和正NPV概率最高，70元的5%分位数最高。三项指标未必指向同一方案。这里没有另外指定企业风险约束，不给出唯一最优价格。')
markdown(r'''
### NPV = 0 的决策边界 {.unnumbered}

固定年度份额时，临界份额由价格与贴现率决定。年度份额随冲击变化时，需要按各年的贴现系数计算加权平均，再与同一情景贴现率下的门槛比较。简单平均份额不能保证与逐年NPV对应。

下图边界带来自贴现率上下限，不是置信区间。左图每价选250个情景显示，右图显示基准价格的全部20000个情景。
''')
code(old('valuation', 12), 'N02:12')
code(old('valuation', 14), 'N02:14', 'fig-mc-nb-valuation-boundary', '贴现加权份额与NPV=0门槛的对应关系。')
supplement('案例二压力测试、边界核验与稳定性')
markdown('压力测试改变市场规模、固定支出或贴现率分布。下面同时核验NPV两种计算方式、同样算术平均而时序不同的反例，以及种子变化时的价格比较结果。')
code(old('valuation', 16), 'N02:16')
code(old('valuation', 18), 'N02:18')
source = old('valuation', 20).replace("Path(os.environ.get('FINECO_VALUATION_EXPORT', 'output/monte-carlo/valuation'))", "OUTPUT / 'valuation'").replace('scenario = simulate_project(price)', 'scenario = valuation_cache[float(price)]').replace('display(decision_results)\n', '')
code(source, 'N02:20, reuse cache')
code(old('valuation', 22), 'N02:22')
code("case_results['valuation'] = audit")
close_supplement()

markdown(r'''
## 案例三：用真实数据校准组合风险模型 {.unnumbered #sec-mc-nb-portfolio}

[返回正文：案例三](../../lectures/monte-carlo.qmd#sec-mc-portfolio)。

前两例预先设定了生成机制。本例根据五只股票的历史收益估计均值、波动和共同变化，再比较正态模拟、历史整行重抽样与多日区块抽样。它们使用相同的两组组合权重，重点是生成方式怎样影响损失分布，不把本例解释为实时风险预测。

### 数据、股票池与组合权重 {.unnumbered}

股票为招商银行、长江电力、万科A、格力电器和比亚迪。共同有效日收益覆盖2016-09-05至2026-09-30，共2397日。日收益由后复权价格计算。等权组合各占20%，市值权重使用2026-09-30五只股票总市值的相对比例，比较方法时不改变权重。

下面只读取仓库处理后数据。价格文件保留原始日期和缺失位置，用于识别连续区块；收益文件只包含共同有效日。不能把删除缺失后的有效日序列直接当作没有间断的交易日序列。接口与口径资料见[数据说明](../../data/monte-carlo/README.md)。
''')
code('''
portfolio_data = ROOT / 'data/monte-carlo'
required_inputs = ['returns.csv', 'adjusted_prices.csv', 'portfolio-results/portfolio_weights.csv', 'stock_pool.csv']
missing_inputs = [name for name in required_inputs if not (portfolio_data / name).is_file()]
if missing_inputs:
    raise FileNotFoundError('缺少仓库冻结文件：' + ', '.join(missing_inputs))
portfolio_returns = pd.read_csv(portfolio_data / 'returns.csv', index_col=0, parse_dates=True, encoding='utf-8-sig')
portfolio_prices = pd.read_csv(portfolio_data / 'adjusted_prices.csv', index_col=0, parse_dates=True, encoding='utf-8-sig')
portfolio_weight_table = pd.read_csv(portfolio_data / 'portfolio-results/portfolio_weights.csv', dtype={'code': str}, encoding='utf-8-sig').set_index('code').loc[portfolio_returns.columns]
portfolio_weights = portfolio_weight_table[['equal_weight', 'value_weight']].to_numpy()
portfolio_names = ['等权组合', '市值权重组合']
stock_names = portfolio_weight_table['name'].tolist()
assert portfolio_returns.index.is_unique and portfolio_prices.index.is_unique
assert portfolio_returns.index.is_monotonic_increasing and portfolio_prices.index.is_monotonic_increasing
assert portfolio_returns.index.isin(portfolio_prices.index).all()
assert np.isfinite(portfolio_returns.to_numpy()).all()
assert (portfolio_returns.to_numpy() > -1).all()
assert np.isfinite(portfolio_weights).all() and (portfolio_weights >= 0).all()
assert np.allclose(portfolio_weights.sum(axis=0), 1)
display(pd.Series({'共同有效日': len(portfolio_returns), '原日期索引长度': len(portfolio_prices),
                   '开始': str(portfolio_returns.index.min().date()), '结束': str(portfolio_returns.index.max().date())}))
display(portfolio_weight_table[['name', 'sector', 'equal_weight', 'value_weight', 'reference_date']])
''', 'N03 data entry refactored to frozen repository CSVs')
markdown(r'''
### 用历史数据设定联合分布 {.unnumbered}

每行是同一天五只股票的收益。按列计算均值得到五维均值向量，样本协方差矩阵的对角线表示各股票收益方差，非对角线表示共同变化。下面显示完整估计矩阵，并画相关系数图，便于按股票名称查阅。
''')
code('''
portfolio_values = portfolio_returns.to_numpy()
portfolio_mu = portfolio_values.mean(axis=0)
portfolio_cov = np.cov(portfolio_values, rowvar=False, ddof=1)
assert np.linalg.eigvalsh(portfolio_cov).min() > 0
display(pd.Series(portfolio_mu, index=stock_names, name='平均日收益率'))
display(pd.DataFrame(portfolio_cov, index=stock_names, columns=stock_names))
fig, axis = plt.subplots(figsize=(6.4, 5.2), layout='constrained')
correlations = portfolio_returns.corr().to_numpy()
picture = axis.imshow(correlations, vmin=-1, vmax=1, cmap='RdBu_r')
axis.set_xticks(range(5), stock_names, rotation=30, ha='right')
axis.set_yticks(range(5), stock_names)
for row in range(5):
    for column in range(5):
        axis.text(column, row, f'{correlations[row, column]:.2f}', ha='center', va='center',
                  color='white' if abs(correlations[row, column]) > .65 else 'black')
fig.colorbar(picture, ax=axis, label='相关系数')
plt.show()
''', 'N03:10 moments and complete covariance output', 'fig-mc-nb-portfolio-correlation', '五只股票的日收益相关系数；主对角线为1。')
markdown(r'''
### 两种生成方式保留什么 {.unnumbered}

正态模拟从历史估计的联合分布抽取收益，不是人为另定均值和协方差。整行重抽样则直接抽取某个历史交易日的五个收益，同时保留当天股票间的联系。两种方法各生成100000组单日收益，再按同一组权重计算组合收益。

这一步只比较单日分布，并不保留跨日联系。多日持有期将在区块部分单独处理。
''')
code('''
portfolio_B = 100000
portfolio_normal_rng = np.random.default_rng(SEED)
portfolio_boot_rng = np.random.default_rng(SEED + 1)
portfolio_normal = portfolio_normal_rng.multivariate_normal(portfolio_mu, portfolio_cov, size=portfolio_B)
portfolio_rows = portfolio_boot_rng.integers(0, len(portfolio_values), size=portfolio_B)
portfolio_boot = portfolio_values[portfolio_rows]
portfolio_arrays = {
    'Historical': portfolio_values @ portfolio_weights,
    'Parametric MC': portfolio_normal @ portfolio_weights,
    'Bootstrap': portfolio_boot @ portfolio_weights,
}
np.savez_compressed(OUTPUT / 'portfolio-single-day.npz', **portfolio_arrays)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharex=True, layout='constrained')
distribution_edges = np.linspace(-.10, .10, 121)
for column, axis in enumerate(axes):
    for method, color, style in [('Historical', '#666666', '-'), ('Parametric MC', '#0072B2', '--'), ('Bootstrap', '#D55E00', ':')]:
        values = portfolio_arrays[method][:, column]
        counts, edges = np.histogram(values, bins=distribution_edges)
        axis.stairs(counts / len(values) / np.diff(edges), edges, label=method, color=color, linestyle=style)
    axis.set(title=portfolio_names[column], xlabel='单日收益率', ylabel='概率密度')
    axis.grid(alpha=.15)
axes[0].legend(frameon=False)
plt.show()
''', 'N03:10/12 sampling, frozen inputs', 'fig-mc-nb-portfolio-distributions', '同一组权重下的历史、正态模拟与整行重抽样单日组合收益分布。')
markdown(r'''
### 用 VaR 与 ES 比较尾部损失 {.unnumbered}

将损失定义为收益率的相反数，95% VaR是损失分布的95%分位数，95% ES是最差5%概率质量内的平均损失。样本数乘尾部概率不为整数时，边界观测按相应份额计权。以下表图均为单日损失率，表中换算为百分比。
''')
code('''
def portfolio_risk(values, alpha=.05):
    # 固定最差alpha的经验概率质量，不因相同取值而扩大尾部。
    losses = -np.asarray(values)
    ordered = np.sort(losses)[::-1]
    mass = len(losses) * alpha
    count = int(np.floor(mass))
    fraction = mass - count
    tail_sum = ordered[:count].sum()
    if fraction > 0:
        tail_sum += fraction * ordered[count]
    return float(np.quantile(losses, 1 - alpha)), float(tail_sum / mass)

portfolio_risk_rows = []
for method, values in portfolio_arrays.items():
    for column, portfolio in enumerate(['Equal-weight', 'Value-weight']):
        value95, es95 = portfolio_risk(values[:, column])
        value99, es99 = portfolio_risk(values[:, column], .01)
        portfolio_risk_rows.append({'portfolio': portfolio, 'method': method,
                                    'VaR_95': value95, 'ES_95': es95, 'VaR_99': value99, 'ES_99': es99})
portfolio_risks = pd.DataFrame(portfolio_risk_rows)
portfolio_risks.to_csv(OUTPUT / 'portfolio-risk-metrics.csv', index=False, encoding='utf-8-sig')
portfolio_main = portfolio_risks[['portfolio', 'method', 'VaR_95', 'ES_95']].copy()
portfolio_main[['VaR_95', 'ES_95']] *= 100
display(portfolio_main.rename(columns={'VaR_95': '95% VaR (%)', 'ES_95': '95% ES (%)'}))
fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout='constrained')
for column, portfolio in enumerate(['Equal-weight', 'Value-weight']):
    subset = portfolio_main[portfolio_main.portfolio == portfolio].set_index('method')
    positions = np.arange(3)
    axes[column].bar(positions-.18, subset.VaR_95, width=.36, label='95% VaR', color='#0072B2')
    axes[column].bar(positions+.18, subset.ES_95, width=.36, label='95% ES', color='#D55E00')
    axes[column].set_xticks(positions, ['历史', '正态模拟', '整行重抽样'])
    axes[column].set(title=portfolio_names[column], ylabel='单日损失率 (%)')
    axes[column].grid(axis='y', alpha=.15)
axes[0].legend(frameon=False)
plt.show()
''', 'N03 risk function and recalculated tables', 'fig-mc-nb-portfolio-risk', '95%单日VaR与ES，损失率以百分比表示。')
markdown(r'''
历史与正态模拟的VaR可能较接近，但ES仍可能有明显区别。应分别观察损失分位点与尾部平均损失，不能仅凭均值、方差接近就认为尾部风险也一致。

### 用区块抽样模拟多日组合收益 {.unnumbered #sec-mc-nb-block}

[返回正文：多日区块抽样](../../lectures/monte-carlo.qmd#sec-mc-portfolio)。

持有期限固定为20个交易日，期初按等权或市值权重配置，期间不调仓。区块长度取5、10、20日。候选窗口逐日移动且允许重叠，仅保留窗口内五只股票收益均有效的记录。

每种长度分别建立独立整行抽样对照，其日收益池由当前全部有效区块展开得到，保留窗口重叠引起的抽样权重。两种方式因而具有相同的单日经验抽样分布，区别主要在于是否成段保留连续记录。不同长度的有效窗口略有差异，应先在相同长度内比较。

先将每只股票逐日收益连乘得到期末价值，再按期初权重加总。不能把单日风险乘以根号20，或把权重改为每天再平衡来替代这个实验。
''')
code('''
def block_risk_metrics(values):
    ordered = np.sort(-values)[::-1]
    mass = len(values) * .05
    count = int(np.floor(mass))
    fraction = mass - count
    tail_sum = ordered[:count].sum()
    if fraction:
        tail_sum += fraction * ordered[count]
    return dict(mean=values.mean(), sd=values.std(ddof=1), q05=np.quantile(values, .05),
                VaR95=np.quantile(-values, .95), ES95=tail_sum / mass)

block_values = portfolio_returns.reindex(portfolio_prices.index).to_numpy()
block_horizon = 20
block_records, block_support, block_saved = [], [], {}
for block_length in [5, 10, 20]:
    starts = np.array([start for start in range(len(block_values)-block_length+1)
                       if np.isfinite(block_values[start:start+block_length]).all()])
    blocks = np.stack([block_values[start:start+block_length] for start in starts])
    assert block_horizon % block_length == 0 and np.isfinite(blocks).all()
    covered = np.unique((starts[:, None] + np.arange(block_length)).ravel())
    pool = blocks.reshape(-1, len(portfolio_returns.columns))
    block_support.append(dict(L=block_length, blocks=len(blocks), covered_days=len(covered), pool_size=len(pool)))
    for repetitions in [10000, 100000]:
        for seed in [20261017, 20261018, 20261019]:
            for method in ['iid', 'block']:
                # 保留原种子组合及分批大小，合并不会改变抽样次序。
                block_rng = np.random.default_rng(np.random.SeedSequence([seed, block_length, method == 'block']))
                outcomes = []
                for offset in range(0, repetitions, 10000):
                    batch = min(10000, repetitions-offset)
                    if method == 'block':
                        selected = block_rng.integers(len(blocks), size=(batch, block_horizon//block_length))
                        paths = blocks[selected].reshape(batch, block_horizon, len(portfolio_returns.columns))
                    else:
                        selected = block_rng.integers(len(pool), size=(batch, block_horizon))
                        paths = pool[selected]
                    outcomes.append(np.prod(1+paths, axis=1) @ portfolio_weights - 1)
                outcomes = np.concatenate(outcomes)
                assert outcomes.shape == (repetitions, 2) and np.isfinite(outcomes).all()
                for column, name in enumerate(portfolio_names):
                    block_records.append(dict(L=block_length, B=repetitions, seed=seed, method=method,
                                              portfolio=name, **block_risk_metrics(outcomes[:, column])))
                if repetitions == 100000 and seed == 20261017:
                    block_saved[f'L{block_length}_{method}'] = outcomes

block_metrics = pd.DataFrame(block_records)
block_main = block_metrics.query('B == 100000 and seed == 20261017')
block_metrics.to_csv(OUTPUT / 'block-metrics-all.csv', index=False, encoding='utf-8-sig')
np.savez_compressed(OUTPUT / 'block-returns.npz', **block_saved)
pd.DataFrame(block_support).to_csv(OUTPUT / 'block-support.csv', index=False, encoding='utf-8-sig')
block_display = []
for name in portfolio_names:
    for length in [5, 10, 20]:
        subset = block_main[(block_main.portfolio == name) & (block_main.L == length)].set_index('method')
        block_display.append({'组合': name, '区块长度': length,
                              '独立 VaR (%)': subset.loc['iid', 'VaR95']*100,
                              '区块 VaR (%)': subset.loc['block', 'VaR95']*100,
                              '独立 ES (%)': subset.loc['iid', 'ES95']*100,
                              '区块 ES (%)': subset.loc['block', 'ES95']*100})
display(pd.DataFrame(block_display).round(2))
''', 'accepted B20 core; repository data, original RNG and batches')
code('''
fig, axes = plt.subplots(2, 3, figsize=(12, 6.5), sharex=True, sharey=True, layout='constrained')
block_edges = np.linspace(-30, 45, 121)
for column, length in enumerate([5, 10, 20]):
    for portfolio, name in enumerate(portfolio_names):
        axis = axes[portfolio, column]
        for method, color, style, label in [('iid', '#0072B2', '--', '匹配独立抽样'), ('block', '#D55E00', '-', '区块抽样')]:
            values = block_saved[f'L{length}_{method}'][:, portfolio] * 100
            counts, edges = np.histogram(values, bins=block_edges)
            axis.stairs(counts/len(values)/np.diff(edges), edges, color=color, linestyle=style, label=label)
        axis.set(title=f'{name}，L={length}', xlim=(-30, 45))
        axis.axvline(0, color='.65', linewidth=.7)
        axis.grid(alpha=.15)
        if portfolio == 1:
            axis.set_xlabel('20日累计收益率 (%)')
        if column == 0:
            axis.set_ylabel('概率密度 (每个百分点)')
axes[0, 0].legend(frameon=False, fontsize=9)
plt.show()
''', 'accepted B20 main figure', 'fig-mc-nb-block-distributions', '每组100000条20日买入持有路径；各面板坐标和分箱一致。')
markdown('L=10时，等权组合区块抽样的VaR约为6.38%，ES约为8.79%。与匹配独立抽样比较，VaR较低而ES较高，说明两项指标需要分别阅读。保留连续关系不必然提高风险估计，也不能因某个长度得到较低风险就认定它最合适。')
supplement('案例三完整指标、窗口与稳定性核验')
markdown('以下保留72组区块指标、有效窗口、自相关和L=20完整窗口枚举。单日正态模拟的解析基准及忽略相关性的方差对照也在这里核对。表中原始风险值为收益率，正文与主表另乘100显示。')
code('''
with pd.option_context('display.max_rows', None):
    display(block_metrics)
display(pd.DataFrame(block_support))
display(block_metrics.groupby(['B', 'L', 'method', 'portfolio'])[['VaR95', 'ES95']].agg(['min', 'max']))
block_acf = []
for lag in [1, 5, 10, 20]:
    for stock in portfolio_returns.columns:
        series = pd.Series(block_values[:, list(portfolio_returns.columns).index(stock)], index=portfolio_prices.index)
        block_acf.append({'stock': stock, 'lag': lag, 'return_acf': series.autocorr(lag),
                          'squared_return_acf': series.pow(2).autocorr(lag)})
display(pd.DataFrame(block_acf))
exact_blocks = np.stack([block_values[start:start+20] for start in range(len(block_values)-19)
                         if np.isfinite(block_values[start:start+20]).all()])
exact_returns = np.prod(1+exact_blocks, axis=1) @ portfolio_weights - 1
exact_table = pd.DataFrame([{'portfolio': name, **block_risk_metrics(exact_returns[:, column])}
                            for column, name in enumerate(portfolio_names)])
exact_table.to_csv(OUTPUT / 'block-L20-exact.csv', index=False, encoding='utf-8-sig')
display(exact_table)
analytic_rows = []
for column, name in enumerate(portfolio_names):
    weights = portfolio_weights[:, column]
    mean = portfolio_mu @ weights
    deviation = np.sqrt(weights @ portfolio_cov @ weights)
    analytic_rows.append({'组合': name, '解析正态95%VaR': -mean+norm.ppf(.95)*deviation,
                          '解析正态95%ES': -mean+norm.pdf(norm.ppf(.95))/.05*deviation,
                          '忽略相关性标准差': np.sqrt(weights @ np.diag(np.diag(portfolio_cov)) @ weights),
                          '保留相关性标准差': deviation})
display(pd.DataFrame(analytic_rows))
portfolio_stability = []
for stability_seed in [SEED+10, SEED+20, SEED+30]:
    normal_rng = np.random.default_rng(stability_seed)
    bootstrap_rng = np.random.default_rng(stability_seed+1)
    normal_paths = normal_rng.multivariate_normal(portfolio_mu, portfolio_cov, size=500000) @ portfolio_weights
    bootstrap_paths = portfolio_values[bootstrap_rng.integers(0, len(portfolio_values), size=500000)] @ portfolio_weights
    for size in [10000, 50000, 100000, 500000]:
        for method, values in [('Parametric MC', normal_paths), ('Bootstrap', bootstrap_paths)]:
            for column, name in enumerate(['Equal-weight', 'Value-weight']):
                value95, es95 = portfolio_risk(values[:size, column])
                portfolio_stability.append({'seed': stability_seed, 'B': size, 'portfolio': name,
                                            'method': method, 'VaR_95': value95, 'ES_95': es95})
portfolio_stability = pd.DataFrame(portfolio_stability)
portfolio_stability.to_csv(OUTPUT / 'portfolio-stability.csv', index=False, encoding='utf-8-sig')
display(portfolio_stability.groupby(['B', 'portfolio', 'method'])[['VaR_95', 'ES_95']].agg(['min', 'max']))
case_results['portfolio'] = {'daily_risk_rows': len(portfolio_risks), 'block_metric_rows': len(block_metrics),
                              'sample_rows': len(portfolio_returns), 'block_support': block_support}
''')
code('''
fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True, layout='constrained')
for portfolio, name in enumerate(portfolio_names):
    for length, color in [(5, '#0072B2'), (10, '#D55E00'), (20, '#009E73')]:
        for method, style in [('iid', '--'), ('block', '-')]:
            values = np.sort(block_saved[f'L{length}_{method}'][:, portfolio]) * 100
            indices = np.arange(0, int(len(values)*.12), 10)
            axes[portfolio].plot(values[indices], (indices+1)/len(values)*100, color=color, linestyle=style,
                                  label=f'L={length}，' + ('区块' if method == 'block' else '独立'))
    axes[portfolio].axhline(5, color='.5', linewidth=.8)
    axes[portfolio].set(title=name, xlabel='20日累计收益率 (%)', xlim=(-25, 0), ylim=(0, 12))
axes[0].set_ylabel('累计概率 (%)')
axes[1].legend(frameon=False, fontsize=9, ncol=2)
plt.show()
''', 'B20 supplementary left tail', 'fig-mc-nb-block-tail', '左尾经验分布。5%横线对应的收益率取负可读出95% VaR。')
close_supplement()

markdown(r'''
## 案例四：从随机变量到随机过程 {.unnumbered #sec-mc-nb-process}

[返回正文：案例四](../../lectures/monte-carlo.qmd#sec-mc-process)。

本例关注期末上涨与途中跌破阈值两类事件。二者都从价格路径计算，但回答不同问题。下面依次用随机游走说明冲击累积、用布朗运动说明时间尺度，再用GBM保持价格为正。

### 随机游走 {.unnumbered}

每一步给前值增加一个独立冲击，从0开始逐步累加。该例的横轴是离散步数，冲击标准差设为1，不把它误当作已经按年化尺度设置的资产收益模型。
''')
code(old('process', 4), 'N04:4', 'fig-mc-nb-random-walk', '独立冲击逐步累积形成的随机游走路径。')
markdown(r'''
### 布朗运动 {.unnumbered}

在一年划分252个时间步的网格上，布朗增量方差为每步长度 $\Delta t$，标准差为 $\sqrt{\Delta t}$。不重叠区间的增量独立。下图展示20条路径，后面单独抽取100000个终点检查均值与标准差。
''')
code(old('process', 6), 'N04:6', 'fig-mc-nb-brownian', '一年时间网格上的布朗运动路径。')
code(old('process', 7), 'N04:7')
markdown(r'''
### 几何布朗运动 {.unnumbered}

GBM 通过对数价格的变化生成价格路径。漂移率为 0.08，下面分别取年化波动率 0.10 和 0.35，各画 30 条路径。两组使用不同种子，不能将图中任意两条线当作共用冲击的配对比较。指数表达式计算的是网格上的精确转移，不是 Euler 价格更新。
''')
code(old('process', 9), 'N04:9', 'fig-mc-nb-gbm', ['较低年化波动率下的GBM路径。', '较高年化波动率下的GBM路径。'])
markdown(r'''
### 终值风险和路径风险 {.unnumbered}

主风险实验单独设定初始价格100元、漂移率0.08、波动率0.30、期限1年、252步、5000条路径，阈值为75元。三个事件分别是期末价格高于100、网格价格曾严格低于75，以及两者同时发生。下面补齐各事件的计数，概率分母全部为5000。

这不是止损交易模拟，也不是最大回撤。统计仅监测离散网格时点，不保证捕捉时点之间的连续越界。
''')
code(old('process', 11), 'N04:11')
code('''
path_events = pd.DataFrame({
    '事件': ['期末上涨', '网格中曾跌破75', '期末上涨且网格中曾跌破75'],
    '计数': [int((terminal > S0).sum()), int(hit_barrier.sum()), int(((terminal > S0) & hit_barrier).sum())],
})
path_events['分母'] = n_paths
path_events['概率 (%)'] = path_events['计数'] / n_paths * 100
display(path_events)
path_events.to_csv(OUTPUT / 'path-events.csv', index=False, encoding='utf-8-sig')
case_results['path_risk'] = {'B': int(n_paths), 'counts': path_events['计数'].tolist(),
                             'parameters': {'S0': float(S0), 'mu': float(mu), 'sigma': float(sigma),
                                             'T': float(T), 'N': int(N), 'barrier': float(barrier)}}
''')
markdown('期末上涨的路径仍可能在途中跌破75元。按本页设定，两类单独事件和联合事件分别约为54.98%、28.04%和2.66%。第三项不是以期末上涨路径为分母的条件概率。')
supplement('扩展阅读：Monte Carlo 期权定价')
markdown(r'''
欧式看涨期权到期支付为 $\max(S_{T}-K,0)$，只与终值有关，因此本例直接模拟终值，不必生成完整路径。风险中性分布的漂移使用无风险利率，不能将其中的上涨概率解释为现实发生概率。

本段独立设置初始价与执行价均为100元、连续复利无风险年利率0.05、年化波动率0.20、期限1年。参数与上面的路径风险实验不同。先计算折现支付的平均值，再用其标准差除以样本数平方根得到MC标准误，并与同一模型下的Black–Scholes闭式价格比较。
''')
code(old('process', 13), 'N04:13')
code('''
pricing_B = 100000
pricing_rng = np.random.default_rng(SEED)
pricing_shocks = pricing_rng.normal(size=pricing_B)
pricing_terminal = S0 * np.exp((r-.5*sigma**2)*T + sigma*np.sqrt(T)*pricing_shocks)
discounted_payoff = np.exp(-r*T) * np.maximum(pricing_terminal-K, 0)
pricing_mcse = discounted_payoff.std(ddof=1) / np.sqrt(pricing_B)
assert np.isclose(discounted_payoff.mean(), mc_price)
display(pd.Series({'MC价格': mc_price, '闭式价格': bs_price, 'MC标准误': pricing_mcse,
                   'MC减闭式': mc_price-bs_price}))
case_results['option'] = {'MC': float(mc_price), 'closed_form': float(bs_price), 'MCSE': float(pricing_mcse)}
''', 'accepted pricing MCSE check')
code(old('process', 14), 'N04:14')
code(old('process', 15), 'N04:15', 'fig-mc-nb-option-convergence', '不同重复次数下MC价格与闭式价格比较，误差不要求单调下降。')
markdown('本参数下MC价格约为10.4165，闭式价格约为10.4506，MC标准误约为0.0463。这个对照用于核验计算，并不证明真实资产价格符合GBM。')
close_supplement()
markdown(r'''
## 结果保存与返回正文 {.unnumbered #sec-mc-nb-output}

本页各案例的参数和随机数设置相互明确区分。完整结果文件保存在开头指定的输出目录，不改输入数据。课前从头运行并保存Notebook，课堂可以直接通过目录跳转阅读，不需要现场重新计算。

[返回理论正文](../../lectures/monte-carlo.qmd)。模型选择、设计检查和全章总结仍以理论章为主，不在这里重复展开。
''')
code('''
(OUTPUT / 'run-summary.json').write_text(json.dumps(case_results, ensure_ascii=False, indent=2), encoding='utf-8')
display(pd.DataFrame([{'案例': name, '已保存': True} for name in case_results]))
''')


def apply_sources(output):
    cells.insert(0, nbformat.v4.new_raw_cell('---\ntitle: "# Monte Carlo 模拟：案例与代码 {.unnumbered}"\nnumber-sections: false\n---'))
    for item in mapping:
        item['cell'] += 1
    launcher = Path(subprocess.check_output(
        ['powershell', '-NoProfile', '-Command', '(Get-Command apply_patch).Source'], text=True).strip())
    relative = re.search(r'"%~dp0([^"\n]+codex.exe)"', launcher.read_text()).group(1)
    backend = (launcher.parent / relative).resolve()
    notebook = nbformat.read(TARGET, as_version=4)
    previous_cells = notebook.cells
    for index, cell in enumerate(cells):
        cell['id'] = f'mc-cases-{index:03d}'
        if index < len(previous_cells) and cell.cell_type == previous_cells[index].cell_type == 'code':
            cell.outputs = previous_cells[index].outputs
            cell.execution_count = previous_cells[index].execution_count
    notebook.cells = cells
    notebook.metadata = {
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python', 'version': '3.11'},
    }

    def apply(notebook):
        before = TARGET.read_text(encoding='utf-8')
        after = nbformat.writes(notebook)
        differences = list(difflib.unified_diff(before.splitlines(), after.splitlines(), n=3, lineterm=''))
        if not differences:
            return
        hunks = []
        for line in differences[2:]:
            if line.startswith('@@'):
                hunks.append(['@@'])
            else:
                hunks[-1].append(line)
        for hunk in hunks:
            patch = '*** Begin Patch\n*** Update File: ' + str(TARGET) + '\n' + '\n'.join(hunk) + '\n*** End Patch\n'
            if len(patch) > 30000:
                raise ValueError('Source patch exceeds Windows safe command length')
            subprocess.run([str(backend), '--codex-run-as-apply-patch', patch], check=True, cwd=ROOT,
                           stdout=subprocess.DEVNULL)

    apply(notebook)
    actual = nbformat.read(TARGET, as_version=4)
    assert [cell.source for cell in actual.cells] == [cell.source for cell in cells]
    output.mkdir(parents=True, exist_ok=True)
    (output / 'source-map.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Built {len(cells)} cells; code cells: {sum(cell.cell_type == "code" for cell in cells)}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'logs/monte-carlo/site-update-20261019')
    arguments = parser.parse_args()
    apply_sources(arguments.output_dir.resolve())
