"""Static-site checks: links/images resolve, alt text present, no external scripts or styles."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from check_links import references  # noqa: E402

def main():
    page = ROOT / 'site' / 'index.html'
    external_code = [u for kind, u, _ in references(page) if kind == 'script' or
                     (kind == 'link' and u.endswith('.css') and u.startswith('http'))]
    print(f'external scripts/styles: {len(external_code)}')
    size = sum(p.stat().st_size for p in (ROOT / 'site').rglob('*') if p.is_file())
    print(f'site size: {size / 1e6:.2f} MB')
    links = subprocess.run([sys.executable, str(Path(__file__).parent / 'check_links.py'), str(page)])
    sys.exit(1 if external_code or links.returncode or size > 10e6 else 0)

if __name__ == '__main__':
    main()
