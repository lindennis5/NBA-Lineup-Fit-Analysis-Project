"""Effect scaling, equivalence and multiplicity helpers shared by the final audit steps."""
import numpy as np
from scipy.stats import t
from .models import lineup_weights

EQUIVALENCE_MARGIN = 1.0   # net points per 100 possessions per within-core SD (docs/FINAL_AUDIT.md)

def within_core_sd(sample, column):
    """Possession-weighted SD of a column after removing core means (the model's own variation)."""
    w = lineup_weights(sample)
    values = sample[column]
    means = (values * w).groupby(sample.core_key).transform('sum') / w.groupby(sample.core_key).transform('sum')
    return float(np.sqrt((w * (values - means) ** 2).sum() / w.sum()))

def scaled_effect(coefficient, se, clusters, sd):
    """Per-SD effect with 95% CI, 90% CI (equivalence), equivalence verdict and minimum detectable effect."""
    crit95, crit90 = t.ppf(.975, clusters - 1), t.ppf(.95, clusters - 1)
    lo90, hi90 = (coefficient - crit90 * se) * sd, (coefficient + crit90 * se) * sd
    return {'sd_within_core': sd, 'effect_per_sd': coefficient * sd, 'se_per_sd': se * sd,
            'ci_low_per_sd': (coefficient - crit95 * se) * sd, 'ci_high_per_sd': (coefficient + crit95 * se) * sd,
            'ci90_low_per_sd': lo90, 'ci90_high_per_sd': hi90,
            'equivalent_within_margin': bool(-EQUIVALENCE_MARGIN < lo90 and hi90 < EQUIVALENCE_MARGIN),
            'min_detectable_effect_per_sd': float((crit95 + .842) * se * sd)}

def holm(p_values):
    """Holm step-down adjusted p-values, returned in the input order."""
    p = np.asarray(p_values, dtype=float)
    order = np.argsort(p)
    adjusted = np.empty_like(p)
    running = 0.
    for rank, index in enumerate(order):
        running = max(running, (len(p) - rank) * p[index])
        adjusted[index] = min(1., running)
    return adjusted
