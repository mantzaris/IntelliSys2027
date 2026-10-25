"""Frozen descriptive analysis of the locked collections; CPU only."""
from collections import Counter,defaultdict
import gzip
import json
from .common import *
from .records import load_cell,DIRECT
from .sequences import actor_sequences,event_windows,direct
from .peers import reconstruct
from .statistics import paired_worlds,family_rate_rows,all_contrasts

CHANNELS=('edit','recollect','propose','peer_component','peer_answerer','peer_invalid_recipient','pass','malformed','unknown')

def available(action,channel):
    return not action['communication_slot'] if channel in DIRECT else True

def group_counts(rows,keys):
    counts=Counter(tuple(r.get(k) for k in keys) for r in rows)
    return [dict(zip(keys,key),count=n) for key,n in sorted(counts.items(),key=lambda kv:str(kv[0]))]

def matchedness(cells):
    lookup={(c['cohort'],c['condition'],c['seed']):c for c in cells};rows=[]
    for (cohort,condition,seed),first in lookup.items():
        if condition!='C5':continue
        for control in ('C3','A1'):
            second=lookup.get((cohort,control,seed))
            if second is None:continue
            for field in ('family_ids','horizon','schedule','model_revision'):
                if first[field]!=second[field]:raise ValueError('Comparison not matched on '+field)
            shared=first['defender_identity']==second['defender_identity']
            if cohort!='main_refreshed' and not shared:raise ValueError('Purported common defender differs')
            rows.append({'cohort':cohort,'seed':seed,'first':'C5','second':control,'matched_families':len(first['family_ids']),
                'horizon':first['horizon'],'schedule':first['schedule'],'same_defender':shared,
                'qualification':'shared initial defender, divergent subsequent trajectories' if shared else 'condition-specific defender and trajectories; observational'})
    return rows

def episode_metrics(episode,sequences,events,messages):
    """All rate definitions return explicit numerator and denominator."""
    actions=episode['actions'];n=len(actions);result={}
    def add(name,numerator,denominator):result[name]=(int(numerator),int(denominator))
    for channel in CHANNELS:
        count=sum(a['channel']==channel for a in actions)
        add('channel_'+channel,count,n)
        eligible=[a for a in actions if available(a,channel)]
        add('available_channel_'+channel,sum(a['channel']==channel for a in eligible),len(eligible))
    for name,field in [('structurally_valid','valid'),('applied','applied'),('state_changed','state_changed'),('notes_changed','notes_changed')]:
        add(name,sum(a[field] is True for a in actions),sum(a[field] is not None for a in actions))
    add('rejected',sum(a['applied'] is False for a in actions),n)
    add('correct_to_incorrect_state',sum(a['transition']=='correct_to_incorrect' for a in actions),n)
    typed=[a for a in actions if a['goal'] is not None]
    add('following_goal_adoption',sum(a['following_adoption']=='same' for a in typed),len(typed))
    pairs=sequences['pairs'];same=[p for p in pairs if p['same_goal']]
    add('consecutive_direct_goal_repetition',len(same),len(pairs))
    add('strict_own_opportunity_goal_repetition',sum(a['strict_repeated_goals'] for a in sequences['actors']),sum(a['own_adjacent_pairs'] for a in sequences['actors']))
    add('same_goal_channel_change',sum(p['channel_changed'] for p in same),len(same))
    add('same_goal_exact_claim_repeat',sum(p['same_claim'] for p in same),len(same))
    add('same_goal_reference_class_change',sum(p['reference_class_changed'] for p in same),len(same))
    other=[p for p in pairs if p['observed_defender_relation_to_previous_goal']=='different']
    add('repeat_after_observed_other_plan_value',sum(p['same_goal'] for p in other),len(other))
    after_away=[e for e in events if e['event_kind']=='set' and e['side']=='after' and e['alignment_change']=='away_from_owned']
    add('owned_goal_insistence_after_revision',sum(e['insistence_after_revision'] for e in after_away),len(after_away))
    add('owned_goal_endorsement',sum(a['owned_goal_endorsed'] for a in actions),sum(not a['communication_slot'] for a in actions))
    for name in ('reference_unavailable','assistant_reference','explicit_current_support','explicit_superseded_support','explicit_contradiction','nonbinding_mention','other_user_reference','no_reference'):
        add('reference_'+name,sum(a['reference_class']==name for a in actions),n)
    for field in ('current_value_inappropriate_citation','contradictory_value_with_source_visible','canonical_mismatch'):
        add(field,sum(a[field] is True for a in actions),sum(a[field] is not None for a in actions))
    component=[m for m in messages if m['recipient_type']=='component']
    add('component_delivery',sum(m['delivered'] is True for m in component),len(component))
    delivered=[m for m in component if m['delivered'] is True]
    add('component_observed_in_later_inbox',sum(m['visible'] is True for m in delivered),len(delivered))
    visible_typed=[m for m in component if m['visible'] is True and m['goal'] is not None]
    add('visible_typed_next_goal_match',sum(m['next_response']=='same_goal' for m in visible_typed),len(visible_typed))
    comparable=[m for m in component if m['paired_reference_eligible']]
    add('peer_before_goal_match',sum(m['previous_response']=='same_goal' for m in comparable),len(comparable))
    add('peer_after_goal_match',sum(m['next_response']=='same_goal' for m in comparable),len(comparable))
    return result

