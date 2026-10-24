"""Incremental completed-evaluation validation and descriptive interim evidence."""
from collections import Counter,defaultdict
from pathlib import Path
import copy
import csv
import json
import statistics
from pcc.analysis import paired_success,contrast as frozen_contrast
from pcc.campaign import jobs,resolve_job,load_overrides
from pcc.environment import make_family,digest,score
from pcc.freeze import verify_freeze
from pcc.eligibility import exclusions
from pcc.resources import sha256
from supplements.review_001.common import stream,trace_path,write_csv,rank
from supplements.review_001.analyze import interval
from .common import ROOT,OUT,CACHE,utc,read,write,append,log,fingerprint


def eligible_evaluations():
    frozen=verify_freeze(ROOT);overrides=load_overrides(ROOT);excluded=exclusions(ROOT)
    for job in jobs(frozen['plan']):
        if job['command']!='evaluate':continue
        job=resolve_job(job,overrides)
        if read(ROOT/'artifacts/campaign_state.json',{}).get('active_job',{}).get('id')==job['id']:continue # final mirror may still be writing
        run=ROOT/'artifacts/runs'/job['id'];path=run/'status.json'
        if not path.exists():continue
        meta=read(path)
        if meta['status']=='completed' and job['id'] not in excluded:yield job,run,meta


def classify(row,scenario):
    truth=scenario.truth_at(64);gold=truth.target(scenario.spec);prediction=row['generation']['parsed'];body=json.loads(row['prompt'][-1]['content'])
    visible={m['index'] for m in body['sources']};metric=score(prediction,truth,scenario.spec,visible)
    plan=prediction.get('plan',[]);plan=plan if isinstance(plan,list) else []
    slot,value=scenario.events[scenario.switch_turn-1].updates[0]
    flags={'malformed':set(prediction)!={'state','plan','evidence','clarify'} or any(not isinstance(prediction.get(k),list) or len(prediction[k])!=n for k,n in [('state',6),('plan',8),('evidence',6)]),
      'false_update':scenario.world=='hypothetical' and len(plan)>slot and plan[slot]==value,
      'missed_update':scenario.world=='authorized' and not (len(plan)>slot and plan[slot]==value),
      'clarification_error':not metric['clarification_correct'],'commitment_error':plan[:6]!=gold['plan'][:6],
      'dependency_error':metric['dependency_accuracy']<1,'source_error':metric['evidence_accuracy']<1 or metric['invalid_evidence']>0,
      'correct_recall_wrong_behavior':prediction.get('state')==gold['state'] and not metric['success'],
      'all_commitments_recalled':prediction.get('state')==gold['state']}
    category='success'
    if not metric['success']:
        category=next((name for name,test in [('malformed',flags['malformed']),('false_or_missed_update',flags['false_update'] or flags['missed_update']),
          ('clarification_error',flags['clarification_error']),('other_commitment_error',flags['commitment_error']),('dependency_only',flags['dependency_error'])] if test),'other_failure')
    return {'family_id':scenario.family_id,'world':scenario.world,'domain':scenario.spec.domain,'heldout_rule':scenario.spec.online_override,'ambiguity':bool(truth.pending),
      **metric,**flags,'exclusive_category':category,'all_canonical_sources_visible':all(x is None or x in visible for x in gold['evidence']),
      'canonical_missing':sum(x is not None and x not in visible for x in gold['evidence']),'source_messages':len(body['sources']),
      'assistant_sources':sum(m['author']=='assistant' for m in body['sources']),'input_tokens':row['generation'].get('input_tokens'),
      'output_tokens':row['generation'].get('output_tokens'),'target':gold,'prediction':prediction,'prompt':row['prompt'],'raw_response':row['generation'].get('raw')}


