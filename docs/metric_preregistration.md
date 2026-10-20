# Metric pre-registration

Written 2026-10-20, **before any alternative metric was computed on outcome data**. The commit that adds this file must precede the commit that adds `docs/audit/metric_comparison.csv`.

## Why

The original largest-gap-closure score credits one of five skill dimensions, caps credit at the gap, divides by five and uses core means. In the primary sample 39.3% of rows score exactly zero and 9.3% of cores have no deficiency at all. Jalen Brunson scores zero for the 2024–25 Towns–Anunoby–Hart–Bridges core despite creation +3.46 SD and playmaking +1.61 SD. The original model remains the headline; the three alternatives below are the only ones that will be tested.

## Definitions

All use the lagged, standardized skills already in the pipeline (spacing, playmaking, creation, rebounding, interior). `c_k` is the four-player core mean of skill k, `c_ik` is core player i's skill k, `f_k` is the fifth player's skill k, `g_k = max(0, −c_k)`.

| ID | Definition | Rationale | Expected sign |
|---|---|---|---|
| A1 deficiency-weighted skill supply | `Σ_k g_k·f_k / Σ_k g_k`; 0 if `Σ_k g_k = 0` | The fifth player brings skill where the core is weak, in proportion to how weak. Uses every gap; no cap, no zero mass. | + |
| A2 skill redundancy | `Σ_k max(0,c_k)·max(0,f_k)` | Stacking skills the core already has has diminishing returns. | − |
| A3 specialist coverage | `Σ_k max(0, f_k − max_i c_ik)` over the four core players | A lineup needs one elite specialist, not four slightly-above-average players; non-additive. | + |

## Models

Identical to the primary model: core fixed effects, fifth-player quality and five skill main effects, possession weights divided across a lineup's retained representations, 50-possession-per-side threshold, franchise-clustered CR1 errors, restricted wild franchise bootstrap (seed 20261016, 1,999 draws). Each alternative replaces the `complementarity` column in a copy of the data; the original column is never overwritten. Effects are reported per 1 within-core SD of the score and per 0.1 unit.

Samples: (1) validated seasons (primary for the alternatives), (2) all four seasons pooled (secondary, provisional seasons marked).

## Decision rule

An alternative is **supported** only if all three hold:
1. Holm-adjusted wild-bootstrap p < 0.05 across the three alternatives on the validated-season sample.
2. The pooled estimate has the same sign and its 95% CI excludes zero.
3. The season-forward paired ΔRMSE CI lies entirely below zero (improvement).

Otherwise it is **not supported** and the null stands. All results are reported whichever way they fall. If any alternative is supported it is treated as an exploratory hypothesis needing new-season data, and the narrative is not changed without the project owner's decision.
