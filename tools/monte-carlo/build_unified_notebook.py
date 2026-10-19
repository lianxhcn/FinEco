from pathlib import Path
import argparse
import json
import re
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


def code(source, origin='new', label=None, caption=None, hidden=False, folded=False):
    source = textwrap.dedent(source).strip()
    if label:
        options = f'#| label: {label}\n'
        if caption:
            options += '#| fig-cap: ' + json.dumps(prose_spacing(caption), ensure_ascii=False) + '\n'
        source = options + source
    if hidden:
        source = '#| include: false\n' + source
    elif folded:
        source = '#| code-fold: true\n#| code-summary: "展开运行准备代码"\n' + source
    cells.append(nbformat.v4.new_code_cell(source))
    mapping.append({'cell': len(cells) - 1, 'origin': origin})


def old(book, index):
    return BOOKS[book].cells[index].source.strip()


def supplement(title):
    markdown(f'::: {{.callout-note collapse="true" title="{title}"}}')


def close_supplement():
    markdown(':::')


markdown(r'''
本页集中展示基础抽样与四个案例的代码、运行结果和解读，可按目录直接阅读。各案例开头的链接通向正文的相应小节。

## 阅读与运行说明 {.unnumbered #sec-mc-nb-guide}

本地复现请在完整课程仓库中打开同名 Notebook，从第一个代码单元依次运行。所需环境包括 NumPy、pandas、Matplotlib、SciPy 和 statsmodels，配置方法见[软件配置](../../settings.qmd)。下方代码统一导入工具、设置图形样式并指定输出目录，各案例随后设置自己的参数与随机数发生器。

案例一、二、四使用教学模拟。案例三读取仓库 `data/monte-carlo/` 中的配套数据，无需重新下载行情。生成文件写入 `output/monte-carlo/cases/`，不修改输入数据。各案例的折叠部分提供补充分析，可按需展开。
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
from matplotlib.ticker import PercentFormatter
from scipy.stats import norm
import statsmodels.api as sm
from statsmodels.sandbox.regression.gmm import IV2SLS
from IPython.display import display, Image, HTML

def show_table(frame, labels=None, percentages=(), digits=3):
    # 展示表使用易读名称与单位，原始数组和导出字段保持不变。
    table = frame.copy()
    for column in percentages:
        table[column] = table[column] * 100
    if labels:
        table = table.rename(columns=labels)
    display(HTML(table.to_html(index=False, border=0,
                              float_format=lambda value: f'{value:.{digits}f}')))

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
show_table(pd.DataFrame({'项目': ['Python', 'NumPy', 'pandas', '基准种子'],
                         '设置': [platform.python_version(), np.__version__, pd.__version__, str(SEED)]}))
''', folded=True)
code('case_results = {}', hidden=True)
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
    '指数分布 (均值 1)': distribution_rng.exponential(scale=1, size=10000),
}
fig, axes = plt.subplots(1, 3, figsize=(12, 3.7), layout='constrained')
for axis, (name, sample) in zip(axes, distribution_samples.items()):
    axis.hist(sample, bins=45, density=True, alpha=.65, color='#0072B2')
    axis.set(title=name, xlabel='取值', ylabel='概率密度')
    axis.grid(alpha=.15)
plt.show()
''', label='fig-mc-nb-three-distributions', caption='三种概率分布的抽样对照。各生成10000个值，保留各分布适合的横轴范围，不用图形宽度直接比较波动大小。')
code('''
distribution_summary = pd.DataFrame({name: {'样本均值': values.mean(), '样本标准差': values.std(ddof=1)}
                                     for name, values in distribution_samples.items()}).T
show_table(distribution_summary.rename_axis('分布').reset_index())
''')
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
show_table(pd.DataFrame({'指标': ['均值', '标准差'],
                         '模拟结果': [exponential_values.mean(), exponential_values.std(ddof=1)],
                         '理论值': [1.0, 1.0]}))
''')
markdown(r'''
### 随机种子、DGP 与重复次数 {.unnumbered}

相同的发生器、种子和调用顺序可以产生相同序列。下面分别初始化两个发生器，比较它们生成的前五个标准正态数。

数据生成过程 (data-generating process, DGP) 规定模拟变量如何产生，以及它们之间的关系和依赖设定。案例一将完整演示如何生成解释变量、扰动项和因变量，再通过重复估计观察估计量的表现。这里先区分：$n$ 是每次回归所用的样本量，$B$ 是重复生成样本并估计的次数。
''')
code(old('basics', 7).replace('pd.DataFrame({"run_1": a, "run_2": b, "same": a == b})',
     "show_table(pd.DataFrame({'第一次生成': a, '第二次生成': b, '两次之差': a - b}))"), 'N00:7')
supplement('补充核验：用模拟均值近似一个已知期望')
markdown(r'设 $X\sim N(0,1)$，则 $E(X^{2})=1$。随着抽样数量增加，样本平方的平均值通常更接近该期望，单条随机序列不要求误差单调下降。')
code(old('basics', 9).replace('pd.DataFrame({', 'running_summary = pd.DataFrame({') +
     "\nshow_table(running_summary, {'B': '抽样数量 B', 'MC_estimate': '模拟均值', 'error': '与理论值之差'})", 'N00:9')
code(old('basics', 10).replace('Monte Carlo repetitions B (log scale)', '抽样数量 B (对数刻度)')
     .replace('Running estimate of E[X^2]', '平方的累计平均值')
     .replace('Monte Carlo estimate converges as B increases', '用样本平方的平均值近似理论期望'),
     'N00:10', 'fig-mc-nb-running-mean', '标准正态平方的累计平均值与理论期望1。')
close_supplement()


