# NBA Lineup Fit Analysis Project

### Does the fifth player fill the gap?

**Does filling a four-player NBA lineup’s largest skill deficiency improve lineup performance beyond simply adding the best available player?**

This project compares observed fifth players alongside the same four-player core, using prior-season skill and production measures. A null or inconclusive result is a valid research outcome.

## TL;DR

Filling a lineup's biggest measured weakness sounds useful, but this project has not shown that this particular fit score improves predictions beyond the fifth player's prior production and skills. There is no supported reason to use it as a lineup-selection rule yet. That does not establish that basketball fit is unimportant.

Take an example from my favorite team, the New York Knicks. In 2024–25, one of their four-player cores consisted of Karl-Anthony Towns, OG Anunoby, Josh Hart and Mikal Bridges. Using the previous season's player profiles, the model identifies blocks as their largest measured gap. Jalen Brunson receives a gap-closure score of zero because his block rate does not improve that dimension. His strong creation and playmaking scores do not earn credit in this narrow fit measure. A zero score therefore does not mean Brunson adds no value or is a poor fit. It means the metric asks a much narrower question than a coach does. This core was selected for having the most eligible Knicks exposure, not for producing a preferred result; its 2024–25 outcome data remain provisional.

The main caution is data quality: two of the four seasons have unresolved provider counter imbalances. The earlier two seasons have balanced counters and lead to the same practical conclusion, but still leave substantial uncertainty about the size of any association.

## Current result

The balanced-counter 2022–23 and 2023–24 subset estimates **−0.03 net points per 100 possessions per 0.1 gap unit**, with a **95% interval of −1.63 to +1.57**. The provisional four-season estimate is **−0.04 [−0.91, +0.82]**. Neither establishes a positive association. Forward prediction errors are essentially unchanged after adding fit.

Read the [detailed conclusion and research report](docs/research_report.md) for the plain-language explanation, Knicks example, exact prediction results and limitations.

## Scope and data status

All four regular seasons, 2022–23 through 2025–26, were retrieved and modeled: 70,064 unique lineups, with 1,537 lineups in the primary comparison. Each season contains 30 teams and 1,230 games. Prior profiles require 500 minutes; primary lineups require 50 possessions on each side and an eligible alternative fifth player for the same core.

**The four-season results are provisional.** Provider league counters do not balance in 2024–25 or 2025–26. Extraction reconciles to provider totals, but this does not resolve upstream issues. The earlier-season subset is reported separately. Independent official scoring and games reconciliation passes for 2022–23 only. See [season status](docs/season_validation_status.csv).

## Method

The fit score measures how much the fifth player closes the core's single largest below-average skill gap, capped at league average. Skills cover spacing, playmaking, creation, rebounding and blocks. Blocks are an interior-activity proxy, not overall defense. The model includes season-team-core fixed effects, fifth-player prior Game Score per 36, skill controls, exposure weighting and franchise-clustered uncertainty. Lineup exposure is shared across retained core/fifth representations.

Observed coach-selected lineups cannot establish causal substitution effects. Prediction tests assess within-core contrasts, not absolute ratings for unseen lineups.

![Season effects](figures/season_effects.png)

## Reproduce and inspect

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-lock.txt
.venv/Scripts/python -m unittest discover -s tests -v
.venv/Scripts/python run.py --download --workers 2 --release --notebooks
```

Omit `--download` to use the preserved local caches. Bulk raw and processed data are excluded from Git. Source URLs, timestamps, checksums and code hashes are retained; future provider revisions may change retrieved records.

- [Reproduction instructions](docs/REPRODUCING.md)
- [Research report and conclusion](docs/research_report.md)
- [Methodology](docs/methodology_notes.md)
- [Audit findings and fixes](docs/audit_findings.md)
- [Validation status](docs/validation_report.md)
- [Original pilot, preserved](docs/pilot_readme.md)
- [Publication steps](docs/PUBLISHING.md)

Seven executed notebooks are in `notebooks/`; analysis code is in `src/`, invariant tests in `tests/`, and machine-readable results in `docs/`. The original pilot is preserved in `docs/pilot_baseline/` and result snapshots in `docs/runs/`.
