# Does the fifth player fill the gap?

## TL;DR

Filling a lineup's biggest measured weakness sounds useful, but this project has not shown that this particular fit score improves predictions beyond the fifth player's prior production and skills. There is no supported reason to use it as a lineup-selection rule yet. That does not establish that basketball fit is unimportant.

Take an example from my favourite team, the New York Knicks. In 2024–25, one of their four-player cores consisted of Karl-Anthony Towns, OG Anunoby, Josh Hart and Mikal Bridges. Using the previous season's player profiles, the model identifies blocks as their largest measured gap. Jalen Brunson receives a gap-closure score of zero because his block rate does not improve that dimension. His strong creation and playmaking scores do not earn credit in this narrow fit measure. A zero score therefore does not mean Brunson adds no value or is a poor fit. It means the metric asks a much narrower question than a coach does. This core was selected for having the most eligible Knicks exposure, not for producing a preferred result; its 2024–25 outcome data remain provisional.

The main caution is data quality: two of the four seasons have unresolved provider counter imbalances. The earlier two seasons have balanced counters and lead to the same practical conclusion, but still leave substantial uncertainty about the size of any association.

## What can actually be concluded?

**The proposed largest-gap score has not demonstrated incremental predictive value in these observed lineups.** The estimates remain compatible with both positive and negative associations. The practical conclusion is to keep this score as a research feature, rather than use it to rank substitutions or acquisitions.

This is a conclusion about one operational definition of fit. It does not show that talent always dominates fit, that lineup construction is irrelevant, or that adding a particular player causes a team to improve. Those claims require evidence this design does not provide.

## Results and uncertainty

Effects below are net points per 100 possessions for a 0.1-unit increase in gap closure. The primary comparison requires at least 50 possessions on each side, all five prior-season profiles, and multiple observed fifth players for the same core. Intervals use franchise-clustered uncertainty.

| Sample | Effect | 95% interval | Distinct lineups | Interpretation |
|---|---:|---:|---:|---|
| 2022–23 and 2023–24, balanced source counters | −0.03 | [−1.63, +1.57] | 808 | Preferred check excluding the flagged seasons; not fully externally validated |
| All four seasons | −0.04 | [−0.91, +0.82] | 1,537 | Provisional because 2024–25 and 2025–26 have unresolved source issues |

The four-season estimate is close to zero, but its interval is not proof of a negligible effect. In the earlier-season check, the range is wider still. Restricted wild franchise bootstrap p-values are 0.9585 for the balanced-counter subset and 0.898 for all four seasons. Neither provides clear evidence against a zero association. Delete-franchise jackknife results also span zero. These checks address limited franchise counts; they do not solve confounding or dependence between opponents.

Sources: [coefficient table](extended_coefficients.csv), [inference diagnostics](inference_diagnostics.json). CSV coefficients and intervals are per full unit; this report multiplies them by 0.1.

## Does the score help predict performance?

The model was trained on earlier seasons and scored on the next season. Lower prediction error is better.

| Held-out season | Talent + skills RMSE | With fit RMSE | Difference |
|---|---:|---:|---:|
| 2023–24 | 10.718173 | 10.720560 | +0.002387 |
| 2024–25, provisional | 10.563475 | 10.563546 | +0.000072 |
| 2025–26, provisional | 11.484052 | 11.483968 | −0.000084 |

Adding fit produces essentially the same errors. Across these forward tests, the RMSE difference is +0.000927, with a paired franchise-bootstrap interval of [−0.005723, +0.006855]. Positive means worse with fit. This interval is conditional on the fitted models; it does not include training uncertainty or all cross-franchise dependence. The 2023–24 test alone also shows no improvement and does not use either flagged outcome season.

The separate held-out-franchise comparison has RMSE 10.812718 without fit versus 10.817924 with fit. Both evaluations score **differences within a core**, using outcome demeaning for evaluation. They are not deployable forecasts of an unseen lineup's absolute net rating.

Sources: [forward results](season_forward_validation.csv), [prediction uncertainty](predictive_uncertainty.json), [franchise validation](heldout_club_validation.csv).

## What the Knicks example tells us

For the Towns–Anunoby–Hart–Bridges core, the prior-profile block score is −0.341 standard deviations relative to eligible players. Brunson's corresponding score is −0.949, so adding him cannot close that specific gap under the formula. His creation score is +3.456 and playmaking score +1.611. These skills enter the regression separately, but the complementarity score only rewards closing the core's single weakest measured dimension.

