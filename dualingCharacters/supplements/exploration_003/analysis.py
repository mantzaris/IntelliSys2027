"""Fixed-prefix coverage and paired family analyses from the locked local snapshot."""
from collections import Counter,defaultdict
import gzip
import json
import statistics
import numpy as np
from pcc.environment import make_family
from .common import ROOT,HERE,REPORTS,CACHE,read,write,write_csv,sha256,verified_stream,rank,log
from .descriptors import descriptor,unique_categories,short_sequences,persistence,DIRECT

BOOTSTRAP_SEED=830031
DRAWS=10000

def verify_science():
    from .common import verify_prior
    verify_prior();manifest=read(HERE/'SCIENTIFIC_MANIFEST.json')
    for name,digest in manifest['files'].items():
        if sha256(HERE/name)!=digest:raise ValueError('Exploration scientific file changed: '+name)
    return manifest

def load_cell(cell):
    """Caches depend on raw SHA256 and this code's scientific freeze."""
    run=ROOT/'artifacts/runs'/cell['run_id'];prefix=cell['prefix'];paths=cell['raw_hashes']
    expected={'raw_hashes':paths,'science_sha256':sha256(HERE/'SCIENTIFIC_MANIFEST.json')}
    cache=CACHE/'cells'/f"{cell['id']}.json.gz";meta=cache.with_suffix('.meta.json')
    # Even cache reuse revalidates immutable bytes; no size-only cache is trusted.
    for name,digest in paths.items():
        if sha256(run/name)!=digest:raise ValueError('Source changed: '+str(run/name))
    if cache.exists() and meta.exists() and read(meta)==expected:
        with gzip.open(cache,'rt') as f:return json.load(f)
    action_file=next((n for n in paths if n.startswith(prefix+'_characters.jsonl')),None)
    raw_actions={}
    if action_file:
        for a in verified_stream(run/action_file,paths[action_file]):
            key=a['family_id'],a['world'],a['turn']
            if key in raw_actions:raise ValueError('Duplicate action key')
            raw_actions[key]=a
    episodes={};scenarios={}
    for f in cell['family_ids']:
        for s in make_family(f.split('-')[0],int(f.split('-')[-1]),cell['horizon']):scenarios[f,s.world]=s
    turn_file=next(n for n in paths if n in {prefix+'.jsonl',prefix+'.jsonl.gz'})
    for row in verified_stream(run/turn_file,paths[turn_file]):
        key=row['family_id'],row['world'];scenario=scenarios[key];turn=row['turn']
        if scenario.truth_at(turn).target(scenario.spec)!=row['target']:
            raise ValueError('Time-indexed truth mismatch: '+cell['id']+str(key)+str(turn))
        e=episodes.setdefault(key,{'family_id':key[0],'world':key[1],'actions':[],
            'defender_input_tokens':0,'defender_output_tokens':0,'defender_calls':0,'defender_cost_by_turn':[]})
        e['defender_input_tokens']+=row['generation']['input_tokens'];e['defender_output_tokens']+=row['generation']['output_tokens'];e['defender_calls']+=1
        e['defender_cost_by_turn'].append([turn,e['defender_input_tokens']+e['defender_output_tokens']])
        action=raw_actions.pop((*key,turn),None)
        if action:
            d=descriptor(action,scenario,row);d['ordinal']=len(e['actions'])+1;e['actions'].append(d)
        if turn==cell['horizon']:e['final_success']=row['metrics']['success']
    if raw_actions:raise ValueError('Orphan actions')
    output=[episodes[k] for k in sorted(episodes)]
    cache.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(cache,'wt') as f:json.dump(output,f,separators=(',',':'))
    write(meta,expected)
    return output

def family_interval(values):
    """Input is one paired-world mean per family, never a vector of actions."""
    values=np.asarray(values,dtype=float)
    if len(values)<2:return [None,None]
    rng=np.random.default_rng(BOOTSTRAP_SEED)
    draws=values[rng.integers(0,len(values),(DRAWS,len(values)))].mean(axis=1)
    return np.quantile(draws,[.025,.975]).tolist()

