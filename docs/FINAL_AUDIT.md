# Final audit

Branch `finish/final-release`. Plan: [`PLAN.md`](../PLAN.md). Pre-registration: [`metric_preregistration.md`](metric_preregistration.md). **The null finding stands: no check in this audit gives a reason to revise it.** The revision gate in the plan never triggered: no primary 95% interval excludes zero, no primary sign flipped, and the regenerated outputs match the frozen snapshot.

## Status

| Area | Status | Evidence |
|---|---|---|
| B1 Raw data and reproducibility | **Done** | 450 of 457 inventory files re-downloaded with 0 checksum mismatches (the 7 absent files are API probe files the pipeline never reads); `run.py --release --notebooks` completes offline in about a minute; 25 result files match snapshot `docs/runs/7955a2391b0d` at 1e-9 (one intentional difference: new `disposition` column) |
| B2 Season discrepancies | **Documented** (origins unresolved) | `docs/audit/external_team_check.csv`, `docs/season_validation_status.csv` |
| B3 IDs, lineups, possessions, coverage | **Done; one flag** | `docs/audit/structural_checks.json`, `docs/audit/player_spotcheck.csv` |
| B4 Claims vs outputs | **Done** | `docs/claims.json`, `tests/test_claims_trace.py` |
| B5, B6 Robustness | **Done** | `docs/audit/final_robustness.csv`, `docs/audit/selection_table.csv`, `docs/extended_coefficients.csv` |
| Alternative metrics | **Done; all null** | `docs/audit/metric_comparison.csv`, `docs/audit/metric_diagnostics.json` |
| Figures | **Done** (7; 6 redundant ones removed) | `figures/` |
| Notebooks | **Done** (7, no error outputs) | `scripts/check_notebooks.py` |

## B1. Reproducibility

The raw cache had to be rebuilt (it held only 2022–23 at the start). The provider (api.pbpstats.com) was slow and intermittently returned HTTP 502; the download was stopped by the project owner with 450 of 457 payload files present. The 7 absent files are `probe_*.json`, `pbp_latest_teams.json`, `pbp_team_lineup.json` and `pbpstats_openapi.json`, written during the original feasibility probes; no analysis step reads them. Every payload that was re-downloaded matches its recorded checksum, so the provider has not revised the records retrieved. The results of the final run are archived in `docs/runs/add2163bee5b`. Python 3.14.8 with the locked dependencies reproduces the Windows/3.12 results to within 1e-9.

## B2. The 2024–25 and 2025–26 discrepancies

Independent source: Basketball-Reference team and opponent totals (`data/external/`, with URL and retrieval time). Points and games must match exactly; possessions are compared with the box-score estimate `FGA + 0.44·FTA − ORB + TOV`. The tolerance is data-calibrated: the largest relative gap seen in the two balanced seasons (3.775%).

| Season | Teams with exact points/games match | Mean provider-minus-estimate gap, offense / defense | Disposition |
|---|---:|---|---|
| 2022–23 | 30 of 30 | −2.80% / −2.81% | validated |
| 2023–24 | 30 of 30 | −2.78% / −2.78% | validated |
| 2024–25 | 19 of 30 | −2.80% / −2.80% | provisional |
| 2025–26 | 28 of 30 | −2.81% / −2.08% | provisional |

- **2024–25:** provider points scored are 57 below the independent totals on 11 teams (largest: Knicks, 12); opponent points match except 1 point for Portland. That is the league imbalance of −56, a loss of scored points rather than a possessions problem. The player spot-check localizes the Knicks' 12 points: Anunoby is 8 points short and Hart 2 (and 1 assist); Brunson matches exactly. Origin unresolved. The 25 lineups whose provider plus-minus disagrees with points minus opponent points are listed in `docs/provider_plusminus_discrepancies.csv`.
- **2025–26:** the offensive side sits at the same gap to the estimate as in every earlier season (about −2.8%). The defensive side sits 0.73 percentage points higher on every team: the 1,850-possession league imbalance is inflated defensive possessions, not lost offensive ones. Origin unresolved. Points are off by 1 on two teams.
- **Limit of the possession check:** the estimator's own error (about 2.8% low, up to 4% for single teams) dwarfs the 0.73-point shift, so the calibrated tolerance cannot flag 2025–26 alone; the diagnosis comes from comparing the offensive and defensive gaps, and points and games are the exact test.
- No provider data were repaired or guessed. The headline estimate uses only validated seasons; pooled results are labelled provisional.

## B3. Structural validation (`docs/audit/structural_checks.json`)

| Check | 2022–23 | 2023–24 | 2024–25 | 2025–26 |
|---|---|---|---|---|
| 30 teams, 82 games each | pass | pass | pass | pass |
| Team minutes within 3,936–4,200 | pass | pass | pass | pass |
| Team possessions per game within 85–110 | pass | pass | pass | pass |
| Player-to-team points ratio ≥ 0.995 | 0.9989 | 0.9972 | 0.9967 | 0.9952 |
| No player on more than 3 teams | pass | pass | pass | **flag** |
| Lineups with an ID missing from the player file | 252 (0.6% of possessions) | 673 (1.7%) | 685 (1.9%) | 1,132 (2.8%) |
| Share of lineup possessions with all five prior profiles | 41.0% | 50.8% | 42.1% | 39.2% |

