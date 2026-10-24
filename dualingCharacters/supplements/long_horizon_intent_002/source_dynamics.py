"""Exploratory temporal source/memory audit prompted by observed trajectory curves.

Gold source annotations characterize saved inputs AFTER generation. They never
select policy inputs or change the frozen retriever, memory, or scores.
"""
from collections import Counter,defaultdict
from pathlib import Path
import json
from pcc.environment import make_family
from pcc.resources import sha256
from supplements.review_001.common import stream,trace_path,write_csv
from .common import ROOT,REPORTS,ARTIFACTS,read,write,utc,log


def describe(row,scenario):
    turn=row['turn'];body=json.loads(row['prompt'][-1]['content']);truth=scenario.truth_at(turn);previous=scenario.truth_at(turn-1)
    target=truth.target(scenario.spec)
    if row['target']!=target:raise ValueError('Time-specific target mismatch')
    visible={m['index'] for m in body['sources']};canonical={x for x in truth.evidence if x is not None};updates={x for x in canonical if x!=1}
    memory=body['memory']['state'];prediction=row['generation']['parsed'].get('state');event=scenario.events[turn-1]
    unchanged=truth.values==previous.values
    return {'family_id':row['family_id'],'world':row['world'],'turn':turn,'event_kind':event.kind,
      'success':row['metrics']['success'],'recall_correct':prediction==truth.values,
      'all_canonical_visible':canonical<=visible,'canonical_sources_total':len(canonical),'canonical_sources_visible':len(canonical&visible),
      'has_active_revisions':bool(updates),'all_active_revision_sources_visible':bool(updates) and updates<=visible,
      'none_active_revision_sources_visible':bool(updates) and not bool(updates&visible),
      'initial_source_visible':1 in visible,'memory_correct_for_current_truth':memory==truth.values,
      'memory_correct_for_previous_truth':memory==previous.values,'truth_values_unchanged':unchanged,
      'valid_memory_lost_without_user_change':unchanged and memory==truth.values and prediction!=truth.values,
      'stale_initial_state_returned':truth.values!=scenario.truth_at(1).values and prediction==scenario.truth_at(1).values,
      'repaired_incorrect_memory':memory!=truth.values and prediction==truth.values,
      'input_tokens':row['generation']['input_tokens'],'output_tokens':row['generation']['output_tokens'],
      'generation_capped':row['generation'].get('generation_capped',False),'source_messages':len(body['sources']),
      'assistant_sources':sum(m['author']=='assistant' for m in body['sources'])}


def audit(run_id):
    run=ROOT/'artifacts/runs'/run_id;status=read(run/'status.json');source=trace_path(run/'evaluation.jsonl');cache=ARTIFACTS/'source_dynamics'/f'{run_id}.json'
    signature=[sha256(run/'status.json'),source.stat().st_size,source.stat().st_mtime_ns]
    if cache.exists() and read(cache)['signature']==signature:return read(cache)
    if status['status']!='completed' or run_id==(read(ROOT/'artifacts/campaign_state.json').get('active_job') or {}).get('id'):raise ValueError('Only immutable complete runs')
    scenarios={(s.family_id,s.world):s for n in range(240) for s in make_family('test',n,64)}
    turns=defaultdict(Counter);strata=defaultdict(Counter);selected=[];seen=set()
    for row in stream(source):
        k=row['family_id'],row['world'],row['turn']
        if k in seen:raise ValueError('Duplicate source-dynamics observation')
        seen.add(k);r=describe(row,scenarios[k[:2]]);counter=turns[r['turn']];counter['conversations']+=1
        for name,value in r.items():
            if isinstance(value,bool):counter[name]+=value
            elif name in ('input_tokens','output_tokens','source_messages','assistant_sources'):counter[name+'_sum']+=value
        for kind,level in [('canonical_visibility',r['all_canonical_visible']),('memory_current_correct',r['memory_correct_for_current_truth']),('revision_sources_visible',r['all_active_revision_sources_visible'])]:
            v=strata[kind,str(level),r['event_kind']];v['observations']+=1;v['successes']+=r['success'];v['correct_recall']+=r['recall_correct'];v['stale_initial_state']+=r['stale_initial_state_returned']
        # Fixed lowest-ID family example, selected independently of outcome.
        if r['family_id']=='test-0000' and r['turn'] in (32,40,60,61,64):
            body=json.loads(row['prompt'][-1]['content']);selected.append({**r,'memory_before':body['memory'],'actual_output':row['generation']['parsed'],'target':row['target'],
              'current_user_message':scenarios[k[:2]].messages[r['turn']-1].text,'visible_sources':body['sources']})
    if len(seen)!=30720:raise ValueError('Incomplete source-dynamics coverage')
    cfg=status['config'];header={'run_id':run_id,'model':cfg['model'],'condition':cfg['condition'],'seed':cfg['seed']}
    result={'signature':signature,'metadata':header,'turns':[{'turn':turn,**v} for turn,v in sorted(turns.items())],
      'strata':[{'factor':kind,'level':level,'event_kind':event,**v} for (kind,level,event),v in strata.items()],
      'fixed_lowest_id_examples':selected,'raw_sha256':sha256(source),'analysis_sha256':sha256(Path(__file__)),'validated_utc':utc()}
    write(cache,result);log('New temporal source/memory audit: '+run_id+'; descriptive response to observed curves, not a changed policy or causal intervention.');return result


def main():
    rows=[];strata=[];inputs={};snapshots=[]
    for path in sorted((ARTIFACTS/'core_trajectory').glob('*.json')):
        meta=read(path)['metadata']
        if meta['model']!='qwen' or meta['condition'] not in ('C1','C3','C5'):continue
        result=audit(meta['run_id']);rows.extend({**meta,**r} for r in result['turns']);strata.extend({**meta,**r} for r in result['strata'])
        inputs[meta['run_id']]={'raw_sha256':result['raw_sha256'],'analysis_sha256':result['analysis_sha256']}
        snapshots.extend({**meta,**r} for r in result['turns'] if r['turn'] in (1,16,32,40,56,60,61,62,63,64))
    write(REPORTS/'source_dynamics_by_turn.json',rows);write_csv(REPORTS/'source_dynamics_by_turn.csv',rows)
    write(REPORTS/'source_dynamics_strata.json',strata);write_csv(REPORTS/'source_dynamics_strata.csv',strata)
    write(REPORTS/'source_dynamics_selected_turns.json',snapshots);write_csv(REPORTS/'source_dynamics_selected_turns.csv',snapshots)
    write(REPORTS/'source_dynamics_provenance.json',{'generated_utc':utc(),'inputs':inputs,
      'chronology':'Added after inspecting new dynamic-oracle curves and fixed lowest-ID example at approximately14:23UTC on2026-10-24. Post-result exploratory analysis.',
      'interpretation':'Associations among source coverage, memory and correctness. Legitimate user updates are distinguished. No causal effect of retrieval or memory is identified; no policy inputs are selected by annotations.'})
    print({'runs':len(inputs),'actual_turns_characterized':len(inputs)*30720,'gpu_calls':0})


if __name__=='__main__':main()
