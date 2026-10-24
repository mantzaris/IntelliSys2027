"""Stream only completed, eligible artifacts; keep pilots and main runs separate."""
from collections import Counter,defaultdict
import json
from pcc.analysis import paired_success
from pcc.environment import make_family,score
from pcc.characters import cast
from pcc.freeze import verify_freeze
from pcc.eligibility import exclusions
from pcc.resources import sha256,used_seconds
from .common import ROOT,HERE,RESULTS,ARTIFACTS,read,write,write_csv,stable_rows,trace_path,identity,record_source,eligible_runs,require_completed


def coordination(actions):
    by_episode=defaultdict(list)
    for a in actions:by_episode[identity(a)].append(a)
    messages=[];directed=Counter();matches=0;reversals=0
    for key,episode in by_episode.items():
        for a in episode:
            if a['kind']!='peer' or not a['applied'] or a.get('target')=='Jekyll':continue
            later=[b for b in episode if b['actor']==a.get('target') and b['turn']>a['turn']]
            match=next((b for b in later[:2] if b['kind'] in {'edit','recollect','propose'} and
                        b.get('slot')==a.get('slot') and b.get('value')==a.get('value') and a.get('value') is not None),None)
            if match:
                matches+=1;directed[*key,a['actor'],a['target']]+=1
                reversals+=any(b['turn']>match['turn'] and b['kind'] in {'edit','recollect','propose'} and
                               b.get('slot')==a.get('slot') and b.get('value')!=a.get('value') for b in later)
            messages.append({'action':a,'followups':later[:2],'typed_match':bool(match)})
    return {'delivered_antagonist_peer_messages':len(messages),'typed_matching_followups':matches,
            'repeated_directed_coordination_candidates':sum(v>=2 for v in directed.values()),
            'echoed_option_reversals':reversals},messages


def evaluation(run,meta,inputs):
    summaries=read(run/'evaluation_summary.json');record_source(inputs,run/'evaluation_summary.json')
    horizon=summaries[0]['horizon'];finals=[];seen=set();count=0;canonical_all=0
    failures=dependency_failures=recalled_failures=0;strata=defaultdict(list)
    for row in stable_rows(run/'evaluation.jsonl',inputs):
        key=(*identity(row),row['turn'])
        if key in seen:raise ValueError('Duplicate evaluation row')
        seen.add(key);count+=1
        if row['turn']!=horizon:continue
        scenario=next(s for s in make_family(row['split'],int(row['family_id'].split('-')[-1]),horizon) if s.world==row['world'])
        truth=scenario.truth_at(horizon);target=truth.target(scenario.spec)
        if row['target']!=target:raise ValueError('Stored target differs from independent frozen oracle')
        body=json.loads(row['prompt'][-1]['content']);visible={m['index'] for m in body['sources']}
        metrics=score(row['generation']['parsed'],truth,scenario.spec,visible)
        for key in ('success','recall_accuracy','dependency_accuracy'):
            if row['metrics'][key]!=metrics[key]:raise ValueError('Saved score differs from recomputation')
        canonical_all+=all(i is None or i in visible for i in target['evidence'])
        failures+=not metrics['success'];dependency_failures+=not metrics['success'] and metrics['dependency_accuracy']<1
        recalled_failures+=not metrics['success'] and metrics['recall_accuracy']==1
        short={'seed':meta['config']['seed'],'family_id':row['family_id'],'world':row['world'],'success':metrics['success']}
        finals.append(short);strata[scenario.spec.online_override].append(short)
    assert count==len(summaries)*horizon and len(finals)==len(summaries)
    paired=paired_success(finals)
    return {'run_id':run.name,'condition':meta['config']['condition'],'model':meta['config']['model'],'seed':meta['config']['seed'],
            'families':len(paired),'paired_successes':sum(paired.values()),'conversations':len(finals),'failed_conversations':failures,
            'failed_with_dependency_error':dependency_failures,'failed_with_correct_recall':recalled_failures,
            'all_canonical_sources_visible':canonical_all,'final_prompts':len(finals),'raw_rows':count,
            **{('heldout' if flag else 'familiar')+'_paired_successes':sum(paired_success(rows).values()) for flag,rows in strata.items()},
            **{('heldout' if flag else 'familiar')+'_families':len(paired_success(rows)) for flag,rows in strata.items()}}


