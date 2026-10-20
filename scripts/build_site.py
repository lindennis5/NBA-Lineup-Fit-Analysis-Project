"""Copy release figures into site/assets so the static site is self-contained."""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ['season_effects', 'knicks_example', 'metric_comparison', 'core_deficiencies',
           'talent_complementarity', 'forward_prediction', 'robustness_effects']

def main():
    assets = ROOT / 'site' / 'assets'
    assets.mkdir(parents=True, exist_ok=True)
    for name in FIGURES:
        shutil.copyfile(ROOT / 'figures' / f'{name}.png', assets / f'{name}.png')
    print(f'copied {len(FIGURES)} figures to site/assets')

if __name__ == '__main__':
    main()
