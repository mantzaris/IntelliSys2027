"""Preserve frozen replay code while separately versioning live-worker instructions.

The first controller finishes Phi-4 replay validation before this successor starts.
No accepted call is resampled. Both live development checks precede held-out calls.
"""
import argparse
import importlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from rep_sensitivity.live import run_live
from rep_sensitivity.aux_analysis import summarize as summarize_aux
from rep_sensitivity.schema import digest
from rep_sensitivity.storage import immutable_json,utcnow


def archived_replay(path):
    package=Path(path).resolve()/'rep_sensitivity'
    spec=importlib.util.spec_from_file_location('rep_replay_frozen',package/'__init__.py',submodule_search_locations=[str(package)])
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return importlib.import_module('rep_replay_frozen.study_execution')


def live_development(frozen,alias,templates,model=None):
    config=frozen.read(Path(templates)/'live-v8-candidate.json')
    config.update(name='live-development-v8',status='development_live',generated_pairs=12)
    if not frozen.complete(config['name'],alias,'live'):model=run_live(config,alias,model)
    rows=[json.loads(p.read_text()) for p in Path('artifacts/runs',config['name'],alias,'scores').glob('*.json')]
    baseline=[r for r in rows if r['allocation']=='nonoverlap']
    if len(baseline)!=12:raise RuntimeError('Incomplete corrected live-worker development check')
    rate=sum(r['correct'] for r in baseline)/len(baseline)
    record={'suite':config['name'],'model':alias,'baseline_decisions':len(baseline),'baseline_clusters':len({r['pair_id'] for r in baseline}),
            'baseline_accuracy':rate,'threshold':0.85,'passed':rate>=0.85,
            'interpretation':'Below-threshold live results describe task/interface limitations, not an identified redundancy mechanism. This does not alter the independently qualified frozen-report replay.'}
    immutable_json(Path('records/gates')/('live-development-v8-'+alias+'.json'),record)
    print(json.dumps(record),flush=True)
    return model


def freeze_live(frozen,templates):
    config=frozen.read(Path(templates)/'live-v8-candidate.json')
    records={m:frozen.read(Path('records/gates')/('live-development-v8-'+m+'.json')) for m in config['models']}
    if not all(frozen.complete('live-development-v8',m,'live') for m in config['models']):
        raise RuntimeError('Both corrected live development checks must complete before held-out inference')
    config.update(status='frozen')
    source=Path(__file__).parent/'rep_sensitivity'
    return frozen.publish(config,'Explicit worker predicate definitions; frozen before any held-out inference',{
        'supersedes':'live-v7 configuration only; live-v7 held-out calls are never executed',
        'development_adequacy':records,'live_implementation_sha256':digest({p.name:p.read_text() for p in source.glob('*.py')}),
        'replay_protocol':'Unchanged v7 archived implementation',
        'negative_adequacy_rule':'Retain all live results, but limit their interpretation to diagnostics when baseline competence is inadequate.'})


def stage(name,replay_snapshot,templates):
    for package,version in (('vllm','0.10.2'),('transformers','4.55.4')):
        if importlib.metadata.version(package)!=version:raise RuntimeError('Inference environment changed: '+package)
    frozen=archived_replay(replay_snapshot)
    old_templates=Path(replay_snapshot)/'configuration'
    primary,secondary=frozen.selected_models(old_templates)
    if not frozen.complete('validation-v7',secondary):raise RuntimeError('Preceding frozen Phi-4 validation is incomplete')
    if name=='secondary_live_development':
        live_development(frozen,secondary,templates)
        return
    alias=primary if name=='primary_replay_and_live' else secondary
    model=None
    if alias==primary:
        # Reuse the exact archived source for both models' control and validation runs.
        common=frozen.read(old_templates/'validation-candidate-v7.json')
        controls=frozen.read(old_templates/'supporting-provisional.json')
        for key in ('models','model_settings','max_context_tokens','max_output_tokens','temperature','top_p',
                    'batch_size','enforce_eager','gpu_memory_utilization','root_ancestry_registry'):
            controls[key]=common[key]
        controls.update(name='controls-development-v7',status='development_controls',source_corpus='artifacts/runs/pilot-v7',
                        pair_indices=[0,5],stochastic_repetitions=1,bootstrap_strata=['decision_changed'])
        if not frozen.complete(controls['name'],alias,'controls'):model=frozen.run_controls(controls,alias,model)
        model=live_development(frozen,alias,templates,model)
        validation=frozen.read('configs/frozen/validation-v7.json')
        if not frozen.complete(validation['name'],alias):model=frozen.run(validation,alias,model=model)
    # freeze_main uses the original validation/resource rule and original replay code.
    # Its unused legacy live plan is prospectively superseded before the first call.
    main=frozen.freeze_main(old_templates)
    live=freeze_live(frozen,templates)
    if not frozen.complete(main['name'],alias):model=frozen.run(main,alias,model=model)
    controls=frozen.read('configs/frozen/supporting-v7.json')
    if not frozen.complete(controls['name'],alias,'controls'):model=frozen.run_controls(controls,alias,model)
    if not frozen.complete(live['name'],alias,'live'):run_live(live,alias,model)
    if all(frozen.complete('main-v7',m) for m in (primary,secondary)):
        frozen.summarize('artifacts/runs/main-v7','results/main-v7')
        for suite in ('supporting-v7','live-v8','controls-development-v7','live-development-v8'):
            summarize_aux(Path('artifacts/runs')/suite,Path('results')/suite)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--templates',required=True)
    parser.add_argument('--replay-snapshot',required=True);parser.add_argument('--after-pid',type=int)
    stages=('secondary_live_development','primary_replay_and_live','secondary_replay_and_live')
    parser.add_argument('--stage',choices=('all',*stages),default='all');a=parser.parse_args()
    while a.after_pid:
        try:os.kill(a.after_pid,0)
        except ProcessLookupError:break
        time.sleep(5)
    record_root=Path('artifacts/runs/study-execution-v8');record_root.mkdir(parents=True,exist_ok=True)
    try:
        if a.stage=='all':
            for name in stages:
                if (record_root/'STOP_AFTER_CURRENT_STAGE').exists():raise RuntimeError('Stop file present')
                with Path('logs','study-v8-'+name+'.log').open('a') as log:
                    subprocess.run([sys.executable,__file__,'--templates',a.templates,'--replay-snapshot',a.replay_snapshot,
                                    '--stage',name],stdout=log,stderr=subprocess.STDOUT,check=True)
                immutable_json(record_root/(name+'-complete.json'),{'stage':name,'complete':True})
        else:stage(a.stage,a.replay_snapshot,a.templates)
    except Exception as error:
        immutable_json(record_root/('failure-'+str(time.time_ns())+'.json'),{'utc':utcnow(),'stage':a.stage,
                       'exception':repr(error),'action':'Stopped; accepted outputs are immutable. No automatic resampling.'})
        raise


if __name__=='__main__':main()
