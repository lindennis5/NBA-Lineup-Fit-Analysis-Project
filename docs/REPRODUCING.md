# Reproducing the research

Use Python 3.12 from the repository root. The release was executed on Windows. CI is configured for Windows and Linux; a local Windows pass does not imply that remote CI has run.

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-lock.txt
.venv/Scripts/python -m pip check
.venv/Scripts/python -m unittest discover -s tests -v
.venv/Scripts/python -m compileall -q src run.py
```

On macOS/Linux use `.venv/bin/python`. `requirements.txt` pins direct dependencies; the lock file records the tested transitive versions, with the Windows-only terminal dependency guarded by a platform marker.

## Full release workflow

```powershell
.venv/Scripts/python run.py --download --workers 2 --release --notebooks
```

This requests regular seasons 2022–23 through 2025–26 and the necessary lagged player profiles. Requests are cached. A capped lineup request is recursively split into disjoint date intervals. Download failures are listed in `docs/download_failures.json`; the command fails instead of treating missing teams as complete. Retry the same command to resume. Public API availability is outside this repository's control. Two workers and per-request delays are courtesy settings, not a verified provider rate allowance.

From existing caches:

```powershell
.venv/Scripts/python run.py --release --notebooks
```

The main pipeline validates data, builds profiles and observations, estimates primary models, evaluates held-out franchises, runs an independent SQL count check, and creates figures. `--release` adds season-specific estimates, alternative specifications, small-cluster inference, season-forward scoring, official pilot reconciliation, additional figures and compact result snapshots. Notebook execution uses fresh local IPython namespaces and captures rich output; it does not require a TCP kernel broker.

## Original pilot

```powershell
.venv/Scripts/python run.py --seasons 2022-23 --release --notebooks
```

Original outputs are preserved in `docs/pilot_baseline/`. `docs/pilot_reproduction.csv` compares primary coefficients, standard errors and intervals at 25, 50 and 100 possessions against the original pilot. No fake observations are used; synthetic data appear only in unit tests.

## Outputs and provenance

- `data/raw/`: original HTTP payloads, metadata and recombined lineup caches; ignored by Git.
- `data/processed/`: latest analysis tables and SQLite database; ignored by Git.
- `docs/data_manifest.json` and `docs/raw_inventory.json`: URLs, timestamps and checksums.
- `docs/release_run_manifest.json`: analyzed seasons, settings, seed and code hashes.
- `docs/runs/`: compact result snapshots keyed by configuration, code and raw inventory.
- `docs/*coefficients.csv`, validation tables and JSON diagnostics: traceable research results.
- `figures/` and `notebooks/`: viewable analysis, without AI branding or signatures.

The latest working files are regenerated on each run. Snapshot directories and the pilot baseline preserve prior small outputs. README and narrative reports describe the reviewed release; if new source revisions change the results, review those narratives against the new tables before publishing. Bulk data are excluded from Git; rerunning from the API retrieves its current historical records, which may differ from the preserved local snapshot.
