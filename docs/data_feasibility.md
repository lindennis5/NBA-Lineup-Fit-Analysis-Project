# Data feasibility and source recommendation

Investigation date: 2026-10-05. This document separates documentation claims from access tests. Actual query URLs, timestamps, and SHA-256 hashes are in `data_manifest.json`; endpoint comparison results are in `access_probes.json`.

**Handoff scope:** after the user's instruction to prioritize code structure, only 2022–23 was fully retrieved and analyzed, with 2021–22 profiles. Four seasons remain the intended window, not a completed dataset. Separate 2024–25 and 2025–26 probes establish limited access only.

## Recommendation

Use **PBP Stats totals** for the initial study, with NBA identifiers and a single provider's possession convention throughout. Retrieve regular-season team and player totals, and five-player lineups **by team**. Recursively split capped lineup requests into disjoint date intervals, sum event counts, and reconcile against season team totals. Do not silently combine NBA ratings with PBP Stats possession counts.

Retain the official NBA Stats service as the preferred independent benchmark and a future alternate ingestion path. Its tested lineup request timed out after 25 seconds in this environment; that is an access result, not proof the service is unavailable generally. PBP Stats returned parseable data here. Successful access alone does not certify accuracy or redistribution rights.

## Candidate comparison

| Source | Data, granularity, and historical coverage | IDs | Access and reproducibility | Reliability and GitHub suitability |
|---|---|---|---|---|
| [NBA Stats](https://www.nba.com/stats/lineups/advanced), accessed through documented community [nba_api endpoint definitions](https://github.com/swar/nba_api/blob/master/docs/nba_api/stats/endpoints/leaguedashlineups.md) | Player statistics; five-man season/team lineups with base/advanced measures; finer date filters. Coverage varies by endpoint; this session did not establish the earliest complete lineup season. Recent four-season window is the intended test. | Native NBA player/team IDs and explicit season query. | HTTP JSON rather than HTML scraping. No stable public service-level guarantee or numeric rate budget verified. A correct query can time out. Pin client versions and cache responses. | Authoritative upstream source; endpoint schemas/availability can change. Publish retrieval code and attribution, not assume bulk raw redistribution is licensed. Tested Advanced lineup request timed out. |
| [PBP Stats API](https://api.pbpstats.com/docs), [parser documentation](https://pbpstats.readthedocs.io/en/latest/) | Team/player/lineup aggregates and separate possession endpoints. Site advertises NBA history from 2000–01; verify each selected partition. This build evaluates 2022–23 to 2025–26 outcomes plus 2021–22 player history. | NBA numeric IDs represented as strings in API. Canonicalize sorted lineup membership ourselves. Player totals can span trades; do not interpret attached team label as a roster history. | Public JSON; no HTML scraping for V1. Snapshot API schema. Empirically league-wide player/lineup responses stop at 500 rows. Team lineup responses can also cap. Three workers maximum, one-second pause per successful request, bounded retries; these are our courtesy settings, not claimed provider limits. | Derived play-by-play has event-order/lineup edge cases and provider-specific possession rules. Team totals are an internal cross-check, not independent validation. Code can be shared with attribution; no verified blanket data-redistribution grant, so raw/processed bulk caches stay out of Git. |
| [ramirobentes/nba_pbp_data](https://github.com/ramirobentes/nba_pbp_data) | Repository lists regular-season lineup/PBP files from 1997 through 2026 plus playoffs. API directory inspection found a 21,801,546-byte 2025 lineup CSV. Did not download or validate this file. | Field-level ID quality not yet verified; do not assume schema equivalence. | Public GitHub files; no HTML scraping required. Reproduction should pin a commit and checksum, not a moving branch. GitHub API/raw hosting limits apply; exact budget not measured. | Useful fallback and possession-level candidate. Documentation, parsing assumptions, season completeness, and redistribution permission require further audit before selection. Not rejected for quality; deferred because the directly documented API worked. |
| [Basketball Reference](https://www.basketball-reference.com/about/) | Long historical player/team box scores and advanced metrics; potential lagged BPM talent control. Not a single demonstrated source for the requested linked lineup table. | Own player slugs, not NBA numeric IDs; crosswalk validation needed. | HTML/manual exports rather than a tested supported bulk API. [Data-use policy](https://www.sports-reference.com/data_use.html) and current restrictions should be reviewed before bulk use. No bulk scraping attempted. | Good conceptual/reference cross-check. Historical advanced-metric availability varies. Do not equate box-score player ratings with five-man on-court ratings. Deferred to avoid fragile scraping and ID joins in V1. |

## Required data feasibility

| Requirement | Selected source fields / construction | Remaining qualification |
|---|---|---|
| Player statistics | Player totals: shot-zone counts, assists, turnovers, rebounds, steals, blocks, points, time | League cap must fall below profile eligibility cutoff; sparse zero event keys require explicit handling |
| Five players | Lineup `EntityId`, split into five unique positive NBA IDs | Reject malformed/duplicate membership and record exclusions |
| Time / exposure | `SecondsPlayed`, `OffPoss`, `DefPoss` | Use seconds/60, not rounded `Minutes`; retain both possession sides |
| Offense / defense / net | 100 × Points/OffPoss; 100 × OpponentPoints/DefPoss; difference | Exclude undefined rates when either denominator is zero |
| Stable identifiers | Player/team numeric IDs; `YYYY-YY` season strings | Preserve team-season identity in keys |
| Shared four-player cores | Five distinct subsets per canonical lineup | Count alternate fifth players after each sample/feature filter |
| Multiple seasons | Four recent complete-season candidates and one prior profile season | Team games, coverage reconciliation and schema checks must pass |
| Skill dimensions | Public event counts support interpretable proxies | Tracking-based spacing, potential assists, shot difficulty, and comprehensive defense not established |

## Historical window

Choose 2022–23 through 2025–26 for V1, conditional on validation: four recent seasons, manageable aggregate downloads, a consistent source, and lagged profiles available from 2021–22. The latest-season team query reports 30 teams and 1,230 games; this alone does not establish lineup completeness. Playoffs and play-in are excluded. The shortened 2020–21 season is outside the outcome window. Do not expand backward simply to find a favorable result.

## Access discoveries

1. An initial sandbox DNS failure was an environment restriction; public access succeeded in the approved network context.
2. The 2024–25 league-wide Lineup response contained 500 rows, 83,020 offensive possessions, versus 243,787 in the team totals. It is not a league-complete lineup dataset.
3. Team-specific requests recover more observations, but several also stop at 500. Date partitioning is necessary. A low minimum possession count does not prove completeness, particularly when sorting is by time.
4. 2024–25 Player returns 500 unique player IDs; the smallest observed time is about 86 minutes, below the prespecified 500-minute prior-profile requirement. Recheck this boundary separately in every feature season.
5. NBA Stats access timed out; independent NBA reconciliation is still required before strong research claims.
6. Some uncapped 2022–23 responses slightly exceeded team totals. Date-filtered queries resolved these discrepancies; the upstream cause is unknown. Final pilot totals reconcile exactly for all 30 teams on seconds, both possession sides and both scoring sides. The pipeline repairs both capped and nonreconciling source responses.