- The flag is Charles Bassey, who appears on four teams in 2025–26 (BOS, GSW, MEM, PHI) with 36, 202, 66 and 10 possessions. That is plausible for a player moved between teams, but it is not independently verified, and the check is reported as failed rather than relaxed.
- Unresolved IDs are lineups containing players absent from the season's player file, a small share of exposure.
- **Selection:** only about 39–51% of lineup possessions have all five prior profiles (rookies and low-minute players are excluded), so the sample describes established rotations. See `docs/audit/selection_table.csv`.
- **Player spot-check:** the 10 most influential players, plus Brunson (already among them), against Basketball-Reference totals for five seasons: 50 player-seasons, 48 exact on points, assists and blocks; the two exceptions are the 2024–25 Knicks gaps above; minutes within 0.04%.

## B5, B6. Robustness and sample sensitivity

Effects are per 1 within-core SD of the fit score; net points per 100 possessions; 95% franchise-clustered intervals. Equivalence margin (fixed in the plan): ±1.0, using the 90% interval.

| Specification | Sample | Effect | 95% interval | Equivalent within ±1.0? | Min. detectable effect |
|---|---|---:|---:|---|---:|
| Primary | Validated seasons | −0.02 | [−1.33, +1.28] | no (inconclusive) | 1.84 |
| Primary | All four seasons (provisional) | −0.04 | [−0.74, +0.66] | yes | 0.99 |
| Primary | 2022–23 / 2023–24 / 2024–25 / 2025–26 | +0.17 / −0.19 / −0.01 / −0.14 | all include zero | no | 2.3–3.0 |
| Leave one season out | Pooled, drop each season | −0.06 / −0.01 / −0.07 / −0.01 | all include zero | yes | 1.1–1.3 |
| Large-gap subgroup (top quartile of core gaps) | Pooled / validated | +0.17 / +0.34 | both include zero | no | 2.0 / 3.8 |
| Drop the 10 teams with the largest possession gap in flagged seasons | Pooled | +0.21 | [−0.73, +1.15] | yes | 1.3 |

All of the 17 existing specifications (weights, outcome definitions, controls, thresholds, profile minutes, spacing definition, median core) are in `docs/extended_coefficients.csv` and the figure `figures/robustness_effects.png`: every interval includes zero. **Reading:** no evidence of a benefit in any sample or subgroup. With only the validated seasons, the data cannot rule out effects as large as the ±1.0 margin; with all four seasons the interval sits inside it. The large-gap subgroup is positive but very wide, and is reported as such.

## Alternative metrics (pre-registered 2026-10-20 before testing)

A1 deficiency-weighted skill supply, A2 skill redundancy, A3 specialist coverage; same model, sample and clustering as the primary; Holm correction across the three; supported only if all three gates pass.

| Score | Validated seasons: effect per SD [95% interval] | Wild p | Holm p | Pooled effect [95% interval] | Forward ΔRMSE [95% interval] | Rows exactly 0 | Verdict |
|---|---|---:|---:|---|---|---:|---|
| Original | −0.02 [−1.33, +1.28] | 0.96 | n/a | −0.04 [−0.74, +0.66] | +0.0009 [−0.0057, +0.0069] | 37.7% (39.3% pooled) | reference |
| A1 | −0.28 [−1.70, +1.14] | 0.60 | 1.00 | −0.26 [−1.02, +0.51] | −0.0011 [−0.0094, +0.0086] | 10.9% | not supported |
| A2 | +0.13 [−1.49, +1.75] | 0.83 | 1.00 | −0.09 [−0.98, +0.80] | +0.0074 [−0.0015, +0.0152] | 29.6% | not supported |
| A3 | +0.27 [−1.14, +1.67] | 0.62 | 1.00 | +0.18 [−0.74, +1.09] | +0.0032 [−0.0049, +0.0115] | 41.4% | not supported |

No alternative passes any of the three gates. A1 does separate the Knicks candidates (Brunson +0.84, McBride −0.53, Payne −0.16, Wright −0.12), and A3 gives Brunson 4.44 against 0.26 to 0.59 for the other three, but neither translates into a detectable performance association. The original model is unchanged and remains the headline.

## Claims ladder

| Level | What this project says | Basis |
|---|---|---|
| Association | Closing the largest gap is not associated with better net rating beyond the fifth player's quality and skills. | Core fixed-effects model; franchise-clustered intervals; wild bootstrap. |
| Prediction | Adding the score does not improve next-season prediction of **within-core** differences; nothing is said about absolute lineup ratings. | Season-forward validation; franchise bootstrap interval conditional on fitted models. |
| Causation | **Not claimed.** | Coaches choose lineups; injuries, opponents and matchups are not modeled. |

## B4. Claims vs outputs

`python -m src.claims` builds `docs/claims.json` from regenerated outputs; `tests/test_claims_trace.py` scans the README, fan explanation, article, career file and site. Every number with a decimal point, a percent sign or three or more digits must equal a claim value rounded to the precision shown, and banned causal wording is rejected. The detector is tested with a fabricated number.

## Unresolved

1. Origins of the provider discrepancies in 2024–25 (scored points) and 2025–26 (defensive possessions).
2. 2024–25 and 2025–26 remain provisional; the pooled estimate depends on them.
3. The Charles Bassey flag and the 252–1,132 lineups per season with unresolved IDs are documented, not explained.
4. Effects up to about 1.0 net points per 100 possessions per SD cannot be ruled out with the validated seasons alone.
5. Remote CI has not been run (nothing is pushed from this machine without credentials).
