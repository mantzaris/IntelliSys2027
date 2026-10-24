"""Deterministic, one-seed exploratory analyses; no partially written runs."""
from collections import Counter,defaultdict
import json
import numpy as np
from pcc.environment import make_family,score
from pcc.resources import sha256
from .common import ROOT,HERE,ARTIFACTS,RESULTS,read,write,write_csv,stable_rows,record_source
from .fresh import family
from .audit import coordination


def interval(values):
    values=np.asarray(values,dtype=float)
    if not len(values):return [None,None]
    rng=np.random.default_rng(40721)
    boot=values[rng.integers(0,len(values),size=(10000,len(values)))].mean(axis=1)
    return [float(x) for x in np.quantile(boot,[.025,.975])]


def pairs(rows):
    grouped=defaultdict(dict)
    for row in rows:
        key=row['family_id'];world=row['world']
        if world in grouped[key]:raise ValueError('Duplicate family/world final')
        grouped[key][world]=row['success']
    if any(set(v)!={'authorized','hypothetical'} for v in grouped.values()):raise ValueError('Incomplete pair')
    return {k:float(all(v.values())) for k,v in grouped.items()}


def contrast(left,right,label):
    assert left.keys()==right.keys()
    differences=[left[k]-right[k] for k in sorted(left)]
    lo,hi=interval(differences)
    return {'contrast':label,'families':len(differences),'paired_difference':float(np.mean(differences)),
            'ci95_low':lo,'ci95_high':hi,'uncertainty':'Family bootstrap; fixed seed17, no training-seed variance estimate'}


def scored(row,scenario):
    turn=row.get('turn',len(scenario.messages));truth=scenario.truth_at(turn);gold=truth.target(scenario.spec)
    body=json.loads(row['prompt'][-1]['content']);sources=body['sources'];visible={m['index'] for m in sources}
    parsed=row['generation']['parsed'];plan=parsed.get('plan',[])
    if not isinstance(plan,list):plan=[]
    switch=scenario.events[scenario.switch_turn-1].updates[0]
    slot,alternate=switch
    metric=score(parsed,truth,scenario.spec,visible)
    return {'family_id':scenario.family_id,'world':scenario.world,'domain':scenario.spec.domain,'heldout_rule':scenario.spec.online_override,
            'ambiguity':bool(truth.pending),**metric,'dependency_error':metric['dependency_accuracy']<1,
            'authorized_update_correct':int(slot<len(plan) and plan[slot]==alternate) if scenario.world=='authorized' else None,
            'false_hypothetical_update':int(slot<len(plan) and plan[slot]==alternate) if scenario.world=='hypothetical' else None,
            'all_canonical_sources_visible':all(i is None or i in visible for i in gold['evidence']),
            'canonical_sources_missing':sum(i is not None and i not in visible for i in gold['evidence']),
            'source_count':len(sources),'assistant_source_count':sum(m['author']=='assistant' for m in sources),
            'user_source_count':sum(m['author']=='user' for m in sources),
            'input_tokens':row['generation']['input_tokens'],'output_tokens':row['generation']['output_tokens']}


def summarize(rows,**labels):
    paired=pairs(rows);lo,hi=interval(list(paired.values()))
    result={**labels,'families':len(paired),'conversations':len(rows),'paired_successes':int(sum(paired.values())),
            'paired_success':float(np.mean(list(paired.values()))),'ci95_low':lo,'ci95_high':hi}
    for key in ('success','plan_accuracy','recall_accuracy','evidence_accuracy','dependency_error','authorized_update_correct',
                'false_hypothetical_update','all_canonical_sources_visible','source_count','assistant_source_count','user_source_count','input_tokens','output_tokens'):
        values=[r[key] for r in rows if r.get(key) is not None]
        result[key+'_mean']=float(np.mean(values)) if values else None
    return result