def paired_difference(first,second,field):
    a={(r['family_id'],r['world']):r[field] for r in first};b={(r['family_id'],r['world']):r[field] for r in second}
    if set(a)!=set(b):raise ValueError('Unmatched paired episodes')
    families=sorted({f for f,w in a}); diffs=[]
    for f in families:
        if {w for ff,w in a if ff==f}!={'authorized','hypothetical'}:raise ValueError('Missing paired world')
        diffs.append(statistics.mean(a[f,w]-b[f,w] for w in ('authorized','hypothetical')))
    return {'families':len(families),'difference':statistics.mean(diffs),'family_interval':family_interval(diffs)}

def episode_metrics(episode,budget):
    actions=episode['actions'];subset=actions[:budget]
    if len(subset)!=budget:raise ValueError('Incomplete prefix')
    sets=defaultdict(set)
    for a in subset:
        if a['category']:sets[a['actor']].add(tuple(a['category']))
    union=set().union(*sets.values()) if sets else set()
    roles=persistence(subset)
    return {'family_id':episode['family_id'],'world':episode['world'],'budget':budget,
        'coverage':len(union),'coarse_coverage':len(unique_categories(actions,budget,'coarse_category')),
        'sequence_coverage':len(short_sequences(actions,budget)),
        'transition_coverage':len({a['transition'] for a in subset if a['valid'] and a['kind']!='pass' and a['transition'] not in {'missing_state','no_typed_slot'}}),
        'valid':sum(a['valid'] for a in subset),'substantive':sum(a['category'] is not None for a in subset),
        'applied':sum(a['applied'] is True for a in subset),'substantive_applied':sum(a['applied'] is True and a['category'] is not None for a in subset),
        'memory_changes':sum(a['memory_changed'] is True for a in subset),
        'correct_to_incorrect_edits':sum(a['transition']=='correct_to_incorrect' for a in subset),
        'incorrect_to_correct_edits':sum(a['transition']=='incorrect_to_correct' for a in subset),
        'adoption_cases':sum(a['following_option_adopted'] is not None for a in subset),
        'adopted':sum(a['following_option_adopted'] is True for a in subset),
        'actor_category_sum':sum(map(len,sets.values())),
        'collective_beyond_largest_actor':len(union)-max(map(len,sets.values()),default=0),
        'input_tokens':sum(a['input_tokens'] or 0 for a in subset) if all(a['input_tokens'] is not None for a in subset) else None,
        'output_tokens':sum(a['output_tokens'] or 0 for a in subset) if all(a['output_tokens'] is not None for a in subset) else None,
        'model_calls':sum(a['model_call'] for a in subset),
        'same_goal':sum(r['same_goal'] for r in roles),'goal_comparisons':sum(r['goal_comparisons'] for r in roles),
        'same_goal_tactic_changes':sum(r['same_goal_tactic_changes'] for r in roles),
        'returns_after_other_goal':sum(r['returns_after_other_goal'] for r in roles),
        'final_success':episode['final_success']}