markdown(r'''
## 案例一：用模拟理解计量性质 {.unnumbered #sec-mc-nb-econometrics}

[返回正文：案例一](../../lectures/monte-carlo.qmd#sec-mc-econometrics)。

本例在已知参数真值的 DGP 中，考察普通最小二乘法 (OLS) 与工具变量法 (IV) 的估计表现。OLS 部分采用 $Y_{i}=1+2X_{i}+u_{i}$，其中 $X_{i}$ 为解释变量，$u_{i}$ 为扰动项，二者相互独立且均服从标准正态分布，不同观测之间也独立。每次重新生成整个样本，再估计和保存斜率。

### OLS 的无偏性 {.unnumbered}

固定 $n=100$，重复 $B=5000$ 次。输出均值与真值 2 的差作为 MC 偏差，不能把一次估计或有限次均值当作无偏性的证明。
''')
code(old('ols', 4).replace('pd.Series({', 'unbiased_summary = pd.Series({') +
     "\nshow_table(unbiased_summary.rename_axis('指标').rename('数值').reset_index().replace("
     "{'true_beta': '参数真值', 'mean_beta_hat': '估计均值', 'bias': 'MC 偏差', 'empirical_sd': '经验标准差'}), digits=6)", 'N01:4')
code(old('ols', 5).replace(r'$\hat{\beta}_{1}$ 的 OLS 估计值', r'$\beta_{1}$ 的 OLS 估计值'),
     'N01:5', 'fig-mc-nb-ols-unbiased', 'OLS无偏性：估计分布、参数真值与MC均值。')
markdown(r'''
模拟得到的估计均值约为 2.001526，与真值 2 接近。图中估计值分布在真值线两侧，平均偏离约为 0.001526。有限次模拟与无偏性的理论结论相符，但不能代替数学证明。

### OLS 的一致性 {.unnumbered}

保持 DGP 不变，改变每次回归的样本量，各组重复 3000 次。左图比较估计分布，右图和表比较经验标准差。图形只使用统一显示窗口，没有将窗口外的估计值从统计量中删除。
''')
code(old('ols', 7).removesuffix('ols_summary') +
     "show_table(ols_summary, {'n': '样本量 n', 'mean_beta_hat': '估计均值', 'bias': 'MC 偏差', 'empirical_sd': '经验标准差'})", 'N01:7')
code(old('ols', 8).replace(r'$\hat{\beta}_{1}$ 的 OLS 估计值', r'$\beta_{1}$ 的 OLS 估计值'),
     'N01:8', 'fig-mc-nb-ols-consistency', 'OLS一致性：不同样本量下的估计分布与经验标准差。')
markdown('样本量由 20 增至 2000 时，估计值的经验标准差由约 0.244 降至 0.023，分布也更集中于真值 2 附近。这里增加的是每次回归使用的观测数，各组重复次数均为 3000。有限组样本量的比较展示了一致性所预期的变化，但不证明其极限性质。')
markdown(r'''
### IV：内生性与弱工具变量 {.unnumbered}

本例生成 $Y=\beta X+\gamma W+u$ 和 $X=\pi Z+\delta u+v$。其中 $X$ 是需要估计其影响的解释变量，$W$ 是外生控制变量，$Z$ 是工具变量，$u$、$v$ 是两项扰动。$Z,W,u,v$ 相互独立且均服从标准正态分布，不同观测之间也独立。参数真值为 $\beta=\gamma=1$。

$\delta$ 控制 $X$ 中来自 $u$ 的部分，非零时使 $X$ 与结果方程的扰动相关，产生内生性。$\pi$ 控制工具变量与 $X$ 的相关性。$Z$ 与 $u$ 独立且不直接进入结果方程，IV 利用 $Z$ 引起的 $X$ 变动估计 $\beta$。每个样本同时计算 OLS 与 IV，便于比较。

#### 改变内生性 {.unnumbered}

固定 $n=500$、$B=1200$ 和 $\pi=1$，改变 $\delta$。下面先定义生成与估计函数，再比较两种估计均值。
''')
code(old('ols', 10).replace('# IV2SLS: regressors = [const, x, w], instruments = [const, z, w]',
     '# 2SLS 的解释变量为常数项、X、W，工具变量为常数项、Z、W。'), 'N01:10')
code(old('ols', 12).removesuffix('pd.DataFrame(summary_b1)') +
     "show_table(pd.DataFrame(summary_b1), {'delta': '内生性参数 δ', 'method': '估计方法', 'mean': '估计均值', 'bias': 'MC 偏差', 'sd': '经验标准差', 'rmse': '均方根误差'})", 'N01:12')
code(old('ols', 13), 'N01:13', 'fig-mc-nb-iv-endogeneity', '固定工具变量相关性，比较内生性变化下的OLS与IV均值。')
markdown(r'随着 $\delta$ 从 0 增至 0.8，OLS 估计均值由约 0.999 升至 1.303，而 IV 估计均值仍接近真值 1。表中的均方根误差是估计误差平方平均值的平方根，同时反映偏差和离散程度。本组实验的工具变量较强，IV 对内生性的处理较稳定，但这不意味着 IV 在有限样本中必然无偏。')
markdown(r'''
#### 减弱工具变量相关性 {.unnumbered}

固定 $\delta=0.5$，依次降低 $\pi$，其余设置不变。下图为经验累积分布 (ECDF)：横轴给定一个估计值，纵轴表示不超过该值的估计结果所占比例。两图都以全部 1200 次估计为分母，左图保留极端估计，右图放大真值附近。
''')
code(old('ols', 15).removesuffix('pd.DataFrame(summary_b2)') +
     "show_table(pd.DataFrame(summary_b2), {'pi': '工具变量参数 π', 'mean_iv': 'IV 估计均值', 'bias_iv': 'MC 偏差', 'sd_iv': '经验标准差', 'rmse_iv': '均方根误差', 'q01': '1% 分位数', 'q99': '99% 分位数'})", 'N01:15')
code(old('ols', 16), 'N01:16', 'fig-mc-nb-iv-weak', '弱工具变量的完整经验分布及局部放大。')
markdown(r'当 $\pi=1$ 时，IV 估计值的 1% 与 99% 分位数约为 0.887 和 1.101。降至 $\pi=0.05$ 后，两者约为 -13.637 和 23.416，极端估计明显增多。此时均值容易受少数结果影响，需要结合完整分布与分位数判断估计的稳定程度。')
source = old('ols', 23).replace("Path(os.environ.get('FINECO_CASE1_EXPORT', 'output/monte-carlo/case1'))", "OUTPUT / 'case1'")
source = source[:source.index('display(ols_summary)')]
code(source, 'N01:23 export', hidden=True)
code("case_results['case1'] = {'mean': float(bhat_100.mean()), 'bias': float(bhat_100.mean()-2), 'arrays': len(arrays)}", hidden=True)

