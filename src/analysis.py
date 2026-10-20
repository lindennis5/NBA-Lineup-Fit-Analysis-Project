"""Offline V1 build from verified caches: validation, EDA, models, figures, SQLite."""
import json
import argparse
import os
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[1]/'.cache'/'matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from .data_pipeline import ROOT,OUT,validate_seasons
from .lineups import build_lineups,expand_cores,threshold_table,comparison_sample,SEASONS
from .features import player_profiles,attach_features,SKILLS
from .models import run_models,leave_club_out

BLUE='#285D8F';ORANGE='#C87932';INK='#25313C'

def save_figure(fig,name):
    directory=ROOT/'figures';directory.mkdir(exist_ok=True)
    fig.savefig(directory/f'{name}.png',dpi=180,bbox_inches='tight',facecolor='white')
    fig.savefig(directory/f'{name}.svg',bbox_inches='tight',facecolor='white',metadata={'Date':None})
    plt.close(fig)

def main(seasons=SEASONS):
    validate_seasons(seasons)
    lineups,coverage=build_lineups(seasons)
    differences={}
    for field in ['SecondsPlayed','OffPoss','DefPoss','Points','OpponentPoints']:
        coverage[f'{field}_difference']=coverage[f'{field}_lineup']-coverage[f'{field}_team']
        differences[field]={'max_absolute_difference':float(coverage[f'{field}_difference'].abs().max()),
                            'total_difference':float(coverage[f'{field}_difference'].sum())}
    coverage.to_csv(ROOT/'docs'/'coverage_audit.csv',index=False)
    # Exact time/exposure checks catch omitted or overlapping intervals. Investigate before relaxing.
    qa={'reconciliation':differences,'lineups':len(lineups),'seasons':sorted(lineups.season.unique()),
        'zero_off_poss':int((lineups.off_poss==0).sum()),'zero_def_poss':int((lineups.def_poss==0).sum()),
        'nonfinite_net_rating':int((~np.isfinite(lineups.net_rating)).sum())}
    (ROOT/'docs'/'validation_summary.json').write_text(json.dumps(qa,indent=2),encoding='utf-8')
    if differences['SecondsPlayed']['max_absolute_difference']>1 or any(differences[c]['max_absolute_difference']>0 for c in ['OffPoss','DefPoss']):
        raise ValueError('Lineup/team time or possession reconciliation failed; inspect docs/coverage_audit.csv')
    observations=expand_cores(lineups)
    observations.to_csv(OUT/'core_observations_unfiltered.csv',index=False)
    profiles=player_profiles(seasons)
    featured,feature_coverage=attach_features(observations,profiles)
    raw_thresholds=threshold_table(observations);feature_thresholds=threshold_table(featured)
    raw_thresholds.to_csv(OUT/'thresholds_before_profiles.csv',index=False)
    feature_thresholds.to_csv(OUT/'thresholds_after_profiles.csv',index=False)
    sample=comparison_sample(featured,50)
    if not ((profiles.season.str[:4].astype(int)-profiles.feature_season.str[:4].astype(int))==1).all():
        raise ValueError('Temporal leakage in features')
    coefficients=run_models(featured)
    heldout=leave_club_out(featured)
    lineups.groupby('season').agg(lineups=('lineup_key','size'),mean_side_possessions=('possessions','sum'),minutes=('minutes','sum')).to_csv(OUT/'season_summary.csv')
    team_summary=sample.groupby(['season','team_id','team']).agg(core_rows=('core_key','size'),cores=('core_key','nunique'),lineups=('lineup_key','nunique'))
    team_summary.to_csv(OUT/'team_comparison_coverage.csv')
    sample.drop_duplicates('core_key').groupby('weakest_skill').agg(cores=('core_key','size'),mean_gap=('deficiency_gap','mean')).to_csv(OUT/'deficiency_summary.csv')
    with sqlite3.connect(OUT/'analysis.sqlite') as connection:
        lineups.to_sql('lineups',connection,if_exists='replace',index=False)
        featured[['season','team_id','team','lineup_key','core_key','fifth_id','min_side_poss','possessions','net_rating','fifth_quality','complementarity']].to_sql('observations',connection,if_exists='replace',index=False)
        connection.execute('CREATE UNIQUE INDEX IF NOT EXISTS observation_key ON observations(core_key,fifth_id)')
        sql=(ROOT/'sql'/'analysis_queries.sql').read_text(encoding='utf-8')
        sql_result=pd.read_sql_query(sql,connection)
    sql_result.to_csv(OUT/'sql_threshold_audit.csv',index=False)
    expected=feature_thresholds.set_index('threshold').loc[sql_result.threshold,'comparison_cores'].to_numpy()
    if not np.array_equal(sql_result.comparison_cores.to_numpy(),expected):
        raise ValueError('Independent SQL threshold audit failed')
    comparison_exposure=sample.drop_duplicates('lineup_key').possessions.sum()
    summary={'status':'observational_analysis','seasons':seasons,'unique_lineups':len(lineups),
        'all_cores':observations.core_key.nunique(),'all_core_fifth_rows':len(observations),
        'all_mean_side_possessions':float(lineups.possessions.sum()),'eligible_player_profiles':len(profiles),
        'feature_complete_lineups':featured.lineup_key.nunique(),'feature_complete_rows':len(featured),
        'primary_rows':len(sample),'primary_cores':sample.core_key.nunique(),'primary_lineups':sample.lineup_key.nunique(),
        'primary_mean_side_possessions':float(comparison_exposure),'primary_clubs':sample.team_id.nunique(),
        'talent_complementarity_correlation':float(sample.fifth_quality.corr(sample.complementarity)),
        'zero_fill_share':float((sample.complementarity==0).mean()),
        'no_gap_core_share':float((sample.drop_duplicates('core_key').deficiency_gap==0).mean()),
        'heldout_rmse':{str(model):float(np.sqrt(g.squared_error_sum.sum()/g.weight_sum.sum())) for model,g in heldout.groupby('model')}}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (ROOT/'docs'/'results_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    # Small derived results are versioned; bulk player/lineup data are deliberately not.
    for name in ['model_coefficients','thresholds_before_profiles','thresholds_after_profiles','feature_coverage','season_summary','heldout_club_validation','deficiency_summary','sql_threshold_audit']:
        (ROOT/'docs'/f'{name}.csv').write_bytes((OUT/f'{name}.csv').read_bytes())
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--seasons',nargs='+',default=SEASONS)
    main(parser.parse_args().seasons)
