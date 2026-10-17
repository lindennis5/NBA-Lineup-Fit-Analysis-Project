"""Fail-closed integrity checks for the intended full regular-season study."""
import numpy as np

FIELDS = ['SecondsPlayed', 'OffPoss', 'DefPoss', 'Points', 'OpponentPoints']

def validate_teams(teams):
    ids = [str(t['EntityId']) for t in teams]
    if len(ids) != 30 or len(set(ids)) != 30:
        raise ValueError('Expected 30 distinct franchises')
    # Applies to the four explicitly supported, full 82-game seasons only.
    if any(t['GamesPlayed'] != 82 for t in teams):
        raise ValueError('Incomplete regular season: expected 82 games per franchise')

def reconcile(rows, team):
    for field in FIELDS:
        values = np.asarray([r.get(field, 0) for r in rows], dtype=float)
        if not np.isfinite(values).all() or (values < 0).any():
            raise ValueError(f'Invalid {field} values')
        if not np.isclose(values.sum(), team[field], atol=1e-5, rtol=0):
            raise ValueError(f'Lineup/team {field} mismatch: {values.sum()} versus {team[field]}')
    # Provider PlusMinus is not used in our outcome. Preserve discrepancies for
    # diagnosis rather than assume it is interchangeable with scoring counters.
    return [r for r in rows if r.get('PlusMinus',0)!=r.get('Points',0)-r.get('OpponentPoints',0)]