def curve(cell,episodes):
    budget=cell['opportunities_per_episode'];rows=[];per_episode=[];actors=[]
    if not budget:return rows,per_episode,actors
    identity={k:cell[k] for k in ('id','run_id','condition','cohort','seed','round','horizon','defender_identity')}
    for k in range(1,budget+1):
        metrics=[episode_metrics(e,k) for e in episodes]
        pooled=set().union(*(unique_categories(e['actions'],k) for e in episodes))
        summary={**identity,'budget':k,'families':cell['families'],'episodes':len(episodes),
          'mean_episode_coverage':statistics.mean(r['coverage'] for r in metrics),'pooled_coverage':len(pooled)}
        for field in ('coarse_coverage','sequence_coverage','transition_coverage','collective_beyond_largest_actor'):
            summary['mean_'+field]=statistics.mean(r[field] for r in metrics)
        for field in ('valid','substantive','applied','substantive_applied','memory_changes','correct_to_incorrect_edits','incorrect_to_correct_edits','adoption_cases','adopted','model_calls','same_goal','goal_comparisons','same_goal_tactic_changes','returns_after_other_goal'):
            summary[field]=sum(r[field] for r in metrics)
        for field in ('input_tokens','output_tokens'):
            summary[field]=sum(r[field] for r in metrics) if all(r[field] is not None for r in metrics) else None
        summary['consumed_opportunities']=k*len(episodes)
        rows.append(summary)
        if k==budget:per_episode=[{**identity,**r} for r in metrics]
    for e in episodes:
        actors.extend({**identity,'family_id':e['family_id'],'world':e['world'],**r} for r in persistence(e['actions']))
    return rows,per_episode,actors

def cost_prefix(actions,cap):
    spent=0;selected=[]
    for a in actions:
        if a['input_tokens'] is None or a['output_tokens'] is None:raise ValueError('Missing measured cost')
        cost=a['input_tokens']+a['output_tokens']
        if spent+cost>cap:break
        spent+=cost;selected.append(a)
    return selected,spent

