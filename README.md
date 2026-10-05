## NBA Lineup Fit
### Research Question

**Does filling a four-player NBA lineup's largest skill deficiency improve lineup performance beyond simply adding the best available player?**

A reproducible observational study separating a fifth player's prior production from their contribution to a particular core. A null or inconclusive result is a valid outcome.

## Current answer: inconclusive pilot

**The 2022–23 pilot does not establish a benefit from filling the largest measured skill gap.** The primary estimate is **+0.21 net points per 100 possessions per 0.1 standardized skill-unit gap closed**, with a **95% interval of −1.99 to +2.40**. Point estimates change sign across possession thresholds.

Held-out franchise **within-core contrast** RMSE is 10.658 with quality and skill controls, versus 10.691 with complementarity added. That is no observed predictive improvement here. This exercise scores demeaned contrasts, not prospective absolute ratings of unseen lineups.

These are preliminary one-season results, not evidence that basketball fit never matters. Talent measurement, public skill proxies, sparse samples and lineup selection limit interpretation.

## Status and scope

Following the request to prioritize code structure, this session completes a tested pilot and a configurable multi-season pipeline. The planned outcome window is **2022–23 through 2025–26**. Only **2022–23** has been fully downloaded, reconciled and modeled; **2021–22** supplies its lagged profiles. Separate 2024–25 source probes and 2025–26 team-coverage probes are not analyzed seasons. Full 2023–24 and 2024–25 coverage remains unverified.

| Pilot quantity | Count |
|---|---:|
| Retrieved teams / games | 30 / 1,230 |
| Unique season-team five-player lineups | 16,752 |
| Distinct season-team four-player cores | 30,766 |
| Expanded core/fifth representations | 83,760 |
| Mean-side possessions, counted once per lineup | 244,628 |
| Eligible prior-season player profiles | 375 |
| Lineups with all five prior profiles | 4,905 |
| Primary comparison lineups / cores / rows | 358 / 430 / 1,018 |
| Franchises contributing to the primary model | 24 |

Primary eligibility requires **50 offensive and 50 defensive possessions**, all five prior profiles (500+ prior minutes each), and two eligible fifth players per core. There are 1,089 retrieved lineups with undefined net rating because at least one possession denominator is zero; they are excluded from comparisons.

## Data