def run():
    manifest=verify_science();audit=read(HERE/'DATA_AUDIT.json');tables=defaultdict(list);episode_rows=[];costs=[];checks=[]
    write(REPORTS/'MATCHEDNESS.json',matchedness(audit['cells']))
    detail_path=CACHE/'derived_records.jsonl.gz';detail_path.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(detail_path,'wt') as detail:
        for cell in audit['cells']:
            print('Reading '+cell['id'],flush=True)
            episodes=load_cell(cell);paired_worlds(episodes)
            base={k:cell[k] for k in ('id','cohort','condition','seed','round','horizon','defender_identity')}
            cost=dict(base,episodes=len(episodes),families=cell['families'],generator_calls=0,generator_input_tokens=0,generator_output_tokens=0,
                generator_token_missing=0,defender_calls=0,defender_input_tokens=0,defender_output_tokens=0)
            for episode in episodes:
                meta=dict(base,family_id=episode['family_id'],world=episode['world'])
                sequences=actor_sequences(episode);events=event_windows(episode,cell['horizon']);messages,queue_checks=reconstruct(episode,cell['config']['history_actions'])
                if any(q['queue_matches'] is False for q in queue_checks):raise ValueError('Inbox reconstruction disagrees in '+cell['id']+' '+episode['family_id'])
                checks.append(dict(meta,queue_checks=len(queue_checks),missing_observations=sum(q['queue_matches'] is None for q in queue_checks)))
                for metric,(num,den) in episode_metrics(episode,sequences,events,messages).items():
                    episode_rows.append(dict(meta,metric=metric,numerator=num,denominator=den,rate=num/den if den else None))
                actions=episode['actions']
                for keys,name in [(['role','actor_index','ordinal','turn','communication_slot','phase','event_kind','channel'],'channel_exposure'),
                    (['role','history_records','communication_slot','claim_truncated'],'observation_capacity'),
                    (['channel','valid','validity_reason','applied','state_changed','evidence_changed','notes_changed','following_adoption','actual_user_revision'],'action_flow'),
                    (['role','channel','reference_class','reference_available','reference_author','reference_exists_in_transcript','indexed_reference_author','value_relation','value_current','canonical_mismatch','current_value_inappropriate_citation'],'evidence_relations'),
                    (['role','channel','authorization_vocabulary','authorization_negation','advocacy_vocabulary','correction_vocabulary','value_current','canonical_visible'],'lexical_candidates'),
                    (['channel','transition','following_adoption','previous_plan_relation','following_success','previous_success_at_current_truth','actual_user_revision'],'following_associations')]:
                    tables[name].extend(dict(meta,**r) for r in group_counts(actions,keys))
                for name,rows,keys in [
                    ('actor_persistence',sequences['actors'],None),
                    ('goal_runs',sequences['runs'],['role','direct_actions','own_opportunity_span','conversation_turn_span','terminal_censored']),
                    ('goal_pairs',sequences['pairs'],['role','conversation_gap','own_opportunity_gap','same_goal','channel_changed','same_claim','same_reference','reference_class_changed','source_available_changed','observed_defender_relation_to_previous_goal']),
                    ('source_loss',sequences['source_losses'],['role','same_goal','same_claim','same_channel','same_canonical_authority']),
                    ('event_responsiveness',events,['role','event_kind','side','window_index','turn_lag','assigned_slot_relevant','alignment_change','valid_direct','event_value_endorsed','old_value_endorsed','owned_value_endorsed','action_value_current','insistence_after_revision']),
                    ('peer_responses',messages,['sender_role','recipient_type','communication_slot','structurally_valid','delivered','visible','visibility_status','claim_truncated','previous_response','next_response','second_response','next_same_slot_type','next_applied_matching_direct','next_mentions_sender','next_defender_adoption','paired_reference_eligible'])]:
                    if keys is None:tables[name].extend(dict(meta,**r) for r in rows)
                    else:tables[name].extend(dict(meta,**r) for r in group_counts(rows,keys))
                # Raw derived details stay ignored, preserving compact repository outputs.
                detail.write(json.dumps(dict(meta,actions=actions,sequences=sequences,events=events,messages=messages,queue_checks=queue_checks),separators=(',',':'))+'\n')
                for a in actions:
                    cost['generator_calls']+=a['generator_call']
                    for direction in ('input','output'):
                        value=a[direction+'_tokens'];cost['generator_'+direction+'_tokens']+=value or 0
                        cost['generator_token_missing']+=int(value is None and a['generator_call']==1)
                for field in ('defender_calls','defender_input_tokens','defender_output_tokens'):cost[field]+=episode[field]
            costs.append(cost)
    families=family_rate_rows(episode_rows);contrasts=all_contrasts(families)
    write_csv(CACHE/'family_rates.csv',families);write(REPORTS/'matched_contrasts.json',contrasts);write_csv(REPORTS/'costs.csv',costs)
    # Preserve family information in a local detailed archive; publish compact cell-level distributions.
    with gzip.open(CACHE/'family_distributions.jsonl.gz','wt') as f:
        for name,rows in tables.items():
            for row in rows:f.write(json.dumps({'table':name,**row},separators=(',',':'))+'\n')
    for name,rows in tables.items():
        if not rows:write_csv(REPORTS/(name+'.csv'),[]);continue
        if name=='actor_persistence':
            numeric=[k for k in rows[0] if k not in set(base)|{'family_id','world','actor','role','actor_index'}]
            accum={}
            for row in rows:
                key=tuple(row[k] for k in ('id','role','actor_index'));out=accum.setdefault(key,{k:row[k] for k in base}|{'role':row['role'],'actor_index':row['actor_index'],'actor_episodes':0,**{k:0 for k in numeric}})
                out['actor_episodes']+=1
                for k in numeric:out[k]+=row[k]
            condensed=list(accum.values())
        else:
            keys=[k for k in rows[0] if k not in {'family_id','world','count'}];accum=Counter()
            for row in rows:accum[tuple(row.get(k) for k in keys)]+=row['count']
            condensed=[dict(zip(keys,key),count=n) for key,n in sorted(accum.items(),key=lambda kv:str(kv[0]))]
        write_csv(REPORTS/(name+'.csv'),condensed)
    rates=defaultdict(lambda:[0,0,[]])
    for r in families:
        key=tuple(r[k] for k in ('cohort','condition','seed','metric'));entry=rates[key];entry[0]+=r['numerator'];entry[1]+=r['denominator']
        if r['rate'] is not None:entry[2].append(r['rate'])
    summaries=[dict(zip(('cohort','condition','seed','metric'),key),numerator=n,denominator=d,pooled_rate=n/d if d else None,
        families_with_denominator=len(values),mean_family_rate=sum(values)/len(values) if values else None) for key,(n,d,values) in sorted(rates.items())]
    write_csv(REPORTS/'metric_summary.csv',summaries)
    run_costs=[]
    for run in read(HERE/'EVIDENCE_SNAPSHOT.json')['included_runs']:
        meta=run['metadata'];included=[c for c in costs if c['id'].split('__')[0]==run['run_id']]
        counted_input=sum(c['generator_input_tokens']+c['defender_input_tokens'] for c in included)
        counted_output=sum(c['generator_output_tokens']+c['defender_output_tokens'] for c in included)
        counted_calls=sum(c['generator_calls']+c['defender_calls'] for c in included)
        run_costs.append({'run_id':run['run_id'],'recorded_model_input_tokens':meta.get('input_tokens'),
            'recorded_model_output_tokens':meta.get('output_tokens'),'recorded_model_calls':meta.get('model_calls'),
            'collection_input_tokens':counted_input,'collection_output_tokens':counted_output,'collection_calls':counted_calls,
            'residual_input_tokens':meta['input_tokens']-counted_input,'residual_output_tokens':meta['output_tokens']-counted_output,
            'residual_calls':meta['model_calls']-counted_calls,'model_load_seconds':meta.get('model_load_seconds'),
            'gpu_reserved_seconds':meta.get('gpu_reserved_seconds'),'qualification':'Residual includes recovery-candidate calls where run includes collection and labeling; no allocation of common load cost among pilot cells.'})
    write_csv(REPORTS/'run_cost_reconciliation.csv',run_costs)
    write(REPORTS/'RESULTS_PROVENANCE.json',{'generated_utc':utc(),'snapshot_sha256':sha256(HERE/'EVIDENCE_SNAPSHOT.json'),
        'scientific_manifest_sha256':sha256(HERE/'SCIENTIFIC_MANIFEST.json'),'cells':len(audit['cells']),
        'derived_records':str(detail_path.relative_to(ROOT)),'derived_records_sha256':sha256(detail_path),
        'paired_worlds_validated':True,'queue_checks':sum(r['queue_checks'] for r in checks),
        'queue_missing_observations':sum(r['missing_observations'] for r in checks),'queue_mismatches':0,
        'new_gpu_calls':0,'new_judge_calls':0,'tables':{p.name:sha256(p) for p in REPORTS.glob('*.csv')}})
    log('Completed frozen behavioral analysis; '+str(len(audit['cells']))+' condition cells; no new model calls.')

if __name__=='__main__':run()
