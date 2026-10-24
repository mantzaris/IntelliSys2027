"""Read-only integrity audit of earlier human materials; never overwrites annotations."""
from pathlib import Path
import csv
from pcc.resources import sha256
from .common import ROOT,REPORTS,read,write,utc


def main():
    directory=ROOT/'artifacts/review_001/human_review/pilot_actions';items=read(directory/'items.json');key=read(directory/'private_key.json')
    ids={r['item_id'] for r in items}
    if len(items)!=60 or len(ids)!=60 or {r['item_id'] for r in key}!=ids:raise ValueError('Existing action packet identity mismatch')
    reference=read(ROOT/'supplements/review_001/results/pilot_actions_packet.json')['items_sha256']
    if sha256(directory/'items.json')!=reference:raise ValueError('Original action items changed')
    forms=[]
    for number in (1,2):
        path=directory/f'rater_{number}.csv'
        with path.open() as f:rows=list(csv.DictReader(f))
        if len(rows)!=60 or {r['item_id'] for r in rows}!=ids:raise ValueError('Existing human rating identity mismatch')
        forms.append({'rater':number,'items':60,'nonempty_annotation_cells':sum(bool(v) for r in rows for k,v in r.items() if k!='item_id'),'sha256':sha256(path),'modified_by_this_audit':False})
    missing=[]
    for c in ('c1','c3','c5'):
        run=f'extra-qwen-{c}-17-natural'
        if read(ROOT/'artifacts/runs'/run/'status.json',{}).get('status')!='completed':missing.append(run)
    write(REPORTS/'LEGACY_HUMAN_PACKET_STATUS.json',{'checked_utc':utc(),'action_items':60,'item_sha256':reference,'forms':forms,
      'private_key_sha256':sha256(directory/'private_key.json'),'prose_120_status':'pending_required_outputs' if missing else 'inputs_available_use_existing_packaging',
      'missing_original_natural_runs':missing,'fresh_intent_packet':'Separate; see HUMAN_REVIEW_STATUS.json','external_contact':False,'files_modified':[]})
    print({'original_action_items':60,'nonempty_annotation_cells':[r['nonempty_annotation_cells'] for r in forms],'missing_original_prose_runs':len(missing)})


if __name__=='__main__':main()
