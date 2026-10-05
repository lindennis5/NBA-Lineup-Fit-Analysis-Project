# Validation report — pilot, 2026-10-05

## Assessment: share with caveats as a one-season pilot

Verified: 30 teams / 1,230 games; 16,752 unique canonical lineups; no malformed membership quarantined; exactly 83,760 core/fifth representations. Every team's seconds, possessions and points on both sides reconcile exactly after date-filtered recovery.

There are 1,089 undefined net ratings, excluded explicitly. Lagged features yield 375 eligible player profiles and 4,905 complete-profile lineups. The primary comparison sample has 1,018 rows, 430 cores, 358 lineups and 24 franchises. Independent SQL counts match Python. Synthetic tests reproduce explicit fixed-effects coefficients and clustered standard errors.

Primary effect per 0.1 gap unit: +0.2078, interval [−1.9873, +2.4029]. All tested complementarity variants have intervals spanning zero. This is inconclusive, not proof that fit is irrelevant.

Material limitations: incomplete external NBA validation; imperfect talent/defense proxies; one season and selection bias; substantial feature exclusions; within-team clustering does not capture shared-game cross-team dependence. Holdout scoring evaluates demeaned contrasts, not prospective absolute ratings.

Six static figures accompany the pipeline. Initial title/subtitle overlap was caught during visual inspection and corrected in the plotting code. See the research log for final notebook execution status. No final article or resume finding is warranted.
