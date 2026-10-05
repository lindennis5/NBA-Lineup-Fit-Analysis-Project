"""Lagged player profiles, transparent deficiency and complementarity specifications."""
import numpy as np
import pandas as pd
from .lineups import load_rows, SEASONS
from .data_pipeline import RAW, OUT

SKILLS=['spacing','playmaking','creation','rebounding','interior']
EVENTS=['FG2M','FG2A','FG3M','FG3A','FtPoints','FTA','Points','Assists',
        'Turnovers','OffRebounds','DefRebounds','Steals','Blocks','Fouls',
        'PtsUnassisted2s','PtsUnassisted3s','PtsPutbacks']

def zscore(values):
    sd=values.std(ddof=0)
    if not np.isfinite(sd) or sd<=0:
        raise ValueError('Degenerate normalization population')
    return (values-values.mean())/sd

def player_profiles(seasons=SEASONS, minimum_minutes=500):
    profiles=[]
    for season in seasons:
        start=int(season[:4]); prior=f'{start-1}-{start%100:02d}'
        p=pd.DataFrame(load_rows(RAW/f'pbp_{prior}_Player.json'))
        if p.EntityId.duplicated().any():
            raise ValueError('League player totals must have one row per player, including traded players')
        if len(p)>=500 and p.SecondsPlayed.min()/60>=minimum_minutes:
            raise ValueError('Player cap may exclude normalization-eligible players')
        p=p[p.SecondsPlayed>=minimum_minutes*60].copy()
        if any(c not in p for c in EVENTS):
            raise ValueError('Player source schema changed')
        p[EVENTS]=p[EVENTS].fillna(0)
        if (p.OffPoss<=0).any() or (p.DefPoss<=0).any():
            raise ValueError('Invalid profile denominators')
        fga=p.FG2A+p.FG3A; fgm=p.FG2M+p.FG3M
        league_3=p.FG3M.sum()/p.FG3A.sum()
        # Fixed 100-attempt pseudo-count avoids treating 0/0 as a zero-percent shooter.
        accuracy=(p.FG3M+100*league_3)/(p.FG3A+100)
        components=pd.DataFrame(index=p.index)
        components['three_volume']=100*p.FG3A/p.OffPoss
        components['three_accuracy']=accuracy
        components['assists']=100*p.Assists/p.OffPoss
        components['unassisted_points']=100*(p.PtsUnassisted2s+p.PtsUnassisted3s)/p.OffPoss
        components['off_rebounds']=100*p.OffRebounds/p.OffPoss
        components['def_rebounds']=100*p.DefRebounds/p.DefPoss
        components['blocks']=100*p.Blocks/p.DefPoss
        q=(p.Points+.4*fgm-.7*fga-.4*(p.FTA-p.FtPoints)+.7*p.OffRebounds+
           .3*p.DefRebounds+p.Steals+.7*p.Assists+.7*p.Blocks-.4*p.Fouls-p.Turnovers)*2160/p.SecondsPlayed
        s=pd.DataFrame({'player_id':p.EntityId.astype(int),'name':p.Name,'season':season,
            'feature_season':prior,'prior_minutes':p.SecondsPlayed/60,'quality_gmsc36':q,
            'quality':zscore(q),'three_prior_mean':league_3})
        s['spacing']=zscore((zscore(components.three_volume)+zscore(components.three_accuracy))/2)
        s['playmaking']=zscore(components.assists)
        s['creation']=zscore(components.unassisted_points)
        s['rebounding']=zscore((zscore(components.off_rebounds)+zscore(components.def_rebounds))/2)
        s['interior']=zscore(components.blocks)
        for col in components:
            s[col+'_raw']=components[col]
        profiles.append(s)
    result=pd.concat(profiles,ignore_index=True)
    if not np.isfinite(result[SKILLS+['quality']].to_numpy()).all():
        raise ValueError('Nonfinite profile')
    result.to_csv(OUT/'player_profiles.csv',index=False)
    return result

def complementarity(core, fifth):
    """Amount of largest below-average gap closed by the resulting five-player mean."""
    core=np.asarray(core,dtype=float); fifth=np.asarray(fifth,dtype=float)
    lowest=core.min(axis=1)
    ties=np.isclose(core,lowest[:,None],atol=1e-12,rtol=0)
    gaps=np.maximum(0,-core)
    fills=np.minimum(gaps,np.maximum(0,(fifth-core)/5))
    main=(fills*ties).sum(axis=1)/ties.sum(axis=1)
    all_gap=fills.mean(axis=1)
    uncapped=(np.maximum(0,-lowest)[:,None]*fifth*ties).sum(axis=1)/ties.sum(axis=1)
    return main,all_gap,uncapped

def attach_features(observations, profiles):
    d=observations.copy()
    for role in ['c1','c2','c3','c4','fifth_id']:
        columns=['season','player_id','quality','name']+SKILLS
        p=profiles[columns].rename(columns={c:f'{role}_{c}' for c in columns if c not in ['season','player_id']})
        d=d.merge(p,left_on=['season',role],right_on=['season','player_id'],how='left',validate='many_to_one').drop(columns='player_id')
    d['profiles_complete']=d[[f'{r}_quality' for r in ['c1','c2','c3','c4','fifth_id']]].notna().all(axis=1)
    coverage=d.groupby('season').agg(core_rows=('core_key','size'),complete_rows=('profiles_complete','sum')).reset_index()
    d=d[d.profiles_complete].copy()
    for skill in SKILLS+['quality']:
        d[f'core_{skill}']=d[[f'c{i}_{skill}' for i in range(1,5)]].mean(axis=1)
        d[f'fifth_{skill}']=d[f'fifth_id_{skill}']
    core=d[[f'core_{s}' for s in SKILLS]].to_numpy()
    fifth=d[[f'fifth_{s}' for s in SKILLS]].to_numpy()
    d['weakest_skill']=[SKILLS[i] for i in core.argmin(axis=1)]
    d['deficiency_gap']=np.maximum(0,-core.min(axis=1))
    d['complementarity'],d['complementarity_all'],d['complementarity_uncapped']=complementarity(core,fifth)
    d['complementarity_no_interior'],_,_=complementarity(core[:,:4],fifth[:,:4])
    d.to_csv(OUT/'observations.csv',index=False)
    coverage.to_csv(OUT/'feature_coverage.csv',index=False)
    return d,coverage
