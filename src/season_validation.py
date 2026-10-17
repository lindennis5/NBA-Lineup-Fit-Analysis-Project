"""League conservation checks complement, rather than repeat, provider reconciliation."""
import pandas as pd
from .data_pipeline import ROOT,RAW
from .lineups import load_rows,SEASONS

def main(seasons=SEASONS):
    rows=[]
    for season in seasons:
        teams=pd.DataFrame(load_rows(RAW/f'pbp_{season}_Team.json'))
        points=float((teams.Points-teams.OpponentPoints).sum())
        possessions=float((teams.OffPoss-teams.DefPoss).sum())
        rows.append({'season':season,'teams':len(teams),'games':teams.GamesPlayed.sum()/2,
            'off_possessions':teams.OffPoss.sum(),'def_possessions':teams.DefPoss.sum(),
            'points_scored':teams.Points.sum(),'points_allowed':teams.OpponentPoints.sum(),
            'points_balance':points,'possession_balance':possessions,
            'balanced_counters':points==0 and possessions==0,
            'official_scoring_verified':season=='2022-23',
            'status':'balanced counters; lineup/game-level external validation still limited' if points==0 and possessions==0 else 'provisional: unresolved upstream counter imbalance'})
    result=pd.DataFrame(rows)
    result.to_csv(ROOT/'docs'/'season_validation_status.csv',index=False)
    return result

if __name__=='__main__':print(main().to_string(index=False))
