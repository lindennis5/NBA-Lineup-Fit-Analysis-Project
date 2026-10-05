"""Interpretable within-core WLS with club-clustered inference and specification checks."""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import t
from statsmodels.stats.sandwich_covariance import cov_cluster
from .features import SKILLS
from .lineups import comparison_sample
from .data_pipeline import OUT

def fit_within(observations, threshold=50, fit_column='complementarity', weighted=True, skill_controls=True):
    d=comparison_sample(observations,threshold).reset_index(drop=True)
    columns=['fifth_quality']+([f'fifth_{s}' for s in SKILLS] if skill_controls else [])
    if fit_column:
        columns.append(fit_column)
    # Each lineup contributes its original exposure once across retained representations.
    multiplicity=d.groupby('lineup_key').lineup_key.transform('size')
    w=(d.possessions if weighted else pd.Series(1.,index=d.index))/multiplicity
    numeric=d[['net_rating']+columns]
    means=numeric.mul(w,axis=0).groupby(d.core_key).transform('sum').div(w.groupby(d.core_key).transform('sum'),axis=0)
    within=numeric-means
    x=within[columns];y=within.net_rating
    if np.linalg.matrix_rank(x.to_numpy())!=len(columns):
        raise ValueError('Within-core model rank deficiency')
    result=sm.WLS(y,x,weights=w).fit()
    codes=pd.factorize(d.team_id)[0]
    clusters=len(np.unique(codes));groups=d.core_key.nunique();n=len(d);p=len(columns)
    if clusters<10 or n<=groups+p:
        raise ValueError('Insufficient independent clusters/degrees of freedom')
    covariance=cov_cluster(result,codes,use_correction=False)
    # Account for absorbed core intercepts in the CR1 finite-sample correction.
    covariance*=clusters/(clusters-1)*(n-1)/(n-groups-p)
    se=np.sqrt(np.diag(covariance));crit=t.ppf(.975,clusters-1)
    sse=np.sum(w*result.resid**2);sst=np.sum(w*y**2)
    rows=[]
    for j,col in enumerate(columns):
        beta=float(result.params.iloc[j])
        rows.append({'threshold':threshold,'fit_column':fit_column or 'none','weighted':weighted,
            'skill_controls':skill_controls,'term':col,'coefficient':beta,'se':se[j],
            'ci_low':beta-crit*se[j],'ci_high':beta+crit*se[j],
            'p_value':2*t.sf(abs(beta/se[j]),clusters-1),'rows':n,'cores':groups,
            'lineups':d.lineup_key.nunique(),'clubs':clusters,'within_r2':1-sse/sst,
            'within_rmse':np.sqrt(sse/w.sum()),'df_residual':n-groups-p,
            'condition_number':float(np.linalg.cond(x.to_numpy()*np.sqrt(w.to_numpy())[:,None]))})
    return pd.DataFrame(rows),result,d

def run_models(observations):
    outputs=[]
    specs=[(threshold,fit,True,True) for threshold in [25,50,100]
           for fit in [None,'complementarity','complementarity_all','complementarity_uncapped']]
    specs += [(50,'complementarity',False,True),(50,'complementarity',True,False)]
    specs += [(50,'complementarity_no_interior',True,True)]
    for threshold,fit,weighted,skills in specs:
        table,_,_=fit_within(observations,threshold,fit,weighted,skills)
        outputs.append(table)
    results=pd.concat(outputs,ignore_index=True)
    results.to_csv(OUT/'model_coefficients.csv',index=False)
    return results

def leave_club_out(observations,threshold=50):
    """Validate generalization of within-core contrasts, not deployable lineup-level predictions.

    Entire franchises are held out across seasons. Test-core outcome demeaning is used
    only to score contrasts; its fixed effect is not estimated or claimed predictable.
    """
    all_d=comparison_sample(observations,threshold).reset_index(drop=True)
    records=[]
    for club in sorted(all_d.team_id.unique()):
        train=all_d[all_d.team_id!=club]
        test=all_d[all_d.team_id==club].copy()
        w=test.possessions/test.groupby('lineup_key').lineup_key.transform('size')
        for fit in [None,'complementarity']:
            _,fitted,_=fit_within(train,threshold,fit)
            cols=list(fitted.params.index)
            numeric=test[['net_rating']+cols]
            means=numeric.mul(w,axis=0).groupby(test.core_key).transform('sum').div(w.groupby(test.core_key).transform('sum'),axis=0)
            within=numeric-means
            residual=within.net_rating-within[cols].to_numpy()@fitted.params.to_numpy()
            records.append({'held_out_club':club,'model':'talent_and_skills' if fit is None else 'plus_complementarity',
                'squared_error_sum':float(np.sum(w*residual**2)),'weight_sum':float(w.sum()),
                'rmse':float(np.sqrt(np.sum(w*residual**2)/w.sum())),'test_rows':len(test)})
    result=pd.DataFrame(records)
    result.to_csv(OUT/'heldout_club_validation.csv',index=False)
    return result
