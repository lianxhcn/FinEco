"""从 FinEco 仓库根目录运行线性回归实验，保存 Stata 真实输出。"""
from pathlib import Path
import asyncio, hashlib, json, os, re, sys
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
ROOT=Path(__file__).resolve().parents[2]
RUNTIME=ROOT/'logs/linear-regression/runtime'
def main():
    # 校验本章快照，防止默默改用另一个样本版本。
    for item in json.loads((ROOT/'data/linear-regression/source-manifest.json').read_text(encoding='utf-8')):
        data=ROOT/'data/linear-regression'/item['file']
        if hashlib.sha256(data.read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('数据 SHA-256 不匹配：'+item['file'])
    stata=Path(os.environ.get('STATA_EXE',''))
    if not stata.is_file(): raise FileNotFoundError('STATA_EXE 未指向已安装的 Stata。')
    for d in ['ipython','jupyter','config/nbstata','kernels/linear-regression-stata']:
        (RUNTIME/d).mkdir(parents=True,exist_ok=True)
    os.environ.update(IPYTHONDIR=str(RUNTIME/'ipython'),JUPYTER_RUNTIME_DIR=str(RUNTIME/'jupyter'),XDG_CONFIG_HOME=str(RUNTIME/'config'),FINECO_ROOT=str(ROOT),PYTHONIOENCODING='utf-8')
    edition='mp' if 'mp' in stata.name.lower() else ('se' if 'se' in stata.name.lower() else 'be')
    (RUNTIME/'config/nbstata/nbstata.conf').write_text(f'[nbstata]\nstata_dir = {stata.parent.as_posix()}\nedition = {edition}\nsplash = False\n',encoding='utf-8')
    spec={'argv':[sys.executable,'-m','nbstata','-f','{connection_file}'],'display_name':'Stata','language':'stata'}
    (RUNTIME/'kernels/linear-regression-stata/kernel.json').write_text(json.dumps(spec),encoding='utf-8')
    nb=nbformat.v4.new_notebook(metadata={'kernelspec':{'name':'linear-regression-stata','display_name':'Stata','language':'stata'}})
    nb.cells=[nbformat.v4.new_markdown_cell('''# 线性回归：Stata 实验 {#sec-linear-regression-lab}

[返回理论篇](../../lectures/linear-regression.qmd) · [数据说明](../../data/linear-regression/README.md) · [完整 do-file](../../tools/linear-regression/linear-regression.do)

本实验保留工资、汽车和企业财务案例，核对去均值、FWL、虚拟变量的两种参数化，以及中心化前后的拟合等价性。数据均读取本地快照；网页只展示从头运行后保存的实际结果，不执行代码或实时取数。企业数据来源的部分口径未完整说明，结果只作教学演示。

从仓库根目录运行 `python tools/linear-regression/run_notebook.py`。需要已配置的 `STATA_EXE` 和 nbstata 环境。
'''),nbformat.v4.new_code_cell('''%%quietly
local project_root : environment FINECO_ROOT
cd "`project_root'"
''')]
    nb.cells[1].metadata['tags']=['remove-cell']
    text=(ROOT/'tools/linear-regression/linear-regression.do').read_text(encoding='utf-8')
    # 各段在同一个内核按顺序执行，保留 Stata 数据和估计状态。
    groups=re.split(r'^\*\*# (.+)$',text,flags=re.M)
    nb.cells.append(nbformat.v4.new_markdown_cell('## 运行准备\n\n校验冻结数据并检查 SSC 命令；已安装的命令不会重复安装。'))
    nb.cells.append(nbformat.v4.new_code_cell(groups[0]))
    for i in range(1,len(groups),2):
        title,code=groups[i],groups[i+1]
        nb.cells.append(nbformat.v4.new_markdown_cell('## '+title+'\n\n按顺序运行，比较同一段中不同设定的输出。'))
        nb.cells.append(nbformat.v4.new_code_cell(code))
    if sys.platform=='win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    manager=KernelManager(kernel_name='linear-regression-stata',kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(RUNTIME/'kernels')]))
    client=NotebookClient(nb,km=manager,timeout=600,resources={'metadata':{'path':str(ROOT)}})
    try: client.execute()
    except Exception:
        nbformat.write(nb,ROOT/'logs/linear-regression/failed.ipynb')
        raise
    # Stata 的 assert 已核对关键等价关系，再保存实际执行的 Notebook。
    nb.cells.append(nbformat.v4.new_markdown_cell('''## 阅读结果

工资教育案例使用剔除极端工资并合并教育档位后的样本，不能与原 OLS 章的未截尾样本混用系数。FWL 的核对只针对斜率，不把残差回归的默认标准误当作完整模型的标准误。中心化改变一阶项参考点，同一实际点上的预测与边际效应保持不变。40 小时处仅是分段拟合演示，没有因果 RDD 识别依据。

[返回理论篇](../../lectures/linear-regression.qmd)
'''))
    nbformat.write(nb,ROOT/'notebooks/linear-regression/linear-regression-stata.ipynb')
    values=dict(line.split('=',1) for line in (ROOT/'logs/linear-regression/results.txt').read_text().splitlines())
    (ROOT/'logs/linear-regression/execution.json').write_text(json.dumps({'status':'PASS','values':values},indent=2),encoding='utf-8')
    print('PASS: Notebook 从头执行，FWL、去均值、虚拟变量与中心化核对通过。')
if __name__=='__main__':
    if sys.stdout.encoding and sys.stdout.encoding.lower()!='utf-8': sys.stdout.reconfigure(encoding='utf-8')
    main()
