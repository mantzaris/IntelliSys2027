"""A small, outcome-independent semantic-review packet; ratings stay blank."""
from collections import defaultdict
import csv
import json
import re
from .common import ROOT,HERE,REPORTS,CACHE,read,write,sha256,verified_stream,rank
from .analysis import verify_science

ROLE_WORDS=('Jekyll','Hyde','Rival','Traditionalist','Provocateur','Generic','Random')
PACKET_CONDITIONS=('C3','C4','C5','C6','A1','A2','A3')

def anonymize(value,mapping):
    if isinstance(value,dict):return {k:anonymize(v,mapping) for k,v in value.items()}
    if isinstance(value,list):return [anonymize(v,mapping) for v in value]
    if isinstance(value,str):
        for before,after in sorted(mapping.items(),key=lambda kv:-len(kv[0])):
            value=re.sub(r'\b'+re.escape(before)+r'\b',after,value)
        return value
    return value

def selection(cells):
    """One window per family/condition, balanced paired-world representation."""
    selected=[]
    for condition in PACKET_CONDITIONS:
        cell=next(c for c in cells if c['cohort']=='primary_mechanism' and c['condition']==condition)
        families=sorted(cell['family_ids'],key=lambda f:rank('exploration003-packet-world:'+condition,f))
        for i,family in enumerate(families):
            world='authorized' if i<len(families)//2 else 'hypothetical'
            ends=(4,8,12);end=ends[int(rank('exploration003-packet-anchor',(condition,family,world)),16)%3]
            key=(cell['id'],family,world,end)
            selected.append({'cell':cell['id'],'family_id':family,'world':world,'end_ordinal':end,
                'item_id':'EX3-'+rank('exploration003-item-v1',key)[:12]})
    if len(selected)>60:raise ValueError('Packet exceeds 60-item cap')
    if len({r['item_id'] for r in selected})!=len(selected):raise ValueError('Duplicate packet item')
    return sorted(selected,key=lambda x:rank('exploration003-review-order',x['item_id']))

def blank_ratings(path,items):
    fields=['item_id','semantic_strategy_codes','coherence_0_2','task_relevance_0_2','repetition_0_2','substantive_novelty_0_2','evidence_supported_goal_continuity','confidence_0_2','source_evidence','notes']
    if path.exists():
        with path.open() as f:existing=list(csv.DictReader(f))
        if [r['item_id'] for r in existing]!=[i['item_id'] for i in items]:raise ValueError('Existing rating identities differ; preserve them')
        return # Never overwrite human annotations.
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        writer.writerows({'item_id':i['item_id']} for i in items)

def main():
    verify_science();audit=read(HERE/'DATA_AUDIT.json');selected=selection(audit['included_cells'])
    reviewer=CACHE/'human_review/reviewer';private=CACHE/'human_review/private';reviewer.mkdir(parents=True,exist_ok=True);private.mkdir(exist_ok=True)
    items=[];source_hashes={}
    for condition in PACKET_CONDITIONS:
        cell=next(c for c in audit['included_cells'] if c['cohort']=='primary_mechanism' and c['condition']==condition)
        run=ROOT/'artifacts/runs'/cell['run_id'];action_name=condition+'_characters.jsonl';turn_name=condition+'.jsonl'
        actions=defaultdict(list);turns={}
        for a in verified_stream(run/action_name,cell['raw_hashes'][action_name]):actions[a['family_id'],a['world']].append(a)
        for t in verified_stream(run/turn_name,cell['raw_hashes'][turn_name]):turns[t['family_id'],t['world'],t['turn']]=t
        source_hashes[str((run/action_name).relative_to(ROOT))]=cell['raw_hashes'][action_name]
        source_hashes[str((run/turn_name).relative_to(ROOT))]=cell['raw_hashes'][turn_name]
        for choice in [r for r in selected if r['cell']==cell['id']]:
            key=choice['family_id'],choice['world'];episode=actions[key];end=choice['end_ordinal']
            aliases=list(dict.fromkeys(a['actor'] for a in episode));mapping={alias:f'Speaker {i+1}' for i,alias in enumerate(aliases)}
            mapping.update({r:'Component' for r in ROLE_WORDS});mapping['Jekyll']='Answerer'
            window=[]
            for a in episode[end-3:end]:
                t=turns[*key,a['turn']];body=json.loads(a['prompt'][-1]['content'])
                preceding=turns.get((*key,a['turn']-1))
                window.append({'turn':a['turn'],'speaker':a['actor'],
                    'action':{k:a.get(k) for k in ('kind','slot','value','claim','source','target','applied')},
                    'visible_source_evidence':body['sources'],'observed_working_memory':body['memory'],
                    'received_messages':body.get('inbox',[]),'prior_answer':preceding['generation']['parsed'] if preceding else None,
                    'time_indexed_truth_for_review_only':t['target'],'following_answer':t['generation']['parsed']})
            item={'item_id':choice['item_id'],'instructions':'Three consecutive intervention opportunities; intervening turns are not additional rated actions. Truth is offline reviewer material, never an actor observation. Missing support must be marked uncertain.',
                  'catalog':body['catalog'],'window':anonymize(window,mapping)}
            items.append(item)
    items=sorted(items,key=lambda x:next(i for i,r in enumerate(selected) if r['item_id']==x['item_id']))
    path=reviewer/'items.json';old=read(path) if path.exists() else None
    if old is not None and old!=items:raise ValueError('Packet would change existing identities/content')
    write(path,items);write(private/'mapping.json',selected)
    for rater in (1,2):blank_ratings(reviewer/f'rater_{rater}.csv',items)
    text=['# Exploration trajectory review','', 'Use CODEBOOK.md. Rate independently; do not infer unseen intentions. Condition identities and biographies have been removed, but cast size, routing and behavior may reveal experimental structure. Actual outputs are preserved apart from consistent speaker anonymization.','']
    for item in items:
        text.extend(['## '+item['item_id'],'','```json',json.dumps(item,indent=2,ensure_ascii=False),'```',''])
    (reviewer/'PACKET.md').write_text('\n'.join(text))
    (reviewer/'CODEBOOK.md').write_text((HERE/'CODEBOOK.md').read_text())
    annotations={}
    for rater in (1,2):
        with (reviewer/f'rater_{rater}.csv').open() as f:
            annotations[str(rater)]=sum(any(v.strip() for k,v in row.items() if k!='item_id') for row in csv.DictReader(f))
    manifest={'items':len(items),'classification':'Outcome-independent semantic-review sample, final mechanism pilot only; human ratings pending',
        'selection':selected,'reviewer_directory':str(reviewer.relative_to(ROOT)),'private_directory':str(private.relative_to(ROOT)),
        'reviewer_files':{p.name:sha256(p) for p in sorted(reviewer.iterdir()) if p.is_file()},
        'private_mapping_sha256':sha256(private/'mapping.json'),'source_hashes':source_hashes,'annotation_rows':annotations,
        'blinding_limits':'Identifying metadata, semantic role labels and biographies removed. Actor count, routing, recurrent wording and actual behavior can still reveal condition. Truth annotations are visible only to reviewers.',
        'maximum_action_window':3,'per_condition_items':8,'worlds_per_condition':{'authorized':4,'hypothetical':4},
        'condition_and_seed_labels_hidden':True}
    # Selection mapping is private, so only its hash/count is published in compact manifest.
    manifest.pop('selection');write(REPORTS/'HUMAN_REVIEW_MANIFEST.json',manifest)
    print({'items':len(items),'annotations':annotations})

if __name__=='__main__':main()
