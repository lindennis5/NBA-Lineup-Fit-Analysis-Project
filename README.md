# NBA Lineup Fit Analysis

**Does filling a four-player lineup's biggest skill gap improve performance beyond simply adding the best available player?**

## Conclusion

> **No evidence that it does.** Across four NBA seasons (2022–23 to 2025–26), a fifth player who closes the core's largest measured skill gap shows no reliable benefit beyond that player's prior production and skills. **Don't use this gap-closure score as a lineup-selection rule yet.**

- **The effect is essentially zero, with wide uncertainty.** It is −0.03 net points per 100 possessions in the two clean-data seasons and −0.04 across all four. Both intervals include positive and negative effects.
- **Fit doesn't improve forward predictions.** Trained on earlier seasons and scored on the next one, the model's prediction error is essentially unchanged after adding fit.
- **The conclusion is narrow.** It concerns one definition of fit. It does **not** show that fit is unimportant, that talent always beats fit, or that adding any particular player causes improvement.

| Sample | Effect per 0.1 gap closed | 95% interval | Lineups |
|---|---:|---:|---:|
| **2022–23 + 2023–24 (balanced source data, preferred)** | **−0.03** | **[−1.63, +1.57]** | 808 |
| All four seasons (provisional) | −0.04 | [−0.91, +0.82] | 1,537 |

| Forward test: held-out season | Talent + skills RMSE | With fit RMSE | Change |
|---|---:|---:|---:|
| 2023–24 | 10.7182 | 10.7206 | +0.0024 |
| 2024–25 (provisional) | 10.5635 | 10.5635 | +0.0001 |
| 2025–26 (provisional) | 11.4841 | 11.4840 | −0.0001 |

A positive change means the model is worse with fit. Restricted wild franchise bootstrap p-values are 0.96 for the balanced subset and 0.90 for all four seasons.

![Season effects](figures/season_effects.png)

**Full write-up:** [docs/research_report.md](docs/research_report.md)

---

## Example: the Knicks

Take my favourite team, the New York Knicks. In 2024–25, one of their four-player cores was **Karl-Anthony Towns, OG Anunoby, Josh Hart and Mikal Bridges**. Based on the previous season's profiles, that core's largest measured gap is **blocks**.

**Jalen Brunson gets a fit score of zero.** His block rate can't close that gap, and his elite creation (+3.46 SD) and playmaking (+1.61 SD) earn no credit in this narrow measure. Miles McBride, Cameron Payne and Delon Wright also score zero, so the metric can't tell any of them apart.

A zero doesn't mean Brunson is a poor fit. It shows the metric asks a much narrower question than a coach does. This core was chosen because it had the most eligible Knicks exposure, not because it produced a preferred result.

![Knicks profiles](figures/knicks_example.png)

---

## Data caution

**Two of the four seasons are provisional.** In the provider's league-wide totals, points scored and allowed and offensive and defensive possessions should balance. They don't in 2024–25 or 2025–26, and the cause is unresolved.

| Season | Points scored − allowed | Off. − def. possessions | Status |
|---|---:|---:|---|
| 2022–23 | 0 | 0 | Balanced; official scoring and games matched |
| 2023–24 | 0 | 0 | Balanced; external validation incomplete |
| 2024–25 | −56 | −2 | Provisional |
| 2025–26 | 0 | −1,850 | Provisional |

The two balanced seasons lead to the same practical conclusion. See [season validation status](docs/season_validation_status.csv).

---

## Method

- **Comparison:** different fifth players observed alongside the **same season-team four-player core**, using core fixed effects.
- **Fit score:** how much the fifth player closes the core's single largest below-average skill gap, capped at league average.
- **Skills (prior season):** spacing, playmaking, creation, rebounding and blocks. Blocks are an interior-activity proxy, not overall defense.
- **Controls:** fifth-player prior Game Score per 36, all five skill main effects, exposure weighting shared across a lineup's representations, and franchise-clustered uncertainty.
- **Primary sample:** at least 50 possessions per side, prior profiles for all five players with at least 500 minutes each, and an eligible alternative fifth player for the same core.

| Scope | Count |
|---|---:|
| Seasons / teams / games per season | 4 / 30 / 1,230 |
| Unique season-team lineups | 70,064 |
| Lineups with all prior profiles | 19,795 |
| Primary lineups / cores / franchises | 1,537 / 1,811 / 30 |

**Limits:** observed lineups were chosen by coaches, so this can't establish causal substitution effects. The prediction tests score differences within a core, not absolute ratings for unseen lineups.

---

## Reproduce

Tested with Python 3.12 on Windows. On macOS/Linux, use `.venv/bin/python`.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-lock.txt
.venv/Scripts/python -m unittest discover -s tests -v
.venv/Scripts/python run.py --download --workers 2 --release --notebooks
```

Omit `--download` to use the preserved local caches. Bulk raw and processed data are excluded from Git. Source URLs, timestamps, checksums and code hashes are kept, though future provider revisions may change retrieved records.

## Further reading

- [Research report and full conclusion](docs/research_report.md)
- [Methodology](docs/methodology_notes.md)
- [Audit findings and fixes](docs/audit_findings.md)
- [Validation status](docs/validation_report.md)
- [Reproduction instructions](docs/REPRODUCING.md)
- [Original 2022–23 pilot, preserved](docs/pilot_readme.md)
- [Publication steps](docs/PUBLISHING.md)

Seven executed notebooks are in `notebooks/`, analysis code in `src/`, invariant tests in `tests/`, and machine-readable results in `docs/`. The pilot baseline is in `docs/pilot_baseline/`, and result snapshots are in `docs/runs/`.
