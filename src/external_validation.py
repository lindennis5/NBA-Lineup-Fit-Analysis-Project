"""Independent season validation against Basketball-Reference team totals.

Points, opponent points and games must match the provider exactly. Possessions use the
box-score estimate FGA + 0.44*FTA - ORB + TOV for the team (offense) and its opponents
(defense). The pass tolerance is the largest relative provider-vs-estimate gap seen in the
two seasons whose league counters balance; it is data-calibrated, not chosen.
"""
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
import pandas as pd
from .data_pipeline import ROOT, RAW
from .lineups import load_rows, SEASONS

EXTERNAL = ROOT / 'data' / 'external'
AUDIT = ROOT / 'docs' / 'audit'
ALIASES = {'BRK': 'BKN', 'PHO': 'PHX', 'CHO': 'CHA'}
TEAM_FIELDS = {'g': 'games', 'pts': 'points', 'fga': 'fga', 'fta': 'fta', 'orb': 'orb', 'tov': 'tov'}
OPP_FIELDS = {'opp_pts': 'opp_points', 'opp_fga': 'opp_fga', 'opp_fta': 'opp_fta',
              'opp_orb': 'opp_orb', 'opp_tov': 'opp_tov'}
UA = 'Mozilla/5.0 (nba-lineup-fit research; contact dennislin2900@gmail.com)'

def norm(abbreviation):
    return ALIASES.get(abbreviation, abbreviation)

class TableParser(HTMLParser):
    """Collect data-stat cells of the table with the requested id."""
    def __init__(self, table_id):
        super().__init__()
        self.table_id, self.depth, self.rows = table_id, 0, []
        self.row, self.stat, self.text = None, None, ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'table' and a.get('id') == self.table_id:
            self.depth = 1
        elif self.depth and tag == 'table':
            self.depth += 1
        elif self.depth and tag == 'tr':
            self.row = {}
        elif self.depth and self.row is not None and tag in ('td', 'th') and a.get('data-stat'):
            self.stat, self.text = a['data-stat'], ''
        elif self.depth and self.stat == 'team' and tag == 'a':
            match = re.search(r'/teams/([A-Z]{3})/', a.get('href', ''))
            if match:
                self.row['abbr'] = match.group(1)

    def handle_data(self, data):
        if self.stat:
            self.text += data

    def handle_endtag(self, tag):
        if self.depth and tag in ('td', 'th') and self.stat:
            self.row[self.stat] = self.text.strip()
            self.stat = None
        elif self.depth and tag == 'tr' and self.row is not None:
            if self.row.get('abbr'):
                self.rows.append(self.row)
            self.row = None
        elif self.depth and tag == 'table':
            self.depth -= 1

def parse_totals(html):
    """Return one row per team with team and opponent totals from a season page."""
    tables = {}
    for table_id in ('totals-team', 'totals-opponent'):
        parser = TableParser(table_id)
        parser.feed(html)
        tables[table_id] = {norm(r['abbr']): r for r in parser.rows}
    if len(tables['totals-team']) != 30 or len(tables['totals-opponent']) != 30:
        raise ValueError('Expected 30 teams in both totals tables')
    records = []
    for abbr, row in tables['totals-team'].items():
        opp = tables['totals-opponent'][abbr]
        record = {'team': abbr}
        record.update({name: float(row[key]) for key, name in TEAM_FIELDS.items()})
        record.update({name: float(opp[key]) for key, name in OPP_FIELDS.items()})
        records.append(record)
    return pd.DataFrame(records)

def fetch(season):
    end_year = int(season[:4]) + 1
    path = EXTERNAL / f'bbref_{season}_team_totals.csv'
    if path.exists():
        return pd.read_csv(path)
    url = f'https://www.basketball-reference.com/leagues/NBA_{end_year}.html'
    request = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(request, timeout=60) as response:
        html = response.read().decode('utf-8')
    table = parse_totals(html)
    table['source_url'] = url
    table['retrieved_utc'] = datetime.now(timezone.utc).isoformat()
    EXTERNAL.mkdir(parents=True, exist_ok=True)
    table.to_csv(path, index=False)
    time.sleep(5)
    return table

