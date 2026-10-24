"""Matched existing-core horizon audit and exploratory interaction, no new calls."""
from pathlib import Path
import json
import numpy as np
from pcc.environment import make_family,digest
from pcc.resources import sha256
from pcc.campaign import jobs,resolve_job,load_overrides
from pcc.freeze import verify_freeze
from pcc.eligibility import exclusions
from supplements.review_001.common import write_csv,trace_path
from .common import ROOT,REPORTS,ARTIFACTS,read,write,utc


HORIZONS=(32,64,128)
CONDITIONS=('base','C1','C3','C4','C5')


def semantic_events(scenario):
    return [{'kind':e.kind,'updates':[list(x) for x in e.updates],'author':m.author,'text':m.text}
            for m,e in zip(scenario.messages,scenario.events) if e.kind!='filler']


def design_audit():
    plan=read(ROOT/'configs/study_plan.json');families=plan['extension_family_numbers'];assert len(families)==len(set(families))==48
    rows=[]
    for number in families:
        variants={h:make_family('test',number,h) for h in HORIZONS}
        for world_idx,world in enumerate(('authorized','hypothetical')):
            short=variants[32][world_idx];ref_events=semantic_events(short);target=short.truth_at(32).target(short.spec)
            for h in HORIZONS:
                s=variants[h][world_idx];g=s.truth_at(h).target(s.spec)
                assert semantic_events(s)==ref_events and s.graph_hash==short.graph_hash and s.spec==short.spec
                assert all(g[k]==target[k] for k in ('state','plan','clarify'))
                rows.append({'family_id':s.family_id,'world':world,'horizon':h,'graph_hash':s.graph_hash,
                  'semantic_event_hash':digest(ref_events),'public_transcript_sha256':digest([m.public() for m in s.source_messages()]),
                  'decisive_events':[{'turn':i+1,'kind':e.kind,'updates':e.updates} for i,e in enumerate(s.events) if e.kind!='filler'],
                  'final_decisions_preserved':True,'evidence_indices_horizon_specific':g['evidence'],
                  'prefix_32_is_matched_experiment':h==32})
    result={'families':families,'rows':rows,'semantics_preserved':True,'frozen_plan_sha256':sha256(ROOT/'configs/study_plan.json'),
      'qualification':'Same task/decision sequence and decisive-event text, with horizon-specific event placement and evidence indices. Early events remain at absolute turns 1/3/5/6; this is not uniformly relative placement. Background text repeats in the original benchmark. Prefixes of long scripts are not matched shorter experiments.'}
    write(REPORTS/'CORE_HORIZON_DESIGN_AUDIT.json',result);return result


def paired_table(summary,ids):
    observed={}
    for r in summary:
        if r['family_id'] not in ids:continue
        key=r['family_id'],r['world']
        if key in observed:raise ValueError('Duplicate family/world')
        observed[key]=bool(r['success'])
    expected={(i,w) for i in ids for w in ('authorized','hypothetical')}
    if set(observed)!=expected:raise ValueError('Incomplete paired coverage')
    return np.array([observed[i,'authorized'] and observed[i,'hypothetical'] for i in sorted(ids)],float)


def contrast(short_method,long_method,short_control,long_control):
    arrays=[np.asarray(x,float) for x in (short_method,long_method,short_control,long_control)]
    if len({len(x) for x in arrays})!=1 or not len(arrays[0]):raise ValueError('Mismatched family dimensions')
    delta=(arrays[1]-arrays[0])-(arrays[3]-arrays[2]);absolute=arrays[1]-arrays[3]
    rng=np.random.default_rng(720021);indices=rng.integers(0,len(delta),(10000,len(delta)))
    return {'interaction':float(delta.mean()),'interaction_ci95':np.quantile(delta[indices].mean(1),[.025,.975]).tolist(),
      'absolute_128_difference':float(absolute.mean()),'absolute_128_ci95':np.quantile(absolute[indices].mean(1),[.025,.975]).tolist(),
      'method_long_minus_short':float((arrays[1]-arrays[0]).mean()),'control_long_minus_short':float((arrays[3]-arrays[2]).mean()),
      'qualification':'Exploratory family-only paired resampling of all methods/horizons/worlds together; seed17 only. Positive interaction does not imply higher absolute 128-turn performance.'}


def main():
    design=design_audit();ids={f'test-{i:04d}' for i in design['families']};frozen=verify_freeze(ROOT);override=load_overrides(ROOT)
    queue=[resolve_job(j,override) for j in jobs(frozen['plan'])];active=read(ROOT/'artifacts/campaign_state.json')['active_job']['id'];excluded=exclusions(ROOT)
    rows=[];values={};inputs={}
    for condition in CONDITIONS:
        for h in HORIZONS:
            command='evaluate' if h==64 else f'horizon{h}'
            matching=[j for j in queue if j['model']=='qwen' and j['condition']==condition and j['seed']==17 and j['command']==command]
            assert len(matching)==1
            job=matching[0];run=ROOT/'artifacts/runs'/job['id'];status=read(run/'status.json',{})
            row={'model':'qwen','condition':condition,'seed':17,'horizon':h,'families':48,'run_id':job['id'],'status':'pending','paired_success':None}
            if status.get('status')=='completed' and job['id']!=active and job['id'] not in excluded:
                assert status['horizon']==h and status['config']['seed']==17 and status['config']['condition']==condition
                if job.get('adapter'):assert sha256(ROOT/job['adapter']/'adapter_model.safetensors')==status['loaded_adapter_sha256']
                path=run/'evaluation_summary.json';summary=read(path);v=paired_table(summary,ids);values[condition,h]=v
                row.update(status='completed',paired_success=float(v.mean()),paired_successes=int(v.sum()))
                inputs[str(path.relative_to(ROOT))]=sha256(path);inputs[str((run/'status.json').relative_to(ROOT))]=sha256(run/'status.json')
            rows.append(row)
    comparisons=[];transitions=[]
    for control in ('C3','C1'):
        for h in HORIZONS:
            if ('C5',h) in values and (control,h) in values:
                a=values['C5',h].astype(bool);b=values[control,h].astype(bool)
                transitions.append({'contrast':'C5-'+control,'horizon':h,'families':48,'both':int((a&b).sum()),'only_C5':int((a&~b).sum()),'only_control':int((~a&b).sum()),'neither':int((~a&~b).sum())})
        keys=[('C5',32),('C5',128),(control,32),(control,128)]
        if all(k in values for k in keys):comparisons.append({'control':control,'status':'completed',**contrast(*(values[k] for k in keys))})
        else:comparisons.append({'control':control,'status':'pending','missing_cells':[list(k) for k in keys if k not in values]})
    for name,records in [('core_horizon_levels',rows),('core_horizon_interactions',comparisons),('core_horizon_transitions',transitions)]:
        write(REPORTS/(name+'.json'),records);write_csv(REPORTS/(name+'.csv'),records)
    write(REPORTS/'core_horizon_provenance.json',{'generated_utc':utc(),'inputs':inputs,'source_sha256':sha256(Path(__file__)),'seed':17,'inference':'New exploratory interaction; original horizon schedule/selection unchanged'})
    print({'existing_horizon_cells_complete':sum(r['status']=='completed' for r in rows),'total_cells':15,'interactions_complete':sum(r['status']=='completed' for r in comparisons)})


if __name__=='__main__':main()
