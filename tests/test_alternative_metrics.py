import unittest
import numpy as np
import pandas as pd
from src.alternative_metrics import (deficiency_supply, redundancy, specialist_coverage,
                                     add_alternatives, ALTERNATIVES)
from src.features import SKILLS, complementarity

# 2024-25 Knicks core (Towns, Anunoby, Hart, Bridges) and fifth players from docs/knicks_example.csv
CORE = np.array([[0.2781791777335208, -0.1283898856611275, -0.196837701491681, 0.0886599204817795, -0.3414486672164887]])
BRUNSON = np.array([[1.218732647817689, 1.6106484187252026, 3.4556071618735924, -0.933673607028948, -0.9493748757908176]])
WRIGHT = np.array([[-0.3297815883167934, 0.9887636611411988, -0.4060281101733203, -0.7744993100929859, -0.3772808573871111]])

class AlternativeMetrics(unittest.TestCase):
    def test_original_gives_brunson_zero_but_a1_credits_him(self):
        self.assertEqual(complementarity(CORE, BRUNSON)[0][0], 0.0)
        self.assertAlmostEqual(deficiency_supply(CORE, BRUNSON)[0], 0.844, places=3)
        self.assertAlmostEqual(deficiency_supply(CORE, WRIGHT)[0], -0.123, places=3)

    def test_a1_zero_when_no_gap(self):
        self.assertEqual(deficiency_supply(np.array([[.1, .2, 0., .3, .4]]), BRUNSON)[0], 0.0)

    def test_a2_redundancy(self):
        self.assertAlmostEqual(redundancy(CORE, BRUNSON)[0], 0.339, places=3)
        self.assertEqual(redundancy(CORE, WRIGHT)[0], 0.0)
        self.assertGreaterEqual(redundancy(np.random.default_rng(0).normal(size=(50, 5)),
                                           np.random.default_rng(1).normal(size=(50, 5))).min(), 0.0)

    def test_a3_uses_best_core_player_not_mean(self):
        players = np.array([[[0, 0, 0, 0, 0], [0, 0, 0, 0, 2.], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]])
        fifth = np.array([[1., 0, 0, 0, 1.5]])
        self.assertAlmostEqual(specialist_coverage(players, fifth)[0], 1.0)   # interior: 1.5 < best 2.0
        self.assertGreaterEqual(specialist_coverage(players, fifth).min(), 0.0)

    def test_add_alternatives_preserves_original_columns(self):
        d = pd.DataFrame({f'core_{s}': CORE[0, i:i + 1] for i, s in enumerate(SKILLS)})
        for i, s in enumerate(SKILLS):
            d[f'fifth_{s}'] = BRUNSON[0, i]
            for j in range(1, 5):
                d[f'c{j}_{s}'] = CORE[0, i]
        d['complementarity'] = 0.0
        out = add_alternatives(d)
        self.assertTrue(set(ALTERNATIVES) <= set(out))
        self.assertEqual(list(d.complementarity), list(out.complementarity))
        self.assertNotIn('alt_deficiency_supply', d)

if __name__ == '__main__':
    unittest.main()
