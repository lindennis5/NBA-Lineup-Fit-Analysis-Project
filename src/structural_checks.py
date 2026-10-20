"""Structural validation of player IDs, lineup composition, possessions and season coverage.

Run after run.py so data/processed/lineups.csv and player_profiles.csv exist.
"""
import json
import re
import time
import unicodedata
import urllib.request
from html.parser import HTMLParser
import pandas as pd
from .data_pipeline import ROOT, RAW, OUT
from .lineups import load_rows, SEASONS

AUDIT = ROOT / 'docs' / 'audit'
EXTERNAL = ROOT / 'data' / 'external'
MINUTES_RANGE = (3936, 4200)   # 82 games x 48 minutes, ceiling allows overtime
PACE_RANGE = (85, 110)         # team possessions per game
MAX_TEAMS_PER_PLAYER = 3
POINTS_RATIO_FLOOR = .995
BRUNSON_ID = 1628973
UA = 'Mozilla/5.0 (nba-lineup-fit research; contact dennislin2900@gmail.com)'

def unresolved_exposure(lineups, player_ids):
    """Share of lineup possessions and lineups containing an ID absent from the player file."""
    ids = lineups[[f'p{i}' for i in range(1, 6)]]
    missing = ~ids.isin(player_ids).all(axis=1)
    return {'lineups': int(missing.sum()), 'lineup_share': float(missing.mean()),
            'possession_share': float(lineups.possessions[missing].sum() / lineups.possessions.sum())}

def players_on_many_teams(lineups, maximum=MAX_TEAMS_PER_PLAYER):
    long = pd.concat([lineups[['team_id', f'p{i}']].rename(columns={f'p{i}': 'player'}) for i in range(1, 6)])
    teams = long.groupby('player').team_id.nunique()
    return sorted(int(p) for p in teams[teams > maximum].index)

def range_violations(values, low, high):
    return [str(i) for i, v in values.items() if not low <= v <= high]

def points_ratio(players, teams):
    return float(players.Points.sum() / teams.Points.sum())

def profile_exposure_share(lineups, profile_ids):
    complete = lineups[[f'p{i}' for i in range(1, 6)]].isin(profile_ids).all(axis=1)
    return {'lineups_complete': int(complete.sum()), 'lineup_share': float(complete.mean()),
            'possession_share': float(lineups.possessions[complete].sum() / lineups.possessions.sum())}

def season_checks(season, lineups, profiles):
    teams = pd.DataFrame(load_rows(RAW / f'pbp_{season}_Team.json'))
    players = pd.DataFrame(load_rows(RAW / f'pbp_{season}_Player.json'))
    lin = lineups[lineups.season == season]
    coverage = pd.read_csv(ROOT / 'docs' / 'coverage_audit.csv')
    cov = coverage[coverage.season == season].set_index('team')
    minutes = cov.SecondsPlayed_team / 60
    pace = cov.OffPoss_team / cov.team_games
    ratio = points_ratio(players, teams)
    prof_ids = set(profiles.loc[profiles.season == season, 'player_id'])
    result = {
        'teams': int(len(teams)), 'games_each_82': bool((teams.GamesPlayed == 82).all()),
        'distinct_lineups': int(len(lin)),
        'unresolved_ids': unresolved_exposure(lin, set(players.EntityId.astype(int))),
        'players_on_more_than_3_teams': players_on_many_teams(lin),
        'team_minutes_out_of_range': range_violations(minutes, *MINUTES_RANGE),
        'team_pace_out_of_range': range_violations(pace, *PACE_RANGE),
        'team_minutes_min_max': [float(minutes.min()), float(minutes.max())],
        'pace_min_max': [float(pace.min()), float(pace.max())],
        'player_to_team_points_ratio': ratio, 'points_ratio_ok': bool(ratio >= POINTS_RATIO_FLOOR),
        'profile_coverage': profile_exposure_share(lin, prof_ids)}
    result['pass'] = bool(result['games_each_82'] and not result['team_minutes_out_of_range']
        and not result['team_pace_out_of_range'] and not result['players_on_more_than_3_teams']
        and result['points_ratio_ok'])
    return result

# ---- Basketball-Reference player-total spot check ----------------------------------

def plain(name):
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    name = re.sub(r'[.\']', '', name)
    return re.sub(r'\s+(jr|sr|ii|iii|iv)$', '', name).strip()