def action_audit(run,meta,inputs,prefix='collection',evidence_class='main'):
    path=trace_path(run/(prefix+'_characters.jsonl'))
    if not path.exists():return [],None
    actions=list(stable_rows(path,inputs));slots=defaultdict(Counter)
    for a in actions:
        group=slots['reserved' if a['communication_slot'] else 'direct_opportunity']
        group['opportunities']+=1;group['kind_'+a['kind']]+=1
        group['applied']+=a['applied'];group['rejected_or_undelivered']+=not a['applied']
        group['direct_peer_notes_to_jekyll']+=a['kind']=='peer' and a['applied'] and a.get('target')=='Jekyll'
        group['antagonist_recipient_deliveries']+=a['kind']=='peer' and a['applied'] and a.get('target')!='Jekyll'
        group['source_visible_contradiction_flags']+=a.get('contradictory_edit_with_source_access',False)
        group['shared_memory_changed']+=a.get('memory_changed',False)
    coord,_=coordination(actions)
    return [{'run_id':run.name,'condition':meta['config']['condition'] if prefix=='collection' else prefix,
             'seed':meta['config']['seed'],'evidence_class':evidence_class,'slot_type':kind,**counts} for kind,counts in slots.items()],coord


def collection(run,meta,inputs):
    counts=read(run/'supervision.counts.json');record_source(inputs,run/'supervision.counts.json')
    windows=list(stable_rows(run/'supervision.jsonl',inputs));labels=Counter(w['label_source'] for w in windows)
    clean=[w for w in windows if w['metrics']['success']];failed=[w for w in windows if not w['metrics']['success']]
    assert len(clean)==counts['clean_valid'] and len(failed)==counts['failed_eligible']
    action_path=trace_path(run/'collection_characters.jsonl')
    actions={(*identity(a),a['turn']):a for a in stable_rows(action_path,inputs)} if action_path.exists() else {}
    previous={};assoc=Counter();note_prompts=note_survival=note_comparisons=rows=0
    for row in stable_rows(run/'collection.jsonl',inputs):
        rows+=1;key=identity(row);before=previous.get(key)
        body=json.loads(row['prompt'][-1]['content']);notes=body['memory']['notes'];note_prompts+=bool(notes)
        encoded={json.dumps(x,sort_keys=True) for x in notes}
        if before:
            note_comparisons+=len(before['notes']);note_survival+=len(before['notes']&encoded)
            action=actions.get((*key,row['turn']))
            if action and action['kind'] in {'edit','propose','recollect'}:
                assoc['direct_actions']+=1
                if before['success']:
                    assoc['previous_turn_correct']+=1;assoc['following_failure']+=not row['metrics']['success']
                    changed=before['state']!=row['target']['state']
                    assoc['previous_correct_with_user_state_change']+=changed
                    assoc['following_failure_with_user_state_change']+=changed and not row['metrics']['success']
        previous[key]={'success':row['metrics']['success'],'notes':encoded,'state':row['target']['state']}
    return {'run_id':run.name,'model':meta['config']['model'],'condition':meta['config']['condition'],'seed':meta['config']['seed'],
            **counts,'eligible_windows':len(windows),'eligible_families':len({w['family_id'] for w in windows}),
            'eligible_failed_families':len({w['family_id'] for w in failed}),'label_sources':dict(labels),
            'defender_prompts':rows,'prompts_with_persistent_notes':note_prompts,'note_retention_comparisons':note_comparisons,
            'notes_retained_next_prompt':note_survival,'observational_severity':dict(assoc),
            'qualification':'Following failures are temporal associations, not causal effects; a genuine user update can intervene. Loaded supervision is not actual loss exposure.'}