markdown(r'''
## 案例二：项目估值 {.unnumbered #sec-mc-nb-valuation}

[返回正文：案例二](../../lectures/monte-carlo.qmd#sec-mc-valuation)。

企业选择价格后，由年度需求冲击生成市场份额，再沿销量、收入和现金流关系计算项目 NPV。价格是决策变量，需求冲击和贴现率是不确定性因素，市场份额及 NPV 是模型计算结果。

本例期限为 10 年，年度潜在市场规模为 100 万件，初始投资 3500 万元，年度固定支出 600 万元，现金流转化比例为 0.28。需求冲击标准差为 0.55。贴现率设为 $r=0.05+0.07X_{r}$，其中 $X_{r}\sim Beta(3,4)$。每个情景使用一个贴现率，需求冲击按年独立抽取。金额计算使用元，NPV 表和图使用百万元。

实际应用中，市场规模可结合行业资料与市场调研估算，现金流比例与固定支出需参考财务记录，价格敏感性则需要历史销售或试销资料支持。本页参数为教学设定，不是这些资料的实证估计。

### 经营关系与参数 {.unnumbered}

将价格 $p$ 固定在规划期内，各年的市场份额按下式生成：

$$
s_{t}=\Lambda\!\left[\alpha-\beta\log(p/\bar p)+\varepsilon_{t}\right],
\qquad \Lambda(x)=\frac{e^{x}}{1+e^{x}}.
$$ {#eq-mc-nb-valuation-share}

其中，$\bar p=100$ 为市场参考价格，$\alpha=-0.4$ 决定参考价格且无冲击时的份额水平，$\beta=2.2$ 控制价格敏感性，$\varepsilon_{t}\sim N(0,0.55^{2})$ 为年度需求冲击。价格提高会压低份额，logistic 变换则保证份额在 0 与 1 之间。代码中的 `p_ref` 和 `beta_price` 分别对应 $\bar p$ 和 $\beta$。

市场份额乘以年度潜在市场规模 $Q_{0}$ 得到销量，再乘以价格得到收入。自由现金流为 $FCF_{t}=mpQ_{0}s_{t}-F$，其中 $m=0.28$ 为现金流转化比例，$F$ 为年度固定支出。NPV 为未来十年各年末现金流的现值之和减去初始投资 $I_{0}$：

$$
NPV=-I_{0}+\sum_{t=1}^{10}\frac{FCF_{t}}{(1+r)^{t}}.
$$ {#eq-mc-nb-valuation-npv}

`simulate_project` 在函数内初始化发生器。比较价格时使用相同种子和相同的抽样步骤，使各方案面对同一批需求冲击和贴现率。
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
code(old('valuation', 6).removesuffix('summary') + '''
baseline_display = summary.loc[['Price', 'Mean NPV (million)', 'P(NPV > 0)',
                                'NPV 5% quantile (million)']].copy()
baseline_display.loc['P(NPV > 0)'] *= 100
baseline_display.index = ['产品价格 (元)', '平均 NPV (百万元)',
                          'NPV 为正的概率 (%)', 'NPV 的 5% 分位数 (百万元)']
show_table(baseline_display.rename_axis('指标').rename('数值').reset_index())
''', 'N02:6')
code(old('valuation', 7), 'N02:7', 'fig-mc-nb-valuation-npv', '价格80元下的NPV分布与经验累积分布。')
markdown('平均 NPV 约为 3.188 百万元，正 NPV 的情景占 68.365%，但 NPV 的 5% 分位数为 -7.493 百万元。图中仍有相当一部分情景落在零的左侧，因此平均价值为正并不意味着下行损失可以忽略。正 NPV 表示该情景下未来现金流现值超过初始投资，满足净现值投资标准。')
markdown(r'''
### 从 NPV 分布进入价格决策 {.unnumbered}

候选价格从55到160元，间隔5元。每个价格使用同样的模拟次数和随机输入，以便比较价格改变后的经营结果。下表同时列出平均 NPV、正 NPV 概率和 NPV 的 5% 分位数，分别对应预期价值、满足投资标准的可能性和下行风险。
''')
source = old('valuation', 9).replace('rows = []', 'valuation_cache = {float(price): simulate_project(price) for price in price_grid}\nrows = []').replace('result = simulate_project(p)', 'result = valuation_cache[float(p)]')
source = source.removesuffix('price_results') + '''
show_table(price_results[['price', 'mean_npv_million', 'prob_positive', 'npv_5pct_million']],
           {'price': '价格 (元)', 'mean_npv_million': '平均 NPV (百万元)',
            'prob_positive': 'NPV 为正的概率 (%)', 'npv_5pct_million': '5% 分位数 (百万元)'},
           percentages=['prob_positive'])
'''
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

给定价格和贴现率，项目需要达到多大的市场份额，才能使 NPV 不低于零？令 $A(r,T)=\sum_{t=1}^{T}(1+r)^{-t}$ 为年金现值因子。当每年的份额相同，使 NPV 恰好为零的临界份额为

$$
s^{*}(p,r)=\frac{F+I_{0}/A(r,T)}{mpQ_{0}}.
$$ {#eq-mc-nb-valuation-threshold}

年度份额随冲击变化时，应按贴现系数计算加权平均份额 $\widetilde{s}(r)$，才能与同一情景的投资门槛比较：

$$
\widetilde{s}(r)=\frac{\sum_{t=1}^{T}s_{t}(1+r)^{-t}}{A(r,T)},
\qquad
NPV=mpQ_{0}A(r,T)\left[\widetilde{s}(r)-s^{*}(p,r)\right].
$$ {#eq-mc-nb-valuation-weighted-share}

前面的乘数均为正，因此加权份额高于门槛时 NPV 为正，低于门槛时 NPV 为负。这里各年份的高份额出现得越早，对现值的贡献越大，简单平均份额不能代替贴现加权份额。

下图边界带来自贴现率上下限，不是置信区间。左图每价选250个情景显示，右图显示基准价格的全部20000个情景。
''')
code(old('valuation', 12), 'N02:12')
code(old('valuation', 14), 'N02:14', 'fig-mc-nb-valuation-boundary', '贴现加权份额与NPV=0门槛的对应关系。')
supplement('补充分析：经营条件变差后，项目是否仍值得投资')
markdown('保持价格为 80 元，分别降低市场规模、提高固定支出和调整贴现率分布，其余条件不变。三种不利条件分别进行模拟，不同时叠加，以便分辨各自的影响。')
code(old('valuation', 16).removesuffix('stress_results') + '''
stress_display = stress_results.replace({'Baseline': '基准情景', 'Market size -15%': '市场规模下降 15%',
                                         'Fixed cost +20%': '固定支出增加 20%',
                                         'Higher discount rates': '贴现率整体提高'})
show_table(stress_display, {'scenario': '情景', 'mean_npv_million': '平均 NPV (百万元)',
                           'prob_positive': 'NPV 为正的概率 (%)',
                           'npv_5pct_million': '5% 分位数 (百万元)'}, percentages=['prob_positive'])
''', 'N02:16')
markdown('本例中，市场规模下降 15% 后，平均 NPV 由约 3.188 降至 -8.592 百万元，正 NPV 概率降至 6.120%。固定支出增加或贴现率提高也使平均 NPV 转为负值。这说明基准情景的正平均价值依赖经营条件，增加模拟次数并不能消除这些风险。')
close_supplement()
code(old('valuation', 18).removesuffix('diagnostics'), 'N02:18', hidden=True)
source = old('valuation', 20).replace("Path(os.environ.get('FINECO_VALUATION_EXPORT', 'output/monte-carlo/valuation'))", "OUTPUT / 'valuation'").replace('scenario = simulate_project(price)', 'scenario = valuation_cache[float(price)]').replace('display(decision_results)\n', '')
source = source[:source.index('display(weighted_checks)')]
code(source, 'N02:20, reuse cache', hidden=True)
supplement('补充分析：相同平均份额为什么会得到不同 NPV')
markdown('设前五年的市场份额为 0.8、后五年为 0.2，再将两段对调。两条经营记录的简单平均份额均为 0.5，但较早收到的现金流折现较少。下面固定价格为 80 元、贴现率为 8%，比较两种记录。')
code('''
show_table(counterexample, {'example': '经营记录', 'arithmetic_share': '简单平均份额 (%)',
                            'weighted_share': '贴现加权份额 (%)', 'critical_share': '临界份额 (%)',
                            'npv_million': 'NPV (百万元)'},
           percentages=['arithmetic_share', 'weighted_share', 'critical_share'])
''')
markdown('较高份额出现在前五年时，NPV 约为 8.463 百万元；出现在后五年时，NPV 约为 -8.678 百万元。两种记录的简单平均份额相同，贴现加权份额却分别位于临界份额两侧。投资门槛必须与现金流时序相匹配。')
code('''
show_table(pd.DataFrame({'检查': ['逐年贴现与加权份额公式的最大差值 (元)',
                                '两种算法对 NPV 正负分类的不同次数'],
                         '结果': [audit['max_identity_error'], audit['weighted_sign_mismatches']]}), digits=8)
''')
markdown(r'在全部 22 个价格各 20000 个情景中，两种算法对 NPV 正负的判断完全一致。金额的最大差值约为 $6\times10^{-8}$ 元，属于浮点计算误差，不是项目损失或模型误差。')
close_supplement()
supplement('补充分析：更换种子后，价格比较是否稳定')
markdown('保持模型与价格网格不变，换用三个种子，分别寻找使三项指标最高的价格。该比较检查有限次模拟的数值波动，不是对需求参数或未来项目价值建立置信区间。')
source = old('valuation', 22)
source = source[:source.index('display(seed_peaks)')]
code(source + '''
peak_prices = seed_peaks.pivot(index='seed', columns='metric', values='price').reset_index()
show_table(peak_prices, {'seed': '随机种子', 'mean_npv_million': '平均 NPV 最高的价格 (元)',
                        'prob_positive': '正 NPV 概率最高的价格 (元)',
                        'npv_5pct_million': '5% 分位数最高的价格 (元)'}, digits=0)
show_table(pd.DataFrame({'指标': ['80 元与 75 元方案的正 NPV 概率之差', '该差值的配对 MC 标准误'],
                         '数值 (百分点)': paired_probability_check.to_numpy() * 100}))
''', 'N02:22')
markdown('三个种子下，平均 NPV 与正 NPV 概率最高的价格均为 80 元，5% 分位数最高的价格均为 70 元。不过，基准种子下 80 元与 75 元的正 NPV 概率只相差约 0.140 个百分点，其配对 MC 标准误约为 0.069 个百分点。相邻方案差距较小时，仍应关注模拟精度。')
close_supplement()
code("case_results['valuation'] = audit", hidden=True)

