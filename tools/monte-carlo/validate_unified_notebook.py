from pathlib import Path
import argparse
import asyncio
import base64
import hashlib
import json
import os
import shutil
from datetime import datetime

import nbformat
from nbclient import NotebookClient
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--output-dir', type=Path, default=ROOT / 'logs/monte-carlo/site-update-20261019')
arguments = parser.parse_args()
OUT = arguments.output_dir.resolve()
TARGET = ROOT / 'notebooks/monte-carlo/monte-carlo-cases.ipynb'
OUT.mkdir(parents=True, exist_ok=True)
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(source, directory, results):
    notebook = nbformat.read(source, as_version=4)
    expected_sources = [cell.source for cell in notebook.cells]
    os.environ['FINECO_MC_OUTPUT'] = str(results)
    NotebookClient(notebook, timeout=600, kernel_name='python3',
                   resources={'metadata': {'path': str(directory)}}).execute()
    assert [cell.source for cell in notebook.cells] == expected_sources
    errors = [output for cell in notebook.cells if cell.cell_type == 'code'
              for output in cell.outputs if output.output_type == 'error']
    assert not errors
    assert all(cell.execution_count is not None for cell in notebook.cells if cell.cell_type == 'code')
    return notebook


original_files = sorted(path for path in (ROOT / 'notebooks/monte-carlo').glob('*.ipynb') if path != TARGET)
original_hashes = {path.name: digest(path) for path in original_files}
source = nbformat.read(TARGET, as_version=4)
nbformat.write(source, OUT / 'unexecuted.ipynb')
code_source = '\n'.join(cell.source for cell in source.cells if cell.cell_type == 'code')
for forbidden in ['portfolio-reproduction', '003-tasks', 'logs/monte-carlo', 'sys.path', '%run']:
    assert forbidden not in code_source, forbidden
report = {'date': '2026-10-19', 'cells': len(source.cells),
          'code_cells': sum(cell.cell_type == 'code' for cell in source.cells),
          'no_private_or_log_runtime_dependencies': True, 'checks': {}}
(OUT / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('Executing unified Notebook from the repository root...', flush=True)
notebook = execute(TARGET, ROOT, OUT / 'execution')
nbformat.write(notebook, TARGET)
nbformat.write(notebook, OUT / 'executed.ipynb')
report['executed'] = True
report['executed_code_cells'] = [cell.execution_count for cell in notebook.cells if cell.cell_type == 'code']
results = OUT / 'execution'
print('Full execution completed; checking accepted results...', flush=True)

reference = np.load(ROOT / 'logs/monte-carlo/case1-20261017-202922/estimates.npz')
actual = np.load(results / 'case1/estimates.npz')
assert actual.files == reference.files
assert all(np.array_equal(actual[key], reference[key]) for key in reference.files)
report['checks']['case1_all_14_arrays_exact'] = True

reference = np.load(ROOT / 'logs/monte-carlo/valuation-20261017-215223/final/scenarios.npz')
actual = np.load(results / 'valuation/scenarios.npz')
assert actual.files == reference.files
assert all(np.array_equal(actual[key], reference[key]) for key in reference.files)
audit = json.loads((results / 'valuation/weighted-audit.json').read_text(encoding='utf-8'))
assert audit['scenario_count'] == 440000 and audit['weighted_sign_mismatches'] == 0
report['checks']['valuation_all_6_arrays_exact'] = True
report['checks']['weighted_boundary_440000_no_sign_mismatch'] = True

actual = pd.read_csv(results / 'portfolio-risk-metrics.csv')
reference = pd.read_csv(ROOT / 'data/monte-carlo/portfolio-results/risk_metrics.csv')
columns = ['VaR_95', 'ES_95', 'VaR_99', 'ES_99']
pd.testing.assert_frame_equal(actual[['portfolio', 'method']], reference[['portfolio', 'method']])
maximum_error = float(np.max(np.abs(actual[columns].to_numpy() - reference[columns].to_numpy())))
assert np.allclose(actual[columns], reference[columns], rtol=1e-10, atol=1e-12)
report['checks']['single_day_risk_max_abs_difference'] = maximum_error

actual = pd.read_csv(results / 'block-metrics-all.csv')
reference = pd.read_csv(ROOT / 'logs/monte-carlo/block-20261017-183940/metrics-all.csv')
pd.testing.assert_frame_equal(actual, reference, check_exact=True)
report['checks']['block_all_72_metric_rows_exact'] = True
block_arrays = np.load(results / 'block-returns.npz')
block_differences = {}
for length in [5, 10, 20]:
    for method in ['iid', 'block']:
        reference = pd.read_csv(ROOT / f'logs/monte-carlo/block-20261017-183940/returns-L{length}-{method}.csv.gz',
                                float_precision='round_trip').to_numpy()
        actual = block_arrays[f'L{length}_{method}']
        assert np.allclose(actual, reference, rtol=0, atol=2e-15)
        block_differences[f'L{length}_{method}'] = float(np.abs(actual - reference).max())
report['checks']['block_all_six_return_tables_max_difference'] = block_differences

summary = json.loads((results / 'run-summary.json').read_text(encoding='utf-8'))
assert summary['path_risk']['counts'] == [2749, 1402, 133]
assert summary['path_risk']['B'] == 5000
assert abs(summary['option']['MC'] - 10.4165) < .00005
assert abs(summary['option']['closed_form'] - 10.4506) < .00005
assert abs(summary['option']['MCSE'] - .0463) < .00005
report['checks']['path_counts_and_pricing_match'] = True

manifest = [TARGET.relative_to(ROOT).as_posix(), 'data/monte-carlo/returns.csv',
            'data/monte-carlo/adjusted_prices.csv', 'data/monte-carlo/stock_pool.csv',
            'data/monte-carlo/portfolio-results/portfolio_weights.csv',
            'figs/raw/mc-valuation-fig01-mechanism-corrected-20261017-225145.png']
clean = OUT / 'clean-repository'
for relative in manifest:
    destination = clean / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / relative, destination)
