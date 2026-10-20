"""Compare local raw payload checksums with docs/raw_inventory.json (meta files excluded)."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    inventory = json.loads((ROOT / 'docs' / 'raw_inventory.json').read_text(encoding='utf-8'))
    expected = {Path(r['path'].replace('\\', '/')).name: r['sha256']
                for r in inventory if not r['path'].endswith('.meta.json')}
    raw = ROOT / 'data' / 'raw'
    missing = [n for n in expected if not (raw / n).exists()]
    mismatched = [n for n in expected if (raw / n).exists()
                  and hashlib.sha256((raw / n).read_bytes()).hexdigest() != expected[n]]
    extra = [p.name for p in raw.glob('*.json') if not p.name.endswith('.meta.json') and p.name not in expected]
    print(f'payload files in inventory: {len(expected)}; missing: {len(missing)}; '
          f'mismatched: {len(mismatched)}; not in inventory: {len(extra)}')
    for label, names in [('missing', missing), ('mismatched', mismatched), ('extra', extra)]:
        for n in names[:20]:
            print(f'  {label}: {n}')
    sys.exit(1 if missing or mismatched else 0)

if __name__ == '__main__':
    main()
