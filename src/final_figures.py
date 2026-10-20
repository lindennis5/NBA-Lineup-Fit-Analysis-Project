"""The seven release figures. Each shows core deficiencies, fifth-player contributions,
talent vs fit, effects with uncertainty, or the Knicks/Brunson example. PNG + SVG.
"""
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from .analysis import save_figure, BLUE, ORANGE, INK
from .data_pipeline import ROOT, OUT
from .lineups import comparison_sample
from .features import SKILLS
from .alternative_metrics import add_alternatives

AUDIT = ROOT / 'docs' / 'audit'
DOCS = ROOT / 'docs'
GREY = '#9CA7AF'
SOURCE = 'Source: PBP Stats; regular seasons. Observational association, not a causal effect.'
KNICKS_CORE = '1626157-1628384-1628404-1628969'
SPEC_LABELS = {'primary': 'Primary model', 'common_denominator_outcome': 'Outcome uses mean possessions',
    'provider_plusminus_outcome': 'Outcome uses provider plus-minus',
    'exclude_provider_plusminus_discrepancies': 'Drop plus-minus discrepancy lineups',
    'equal_lineup': 'Equal lineup weights', 'equal_representation': 'Equal row weights',
    'exposure_per_representation': 'Full exposure per row', 'skills_without_quality': 'No talent control',
    'quality_without_skills': 'No skill controls', 'all_gaps': 'Credit all gaps', 'uncapped': 'No cap on credit',
    'no_interior': 'Drop blocks dimension', 'median_core': 'Median instead of mean core',
    'quadratic_quality': 'Quadratic talent control', 'spacing_volume_only': 'Spacing = 3PA volume only',
    'prior_minutes_250': 'Profiles need 250+ minutes', 'prior_minutes_1000': 'Profiles need 1,000+ minutes'}
FIT_TERMS = {'complementarity', 'complementarity_all', 'complementarity_uncapped', 'complementarity_no_interior', 'median_closure'}

def style():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'svg.hashsalt': 'nba-lineup-fit',
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.labelcolor': INK, 'text.color': INK,
        'axes.titlecolor': INK, 'axes.titleweight': 'bold', 'figure.facecolor': 'white', 'axes.facecolor': 'white'})

def status():
    return pd.read_csv(DOCS / 'season_validation_status.csv').set_index('season')

def is_validated(label, s):
    if label in s.index:
        return s.loc[label, 'disposition'] == 'validated'
    return label == 'validated_seasons'

def interval(ax, y, beta, low, high, hollow, color=BLUE):
    ax.errorbar(beta, y, xerr=[[beta - low], [high - beta]], fmt='o', color=color, capsize=4,
                mfc='white' if hollow else color, mew=1.5)

def season_effects(s):
    r = pd.read_csv(AUDIT / 'final_robustness.csv')
    r = r[(r.specification == 'primary') & (r.term == 'complementarity')]
    good = [x for x in s.index if s.loc[x, 'disposition'] == 'validated']
    order = [('validated_seasons', f'Validated seasons ({", ".join(good)})'), ('pooled', 'All four seasons (provisional)')] + \
            [(x, x + ('' if x in good else ' (provisional)')) for x in s.index]
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), sharey=True)
    for ax, (lo, hi, beta, scale, label) in zip(axes, [
            ('ci_low', 'ci_high', 'coefficient_per_unit', .1, 'Net points per 100 possessions\nper 0.1 unit of gap closed'),
            ('ci_low_per_sd', 'ci_high_per_sd', 'effect_per_sd', 1, 'Net points per 100 possessions\nper 1 within-core SD of gap closed')]):
        for i, (key, text) in enumerate(order):
            row = r[r.scope == key]
            if row.empty:
                continue
            row = row.iloc[0]
            interval(ax, i, row[beta] * scale, row[lo] * scale, row[hi] * scale, hollow=not is_validated(key, s))
        ax.axvline(0, color=INK, lw=1, ls='--')
        ax.set_xlabel(label)
        ax.set_yticks(range(len(order)), [t for _, t in order])
        ax.invert_yaxis()
    axes[0].set_title('Largest-gap closure: effect by sample', loc='left')
    fig.text(.01, .01, 'Filled = validated season set; hollow = provisional source counters. 95% franchise-clustered intervals; zero = no effect.\n' + SOURCE,
             fontsize=8)
    fig.tight_layout(rect=[0, .07, 1, 1])
    save_figure(fig, 'season_effects')

