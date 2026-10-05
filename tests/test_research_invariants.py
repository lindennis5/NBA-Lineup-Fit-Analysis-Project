"""Synthetic fixtures verify mathematics only; they are never research observations."""
import unittest
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_cluster
from src.lineups import player_tuple,canonical_id,expand_cores,comparison_sample
from src.features import complementarity,SKILLS
from src.models import fit_within
from src.data_pipeline import validate_seasons

class ResearchInvariants(unittest.TestCase):
    def test_season_contract(self):
        validate_seasons(['2022-23','2023-24'])
        for seasons in [[],['2022-24'],['2022'],['2023-24','2022-23'],['2022-23','2024-25']]:
            with self.assertRaises(ValueError):validate_seasons(seasons)
    def test_core_expansion_and_order(self):
        self.assertEqual(player_tuple('5-3-1-4-2'),(1,2,3,4,5))
        self.assertEqual(canonical_id([3,1,2,4]),'1-2-3-4')
        for value in ['1-2-3-4-4','1-2-3-4','0-1-2-3-4']:
            with self.assertRaises(ValueError): player_tuple(value)
        row={'season':'2024-25','team_id':'10',**{f'p{i}':i for i in range(1,6)}}
        result=expand_cores(pd.DataFrame([row]))
        self.assertEqual(len(result),5)
        for record in result.to_dict('records'):
            core=set(map(int,record['core_id'].split('-')))
            self.assertNotIn(record['fifth_id'],core)
            self.assertEqual(core|{record['fifth_id']},set(range(1,6)))

    def test_gap_closure(self):
        core=np.array([[-1,0,0,0,0],[1,2,3,4,5],[-1,-1,0,0,0],[-1,0,0,0,0]])
        fifth=np.array([[1,0,0,0,0],[9,9,9,9,9],[1,-1,0,0,0],[-2,9,9,9,9]])
        main,_,_=complementarity(core,fifth)
        np.testing.assert_allclose(main,[.4,0,.2,0])
        main,_,_=complementarity(np.array([[-.1,0,0,0,0]]),np.array([[10,0,0,0,0]]))
        self.assertAlmostEqual(main[0],.1)

    def test_within_estimator_matches_explicit_fixed_effects(self):
        rng=np.random.default_rng(123)
        rows=[]
        for club in range(12):
            for core in range(4):
                alpha=rng.normal()*5
                for fifth in range(4):
                    skills=rng.normal(size=5);quality=rng.normal();fit=rng.random()
                    rows.append({'team_id':str(club),'core_key':f'{club}-{core}','fifth_id':fifth,
                        'lineup_key':f'{club}-{core}-{fifth}','min_side_poss':100,
                        'possessions':rng.uniform(100,400),'fifth_quality':quality,
                        **{f'fifth_{s}':v for s,v in zip(SKILLS,skills)},'complementarity':fit,
                        'net_rating':alpha+2*quality+3*fit+skills.sum()+rng.normal()})
        d=pd.DataFrame(rows)
        coefficients,within,sample=fit_within(d)
        columns=list(within.params.index)
        dummy=pd.get_dummies(d.core_key,dtype=float)
        explicit=sm.WLS(d.net_rating,pd.concat([d[columns],dummy],axis=1),weights=d.possessions).fit()
        np.testing.assert_allclose(within.params,explicit.params[columns],atol=1e-9)
        explicit_se=np.sqrt(np.diag(cov_cluster(explicit,pd.factorize(d.team_id)[0])))[:len(columns)]
        np.testing.assert_allclose(coefficients.se,explicit_se,atol=1e-9)
        shifted=d.copy();shifted.net_rating+=pd.factorize(d.core_key)[0]*20
        _,shifted_fit,_=fit_within(shifted)
        np.testing.assert_allclose(within.params,shifted_fit.params,atol=1e-9)

    def test_threshold_both_sides_and_alternatives(self):
        d=pd.DataFrame({'core_key':['a','a','b'],'fifth_id':[1,2,3],
                        'min_side_poss':[100,49,100],'net_rating':[1,2,3]})
        self.assertEqual(len(comparison_sample(d,50)),0)
        self.assertEqual(len(comparison_sample(d,25)),2)

if __name__=='__main__': unittest.main()
