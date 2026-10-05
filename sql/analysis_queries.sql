-- Independently verify how many eligible cores retain two or more fifth players.
-- observations already requires all five lagged profiles. Exposure is NOT summed here.
WITH thresholds(threshold) AS (VALUES (25),(50),(100),(200)),
eligible_cores AS (
    SELECT t.threshold, o.core_key, COUNT(DISTINCT o.fifth_id) AS fifth_players
    FROM observations AS o
    JOIN thresholds AS t ON o.min_side_poss >= t.threshold
    WHERE o.net_rating IS NOT NULL
    GROUP BY t.threshold, o.core_key
    HAVING COUNT(DISTINCT o.fifth_id) >= 2
)
SELECT t.threshold, COUNT(e.core_key) AS comparison_cores,
       COALESCE(SUM(e.fifth_players),0) AS comparison_rows
FROM thresholds t
LEFT JOIN eligible_cores e ON e.threshold=t.threshold
GROUP BY t.threshold
ORDER BY t.threshold;
