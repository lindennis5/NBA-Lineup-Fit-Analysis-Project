"""Test the three pre-registered alternatives against the original fit score.

Decision rule: docs/metric_preregistration.md. Each alternative is placed in a copy of the data
under the `complementarity` column so the unchanged model, bootstrap and forward-validation code
can be reused. The original column is never overwritten in the saved data.
"""
import json
import pandas as pd
from .data_pipeline import ROOT, OUT
from .lineups import comparison_sample
from .models import fit_within
from .release_audit import inference, score_contrasts, predictive_uncertainty
from .alternative_metrics import add_alternatives, ALTERNATIVES
from .effect_scale import within_core_sd, scaled_effect, holm
from .final_robustness import validated_seasons

AUDIT = ROOT / 'docs' / 'audit'
METRICS = ['complementarity'] + ALTERNATIVES
EXPECTED_SIGN = {'complementarity': 1, 'alt_deficiency_supply': 1, 'alt_redundancy': -1, 'alt_specialist_coverage': 1}

def swapped(frame, column):
    copy = frame.copy()
    copy['complementarity'] = frame[column]
    return copy

def forward(frame, column):
    seasons = sorted(frame.season.unique())
    swap = swapped(frame, column)
    records, clubs = [], []
    for cutoff in seasons[1:]:
        scored, club = score_contrasts(swap[swap.season < cutoff], swap[swap.season == cutoff], return_clubs=True)
        records.extend(r | {'test_season': cutoff} for r in scored)
        clubs.extend(club)
    return pd.DataFrame(records), predictive_uncertainty(clubs)

def main():
    d = add_alternatives(pd.read_csv(OUT / 'observations.csv'))
    good = validated_seasons()
    samples = {'validated_seasons': d[d.season.isin(good)], 'pooled': d}
    rows = []
    for scope, frame in samples.items():
        for metric in METRICS:
            swap = swapped(frame, metric)
            table, _, sample = fit_within(swap)
            r = table[table.term == 'complementarity'].iloc[0]
            diag = inference(swap)
            rows.append({'scope': scope, 'metric': metric, 'expected_sign': EXPECTED_SIGN[metric],
                'coefficient_per_unit': r.coefficient, 'se': r.se, 'ci_low': r.ci_low, 'ci_high': r.ci_high,
                'p_cr1': r.p_value, 'wild_p': diag['wild_cluster_p'], 'lineups': int(r.lineups),
                'zero_share': float((sample[metric] == 0).mean()),
                'corr_with_fifth_quality': float(sample[metric].corr(sample.fifth_quality))}
                | scaled_effect(r.coefficient, r.se, int(r.clubs), within_core_sd(sample, metric)))
    result = pd.DataFrame(rows)
    # Holm adjustment across the three alternatives on the validated sample (original is the reference).
    mask = (result.scope == 'validated_seasons') & result.metric.isin(ALTERNATIVES)
    result.loc[mask, 'holm_p'] = holm(result.loc[mask, 'wild_p'])
    fwd = {}
    for metric in METRICS:
        scored, unc = forward(d, metric)
        fwd[metric] = {'forward_delta_rmse': unc['delta_rmse'], 'forward_ci_low': unc['ci_low'], 'forward_ci_high': unc['ci_high']}
        scored.assign(metric=metric).to_csv(AUDIT / f'metric_forward_{metric}.csv', index=False)
    result = result.merge(pd.DataFrame(fwd).T.rename_axis('metric').reset_index(), on='metric')
    verdicts = {}
    for metric in ALTERNATIVES:
        v = result[(result.metric == metric) & (result.scope == 'validated_seasons')].iloc[0]
        p = result[(result.metric == metric) & (result.scope == 'pooled')].iloc[0]
        gates = {'holm_p_below_0.05': bool(v.holm_p < .05),
                 'pooled_same_sign_ci_excludes_0': bool((p.coefficient_per_unit * v.coefficient_per_unit > 0)
                                                        and (p.ci_low > 0 or p.ci_high < 0)),
                 'forward_ci_entirely_below_0': bool(v.forward_ci_high < 0)}
        verdicts[metric] = {'gates': gates, 'verdict': 'supported' if all(gates.values()) else 'not supported'}
    result['verdict'] = result.metric.map(lambda m: verdicts.get(m, {}).get('verdict', 'reference (original)'))
    result.to_csv(AUDIT / 'metric_comparison.csv', index=False)
    # Diagnostics: where the original score differs, and the Knicks/Brunson example.
    primary = comparison_sample(d, 50)
    knicks = primary[(primary.team == 'NYK') & (primary.season == '2024-25')
                     & primary.core_key.str.contains('1626157-1628384-1628404-1628969')]
    example = knicks[['fifth_id_name', 'possessions', 'net_rating', 'complementarity'] + ALTERNATIVES].to_dict('records')
    diagnostics = {'validated_seasons': good, 'verdicts': verdicts,
        'primary_sample_zero_share': {m: float((primary[m] == 0).mean()) for m in METRICS},
        'primary_sample_corr_with_quality': {m: float(primary[m].corr(primary.fifth_quality)) for m in METRICS},
        'primary_cores_with_no_gap_share': float((primary.drop_duplicates('core_key').deficiency_gap == 0).mean()),
        'knicks_2024_25_example': example}
    (AUDIT / 'metric_diagnostics.json').write_text(json.dumps(diagnostics, indent=2), encoding='utf-8')
    print(result[['scope', 'metric', 'effect_per_sd', 'ci_low_per_sd', 'ci_high_per_sd', 'wild_p', 'holm_p',
                  'forward_delta_rmse', 'verdict']].to_string(index=False))
    print(json.dumps({'verdicts': verdicts, 'knicks': example}, indent=2))

if __name__ == '__main__':
    main()
