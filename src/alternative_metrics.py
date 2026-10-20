"""Three pre-registered alternative fit scores (docs/metric_preregistration.md).

Inputs are lagged standardized skills in the order of features.SKILLS. The original
largest-gap-closure score is untouched; alternatives are added as separate columns.
"""
import numpy as np
import pandas as pd
from .features import SKILLS

ALTERNATIVES = ['alt_deficiency_supply', 'alt_redundancy', 'alt_specialist_coverage']

def deficiency_supply(core_mean, fifth):
    """A1: fifth-player skill weighted by the size of each core deficiency; 0 with no gap."""
    gaps = np.maximum(0, -np.asarray(core_mean, dtype=float))
    total = gaps.sum(axis=1)
    weighted = (gaps * np.asarray(fifth, dtype=float)).sum(axis=1)
    return np.divide(weighted, total, out=np.zeros_like(total), where=total > 0)

def redundancy(core_mean, fifth):
    """A2: overlap between the fifth player's strengths and the core's strengths."""
    return (np.maximum(0, core_mean) * np.maximum(0, fifth)).sum(axis=1)

def specialist_coverage(core_players, fifth):
    """A3: how far the fifth player exceeds the best core player in each skill."""
    best = np.asarray(core_players, dtype=float).max(axis=1)
    return np.maximum(0, np.asarray(fifth, dtype=float) - best).sum(axis=1)

def add_alternatives(observations):
    """Return a copy with the three alternative scores added."""
    d = observations.copy()
    core_mean = d[[f'core_{s}' for s in SKILLS]].to_numpy(dtype=float)
    fifth = d[[f'fifth_{s}' for s in SKILLS]].to_numpy(dtype=float)
    players = np.stack([d[[f'c{i}_{s}' for s in SKILLS]].to_numpy(dtype=float) for i in range(1, 5)], axis=1)
    d['alt_deficiency_supply'] = deficiency_supply(core_mean, fifth)
    d['alt_redundancy'] = redundancy(core_mean, fifth)
    d['alt_specialist_coverage'] = specialist_coverage(players, fifth)
    return d
