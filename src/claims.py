"""Build docs/claims.json: the curated numbers that README, article, site and career text may quote.

Every number in prose must equal one of these values rounded to the precision shown
(tests/test_claims_trace.py). Values come only from regenerated output files.
"""
import json
import numpy as np
import pandas as pd
from .data_pipeline import ROOT

DOCS = ROOT / 'docs'
AUDIT = DOCS / 'audit'
# Fixed design constants that may appear in prose (thresholds, seeds, draws, scale factors).
CONSTANTS = {'bootstrap_draws': 1999, 'bootstrap_seed': 20261016, 'primary_min_possessions': 50,
             'profile_min_minutes': 500, 'threshold_low': 25, 'threshold_high': 100, 'equivalence_margin': 1.0,
             'games_per_team': 82, 'teams': 30, 'seasons': 4, 'gap_unit': 0.1, 'possession_formula_ft': 0.44,
             'minutes_floor': 3936, 'minutes_ceiling': 4200, 'provider_http_error': 502}

def load(name, directory=DOCS):
    path = directory / name
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8')) if name.endswith('.json') else pd.read_csv(path)

def put(values, key, value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return
    if np.isfinite(number):
        values[key] = number

def build():
    v = dict(CONSTANTS)
    summary = load('results_summary.json') or {}
    for k in ['unique_lineups', 'all_cores', 'all_core_fifth_rows', 'eligible_player_profiles', 'feature_complete_lineups',
              'primary_rows', 'primary_cores', 'primary_lineups', 'primary_clubs', 'talent_complementarity_correlation',
              'zero_fill_share', 'no_gap_core_share']:
        put(v, f'summary.{k}', summary.get(k))
    for model, rmse in (summary.get('heldout_rmse') or {}).items():
        put(v, f'heldout_rmse.{model}', rmse)
    robust = load('final_robustness.csv', AUDIT)
    if robust is not None:
        for _, r in robust[robust.get('error').isna() if 'error' in robust else slice(None)].iterrows():
            base = f'robust.{r.specification}.{r.scope}.{r.term}'
            for col in ['coefficient_per_unit', 'ci_low', 'ci_high', 'p_value', 'lineups', 'cores', 'clubs', 'effect_per_sd',
                        'ci_low_per_sd', 'ci_high_per_sd', 'ci90_low_per_sd', 'ci90_high_per_sd',
                        'min_detectable_effect_per_sd', 'sd_within_core']:
                put(v, f'{base}.{col}', r.get(col))
            for col in ['coefficient_per_unit', 'ci_low', 'ci_high']:   # per 0.1 unit, as quoted in prose
                put(v, f'{base}.{col}_per_0.1', r.get(col) * .1 if pd.notna(r.get(col)) else None)
    ext_c = load('extended_coefficients.csv')
    if ext_c is not None:
        for _, r in ext_c[ext_c.term.isin(['complementarity', 'fifth_quality'])].iterrows():
            base = f'ext.{r.scope}.{r.specification}.t{int(r.threshold)}.{r.term}'
            for col in ['coefficient', 'ci_low', 'ci_high', 'p_value']:
                put(v, f'{base}.{col}', r[col])
            for col in ['coefficient', 'ci_low', 'ci_high']:
                put(v, f'{base}.{col}_per_0.1', r[col] * .1)
            for col in ['lineups', 'cores', 'clubs']:
                put(v, f'{base}.{col}', r[col])
    meta = load('metric_comparison.csv', AUDIT)
    if meta is not None:
        for _, r in meta.iterrows():
            base = f'metric.{r.scope}.{r.metric}'
            for col in ['effect_per_sd', 'ci_low_per_sd', 'ci_high_per_sd', 'wild_p', 'holm_p', 'zero_share',
                        'corr_with_fifth_quality', 'forward_delta_rmse', 'forward_ci_low', 'forward_ci_high', 'lineups']:
                put(v, f'{base}.{col}', r.get(col))
    diag = load('metric_diagnostics.json', AUDIT) or {}
    for metric, share in (diag.get('primary_sample_zero_share') or {}).items():
        put(v, f'metric.primary_zero_share.{metric}', share)
    for i, row in enumerate(diag.get('knicks_2024_25_example') or []):
        for col in ['possessions', 'net_rating', 'complementarity', 'alt_deficiency_supply', 'alt_redundancy', 'alt_specialist_coverage']:
            put(v, f'knicks.{row["fifth_id_name"]}.{col}', row.get(col))
    knicks = load('knicks_example.csv')
    if knicks is not None:
        first = knicks.iloc[0]
        for col in ['deficiency_gap'] + [c for c in knicks.columns if c.startswith(('core_', 'fifth_')) and c != 'fifth_id_name']:
            put(v, f'knicks.{first.fifth_id_name}.{col}', first[col])
        put(v, 'knicks.core_gap', first.deficiency_gap)
    boot = load('inference_diagnostics.json') or {}
    for scope, d in boot.items():
        for col in ['wild_cluster_p', 'jackknife_ci_low', 'jackknife_ci_high']:
            put(v, f'wild.{scope}.{col}', d.get(col))
    fwd = load('season_forward_validation.csv')
    if fwd is not None:
        for _, r in fwd.iterrows():
            put(v, f'forward.{r.test_season}.{r.model}.rmse', r.rmse)
        piv = fwd.pivot(index='test_season', columns='model', values='rmse')
        for season, r in piv.iterrows():
            put(v, f'forward.{season}.delta', r.complementarity - r.baseline)
    unc = load('predictive_uncertainty.json') or {}
    for col in ['delta_rmse', 'ci_low', 'ci_high']:
        put(v, f'forward.all.{col}', unc.get(col))
    status = load('season_validation_status.csv')
    if status is not None:
        for _, r in status.iterrows():
            for col in ['points_balance', 'possession_balance', 'off_poss_balance' if 'off_poss_balance' in status else 'games']:
                put(v, f'season.{r.season}.{col}', r.get(col))
            put(v, f'season.{r.season}.validated', float(r.get('disposition') == 'validated'))
            put(v, f'season.{r.season}.possession_balance_abs', abs(r.possession_balance))
            put(v, f'season.{r.season}.points_balance_abs', abs(r.points_balance))
    ext = load('external_team_check.csv', AUDIT)
    if ext is not None:
        for season, g in ext.groupby('season'):
            put(v, f'external.{season}.teams_exact_pass', g.exact_pass.sum())
            put(v, f'external.{season}.points_shortfall', -g.points_diff.sum())
            put(v, f'external.{season}.teams_with_point_gap', (g.points_diff != 0).sum() + 0 * g.opp_points_diff.sum())
            put(v, f'external.{season}.mean_off_gap_pct', 100 * g.off_rel_gap.mean())
            put(v, f'external.{season}.mean_def_gap_pct', 100 * g.def_rel_gap.mean())
            put(v, f'external.{season}.def_minus_off_gap_pct', 100 * (g.def_rel_gap.mean() - g.off_rel_gap.mean()))
        base = ext[ext.season.isin(['2022-23', '2023-24'])]
        put(v, 'external.calibrated_tolerance_pct', 100 * max(base.off_rel_gap.abs().max(), base.def_rel_gap.abs().max()))
        put(v, 'external.nyk_2024_25_points_shortfall', -ext[(ext.season == '2024-25') & (ext.team == 'NYK')].points_diff.sum())
    if meta is not None:
        for _, r in meta.iterrows():
            put(v, f'metric.{r.scope}.{r.metric}.zero_share_pct', 100 * r.zero_share)
    structural = load('structural_checks.json', AUDIT) or {}
    for season, r in structural.items():
        if season == 'spot_check':
            for k, x in r.items():
                put(v, f'spot_check.{k}', x)
            continue
        put(v, f'structural.{season}.points_ratio', r.get('player_to_team_points_ratio'))
        put(v, f'structural.{season}.profile_possession_share', (r.get('profile_coverage') or {}).get('possession_share'))
        put(v, f'structural.{season}.unresolved_lineups', (r.get('unresolved_ids') or {}).get('lineups'))
    return v

def token_forms(value):
    """All strings a quoted value may take: rounded to 0-4 decimals, and as a percentage."""
    forms = set()
    for x in (abs(value), abs(value) * 100):
        for d in range(0, 5):
            forms.add(f'{round(x, d):,.{d}f}')
            forms.add(f'{round(x, d):.{d}f}')
    return sorted(forms)

def main():
    values = build()
    tokens = sorted({t for x in values.values() for t in token_forms(x)})
    (DOCS / 'claims.json').write_text(json.dumps({'values': values, 'tokens': tokens}, indent=1, sort_keys=True), encoding='utf-8')
    print(f'{len(values)} claim values; {len(tokens)} accepted number strings')

if __name__ == '__main__':
    main()