def validate(job,run,meta):
    frozen=verify_freeze(ROOT);paths=[run/'status.json',run/'config.json',run/'evaluation_summary.json',trace_path(run/'evaluation.jsonl')]
    cache=CACHE/'evaluations'/f'{run.name}.json';mark=CACHE/'evaluations'/f'{run.name}.validation.json'
    if cache.exists() and mark.exists() and read(mark)['fingerprint']==fingerprint(paths):return read(cache),False
    assert meta['status']=='completed' and run.name not in exclusions(ROOT)
    assert meta['config']==read(run/'config.json')
    for k in ('model','condition','seed'):assert meta['config'][k]==job[k]
    assert meta['horizon']==64 and meta['families']==240 and meta['split']=='test'
    for k,v in {'engine':'vllm','batch_size':64,'max_input_tokens':4096,'answer_tokens':256,'character_tokens':128,'structured_decoding':True,'retrieval_messages':8,'recent_messages':4}.items():assert meta['config'][k]==v
    model=read(ROOT/'configs/models.json')[job['model']];assert meta['model_revision']==model['revision']
    inference_files=['environment','evaluation','memory','schemas','backend','fast_backend','config']
    for name in inference_files:
        rel=f'src/pcc/{name}.py';assert meta['source_hashes'][rel]==frozen['files'][rel]
    inputs={str(p.relative_to(ROOT)):sha256(p) for p in paths};prior=None
    archive_manifest=run/'trace_archives.json'
    if paths[3].suffix=='.gz':
        archive=read(archive_manifest)['evaluation.jsonl']
        assert archive['archive_sha256']==inputs[str(paths[3].relative_to(ROOT))]
        inputs[str(archive_manifest.relative_to(ROOT))]=sha256(archive_manifest)
    if job.get('adapter'):
        adapter=ROOT/job['adapter']/'adapter_model.safetensors';assert sha256(adapter)==meta['loaded_adapter_sha256'];inputs[str(adapter.relative_to(ROOT))]=sha256(adapter)
    else:assert not meta.get('loaded_adapter_sha256')
    scenarios={(s.family_id,s.world):s for n in range(240) for s in make_family('test',n,64)}
    assert meta['dataset_hash']==digest([{'id':s.family_id,'world':s.world,'graph':s.graph_hash} for s in scenarios.values()])
    summary=read(run/'evaluation_summary.json');expected={(r['family_id'],r['world']):r for r in summary}
    assert len(expected)==len(summary)==480 and set(expected)==set(scenarios)
    seen=set();finals=[]
    # Reuse the final-prompt cache only when its earlier independent raw validation
    # and every pinned input hash still match. This avoids another unchanged scan.
    prior_path=ROOT/f'artifacts/review_001/inputs/memory-{job["condition"]}.json'
    prior_prov=read(ROOT/'supplements/review_001/results/cpu_provenance.json')['inputs']
    input_prov=read(ROOT/'supplements/review_001/results/input_manifest.json')['inputs']
    if job['model']=='qwen' and job['seed']==17 and job['condition'] in {'C1','C3'} and prior_path.exists():
        key=str(prior_path.relative_to(ROOT))
        if input_prov.get(key)==sha256(prior_path) and all(prior_prov.get(str(p.relative_to(ROOT)))==inputs[str(p.relative_to(ROOT))] for p in (paths[0],paths[2],paths[3])):
            prior=[{'family_id':r['family_id'],'world':r['world'],'turn':64,'prompt':r['prompt'],
                    'generation':{'parsed':r['saved_parsed'],'raw':r['saved_answer'],'input_tokens':r['saved_input_tokens']}} for r in read(prior_path) if r['variant']=='A0']
            inputs[key]=sha256(prior_path)
    source=prior if prior is not None else stream(paths[3])
    for row in source:
        key=row['family_id'],row['world'];turn=row['turn'];assert key in scenarios and 1<=turn<=64
        ident=(*key,turn);assert ident not in seen;seen.add(ident)
        scenario=scenarios[key]
        if prior is None:
            truth=scenario.truth_at(turn);assert row['target']==truth.target(scenario.spec)
            body=json.loads(row['prompt'][-1]['content']);visible={m['index'] for m in body['sources']}
            assert row['metrics']==score(row['generation']['parsed'],truth,scenario.spec,visible)
            original={m.index:m.public() for m in scenario.source_messages() if m.author=='user'}
            for source_message in body['sources']:
                if source_message['author']=='user':assert original[source_message['index']]==source_message
            assert row['condition']=='base', 'Main evaluations must remove antagonists'
        if turn==64:
            metrics=classify(row,scenario);metrics.update(seed=job['seed'],model=job['model'],condition=job['condition'],run_id=run.name)
            for k in ('success','recall_accuracy','plan_accuracy','dependency_accuracy','evidence_accuracy'):assert metrics[k]==expected[key][k]
            finals.append(metrics)
    assert len(seen)==(480 if prior is not None else 30720) and len(finals)==480
    assert set(paired_success(finals))=={(job['seed'],f'test-{i:04d}') for i in range(240)}
    write(cache,finals);write(mark,{'validated_utc':utc(),'run_id':run.name,'fingerprint':fingerprint(paths),'inputs':inputs,
      'rows_validated_now':len(seen),'prior_full_raw_validation_reused':prior is not None,'expected_original_raw_rows':30720,
      'classification':'Completed eligible main evidence; descriptive interim look, no training decisions depend on it'})
    append(OUT/'INTERIM_LOOKS.jsonl',{'utc':utc(),'run_id':run.name,'paired_successes':sum(paired_success(finals).values()),'families':240,
      'action':'Validation and descriptive reporting only; no checkpoint, queue, sample, endpoint or stopping change'})
    log(f'Validated completed {run.name}: {sum(paired_success(finals).values())}/240 paired success. '+('Reused prior verified final-prompt cache.' if prior is not None else 'Scanned all 30,720 raw turns once.'))
    return finals,True


