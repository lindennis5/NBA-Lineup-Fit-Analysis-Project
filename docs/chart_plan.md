# Figure contracts

Static Matplotlib figures in the requested GitHub/notebook deliverable. All figures use white backgrounds, dark ink, quiet horizontal guides, blue (#285D8F), and orange (#C87932) only for a second meaningful series. Export PNG at 180 dpi and SVG, approximately 9 × 5.5 inches. Inspect saved PNGs; show dates, grain, units, filtering and source. No decorative charts.

| File | Question / intended reading | Family and data | Encoding / QA |
|---|---|---|---|
| possession_distribution | How much exposure supports each lineup? | Histogram of unique lineup mean-side possessions, one value per season-team-lineup; expect tens of thousands | Log x axis explicitly labeled; zero-exposure cases separately noted. Never count five expansions. |
| threshold_tradeoff | How much comparison data is lost with stricter sample rules? | Grouped bars at 25/50/100/200 thresholds, before and after prior-profile eligibility | Four meaningful policy options, zero baseline, common counts of cores with 2+ fifth players. Sparse policy grid is intentional, not a time trend. |
| skill_correlation | Do the proposed skill dimensions overlap? | Five-by-five correlation heatmap of lagged player profiles | Fixed −1 to +1 scale, signed values annotated; no outcome-based player selection. |
| talent_complementarity | Is the initial complementarity score distinct from the talent proxy? | Scatter/hexbin of primary sample fifth quality versus gap closure | Dense same-grain observations; density displayed rather than hiding overplotting. This is not an effect estimate. |
| model_effects | How stable is the estimated largest-gap association across thresholds? | Dot and interval plot for 25/50/100, weighted within-core model with fifth-skill main effects | Effect per 0.1 standardized gap closed; club-clustered 95% intervals; zero reference, no claim of causality. |
| core_example | How does the measure behave for a real core? | Grouped horizontal bars of five dimensions: one core and two fifth-player profiles | Core selected by total exposure among primary comparison cores, players by exposure, never outcomes; signed standardized axes and names. Explain profiles are lagged and the example is illustrative. |

The raw complementarity–net-rating scatter is intentionally omitted: a within-core adjusted effect plot better matches the question and avoids inviting a misleading unadjusted interpretation. Full numerical tables remain available for auditing.

## Release additions

All added charts use reproducible static Matplotlib output (PNG/SVG), white backgrounds, labelled units and source notes. No decorative branding, watermarks or signatures. Blue is the primary mark; orange plus hatching distinguishes the second model/player. Exact values remain in versioned CSVs.

| File | Question | Design and evidence | QA |
|---|---|---|---|
| season_effects | Does the primary association differ by outcome season? | Dot/95% interval plot, one primary estimate per validated season plus pooled, per 0.1 gap unit | Zero reference; common scale; uncertainty is franchise-clustered, not causal |
| performance_distribution | How dispersed are observed eligible lineup outcomes? | Histogram of unique season-team lineups with all profiles and 50+ possessions each side | Count lineups once; label the eligible population, which differs from the comparison-core sample |
| forward_prediction | Does adding fit improve later-season contrast predictions? | Grouped zero-baseline RMSE bars, one test season per pair, direct difference annotation | Train only on earlier seasons; hatching identifies fit; clarify demeaned contrasts, not absolute forecasts |
| knicks_example | What does the metric reward for a recognizable Knicks core? | Grouped horizontal profile bars, highest-exposure eligible Knicks core, top two fifth players by exposure | Signed standardized scale; explain zero fit is not zero player value; all alternatives and exact scores in knicks_example.csv |

The small number of outcome seasons is the intended study window. Season comparisons use discrete interval/bar charts, not a misleading smooth time trend.
