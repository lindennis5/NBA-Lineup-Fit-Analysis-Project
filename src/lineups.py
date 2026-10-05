"""Deterministic lineup/core construction and auditable coverage checks."""
import json
import hashlib
import re
import numpy as np
import pandas as pd
from .data_pipeline import RAW, OUT, ROOT

SEASONS = ['2022-23', '2023-24', '2024-25', '2025-26']
COUNTS = ['SecondsPlayed','OffPoss','DefPoss','Points','OpponentPoints','PlusMinus']

def player_tuple(value, size=5):
    parts = str(value).split('-')
    if len(parts) != size or any(not re.fullmatch(r'[1-9][0-9]*', p) for p in parts):
        raise ValueError(f'Invalid {size}-player ID: {value}')
    ids = tuple(sorted(map(int, parts)))
    if len(set(ids)) != size:
        raise ValueError(f'Repeated player in {value}')
    return ids

def canonical_id(ids):
    return '-'.join(map(str, sorted(ids)))

def load_rows(path):
    payload=path.read_bytes()
    meta=path.with_suffix('.meta.json')
    if meta.exists():
        expected=json.loads(meta.read_text(encoding='utf-8'))['sha256']
        if hashlib.sha256(payload).hexdigest()!=expected:
            raise ValueError(f'Cache checksum mismatch: {path.name}')
    return json.loads(payload)['multi_row_table_data']

def build_lineups(seasons=SEASONS):
    records, coverage, quarantine = [], [], []
    for season in seasons:
        teams = load_rows(RAW / f'pbp_{season}_Team.json')
        for team in teams:
            tid = str(team['EntityId'])
            source_path=RAW / f'pbp_{season}_Lineup_{tid}.json'
            original_rows=load_rows(source_path)
            capped=len(original_rows)>=500
            mismatch=any(abs(sum(r.get(k,0) for r in original_rows)-team.get(k,0))>1e-5 for k in COUNTS[:-1])
            corrected_path=RAW / f'pbp_{season}_Lineup_{tid}_complete.json'
            if capped or mismatch:
                source_path=corrected_path
            rows = load_rows(source_path)
            frame = pd.DataFrame(rows)
            # Sparse event-count keys are omitted for zero counts by the source.
            for col in COUNTS:
                if col not in frame:
                    raise ValueError(f'Missing whole required field {col}')
            frame[COUNTS] = frame[COUNTS].fillna(0)
            if frame.EntityId.duplicated().any():
                raise ValueError(f'Duplicate source lineup in {season}/{tid}')
            if set(frame.TeamId.astype(str)) != {tid}:
                raise ValueError('Requested team differs from response')
            if (frame[COUNTS[:-1]] < 0).any().any():
                raise ValueError('Negative count')
            # Track truncation; do not infer complete coverage from a low last-row possession count.
            total = frame.OffPoss + frame.DefPoss
            ordered = bool((np.diff(total.to_numpy()) <= 0).all())
            cap_boundary = float(total.min()/2) if len(rows) >= 500 else 0.0
            coverage.append({'season':season,'team_id':tid,'team':team['TeamAbbreviation'],
                'rows':len(rows),'original_query_capped':capped,'original_totals_mismatch':mismatch,'date_partitioned':source_path==corrected_path,'ordered_by_total_poss':ordered,
                'cap_boundary_mean_poss':cap_boundary, 'ordered_by_seconds':bool((np.diff(frame.SecondsPlayed)<=0).all()), 'team_games':team['GamesPlayed'],
                **{f'{c}_lineup':float(frame[c].sum()) for c in COUNTS[:-1]},
                **{f'{c}_team':float(team.get(c,0)) for c in COUNTS[:-1]}})
            for row in frame.to_dict('records'):
                try:
                    ids = player_tuple(row['EntityId'])
                except ValueError as exc:
                    quarantine.append({'season':season,'team_id':tid,'raw_id':row['EntityId'],'reason':str(exc)})
                    continue
                off, deff = row['OffPoss'], row['DefPoss']
                lid = canonical_id(ids)
                records.append({'season':season,'team_id':tid,'team':team['TeamAbbreviation'],
                    'lineup_id':lid,'lineup_key':f'{season}|{tid}|{lid}',
                    **{f'p{i+1}':pid for i,pid in enumerate(ids)},
                    'lineup_name':row['Name'],'minutes':row['SecondsPlayed']/60,
                    'off_poss':off,'def_poss':deff,'possessions':(off+deff)/2,
                    'min_side_poss':min(off,deff),'points':row['Points'],'opponent_points':row['OpponentPoints'],
                    'off_rating':100*row['Points']/off if off else np.nan,
                    'def_rating':100*row['OpponentPoints']/deff if deff else np.nan})
    lineups = pd.DataFrame(records)
    if lineups.lineup_key.duplicated().any():
        raise ValueError('Canonical lineup collision')
    lineups['net_rating'] = lineups.off_rating-lineups.def_rating
    coverage = pd.DataFrame(coverage)
    OUT.mkdir(parents=True,exist_ok=True)
    lineups.to_csv(OUT/'lineups.csv',index=False)
    coverage.to_csv(ROOT/'docs'/'coverage_audit.csv',index=False)
    pd.DataFrame(quarantine, columns=['season','team_id','raw_id','reason']).to_csv(ROOT/'docs'/'quarantine.csv',index=False)
    return lineups, coverage

def expand_cores(lineups):
    records=[]
    for row in lineups.to_dict('records'):
        ids=tuple(int(row[f'p{i}']) for i in range(1,6))
        for fifth in ids:
            core=tuple(p for p in ids if p!=fifth)
            cid=canonical_id(core)
            records.append(row | {'core_id':cid,'core_key':f'{row["season"]}|{row["team_id"]}|{cid}',
                'fifth_id':fifth, **{f'c{i+1}':p for i,p in enumerate(core)}})
    result=pd.DataFrame(records)
    if len(result)!=5*len(lineups) or result.duplicated(['core_key','fifth_id']).any():
        raise ValueError('Core expansion cardinality failure')
    return result

def comparison_sample(observations, threshold):
    valid=observations[(observations.min_side_poss>=threshold)&np.isfinite(observations.net_rating)].copy()
    count=valid.groupby('core_key').fifth_id.transform('nunique')
    return valid[count>=2].copy()

def threshold_table(observations, thresholds=(0,10,25,50,100,200)):
    result=[]
    for threshold in thresholds:
        eligible=observations[(observations.min_side_poss>=threshold)&np.isfinite(observations.net_rating)]
        compare=comparison_sample(observations,threshold)
        unique=compare.drop_duplicates('lineup_key')
        result.append({'threshold':threshold,'eligible_lineups':eligible.lineup_key.nunique(),
            'eligible_core_rows':len(eligible),'comparison_cores':compare.core_key.nunique(),
            'comparison_rows':len(compare),'comparison_lineups':len(unique),
            'comparison_mean_side_possessions':unique.possessions.sum()})
    return pd.DataFrame(result)