def common_pair_analyses(a,b,cap):
    """Final pilot only: paired curves, complementarity, costs, archive ordering."""
    lookup=[{(e['family_id'],e['world']):e for e in xs} for xs in (a,b)]
    if set(lookup[0])!=set(lookup[1]):raise ValueError('Pair mismatch')
    paired=[];overlap=[];costs=[];novelty=[];archive=[]
    for k in range(1,cap+1):
        first=[episode_metrics(e,k) for e in a];second=[episode_metrics(e,k) for e in b]
        for metric in ('coverage','coarse_coverage','sequence_coverage','transition_coverage'):
            paired.append({'first':'C5','second':'C3','budget':k,'metric':metric,**paired_difference(first,second,metric)})
    half=cap//2
    for key in sorted(lookup[0]):
        ea,eb=lookup[0][key],lookup[1][key]
        sa,sb=unique_categories(ea['actions'],cap),unique_categories(eb['actions'],cap)
        mix=unique_categories(ea['actions'],half)|unique_categories(eb['actions'],cap-half)
        overlap.append({'family_id':key[0],'world':key[1],'C5':len(sa),'C3':len(sb),'shared':len(sa&sb),
            'C5_only':len(sa-sb),'C3_only':len(sb-sa),'jaccard':len(sa&sb)/len(sa|sb) if sa|sb else None,
            'mixture_half_prefix':len(mix),'mixture_minus_C3':len(mix)-len(sb),'mixture_minus_C5':len(mix)-len(sa),
            'mixture_interventions':cap,
            'mixture_character_tokens':sum(x['input_tokens']+x['output_tokens'] for x in ea['actions'][:half]+eb['actions'][:cap-half]),
            'mixture_defender_tokens_through_prefix':sum(next(c for t,c in e['defender_cost_by_turn'] if t==e['actions'][n-1]['turn']) for e,n in ((ea,half),(eb,cap-half)))})
        for condition,e in (('C5',ea),('C3',eb)):
            seen=set()
            for start,end in ((1,cap//3),(cap//3+1,2*cap//3),(2*cap//3+1,cap)):
                current=unique_categories(e['actions'],end);new=current-seen
                novelty.append({'condition':condition,'family_id':key[0],'world':key[1],'segment_start':start,'segment_end':end,'new_categories':len(new),'cumulative_categories':len(current),'opportunities':end-start+1})
                seen=current
    # Same absolute character-token caps, determined solely by measured costs.
    minimum=min(sum(x['input_tokens']+x['output_tokens'] for x in e['actions']) for e in a+b)
    for fraction in (.25,.5,.75,1.):
        token_cap=int(minimum*fraction);arrays=[]
        for condition,episodes in (('C5',a),('C3',b)):
            rows=[]
            for e in episodes:
                selected,spent=cost_prefix(e['actions'],token_cap)
                r={'condition':condition,'family_id':e['family_id'],'world':e['world'],'token_cap':token_cap,'spent':spent,'opportunities':len(selected),'coverage':len(unique_categories(selected,len(selected)))}
                rows.append(r);costs.append(r)
            arrays.append(rows)
        paired.append({'first':'C5','second':'C3','metric':'token_capped_coverage','token_cap':token_cap,**paired_difference(*arrays,'coverage')})
    # Archive curves shuffle whole paired families only; never individual actions.
    families=sorted({e['family_id'] for e in a});orderings=[]
    for replicate in range(100):
        ordering=sorted(families,key=lambda f:rank(f'exploration003-archive-{replicate}',f));orderings.append(ordering)
        seen={'C3':set(),'C5':set(),'balanced_mixture':set()}
        for index,family in enumerate(ordering):
            for world in ('authorized','hypothetical'):
                for condition,look in (('C5',lookup[0]),('C3',lookup[1])):
                    seen[condition]|=unique_categories(look[family,world]['actions'],cap)
                chosen=lookup[index%2]
                seen['balanced_mixture']|=unique_categories(chosen[family,world]['actions'],cap)
            for condition,categories in seen.items():
                archive.append({'ordering':replicate,'families':index+1,'condition':condition,'opportunities':(index+1)*2*cap,'categories':len(categories)})
    pooled_a=set().union(*(unique_categories(e['actions'],cap) for e in a));pooled_b=set().union(*(unique_categories(e['actions'],cap) for e in b))
    categories={'shared':sorted(pooled_a&pooled_b),'C5_only':sorted(pooled_a-pooled_b),'C3_only':sorted(pooled_b-pooled_a)}
    return paired,overlap,costs,novelty,archive,categories

def historical(cell):
    """No modern truth semantics are retroactively applied to older sources."""
    run=ROOT/'artifacts/runs'/cell['run_id'];prefix=cell['prefix'];seqs=defaultdict(list);counts=Counter()
    name=next((n for n in cell['raw_hashes'] if n.startswith(prefix+'_characters.jsonl')),None)
    if name:
        for a in verified_stream(run/name,cell['raw_hashes'][name]):
            counts[a['kind']]+=1
            if a['kind'] in DIRECT:seqs[a['family_id'],a['world'],a['actor']].append((a.get('slot'),a.get('value')))
    comparisons=[a==b for seq in seqs.values() for a,b in zip(seq,seq[1:])]
    return {'id':cell['id'],'run_id':cell['run_id'],'condition':cell['condition'],'families':cell['families'],
      'seed':cell['seed'],'action_counts':dict(counts),'repeat_numerator':sum(comparisons),'repeat_denominator':len(comparisons),
      'repeat_rate':statistics.mean(comparisons) if comparisons else None,'qualification':'Earlier protocol; coarse historical diagnostic only, not pooled.'}

def main():
    verify_science();audit=read(HERE/'DATA_AUDIT.json');curves=[];per_episode=[];actor_rows=[];history=[];loaded={}
    for cell in audit['included_cells']:
        if cell['cohort']=='historical_protocol':history.append(historical(cell));continue
        episodes=load_cell(cell);loaded[cell['id']]=episodes
        rows,episodes_rows,actors=curve(cell,episodes);curves+=rows;per_episode+=episodes_rows;actor_rows+=actors
    primary={c:loaded['mechanism-final-001__'+c] for c in ('C3','C5')}
    paired,overlap,costs,novelty,archive,categories=common_pair_analyses(primary['C5'],primary['C3'],audit['primary_common_budget'])
    write(REPORTS/'primary_paired_contrasts.json',paired)
    for name,rows in [('coverage_curves',curves),('primary_overlap',overlap),('primary_cost_prefixes',costs),('primary_novelty',novelty),('archive_rarefaction',archive)]:
        write_csv(REPORTS/(name+'.csv'),rows)
    write(REPORTS/'primary_category_overlap.json',categories);write(REPORTS/'historical_protocol_diagnostics.json',history)
    # Compact aggregate tables are versioned; full episode/actor detail remains regenerable bulk.
    write(CACHE/'episode_metrics.json',per_episode);write(CACHE/'actor_metrics.json',actor_rows)
    write_csv(REPORTS/'primary_episode_metrics.csv',[r for r in per_episode if r['cohort']=='primary_mechanism'])
    write_csv(REPORTS/'primary_actor_metrics.csv',[r for r in actor_rows if r['cohort']=='primary_mechanism'])
    comparisons=[]
    for seed in (17,29,43):
        for rnd in (0,1):
            cells={c:next((r for r in audit['included_cells'] if r['cohort']=='main_collection' and r['condition']==c and r['seed']==seed and r['round']==rnd),None) for c in ('C3','C5','C4','A1','C6','A2','A3','C2')}
            if not cells['C5']:continue
            for control in ('C3','C4','A1','C6','A2','A3','C2'):
                if not cells[control]:continue
                ca,cb=cells['C5'],cells[control]
                for key in ('family_ids','horizon','schedule','model_revision'):
                    if ca[key]!=cb[key]:raise ValueError('Main paired comparison mismatch')
                aa=[r for r in per_episode if r['id']==ca['id']];bb=[r for r in per_episode if r['id']==cb['id']]
                comparisons.append({'first':'C5','second':control,'seed':seed,'round':rnd,
                    'same_defender_weights':ca['defender_identity']==cb['defender_identity'],
                    'qualification':'Observational collection; family uncertainty within this generator seed; no training-seed population claim',
                    **paired_difference(aa,bb,'coverage')})
    write(REPORTS/'main_collection_contrasts.json',comparisons)
    # Ratios retain denominators and role identities solely for private descriptive diagnostics.
    role_summary=[]
    grouped=defaultdict(list)
    for row in actor_rows:grouped[row['id'],row['role']].append(row)
    for (identity,role),rows in grouped.items():
        out={'id':identity,'role':role,'actors_across_episodes':len(rows)}
        for field in ('opportunities','direct_actions','goal_comparisons','same_goal','same_goal_tactic_changes','returns_after_other_goal'):
            out[field]=sum(r[field] for r in rows)
        out['repeat_rate']=out['same_goal']/out['goal_comparisons'] if out['goal_comparisons'] else None
        out['tactic_change_given_same_goal']=out['same_goal_tactic_changes']/out['same_goal'] if out['same_goal'] else None
        out['mean_within_actor_categories']=statistics.mean(r['within_actor_categories'] for r in rows)
        role_summary.append(out)
    write_csv(REPORTS/'persistence_by_role.csv',role_summary)
    write(REPORTS/'ANALYSIS_PROVENANCE.json',{'scientific_manifest_sha256':sha256(HERE/'SCIENTIFIC_MANIFEST.json'),
        'snapshot_sha256':sha256(HERE/'EVIDENCE_SNAPSHOT.json'),'data_audit_sha256':sha256(HERE/'DATA_AUDIT.json'),
        'tables':{p.name:sha256(p) for p in sorted(REPORTS.iterdir()) if p.suffix in {'.csv','.json'} and p.name not in {'ANALYSIS_PROVENANCE.json','LATEST_STATE.json','RESOURCE_FORECAST.json','SESSION.json','STARTING_INVENTORY.json'}},
        'gpu_calls':0,'model_judge_calls':0,'bootstrap_seed':BOOTSTRAP_SEED,'bootstrap_draws':DRAWS})
    log('Completed frozen descriptor analysis without new model calls. Pilot and observational collection tables remain separate.')
    print({'analyzed_cells':len(loaded),'historical_cells':len(history),'primary_endpoint':[r for r in paired if r.get('budget')==audit['primary_common_budget'] and r['metric']=='coverage']})

if __name__=='__main__':main()