Brunson, Miles McBride, Cameron Payne and Delon Wright all receive zero closure scores for this core. The score cannot distinguish their fit here. Their observed lineup ratings differ, but they played different minutes, opponents and situations. Those raw ratings do not establish who should replace whom. The example explains how the feature behaves; it is not a substitution recommendation or a causal finding.

Source: [Knicks example data](knicks_example.csv). Profiles use 2023–24 inputs for 2024–25 outcomes. Interior activity means blocks, not comprehensive defense.

![Knicks profiles](../figures/knicks_example.png)

## What was analyzed and checked?

The assembled data cover 30 teams and 1,230 regular-season games in each of four seasons, 2022–23 through 2025–26. There are 70,064 distinct season-team lineups. Expanding them into core/fifth-player views produces 350,320 rows, not 350,320 independent lineups. Prior-profile requirements leave 19,795 lineups; the primary within-core comparison retains 1,537 lineups, 1,811 cores and 4,321 representations across 30 franchises.

The model compares observed fifth players alongside the same season-team four-player core. It adjusts for prior-season Game Score per 36 and five skill proxies. Possession weights are divided among retained representations so a lineup's exposure is counted once. This limits direct outcome leakage and avoids multiplying exposure; it does not remove coach selection, matchup differences, injuries or unmeasured player quality.

The audit reproduced the original pilot coefficients and standard errors exactly, strengthened cache and source validation, corrected later-season identity permutations by summing counts before calculating rates, and added forward evaluation and inference checks. Sensitivities include possession thresholds, weighting rules, alternative gap definitions and aggregation, player-minute cutoffs, quality controls, spacing measurement, outcome denominators, provider discrepancies and player influence. These are exploratory robustness checks, not independent replications. Complete outputs and any failures are retained rather than selecting the most favorable model.

Sources: [coverage](coverage_audit.csv), [results summary](results_summary.json), [pilot reproduction](pilot_reproduction.csv), [audit findings](audit_findings.md), [extended specifications](extended_coefficients.csv), [player influence](player_influence.csv).

## Data limitations that affect the conclusion

Lineup sums reconcile to provider team totals for time, both possession counters and both scoring counters. That proves the extraction matches the provider; it does not prove the provider is correct.

| Season | League points scored minus allowed | Offensive minus defensive possessions | Status |
|---|---:|---:|---|
| 2022–23 | 0 | 0 | Balanced; official team scoring and games independently matched |
| 2023–24 | 0 | 0 | Balanced; external scoring validation remains incomplete |
| 2024–25 | −56 | −2 | Provisional |
| 2025–26 | 0 | −1,850 | Provisional |

The causes of the imbalances remain unresolved. They have not been repaired by substituting guessed values. In 2024–25, 25 source lineups also have provider PlusMinus values that differ from points minus opponent points. The primary outcome uses scoring and possession counters, not that PlusMinus field; alternative outcomes and exclusion checks are retained. The two balanced seasons provide a transparent restricted comparison, not a declaration that their lineup assignments are error-free.

The official 2022–23 check matches all 30 teams' games, points and opponent points to the NBA's [Thunder 2023–24 media guide](https://cdn.nba.com/teams/uploads/sites/1610612760/2023/10/mediaguide-2324.pdf), printed pages 102–103. This does not independently validate possessions or lineup assignments. See [official reconciliation](official_reconciliation.csv) and [season validation](season_validation_status.csv).

## What would change the conclusion?

First, reconcile the flagged source seasons with independent game-level records and establish consistent possession definitions. Then improve the basketball measurement: blocks omit most defensive work, box-score spacing omits gravity, and Game Score does not fully measure player impact. Prior-profile requirements also exclude rookies and many low-minute players.

A more convincing positive finding would require an effect that survives defensible measurement choices and improves genuinely held-out predictions by a meaningful amount. A more convincing negligible-effect claim would require a prespecified practical equivalence margin and intervals narrow enough to rule out important effects. Neither standard is met here.

The current evidence supports a limited but useful decision: **do not treat this gap-closure metric as a validated lineup decision tool.** Preserve the basketball question and improve the data and measurement before making a stronger claim.

## Reproduction and release status

The four-season pipeline and all seven notebooks executed successfully on Windows with Python 3.12.2. Notebook execution uses local IPython namespaces; native Jupyter kernel execution was not separately certified. The final numerical snapshot is `docs/runs/7955a2391b0d`; an earlier snapshot is explicitly marked developmental. Tests and dependency checks are recorded in [test results](test_results.txt). Remote CI and publication have not been performed.

See [reproduction instructions](REPRODUCING.md), [methodology](methodology_notes.md), and [publication instructions](PUBLISHING.md). The completed release is a reproducible observational study with a qualified conclusion; source reconciliation and causal identification remain open work.