report['clean_repository_files'] = [{'path': path, 'sha256': digest(ROOT / path)} for path in manifest]
print('Executing again from a clean, manifest-only repository copy...', flush=True)
clean_results = clean / 'output/monte-carlo/cases'
clean_notebook = execute(clean / TARGET.relative_to(ROOT), clean / 'notebooks/monte-carlo', clean_results)
nbformat.write(clean_notebook, OUT / 'clean-executed.ipynb')
for relative in ['case1/estimates.npz', 'valuation/scenarios.npz', 'block-returns.npz', 'portfolio-single-day.npz']:
    before = np.load(results / relative)
    after = np.load(clean_results / relative)
    assert before.files == after.files and all(np.array_equal(before[key], after[key]) for key in before.files)
for relative in ['portfolio-risk-metrics.csv', 'block-metrics-all.csv', 'path-events.csv',
                 'portfolio-stability.csv', 'valuation/price-results.csv']:
    pd.testing.assert_frame_equal(pd.read_csv(results / relative), pd.read_csv(clean_results / relative), check_exact=True)
assert json.loads((clean_results / 'run-summary.json').read_text(encoding='utf-8')) == summary
report['clean_repository_execution'] = {'success': True, 'all_output_arrays_and_tables_identical': True,
                                         'not_a_remote_clone_or_clean_environment_install': True}
assert original_hashes == {path.name: digest(path) for path in original_files}
report['old_five_notebooks_unchanged'] = True

existing = {digest(path): path for path in (ROOT / 'figs/raw').glob('*.png')}
timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
figures = []
for cell_index, cell in enumerate(notebook.cells):
    if cell.cell_type != 'code':
        continue
    for output in cell.outputs:
        encoded = output.get('data', {}).get('image/png')
        if not encoded:
            continue
        if isinstance(encoded, list):
            encoded = ''.join(encoded)
        raw = base64.b64decode(encoded)
        sha = hashlib.sha256(raw).hexdigest()
        number = len(figures) + 1
        if sha in existing:
            path = existing[sha]
            new = False
        else:
            path = ROOT / f'figs/raw/mc-cases-fig{number:02d}-notebook-{timestamp}.png'
            path.write_bytes(raw)
            existing[sha] = path
            new = True
        figures.append({'cell': cell_index, 'path': path.relative_to(ROOT).as_posix(),
                        'new_asset': new, 'sha256': sha})
report['figures'] = figures
report['notebook_sha256'] = digest(TARGET)
(OUT / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
