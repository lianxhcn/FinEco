"""用当前 Python 从头执行 Notebook，临时 kernel spec 仅写本章日志。"""
from pathlib import Path
import os, sys, json
import nbformat
from nbclient import NotebookClient

root=Path(__file__).resolve().parents[2]
runtime=root/'logs/financial-data/jupyter'
kernel=runtime/'kernels/fineco-financial-data'
kernel.mkdir(parents=True,exist_ok=True)
(kernel/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
    'display_name':'FinEco local Python','language':'python'}),encoding='utf-8')
os.environ['JUPYTER_PATH']=str(runtime)+os.pathsep+os.environ.get('JUPYTER_PATH','')
os.environ['JUPYTER_RUNTIME_DIR']=str(runtime/'runtime')
os.environ['IPYTHONDIR']=str(runtime/'ipython')
target=root/'notebooks/financial-data/financial-data.ipynb'
nb=nbformat.read(target,as_version=4)
NotebookClient(nb,timeout=600,kernel_name='fineco-financial-data',
               resources={'metadata':{'path':str(root)}}).execute()
nb.metadata.kernelspec={'name':'python3','display_name':'Python 3','language':'python'}
nbformat.write(nb,target)
print('PASS: Notebook 从头执行并保存，代码单元格数',sum(c.cell_type=='code' for c in nb.cells))