def robustness_effects(s):
    e = pd.read_csv(DOCS / 'extended_coefficients.csv')
    e = e[e.term.isin(FIT_TERMS) & (e.threshold == 50)]
    rows = []
    good = [x for x in s.index if s.loc[x, 'disposition'] == 'validated']
    bal = e[(e.scope == 'balanced_source_seasons') & (e.specification == 'primary')]
    if len(bal):
        rows.append(('Primary model, validated seasons', bal.iloc[0], False))
    for spec, row in e[e.scope == 'pooled'].groupby('specification'):
        rows.append((f'{SPEC_LABELS.get(spec, spec)} (all seasons)', row.iloc[0], True))
    for thr in (25, 100):
        t = pd.read_csv(DOCS / 'extended_coefficients.csv')
        t = t[(t.scope == 'pooled') & (t.specification == 'primary') & (t.term == 'complementarity') & (t.threshold == thr)]
        if len(t):
            rows.append((f'Primary model, {thr}+ possessions per side (all seasons)', t.iloc[0], True))
    fig, ax = plt.subplots(figsize=(10, 0.36 * len(rows) + 1.8))
    for i, (label, r, hollow) in enumerate(rows):
        interval(ax, i, r.coefficient * .1, r.ci_low * .1, r.ci_high * .1, hollow)
    ax.axvline(0, color=INK, lw=1, ls='--')
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.invert_yaxis()
    ax.set_xlabel('Net points per 100 possessions per 0.1 unit of gap closed (scale differs slightly for rows that change the score)')
    ax.set_title('Every specification: the interval stays centred near zero', loc='left')
    fig.text(.01, .01, 'Filled = validated seasons; hollow = includes provisional seasons. 95% franchise-clustered intervals. ' + SOURCE, fontsize=8)
    fig.tight_layout(rect=[0, .04, 1, 1])
    save_figure(fig, 'robustness_effects')

def metric_comparison():
    m = pd.read_csv(AUDIT / 'metric_comparison.csv')
    names = {'complementarity': 'Original: largest-gap closure', 'alt_deficiency_supply': 'A1: deficiency-weighted supply',
             'alt_redundancy': 'A2: skill redundancy', 'alt_specialist_coverage': 'A3: specialist coverage'}
    fig, ax = plt.subplots(figsize=(10, 5))
    ys = {k: i for i, k in enumerate(names)}
    for scope, shift, color, hollow in [('validated_seasons', -.12, BLUE, False), ('pooled', .12, ORANGE, True)]:
        for _, r in m[m.scope == scope].iterrows():
            interval(ax, ys[r.metric] + shift, r.effect_per_sd, r.ci_low_per_sd, r.ci_high_per_sd, hollow, color)
    ax.axvline(0, color=INK, lw=1, ls='--')
    ax.set_yticks(range(len(names)), list(names.values()))
    ax.invert_yaxis()
    ax.set_xlabel('Net points per 100 possessions per 1 within-core SD of the score')
    ax.set_title('Original score and three alternatives: same answer', loc='left')
    ax.plot([], [], 'o', color=BLUE, label='Validated seasons')
    ax.plot([], [], 'o', color=ORANGE, mfc='white', label='All four seasons (provisional)')
    ax.legend(frameon=False, loc='upper center', bbox_to_anchor=(.5, -.14), ncol=2)
    fig.text(.01, .01, 'Alternatives were pre-registered before testing; none is called supported unless all three gates in the pre-registration pass.\n95% franchise-clustered intervals. ' + SOURCE, fontsize=8)
    fig.tight_layout(rect=[0, .09, 1, 1])
    save_figure(fig, 'metric_comparison')

def talent_complementarity(d):
    primary = comparison_sample(d, 50)
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.6), sharex=True, constrained_layout=True)
    for ax, (col, title) in zip(axes, [('complementarity', 'Original: largest-gap closure'),
                                       ('alt_deficiency_supply', 'A1: deficiency-weighted skill supply')]):
        hb = ax.hexbin(primary.fifth_quality, primary[col], gridsize=35, mincnt=1, cmap='Blues', bins='log')
        zero = (primary[col] == 0).mean()
        corr = primary[col].corr(primary.fifth_quality)
        ax.set(xlabel='Fifth player prior Game Score/36 (z-score)', title=title)
        ax.text(.02, .95, f'{zero:.1%} of rows exactly 0\ncorrelation with talent {corr:+.2f}', transform=ax.transAxes,
                va='top', fontsize=9, bbox=dict(facecolor='white', edgecolor='none', alpha=.85))
    axes[0].set_ylabel('Score (standardized skill units)')
    fig.colorbar(hb, ax=axes, label='Core/fifth rows per hexagon (log scale)', shrink=.8, pad=.02)
    fig.text(.01, .01, f'{len(primary):,} core/fifth rows with 50+ possessions per side; dependent rows, descriptive only. ' + SOURCE, fontsize=8)
    fig.get_layout_engine().set(rect=(0, .05, 1, .95))
    save_figure(fig, 'talent_complementarity')

