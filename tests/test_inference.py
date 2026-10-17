"""Synthetic estimator checks, never research data."""
import unittest
import numpy as np
import pandas as pd
from src.features import SKILLS
from src.models import fit_within
from src.release_audit import inference, score_contrasts,predictive_uncertainty

def fixture(season, seed):
    rng=np.random.default_rng(seed);rows=[]
    for team in range(12):
        for core in range(3):
            alpha=rng.normal()*5
            for fifth in range(4):
                skills=rng.normal(size=5);quality=rng.normal();fill=rng.random()
                rows.append({'season':season,'team_id':str(team),'core_key':f'{season}|{team}|{core}',
                    'lineup_key':f'{season}|{team}|{core}|{fifth}','fifth_id':fifth,
                    'min_side_poss':100,'possessions':rng.uniform(100,400),
                    'fifth_quality':quality,**{f'fifth_{s}':v for s,v in zip(SKILLS,skills)},
                    'complementarity':fill,'net_rating':alpha+quality+skills.sum()+3*fill+rng.normal()})
    return pd.DataFrame(rows)

class InferenceTests(unittest.TestCase):
    def test_paired_prediction_difference_known_errors(self):
        rows=[{'team_id':team,'model':model,'squared_error_sum':error,'weight_sum':1}
            for team in [1,2,3] for model,error in [('baseline',4),('complementarity',9)]]
        result=predictive_uncertainty(rows,draws=19)
        self.assertEqual(result['delta_rmse'],1)
        self.assertEqual(result['ci_low'],1)
        self.assertEqual(result['ci_high'],1)

    def test_bootstrap_studentization_matches_primary(self):
        d=fixture('2022-23',12)
        table,_,_=fit_within(d);r=table[table.term=='complementarity'].iloc[0]
        check=inference(d,seed=123,draws=19)
        self.assertAlmostEqual(check['observed_t'],r.coefficient/r.se,places=10)
        self.assertEqual(check,inference(d,seed=123,draws=19))
        self.assertTrue(0<check['wild_cluster_p']<=1)
        self.assertGreater(check['jackknife_se'],0)

    def test_forward_contrast_invariance_and_temporal_guard(self):
        train=fixture('2022-23',14);test=fixture('2023-24',15)
        original=score_contrasts(train,test)
        shifted=test.copy();shifted.net_rating+=pd.factorize(test.core_key)[0]*30
        after=score_contrasts(train,shifted)
        np.testing.assert_allclose([r['rmse'] for r in original],[r['rmse'] for r in after],atol=1e-10)
        with self.assertRaisesRegex(ValueError,'before'):
            score_contrasts(test,train)

if __name__=='__main__':unittest.main()
