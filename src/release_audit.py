"""Reproducible extensions; never substitutes synthetic rows for NBA observations.

Run after run.py. Writes small, versioned audit outputs. Sensitivity experiments
operate in memory without replacing primary profile or observation files.
"""
import hashlib
import json
import platform
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import t
from .data_pipeline import ROOT, OUT, RAW
from .features import player_profiles, attach_features, SKILLS, zscore
from .lineups import comparison_sample
from .models import fit_within
from .season_validation import main as validate_source_seasons

DOC=ROOT/'docs'

def demean(d, columns, w):
    values=d[columns]
    return values-values.mul(w,axis=0).groupby(d.core_key).transform('sum').div(
        w.groupby(d.core_key).transform('sum'),axis=0)

def inference(d, seed=20261016, draws=1999):
    """Restricted wild franchise bootstrap-t for H0: complementarity=0.

    All representations of a franchise receive the same Rademacher multiplier.
    Works on absorbed, whitened WLS data; fixed design and CR1 studentization.
    This does not repair cross-franchise shared-game dependence.
    """
    if draws<1:
        raise ValueError('Bootstrap draws must be positive')
    table,fit,sample=fit_within(d)
    cols=list(fit.params.index);j=cols.index('complementarity')
    x=np.asarray(fit.model.wexog);y=np.asarray(fit.model.wendog)
    codes,clubs=pd.factorize(sample.team_id);g=len(clubs);n,p=x.shape
    correction=g/(g-1)*(n-1)/(n-sample.core_key.nunique()-p)
    inv=np.linalg.inv(x.T@x)
    def statistic(outcome):
        beta=inv@x.T@outcome;resid=outcome-x@beta
        scores=np.zeros((g,p));np.add.at(scores,codes,x*resid[:,None])
        variance=correction*(inv@(scores.T@scores)@inv)[j,j]
        return beta[j]/np.sqrt(variance)
    xr=np.delete(x,j,axis=1);fitted0=xr@np.linalg.lstsq(xr,y,rcond=None)[0]
    residual0=y-fitted0;rng=np.random.default_rng(seed)
    observed=statistic(y);extreme=0
    for _ in range(draws):
        signs=rng.choice([-1.,1.],g)
        extreme+=abs(statistic(fitted0+residual0*signs[codes]))>=abs(observed)
    jack=[]
    for club in clubs:
        _,f,_=fit_within(d[d.team_id!=club])
        jack.append(float(f.params['complementarity']))
    jack=np.array(jack);se=np.sqrt((g-1)/g*np.sum((jack-jack.mean())**2))
    beta=float(fit.params['complementarity']);crit=t.ppf(.975,g-1)
    residual_fit=sm.WLS(x[:,j],np.delete(x,j,axis=1)).fit()
    leverage=(x@inv*x).sum(axis=1)
    return {'seed':seed,'draws':draws,'observed_t':float(observed),'wild_cluster_p':(extreme+1)/(draws+1),
        'wild_null':0,'jackknife_se':se,'jackknife_ci_low':beta-crit*se,
        'jackknife_ci_high':beta+crit*se,'leave_franchise_out_min':float(jack.min()),
        'leave_franchise_out_max':float(jack.max()),'clusters':g,
        'conditional_fit_variance_share':float(np.sum(residual_fit.resid**2)/np.sum(x[:,j]**2)),
        'slope_leverage_max':float(leverage.max()),
        'lineup_weight_kish':float(sample.drop_duplicates('lineup_key').possessions.sum()**2/
            (sample.drop_duplicates('lineup_key').possessions**2).sum()),
        'note':'Kish count describes exposure concentration, not independent information or inferential degrees of freedom.'}

def score_contrasts(train,test,return_clubs=False):
    if train.season.max()>=test.season.min():
        raise ValueError('Forward validation requires training seasons before test seasons')
    test=comparison_sample(test,50).reset_index(drop=True)
    w=test.possessions/test.groupby('lineup_key').lineup_key.transform('size')
    records=[];club_records=[]
    for fit_column in [None,'complementarity']:
        _,f,_=fit_within(train,fit_column=fit_column)
        cols=list(f.params.index);v=demean(test,['net_rating']+cols,w)
        error=v.net_rating-v[cols].to_numpy()@f.params.to_numpy()
        records.append({'model':fit_column or 'baseline','rmse':float(np.sqrt(np.sum(w*error**2)/w.sum())),
            'mae':float(np.sum(w*abs(error))/w.sum()),'rows':len(test),
            'lineups':test.lineup_key.nunique(),'weight_sum':float(w.sum())})
        scored=pd.DataFrame({'team_id':test.team_id,'squared_error_sum':w*error**2,
            'absolute_error_sum':w*abs(error),'weight_sum':w})
        club_records.extend(scored.groupby('team_id').sum().reset_index().assign(model=fit_column or 'baseline').to_dict('records'))
    return (records,club_records) if return_clubs else records

