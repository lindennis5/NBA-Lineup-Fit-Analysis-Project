"""Static, reproducible uncertainty and predictive comparisons for the release."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from .analysis import save_figure, BLUE, ORANGE, INK
from .data_pipeline import ROOT, OUT
from .lineups import comparison_sample
from .features import SKILLS

def main():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.hashsalt':'nba-lineup-fit',
        'axes.spines.top':False,'axes.spines.right':False})
    coefficients=pd.read_csv(ROOT/'docs'/'extended_coefficients.csv')
    d=coefficients[(coefficients.term=='complementarity') & (coefficients.specification=='primary') & (coefficients.threshold==50)]
    fig,ax=plt.subplots(figsize=(9,5))
    y=np.arange(len(d));beta=d.coefficient.to_numpy()*.1
    ax.errorbar(beta,y,xerr=np.vstack([beta-.1*d.ci_low.to_numpy(),.1*d.ci_high.to_numpy()-beta]),fmt='o',color=BLUE,capsize=5)
    ax.axvline(0,color=INK,lw=1,ls='--')
    ax.set(yticks=y,yticklabels=d.scope,xlabel='Net points / 100 possessions per 0.1 gap unit',title='Season-specific and pooled fit associations')
    fig.text(.1,.02,'50+ possessions each side; lagged profiles with 500+ minutes.\n95% franchise-clustered intervals. 2024-25, 2025-26 and pooled: provisional source counters.\nBalanced source seasons: 2022-23 and 2023-24. Source: PBP Stats.',fontsize=8)
    fig.tight_layout(rect=[0,.12,1,1]);save_figure(fig,'season_effects')
    lineups=pd.read_csv(OUT/'observations.csv').drop_duplicates('lineup_key')
    lineups=lineups[lineups.min_side_poss>=50]
    fig,ax=plt.subplots(figsize=(9,5))
    ax.hist(lineups.net_rating,bins=45,color=BLUE,edgecolor='white')
    ax.set(xlabel='Observed net points per 100 possessions',ylabel='Unique season-team lineups',title='Distribution of eligible lineup performance')
    fig.text(.1,.02,f'{len(lineups):,} unique lineups; 50+ possessions each side and all five lagged profiles.\nSource: PBP Stats. Unweighted histogram; this is not the within-core comparison sample.',fontsize=9)
    fig.tight_layout(rect=[0,.09,1,1]);save_figure(fig,'performance_distribution')
    observations=pd.read_csv(OUT/'observations.csv')
    knicks=comparison_sample(observations[observations.team=='NYK'],50)
    key=knicks.groupby('core_key').possessions.sum().idxmax()
    example=knicks[knicks.core_key==key].sort_values('possessions',ascending=False)
    names=[example.iloc[0][f'c{i}_name'] for i in range(1,5)]
    columns=['season','team','core_key','fifth_id_name','possessions','net_rating','weakest_skill','deficiency_gap','complementarity']
    columns += [f'c{i}_name' for i in range(1,5)]+[f'core_{s}' for s in SKILLS]+[f'fifth_{s}' for s in SKILLS]
    example[columns].to_csv(ROOT/'docs'/'knicks_example.csv',index=False)
    fig,ax=plt.subplots(figsize=(10,6));y=np.arange(5)
    ax.barh(y-.24,[example.iloc[0][f'core_{s}'] for s in SKILLS],height=.24,color='#9CA7AF',label='Four-player core')
    for i,(_,r) in enumerate(example.head(2).iterrows()):
        ax.barh(y+i*.24,[r[f'fifth_{s}'] for s in SKILLS],height=.24,color=[BLUE,ORANGE][i],
            hatch=None if i==0 else '//',label=r.fifth_id_name)
    ax.axvline(0,color=INK,lw=.8)
    ax.set(yticks=y,yticklabels=SKILLS,xlabel='Prior-season standardized skill score',
        title=f'New York Knicks: core and fifth-player profiles | {example.iloc[0].season}')
    ax.legend(frameon=False,loc='best',fontsize=9)
    fig.text(.12,.90,'Core: '+', '.join(names[:2])+'\n'+', '.join(names[2:]),fontsize=9)
    fig.text(.12,.02,'Highest-exposure eligible Knicks core; two fifth players selected by exposure.\nIllustration, not a causal substitution estimate. Interior = blocks only. Source: PBP Stats.',fontsize=9)
    fig.tight_layout(rect=[0,.09,1,.88]);save_figure(fig,'knicks_example')
    path=ROOT/'docs'/'season_forward_validation.csv'
    if path.stat().st_size>5:
        cv=pd.read_csv(path);pivot=cv.pivot(index='test_season',columns='model',values='rmse')
        fig,ax=plt.subplots(figsize=(9,5));x=np.arange(len(pivot))
        ax.bar(x-.18,pivot.baseline,.36,label='Talent + skills',color=BLUE)
        ax.bar(x+.18,pivot.complementarity,.36,label='+ Complementarity',color=ORANGE,hatch='//')
        ax.set(xticks=x,xticklabels=pivot.index,ylabel='Within-core contrast RMSE',title='Season-forward validation')
        ax.legend(frameon=False);ax.set_ylim(bottom=0)
        for i,(_,r) in enumerate(pivot.iterrows()):
            ax.text(i,max(r)+.15,f'Difference: {r.complementarity-r.baseline:+.3f}',ha='center',fontsize=9)
        fig.text(.1,.02,'Train on earlier seasons only; lower RMSE is better. Source: PBP Stats.\nOutcome demeaning scores contrasts; this is not prediction of absolute lineup ratings.',fontsize=9)
        fig.tight_layout(rect=[0,.09,1,1]);save_figure(fig,'forward_prediction')

if __name__=='__main__':main()
