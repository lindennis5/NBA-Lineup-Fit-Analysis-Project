# Reproducing the research

Supported: Python 3.12 (CI on Ubuntu, Windows, macOS) and Python 3.14.8 (macOS, local). Run everything from the repository root.

## Install and test (macOS / Linux)

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q src scripts run.py
```

Windows: replace `.venv/bin/python` with `.venv/Scripts/python`. `requirements.txt` pins direct dependencies; `requirements-lock.txt` records the tested transitive versions. If Python on macOS reports `CERTIFICATE_VERIFY_FAILED`, set `SSL_CERT_FILE=/etc/ssl/cert.pem`.

## Run the pipeline

```bash
.venv/bin/python run.py --download --workers 2 --release --notebooks
```

This requests regular seasons 2022–23 through 2025–26 plus the 2021–22 player history, caches every response under `data/raw/` (ignored by Git), and verifies checksums. A capped lineup request is split recursively into disjoint date intervals. Failures are listed in `docs/download_failures.json`; the command fails rather than treat a missing team as complete. Rerun the same command to resume. The provider can be slow or return HTTP 502 at times; retries reuse the cache. Two workers and one-second pauses are courtesy settings, not a verified rate allowance.

From existing caches: `.venv/bin/python run.py --release --notebooks`.

## Final audit steps (run after `run.py --release`)

```bash
.venv/bin/python scripts/verify_raw_inventory.py          # raw payload checksums vs docs/raw_inventory.json
.venv/bin/python -m src.external_validation               # Basketball-Reference team totals (data/external/), season dispositions
.venv/bin/python -m src.structural_checks                 # IDs, lineup composition, possessions, coverage, player spot-check
.venv/bin/python -m src.final_robustness                  # scaled effects, equivalence, subgroup, exclusions, selection
.venv/bin/python -m src.metric_comparison                 # three pre-registered alternatives (docs/metric_preregistration.md)
.venv/bin/python -m src.final_figures                     # the seven release figures
.venv/bin/python -m src.claims                            # docs/claims.json from outputs
.venv/bin/python -m unittest tests.test_claims_trace      # every quoted number traces to an output
.venv/bin/python scripts/build_site.py && .venv/bin/python scripts/check_site.py
.venv/bin/python scripts/check_links.py README.md docs/fans.md docs/medium_article_outline.md
.venv/bin/python scripts/check_notebooks.py
```

Compare regenerated tables with the frozen snapshot: `.venv/bin/python scripts/compare_outputs.py docs/runs/7955a2391b0d docs`.

## Original pilot

```bash
.venv/bin/python run.py --seasons 2022-23 --release --notebooks
```

Original outputs are preserved in `docs/pilot_baseline/`; `docs/pilot_reproduction.csv` compares coefficients, standard errors and intervals with the pilot.

## Outputs and provenance

- `data/raw/`, `data/processed/`: caches and latest tables (ignored by Git). `data/external/`: small committed Basketball-Reference team and player totals used only for validation.
- `docs/data_manifest.json`, `docs/raw_inventory.json`, `docs/release_run_manifest.json`: URLs, checksums, seed and code hashes.
- `docs/audit/`: final-audit outputs. `docs/claims.json`: the numbers prose may quote.
- `docs/runs/`: content-keyed result snapshots.

Source revisions can change retrieved records. If new results differ, review every narrative number against the new tables before publishing; the claims test enforces this.