markdown(r'''
## 案例三：用真实数据校准组合风险模型 {.unnumbered #sec-mc-nb-portfolio}

[返回正文：案例三](../../lectures/monte-carlo.qmd#sec-mc-portfolio)。

前两例预先设定了生成机制。本例根据五只股票的历史收益估计均值、波动和共同变化，再生成模拟收益率，估计组合可能面临的损失。单日分析比较多元正态模拟与历史整行重抽样，多日分析再引入区块抽样。各方法使用相同的两组组合权重，便于观察生成方式怎样影响损失分布。

### 数据、股票池与组合权重 {.unnumbered}

股票为招商银行、长江电力、万科A、格力电器和比亚迪。共同有效日收益覆盖2016-09-05至2026-09-30，共2397日。日收益由后复权价格计算。等权组合各占20%，市值权重使用2026-09-30五只股票总市值的相对比例，比较方法时不改变权重。

下面读取仓库处理后数据。价格文件保留原始日期和缺失位置，用于识别连续区块；收益文件只包含共同有效日。筛选有效日后，部分相邻记录之间可能隔着缺失收益的交易日，构造区块时需要识别这些间断。数据来源、收益计算和缺失值处理规则见[数据说明](../../resources/monte-carlo/portfolio-report.md)。样本末日的市值权重仅用于固定配置下的方法比较，不代表历史可投资策略的回测。
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
show_table(pd.DataFrame({'共同有效日数': [len(portfolio_returns)],
                         '原始价格日期数': [len(portfolio_prices)],
                         '样本开始': [str(portfolio_returns.index.min().date())],
                         '样本结束': [str(portfolio_returns.index.max().date())]}))
show_table(portfolio_weight_table[['name', 'sector', 'equal_weight', 'value_weight', 'reference_date']],
           {'name': '股票', 'sector': '行业', 'equal_weight': '等权配置 (%)',
            'value_weight': '市值配置 (%)', 'reference_date': '权重基准日'},
           percentages=['equal_weight', 'value_weight'], digits=2)
''', 'N03 data entry refactored to frozen repository CSVs')
markdown(r'''
### 用历史数据设定联合分布 {.unnumbered}

收益表每行是同一天五只股票的收益。按列计算均值得到五维均值向量，样本协方差矩阵的对角线表示各股票收益方差，非对角线表示共同变化。均值表换算为百分比，协方差矩阵仍按小数收益率计算。下图将协方差标准化为相关系数，便于比较股票之间的联系。
''')
code('''
portfolio_values = portfolio_returns.to_numpy()
portfolio_mu = portfolio_values.mean(axis=0)
portfolio_cov = np.cov(portfolio_values, rowvar=False, ddof=1)
assert np.linalg.eigvalsh(portfolio_cov).min() > 0
show_table(pd.DataFrame({'股票': stock_names, '平均日收益率 (%)': portfolio_mu * 100}), digits=4)
show_table(pd.DataFrame(portfolio_cov, index=stock_names, columns=stock_names)
           .rename_axis('股票').reset_index(), digits=6)
''', 'N03:10 moments and complete covariance output')
code('''
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
''', 'N03:10 correlation figure', 'fig-mc-nb-portfolio-correlation', '五只股票的日收益相关系数；主对角线为1。')
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
portfolio_method_names = {'Historical': '历史样本', 'Parametric MC': '多元正态模拟', 'Bootstrap': '历史整行重抽样'}
portfolio_display_names = {'Equal-weight': '等权组合', 'Value-weight': '市值权重组合'}
np.savez_compressed(OUTPUT / 'portfolio-single-day.npz', **portfolio_arrays)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharex=True, layout='constrained')
distribution_edges = np.linspace(-.10, .10, 121)
for column, axis in enumerate(axes):
    for method, color, style in [('Historical', '#666666', '-'), ('Parametric MC', '#0072B2', '--'), ('Bootstrap', '#D55E00', ':')]:
        values = portfolio_arrays[method][:, column]
        counts, edges = np.histogram(values, bins=distribution_edges)
        axis.stairs(counts / len(values) / np.diff(edges), edges,
                     label=portfolio_method_names[method], color=color, linestyle=style)
    axis.set(title=portfolio_names[column], xlabel='单日收益率', ylabel='概率密度')
    axis.xaxis.set_major_formatter(PercentFormatter(1))
    axis.grid(alpha=.15)
