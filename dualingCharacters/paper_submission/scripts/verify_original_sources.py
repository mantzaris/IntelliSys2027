"""Optional stronger check against original local research artifacts.
Never required to build the manuscript or regenerate its figures.
"""
from pathlib import Path
from collections import defaultdict
import argparse,gzip,hashlib,json
P=Path(__file__).resolve().parents[1]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()
def main(root):
    root=Path(root);scope=json.loads((P/'SCOPE.json').read_text());hashes=dict(scope['source_sha256']);requests=defaultdict(dict);checks=[]
    episodes=json.loads((P/'data/selected_archive_episodes.json').read_text())
    def add(locator,expected,decode=False):
        hashes[locator['file']]=locator['sha256'];requests[locator['file']][locator['record']]=None;checks.append((locator,expected,decode))
    for e in episodes:
        for t in e['turns']:
            add(t['user']['locator'],t['user']['text'])
            add(t['defender']['locator'],t['defender']['raw'])
            add(t['defender_observation_locator'],t['defender_observation'],True)
            a=t['action']
            if a:
                add(a['claim_locator'],a['claim']);add(a['generated_claim_locator'],a['generated_claim'])
                add(a['observation_locator'],a['observation'],True)
    edges=json.loads((P/'data/selected_edge_records.json').read_text())
    for item in edges:
        hashes[item['path']]=item['original_file_sha256'];requests[item['path']][item['line']]=None
    missing=[name for name in hashes if not (root/name).exists()]
    if missing:raise SystemExit('Missing original-artifact prerequisites (portable build unaffected): '+', '.join(missing))
    for name,digest in hashes.items():assert sha(root/name)==digest, 'Original source hash mismatch: '+name
    for name,needed in requests.items():
        opener=gzip.open if name.endswith('.gz') else open
        with opener(root/name,'rt') as f:
            for line,raw in enumerate(f,1):
                if line in needed:needed[line]=json.loads(raw)
        assert all(v is not None for v in needed.values())
    for loc,expected,decode in checks:
        value=requests[loc['file']][loc['record']]
        for key in loc['field']:value=value[key]
        if loc.get('decoded'):
            value=json.loads(value)
            for key in loc['decoded']:value=value[key]
        if decode and isinstance(value,str):value=json.loads(value)
        assert value==expected,loc
    for item in edges:assert requests[item['path']][item['line']]==item['record']
    report={'original_files_sha256_verified':len(hashes),'original_archive_fields_verified':len(checks),
            'original_edge_records_verified':len(edges),'scope':'Entire original listed file hashes plus selected record equality; not an independent semantic assessment.'}
    (P/'.build/original_source_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--research-root',required=True);main(parser.parse_args().research_root)