def compare(season, provider, external):
    """Team-level comparison of provider totals with the independent table."""
    p = provider.assign(team=provider.TeamAbbreviation.map(norm)).set_index('team')
    e = external.set_index('team')
    if set(p.index) != set(e.index):
        raise ValueError(f'{season}: team crosswalk mismatch {set(p.index) ^ set(e.index)}')
    out = pd.DataFrame(index=sorted(p.index))
    out['season'] = season
    out['games_diff'] = p.GamesPlayed - e.games
    out['points_diff'] = p.Points - e.points
    out['opp_points_diff'] = p.OpponentPoints - e.opp_points
    est_off = e.fga + .44 * e.fta - e.orb + e.tov
    est_def = e.opp_fga + .44 * e.opp_fta - e.opp_orb + e.opp_tov
    out['off_poss_provider'], out['off_poss_estimate'] = p.OffPoss, est_off
    out['def_poss_provider'], out['def_poss_estimate'] = p.DefPoss, est_def
    out['off_rel_gap'] = (p.OffPoss - est_off) / est_off
    out['def_rel_gap'] = (p.DefPoss - est_def) / est_def
    return out.reset_index(names='team')

def provider_totals(season):
    """Provider team totals from the raw cache, or (if absent) the committed coverage audit copy."""
    path = RAW / f'pbp_{season}_Team.json'
    if path.exists():
        return pd.DataFrame(load_rows(path)), 'raw cache'
    cov = pd.read_csv(ROOT / 'docs' / 'coverage_audit.csv')
    cov = cov[cov.season == season].rename(columns={'team': 'TeamAbbreviation', 'team_games': 'GamesPlayed',
        'Points_team': 'Points', 'OpponentPoints_team': 'OpponentPoints', 'OffPoss_team': 'OffPoss', 'DefPoss_team': 'DefPoss'})
    return cov, 'docs/coverage_audit.csv (team totals reconciled to the provider at build time)'

def main(seasons=SEASONS):
    AUDIT.mkdir(parents=True, exist_ok=True)
    frames = []
    for season in seasons:
        provider, origin = provider_totals(season)
        print(f'{season}: provider totals from {origin}')
        frames.append(compare(season, provider, fetch(season)))
    check = pd.concat(frames, ignore_index=True)
    status = pd.read_csv(ROOT / 'docs' / 'season_validation_status.csv')
    reference = status.loc[status.balanced_counters, 'season'].tolist()
    base = check[check.season.isin(reference)]
    tolerance = float(max(base.off_rel_gap.abs().max(), base.def_rel_gap.abs().max()))
    check['off_pass'] = check.off_rel_gap.abs() <= tolerance
    check['def_pass'] = check.def_rel_gap.abs() <= tolerance
    check['exact_pass'] = (check.games_diff == 0) & (check.points_diff == 0) & (check.opp_points_diff == 0)
    check.to_csv(AUDIT / 'external_team_check.csv', index=False)
    summary = check.groupby('season').agg(
        teams=('team', 'size'), exact_pass=('exact_pass', 'sum'), off_pass=('off_pass', 'sum'),
        def_pass=('def_pass', 'sum'), mean_off_gap=('off_rel_gap', 'mean'), mean_def_gap=('def_rel_gap', 'mean'),
        max_abs_gap=('off_rel_gap', lambda s: s.abs().max()))
    summary['max_abs_gap'] = check.assign(m=check[['off_rel_gap', 'def_rel_gap']].abs().max(axis=1)).groupby('season').m.max()
    summary['disposition'] = [
        'validated' if r.teams == 30 and r.exact_pass == 30 and r.off_pass == 30 and r.def_pass == 30 else 'provisional'
        for r in summary.itertuples()]
    status = status.drop(columns=[c for c in ('disposition',) if c in status]).merge(
        summary[['disposition']].reset_index(), on='season', how='left')
    status.to_csv(ROOT / 'docs' / 'season_validation_status.csv', index=False)
    print(f'calibrated tolerance (balanced seasons {reference}): {tolerance:.5f}')
    print(summary.to_string())
    return check, summary, tolerance

if __name__ == '__main__':
    main(sys.argv[1:] or SEASONS)
