"""核对 FinEco 环境和依赖；不执行课程案例、联网取数或启动 Stata。"""
from pathlib import Path
import argparse
import hashlib
import importlib
import importlib.metadata as metadata
import json
import os
import site
import sys
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
MODULES = {
    'numpy': 'numpy', 'pandas': 'pandas', 'scipy': 'scipy',
    'statsmodels': 'statsmodels', 'matplotlib': 'matplotlib',
    'akshare': 'akshare', 'nbstata': 'nbstata', 'nbformat': 'nbformat',
    'nbclient': 'nbclient', 'jupyter-client': 'jupyter_client',
    'ipykernel': 'ipykernel', 'pyarrow': 'pyarrow',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path,
                        default=ROOT/'logs/environment/preflight.json')
    args = parser.parse_args()
    if Path(sys.prefix).resolve() != (ROOT/'.venv').resolve():
        raise SystemExit('请使用本项目 .venv/Scripts/python.exe。')
    from packaging.requirements import Requirement

    installed = {}
    mismatches = []
    lock_count = 0
    for filename in ('requirements.txt', 'requirements-lock.txt'):
        for line in (ROOT/filename).read_text(encoding='utf-8-sig').splitlines():
            line = line.strip()
            if not line or line.startswith(('#', '--')):
                continue
            req = Requirement(line.removesuffix('\\').strip())
            if req.marker and not req.marker.evaluate():
                continue
            if filename == 'requirements-lock.txt':
                lock_count += 1
            try:
                version = metadata.version(req.name)
            except metadata.PackageNotFoundError:
                version = 'MISSING'
            installed[req.name] = version
            if version == 'MISSING' or not req.specifier.contains(version):
                mismatches.append({'file': filename, 'package': req.name,
                                   'expected': str(req.specifier),
                                   'installed': version})

    origins = {}
    for package, name in MODULES.items():
        module = importlib.import_module(name)
        origins[package] = str(Path(module.__file__).resolve())
    package_root = (ROOT/'.venv/Lib/site-packages').resolve()
    isolated_imports = all(Path(p).is_relative_to(package_root)
                           for p in origins.values())
    checks = {
        'python_312': sys.version_info[:2] == (3, 12),
        'project_prefix': Path(sys.prefix).resolve() == (ROOT/'.venv').resolve(),
        'user_site_disabled': not site.ENABLE_USER_SITE,
        'root_and_lock_versions_match': not mismatches,
        'twelve_root_modules_imported_from_project': isolated_imports,
        'no_migration_path_in_sys_path': not any('迁移' in p for p in sys.path),
        'configured_project_python': os.environ.get('PYTHON_EXE') == sys.executable,
        'quarto_uses_project_python': os.environ.get('QUARTO_PYTHON') == sys.executable,
        'stata_path_exists': Path(os.environ.get('STATA_EXE', '')).is_file(),
    }
    report = {
        'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
        'python_executable': sys.executable,
        'python_version': sys.version,
        'base_prefix': sys.base_prefix,
        'checks': checks,
        'lock_packages_for_current_platform': lock_count,
        'versions': installed,
        'mismatches': mismatches,
        'module_origins': origins,
        'root_requirements_sha256': hashlib.sha256(
            (ROOT/'requirements.txt').read_bytes()).hexdigest(),
        'lock_sha256': hashlib.sha256(
            (ROOT/'requirements-lock.txt').read_bytes()).hexdigest(),
        'course_cases_executed': False,
        'stata_launched': False,
        'site_built': False,
        'pass': all(checks.values()),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                           encoding='utf-8')
    print(json.dumps({'pass': report['pass'], 'checks': checks,
                      'root_modules': len(origins), 'locked_packages': lock_count},
                     ensure_ascii=False, indent=2))
    if not report['pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
