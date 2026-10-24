"""Independent scientific freeze and fixed-final-checkpoint binding, never score selection."""
from pathlib import Path
import argparse
import subprocess
from pcc.resources import sha256
from pcc.campaign import jobs,resolve_job,load_overrides
from pcc.freeze import verify_freeze
from supplements.review_001.freeze import verify as verify_review
from .common import ROOT,HERE,REPORTS,ARTIFACTS,read,write,utc

OPERATIONAL={'operations.py','core_refresh.py'}


def science_paths():
    return sorted([p for p in HERE.glob('*.py') if p.name not in OPERATIONAL]+[
      HERE/'PROTOCOL.md',HERE/'RUBRIC.md',HERE/'DATASET_CARD.md',HERE/'dataset_manifest.json',HERE/'requirements-cpu.txt'])


def verify():
    verify_review();doc=read(HERE/'FREEZE.json')
    if doc['core_freeze_sha256']!=sha256(ROOT/'configs/freeze.json') or doc['review_freeze_sha256']!=sha256(ROOT/'supplements/review_001/FREEZE.json'):raise ValueError('Prior scientific freeze changed')
    for name,digest in doc['files'].items():
        if sha256(ROOT/name)!=digest:raise ValueError('Intent scientific freeze changed: '+name)
    return doc


def create():
    verify_review();files={str(p.relative_to(ROOT)):sha256(p) for p in science_paths()}
    if (HERE/'FREEZE.json').exists():
        doc=verify()
        if doc['files']!=files:raise ValueError('New scientific files require an explicit amendment')
        return doc
    results=read(REPORTS/'per_seed_results.json',[])
    doc={'frozen_utc':utc(),'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
      'core_freeze_sha256':sha256(ROOT/'configs/freeze.json'),'review_freeze_sha256':sha256(ROOT/'supplements/review_001/FREEZE.json'),
      'files':files,'known_results_at_freeze':results,'prior_observation_chronology':'reports/WORK_LOG.md',
      'classification':'Exploratory post-negative-C5 and post-C1-seed-reversal specification; fresh intent model calls and human ratings absent at freeze',
      'allocation_rule':'Timing only after fixed disjoint engineering/profile; no outcome-based choice; missing core/review gates leave disabled'}
    write(HERE/'FREEZE.json',doc);return doc


def fixed_jobs():
    plan=verify_freeze(ROOT)['plan'];queue=[resolve_job(j,load_overrides(ROOT)) for j in jobs(plan)]
    found={}
    for seed in (17,29,43):
        for condition in ('C1','C3','C5'):
            evaluation=[j for j in queue if j['model']=='qwen' and j['seed']==seed and j['condition']==condition and j['command']=='evaluate']
            if len(evaluation)!=1:raise ValueError('Ambiguous fixed final checkpoint')
            found[condition,seed]=evaluation[0]
    return found


def checkpoint_readiness():
    rows=[]
    for (condition,seed),job in fixed_jobs().items():
        status=read(ROOT/'artifacts/runs'/job['id']/'status.json',{})
        row={'condition':condition,'seed':seed,'evaluation_run_id':job['id'],'adapter_path':job['adapter'],
          'status':'ready_for_binding' if status.get('status')=='completed' else 'pending_final_evaluation',
          'adapter_sha256':status.get('loaded_adapter_sha256'),'model_revision':status.get('model_revision')}
        rows.append(row)
    write(REPORTS/'CHECKPOINT_READINESS.json',rows);return rows


def bind():
    from .budget import prerequisites
    frozen=verify();p=prerequisites()
    if not p['core_complete'] or not p['review_complete']:raise PermissionError('Core and higher-priority review must resolve before binding execution inputs')
    bindings={}
    for (condition,seed),job in fixed_jobs().items():
        run=ROOT/'artifacts/runs'/job['id'];meta=read(run/'status.json');adapter=ROOT/job['adapter']
        digest=sha256(adapter/'adapter_model.safetensors')
        if digest!=meta['loaded_adapter_sha256']:raise ValueError('Final evaluation and final adapter bytes differ')
        if meta['model_revision']!='cdbee75f17c01a7cc42f958dc650907174af0554':raise ValueError('Unexpected Qwen revision')
        bindings[f'{condition}-{seed}']={'evaluation_run_id':job['id'],'status_sha256':sha256(run/'status.json'),
          'adapter_path':job['adapter'],'adapter_sha256':digest,'adapter_config_sha256':sha256(adapter/'adapter_config.json'),
          'model_revision':meta['model_revision'],'chat_template_sha256':meta['chat_template_sha256']}
    result={'bound_utc':utc(),'intent_freeze_sha256':sha256(HERE/'FREEZE.json'),'dataset_manifest_sha256':sha256(HERE/'dataset_manifest.json'),
      'bindings':bindings,'selection':'Named final checkpoints only, all C1/C3/C5 seeds17/29/43; no score-based choice'}
    path=ARTIFACTS/'bindings.json'
    if path.exists():
        previous=read(path)
        if any(previous[k]!=result[k] for k in ('bindings','intent_freeze_sha256','dataset_manifest_sha256')):raise ValueError('Existing bindings changed')
        return previous
    write(path,result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['create','verify','bind','checkpoint_readiness']);a=p.parse_args();r=globals()[a.command]();print({'operation':a.command,'records':len(r) if isinstance(r,list) else len(r.get('files',{}))})
