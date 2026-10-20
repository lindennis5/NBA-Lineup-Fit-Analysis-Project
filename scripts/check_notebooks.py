"""Fail if any notebook has an error output or references a removed figure."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOVED = ['possession_distribution', 'threshold_tradeoff', 'skill_correlation', 'performance_distribution',
           'core_example', 'model_effects']

def main():
    books = sorted((ROOT / 'notebooks').glob('*.ipynb'))
    problems = 0
    for path in books:
        text = path.read_text(encoding='utf-8')
        book = json.loads(text)
        errors = sum(1 for c in book['cells'] if c['cell_type'] == 'code'
                     for o in c.get('outputs', []) if o.get('output_type') == 'error')
        stale = [name for name in REMOVED if name in text]
        print(f'{path.name}: error_outputs={errors} removed_figure_refs={stale}')
        problems += errors + len(stale)
    print(f'{len(books)} notebooks; problems={problems}')
    sys.exit(1 if problems else 0)

if __name__ == '__main__':
    main()
