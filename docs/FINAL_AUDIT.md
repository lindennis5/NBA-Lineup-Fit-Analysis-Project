# Final audit

Branch `finish/final-release`. Plan: [`PLAN.md`](../PLAN.md). This file records what was verified, what was found, and what is still blocked. The null finding stands: nothing in the audit gives a reason to revise it.

## Status

| Area | Status | Evidence |
|---|---|---|
| Independent season validation (B2) | **Done** | `docs/audit/external_team_check.csv`, `docs/season_validation_status.csv` |
| Claims vs outputs (B4) | **Done** (mechanism); re-run after every regeneration | `docs/claims.json`, `tests/test_claims_trace.py` |
| Clean-environment install and tests (item 3) | **Done** | pip install of `requirements-lock.txt` into a fresh venv; `pip check` clean; test suite passes |
| Raw data re-acquisition and checksum check (B1) | **Blocked, in progress** | The provider (api.pbpstats.com) intermittently returns HTTP 502 and responds in 20–60 s; only part of the raw cache could be rebuilt. See below. |
| Structural validation of IDs, lineups, possessions, coverage (B3) | **Code and tests written; run blocked** | `src/structural_checks.py`, `tests/test_structural_checks.py`; needs the rebuilt processed tables |
| Robustness and sample sensitivity (B5, B6) | **Code and tests written; run blocked** | `src/final_robustness.py`, `tests/test_final_robustness.py`; the 17 pre-existing specifications are in `docs/extended_coefficients.csv` |
| Alternative metrics (section 3 of the plan) | **Pre-registered, code and tests written; run blocked** | `docs/metric_preregistration.md` (committed first), `src/alternative_metrics.py`, `src/metric_comparison.py` |
| Figures (7 planned) | **Code written; regeneration blocked** | `src/final_figures.py` |

Nothing marked blocked has results yet. No result is claimed for it anywhere in the README, article, site or career file.

## B1. Data availability and reproducibility

- At the start of this work `data/raw` held 74 files (2022–23 only) and `data/processed` was empty, so the four-season numbers could not be re-derived locally. The numbers in the documents were checked against the committed `docs/` outputs, where they match.
- Raw payloads verified so far match `docs/raw_inventory.json` byte for byte (`scripts/verify_raw_inventory.py`: 0 mismatched among the files already re-downloaded). Missing files are listed by that script.
- A background retry loop keeps downloading until `docs/download_failures.json` is empty. When it completes, run the commands in `docs/REPRODUCING.md` (`run.py --release`, `scripts/compare_outputs.py docs/runs/7955a2391b0d docs`, then the audit steps) and the revision gate in `PLAN.md` applies.

## B2. The 2024–25 and 2025–26 discrepancies

Independent source: Basketball-Reference team and opponent totals (`data/external/bbref_*_team_totals.csv`, with URL and retrieval time). Points and games must match exactly; possessions are compared with the box-score estimate `FGA + 0.44·FTA − ORB + TOV` for the team and its opponents. The pass tolerance is data-calibrated: the largest relative gap seen in the two seasons whose league counters balance (3.775%).

| Season | Teams with exact points/games match | Mean provider-minus-estimate gap, offense / defense | Disposition |
|---|---:|---|---|
| 2022–23 | 30 of 30 | −2.80% / −2.81% | validated |
| 2023–24 | 30 of 30 | −2.78% / −2.78% | validated |
| 2024–25 | 19 of 30 | −2.80% / −2.80% | provisional |
| 2025–26 | 28 of 30 | −2.81% / −2.08% | provisional |

**Findings**

- **2024–25 (points):** provider points scored are 57 below the independent totals on 11 teams (largest: Knicks, 12); opponent points match except 1 point for Portland. That is the whole league imbalance of −56 and it is a loss of scored points, not a possessions problem. Cause unresolved. The 25 lineups whose provider plus-minus disagrees with points minus opponent points are the same family of defect; they are listed in `docs/provider_plusminus_discrepancies.csv`.
- **2025–26 (possessions):** the offensive side sits at the same gap to the estimate as in every earlier season (about −2.8%). The defensive side sits 0.73 percentage points higher, on every team. So the 1,850-possession league imbalance is an inflation of defensive possessions, not a loss of offensive ones. Cause unresolved. Points are off by 1 on two teams.
- **Limits of the possession check.** The estimator's own error (about 2.8% low, up to 3.8% for single teams) is far larger than the 0.73-point shift. The calibrated tolerance therefore cannot flag 2025–26 by itself; the diagnosis comes from comparing the offensive and defensive gaps. Points and games are the exact test.
- No provider data were repaired or guessed. The headline estimate uses only validated seasons; the pooled estimate is labelled provisional.

## B4. Claims vs outputs

`python -m src.claims` builds `docs/claims.json` from the regenerated outputs. `tests/test_claims_trace.py` scans the README, fan explanation, article, career file and site: every number with a decimal point, a percent sign or three or more digits must equal a claim value rounded to the precision shown, and banned wording is rejected. The detector is itself tested with a fabricated number. Run after every regeneration.

## Claims ladder

| Level | What this project says | Basis |
|---|---|---|
| Association | Closing the largest gap is not associated with better net rating beyond the fifth player's quality and skills; estimates and intervals are in the README. | Core fixed-effects model, franchise-clustered intervals, wild bootstrap. |
| Prediction | Adding the score does not improve next-season prediction of **within-core** differences. It says nothing about absolute lineup ratings. | Season-forward validation, franchise bootstrap interval conditional on fitted models. |
| Causation | **Not claimed.** | Coaches choose lineups; injuries, opponents and matchups are not modeled. |

## Metric verdict

The largest-gap-closure score is a poor representation of fit: it credits one of five dimensions, caps credit at the gap, divides by five, and uses core means. In the primary sample 39.3% of rows score exactly zero, 9.3% of cores have no gap at all, and the Knicks core's gap is 0.34 SD. Brunson's zero is a symptom. The original model is preserved as the headline. Three alternatives were pre-registered (`docs/metric_preregistration.md`): A1 deficiency-weighted skill supply, A2 skill redundancy, A3 specialist coverage. Unit tests confirm the definitions on the Knicks example. **Their results are not yet available (blocked on B1).** The decision rule is fixed: an alternative is supported only if Holm-adjusted p < 0.05 on the validated sample, the pooled estimate agrees in sign with an interval excluding zero, and the forward ΔRMSE interval lies entirely below zero. Otherwise it is reported as not supported.

## Unresolved

1. B1 data re-acquisition (provider outage); everything downstream of it, including B3, B5, B6, the alternative-metric results and the regenerated figures and notebooks.
2. Causes of the provider discrepancies in 2024–25 and 2025–26.
3. Remote CI has not been run; nothing was pushed.
4. `notebooks/01_data_feasibility.ipynb` still carries an accidental error output from a system-Python run (uncommitted); it is overwritten when notebooks are regenerated.