axes[0].legend(frameon=False)
plt.show()
''', 'N03:10/12 sampling, frozen inputs', 'fig-mc-nb-portfolio-distributions', '同一组权重下的历史、正态模拟与整行重抽样单日组合收益分布。')
markdown(r'''
### 用 VaR 与 ES 比较尾部损失 {.unnumbered}

将损失定义为收益率的相反数。95% 风险价值 (Value at Risk, VaR) 是损失分布的 95% 分位数，约有 5% 的结果损失超过该水平。95% 尾部平均损失 (Expected Shortfall, ES) 则是最差 5% 情景的平均损失。两者都是损失率，不是亏损概率。

历史样本的观测数乘以 5% 不一定为整数。下面将尾部边界上的观测按所需份额计入，使 ES 始终对应最差 5% 的经验概率质量。表图均为单日损失率，以百分比表示。
''')
code('''
def portfolio_risk(values, alpha=.05):
    # 固定最差 alpha 的经验概率质量，不因相同取值而扩大尾部。
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
show_table(portfolio_main.replace(portfolio_method_names).replace(portfolio_display_names),
           {'portfolio': '组合', 'method': '生成方式', 'VaR_95': '95% VaR (%)', 'ES_95': '95% ES (%)'})
''', 'N03 risk function and recalculated tables')
code('''
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
以等权组合为例，历史 VaR 约为 1.593%，正态模拟约为 1.681%；历史 ES 约为 2.393%，正态模拟约为 2.120%。在本样本的 95% 水平下，正态模拟的损失分位点略高，却低估了尾部平均损失。整行重抽样的结果较接近历史值，但有限次重抽样仍有数值波动。

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
                # 按种子、区块长度和抽样方式分别初始化，分批生成以控制内存占用。
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
show_table(pd.DataFrame(block_display), digits=2)
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
            axis.set_xlabel('20 日累计收益率 (%)')
        if column == 0:
            axis.set_ylabel('概率密度 (每个百分点)')
axes[0, 0].legend(frameon=False, fontsize=9)
plt.show()
''', 'accepted B20 main figure', 'fig-mc-nb-block-distributions', '每组100000条20日买入持有路径；各面板坐标和分箱一致。')
markdown('L=10时，等权组合区块抽样的VaR约为6.38%，ES约为8.79%。与匹配独立抽样比较，VaR较低而ES较高，说明两项指标需要分别阅读。保留连续关系不必然提高风险估计，也不能因某个长度得到较低风险就认定它最合适。')
supplement('补充分析：区块内部保留了哪些时间联系')
markdown('收益率本身的自相关可能很弱，但较大波动仍可能连续出现。下面分别计算收益率及其平方的自相关。滞后 1 日表示比较相邻交易日，滞后 5 日表示比较间隔五个交易日的记录。收益平方的相关性可以帮助观察大幅波动是否倾向于成段出现。')
code('''
block_acf = []
for lag in [1, 5, 10, 20]:
    for stock in portfolio_returns.columns:
        series = pd.Series(block_values[:, list(portfolio_returns.columns).index(stock)], index=portfolio_prices.index)
        block_acf.append({'stock': stock, 'lag': lag, 'return_acf': series.autocorr(lag),
                          'squared_return_acf': series.pow(2).autocorr(lag)})
