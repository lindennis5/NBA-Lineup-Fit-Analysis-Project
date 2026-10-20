import unittest
import pandas as pd
from src.external_validation import parse_totals, compare, norm

def table(table_id, prefix, scale):
    rows = ''.join(
        f'<tr><td data-stat="team"><a href="/teams/{abbr}/2025.html">{abbr} Name</a></td>'
        f'<td data-stat="{prefix}g">82</td><td data-stat="{prefix}pts">{scale * 100 + i}</td>'
        f'<td data-stat="{prefix}fga">{scale * 90}</td><td data-stat="{prefix}fta">{scale * 20}</td>'
        f'<td data-stat="{prefix}orb">{scale * 10}</td><td data-stat="{prefix}tov">{scale * 12}</td></tr>'
        for i, abbr in enumerate(TEAMS))
    return f'<table id="{table_id}"><tbody>{rows}</tbody></table>'

TEAMS = ['T' + chr(65 + i // 5) + chr(65 + i % 5) for i in range(29)] + ['CHO']

class ExternalValidation(unittest.TestCase):
    def html(self):
        return table('totals-team', '', 1) + table('totals-opponent', 'opp_', 1)

    def test_parse_and_alias(self):
        t = parse_totals(self.html())
        self.assertEqual(len(t), 30)
        self.assertIn('CHA', set(t.team))
        self.assertEqual(norm('PHO'), 'PHX')
        self.assertEqual(t.set_index('team').loc['TAD', 'points'], 103)

    def test_parse_requires_thirty_teams(self):
        with self.assertRaises(ValueError):
            parse_totals(table('totals-team', '', 1).replace('TAA', 'TAB') + '<table id="totals-opponent"></table>')

    def test_compare_flags_point_gap_and_possession_gap(self):
        ext = parse_totals(self.html())
        provider = pd.DataFrame({'TeamAbbreviation': ['CHO' if t == 'CHA' else t for t in ext.team],
            'GamesPlayed': 82, 'Points': ext.points.to_numpy(), 'OpponentPoints': ext.opp_points.to_numpy(),
            'OffPoss': 8000., 'DefPoss': 8000.})
        provider.loc[0, 'Points'] -= 5
        out = compare('2024-25', provider, ext).set_index('team')
        self.assertEqual(out.loc['TAA', 'points_diff'], -5)
        self.assertEqual(out.points_diff.ne(0).sum(), 1)
        estimate = 90 + .44 * 20 - 10 + 12
        self.assertAlmostEqual(out.loc['TAB', 'off_poss_estimate'], estimate)
        self.assertAlmostEqual(out.loc['TAB', 'off_rel_gap'], (8000 - estimate) / estimate)

if __name__ == '__main__':
    unittest.main()
