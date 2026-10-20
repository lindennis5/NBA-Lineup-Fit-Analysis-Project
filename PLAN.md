# Finishing plan: NBA Lineup Fit Analysis

Approved by the user. `PY` = `.venv/bin/python`. Research question: does filling a four-player lineup's largest measurable skill deficiency improve performance beyond adding a more talented player? Current finding: a legitimate null (no reliable incremental benefit after controlling for quality and skills). It stands unless new evidence justifies revising it. Never manufacture significance.

## 0. Executor rules (every task)

1. **The null stands.** Do not change the conclusion in README, docs, site or career materials unless the revision gate passes.
2. **Revision gate.** Stop and report to the user, with no doc edits, if: the primary specification's 95% CI excludes zero (validated-season or pooled sample); the sign of a primary estimate flips; or a rerun changes any primary coefficient by more than 1e-6 from `docs/runs/7955a2391b0d`.
3. **No outcome-driven additions.** Run only the specifications in this plan. Report all, including failures and unfavourable signs.
4. **Every number in prose** comes from `docs/claims.json` (generated from outputs, T5). `tests/test_claims_trace.py` enforces it.
5. **Banned wording:** "causes", "caused", "proves", "fit doesn't matter", "chemistry is a myth". Required framing: association; prediction only of within-core contrasts; no causal claim.
6. **One commit per task** on branch `finish/final-release`. Commit messages end with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not push, open a PR, or touch the remote without the user's say-so.
7. If a command fails or a stop condition triggers, stop and report. Do not improvise a fix.

## 1. Current state (verified 2026-10-20)

**Works**
- 16 unit tests pass; `pip check` clean; `.venv` is Python 3.14.8 (docs say 3.12 on Windows).
- `docs/release_run_manifest.json` code hashes match all 13 `src/*.py`.
- README headline numbers match `docs/` outputs: effects −0.03 / −0.04, CIs [−1.63, +1.57] / [−0.91, +0.82], wild-bootstrap p 0.9585 / 0.898, forward RMSE rows, counts (1,537; 70,064; 19,795), Knicks values (creation +3.456, playmaking +1.611, gap 0.341).
- Design is sound: core fixed effects, exposure weights split across a lineup's five views, franchise-clustered CR1, wild bootstrap, forward validation; pilot reproduces exactly.

**Broken or unverified**
- `data/raw` holds only 74 files (2022–23). 2021–22 players and all of 2023–24 to 2025–26 are missing; `data/processed` is empty. The four-season result cannot be re-derived locally.
- `notebooks/01_data_feasibility.ipynb` is dirty: accidental `ModuleNotFoundError: pandas` output from a system-Python run, contradicting the audit's "no error outputs" claim. (The auto-mode classifier blocked `git checkout --` on it; it is handled in T0/T9 only with the user's explicit OK.)
- No remote CI evidence (`gh` not installed); CI covers Ubuntu/Windows, Python 3.12 only.
- 2025–26: all 30 teams have DefPoss > OffPoss (mean gap −61.7, SD 7.6), points balance exactly: systematic. 2024–25: team gaps average ~0 (SD 15.9), league points off by −56; 25 lineups have provider PlusMinus ≠ points − opponent points.
- External validation covers only 2022–23 games and points (hand-transcribed media guide). Player totals never reconciled to team totals; player IDs checked for syntax only; "balanced" is a league-wide sum that can hide offsetting errors.
- Metric: 39.3% of primary rows score exactly 0; 9.3% of cores have no deficiency; the Knicks core's largest gap is only 0.34 SD; fit correlates 0.30 with the talent proxy.
- Tests are all synthetic: none cover README claims, figures, notebooks, `release_audit` end to end, or `season_validation`.
- 45 files in `docs/` incl. stale `next_steps.md`, `medium_notes.md`, `chart_plan.md`, `validation_report.md`; 10 figures, several off-question; `season_effects` shows raw labels and does not distinguish provisional seasons; `model_effects` pools provisional seasons unlabeled. README/REPRODUCING are Windows-first.

