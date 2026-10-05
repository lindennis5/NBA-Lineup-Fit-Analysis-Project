# Research log

## 2026-10-05 — Initial feasibility and build

- Established the row grain before modeling: team-season/core/fifth, with five dependent representations of each lineup outcome.
- Compared official NBA Stats, PBP Stats, a public lineup/PBP repository, and Basketball Reference. See data_feasibility.md for evidence and restrictions.
- Official Advanced lineup query timed out after 25 seconds. Public PBP Stats schema and totals were accessible in the approved network context.
- Found an empirical 500-row cap on league-wide Player/Lineup queries and some team Lineup queries. Rejected the league-wide lineup response as the analytical dataset.
- Implemented bounded caching, checksums, query provenance and team queries. Added recursive date partitioning for capped queries; never inferred completeness from the last returned row.
- Selected four recent outcome seasons (2022–23 through 2025–26), conditional on validation, with one additional prior feature season.
- Chose lagged player skills and a lagged Game Score/36 production proxy. Rejected same-season on-court rating as a talent control because it includes the outcomes being explained.
- Prespecified 500 prior minutes and 50 offensive plus 50 defensive possessions for the primary analysis, with explicit threshold sensitivity. These are modeling defaults, not claims of statistical reliability.
- Chose a capped gap-closure measure and documented two alternatives. Core fixed effects make comparisons within the same core; fifth-player skill main effects help distinguish an interaction from simply selecting a strong shooter/rebounder.
- Defense remains a major measurement limitation: the implemented fifth axis is interior block activity, not comprehensive defense.
- Windows console encoding failed on NBA player names during early exploration; files use UTF-8 and compact diagnostic output avoids lossy name handling.
- Created an isolated Python environment. Code and reproducible notebooks are the requested primary deliverable; no dashboard, final Medium article, or fabricated resume results.

## Resume components — not final bullets

Populate only from validated outputs: outcome seasons; unique lineups; unique cores; comparison core/fifth rows; unexpanded possession exposure; feature coverage; modeling method; sensitivity and holdout result. Skills: Python, statistical modeling, repeatable HTTP ingestion, data validation, and SQLite auditing if used. Do not claim wins, causal impact, or outperformance without defensible evidence.

## 2026-10-05 — Verified pilot and handoff

- User steering: prioritize code structure for remaining usage. Completed a 2022–23 pilot instead of continuing the full four-season download. The larger window remains configurable and uncompleted.
- Found small overcounts in some uncapped season lineup responses. A date-filtered Denver query matched its team totals exactly; applying the same recovery to affected teams resolved all pilot reconciliation differences. The upstream cause is not established; preserve the original and repaired queries.
- Final pilot: 16,752 unique lineups; 30,766 cores; 83,760 dependent representations. All 30 teams reconcile exactly on time, both possession sides and both scoring sides. No malformed IDs quarantined.
- Prior-profile filter: 375 eligible players; 4,905 lineups retain all five profiles. Primary comparison: 430 cores, 1,018 rows, 358 lineups, 24 franchise clusters. Eligibility loss is substantial.
- Primary association per 0.1 gap unit: +0.208, 95% interval [−1.987, +2.403]. All executed complementarity variants have intervals spanning zero. Franchise-held-out contrast RMSE rises from 10.658 to 10.691 with complementarity. Conclusion: inconclusive; no observed predictive gain in the pilot.
- SQL independently reproduces comparison counts. Five local invariant tests pass, including numerical and standard-error equivalence of the within-core estimator to explicit fixed effects.
- Six figures exported as PNG/SVG. Corrected overlapping title/subtitle text after visual inspection.
- Desktop Jupyter TCP kernel startup stalled, including a retry outside the restricted sandbox. Stopped those attempts. All six notebooks instead executed successfully top-to-bottom in fresh local IPython namespaces with captured tables, text and image outputs; metadata records this method. Native Jupyter kernel execution in this host is not verified.
- Full multi-season validation, official-source reconciliation, stronger quality/defense proxies, alternative profile thresholds/aggregation and season-forward validation remain outstanding. No final resume bullets or article drafted.
