import unittest
import numpy as np
import pandas as pd
from src.effect_scale import within_core_sd, scaled_effect, holm, EQUIVALENCE_MARGIN

class FinalRobustness(unittest.TestCase):
    def test_within_core_sd_ignores_core_level(self):
        d = pd.DataFrame({'core_key': ['a', 'a', 'b', 'b'], 'lineup_key': ['1', '2', '3', '4'],
                          'possessions': [1., 1., 1., 1.], 'x': [0., 2., 100., 102.]})
        self.assertAlmostEqual(within_core_sd(d, 'x'), 1.0)

    def test_scaled_effect_and_equivalence(self):
        tight = scaled_effect(0.1, 0.05, 30, 2.0)
        self.assertAlmostEqual(tight['effect_per_sd'], 0.2)
        self.assertTrue(tight['equivalent_within_margin'])
        wide = scaled_effect(0.1, 5.0, 30, 2.0)
        self.assertFalse(wide['equivalent_within_margin'])
        self.assertGreater(wide['min_detectable_effect_per_sd'], EQUIVALENCE_MARGIN)

    def test_holm_matches_hand_calculation(self):
        adjusted = holm([0.01, 0.04, 0.03])
        np.testing.assert_allclose(adjusted, [0.03, 0.06, 0.06])
        self.assertTrue((holm([0.5]) == 0.5).all())

if __name__ == '__main__':
    unittest.main()