## 2. Credibility blockers, ranked

**B1. Data re-acquisition and reproducibility.** Download all caches; verify every payload SHA-256 against `docs/raw_inventory.json` (exclude `*.meta.json`, whose timestamps differ); rerun `--release`; compare to `docs/runs/7955a2391b0d` at 1e-9. If the provider revised data, regenerate everything and apply the revision gate.

**B2. 2024–25 and 2025–26 discrepancies.**
- Independent source: Basketball-Reference `https://www.basketball-reference.com/leagues/NBA_{end_year}.html` team and opponent totals; 4 pages, 4+ s apart; save `data/external/bbref_{season}_team_totals.csv` with URL and timestamp. Fallback NBA.com `leaguedashteamstats`. If both blocked, stop and ask the user for manual CSVs.
- Per season, 30 teams: games, points, opponent points must match exactly; estimated possessions `FGA + 0.44·FTA − ORB + TOV` for team and opponents.
- Tolerance = max relative |provider − estimate| per side over all teams in 2022–23 and 2023–24 (data-calibrated).
- Diagnose 2025–26 by side (mean residual for OffPoss vs DefPoss).
- Disposition: `validated` iff points and games match exactly and every team passes tolerance on both sides; else `provisional`. Add `disposition` to `docs/season_validation_status.csv`. Apply the same test to 2023–24. Never repair provider data.
- Headline sample = all validated seasons (data-driven); pooled four-season results are secondary, labelled provisional.
- Extra sensitivity: refit excluding the top 10 teams by |OffPoss − DefPoss| in each flagged season.

**B3. Structural validation** (`docs/audit/structural_checks.json`):
- every lineup player ID resolves to a name in that season's player file (report unresolved share);
- no player on more than 3 teams in a season;
- team lineup minutes in [3,936, 4,200];
- team possessions per game in [85, 110];
- ratio of summed player points to summed team points per season (flag < 0.995);
- share of lineup exposure with all 5 prior profiles, per season;
- spot-check points, assists, blocks, minutes vs Basketball-Reference for 11 players (the 10 in `player_influence.csv` plus Jalen Brunson); points/assists/blocks must match exactly.

**B4. Reported statistics vs outputs.** `docs/claims.json` + `tests/test_claims_trace.py`: parse README, fans section, Medium outline, career materials and site; every decimal, 3+ digit count or percentage must appear in `claims.json` or a short allowlist (years, season labels). Run now against the current README (expected pass) and again at the end.

**B5. Modeling assumptions, uncertainty, selection** (`docs/audit/final_robustness.csv`):
- effects per 1 within-core SD of fit (and per 0.1 unit); fifth-player quality on the same scale for a talent-vs-fit comparison;
- equivalence margin fixed now: ±1.0 net points per 100 possessions per within-core SD of fit, 90% interval. CI inside margin → "no effect larger than 1.0 is supported"; otherwise → "inconclusive; no evidence of benefit; cannot rule out effects of 1.0";
- minimum detectable effect `(t_{.975,G−1} + 0.842) × SE` per sample;
- selection table: primary sample vs eligible vs all lineups on exposure, franchise share, skill means;
- state known limits: coach selection, no opponent/game dependence, crude proxies.

**B6. Robustness.** Keep all 17 existing specifications; add leave-one-season-out (4 fits), a large-gap subgroup (cores with gap ≥ 75th percentile of primary-sample cores), the flagged-team exclusion, and the B5 rows.

**B7. Association vs prediction vs causation.** `FINAL_AUDIT.md` carries a 3-row table: association (estimated, with uncertainty); prediction (within-core contrasts only, forward ΔRMSE with franchise bootstrap CI); causation (not claimed). Banned-wording rule applies everywhere.

## 3. Metric decision

