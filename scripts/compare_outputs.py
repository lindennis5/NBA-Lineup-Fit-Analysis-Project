"""Compare regenerated result tables with a frozen snapshot, within a numeric tolerance.

Usage: python scripts/compare_outputs.py SNAPSHOT_DIR CURRENT_DIR [tolerance]
"""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

SKIP = {'release_run_manifest.json', 'data_manifest.json', 'raw_inventory.json',
        'access_probes.json', 'download_failures.json'}

def flatten(value, prefix=''):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from flatten(v, f'{prefix}{k}.')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from flatten(v, f'{prefix}{i}.')
    else:
        yield prefix.rstrip('.'), value

def close(a, b, tol):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return bool(np.isclose(a, b, atol=tol, rtol=tol, equal_nan=True))
    return a == b

def main():
    old, new = Path(sys.argv[1]), Path(sys.argv[2])
    tol = float(sys.argv[3]) if len(sys.argv) > 3 else 1e-9
    compared = failures = 0
    for path in sorted(old.glob('*')):
        if path.name in SKIP or path.suffix not in ('.csv', '.json') or not (new / path.name).exists():
            continue
        compared += 1
        if path.suffix == '.json':
            a = dict(flatten(json.loads(path.read_text(encoding='utf-8'))))
            b = dict(flatten(json.loads((new / path.name).read_text(encoding='utf-8'))))
            bad = [k for k in a.keys() | b.keys() if k not in a or k not in b or not close(a[k], b[k], tol)]
        else:
            a, b = pd.read_csv(path), pd.read_csv(new / path.name)
            if a.shape != b.shape or list(a.columns) != list(b.columns):
                bad = ['shape/columns']
            else:
                bad = []
                for c in a.columns:
                    if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c]):
                        if not np.allclose(a[c], b[c], atol=tol, rtol=tol, equal_nan=True):
                            bad.append(c)
                    elif not a[c].astype(str).equals(b[c].astype(str)):
                        bad.append(c)
        if bad:
            failures += 1
            print(f'DIFF {path.name}: {bad[:5]}')
    print(f'files compared: {compared}; files with differences beyond {tol}: {failures}')
    sys.exit(1 if failures else 0)

if __name__ == '__main__':
    main()
