"""Matched existing-core horizon audit and exploratory interaction, no new calls."""
from pathlib import Path
import json
import numpy as np
from pcc.environment import make_family,digest,score
from pcc.resources import sha256
from pcc.campaign import jobs,resolve_job,load_overrides
from pcc.freeze import verify_freeze
from pcc.eligibility import exclusions
from supplements.review_001.common import write_csv,trace_path,stream
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


def extension_identity(status,job,numbers,horizon):
    if status.get('status')!='completed' or status.get('extension')!=f'horizon{horizon}':raise ValueError('Incomplete/wrong horizon extension')
    if status.get('family_numbers')!=numbers:raise ValueError('Frozen horizon family selection changed')
    for name in ('model','condition','seed'):
        if status['config'][name]!=job[name]:raise ValueError('Horizon configuration identity mismatch')


def validate_extension(job,run,status,numbers,horizon):
    extension_identity(status,job,numbers,horizon);frozen=verify_freeze(ROOT)
    if run.name in exclusions(ROOT):raise ValueError('Excluded horizon run')
    if read(run/'config.json')!=status['config']:raise ValueError('Saved configuration differs')
    for k,v in {'engine':'vllm','batch_size':64,'max_input_tokens':4096,'answer_tokens':256,'character_tokens':128,'structured_decoding':True,'retrieval_messages':8,'recent_messages':4}.items():
        if status['config'][k]!=v:raise ValueError('Frozen horizon inference differs: '+k)
    if status['model_revision']!=read(ROOT/'configs/models.json')['qwen']['revision']:raise ValueError('Model revision differs')
    for name in ('environment','extensions','evaluation','memory','schemas','backend','fast_backend','config'):
        rel=f'src/pcc/{name}.py'
        if status['source_hashes'][rel]!=frozen['files'][rel]:raise ValueError('Horizon source mismatch: '+rel)
    if job.get('adapter') and sha256(ROOT/job['adapter']/'adapter_model.safetensors')!=status['loaded_adapter_sha256']:raise ValueError('Horizon adapter mismatch')
    scenarios={(s.family_id,s.world):s for number in numbers for s in make_family('test',number,horizon)}
    expected_hash=digest([{'id':s.family_id,'world':s.world,'sources':[m.public() for m in s.source_messages()]} for s in scenarios.values()])
    if status['dataset_hash']!=expected_hash:raise ValueError('Horizon transcript manifest mismatch')
    summary=read(run/'evaluation_summary.json');indexed={(r['family_id'],r['world']):r for r in summary}
    if len(indexed)!=len(summary) or set(indexed)!=set(scenarios):raise ValueError('Horizon paired coverage differs')
    source=trace_path(run/'evaluation.jsonl');cache=ARTIFACTS/'core_horizon_validation'/f'{run.name}.json'
    signature=[sha256(run/'status.json'),sha256(run/'evaluation_summary.json'),source.stat().st_size,source.stat().st_mtime_ns]
    if cache.exists() and read(cache)['signature']==signature:return read(cache)
    seen=set()
    for row in stream(source):
        k=row['family_id'],row['world'];turn=row['turn'];identity=(*k,turn)
        if k not in scenarios or not 1<=turn<=horizon or identity in seen:raise ValueError('Invalid/duplicate horizon trace observation')
        seen.add(identity);s=scenarios[k];truth=s.truth_at(turn);body=json.loads(row['prompt'][-1]['content'])
        if row['target']!=truth.target(s.spec) or row['condition']!='base':raise ValueError('Dynamic target or antagonist-free boundary differs')
        metrics=score(row['generation']['parsed'],truth,s.spec,{m['index'] for m in body['sources']})
        if metrics!=row['metrics']:raise ValueError('Raw horizon score differs')
        users={m.index:m.public() for m in s.messages}
        for m in body['sources']:
            if m['author']=='user' and users.get(m['index'])!=m:raise ValueError('Original user source changed')
        if turn==horizon:
            if indexed[k]['horizon']!=horizon or indexed[k]['memory_updates']!=horizon:raise ValueError('Incomplete interactive horizon')
            for field in ('success','recall_accuracy','plan_accuracy','dependency_accuracy','evidence_accuracy'):
                if metrics[field]!=indexed[k][field]:raise ValueError('Horizon final summary differs')
    if len(seen)!=len(scenarios)*horizon:raise ValueError('Missing horizon trace turns')
    value={'signature':signature,'rows':len(seen),'raw_sha256':sha256(source),'source_sha256':sha256(Path(__file__)),'validated_utc':utc()};write(cache,value);return value


def main():
    design=design_audit();ids={f'test-{i:04d}' for i in design['families']};frozen=verify_freeze(ROOT);override=load_overrides(ROOT)
    queue=[resolve_job(j,override) for j in jobs(frozen['plan'])];active=(read(ROOT/'artifacts/campaign_state.json').get('active_job') or {}).get('id');excluded=exclusions(ROOT)
    rows=[];values={};inputs={}
    for condition in CONDITIONS:
        for h in HORIZONS:
            command='evaluate' if h==64 else f'horizon{h}'
            matching=[j for j in queue if j['model']=='qwen' and j['condition']==condition and j['seed']==17 and j['command']==command]
            assert len(matching)==1
            job=matching[0];run=ROOT/'artifacts/runs'/job['id'];status=read(run/'status.json',{})
            row={'model':'qwen','condition':condition,'seed':17,'horizon':h,'families':48,'run_id':job['id'],'status':'pending','paired_success':None}
            if status.get('status')=='completed' and job['id']!=active and job['id'] not in excluded:
                if h==64:
                    assert status['horizon']==h and status['config']['seed']==17 and status['config']['condition']==condition
                    # Full 30,720-turn validation is already cached by incremental main analysis.
                    validated=ARTIFACTS/'core_audits/evaluations'/f'{job["id"]}.validation.json'
                    if not validated.exists():raise ValueError('Validate completed main evaluation first')
                    for path in (run/'status.json',run/'evaluation_summary.json'):
                        if read(validated)['inputs'].get(str(path.relative_to(ROOT)))!=sha256(path):raise ValueError('Previously validated main input changed')
                    inputs[str(validated.relative_to(ROOT))]=sha256(validated)
                else:
                    checked=validate_extension(job,run,status,design['families'],h)
                    inputs[str(trace_path(run/'evaluation.jsonl').relative_to(ROOT))]=checked['raw_sha256']
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
