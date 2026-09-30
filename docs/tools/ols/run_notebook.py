"""从仓库根执行 OLS Notebook，配置与日志只写入本项目。"""
from pathlib import Path
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

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / 'logs/ols/runtime'


def main():
    # 先校验冻结数据，避免用另一个 Mroz 版本悄悄替换样本。
    data = ROOT / 'data/ols/mroz.dta'
    source = json.loads((ROOT / 'data/ols/source.json').read_text(encoding='utf-8'))
    if hashlib.sha256(data.read_bytes()).hexdigest() != source['sha256']:
        raise ValueError('Mroz 数据哈希不匹配，请核对 data/ols/source.json。')
    stata = Path(os.environ.get('STATA_EXE', ''))
    if not stata.is_file():
        raise FileNotFoundError('请把 STATA_EXE 指向已安装的 Stata。')
    for folder in ['ipython', 'jupyter', 'config/nbstata', 'kernels/ols-stata']:
        (RUNTIME / folder).mkdir(parents=True, exist_ok=True)
    os.environ.update(
        IPYTHONDIR=str(RUNTIME / 'ipython'),
        JUPYTER_RUNTIME_DIR=str(RUNTIME / 'jupyter'),
        XDG_CONFIG_HOME=str(RUNTIME / 'config'),
        FINECO_ROOT=str(ROOT), PYTHONIOENCODING='utf-8',
    )
    edition = 'mp' if 'mp' in stata.name.lower() else ('se' if 'se' in stata.name.lower() else 'be')
    (RUNTIME / 'config/nbstata/nbstata.conf').write_text(
        f'[nbstata]\nstata_dir = {stata.parent.as_posix()}\nedition = {edition}\nsplash = False\n',
        encoding='utf-8',
    )
    spec = {'argv': [sys.executable, '-m', 'nbstata', '-f', '{connection_file}'],
            'display_name': 'OLS Stata', 'language': 'stata'}
    (RUNTIME / 'kernels/ols-stata/kernel.json').write_text(json.dumps(spec), encoding='utf-8')

    # Notebook 与 do-file 共用同一份分析代码，去除文件日志开关。
    source_code = (ROOT / 'tools/ols/ols_ch1_run.do').read_text(encoding='utf-8')
    source_code = '\n'.join(line for line in source_code.splitlines()
                            if not re.match(r'(?:capture )?log (?:using|close)', line))
    nb = nbformat.v4.new_notebook(metadata={'kernelspec': {
        'name': 'ols-stata', 'display_name': 'OLS Stata', 'language': 'stata'}})
    nb.cells = [
        nbformat.v4.new_markdown_cell('''# OLS：Stata 实验 {#sec-ols-lab}

[返回理论篇](../../lectures/ols.qmd) · [数据说明](../../data/ols/README.md) · [完整 do-file](../../tools/ols/ols_ch1_run.do)

本实验使用冻结的 Mroz 数据，研究就业女性的小时工资与教育年限。先检查样本，再比较组均值与回归直线，最后核对三条 OLS 代数性质。

从仓库根目录执行 `python tools/ols/run_notebook.py` 可重新运行。下方输出由 Stata 实际产生；网页只展示已保存结果。
'''),
        nbformat.v4.new_code_cell('''%%quietly
local project_root : environment FINECO_ROOT
if "`project_root'" != "" {
    cd "`project_root'"
}
confirm file "data/ols/mroz.dta"
'''),
        nbformat.v4.new_markdown_cell('''## 样本、估计与代数检查

官方文件把 325 名未就业女性的工资编码为 0；本实验明确筛选 `inlf == 1`。回归输出中应看到 `Number of obs = 428`、教育系数约 0.4953、常规标准误约 0.06595。分组图使用同一批个体，标签为各组样本量。

残差矩接近零只说明 OLS 拟合代数成立，不能据此判断教育是外生变量。
'''),
        nbformat.v4.new_code_cell(source_code),
        nbformat.v4.new_markdown_cell('''## 核对结果

教育 12 年组有 212 人，平均工资约 3.800147；16 年组有 39 人，平均工资约 5.154136 美元/小时。回归直线的斜率是统计关系，不是教育的因果回报。

机器结果与分组表保存到 `output/ols/tables/`。重新执行时以刚生成的表为准，执行器会核对样本量、系数和残差正交条件。

[返回理论篇](../../lectures/ols.qmd)
''')]
    nb.cells[1].metadata['tags'] = ['remove-cell']
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    manager = KernelManager(kernel_name='ols-stata', kernel_spec_manager=
                            KernelSpecManager(kernel_dirs=[str(RUNTIME / 'kernels')]))
    NotebookClient(nb, km=manager, timeout=180,
                   resources={'metadata': {'path': str(ROOT)}}).execute()
    values = {}
    for line in (ROOT / 'output/ols/tables/ols_ch1_results.txt').read_text().splitlines():
        key, value = line.split('=', 1)
        try:
            values[key] = float(value)
        except ValueError:
            pass
    expected = {'N_ols': 428, 'n_educ12': 212, 'n_educ16': 39,
                'mean_wage_educ12': 3.800147, 'mean_wage_educ16': 5.154136,
                'b_cons': -2.092367, 'b_educ': .495308,
                'se_cons': .848288, 'se_educ': .065948, 'R2_ols': .116933}
    for key, value in expected.items():
        if abs(values[key] - value) > 1e-6:
            raise AssertionError(f'{key} 与已验证基线不一致：{values[key]}')
    assert abs(values['mean_resid']) < 1e-12
    assert abs(values['sum_resid_educ']) < 1e-9
    nbformat.write(nb, ROOT / 'notebooks/ols/ols-stata.ipynb')
    (ROOT / 'logs/ols/execution.json').write_text(
        json.dumps({'status': 'PASS', 'values': values}, indent=2), encoding='utf-8')
    print('PASS: Stata Notebook 已从头执行，样本、系数和代数检查通过。')


if __name__ == '__main__':
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    main()