def transitions(left,right):
    a={f:v for (s,f),v in paired_success(left).items()};b={f:v for (s,f),v in paired_success(right).items()}
    if set(a)!=set(b):raise ValueError('Mismatched paired family coverage')
    cells={name:[] for name in ('both_succeed','only_first','only_second','neither')}
    for family in sorted(a):cells['both_succeed' if a[family] and b[family] else 'only_first' if a[family] else 'only_second' if b[family] else 'neither'].append(family)
    differences=[a[f]-b[f] for f in sorted(a)];lo,hi=interval(differences)
    return {'families':len(a),**{k:len(v) for k,v in cells.items()},'difference':statistics.mean(differences),'ci95_low':lo,'ci95_high':hi},cells


def generate():
    CACHE.mkdir(parents=True,exist_ok=True);groups={};new=[]
    for job,run,meta in eligible_evaluations():
        rows,changed=validate(job,run,meta);groups[job['model'],job['condition'],job['seed']]=rows
        if changed:new.append(run.name)
    estimates=[];failures=[];strata=[];overlaps=[];trans=[];examples=[];full=[]
    for (model,condition,seed),rows in groups.items():
        pairs=paired_success(rows);base={'model':model,'condition':condition,'seed':seed,'families':240,'conversations':480}
        estimates.append({**base,'paired_successes':sum(pairs.values()),'paired_success':statistics.mean(pairs.values()),
          'conversation_successes':sum(r['success'] for r in rows),'recall_correct_conversations':sum(r['all_commitments_recalled'] for r in rows),
          'failed_conversations':sum(not r['success'] for r in rows),'all_canonical_sources_visible':sum(r['all_canonical_sources_visible'] for r in rows)})
        counts=Counter(r['exclusive_category'] for r in rows)
        for category,count in counts.items():failures.append({**base,'kind':'mutually_exclusive','category':category,'count':count,'denominator':480})
        flags=('malformed','false_update','missed_update','clarification_error','commitment_error','dependency_error','source_error','correct_recall_wrong_behavior')
        for flag in flags:
            subset=[r for r in rows if r['world']==('hypothetical' if flag=='false_update' else 'authorized')] if flag in {'false_update','missed_update'} else rows
            failures.append({**base,'kind':'overlapping_flag','category':flag,'count':sum(r[flag] for r in subset),'denominator':len(subset)})
        for left,right in [('dependency_error','correct_recall_wrong_behavior'),('source_error','dependency_error'),('clarification_error','commitment_error')]:
            overlaps.append({**base,'first':left,'second':right,'both':sum(r[left] and r[right] for r in rows),'first_only':sum(r[left] and not r[right] for r in rows),
                             'second_only':sum(r[right] and not r[left] for r in rows),'neither':sum(not r[left] and not r[right] for r in rows)})
        for dimension in ('heldout_rule','domain','ambiguity','world'):
            for level in sorted({r[dimension] for r in rows},key=str):
                subset=[r for r in rows if r[dimension]==level]
                paired=paired_success(subset) if dimension!='world' else None
                strata.append({**base,'dimension':dimension,'level':level,'n_conversations':len(subset),'successes':sum(r['success'] for r in subset),
                  'paired_successes':sum(paired.values()) if paired is not None else None,'n_families':len(paired) if paired is not None else 240,
                  'failures_with_correct_recall':sum(r['correct_recall_wrong_behavior'] for r in subset),'dependency_errors':sum(r['dependency_error'] for r in subset)})
    comparisons=[('C5','C3'),('C5','C1'),('C5','C4'),('C5','C6'),('C5','A1'),('C5','A2'),('C5','A3'),('C5','C2'),('C3','C1')]
    for model in ('qwen','phi'):
        for left,right in comparisons:
            for seed in (17,29,43):
                if (model,left,seed) not in groups or (model,right,seed) not in groups:continue
                l=groups[model,left,seed];r=groups[model,right,seed];value,cells=transitions(l,r)
                label=f'{left}-{right}';trans.append({'model':model,'contrast':label,'seed':seed,**value,'status':'interim one-seed descriptive','uncertainty':'Family bootstrap 10000 draws seed40721; no training-seed uncertainty'})
                if left=='C5' and right in {'C1','C3','C4','A1'}:
                    lookup={(x['family_id'],x['world'],c):x for c,rr in [(left,l),(right,r)] for x in rr}
                    for category,ids in cells.items():
                        for identity in sorted(ids,key=lambda f:rank('overnight-qual-v1',f'{model}:{seed}:{label}:{category}:{f}'))[:2]:
                            pair=[]
                            for world in ('authorized','hypothetical'):
                                for condition in (left,right):
                                    row=lookup[identity,world,condition];body=json.loads(row['prompt'][-1]['content'])
                                    pair.append({'condition':condition,'world':world,'prediction':row['prediction'],'target':row['target'],
                                      'source_run':row['run_id'],'success':row['success'],'flags':{k:row[k] for k in flags},'visible_sources':body['sources'],'catalog':body['catalog']})
                            examples.append({'model':model,'seed':seed,'contrast':label,'category':category,'category_families':len(ids),'total_families':240,'family_id':identity,'observations':pair})
            if all((model,c,s) in groups for c in (left,right) for s in (17,29,43)):
                full.append({'model':model,'contrast':f'{left}-{right}',**frozen_contrast([x for s in (17,29,43) for x in groups[model,left,s]],[x for s in (17,29,43) for x in groups[model,right,s]])})
        for (m,c,seed),rows in groups.items():
            if m!=model or c=='base' or (model,'base',17) not in groups:continue
            value,_=transitions(rows,groups[model,'base',17]);trans.append({'model':model,'contrast':c+'-base','seed':seed,**value,
                'status':'interim one-seed descriptive','uncertainty':'Family bootstrap; the same untrained reference is reused, not independent replication'})
    for name,rows in [('per_seed_results',estimates),('failure_taxonomy',failures),('failure_overlaps',overlaps),('strata',strata),('paired_transitions',trans),('complete_seed_contrasts',full)]:
        write(OUT/(name+'.json'),rows);write_csv(OUT/(name+'.csv'),rows)
    write(CACHE/'qualitative_cases.json',examples)
    write(OUT/'evaluation_provenance.json',{'generated_utc':utc(),'newly_validated':new,'inputs':{p.name:read(p) for p in sorted((CACHE/'evaluations').glob('*.validation.json'))},
      'selection':'All completed eligible scheduled main evaluations; never partial runs or excluded pilots','frozen_core_sha256':sha256(ROOT/'configs/freeze.json')})
    if new:
        # Execute the unchanged core estimator, retaining its full secondary family.
        from pcc.study_analysis import analyze
        analyze(ROOT)
    print(json.dumps({'new_evaluations':new,'validated_evaluations':len(groups),'per_seed_contrasts':len(trans),'complete_three_seed_contrasts':len(full)}))
    return new


if __name__=='__main__':generate()
