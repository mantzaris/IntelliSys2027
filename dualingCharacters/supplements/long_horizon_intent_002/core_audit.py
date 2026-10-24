"""Incremental CPU audits against the time-varying oracle; no model calls."""
from collections import Counter,defaultdict
from pathlib import Path
import gzip
import json
import statistics
from pcc.environment import make_family,score,FIELDS
from pcc.resources import sha256
from supplements.review_001.common import stream,trace_path,write_csv
from .common import ROOT,HERE,REPORTS,ARTIFACTS,read,write,utc,log


def clarification(prediction,target):
    raw=prediction.get('clarify'); malformed=not isinstance(raw,list) or any(not isinstance(x,str) for x in raw)
    predicted=set(raw) if not malformed else set();expected=set(target['clarify'])
    extra=predicted-expected;missed=expected-predicted
    plan=prediction.get('plan');plan=plan if isinstance(plan,list) else []
    nonpending=[i for i,name in enumerate(FIELDS) if name not in expected]
    settled_nulls=sum(i>=len(plan) or plan[i] is None for i in nonpending)
    return {'clarification_error':raw!=target['clarify'],'unnecessary_clarification':bool(extra),
      'missed_necessary_clarification':bool(missed),'wrong_issue_clarification':bool(expected and extra),
      'malformed_clarification':malformed,'order_or_duplicate_only':not malformed and predicted==expected and raw!=target['clarify'],
      'extra_issues':sorted(extra),'missed_issues':sorted(missed),'settled_null_decisions':settled_nulls,
      'unnecessary_clarification_with_settled_nulls':bool(extra and settled_nulls),
      'clarification_with_otherwise_correct_plan':bool(predicted and plan==target['plan']),
      'necessary_clarification_preserves_settled_values':bool(expected and expected<=predicted and all(i<len(plan) and plan[i]==target['plan'][i] for i in nonpending))}


def reference_audit(prediction,scenario,turn,sources):
    gold=scenario.truth_at(turn).target(scenario.spec);refs=prediction.get('evidence');refs=refs if isinstance(refs,list) else []
    visible={m['index']:m for m in sources};events={m.index:(m,e) for m,e in zip(scenario.messages[:turn],scenario.events[:turn])}
    records=[]
    for slot,canonical in enumerate(gold['evidence']):
        ref=refs[slot] if slot<len(refs) else None
        exists=isinstance(ref,int) and not isinstance(ref,bool) and (ref==0 or ref in events or (ref>0 and ref%2==0 and ref<2*turn))
        visible_ref=isinstance(ref,int) and not isinstance(ref,bool) and ref in visible
        flags={'canonical_mismatch':ref!=canonical,'not_visible':ref is not None and not visible_ref,
          'nonexistent_or_future':ref is not None and not exists,'assistant_authority':bool(exists and ref%2==0),
          'missing_reference':ref is None,'wrong_explicit_user_authorization':False,
          'alternative_unsuperseded_user_authorization':False,'anaphoric_user_reaffirmation_needs_semantic_review':False,
          'user_hypothetical_or_rejected':False,'generic_user_request_not_authorization':False}
        if exists and ref in events and ref!=canonical:
            msg,event=events[ref];updates=dict(event.updates)
            later=[dict(e.updates).get(slot) for m,e in zip(scenario.messages[:turn],scenario.events[:turn]) if m.index>ref and e.kind=='set' and slot in dict(e.updates)]
            if event.kind=='set' and slot in updates:
                flags['alternative_unsuperseded_user_authorization']=updates[slot]==gold['state'][slot] and all(v==gold['state'][slot] for v in later)
                flags['wrong_explicit_user_authorization']=not flags['alternative_unsuperseded_user_authorization']
            elif event.kind=='suggest' and slot in updates and 'retain the decision I approved' in msg.text:
                flags['anaphoric_user_reaffirmation_needs_semantic_review']=True
            elif event.kind in {'consider','reject'} and slot in updates:flags['user_hypothetical_or_rejected']=True
            else:flags['generic_user_request_not_authorization']=True
        records.append({'slot':FIELDS[slot],'reference':ref,'canonical':canonical,**flags})
    return records


