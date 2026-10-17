"""Preserve compact analytical results under a content-derived run identifier."""
import hashlib
import json
import shutil
from .data_pipeline import ROOT

def main():
    docs=ROOT/'docs'
    manifest=json.loads((docs/'release_run_manifest.json').read_text(encoding='utf-8'))
    identity={k:v for k,v in manifest.items() if k!='generated_utc'}
    identity['raw_inventory_sha256']=hashlib.sha256((docs/'raw_inventory.json').read_bytes()).hexdigest()
    key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:12]
    target=docs/'runs'/key;target.mkdir(parents=True,exist_ok=True)
    for path in docs.iterdir():
        if path.is_file() and path.suffix in ['.json','.csv']:
            shutil.copy2(path,target/path.name)
    (target/'README.md').write_text('This directory freezes the small result tables and provenance for this run.\n'
        'Raw data remain in ignored data/raw caches. Code hashes and configuration are in release_run_manifest.json.\n',encoding='utf-8')
    print(f'Archived results: docs/runs/{key}')

if __name__=='__main__':main()