class PlayerTable(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table, self.row, self.stat, self.text, self.rows = False, None, None, '', []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'table' and a.get('id') == 'totals_stats':
            self.in_table = True
        elif self.in_table and tag == 'tr':
            self.row = {}
        elif self.in_table and self.row is not None and tag in ('td', 'th') and a.get('data-stat'):
            self.stat, self.text = a['data-stat'], ''

    def handle_data(self, data):
        if self.stat:
            self.text += data

    def handle_endtag(self, tag):
        if self.in_table and tag in ('td', 'th') and self.stat:
            self.row[self.stat] = self.text.strip()
            self.stat = None
        elif self.in_table and tag == 'tr' and self.row is not None:
            if self.row.get('name_display'):
                self.rows.append(self.row)
            self.row = None
        elif tag == 'table':
            self.in_table = False

def bbref_players(season):
    """First row per player name (the combined row for traded players)."""
    path = EXTERNAL / f'bbref_{season}_player_totals.csv'
    if path.exists():
        return pd.read_csv(path)
    url = f'https://www.basketball-reference.com/leagues/NBA_{int(season[:4]) + 1}_totals.html'
    request = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(request, timeout=90) as response:
        parser = PlayerTable()
        parser.feed(response.read().decode('utf-8'))
    table = pd.DataFrame(parser.rows)
    table['key'] = table.name_display.map(plain)
    table = table.drop_duplicates('key')[['name_display', 'key', 'games', 'mp', 'pts', 'ast', 'blk']]
    EXTERNAL.mkdir(parents=True, exist_ok=True)
    table.to_csv(path, index=False)
    time.sleep(6)
    return table

def spot_check(player_ids, seasons):
    rows = []
    for season in seasons:
        provider = pd.DataFrame(load_rows(RAW / f'pbp_{season}_Player.json'))
        external = bbref_players(season).set_index('key')
        for pid in player_ids:
            hit = provider[provider.EntityId.astype(int) == pid]
            if hit.empty:
                continue
            h = hit.iloc[0]
            key = plain(h.Name)
            if key not in external.index:
                rows.append({'season': season, 'player_id': pid, 'name': h.Name, 'matched': False})
                continue
            e = external.loc[key]
            rows.append({'season': season, 'player_id': pid, 'name': h.Name, 'matched': True,
                'points_diff': h.Points - e.pts, 'assists_diff': h.Assists - e.ast,
                'blocks_diff': h.get('Blocks', 0) - e.blk,
                'minutes_provider': h.SecondsPlayed / 60, 'minutes_bbref': e.mp,
                'minutes_rel_diff': (h.SecondsPlayed / 60 - e.mp) / e.mp})
    return pd.DataFrame(rows)

def main(seasons=SEASONS):
    AUDIT.mkdir(parents=True, exist_ok=True)
    lineups = pd.read_csv(OUT / 'lineups.csv', dtype={'team_id': str})
    profiles = pd.read_csv(OUT / 'player_profiles.csv')
    report = {season: season_checks(season, lineups, profiles) for season in seasons}
    influence = pd.read_csv(ROOT / 'docs' / 'player_influence.csv')
    ids = [int(i) for i in influence.excluded_player_id.dropna().unique()]
    if BRUNSON_ID not in ids:
        ids.append(BRUNSON_ID)
    spot = spot_check(ids, ['2021-22'] + list(seasons))
    spot.to_csv(AUDIT / 'player_spotcheck.csv', index=False)
    matched = spot[spot.matched.astype(bool)]
    report['spot_check'] = {'players': len(ids), 'rows': len(spot), 'unmatched_rows': int((~spot.matched.astype(bool)).sum()),
        'rows_with_exact_points_assists_blocks': int(((matched.points_diff == 0) & (matched.assists_diff == 0)
            & (matched.blocks_diff == 0)).sum()), 'matched_rows': len(matched),
        'max_abs_minutes_rel_diff': float(matched.minutes_rel_diff.abs().max()) if len(matched) else None}
    (AUDIT / 'structural_checks.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({s: {k: v for k, v in r.items() if k in ('pass', 'player_to_team_points_ratio')}
        for s, r in report.items() if s != 'spot_check'} | {'spot_check': report['spot_check']}, indent=2))

if __name__ == '__main__':
    main()