def forward_prediction():
    club = pd.read_csv(DOCS / 'forward_club_scores.csv')
    rng = np.random.default_rng(20261016)
    def delta(g):
        b = g[g.model == 'baseline'].set_index('team_id')
        f = g[g.model == 'complementarity'].set_index('team_id').reindex(b.index)
        return b.squared_error_sum.to_numpy(), f.squared_error_sum.to_numpy(), b.weight_sum.to_numpy()
    def point_and_ci(g):
        b, f, w = delta(g)
        fn = lambda i: np.sqrt(f[i].sum() / w[i].sum()) - np.sqrt(b[i].sum() / w[i].sum())
        all_i = np.arange(len(b))
        draws = [fn(rng.integers(0, len(b), len(b))) for _ in range(1999)]
        return fn(all_i), np.quantile(draws, .025), np.quantile(draws, .975)
    rows = [(f'Test season {s}', *point_and_ci(g)) for s, g in club.groupby('test_season')]
    rows.append(('All forward tests', *point_and_ci(club)))
    fig, ax = plt.subplots(figsize=(9, 4.2))
    for i, (label, p, lo, hi) in enumerate(rows):
        interval(ax, i, p, lo, hi, hollow=False, color=BLUE if i == len(rows) - 1 else GREY)
    ax.axvline(0, color=INK, lw=1, ls='--')
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.invert_yaxis()
    ax.set_xlabel('Change in prediction error (RMSE) after adding the fit score\nleft of zero = fit helps, right = fit hurts')
    ax.set_title('Does fit improve next-season predictions? No', loc='left')
    fig.text(.01, .01, 'Trained on earlier seasons only; scores within-core contrasts, not absolute lineup ratings. 95% franchise-bootstrap intervals,\nconditional on the fitted models. ' + SOURCE, fontsize=8)
    fig.tight_layout(rect=[0, .08, 1, 1])
    save_figure(fig, 'forward_prediction')

def knicks_example(d, s):
    k = comparison_sample(d[(d.team == 'NYK') & (d.season == '2024-25') & d.core_key.str.endswith(KNICKS_CORE)], 50)
    k = k.sort_values('possessions', ascending=False).head(4)
    first = k.iloc[0]
    weakest = first.weakest_skill
    fig, ax = plt.subplots(figsize=(11, 6.6))
    y = np.arange(5)
    h = .16
    ax.barh(y - 2 * h, [first[f'core_{c}'] for c in SKILLS], h, color=GREY, label='Four-player core average')
    colors = [BLUE, ORANGE, '#5E8C61', '#8C5E85']
    for i, (_, r) in enumerate(k.iterrows()):
        label = f'{r.fifth_id_name}: original fit {r.complementarity:.2f}, A1 {r.alt_deficiency_supply:+.2f}'
        ax.barh(y + (i - 1) * h, [r[f'fifth_{c}'] for c in SKILLS], h, color=colors[i], label=label,
                hatch=None if i == 0 else ['', '//', '..', 'xx'][i])
    ax.axvline(0, color=INK, lw=.8)
    ax.set_yticks(y, SKILLS)
    ax.get_yticklabels()[SKILLS.index(weakest)].set_fontweight('bold')
    ax.set_xlabel('Prior-season skill (z-score; 2023-24 profiles for 2024-25 lineups)')
    names = ', '.join(str(first[f'c{i}_name']) for i in range(1, 5))
    prov = '' if s.loc['2024-25', 'disposition'] == 'validated' else ' | 2024-25 outcome data provisional'
    ax.set_title(f'Knicks core: {names}', loc='left', fontsize=11)
    ax.legend(frameon=False, loc='lower right', fontsize=9)
    fig.text(.01, .01, f'Bold row = the core\'s largest gap ({weakest}, blocks only; {first.deficiency_gap:.2f} SD). Candidates are the four with the most shared possessions.{prov}\n'
             'The original score credits only that one row, so Brunson scores 0 despite elite creation. A1 credits skill wherever the core is weak.\n'
             'Illustration, not advice. ' + SOURCE, fontsize=8)
    fig.tight_layout(rect=[0, .11, 1, 1])
    save_figure(fig, 'knicks_example')

def core_deficiencies(d):
    cores = comparison_sample(d, 50).drop_duplicates('core_key')
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    axes[0].hist(cores.deficiency_gap, bins=30, color=BLUE, edgecolor='white')
    median = cores.deficiency_gap.median()
    axes[0].axvline(median, color=ORANGE, lw=2)
    axes[0].set(xlabel='Size of the core\'s largest below-average skill (SD)', ylabel='Four-player cores',
                title='Most core gaps are small')
    axes[0].text(median, axes[0].get_ylim()[1] * .9, f' median {median:.2f} SD\n {(cores.deficiency_gap == 0).mean():.1%} have no gap', color=INK, fontsize=9)
    counts = cores.weakest_skill.value_counts().reindex(SKILLS).fillna(0)
    axes[1].barh(counts.index, counts.values, color=BLUE)
    axes[1].set(xlabel='Cores whose largest gap is in this skill', title='Where the gaps are')
    fig.text(.01, .01, f'{len(cores):,} four-player cores with 2+ observed fifth players, 50+ possessions per side. Interior = blocks only. ' + SOURCE, fontsize=8)
    fig.tight_layout(rect=[0, .05, 1, 1])
    save_figure(fig, 'core_deficiencies')

def main():
    style()
    s = status()
    d = add_alternatives(pd.read_csv(OUT / 'observations.csv'))
    season_effects(s)
    robustness_effects(s)
    metric_comparison()
    talent_complementarity(d)
    forward_prediction()
    knicks_example(d, s)
    core_deficiencies(d)

if __name__ == '__main__':
    main()