def episode_summary(rows):
    rows=sorted(rows,key=lambda r:r['turn']);assert [r['turn'] for r in rows]==list(range(1,len(rows)+1))
    successes=[bool(r['success']) for r in rows];n=len(rows);first=next((i for i,x in enumerate(successes) if x),None)
    transitions=[];failure_spells=[];start=None
    for i,r in enumerate(rows):
        if not r['success'] and start is None:start=i
        if r['success'] and start is not None:
            failure_spells.append({'onset_turn':start+1,'recovered_turn':i+1,'duration_turns':i-start,'right_censored':False,'onset_event':rows[start]['event_kind']});start=None
        if i and successes[i-1] and not successes[i]:transitions.append({'turn':i+1,'event_kind':r['event_kind'],'truth_changed':r['truth_changed'],'ambiguity_started':r['ambiguity_started']})
    if start is not None:failure_spells.append({'onset_turn':start+1,'recovered_turn':None,'duration_turns':n-start,'right_censored':True,'onset_event':rows[start]['event_kind']})
    trailing=0
    for x in reversed(successes):
        if x:break
        trailing+=1
    last=rows[-1]
    return {'family_id':last['family_id'],'world':last['world'],'horizon':n,'initial_success':successes[0],
      'never_aligned':first is None,'first_aligned_turn':None if first is None else first+1,
      'all_turn_success_fraction':sum(successes)/n,'final_quarter_success_fraction':sum(successes[3*n//4:])/(n-3*n//4),
      'final_success':successes[-1],'trailing_failure_turns':trailing,'ever_regressed_after_success':bool(transitions),
      'regressions':transitions,'failure_spells':failure_spells,
      'retained_without_failure_if_initially_correct':all(successes) if successes[0] else None,
      'qualification':'Exact per-turn structured correctness, not qualitative intent or open-ended user alignment. Endogenous errors; no causal disruption estimate.'}


def audit_run(run_id,final_rows):
    run=ROOT/'artifacts/runs'/run_id;path=trace_path(run/'evaluation.jsonl');mark=ARTIFACTS/'core_trajectory'/f'{run_id}.json'
    signature=[path.stat().st_size,path.stat().st_mtime_ns,sha256(run/'status.json')]
    if mark.exists() and read(mark)['signature']==signature:return read(mark)
    meta=read(run/'status.json');assert meta['status']=='completed';assert run_id!=(read(ROOT/'artifacts/campaign_state.json').get('active_job') or {}).get('id')
    cfg=meta['config'];scenarios={(s.family_id,s.world):s for i in range(240) for s in make_family('test',i,64)}
    groups=defaultdict(list);turns=defaultdict(Counter);final_audit=[];seen=set();inputs={str(path.relative_to(ROOT)):sha256(path)}
    for row in stream(path):
        family,world,turn=row['family_id'],row['world'],row['turn'];key=(family,world,turn);assert key not in seen;seen.add(key)
        scenario=scenarios[family,world];truth=scenario.truth_at(turn);target=truth.target(scenario.spec);assert target==row['target']
        pred=row['generation']['parsed'];body=json.loads(row['prompt'][-1]['content']);sources=body['sources']
        metrics=score(pred,truth,scenario.spec,{s['index'] for s in sources});assert metrics==row['metrics']
        previous=scenario.truth_at(turn-1);event=scenario.events[turn-1]
        c=clarification(pred,target)
        entry={'family_id':family,'world':world,'turn':turn,'success':metrics['success'],'recall_correct':metrics['recall_accuracy']==1,
          'dependency_error':metrics['dependency_accuracy']<1,'truth_changed':truth.values!=previous.values,
          'ambiguity_started':bool(truth.pending-previous.pending),'event_kind':event.kind,
          'clarification_error':c['clarification_error'],'unnecessary_clarification':c['unnecessary_clarification'],
          'missed_necessary_clarification':c['missed_necessary_clarification']}
        groups[family,world].append(entry);counter=turns[turn];counter['conversations']+=1
        for k,v in entry.items():
            if isinstance(v,bool):counter[k]+=v
        if turn==64:
            references=reference_audit(pred,scenario,turn,sources)
            final_audit.append({'family_id':family,'world':world,**c,'original_source_error':metrics['evidence_accuracy']<1 or metrics['invalid_evidence']>0,
              'references':references,'source_count':len(sources),'canonical_all_visible':all(i is None or i in {m['index'] for m in sources} for i in target['evidence'])})
    assert len(seen)==30720 and len(groups)==480 and len(final_audit)==480
    episodes=[episode_summary(group) for group in groups.values()]
    header={'run_id':run_id,'model':cfg['model'],'condition':cfg['condition'],'seed':cfg['seed']}
    result={'signature':signature,'metadata':header,'inputs':inputs,'episodes':episodes,'final_audit':final_audit,
      'turns':[{'turn':t,**counter} for t,counter in sorted(turns.items())],
      'validated_utc':utc(),'classification':'New post-result exploratory analysis; original scorer unchanged'}
    write(mark,result);log('New time-varying oracle / clarification / evidence audit: '+run_id+'; 30,720 complete turns, no final-target substitution.');return result


def main():
    records=read(REPORTS/'per_seed_results.json');all_runs=[];clarify=[];evidence=[];trajectory=[];curve=[];provenance={}
    cache=ARTIFACTS/'core_audits/evaluations'
    for path in sorted(cache.glob('*.validation.json')):
        run_id=path.name.removesuffix('.validation.json');final=read(cache/(run_id+'.json'))
        result=audit_run(run_id,final);all_runs.append(result);header=result['metadata'];provenance[run_id]=result['inputs']
        finals=result['final_audit'];clarify.append({**header,'conversations':len(finals),**{k:sum(bool(r[k]) for r in finals) for k in ['clarification_error','unnecessary_clarification','missed_necessary_clarification','wrong_issue_clarification','malformed_clarification','order_or_duplicate_only','unnecessary_clarification_with_settled_nulls','clarification_with_otherwise_correct_plan','necessary_clarification_preserves_settled_values']},
          'qualification':'Flags overlap. Structured clarification fields cannot reveal prose acknowledgments or helpfulness; settled-null behavior is an abandonment proxy, not an inferred motive.'})
        flags=[k for k,v in finals[0]['references'][0].items() if isinstance(v,bool)]
        evidence.append({**header,'conversations':480,'references':2880,'original_source_error_conversations':sum(r['original_source_error'] for r in finals),
          **{k+'_references':sum(ref[k] for r in finals for ref in r['references']) for k in flags},
          **{k+'_conversations':sum(any(ref[k] for ref in r['references']) for r in finals) for k in flags},
          'qualification':'Overlapping structural audit, original scorer unchanged. Anaphoric reaffirmations require semantic review; no automatic rescoring or human validation.'})
        episodes=result['episodes'];spells=[s for r in episodes for s in r['failure_spells']]
        initial=[r for r in episodes if r['initial_success']]
        trajectory.append({**header,'conversations':480,'families':240,'initially_correct':len(initial),
          'never_aligned':sum(r['never_aligned'] for r in episodes),'final_correct':sum(r['final_success'] for r in episodes),
          'mean_all_turn_success':statistics.mean(r['all_turn_success_fraction'] for r in episodes),
          'mean_final_quarter_success':statistics.mean(r['final_quarter_success_fraction'] for r in episodes),
          'mean_trailing_failure_turns':statistics.mean(r['trailing_failure_turns'] for r in episodes),
          'conditional_retained_without_failure':sum(r['retained_without_failure_if_initially_correct'] for r in initial),
          'conditional_retention_denominator':len(initial),'failure_spells':len(spells),'unrecovered_spells':sum(s['right_censored'] for s in spells),
          **{'regressions_after_'+kind:sum(t['event_kind']==kind for r in episodes for t in r['regressions']) for kind in ['set','consider','reject','suggest','ambiguous','filler']},
          'qualification':'Unconditional means over all 480 conversations. Conditional retention is supplementary and selected on initial success. Within-conversation spells are dependent.'})
        curve.extend({**header,**r} for r in result['turns'])
    for name,rows in [('clarification_audit',clarify),('evidence_audit',evidence),('trajectory_summary',trajectory),('trajectory_by_turn',curve)]:
        write(REPORTS/(name+'.json'),rows);write_csv(REPORTS/(name+'.csv'),rows)
    write(REPORTS/'core_intent_audit_provenance.json',{'generated_utc':utc(),'runs':provenance,'source_sha256':sha256(Path(__file__)),'no_gpu_calls':True})
    print({'completed_runs':len(all_runs),'time_indexed_turns':30720*len(all_runs),'new_qualitative_scores':0})


if __name__=='__main__':main()
