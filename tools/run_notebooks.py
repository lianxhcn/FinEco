"""用当前 Python 和项目临时内核执行讲义，不修改全局 Jupyter 配置。"""
from pathlib import Path
import asyncio
import json
import os
import sys
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "002-working" / "runtime"

def prepare():
    # 所有运行时文件留在本地工作区，避免不同 Python 的内核注册相互干扰。
    for sub in ("ipython", "jupyter", "config/nbstata", "kernels/finance-python", "kernels/finance-stata"):
        (LOCAL / sub).mkdir(parents=True, exist_ok=True)
    os.environ.update(IPYTHONDIR=str(LOCAL / "ipython"),
                      JUPYTER_RUNTIME_DIR=str(LOCAL / "jupyter"),
                      XDG_CONFIG_HOME=str(LOCAL / "config"),
                      PYTHONNOUSERSITE="1", PYTHONIOENCODING="utf-8", FINECO_ROOT=str(ROOT))
    stata = Path(os.environ["STATA_EXE"])
    if not stata.is_file():
        raise FileNotFoundError("STATA_EXE 未指向有效的 Stata 程序")
    edition = "mp" if "mp" in stata.name.lower() else ("se" if "se" in stata.name.lower() else "be")
    (LOCAL / "config/nbstata/nbstata.conf").write_text(
        f"[nbstata]\nstata_dir = {stata.parent.as_posix()}\nedition = {edition}\nsplash = False\n", encoding="utf-8")
    for name, module, language in [("finance-python", "ipykernel_launcher", "python"), ("finance-stata", "nbstata", "stata")]:
        spec = {"argv": [sys.executable, "-m", module, "-f", "{connection_file}"],
                "display_name": name, "language": language}
        (LOCAL / f"kernels/{name}/kernel.json").write_text(json.dumps(spec), encoding="utf-8")

def run(path):
    nb = nbformat.read(path, as_version=4)
    name = "finance-stata" if "stata" in path.name else "finance-python"
    manager = KernelManager(kernel_name=name, kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(LOCAL / "kernels")]))
    NotebookClient(nb, km=manager, timeout=300, resources={"metadata": {"path": str(ROOT)}}).execute()
    nbformat.write(nb, path)
    print(f"PASS {path.relative_to(ROOT)}", flush=True)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    prepare()
    paths = [ROOT / a for a in sys.argv[1:]] or list((ROOT / "notebooks/intro").glob("*.ipynb"))
    for path in paths:
        run(path)
