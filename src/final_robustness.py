"""Final-audit robustness: scaled effects, equivalence, power, subgroup, exclusions, selection.

Reads the regenerated featured observations. Writes docs/audit/final_robustness.csv and
docs/audit/selection_table.csv. Every specification is reported, including failures.
"""
import numpy as np
import pandas as pd
from .data_pipeline import ROOT, OUT
from .lineups import comparison_sample
from .models import fit_within
from .effect_scale import within_core_sd, scaled_effect
from .features import SKILLS

AUDIT = ROOT / 'docs' / 'audit'

def fit_rows(label, scope, frame, column='complementarity', note=''):
    """Fit the primary model on a frame; return scaled rows for the fit term and the talent term."""
    try:
        table, _, sample = fit_within(frame, fit_column=column)
    except ValueError as exc:
        return [{'specification': label, 'scope': scope, 'term': column, 'error': str(exc), 'note': note}]
    rows = []
    for term in (column, 'fifth_quality'):
        r = table[table.term == term].iloc[0]
        rows.append({'specification': label, 'scope': scope, 'term': term,
            'coefficient_per_unit': r.coefficient, 'se': r.se, 'ci_low': r.ci_low, 'ci_high': r.ci_high,
            'p_value': r.p_value, 'lineups': int(r.lineups), 'cores': int(r.cores), 'clubs': int(r.clubs),
            'note': note} | scaled_effect(r.coefficient, r.se, int(r.clubs), within_core_sd(sample, term)))
    return rows

def validated_seasons():
    status = pd.read_csv(ROOT / 'docs' / 'season_validation_status.csv')
    column = 'disposition' if 'disposition' in status else None
    if column:
        return status.loc[status.disposition == 'validated', 'season'].tolist()
    return status.loc[status.balanced_counters, 'season'].tolist()

def selection_table(all_lineups, observations):
    primary = comparison_sample(observations, 50)
    eligible = observations.drop_duplicates('lineup_key')
    groups = {'all_lineups': all_lineups, 'with_all_prior_profiles': eligible,
              'primary_comparison_sample': primary.drop_duplicates('lineup_key')}
    rows = []
    for name, g in groups.items():
        rows.append({'group': name, 'lineups': len(g), 'franchise_seasons': g[['season', 'team_id']].drop_duplicates().shape[0],
            'total_mean_side_possessions': g.possessions.sum(), 'median_possessions': g.possessions.median(),
            'mean_net_rating_weighted': np.average(g.net_rating.replace([np.inf, -np.inf], np.nan).fillna(0), weights=g.possessions)})
    table = pd.DataFrame(rows)
    skills = pd.DataFrame({'group': ['with_all_prior_profiles', 'primary_comparison_sample'],
        **{f'mean_fifth_{s}': [observations[f'fifth_{s}'].mean(), primary[f'fifth_{s}'].mean()] for s in SKILLS + ['quality']}})
    return table.merge(skills, on='group', how='left')

def main():
    AUDIT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(OUT / 'observations.csv')
    seasons = sorted(d.season.unique())
    good = validated_seasons()
    rows = []
    rows += fit_rows('primary', 'validated_seasons', d[d.season.isin(good)], note=f'seasons {good}')
    rows += fit_rows('primary', 'pooled', d, note='includes provisional seasons')
    for s in seasons:
        rows += fit_rows('primary', s, d[d.season == s], note='validated' if s in good else 'provisional')
    for s in seasons:
        rows += fit_rows('leave_one_season_out', f'pooled_without_{s}', d[d.season != s])
    # Large-gap subgroup: cores whose largest deficiency is in the top quartile of primary-sample cores.
    cores = comparison_sample(d, 50).drop_duplicates('core_key')
    cut = float(cores.deficiency_gap.quantile(.75))
    rows += fit_rows('large_gap_subgroup', 'pooled', d[d.deficiency_gap >= cut], note=f'gap >= {cut:.4f}')
    rows += fit_rows('large_gap_subgroup', 'validated_seasons', d[(d.deficiency_gap >= cut) & d.season.isin(good)],
                     note=f'gap >= {cut:.4f}')
    # Exclude the 10 teams per flagged season with the largest offensive/defensive possession gap.
    coverage = pd.read_csv(ROOT / 'docs' / 'coverage_audit.csv')
    coverage['gap'] = (coverage.OffPoss_team - coverage.DefPoss_team).abs()
    drop = set()
    for s in [s for s in seasons if s not in good]:
        top = coverage[coverage.season == s].nlargest(10, 'gap')
        drop |= set(zip(top.season, top.team_id.astype(int)))
    keep = ~pd.Series(list(zip(d.season, d.team_id.astype(int))), index=d.index).isin(drop)
    rows += fit_rows('exclude_top10_possession_gap_teams_in_flagged_seasons', 'pooled', d[keep],
                     note=f'{len(drop)} team-seasons excluded')
    pd.DataFrame(rows).to_csv(AUDIT / 'final_robustness.csv', index=False)
    lineups = pd.read_csv(OUT / 'lineups.csv', dtype={'team_id': str})
    d_selection = d.assign(team_id=d.team_id.astype(str))
    selection_table(lineups, d_selection).to_csv(AUDIT / 'selection_table.csv', index=False)
    out = pd.DataFrame(rows)
    print(out[out.term == 'complementarity'][['specification', 'scope', 'effect_per_sd', 'ci_low_per_sd', 'ci_high_per_sd',
        'equivalent_within_margin', 'min_detectable_effect_per_sd']].to_string(index=False))

if __name__ == '__main__':
    main()