def main():
    inputs={};memory=[];replays=[];deltas=[];strata=[];goals=[];routes=[];balanced=[];severity=[]
    stage_status={};groups={}
    allocation=read(ARTIFACTS/'allocation.json') if (ARTIFACTS/'allocation.json').exists() else None
    controller=read(ARTIFACTS/'controller_state.json') if (ARTIFACTS/'controller_state.json').exists() else {}
    for stage in ('memory','conflict','routing','severity','balanced'):
        run=ROOT/f'artifacts/runs/review001-{stage}-17-v1';status=run/'status.json'
        if not status.exists() or read(status)['status']!='completed':
            state='pending' if not status.exists() else read(status)['status']
            if not status.exists() and allocation is not None and stage not in allocation['stages']:state='not_executed_resource_gate'
            elif not status.exists() and controller.get('status')=='not_executed_budget_gate':state='not_executed_resource_gate_before_profile'
            elif not status.exists() and controller.get('status')=='review_incomplete':state='pending_after_recorded_failure'
            stage_status[stage]=state;continue
        record_source(inputs,status);stage_status[stage]='completed'
        if stage=='memory':
            for path in sorted(run.glob('*.jsonl')):
                if path.stem.split('-')[0] not in {'base','C1','C3','C5'}:continue
                condition,variant=path.stem.split('-',1);rows=[];agreement=Counter();saved=[]
                for row in stable_rows(path,inputs):
                    scenario=next(s for s in make_family('test',int(row['family_id'].split('-')[-1]),64) if s.world==row['world'])
                    metrics=scored(row,scenario);rows.append(metrics)
                    if variant=='A0':
                        agreement['raw_equal']+=row['saved_answer']==row['generation']['raw']
                        agreement['parsed_equal']+=row['saved_parsed']==row['generation']['parsed']
                        agreement['plan_equal']+=row['saved_parsed'].get('plan')==row['generation']['parsed'].get('plan')
                        agreement['input_token_equal']+=row['saved_input_tokens']==row['generation']['input_tokens']
                        saved_metric=score(row['saved_parsed'],scenario.truth_at(64),scenario.spec)
                        saved.append({'family_id':row['family_id'],'world':row['world'],'success':saved_metric['success']})
                assert allocation is not None and len(rows)==2*allocation['families']
                assert {r['family_id'] for r in rows}=={f'test-{n:04d}' for n in allocation['selected_families']}
                key=condition,variant;groups[key]=rows;memory.append(summarize(rows,condition=condition,variant=variant))
                write(ARTIFACTS/f'analysis/{condition}-{variant}-metrics.json',rows)
                record_source(inputs,ARTIFACTS/f'analysis/{condition}-{variant}-metrics.json')
                for dimension in ('domain','heldout_rule','ambiguity'):
                    for level in sorted({r[dimension] for r in rows},key=str):
                        strata.append(summarize([r for r in rows if r[dimension]==level],condition=condition,variant=variant,stratum=dimension,level=level))
                if variant=='A0':
                    delta=contrast(pairs(rows),pairs(saved),'A0-minus-saved')
                    replays.append({'condition':condition,'conversations':len(rows),**agreement,**delta,
                       'source_adapter_schema_versions_checked':True,
                       'material_discrepancy':1-agreement['parsed_equal']/len(rows)>.01 or abs(delta['paired_difference'])>.01,
                       'interpretation':'If material: inspect exact input bytes, frozen schema and versions, adapter hashes and batching offsets before interpreting removal contrasts. No cases excluded.'})
            for c in ('C1','C3','C5'):
                for v in ('A1','A2'):deltas.append(contrast(pairs(groups[c,v]),pairs(groups[c,'A0']),f'{c}:{v}-A0'))
            if ('C5','common') in groups:
                for c in ('base','C1','C3'):deltas.append(contrast(pairs(groups['C5','common']),pairs(groups[c,'common']),f'common:C5-{c}'))
        elif stage in ('conflict','routing'):
            conditions=('B0','B1','B2','B3') if stage=='conflict' else ('C-single','C-peer','C-off')
            behavior={}
            for condition in conditions:
                actions=list(stable_rows(run/(condition+'_characters.jsonl'),inputs));counts=Counter();last={}
                assert len(actions)==16*2*12
                assert len({(a['family_id'],a['world'],a['turn']) for a in actions})==len(actions)
                for a in actions:
                    counts['actions']+=1;counts['kind_'+a['kind']]+=1;counts['applied']+=a['applied'];counts['rejected_or_no_delivery']+=not a['applied']
                    counts['reserved_opportunities']+=a['communication_slot'];counts['direct_opportunities']+=not a['communication_slot']
                    counts['direct_notes_to_jekyll']+=a['kind']=='peer' and a['applied'] and a.get('target')=='Jekyll'
                    counts['preferred_option_adoptions']+=a['owned_option_adopted'];counts['incompatible_goal_exposures']+=a['incompatible_goal_exposure']
                    for flag in ('memory_changed','contradictory_edit_with_source_access','false_commitment_candidate','truthful_disclosure_candidate','user_alignment_current'):
                        counts[flag]+=bool(a.get(flag))
                    key=a['family_id'],a['world'],a['actor'];previous=last.get(key)
                    if previous:
                        counts['within_actor_transitions']+=1
                        counts['same_slot_value_repetitions']+=(a.get('slot'),a.get('value'))==(previous.get('slot'),previous.get('value'))
                        counts['action_kind_changes']+=a['kind']!=previous['kind']
                    last[key]=a
                behavior[condition]={}
                for flag in ('owned_option_adopted','memory_changed','contradictory_edit_with_source_access'):
                    by_family=defaultdict(list)
                    for a in actions:by_family[a['family_id']].append(float(a.get(flag,False)))
                    behavior[condition][flag]={k:float(np.mean(v)) for k,v in by_family.items()}
                coord,_=coordination(actions)
                result={'condition':condition,'families':16,'conversations':32,**counts,**coord,
                        'qualification':'Behavioral associations and lexical flags; semantic coordination/intent pending blinded human review'}
                (goals if stage=='conflict' else routes).append(result)
            comparison_set=[('B1','B0'),('B2','B1'),('B3','B1')] if stage=='conflict' else [('C-peer','C-single'),('C-off','C-peer')]
            for left,right in comparison_set:
                for flag in ('owned_option_adopted','memory_changed','contradictory_edit_with_source_access'):
                    deltas.append(contrast(behavior[left][flag],behavior[right][flag],f'{stage}:{left}-{right}:{flag}'))
        elif stage=='balanced':
            bgroups={}
            for c in ('C1','C3','C5'):
                rows=[];turns=set()
                for row in stable_rows(run/(c+'.jsonl'),inputs):
                    turns.add((row['family_id'],row['world'],row['turn']))
                    if row['turn']!=64:continue
                    s=next(s for s in family('balanced',int(row['family_id'].split('-')[-1]),64) if s.world==row['world'])
                    rows.append(scored(row,s))
                assert len(turns)==64*2*64 and len(rows)==64*2
                bgroups[c]=rows;balanced.append(summarize(rows,condition=c))
            for c in ('C1','C3'):deltas.append(contrast(pairs(bgroups['C5']),pairs(bgroups[c]),f'fresh-balanced:C5-{c}'))
        elif stage=='severity':
            by_state=defaultdict(dict)
            for row in stable_rows(run/'severity.jsonl',inputs):
                s=next(s for s in make_family('train',int(row['family_id'].split('-')[-1]),16) if s.world==row['world'])
                by_state[row['family_id'],row['world'],row['turn']][row['action_condition']]=scored(row,s)
            assert len(by_state)==16*2*2 and all(set(v)=={'none','C3','C5'} for v in by_state.values())
            for c in ('C3','C5'):
                correct=[v for v in by_state.values() if v['none']['success']]
                severity.append({'condition':c,'states':len(by_state),'reference_correct':len(correct),'reference_incorrect':len(by_state)-len(correct),
                  'correct_to_incorrect':sum(not v[c]['success'] for v in correct),
                  'reference_incorrect_to_correct':sum(not v['none']['success'] and v[c]['success'] for v in by_state.values()),
                  'qualification':'Same-state interventions with fresh no-action reference; actions were originally produced on their own collection histories. Not a curriculum severity-matching correction.'})
    for name,rows in [('memory_dependence',memory),('replay_agreement',replays),('paired_contrasts',deltas),('memory_strata',strata),('goal_conflict',goals),('routing_control',routes),('balanced_validation',balanced),('severity_replay',severity)]:
        write(RESULTS/(name+'.json'),rows);write_csv(RESULTS/(name+'.csv'),rows)
    write(RESULTS/'supplement_status.json',stage_status)
    record_source(inputs,HERE/'analyze.py')
    write(RESULTS/'supplement_provenance.json',{'inputs':inputs,'stage_status':stage_status,'uncertainty':'Fixed seed17; family bootstrap only; all new evidence exploratory'})


if __name__=='__main__':main()