block_acf = pd.DataFrame(block_acf)
block_acf.to_csv(OUTPUT / 'block-autocorrelations.csv', index=False, encoding='utf-8-sig')
acf_display = block_acf.query('lag in [1, 5]').copy()
acf_display['stock'] = acf_display['stock'].map(dict(zip(portfolio_returns.columns, stock_names)))
show_table(acf_display, {'stock': '股票', 'lag': '滞后交易日数', 'return_acf': '收益自相关',
                         'squared_return_acf': '收益平方自相关'})
''')
markdown('本样本中，收益率的一阶自相关较小，而五只股票收益平方的一阶自相关均为正，约在 0.097 至 0.204 之间。区块抽样保留整段记录，可以保留区块内部的这类联系；独立逐日抽样会将其打散。区块拼接处的联系仍会中断，不能据此声称完整保留了时间序列结构。')
code('''
show_table(pd.DataFrame(block_support), {'L': '区块长度 (日)', 'blocks': '有效窗口数',
                                        'covered_days': '覆盖的有效日数', 'pool_size': '对照组日收益池大小'})
''')
markdown('有效窗口允许重叠，因此日收益池大小可以超过历史交易日数。同一天进入几个窗口，就在对应的独立抽样池中出现几次。比较每个区块长度时，两种抽样方式使用相同的单日经验分布，差别主要来自是否整段保留日收益。')
close_supplement()
supplement('补充分析：用完整 20 日窗口核对模拟结果')
markdown('当区块长度与持有期限同为 20 日时，一条路径就是一个完整历史窗口。可以不作随机抽样，直接枚举全部有效窗口，计算其等概率经验分布，再与抽样结果对照。')
code('''
exact_blocks = np.stack([block_values[start:start+20] for start in range(len(block_values)-19)
                         if np.isfinite(block_values[start:start+20]).all()])
exact_returns = np.prod(1+exact_blocks, axis=1) @ portfolio_weights - 1
exact_table = pd.DataFrame([{'portfolio': name, **block_risk_metrics(exact_returns[:, column])}
                            for column, name in enumerate(portfolio_names)])
exact_table.to_csv(OUTPUT / 'block-L20-exact.csv', index=False, encoding='utf-8-sig')
exact_comparison = []
for column, name in enumerate(portfolio_names):
    reference = exact_table.iloc[column]
    simulated = block_main[(block_main.L == 20) & (block_main.method == 'block')
                            & (block_main.portfolio == name)].iloc[0]
    exact_comparison.append({'组合': name, '完整窗口 VaR (%)': reference.VaR95 * 100,
                              '模拟 VaR (%)': simulated.VaR95 * 100,
                              '完整窗口 ES (%)': reference.ES95 * 100,
                              '模拟 ES (%)': simulated.ES95 * 100})
show_table(pd.DataFrame(exact_comparison))
''')
markdown('模拟得到的 VaR 与 ES 接近完整窗口的计算值，差异来自有限次抽样。下图将各组的左尾放大，5% 水平线对应的收益率取负后，即为 95% VaR。这个对照检验抽样计算，不说明历史窗口已经覆盖未来全部风险。')
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
    axes[portfolio].set(title=name, xlabel='20 日累计收益率 (%)', xlim=(-25, 0), ylim=(0, 12))
axes[0].set_ylabel('累计概率 (%)')
axes[1].legend(frameon=False, fontsize=9, ncol=2)
plt.show()
''', 'B20 supplementary left tail', 'fig-mc-nb-block-tail', '左尾经验分布。5%横线对应的收益率取负可读出95% VaR。')
close_supplement()
supplement('补充分析：正态模型的计算结果能否相互核对')
markdown(r'若五只股票的收益服从本例设定的联合正态分布，固定权重下的组合收益也服从正态分布，均值为 $\mathbf{w}^{\prime}\hat{\boldsymbol{\mu}}$，方差为 $\mathbf{w}^{\prime}\hat{\Sigma}\mathbf{w}$。因此可以直接计算 VaR 与 ES，与随机模拟结果对照。下面还比较忽略或保留股票相关性时的组合标准差。')
code('''
analytic_rows = []
for column, name in enumerate(portfolio_names):
    weights = portfolio_weights[:, column]
    mean = portfolio_mu @ weights
    deviation = np.sqrt(weights @ portfolio_cov @ weights)
    analytic_rows.append({'组合': name, '解析正态95%VaR': -mean+norm.ppf(.95)*deviation,
                          '解析正态95%ES': -mean+norm.pdf(norm.ppf(.95))/.05*deviation,
                          '忽略相关性标准差': np.sqrt(weights @ np.diag(np.diag(portfolio_cov)) @ weights),
                          '保留相关性标准差': deviation})
analytic_display = pd.DataFrame(analytic_rows)
numeric_columns = analytic_display.select_dtypes(include='number').columns
analytic_display[numeric_columns] *= 100
show_table(analytic_display, {'解析正态95%VaR': '解析 95% VaR (%)', '解析正态95%ES': '解析 95% ES (%)',
                              '忽略相关性标准差': '忽略相关性的标准差 (%)',
                              '保留相关性标准差': '保留相关性的标准差 (%)'})
''')
markdown('解析风险值与前面的正态模拟结果接近。等权组合若忽略相关性，单日标准差约为 0.748%；保留相关性后约为 1.043%。本样本中的正相关提高了组合波动，不能通过独立生成个股收益来省略这部分联系。')
close_supplement()
supplement('补充分析：增加重复次数后，风险指标有多稳定')
markdown('保持数据、权重和生成方式不变，使用三个种子及不同重复次数计算风险指标。下面的区间是三个种子所得结果的最小值至最大值，用来观察数值波动，不是未来损失或风险参数的置信区间。区块表以 10 日区块为例，完整明细导出到开头指定的结果目录。')
code('''
block_stability = (block_metrics.query('L == 10')
                   .groupby(['B', 'method', 'portfolio'])[['VaR95', 'ES95']].agg(['min', 'max']))
block_stability.columns = ['VaR 最小值 (%)', 'VaR 最大值 (%)', 'ES 最小值 (%)', 'ES 最大值 (%)']
block_stability *= 100
show_table(block_stability.reset_index().replace({'iid': '独立抽样', 'block': '区块抽样'}),
           {'B': '重复次数 B', 'method': '抽样方式', 'portfolio': '组合'})
''')
code('''
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
daily_stability = (portfolio_stability.query('B in [10000, 500000]')
                   .groupby(['B', 'portfolio', 'method'])[['VaR_95', 'ES_95']].agg(['min', 'max']))
daily_stability.columns = ['VaR 最小值 (%)', 'VaR 最大值 (%)', 'ES 最小值 (%)', 'ES 最大值 (%)']
daily_stability *= 100
show_table(daily_stability.reset_index().replace(portfolio_method_names).replace(portfolio_display_names),
           {'B': '重复次数 B', 'portfolio': '组合', 'method': '单日生成方式'})
''')
code("""
case_results['portfolio'] = {'daily_risk_rows': len(portfolio_risks), 'block_metric_rows': len(block_metrics),
                              'sample_rows': len(portfolio_returns), 'block_support': block_support}
""", hidden=True)
markdown('在这些重复实验中，增加抽样次数通常缩小了种子之间的风险指标差异。但这只说明当前模型下的数值近似更稳定，不会扩大历史样本所覆盖的市场状态，也不能据此选择给出最低风险的区块长度。')
close_supplement()

