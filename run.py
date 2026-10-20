"""One entry point for the cached NBA Lineup Fit workflow."""
import argparse
from src.data_pipeline import download,validate_seasons
from src.lineups import SEASONS

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seasons',nargs='+',default=SEASONS,help='Consecutive NBA seasons, e.g. 2022-23 2023-24')
    parser.add_argument('--download',action='store_true',help='Retrieve missing public source caches before analysis')
    parser.add_argument('--download-only',action='store_true',help='Retrieve data without fitting models')
    parser.add_argument('--notebooks',action='store_true',help='Build and execute companion notebooks, including the release audit when available')
    parser.add_argument('--release',action='store_true',help='Run extended inference, forward validation, official pilot checks and release figures')
    parser.add_argument('--workers',type=int,choices=[1,2,3],default=3)
    args=parser.parse_args()
    validate_seasons(args.seasons)
    if args.download or args.download_only:
        download(args.seasons,workers=args.workers)
    if args.download_only:
        return
    from src.analysis import main as analyze
    analyze(args.seasons)
    if args.release:
        from src.release_audit import run as audit
        from src.official_validation import main as official
        from src.external_validation import main as external
        from src.structural_checks import main as structural
        from src.final_robustness import main as robustness
        from src.metric_comparison import main as metrics
        from src.final_figures import main as figures
        from src.claims import main as claims
        from src.snapshots import main as snapshot
        audit()
        official()
        if list(args.seasons)==SEASONS:   # final audit steps need all four seasons
            external()
            structural()
            robustness()
            metrics()
            figures()
            claims()
        else:
            print('Final audit steps skipped: they require all four seasons.')
        snapshot()
    if args.notebooks:
        from src.notebooks import main as notebooks
        notebooks()

if __name__=='__main__':main()
