"""One entry point for the cached NBA Lineup Fit workflow."""
import argparse
from src.data_pipeline import download,validate_seasons
from src.lineups import SEASONS

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seasons',nargs='+',default=SEASONS,help='Consecutive NBA seasons, e.g. 2022-23 2023-24')
    parser.add_argument('--download',action='store_true',help='Retrieve missing public source caches before analysis')
    parser.add_argument('--download-only',action='store_true',help='Retrieve data without fitting models')
    parser.add_argument('--notebooks',action='store_true',help='Build and execute the six companion notebooks')
    parser.add_argument('--workers',type=int,choices=[1,2,3],default=3)
    args=parser.parse_args()
    validate_seasons(args.seasons)
    if args.download or args.download_only:
        download(args.seasons,workers=args.workers)
    if args.download_only:
        return
    from src.analysis import main as analyze
    analyze(args.seasons)
    if args.notebooks:
        from src.notebooks import main as notebooks
        notebooks()

if __name__=='__main__':main()
