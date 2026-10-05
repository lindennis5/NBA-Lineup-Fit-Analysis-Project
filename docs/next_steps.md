# Next engineering and research steps

The verified pilot uses 2022–23 outcomes and 2021–22 profiles. The user asked to prioritize code structure over further expansion. Preserve that scope in claims.

1. Add per-run output directories keyed by season window and configuration hash; current outputs overwrite the previous analytical run. Record all thresholds, smoothing choices and source hashes in a run manifest.
2. Add mocked HTTP tests for 500-row recursion, disjoint date boundaries, interruption recovery, malformed responses and checksums. Existing tests cover seasons, lineup/core construction, complementarity, both-sided thresholds, and absorbed-WLS equivalence to explicit indicators.
3. Resume the four-season download and analysis. Reconcile every team before fitting; investigate failures instead of loosening validation gates.
4. Independently validate selected provider totals and lineup segments against official NBA box scores/PBP, including substitution boundaries and technical free throws.
5. Evaluate alternate prior quality measures, 250/1,000 prior-minute cutoffs, core aggregation and shooting shrinkage. Retain the original specification.
6. Add game/stint-level opponent and game-state controls, game-aware resampling, and season-forward validation. Do not estimate a prospective held-out core's intercept from future outcomes.

No remote GitHub repository, push, final article or resume bullet was created. CI configuration is supplied; local testing does not imply a successful remote CI run.
