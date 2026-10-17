# Research and engineering audit

## What the original project got right

The supplied pilot asks a specific basketball question and accepts an inconclusive result. Its implemented model matches the stated design: prior-season profiles, fixed effects for season-team four-player cores, talent and skill controls, exposure weighting, and franchise clustering. The weighted within transformation agrees numerically with explicit core indicators and their clustered covariance. The original coefficients and standard errors were reproduced without discrepancy.

Each lineup creates five views of the same performance. The original code already divides exposure among the representations that survive filtering. This was verified, not replaced as a supposed defect. The original held-out evaluation also correctly describes itself as a test of within-core contrasts, not a forecast of absolute lineup ratings.

## Confirmed defects and fixes

| Severity | Original issue | Change and validation |
|---|---|---|
| High | Analysis could continue with a points discrepancy if time and possession checks passed. | Both scoring sides now reconcile before modeling; synthetic counter perturbations fail. |
| High | Thirty rows were insufficient to prove thirty unique teams or a full season. | Require thirty distinct franchise IDs and 82 games each for this study window. Partial seasons fail. |
| High | Derived complete-lineup files could load without checksum metadata. | Record derived checksums and parent hashes; fail on missing provenance or changed parents. |
| High | Reordered player-ID encodings across date partitions became canonical-key collisions in later seasons. | Consolidate equivalent membership using additive counts before calculating ratings; reject exact repeated source IDs. |
| Medium | A cached name could be reused for a different request URL. | Verify URL identity as well as payload hash. |
| Medium | One HTTP failure could prevent attempts for subsequent teams and seasons. | Continue independent retrievals, record all failures, and fail the overall download visibly. Retrying reuses caches. |
| Medium | Invalid lineup membership could be quarantined after reconciliation, losing exposure downstream. | Fail on malformed membership instead of silently excluding it from a reconciled total. |
| Medium | Feature joins did not enforce prior-season alignment themselves. | Check exactly one-season lag and finite predictors before joining. |
| Medium | The player-response cap check assumed playing-time order. | Require descending playing time for capped responses and a boundary below the eligibility cutoff. This remains conditional on provider ordering. |
| Medium | The sensitivity called unweighted still divided by multiplicity. | Retain it as equal-lineup weighting and add true equal-representation weighting; document that they target different comparisons. |
| Medium | Analytical outputs reused the same filenames. | Preserve pilot baseline and content-keyed result snapshots with configuration and source/code hashes. Latest working outputs remain replaceable. |
| Low | SVG timestamps and random element identifiers changed on identical runs. | Fix the SVG hash seed and remove creation timestamps. |

## Methodological judgments

**Weighting.** Dividing by retained multiplicity assigns every observed five-player lineup its exposure once. It changes the relative influence of individual core comparisons; it does not create independent observations. Equal-row and exposure-per-representation alternatives are reported alongside the primary rule. No weighting choice recovers the unobserved coach-available substitution set.

**Inference.** Franchise clustering keeps overlapping lineup representations together and follows a franchise across seasons. The primary CR1 correction includes absorbed core intercepts and uses a t reference with G−1 degrees of freedom. Restricted wild franchise bootstrap-t and delete-franchise jackknife estimates assess sensitivity to the limited cluster count. None captures arbitrary dependence between opponents in shared games or every connection created by traded players. Game-level covariance cannot be recovered from season aggregates; introducing game clusters here would be false precision.

**Identification.** Report weighted design rank/condition number and the share of within-core complementarity variation remaining after projecting out fifth-player skill and quality controls. This diagnoses linear identification. It does not certify that the residual variation is free of unmeasured talent, coaching selection, opponents, or injuries.

**Talent and skill.** Game Score/36 is a prior production control, not true player impact. A quadratic version and omission sensitivities test control dependence without presenting a correlated box-score replacement as an independent validation. Blocks measure block activity only. Volume-only spacing and exclusion of the interior dimension test narrow measurement alternatives; tracking-based defensive quality and shooting gravity remain unavailable in these inputs.

**Aggregation.** The mean assumes interchangeable additive player contributions. The median sensitivity computes the actual change from the four-player median to the five-player median; it does not apply the mean's division-by-five formula to a median. Both are deliberately simplified basketball models.

**Prediction.** Train forward only on earlier seasons. Score weighted, demeaned core contrasts using RMSE and MAE. Test outcomes enter the scoring contrast, never coefficient fitting. This cannot predict an unseen core's absolute rating. The paired test-franchise bootstrap resamples all forward folds for a franchise together and conditions on fitted models; it does not include model-training uncertainty or cross-franchise game dependence.

**Exploration.** Report all specified alternatives, sign changes, failures and negative predictive comparisons. These specifications reuse the same data and are not independent confirmations. The primary specification remains 50 possessions on each side, 500 lagged minutes, mean core skills, capped largest-gap closure, and talent plus five skill controls.

## Source validation boundary

Exact agreement with PBP Stats team totals validates assembly, not the upstream parser. The official Thunder media guide provides an independent 2022–23 benchmark for all thirty franchises' games and scoring totals. The benchmark and executable comparison are versioned. Official possession totals and lineup substitution boundaries were not independently audited. A direct NBA Stats request timed out; this is an access limitation, not evidence that the provider is inaccurate.

See the research report for the final findings, achieved coverage, test record and remaining publication steps.

## Source plus-minus discrepancy

During the extension, a new audit assertion found that some provider PlusMinus values differ from Points minus OpponentPoints. For example, the 2024–25 Warriors have 9,324 points, 9,060 opponent points, and reported plus-minus 270 rather than 264. All of these fields reproduce their respective provider team totals after date partitioning. This is an upstream cross-field inconsistency, not missing partition exposure.

The model never uses the provider PlusMinus field: its outcome is explicitly calculated from each scoring side and its corresponding possessions. Therefore the unused-field identity is recorded as a diagnostic rather than used to exclude an entire season. Hard reconciliation gates remain in place for all five counters used in analysis. A sensitivity removes affected lineups and reports the resulting estimate. The exact upstream cause is unresolved. Provider documentation discusses free-throw attribution to the lineup at the foul, but that does not establish the cause of this particular team-level discrepancy: [PBP Stats free-throw documentation](https://pbpstats.readthedocs.io/en/stable/pbpstats.resources.enhanced_pbp.html).

See provider_plusminus_discrepancies.csv and coverage_audit.csv for the final counts and affected observations.

## Unresolved league conservation checks

Provider-matching team sums conceal upstream imbalance: 2024–25 league points scored minus allowed is −56 and offensive minus defensive possessions is −2; 2025–26 possession balance is −1,850. No cause has been verified and no counters were guessed or silently repaired. These seasons and pooled estimates are explicitly provisional. A restricted 2022–23/2023–24 analysis, labeled balanced_source_seasons, retains the same primary specification and inference checks. Balanced counters alone do not establish lineup-level accuracy. See season_validation_status.csv and research_report.md.
