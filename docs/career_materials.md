# Career materials

Every number below appears in `docs/claims.json` (built from regenerated outputs) and is enforced by `tests/test_claims_trace.py`. No employer, title or team-outcome claims are made. Edit tone to taste; do not add numbers that are not traceable.

## Resume bullets

- Built a reproducible Python pipeline that assembles 70,064 five-player NBA lineups across four seasons and reconciles every team's time, possessions and points to provider totals, with an automated test suite that fails the build on mismatched data.
- Tested whether filling a lineup's largest skill gap beats adding a more talented player using core fixed-effects regression with franchise-clustered inference; reported a null result (−0.03 net points per 100 possessions per 0.1 gap closed, 95% interval [−1.63, +1.57]) rather than a forced finding.
- Audited the source data against an independent site and found the provider's 2024–25 points scored 57 short across 11 teams and 2025–26 defensive possessions inflated by 0.73 percentage points; labelled those seasons provisional and reported the validated seasons as the headline.
- Pre-registered three alternative fit metrics before running them, with a three-gate decision rule and multiple-testing adjustment, to avoid choosing a metric after seeing results.

## LinkedIn description

NBA Lineup Fit Analysis: an end-to-end sports analytics study asking whether filling a four-player lineup's biggest skill gap helps more than adding a better player. I built the data pipeline (70,064 lineups across four seasons), validated it against an independent source, fit a within-core regression with franchise-clustered uncertainty, and reported an honest null: an estimate of −0.03 net points per 100 possessions per 0.1 gap closed, with a 95% interval of [−1.63, +1.57], and no gain in next-season prediction. The audit documents two seasons with unresolved provider data issues, and the project includes a Knicks example showing why the metric gives Jalen Brunson a score of zero. Python, pandas, statsmodels; code, tests and write-ups are public.

## 60–90 second interview answer

"I wanted to know whether the idea of lineup fit survives a data test: does a fifth player who fills a four-player core's biggest skill gap help beyond just being better? I built a dataset of 70,064 five-player lineups across four seasons and compared different fifth players beside the same four teammates, controlling for the fifth player's prior production and skills, with uncertainty clustered by franchise. The answer was no: about −0.03 net points per 100 possessions per 0.1 of gap closed, with a 95% interval from −1.63 to +1.57, so zero is well inside it. I checked the data against an independent source and found two seasons I couldn't validate, so I reported the two clean seasons as the headline and labelled the rest provisional. I also showed the metric is weak: it gives Jalen Brunson a zero for a Knicks core despite elite creation and playmaking, so I pre-registered three alternatives before testing them. What I'd do next is get better skill measures, like tracking data, before saying anything stronger about fit."

## Technical Q&A

**Why core fixed effects?** They compare fifth players beside the same four teammates, removing differences between cores such as team quality and style.

**Why cluster by franchise?** Lineups from one franchise share players, coaches and opponents, so they are not independent. With 30 franchises I also ran a wild bootstrap (p-values 0.96 and 0.90) and a delete-one-franchise jackknife.

**What does the null mean, given the interval?** The estimate is near zero, but the 95% interval [−1.63, +1.57] per 0.1 gap is wide: modest effects of either sign are not ruled out.

**Why is this not causal?** Coaches choose lineups, and injuries, opponents and matchups are unmodeled. The estimates describe association among observed lineups.

**What did the data discrepancy do?** The independent check failed in 2024–25 and 2025–26, so those seasons are provisional. The validated-season estimate is the headline; the pooled estimate (−0.04, [−0.91, +0.82]) is secondary.

**Why pre-register alternative metrics?** To prevent picking the metric that happened to look best. Three alternatives, one decision rule, multiple-testing correction, and all results reported.

**What does the Brunson zero show?** The score credits only the single largest gap. For the 2024–25 Knicks core that gap is blocks, so Brunson gets zero despite creation +3.46 SD and playmaking +1.61 SD.

**How did you handle five views of one lineup?** Each lineup appears once as each possible fifth player; its exposure is split across retained views so it is not counted five times.

**Why does the prediction test only score within-core differences?** The model estimates contrasts among fifth players for a given core, not a core's absolute rating, so scoring anything else would be misleading.

**What would you change?** Better skill proxies (tracking, defensive impact), game-level data for opponent dependence, and new-season data to confirm any metric that passes the pre-registered gates.
