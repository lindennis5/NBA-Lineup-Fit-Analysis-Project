"""Cached public PBP Stats retrieval. Run from repository root with -m src.data_pipeline."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
OUT = ROOT / 'data' / 'processed'

def validate_seasons(seasons):
    if not seasons or any(not re.fullmatch(r'\d{4}-\d{2}',s) or int(s[-2:])!=(int(s[:4])+1)%100 for s in seasons):
        raise ValueError('Use valid NBA season labels such as 2022-23')
    starts=[int(s[:4]) for s in seasons]
    if starts!=list(range(starts[0],starts[0]+len(starts))):
        raise ValueError('Select consecutive seasons in ascending order')

def fetch(name, url, refresh=False):
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f'{name}.json'
    meta = RAW / f'{name}.meta.json'
    if path.exists() and meta.exists() and not refresh:
        payload = path.read_bytes()
        info = json.loads(meta.read_text(encoding='utf-8'))
        if hashlib.sha256(payload).hexdigest() != info['sha256']:
            raise ValueError(f'Cache checksum mismatch: {path}')
        return json.loads(payload)
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'nba-lineup-fit-research/0.1'})
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read()
            parsed = json.loads(payload)
            temporary = path.with_suffix('.tmp')
            temporary.write_bytes(payload)
            temporary.replace(path)
            meta.write_text(json.dumps({'url': url, 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
                'sha256': hashlib.sha256(payload).hexdigest(), 'bytes': len(payload)}, indent=2), encoding='utf-8')
            time.sleep(1)
            return parsed
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))

def totals(season, entity, team=None, refresh=False):
    params = {'Season': season, 'SeasonType': 'Regular Season', 'Type': entity}
    if team:
        params['TeamId'] = str(team)
    name = f'pbp_{season}_{entity}' + (f'_{team}' if team else '')
    data = fetch(name, 'https://api.pbpstats.com/get-totals/nba?' + urllib.parse.urlencode(params), refresh)
    rows = data.get('multi_row_table_data')
    if not isinstance(rows, list) or not rows:
        raise ValueError(f'No rows for {name}')
    return rows

def complete_lineups(season, team, refresh=False, team_totals=None):
    rows=totals(season,'Lineup',team,refresh)
    counters=['SecondsPlayed','OffPoss','DefPoss','Points','OpponentPoints','PlusMinus']
    mismatch=team_totals is not None and any(abs(sum(r.get(k,0) for r in rows)-team_totals.get(k,0))>1e-5
        for k in counters[:-1])
    if len(rows)<500 and not mismatch:
        return rows
    start=int(season[:4])
    def partition(first,last):
        params={'Season':season,'SeasonType':'Regular Season','Type':'Lineup','TeamId':str(team),
                'FromDate':str(first),'ToDate':str(last)}
        part=fetch(f'pbp_{season}_Lineup_{team}_{first}_{last}',
            'https://api.pbpstats.com/get-totals/nba?'+urllib.parse.urlencode(params),refresh)['multi_row_table_data']
        if len(part)<500:
            return part
        if first>=last:
            raise ValueError('Single-day response is capped')
        middle=first+(last-first)//2
        return partition(first,middle)+partition(middle+timedelta(days=1),last)
    if len(rows)<500:
        parts=partition(date(start,10,1),date(start+1,6,30))
    else:
        parts=partition(date(start,10,1),date(start,12,31))+partition(date(start+1,1,1),date(start+1,6,30))
    merged={}
    for row in parts:
        key=row['EntityId']
        if key not in merged:
            merged[key]={k:row[k] for k in ['EntityId','TeamId','Name']}
            merged[key].update({k:0 for k in counters})
        for k in counters:
            merged[key][k]+=row.get(k,0)
    result=list(merged.values())
    (RAW/f'pbp_{season}_Lineup_{team}_complete.json').write_text(json.dumps({'multi_row_table_data':result}),encoding='utf-8')
    return result

def download(seasons, refresh=False, workers=3):
    validate_seasons(seasons)
    for season in seasons:
        teams = totals(season, 'Team', refresh=refresh)
        if len(teams) != 30:
            raise ValueError(f'{season}: expected 30 teams, got {len(teams)}')
        print(f'{season}: teams={len(teams)}, games={sum(t["GamesPlayed"] for t in teams)/2}', flush=True)
        totals(season, 'Player', refresh=refresh)
        def work(team):
            rows=complete_lineups(season,team['EntityId'],refresh,team)
            print(f'{season} {team["EntityId"]}: {len(rows)} complete lineups',flush=True)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(work,teams))
    prior = f'{int(seasons[0][:4])-1}-{int(seasons[0][:4])%100:02d}'
    totals(prior, 'Player', refresh=refresh)
    manifests = [json.loads(p.read_text(encoding='utf-8')) | {'cache_file':p.name.replace('.meta','')}
                 for p in sorted(RAW.glob('pbp_*.meta.json'))]
    (ROOT/'docs'/'data_manifest.json').write_text(json.dumps(manifests, indent=2), encoding='utf-8')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seasons', nargs='+', default=['2022-23','2023-24','2024-25','2025-26'])
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--workers', type=int, choices=[1,2,3], default=3)
    args = parser.parse_args()
    download(args.seasons, args.refresh, args.workers)