def predictive_uncertainty(club_records,seed=20261016,draws=1999):
    """Paired franchise resampling of fixed, already-held-out predictions.

    Resamples test franchise blocks across all forward folds together. Does not
    refit training models; intervals are conditional scoring uncertainty only.
    """
    d=pd.DataFrame(club_records)
    totals=d.groupby(['team_id','model'])[['squared_error_sum','weight_sum']].sum()
    base=totals.xs('baseline',level='model');fit=totals.xs('complementarity',level='model').reindex(base.index)
    if not np.allclose(base.weight_sum,fit.weight_sum):raise ValueError('Unequal prediction samples')
    arrays=np.column_stack([base.squared_error_sum,fit.squared_error_sum,base.weight_sum])
    def delta(a):
        b,f,w=a.sum(axis=0);return np.sqrt(f/w)-np.sqrt(b/w)
    rng=np.random.default_rng(seed)
    values=[delta(arrays[rng.integers(0,len(arrays),len(arrays))]) for _ in range(draws)]
    return {'delta_rmse':float(delta(arrays)),'ci_low':float(np.quantile(values,.025)),
        'ci_high':float(np.quantile(values,.975)),'draws':draws,'seed':seed,'clubs':len(arrays),
        'interpretation':'Positive means worse with fit. Conditional on fitted models; training variability and cross-franchise dependence not represented.'}

