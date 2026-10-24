"""Read-only packet integrity/annotation audit and separate readable rendering."""
from pathlib import Path
import csv
import html
import json
from pcc.resources import sha256
from pcc.validation import human_packet
from .common import ROOT,OUT,CACHE,read,write,utc


def main():
    directory=ROOT/'artifacts/review_001/human_review/pilot_actions';packet=read(directory/'items.json');key=read(directory/'private_key.json')
    identities={x['item_id'] for x in packet};assert len(packet)==len(identities)==60 and {x['item_id'] for x in key}==identities
    expected=read(ROOT/'supplements/review_001/results/pilot_actions_packet.json')['items_sha256'];assert sha256(directory/'items.json')==expected
    annotations={};inputs={}
    for path in sorted(directory.iterdir()):
        if path.is_file():inputs[str(path.relative_to(ROOT))]=sha256(path)
    for number in (1,2):
        path=directory/f'rater_{number}.csv'
        with path.open(newline='') as f:rows=list(csv.DictReader(f))
        assert len(rows)==60 and {r['item_id'] for r in rows}==identities
        annotations[str(number)]={'rows':60,'nonempty_rating_or_comment_cells':sum(bool(v) for row in rows for k,v in row.items() if k!='item_id')}
    # Rendering is a new artifact; original packet, private key and forms unchanged.
    output=CACHE/'human_review';output.mkdir(parents=True,exist_ok=True)
    parts=['<!doctype html><meta charset="utf-8"><title>Blinded character-action review</title><style>body{font:16px/1.5 sans-serif;max-width:70em;margin:2em auto}pre{white-space:pre-wrap}article{border-top:1px solid #777;margin-top:2em}</style>',
      '<h1>Character-action review</h1><p>'+html.escape((directory/'RUBRIC.txt').read_text())+'</p>']
    for row in packet:parts.append('<article><h2>'+html.escape(row['item_id'])+'</h2><pre>'+html.escape(json.dumps({k:v for k,v in row.items() if k!='item_id'},indent=2))+'</pre></article>')
    (output/'action_packet.html').write_text('\n'.join(parts))
    missing=[]
    for c in ('C1','C3','C5'):
        run_id=f'extra-qwen-{c.lower()}-17-natural';path=ROOT/'artifacts/runs'/run_id/'status.json'
        if not path.exists() or read(path)['status']!='completed':missing.append(run_id)
    if not missing:
        human_packet(ROOT)
        from analysis.human_review import generate
        prose=generate(ROOT)
    else:prose={'status':'pending_required_natural_outputs','missing_runs':missing,'required_outputs':120,'packaging_code':'src/pcc/validation.py:human_packet; analysis/human_review.py',
      'rubric':'paper/HUMAN_REVIEW_RUBRIC.md','substitution':'None; no pilot or alternative condition fills missing cells'}
    write(OUT/'HUMAN_REVIEW_STATUS.json',{'utc':utc(),'historical_action_packet':{'items':60,'identity_hash':expected,'annotations':annotations,'inputs':inputs,
      'readable_rendering':str((output/'action_packet.html').relative_to(ROOT)),'original_items_and_forms_preserved':True},'prose_review':prose,
      'new_B_packet':'Pending complete frozen B configurations; original action identities never reused','external_contact':'None'})
    print(json.dumps({'action_items':60,'annotations':annotations,'prose_status':prose['status']}))


if __name__=='__main__':main()
