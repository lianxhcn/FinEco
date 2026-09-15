"""从头运行 v10 完整 Python 和 Stata Notebook，保存真实输出。"""
from pathlib import Path
import asyncio
import json
import os
import sys
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

ROOT = Path(__file__).resolve().parents[2]
runtime = ROOT/'logs/bootstrap/v10/runtime'
for sub in ('ipython','jupyter','config/nbstata','kernels/python3','kernels/nbstata'):
    (runtime/sub).mkdir(parents=True, exist_ok=True)
os.environ.update(IPYTHONDIR=str(runtime/'ipython'),
    JUPYTER_RUNTIME_DIR=str(runtime/'jupyter'), XDG_CONFIG_HOME=str(runtime/'config'),
    PYTHONNOUSERSITE='1', PYTHONIOENCODING='utf-8', FINECO_BOOTSTRAP_ROOT=str(ROOT))
stata = Path(os.environ['STATA_EXE'])
if not stata.is_file():
    raise FileNotFoundError('STATA_EXE 不存在')
edition = 'mp' if 'mp' in stata.name.lower() else ('se' if 'se' in stata.name.lower() else 'be')
(runtime/'config/nbstata/nbstata.conf').write_text(
    f'[nbstata]\nstata_dir = {stata.parent.as_posix()}\nedition = {edition}\nsplash = False\n', encoding='utf-8')
for name, module, lang in (('python3','ipykernel_launcher','python'),('nbstata','nbstata','stata')):
    (runtime/f'kernels/{name}/kernel.json').write_text(json.dumps({
        'argv':[sys.executable,'-m',module,'-f','{connection_file}'],
        'display_name':name,'language':lang}), encoding='utf-8')
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
for language, kernel in (('python','python3'),('stata','nbstata')):
    path = ROOT/'notebooks/bootstrap'/('bootstrap-demo.ipynb' if language=='python' else 'bootstrap-stata.ipynb')
    nb = nbformat.read(path, as_version=4)
    manager = KernelManager(kernel_name=kernel, kernel_spec_manager=KernelSpecManager(
        kernel_dirs=[str(runtime/'kernels')]))
    try:
        NotebookClient(nb, km=manager, timeout=600,
            resources={'metadata':{'path':str(ROOT)}}).execute()
    except Exception:
        nbformat.write(nb, ROOT/f'logs/bootstrap/v10/failed-{language}.ipynb')
        raise
    nbformat.write(nb, path)
    output = '\n'.join(o.get('text','') for c in nb.cells if c.cell_type=='code' for o in c.outputs)
    (ROOT/f'logs/bootstrap/v10/{language}-output.txt').write_text(output, encoding='utf-8')
    print(f'PASS {path.relative_to(ROOT)}', flush=True)