def run():
    d=pd.read_csv(OUT/'observations.csv');seasons=sorted(d.season.unique())
    results=[];uncertainty={};forward=[];forward_clubs=[]
    status=validate_source_seasons(seasons)
    balanced=status.loc[status.balanced_counters,'season'].tolist()
    if balanced and len(balanced)<len(seasons):
        subset=d[d.season.isin(balanced)]
        for threshold in [25,50,100]:
            table,_,_=fit_within(subset,threshold)
            results.append(table.assign(scope='balanced_source_seasons',specification='primary'))
        uncertainty['balanced_source_seasons']=inference(subset)
    alternate=d.copy()
    alternate['net_rating']=100*(alternate.points-alternate.opponent_points)/alternate.possessions
    table,_,_=fit_within(alternate)
    results.append(table.assign(scope='pooled',specification='common_denominator_outcome'))
    alternate['net_rating']=100*alternate.provider_plusminus/alternate.possessions
    table,_,_=fit_within(alternate)
    results.append(table.assign(scope='pooled',specification='provider_plusminus_outcome'))
    if 'plusminus_discrepancy' in d:
        clean=d[d.plusminus_discrepancy==0]
        table,_,_=fit_within(clean)
        results.append(table.assign(scope='pooled',specification='exclude_provider_plusminus_discrepancies'))
        lineups=pd.read_csv(OUT/'lineups.csv')
        lineups[lineups.plusminus_discrepancy!=0].to_csv(DOC/'provider_plusminus_discrepancies.csv',index=False)
    for label,frame in [('pooled',d)]+[(s,d[d.season==s]) for s in seasons]:
        for threshold in [25,50,100]:
            table,_,_=fit_within(frame,threshold)
            results.append(table.assign(scope=label,specification='primary'))
        uncertainty[label]=inference(frame)
    for cutoff in seasons[1:]:
        scored,clubs=score_contrasts(d[d.season<cutoff],d[d.season==cutoff],return_clubs=True)
        forward.extend([r|{'test_season':cutoff,'train_seasons':','.join(s for s in seasons if s<cutoff)}
            for r in scored])
        forward_clubs.extend([r|{'test_season':cutoff} for r in clubs])
    if forward_clubs:
        pd.DataFrame(forward_clubs).to_csv(DOC/'forward_club_scores.csv',index=False)
        (DOC/'predictive_uncertainty.json').write_text(json.dumps(predictive_uncertainty(forward_clubs),indent=2),encoding='utf-8')
    # Fixed list of exploratory alternatives; all are retained regardless of sign.
    for label,kwargs in [('equal_lineup',{'weighted':False}),
        ('equal_representation',{'weighted':False,'weight_mode':'representation'}),
        ('exposure_per_representation',{'weight_mode':'representation'}),
        ('skills_without_quality',{'quality_column':None}),
        ('quality_without_skills',{'skill_controls':False}),
        ('all_gaps',{'fit_column':'complementarity_all'}),
        ('uncapped',{'fit_column':'complementarity_uncapped'}),
        ('no_interior',{'fit_column':'complementarity_no_interior'})]:
        table,_,_=fit_within(d,**kwargs)
        results.append(table.assign(scope='pooled',specification=label))
    # Median alternative measures the change in actual median, not a /5 mean approximation.
    core=np.stack([d[[f'c{i}_{s}' for s in SKILLS]].to_numpy() for i in range(1,5)],axis=1)
    fifth=d[[f'fifth_{s}' for s in SKILLS]].to_numpy()
    median=np.median(core,axis=1);new=np.median(np.concatenate([core,fifth[:,None,:]],axis=1),axis=1)
    ties=np.isclose(median,median.min(axis=1)[:,None],atol=1e-12,rtol=0)
    d['median_closure']=(np.minimum(np.maximum(0,-median),np.maximum(0,new-median))*ties).sum(axis=1)/ties.sum(axis=1)
    table,_,_=fit_within(d,fit_column='median_closure')
    results.append(table.assign(scope='pooled',specification='median_core'))
    # A nonlinear production control tests the primary linear talent assumption.
    alternate=d.copy();alternate['fifth_quality_squared']=alternate.fifth_quality**2
    table,_,_=fit_within(alternate,quality_column=['fifth_quality','fifth_quality_squared'])
    results.append(table.assign(scope='pooled',specification='quadratic_quality'))
    errors=[]
    raw=pd.read_csv(OUT/'core_observations_unfiltered.csv')
    profiles=pd.read_csv(OUT/'player_profiles.csv')
    profiles['spacing']=profiles.groupby('season').three_volume_raw.transform(zscore)
    variant,_=attach_features(raw,profiles,write_output=False)
    table,_,_=fit_within(variant)
    results.append(table.assign(scope='pooled',specification='spacing_volume_only'))
    for minutes in [250,1000]:
        try:
            profiles=player_profiles(seasons,minutes,write_output=False)
            variant,_=attach_features(raw,profiles,write_output=False)
            table,_,_=fit_within(variant)
            results.append(table.assign(scope='pooled',specification=f'prior_minutes_{minutes}'))
        except ValueError as exc:
            errors.append({'specification':f'prior_minutes_{minutes}','error':str(exc)})
    extended=pd.concat(results,ignore_index=True)
    extended.to_csv(DOC/'extended_coefficients.csv',index=False)
    if '2022-23' in seasons:
        baseline=pd.read_csv(DOC/'pilot_baseline'/'model_coefficients.csv')
        baseline=baseline[(baseline.fit_column=='complementarity') & baseline.weighted & baseline.skill_controls]
        current=extended[(extended.scope=='2022-23') & (extended.specification=='primary')]
        comparison=current.merge(baseline,on=['threshold','term'],suffixes=('_new','_original'),validate='one_to_one')
        for field in ['coefficient','se','ci_low','ci_high']:
            comparison[field+'_difference']=comparison[field+'_new']-comparison[field+'_original']
        check=comparison[['threshold','term']+[c for c in comparison if c.endswith('_difference')]]
        check.to_csv(DOC/'pilot_reproduction.csv',index=False)
        if not np.allclose(check.filter(like='_difference'),0,atol=1e-9):
            raise ValueError('Pilot results changed; investigate pilot_reproduction.csv')
    pd.DataFrame(forward).to_csv(DOC/'season_forward_validation.csv',index=False)
    influence=[]
    sample=comparison_sample(d,50).drop_duplicates('lineup_key')
    ids=sample[[f'p{i}' for i in range(1,6)]].to_numpy().ravel()
    exposure=np.repeat(sample.possessions.to_numpy(),5)
    top=pd.Series(exposure,index=ids).groupby(level=0).sum().nlargest(10).index
    for pid in top:
        keep=~d[[f'p{i}' for i in range(1,6)]].eq(pid).any(axis=1)
        try:
            table,_,_=fit_within(d[keep]);r=table[table.term=='complementarity'].iloc[0].to_dict()
            influence.append(r|{'excluded_player_id':int(pid)})
        except ValueError as exc:
            influence.append({'excluded_player_id':int(pid),'error':str(exc)})
    pd.DataFrame(influence).to_csv(DOC/'player_influence.csv',index=False)
    (DOC/'inference_diagnostics.json').write_text(json.dumps(uncertainty,indent=2),encoding='utf-8')
    (DOC/'sensitivity_failures.json').write_text(json.dumps(errors,indent=2),encoding='utf-8')
    inventory=[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
        for p in sorted(RAW.glob('*.json'))]
    (DOC/'raw_inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    manifest={'generated_utc':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),
        'seasons':seasons,'primary_minutes':500,'primary_possessions_each_side':50,
        'bootstrap_seed':20261016,'bootstrap_draws':1999,'raw_inventory':'raw_inventory.json',
        'code':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'src').glob('*.py'))}}
    (DOC/'release_run_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'seasons':seasons,'inference':uncertainty,'sensitivity_failures':errors},indent=2))

if __name__=='__main__':run()