Verdict: largest-gap closure does not adequately represent fit (credits one of five dimensions; capped, so 39.3% exact zeros; gap often trivial; divided by 5; core means cannot see a missing specialist). Brunson's zero is a symptom. **The original model stays the headline.** Add exactly three alternatives from the same lagged standardized skills. `c_k` core mean of skill k, `c_ik` core player i's skill k, `f_k` fifth player's skill k, `g_k = max(0, −c_k)`.

| ID | Name | Definition | Rationale | Sign |
|---|---|---|---|---|
| A1 | Deficiency-weighted skill supply | `Σ_k g_k·f_k / Σ_k g_k`; 0 if `Σ g = 0` | Brings skill where the core is weak, weighted by how weak; all gaps, no cap or zero mass | + |
| A2 | Skill redundancy | `Σ_k max(0,c_k)·max(0,f_k)` | Stacking skills the core already has has diminishing returns | − |
| A3 | Specialist coverage | `Σ_k max(0, f_k − max_i c_ik)` over the four core players | A lineup needs one elite specialist, not four slightly-above-average players; tests non-additivity | + |

Illustration (`docs/knicks_example.csv`): original score = 0 for all four Knicks candidates; A1 = Brunson +0.84, McBride −0.53, Payne −0.16, Wright −0.12; A2 for Brunson = 0.34. A3 needs individual core skills; computed in tests from hand-checked fixtures.

Procedure: commit `docs/metric_preregistration.md` **before** running any alternative. Same sample, controls (fifth quality + 5 skills), core FE, weights and franchise clustering as the primary model. Run on the validated-season sample (primary for alternatives) and pooled. Reuse `inference()` and `score_contrasts()` on a copy with the alternative copied into the `complementarity` column; never overwrite the original column. Holm-adjust the three wild-bootstrap p-values. "Supported" only if all hold: (1) Holm p < 0.05 on the validated sample; (2) pooled estimate has same sign and CI excluding 0; (3) forward paired ΔRMSE CI entirely below 0. Otherwise "not supported" and the null stands. If any alternative is supported, the revision gate triggers: stop and ask the user.

## 4. Deliverables

- **Audit:** `docs/FINAL_AUDIT.md` (B1–B7 results, season dispositions, metric verdict, claims-ladder table, what remains unverified). Supersedes `validation_report.md` and `next_steps.md` (delete).
- **README.md:** Question → Findings (null table from `claims.json`) → Knicks/Brunson example → Key figures (3) → Methodology (brief) → Implications → Limitations → Reproduction (macOS/Linux first, then Windows) → links to technical docs. Includes a short "What Does This Actually Mean for NBA Fans?" subsection linking to `docs/fans.md`.
- **Figures** (`src/final_figures.py` replaces `src/release_figures.py` and figure code in `src/analysis.py`; PNG + SVG):

| Existing | Decision |
|---|---|
| possession_distribution | Drop |
| threshold_tradeoff | Drop (becomes a table) |
| skill_correlation | Drop |
| performance_distribution | Drop |
| core_example | Drop (replaced by Knicks) |
| model_effects | Improve → `robustness_effects` (forest of all 17 specs, readable labels, hollow markers = provisional) |
| season_effects | Improve (readable labels, hollow = provisional, per-0.1 and per-SD axes) |
| talent_complementarity | Improve (two panels: original score and A1 vs talent; annotate 39.3% zero mass and correlations) |
| forward_prediction | Improve (ΔRMSE dots with intervals per season and overall) |
| knicks_example | Improve (all four candidates, weakest dimension marked, original and A1 scores annotated, provisional label if applicable) |

  New: `core_deficiencies` (largest-gap distribution and weakest skill) and `metric_comparison` (original vs A1–A3 effects with CIs, per SD). Final set of 7: season_effects, robustness_effects, metric_comparison, talent_complementarity, forward_prediction, knicks_example, core_deficiencies. `git rm` the dropped files.
