# Methodology: initial specification

## Question and estimand

Does adding a player who closes the largest measured four-player-core skill gap predict better net performance, conditional on that player's prior box-score production and skills? This is an **observational association among actually used lineups**, not a causal comparison of every player a team could have acquired or played. We do not observe the full coach-available choice set, injuries, or assignment mechanism. “Best available” is therefore only approximated by controls for the observed fifth players' prior quality.

## Observation and identities

One row: regular-season `season + team_id + core_id + fifth_id`. A core ID is four sorted, unique NBA player IDs joined by hyphens. Lineup ID uses all five. Context keys additionally contain season and team. Every original lineup has five representations, which share net rating and exposure. Never report the expanded rows as independent lineup samples or sum their possessions without adjusting multiplicity.

Outcome: `100*points/off_poss - 100*opponent_points/def_poss`. Offensive and defensive possessions need not match, particularly in short stints. Weight by their arithmetic mean, but require **both** sides to meet the threshold. This differs from interpreting provider `TotalPoss` as offensive possessions. Use `SecondsPlayed/60` for time. Threshold comparisons: 25, 50, 100, with 10/200 descriptive checks. Initial primary threshold is 50 on each side, chosen before outcome modeling as a compromise to be revisited only transparently. It does not make lineup ratings reliable by itself.

## Lagged skill definitions

For outcomes in season t, use only player season t−1. Eligibility: at least 500 prior minutes. Exclude rather than invent profiles for rookies and low-minute/absent players; report the loss. League Player totals combine a traded player's season across teams. Do not join profiles by the source's attached team label. Normalize over eligible players in the **feature season**, unweighted, with population standard deviation. No current outcome enters the profile.

| Dimension | Initial formula | Interpretation and limits |
|---|---|---|
| Spacing proxy | Average of standardized 3PA per 100 on-court offensive possessions and standardized smoothed 3P accuracy, then standardize the composite | Accuracy = (3PM + 100×eligible-player pooled 3P%)/(3PA+100). The fixed 100-attempt prior is a transparent shrinkage choice, not fitted for results. Does not measure defensive gravity or catch-and-shoot proficiency. |
| Playmaking proxy | Assists per 100 on-court offensive possessions, standardized | Does not capture potential assists, passing quality, or teammate conversion separately. Turnovers enter the talent proxy, not this skill. |
| Creation proxy | Unassisted two- and three-point scoring points per 100 offensive possessions, standardized | Realized scoring proxy, not attempts/shot difficulty. Putbacks and role can affect interpretation. |
| Rebounding proxy | Average of standardized ORB per 100 offensive possessions and DRB per 100 defensive possessions, then standardized | Not rebound opportunity percentage; competition with teammates and role matter. |
| Interior activity proxy | Blocks per 100 defensive possessions, standardized | **Not overall defense or rim protection quality.** Does not measure deterrence, positioning, switching, opponent attempts, or contests. Results with this dimension need a four-dimension sensitivity analysis. |

All source fields and unnormalized components are retained in player_profiles.csv. Sparse omitted event-count keys are treated as zero only for the explicit enumerated event fields; whole missing columns or invalid denominators are errors.

## Core aggregation, deficiency, and complementarity

Initial core skill `c_k = (s_1k+s_2k+s_3k+s_4k)/4`. This exchangeable additive approximation is interpretable but cannot capture role requirements, saturation, or one elite creator carrying a lineup.

Largest deficiency is the lowest core skill dimension k*, **only to the extent it is below zero**, the eligible-player seasonal mean: `gap=max(0,-c_k*)`. A core above average in every dimension has no measured deficiency, even though it still has a relative weakest dimension.

Adding fifth-player skill s changes the five-player mean by `(s_k*-c_k*)/5`. Primary complementarity:

`fill = min(gap, max(0, (s_k* - c_k*)/5))`.

This measures how much of the largest standardized gap is closed. It is nonnegative and capped at the gap; strong talent alone does not necessarily generate a positive fill. Exact ties average the tied dimensions' fills. The categorical weakest label uses fixed skill order only for display.

Alternatives: average capped gap closure across all five dimensions; an uncapped signed interaction `gap*s_k*`; largest-gap closure excluding the interior/block dimension (while retaining the same fifth-player skill controls). These are sensitivity specifications, not a search for the most significant result. This version does not certify the initial score as an objective measure of basketball fit.

## Independent quality proxy

Use prior-season **Game Score per 36 minutes**, standardized within the same eligible player population. Compute from PBP Stats individual box counts using the published [Game Score formula](https://www.basketball-reference.com/about/glossary.html):

`PTS + .4*FGM - .7*FGA - .4*(FTA-FTM) + .7*ORB + .3*DRB + STL + .7*AST + .7*BLK - .4*PF - TOV`, then multiply the season sum by `2160/SecondsPlayed`.

This is a reproducible box-production control, **not BPM, RAPM, or a complete impact measure**. It overlaps the skill inputs, so the primary model also includes all five fifth-player skill main effects. A talent-only control sensitivity shows how much conclusions depend on these controls. No on-court plus-minus or lineup rating is used in talent. Prior-season measurement avoids direct same-outcome leakage but retains age/role/injury uncertainty and historical teammate confounding. Lagged BPM or properly timestamped public impact estimates remain useful extensions; current impact estimates must not be backfilled into historical predictions.

## Baseline model and dependence

Weighted least squares with a fixed intercept for every team-season four-player core:

`net_rating = core_FE + beta*prior_fifth_quality + gamma'prior_fifth_skills + delta*fill + error`.

Estimate by weighted within-core demeaning. Retain only cores with at least two eligible observed fifth players **after** all filters. Core effects absorb fixed core quality and all team/season characteristics constant within a core. Thus separate team/season indicators are redundant here. They do not adjust for changing opponents, game state, garbage time, or coaching selection.

Divide lineup exposure by its number of retained core representations so expanding to five rows cannot multiply a lineup's total regression weight. Dependence remains; cluster standard errors by franchise across seasons (G retained clubs, at most 30), use a CR1 correction including absorbed core intercepts, and t intervals with G−1 degrees of freedom. The pilot primary sample has 24 clubs and 23 reference degrees of freedom. This captures within-team overlap but not all dependence between opposing teams in shared games. Wild cluster/bootstrap and game-level data are future checks.

Fit the nested quality/skills-only baseline on the same sample. Report effect sizes and confidence intervals, within-core R² and weighted residual RMSE; do not interpret in-sample R² improvement as predictive proof. Whole-franchise holdout validation scores **within-core contrasts** and keeps all representations of any lineup together. Test outcomes are demeaned to evaluate contrasts, so that exercise is explicitly not prospective prediction of absolute lineup net ratings or unseen-core intercepts.

Sensitivity grid: 25/50/100 possessions per side; three complementarity specifications; weighted/unweighted; fifth-skill controls included/omitted. The initial implementation uses core fixed effects throughout; a separate team-only model is deferred because it would change the identifying comparison substantially. Avoid uncorrected significance fishing across the grid.

## Validation gates and unresolved risks

Verify ID uniqueness, five distinct players, five correct core expansions, no join explosions, prior-season alignment, finite features/rates, exposure reconciliation, capped responses, and API schema. Invalid lineups go to an explicit quarantine. Caches have checksums; recombined partitions are regenerated from those caches.

Team totals validate internal assembly, not the underlying parser. Technical/free-throw attribution and possession conventions can cause scoring differences that need inspection. Strong conclusions wait for independent NBA box-score reconciliation, date/game-level opponent and game-state controls, defensive alternatives, profile-threshold/shrinkage/aggregation sensitivities, and longitudinal out-of-season validation.