def main():
    frozen=verify_freeze(ROOT);inputs={};evals=[];collections=[];routing=[];coordinates=[]
    excluded=exclusions(ROOT)
    for name in ('configs/freeze.json','configs/run_exclusions.json','src/pcc/characters.py','src/pcc/environment.py','src/pcc/training.py'):
        record_source(inputs,ROOT/name)
    # One streaming pass per immutable trace. This audit never opens a running run.
    candidates=[require_completed('base-qwen-eval'),*eligible_runs('evaluate')]
    for run,meta in candidates:
        if meta.get('horizon')!=64:continue
        record_source(inputs,run/'status.json');evals.append(evaluation(run,meta,inputs))
    for run,meta in eligible_runs('collect'):
        record_source(inputs,run/'status.json');collections.append(collection(run,meta,inputs))
        rows,coord=action_audit(run,meta,inputs);routing+=rows
        if coord:coordinates.append({'run_id':run.name,'evidence_class':'main',**coord})
    pilot,meta=require_completed('mechanism-final-001')
    for condition in ('C4','C5'):
        rows,coord=action_audit(pilot,meta,inputs,condition,'frozen-policy pilot');routing+=rows
        coordinates.append({'run_id':pilot.name,'condition':condition,'evidence_class':'frozen-policy pilot',**coord})
    severity_run,sm=require_completed('pilot-severity-001');severity=defaultdict(Counter)
    for row in stable_rows(severity_run/'severity.jsonl',inputs):
        group=severity[row['condition']];group['actions_replayed']+=1
        group['reference_correct']+=row['before_success'];group['correct_to_incorrect']+=row['success_to_failure']
    forecasts=read(ROOT/'reports/tables/serialization_budget_reforecast.json');record_source(inputs,ROOT/'reports/tables/serialization_budget_reforecast.json')
    ambiguous=[]
    for n in range(240):
        scenario=make_family('test',n,64)[0]
        if scenario.truth_at(64).pending:ambiguous.append({'family_id':scenario.family_id,'domain':scenario.spec.domain,'heldout_rule':scenario.spec.online_override})
    casts=[cast('C5',f'train-{n:04d}',seed) for n in range(300) for seed in (17,29,43)]
    distinct=sum(len({a.slot for a in actors})==len(actors) for actors in casts)
    c1=next(r for r in evals if r['run_id']=='main-qwen-c1-17-eval-format2');base=next(r for r in evals if r['run_id']=='base-qwen-eval')
    cp=next(r for r in coordinates if r['run_id']=='mechanism-final-001' and r.get('condition')=='C5')
    refresh=next(r for r in collections if r['run_id']=='main-qwen-c1-17-r1-collect-format2')
    findings=[('paired_success',[c1['paired_successes'],base['paired_successes']],[186,67]),
              ('rule_strata',[c1['familiar_paired_successes'],c1['heldout_paired_successes']],[117,69]),
              ('failed_dependency_recall',[c1['failed_conversations'],c1['failed_with_dependency_error'],c1['failed_with_correct_recall']],[90,80,81]),
              ('canonical_source_visibility',c1['all_canonical_sources_visible'],471),
              ('distinct_owned_slots',[distinct,len(casts)],[900,900]),
              ('final_c5_peer_diagnostics',[cp['delivered_antagonist_peer_messages'],cp['typed_matching_followups'],cp['repeated_directed_coordination_candidates']],[64,0,0]),
              ('ambiguity_confounded',[len(ambiguous),all(x['domain']=='creative' and x['heldout_rule'] for x in ambiguous)],[30,True]),
              ('historical_severity',[severity['C3']['correct_to_incorrect'],severity['C3']['reference_correct'],severity['C5']['correct_to_incorrect'],severity['C5']['reference_correct']],[50,243,10,241]),
              ('c1_refresh_failed_pool',refresh['failed_eligible'],14),
              ('amended_forecast_rounded',round(forecasts['total_core_forecast_hours'],2),92.74)]
    checks=[{'finding':name,'observed':value,'review_snapshot':expected,'status':'verified' if value==expected else 'discrepancy'} for name,value,expected in findings]
    write(RESULTS/'review_findings.json',checks);write(RESULTS/'main_recomputed.json',evals);write_csv(RESULTS/'main_recomputed.csv',evals)
    write(RESULTS/'collection_audit.json',collections);write(RESULTS/'communication_routing.json',routing);write_csv(RESULTS/'communication_routing.csv',routing)
    write(RESULTS/'coordination.json',coordinates);write(RESULTS/'historical_severity.json',dict(severity));write(RESULTS/'ambiguity_confound.json',ambiguous)
    record_source(inputs,HERE/'audit.py');record_source(inputs,HERE/'common.py')
    write(RESULTS/'cpu_provenance.json',{'classification':'Post-C1 exploratory audit; no new model calls','frozen_files_verified':len(frozen['files']),
          'inputs':inputs,'excluded_runs_not_pooled':excluded,'actual_reserved_gpu_hours':used_seconds(ROOT/'artifacts/run_registry.jsonl')/3600,
          'pilot_qualification':'Historical mechanism/severity pilots use frozen policies and prior protocols; they are not main training estimates.'})
    print(json.dumps({'findings':checks,'completed_evaluations_audited':len(evals),'completed_collections_audited':len(collections)},indent=2))


if __name__=='__main__':main()