- **"What Does This Actually Mean for NBA Fans?"** in `docs/fans.md` (700–900 words, plain language) and repeated on the site. Order: why teams weigh fit; how a four-player core has gaps; how fifth players are compared; what the findings suggest; why the null does not disprove chemistry (one narrow metric, noisy data, coach selection, crude proxies); what fans, coaches and front offices can conclude; what remains unanswered. Knicks/Brunson runs through all, with the author-is-a-Knicks-fan disclosure.
- **Medium outline:** `docs/medium_article_outline.md` (replaces `medium_notes.md`); ~1,500 words total across: best player or best fit; why complementarity might matter; how it was tested; results; real lineup example (Knicks); meaning for fans; limitations; takeaway. 2–3 bullets and an assigned figure per section.
- **Site:** `site/index.html` + `site/assets/style.css`, no JavaScript, no dashboard. `scripts/build_site.py` copies figures into `site/assets/`. Deployed by `.github/workflows/pages.yml` (upload `site/` as Pages artifact; user must set Settings → Pages → Source: GitHub Actions). Local: `PY -m http.server 8000 --directory site`; `curl -sI http://localhost:8000/ | head -1` → `200 OK`; `PY scripts/check_site.py` (internal links and images resolve, alt text present, no external scripts, numbers trace to `claims.json`).
- **Career materials:** `docs/career_materials.md` — 4 resume bullets (pipeline and reconciliation; the null with its CI; validation and audit; metric critique), a LinkedIn paragraph, a 60–90 s interview answer (question, method, null, next steps), a 10-question technical Q&A (fixed effects; franchise clustering; what "null" means with the CI; why not causal; effect of the data discrepancy; why alternatives were pre-registered; what the Brunson zero shows; multiple testing; weighting; what I'd change). Numbers only from `claims.json`; no employer or role claims.
- **Housekeeping:** update `methodology_notes.md` (metric section), `REPRODUCING.md`, `PUBLISHING.md`, `research_report.md`; add a final `research_log.md` entry; delete `next_steps.md`, `medium_notes.md`, `chart_plan.md`, `validation_report.md`; keep `pilot_readme.md`, `audit_findings.md`, `data_feasibility.md`, `docs/runs/*`.

## 5. Ordered task list

| # | Task | Files | Proof command | Expected evidence |
|---|---|---|---|---|
| T0 | Save plan, branch `finish/final-release`; dirty notebook 01 restored only with explicit user OK | `PLAN.md` | `git status --short`; `PY -m unittest discover -s tests` | Only `PLAN.md` (and notebook 01 if not yet OK'd) changed; 16 tests OK |
| T1 | Re-acquire data, verify hashes (B1) | `scripts/verify_raw_inventory.py`, `data/raw/*` | `PY run.py --download-only --workers 2 && PY scripts/verify_raw_inventory.py` | 0 missing, 0 mismatched payloads (a mismatch → regenerate + revision gate); `download_failures.json` is `[]` |
| T2 | Reproduce outputs (B1) | `scripts/compare_outputs.py` | `PY run.py --release && PY scripts/compare_outputs.py docs/runs/7955a2391b0d docs` | All values within 1e-9, else revision gate |
| T3 | Independent season validation (B2) | `src/external_validation.py`, `data/external/bbref_*_team_totals.csv`, `docs/audit/external_team_check.csv`, `docs/season_validation_status.csv`, `tests/test_external_validation.py` | `PY -m src.external_validation && PY -m unittest tests.test_external_validation` | 120-row team-season table; calibrated tolerance printed; disposition per season; 2025–26 side diagnosis |
| T4 | Structural checks (B3) | `src/structural_checks.py`, `docs/audit/structural_checks.json`, `docs/audit/player_spotcheck.csv`, `tests/test_structural_checks.py` | `PY -m src.structural_checks` | Pass/fail per check and season; spot-check matches or discrepancies listed |
| T5 | Claims registry and trace test (B4) | `src/claims.py`, `docs/claims.json`, `tests/test_claims_trace.py` | `PY -m src.claims && PY -m unittest tests.test_claims_trace` | Passes on current README; any failure recorded as a finding |
| T6 | Final robustness (B5, B6) | `src/final_robustness.py`, `docs/audit/final_robustness.csv`, `docs/audit/selection_table.csv`, `tests/test_final_robustness.py` | `PY -m src.final_robustness` | Per-SD effects, equivalence verdict, MDE, leave-one-season-out, large-gap subgroup, flagged-team exclusion, talent-vs-fit row |
| T7 | Metrics: commit pre-registration first, then run | `docs/metric_preregistration.md`, `src/alternative_metrics.py`, `src/metric_comparison.py`, `tests/test_alternative_metrics.py`, `docs/audit/metric_comparison.csv`, `docs/audit/metric_diagnostics.json` | `git log --oneline -- docs/metric_preregistration.md` (older than the results file); `PY -m src.metric_comparison` | A1–A3 Holm p, forward ΔRMSE CIs, supported/not-supported verdicts; any "supported" → stop and ask |
| T8 | Figures | `src/final_figures.py`, `src/analysis.py`, `src/release_figures.py`, `run.py`, `src/notebooks.py`, dropped figure files | `PY -m src.final_figures && ls figures/*.png \| wc -l` | 7 PNG + 7 SVG; each PNG viewed: no overlap, readable labels, provisional marked |
| T9 | Notebooks | `notebooks/*.ipynb`, `scripts/check_notebooks.py` | `PY run.py --release --notebooks && PY scripts/check_notebooks.py` | 7 notebooks, 0 error outputs, no references to dropped figures (this also overwrites notebook 01) |
| T10 | Documents | all deliverables in section 4 | `PY -m unittest tests.test_claims_trace`; `grep -rniE "causes\|proves"` over deliverables | Passes; zero untraceable numbers; zero banned words |
| T11 | Site | `site/*`, `scripts/build_site.py`, `scripts/check_site.py`, `.github/workflows/pages.yml` | `PY scripts/build_site.py && PY scripts/check_site.py`; local server + `curl` | 0 broken links, 0 external scripts, 0 untraceable numbers; `200 OK` |
| T12 | CI | `.github/workflows/tests.yml` | `PY -c "import yaml;yaml.safe_load(open('.github/workflows/tests.yml'))"` | Parses; adds macOS, claims test and site check; remote status stays "not run" until the user pushes |
| T13 | Final gate | `docs/test_results.txt`, final snapshot via `src/snapshots.py` | `PY -m unittest discover -s tests -v 2>&1 \| tee docs/test_results.txt && git status --short` | All tests OK (count > 16, recorded), `pip check` clean, tree clean, summary of what remains unverified |

## 6. Out of scope

A causal study or new causal design; a dashboard or app; data sources beyond T3's validation; tracking, defensive-impact or gravity data; rebuilding the model; more than 3 alternative metrics; repairing provider data; playoff data; publishing the article; pushing, merging or opening a PR; relicensing raw data; any lineup-advice or recommender tool.

## 7. Risks and open questions

1. Notebook 01: discard the uncommitted change (an accidental error output; notebooks get regenerated anyway). Needs explicit user OK because the auto-mode classifier blocked `git checkout --`.
2. Basketball-Reference terms limit automated access; plan is 4 slow requests. If blocked, user supplies the totals by hand (or NBA.com fallback).
3. Redownload may change the data; if the headline moves, the revision gate stops everything.
4. The 2025–26 imbalance may stay unexplained; then it stays `provisional` and the headline rests on validated seasons only.
5. Equivalence margin ±1.0 per within-core SD is a fixed choice; the user may want a different anchor.
6. Pages needs the user to set the source to GitHub Actions (alternative: site in `docs/`, which clutters the data folder).
7. Python documented as 3.12 (CI) plus 3.14.8 (this Mac).
8. Career materials use no employer or title claims; the user will edit tone.
9. Alternative metrics are exploratory (same data); even a pass is a hypothesis needing new-season confirmation; stop for the user's decision before touching the narrative.
10. Download time is unknown (4 seasons × 30 teams, with delays).
