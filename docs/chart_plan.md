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
