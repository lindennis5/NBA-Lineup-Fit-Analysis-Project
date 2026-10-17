"""Compare provider totals to the Thunder's official 2023-24 media guide.

Benchmark transcribed from printed pp. 102-103 (PDF page index 51),
2022-23 offensive/defensive statistics. Not an independent possession audit.
Source: https://cdn.nba.com/teams/uploads/sites/1610612760/2023/10/mediaguide-2324.pdf
"""
import pandas as pd
from .data_pipeline import RAW, ROOT
from .lineups import load_rows

def main():
    official=pd.read_csv(ROOT/'docs'/'official_2022_23_benchmark.csv')
    provider=pd.DataFrame(load_rows(RAW/'pbp_2022-23_Team.json'))
    # Provider abbreviations are normalized explicitly, never matched by row order.
    provider['team']=provider.TeamAbbreviation.replace({'BRK':'BKN','PHO':'PHX'})
    result=official.merge(provider[['team','GamesPlayed','Points','OpponentPoints']],on='team',validate='one_to_one',how='outer',indicator=True)
    if len(result)!=30 or not result['_merge'].eq('both').all():
        raise ValueError('Official/provider team crosswalk mismatch')
    for official_col,pbp_col in [('games','GamesPlayed'),('points','Points'),('opponent_points','OpponentPoints')]:
        result[official_col+'_difference']=result[pbp_col]-result[official_col]
    result.drop(columns='_merge').to_csv(ROOT/'docs'/'official_reconciliation.csv',index=False)
    print(result.filter(regex='difference$').abs().max().to_dict())
    if result.filter(regex='difference$').ne(0).any().any():
        raise ValueError('Official scoring/game discrepancy; inspect official_reconciliation.csv')

if __name__=='__main__':main()