markdown(r'''
## 案例四：从随机变量到随机过程 {.unnumbered #sec-mc-nb-process}

[返回正文：案例四](../../lectures/monte-carlo.qmd#sec-mc-process)。

本例关注期末上涨与途中跌破阈值两类事件。二者都从价格路径计算，但回答不同问题。下面依次用随机游走说明冲击累积、用布朗运动说明时间尺度，再用几何布朗运动生成始终为正的价格路径。

### 随机游走 {.unnumbered}

从 $X_{0}=0$ 出发，每一步按 $X_{k+1}=X_{k}+\varepsilon_{k+1}$ 更新，其中各步冲击 $\varepsilon_{k}$ 独立且服从标准正态分布。独立抽取的是新增冲击，不是各时点的取值，过去冲击的影响会累积在路径中。横轴为离散步数，每步冲击标准差为 1，此时还没有将时间和波动换算为资产收益的年化尺度。
''')
code(old('process', 4).replace('"Step"', '"步数"').replace('"X"', '"累计取值 X"')
     .replace('Discrete random-walk paths', '独立冲击累积形成的随机游走路径'),
     'N04:4', 'fig-mc-nb-random-walk', '独立冲击逐步累积形成的随机游走路径。')
markdown(r'''
### 布朗运动 {.unnumbered}

将一年划分为 252 步，每步长度为 $\Delta t=1/252$ 年。布朗运动从 $W_{0}=0$ 开始，在这些时点上按下式生成：

$$
W_{t_{k+1}}=W_{t_{k}}+\sqrt{\Delta t}\,Z_{k+1},
\qquad Z_{k+1}\overset{\mathrm{iid}}{\sim}N(0,1).
$$ {#eq-mc-nb-brownian}

新增冲击的方差为 $\Delta t$，各段方差加总后，一年的累计方差为 1。这样加密时间网格时不会人为增大整年的波动。下图展示 20 条路径，随后独立抽取 100000 个终点，与 $W_{T}\sim N(0,T)$ 的理论均值和标准差比较。
''')
code(old('process', 6).replace('"Time"', '"时间 (年)"').replace('"W(t)"', '"累计冲击 W(t)"')
     .replace('Brownian-motion sample paths', '标准布朗运动的模拟路径'),
     'N04:6', 'fig-mc-nb-brownian', '一年时间网格上的布朗运动路径。')
code(old('process', 7).replace('pd.Series({', 'brownian_summary = pd.Series({') + '''
show_table(pd.DataFrame({'指标': ['均值', '标准差'],
                         '模拟结果': [brownian_summary['mean_WT'], brownian_summary['sd_WT']],
                         '理论值': [0.0, np.sqrt(T)]}))
''', 'N04:7')
markdown('本次抽样的终点均值约为 -0.002，标准差约为 1.000，与一年期标准布朗运动的理论值 0 和 1 接近。该检查只针对终点分布，不能单独验证路径上全部时点的依赖关系。')
markdown(r'''
### 几何布朗运动 {.unnumbered}

几何布朗运动 (Geometric Brownian Motion, GBM) 将累积冲击引入对数价格，价格取值为

$$
S_{t}=S_{0}\exp\!\left[\left(\mu-\frac{1}{2}\sigma^{2}\right)t+\sigma W_{t}\right].
$$ {#eq-mc-nb-gbm}

其中 $S_{0}$ 为初始价格，$\mu$ 控制预期价格的增长，$\sigma$ 为年化波动率，$t$ 以年计。指数变换保证价格为正，减去 $\sigma^{2}/2$ 则使预期价格按 $\mu$ 指定的速度增长。代码先累积各步布朗增量，再直接计算网格时点的价格。

下面固定 $S_{0}=100$、$\mu=0.08$ 和一年期限，分别取 $\sigma=0.10$ 与 $0.35$，各画 30 条路径。两组使用不同种子，比较的是整体分散程度，不是共用冲击下的逐条路径。
''')
gbm_source = old('process', 9)
code(gbm_source[:gbm_source.index('for sigma in [0.10, 0.35]:')], 'N04:9 function')
for volatility, name in [(0.10, 'low'), (0.35, 'high')]:
    code(f'''
    sigma = {volatility}
    t, S = gbm_paths(sigma=sigma, n_paths=30, seed=SEED + int(sigma*1000))
    fig, ax = plt.subplots(figsize=(8, 5))
    for row in S:
        ax.plot(t, row, linewidth=0.8, alpha=0.65)
    ax.set(xlabel='时间 (年)', ylabel='资产价格 (元)', title=f'GBM 价格路径：σ={{sigma:.2f}}')
    plt.show()
    ''', f'N04:9 {name} volatility', f'fig-mc-nb-gbm-{name}',
         f'年化波动率为 {volatility:.2f} 的 GBM 价格路径。')
