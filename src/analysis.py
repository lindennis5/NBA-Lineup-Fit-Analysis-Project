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
    fig.savefig(directory/f'{name}.svg',bbox_inches='tight',facecolor='white')
    plt.close(fig)

def make_figures(lineups, observations, profiles, raw_thresholds, feature_thresholds, coefficients):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
        'axes.spines.right':False,'axes.labelcolor':INK,'text.color':INK,'axes.titlecolor':INK,
        'axes.titleweight':'bold','figure.facecolor':'white','axes.facecolor':'white'})
    window=lineups.season.min() if lineups.season.nunique()==1 else f'{lineups.season.min()} through {lineups.season.max()}'
    source='Source: PBP Stats; regular season. Calculations: NBA Lineup Fit.'
    positive=lineups[lineups.possessions>0]
    fig,ax=plt.subplots(figsize=(9,5.5))
    ax.hist(positive.possessions,bins=np.geomspace(.5,positive.possessions.max()*1.01,45),color=BLUE,edgecolor='white',linewidth=.5)
    ax.set_xscale('log');ax.set(xlabel='Mean of offensive and defensive possessions (log scale)',ylabel='Unique five-player lineups',
        title=f'Lineup possession distribution | {window}')
    ax.text(0,1.02,f'{len(positive):,} positive-exposure lineups; {len(lineups)-len(positive):,} zero-exposure lineups omitted',transform=ax.transAxes,fontsize=9)
    ax.set_title(ax.get_title(),pad=32)
    fig.text(.08,.01,source,fontsize=8);fig.tight_layout(rect=[0,.03,1,1]);save_figure(fig,'possession_distribution')

    a=raw_thresholds.set_index('threshold').loc[[25,50,100,200]]
    b=feature_thresholds.set_index('threshold').loc[[25,50,100,200]]
    fig,ax=plt.subplots(figsize=(9,5.5));x=np.arange(4)
    ax.bar(x-.19,a.comparison_cores,.38,color=BLUE,label='Before profile filter')
    ax.bar(x+.19,b.comparison_cores,.38,color=ORANGE,label='All five lagged profiles eligible')
    ax.set(xticks=x,xticklabels=a.index,xlabel='Minimum possessions on each side per lineup',ylabel='Cores with at least two fifth players',title=f'Sample threshold tradeoff | {window}')
    ax.legend(frameon=False);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    fig.text(.08,.01,source+' Profile eligibility: 500 prior-season minutes.',fontsize=8)
    fig.tight_layout(rect=[0,.03,1,1]);save_figure(fig,'threshold_tradeoff')

    corr=profiles[SKILLS+['quality']].corr()
    fig,ax=plt.subplots(figsize=(8,6))
    image=ax.imshow(corr,vmin=-1,vmax=1,cmap=LinearSegmentedColormap.from_list('profile_correlation',[ORANGE,'white',BLUE]))
    labels=SKILLS+['quality proxy']
    ax.set(xticks=range(6),yticks=range(6),xticklabels=labels,yticklabels=labels,title='Prior-season player-profile correlations')
    plt.setp(ax.get_xticklabels(),rotation=35,ha='right')
    for i in range(6):
        for j in range(6): ax.text(j,i,f'{corr.iloc[i,j]:.2f}',ha='center',va='center',color='white' if abs(corr.iloc[i,j])>.65 else INK)
    fig.colorbar(image,ax=ax,label='Pearson correlation',shrink=.75)
    feature_window=profiles.feature_season.min() if profiles.feature_season.nunique()==1 else f'{profiles.feature_season.min()} to {profiles.feature_season.max()}'
    fig.text(.07,.015,f'{len(profiles):,} eligible profiles | feature seasons: {feature_window}.\n'+source,fontsize=8)
    fig.tight_layout(rect=[0,.05,1,1]);save_figure(fig,'skill_correlation')

    sample=comparison_sample(observations,50)
    fig,ax=plt.subplots(figsize=(9,5.5))
    image=ax.hexbin(sample.fifth_quality,sample.complementarity,gridsize=40,mincnt=1,cmap='Blues',bins='log')
    ax.set(xlabel='Prior Game Score/36 (seasonal z-score)',ylabel='Largest-gap closure (standardized skill units)',title=f'Talent proxy and complementarity | {window}')
    ax.text(0,1.02,f'{len(sample):,} core/fifth rows; 50+ possessions per side; descriptive, dependent observations',transform=ax.transAxes,fontsize=9)
    ax.set_title(ax.get_title(),pad=32)
    fig.colorbar(image,ax=ax,label='Core/fifth rows per hexagon (log color scale)')
    fig.text(.08,.01,source,fontsize=8);fig.tight_layout(rect=[0,.03,1,1]);save_figure(fig,'talent_complementarity')

    effect=coefficients[(coefficients.term=='complementarity')&coefficients.weighted&coefficients.skill_controls].sort_values('threshold')
    fig,ax=plt.subplots(figsize=(9,5.5))
    yy=np.arange(len(effect));beta=effect.coefficient.to_numpy()*.1
    ax.errorbar(beta,yy,xerr=np.vstack([beta-effect.ci_low.to_numpy()*.1,effect.ci_high.to_numpy()*.1-beta]),fmt='o',color=BLUE,capsize=5)
    ax.axvline(0,color=INK,lw=1,ls='--')
    ax.set(yticks=yy,yticklabels=[f'{int(v)}+ possessions per side' for v in effect.threshold],xlabel='Net points per 100 possessions per 0.1 skill-unit gap closed',title='Largest-gap closure: adjusted association')
    ax.text(0,1.02,'Core fixed effects + fifth-player quality and skills; 95% club-clustered intervals',transform=ax.transAxes,fontsize=9)
    ax.set_title(ax.get_title(),pad=32)
    fig.text(.08,.01,f'{window}. Observational; not a causal effect. '+source,fontsize=8)
    fig.tight_layout(rect=[0,.04,1,1]);save_figure(fig,'model_effects')

    key=sample.groupby('core_key').possessions.sum().idxmax()
    example=sample[sample.core_key==key].sort_values('possessions',ascending=False).head(2)
    first=example.iloc[0]
    fig,ax=plt.subplots(figsize=(10,6.5));y=np.arange(5)
    ax.barh(y-.25,[first[f'core_{s}'] for s in SKILLS],height=.24,color='#9CA7AF',label='Four-player average')
    for i,(_,row) in enumerate(example.iterrows()):
        ax.barh(y+i*.25,[row[f'fifth_{s}'] for s in SKILLS],height=.24,color=[BLUE,ORANGE][i],label=row.fifth_id_name)
    ax.axvline(0,color=INK,lw=.8);ax.set(yticks=y,yticklabels=SKILLS,xlabel='Prior-season skill z-score',title=f'Core skill profile example | {first.team} {first.season}')
    names=', '.join(str(first[f'c{i}_name']) for i in range(1,5))
    fig.text(.09,.89,names,fontsize=9)
    ax.legend(frameon=False,loc='lower right')
    fig.text(.09,.02,'Core and fifth players selected by exposure, not outcome. Interior = block activity only.\n'+source,fontsize=8)
    fig.tight_layout(rect=[0,.06,1,.89]);save_figure(fig,'core_example')
    keep=['season','team','core_id','fifth_id','fifth_id_name','possessions','net_rating','fifth_quality','weakest_skill','deficiency_gap','complementarity']
    sample[sample.core_key==key][keep].sort_values('possessions',ascending=False).to_csv(OUT/'core_example.csv',index=False)

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
    make_figures(lineups,featured,profiles,raw_thresholds,feature_thresholds,coefficients)
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
    summary={'status':'preliminary_observational_v1','seasons':seasons,'unique_lineups':len(lineups),
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
