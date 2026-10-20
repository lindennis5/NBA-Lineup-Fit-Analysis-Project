import unittest
import pandas as pd
from src.structural_checks import (unresolved_exposure, players_on_many_teams, range_violations,
                                   points_ratio, profile_exposure_share, plain)

def lineups():
    return pd.DataFrame({'team_id': ['a', 'a', 'b'], 'possessions': [10., 30., 60.],
        'p1': [1, 1, 1], 'p2': [2, 2, 2], 'p3': [3, 3, 3], 'p4': [4, 4, 4], 'p5': [5, 6, 7]})

class StructuralChecks(unittest.TestCase):
    def test_unresolved_exposure(self):
        r = unresolved_exposure(lineups(), {1, 2, 3, 4, 5, 6})
        self.assertEqual(r['lineups'], 1)
        self.assertAlmostEqual(r['possession_share'], .6)

    def test_players_on_many_teams(self):
        d = pd.concat([lineups().assign(team_id=t) for t in 'abcd'])
        self.assertEqual(players_on_many_teams(d, 3), [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(players_on_many_teams(lineups(), 3), [])

    def test_range_violations_and_ratio(self):
        self.assertEqual(range_violations(pd.Series({'x': 1., 'y': 5.}), 2, 6), ['x'])
        self.assertAlmostEqual(points_ratio(pd.DataFrame({'Points': [99.]}), pd.DataFrame({'Points': [100.]})), .99)

    def test_profile_share_and_names(self):
        self.assertAlmostEqual(profile_exposure_share(lineups(), {1, 2, 3, 4, 5})['possession_share'], .1)
        self.assertEqual(plain('Jimmy Butler III'), plain('Jimmy Butler'))
        self.assertEqual(plain('Nikola Jokić'), 'nikola jokic')

if __name__ == '__main__':
    unittest.main()