Use the [PBP Stats API](https://api.pbpstats.com/docs) consistently for lineup, player and team totals, with NBA player/team identifiers. This is a derived play-by-play source, not the official NBA Stats API. See the [source comparison and recommendation](docs/data_feasibility.md).

The pipeline found a 500-row response cap and recovered omitted lineups through team queries and recursive disjoint date partitions. Several uncapped totals also disagreed with team totals; date-filtered queries resolved those differences. Final pilot totals reconcile **exactly** to provider team totals for seconds, offensive/defensive possessions, and points on both sides. Independent NBA validation remains outstanding.

Bulk raw/processed data are ignored by Git. The [manifest](docs/data_manifest.json) preserves request URLs, timestamps and checksums. Public access does not establish redistribution rights.

## Analytical definitions

One row is **season + team + sorted four-player core + fifth player**. Every lineup produces five dependent representations. Net rating is `100 × points/off_poss − 100 × opponent_points/def_poss`. Count exposure at the original lineup level.

All predictors use the previous season, normalized among players with 500+ minutes:

| Skill | Initial proxy |
|---|---|
| Spacing | 3PA per 100 offensive possessions plus smoothed 3P accuracy |
| Playmaking | Assists per 100 offensive possessions |
| Creation | Unassisted field-goal points per 100 offensive possessions |
| Rebounding | Offensive and defensive rebounds per 100 corresponding possessions |
| Interior activity | Blocks per 100 defensive possessions; **not comprehensive defense** |

**Talent:** prior Game Score per 36 minutes, season-standardized. This is a reproducible production proxy, not a complete impact measure; no current lineup rating enters it.

**Core profile:** mean of four player skill z-scores. **Deficiency:** the largest below-zero core skill gap. An entirely above-average core has no measured deficiency.

**Complementarity:** if `c` is the weakest core skill and `s` the corresponding fifth-player skill, `fill = min(max(0, −c), max(0, (s−c)/5))`. This measures capped improvement toward average in the five-player mean. It is an initial specification, not an objective universal fit score.

Exact formulas, smoothing, normalization, ties and alternatives are in [methodology notes](docs/methodology_notes.md).

## Model and sensitivity

Possession-weighted linear regression with **core fixed effects**, prior fifth-player quality and all five skill main effects, plus complementarity. Divide exposure among retained representations of each lineup. Cluster uncertainty by franchise, with an absorbed-effects correction and t intervals using the number of retained clubs.

| Possessions per side | Comparison cores | Core/fifth rows | Effect per 0.1 gap unit | 95% interval |
|---|---:|---:|---:|---|
| 25 | 978 | 2,558 | −0.63 | [−2.27, +1.00] |
| 50 — primary | 430 | 1,018 | +0.21 | [−1.99, +2.40] |
| 100 | 143 | 320 | −0.68 | [−3.44, +2.09] |

Executed alternatives include all-gap closure, an uncapped interaction, excluding interior activity from the gap, unweighted estimation, and omitting fifth-skill main effects. None provides clear positive evidence in this pilot. Retain every specification in [the coefficient table](docs/model_coefficients.csv).

![Adjusted association and uncertainty](figures/model_effects.png)

## Basketball interpretation

The highest-exposure eligible core, chosen without inspecting outcomes, is Atlanta's Trae Young, Dejounte Murray, De'Andre Hunter and John Collins. Its lagged profile identifies interior activity as its weakest axis. Capela and Okongwu each fully close that measured gap; Bogdanovic does not. The capped score cannot distinguish the centers once the gap is filled. This illustrates both the measure and its limits; it does not demonstrate a causal substitution benefit.

## Project structure

```text
nba-lineup-fit/
  README.md
  requirements.txt             # pinned direct packages
  requirements-lock.txt        # tested Windows environment snapshot
  run.py                       # single workflow entry point
  .github/workflows/tests.yml  # offline invariant tests
  data/raw/                    # cached JSON and metadata; ignored
  data/processed/              # analytical tables and SQLite; ignored
  src/
    data_pipeline.py           # caching, requests and date partitions
    lineups.py                 # IDs, reconciliation, cores, thresholds
    features.py                # lagged skills and complementarity
    models.py                  # within-core WLS and holdout validation
    analysis.py                # offline build, EDA, SQL audit, figures
    notebooks.py               # create and execute companion notebooks
  notebooks/                   # six focused analytical notebooks
  sql/analysis_queries.sql
  tests/test_research_invariants.py
  figures/                     # six figures in PNG and SVG
  docs/                        # methods, source evidence, logs and results
```

## Reproduction

Python **3.12**, tested on Windows. Run from the repository root; no source credentials required.

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m unittest discover -s tests -v

# Retrieve and reproduce the pilot:
.venv/Scripts/python run.py --seasons 2022-23 --download --notebooks

# Recompute offline from existing caches:
.venv/Scripts/python run.py --seasons 2022-23 --notebooks

# Resume the intended four-season build:
.venv/Scripts/python run.py --download --notebooks
```

On macOS/Linux use `.venv/bin/python`. Use `--workers 1` for serial requests. Checked caches are reused. Explicit source refresh: `python -m src.data_pipeline --seasons 2022-23 --refresh`. Preserve old manifests before refreshing; upstream corrections can change results. The Windows-specific full lockfile is an environment record; `requirements.txt` is the cross-platform installation file.

Outputs represent the **latest run** and overwrite prior analytical tables. Preserve a snapshot before comparing windows. Interrupted downloads resume from caches. CI tests mathematical invariants without live downloads; remote GitHub Actions has not been run in this session.

All six notebooks executed sequentially in fresh local IPython namespaces, capturing rich outputs. Their metadata records this method. Native Jupyter TCP kernel startup stalled on this desktop; ordinary Jupyter execution remains unverified here. The notebooks remain standard `.ipynb` files.

## Limitations and next steps

- One outcome season, heavy prior-profile exclusions, and only 24 primary franchise clusters.
- Box-count proxies miss spacing gravity, passing opportunities, shot difficulty and much of defense. Core averages and smoothing require alternatives.
- Prior Game Score leaves residual talent confounding. The full available-player choice set is unobserved.
- Opponent strength, garbage time, injuries and coaching selection are not directly controlled.
- Franchise clustering does not capture all shared-game dependence across opponents.
- Internal reconciliation does not replace official-data/game-level checks.
- Holdout contrast scoring is not prospective absolute-rating prediction.

Before resume-ready conclusions: finish the four-season run, independently validate games/totals, strengthen talent and defense measures, test feature thresholds and aggregation, and add season-forward validation with game-aware uncertainty. See [next steps](docs/next_steps.md), [research log](docs/research_log.md), and [future article notes](docs/medium_notes.md). No final article, fabricated resume claim, remote repository or publication was created.