markdown(r'''
### 终值风险和路径风险 {.unnumbered}

主风险实验设初始价格为100元、漂移率为0.08、波动率为0.30、期限为1年，生成5000条各含252步的路径。将75元设为风险监测阈值，分别统计期末价格高于100元、网格价格曾低于75元，以及两者同时发生的路径。下表列出各事件的路径数，概率分母均为5000。

这不是止损交易模拟，也不是最大回撤。统计仅监测离散网格时点，不保证捕捉时点之间的连续越界。
''')
path_source = old('process', 11)
code(path_source[:path_source.index('pd.Series({')], 'N04:11')
code('''
path_events = pd.DataFrame({
    '事件': ['期末上涨', '网格中曾跌破75', '期末上涨且网格中曾跌破75'],
    '计数': [int((terminal > S0).sum()), int(hit_barrier.sum()), int(((terminal > S0) & hit_barrier).sum())],
})
path_events['分母'] = n_paths
path_events['概率 (%)'] = path_events['计数'] / n_paths * 100
show_table(path_events.assign(事件=path_events['事件'].str.replace('跌破75', '跌破 75 元')),
           {'计数': '路径条数', '分母': '全部路径数'}, digits=2)
''')
code('''
path_events.to_csv(OUTPUT / 'path-events.csv', index=False, encoding='utf-8-sig')
case_results['path_risk'] = {'B': int(n_paths), 'counts': path_events['计数'].tolist(),
                             'parameters': {'S0': float(S0), 'mu': float(mu), 'sigma': float(sigma),
                                             'T': float(T), 'N': int(N), 'barrier': float(barrier)}}
''', hidden=True)
markdown('期末上涨的路径仍可能在途中跌破75元。按本页设定，两类单独事件和联合事件分别约为54.98%、28.04%和2.66%。第三项不是以期末上涨路径为分母的条件概率。')
supplement('扩展阅读：Monte Carlo 期权定价')
markdown(r'''
欧式看涨期权到期支付为 $\max(S_{T}-K,0)$，只与终值有关，因此本例直接模拟终值，不必生成完整路径。风险中性分布的漂移使用无风险利率，不能将其中的上涨概率解释为现实发生概率。

其中，$S_{T}$ 为到期价格，$K$ 为执行价格。本段采用无分红、无交易成本、可连续交易且利率和波动率恒定的 Black–Scholes 模型，另设初始价与执行价均为100元、连续复利无风险年利率0.05、年化波动率0.20、期限1年，独立模拟100000个终值。

先计算各情景折现支付的平均值，得到 MC 价格，再用折现支付的样本标准差除以模拟次数的平方根，得到 MC 标准误。Black–Scholes 闭式价格是同一模型下可直接计算的理论基准，不是另一个市场价格观测。比较二者，可以检查模拟计算的精度。
''')
pricing_source = old('process', 13)
code(pricing_source[:pricing_source.index('pd.Series({')], 'N04:13')
code('''
pricing_B = 100000
pricing_rng = np.random.default_rng(SEED)
pricing_shocks = pricing_rng.normal(size=pricing_B)
pricing_terminal = S0 * np.exp((r-.5*sigma**2)*T + sigma*np.sqrt(T)*pricing_shocks)
discounted_payoff = np.exp(-r*T) * np.maximum(pricing_terminal-K, 0)
pricing_mcse = discounted_payoff.std(ddof=1) / np.sqrt(pricing_B)
assert np.isclose(discounted_payoff.mean(), mc_price)
show_table(pd.DataFrame({'指标': ['MC 价格', 'Black–Scholes 闭式价格', 'MC 标准误', 'MC 价格减去闭式价格'],
                         '数值 (元)': [mc_price, bs_price, pricing_mcse, mc_price-bs_price]}), digits=4)
''', 'accepted pricing MCSE check')
code("case_results['option'] = {'MC': float(mc_price), 'closed_form': float(bs_price), 'MCSE': float(pricing_mcse)}", hidden=True)
code(old('process', 14).removesuffix('conv') +
     "show_table(conv, {'B': '模拟次数 B', 'MC_price': 'MC 价格 (元)', 'error_vs_BS': 'MC 价格减去闭式价格 (元)'}, digits=4)", 'N04:14')
code(old('process', 15).replace('Monte Carlo repetitions B (log scale)', '模拟次数 B (对数刻度)')
     .replace('Call price', '看涨期权价格 (元)').replace('Monte Carlo pricing convergence', '模拟次数与期权定价结果'),
     'N04:15', 'fig-mc-nb-option-convergence', '不同重复次数下MC价格与闭式价格比较，误差不要求单调下降。')
markdown('本参数下MC价格约为10.4165，闭式价格约为10.4506，MC标准误约为0.0463。这个对照用于核验计算，并不证明真实资产价格符合GBM。')
close_supplement()
markdown(r'''
## 从案例回到模拟设计 {.unnumbered #sec-mc-nb-output}

四个案例使用 MC 回答不同问题：比较估计量、评价项目价值、估计组合损失，以及识别价格路径中的风险事件。更换问题时，需要相应调整生成机制和评价指标，计算稳定也不意味着模型一定适用。

[返回正文的五项检查](../../lectures/monte-carlo.qmd#sec-mc-reliable)，结合案例检查自己的模拟设计。
''')
code('''
(OUTPUT / 'run-summary.json').write_text(json.dumps(case_results, ensure_ascii=False, indent=2), encoding='utf-8')
''', hidden=True)


def apply_sources(output):
    cells.insert(0, nbformat.v4.new_raw_cell('---\ntitle: "# Monte Carlo 模拟：案例与代码 {.unnumbered}"\nnumber-sections: false\ncss: ../../tools/monte-carlo/monte-carlo.css\n---'))
    for item in mapping:
        item['cell'] += 1
    notebook = nbformat.read(TARGET, as_version=4)
    previous_code = {cell.source: cell for cell in notebook.cells if cell.cell_type == 'code'}
    for index, cell in enumerate(cells):
        cell['id'] = f'mc-cases-{index:03d}'
        if cell.cell_type == 'code' and cell.source in previous_code:
            cell.outputs = previous_code[cell.source].outputs
            cell.execution_count = previous_code[cell.source].execution_count
    notebook.cells = cells
    notebook.metadata = {
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python', 'version': '3.11'},
    }

    nbformat.validate(notebook)
    nbformat.write(notebook, TARGET)
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
