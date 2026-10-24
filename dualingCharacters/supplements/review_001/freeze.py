"""Freeze supplement implementation now; bind fixed prerequisite bytes later."""
from datetime import datetime,timezone
from dataclasses import asdict
from pathlib import Path
import argparse
import json
import subprocess
from pcc.freeze import verify_freeze
from pcc.environment import digest
from pcc.campaign import jobs,load_overrides,resolve_job
from pcc.resources import sha256
from .common import ROOT,HERE,ARTIFACTS,read,write,final_checkpoint,main_evaluation,require_completed
from .fresh import family,design


def manifests():
    core_graphs=set();core_sources=set();inputs={}
    for split in ('pilot','train','validation','test','natural'):
        path=ROOT/f'data/manifests/{split}.json';document=read(path);inputs[str(path.relative_to(ROOT))]=sha256(path)
        for row in document['families']:
            core_graphs.add(row['graph_hash']);core_sources.update(row['source_hashes'])
    groups={};all_graphs=set();all_sources=set()
    for kind,count,horizon in [('profile',8,32),('mechanism',16,32),('balanced',64,64)]:
        entries=[]
        for number in range(count):
            pair=family(kind,number,horizon);s=pair[0]
            sources=[digest([m.public() for m in x.source_messages()]) for x in pair]
            assert s.graph_hash not in core_graphs|all_graphs,'Exact graph overlap'
            assert not set(sources)&(core_sources|all_sources),'Exact source overlap'
            all_graphs.add(s.graph_hash);all_sources.update(sources)
            entries.append({'family_id':s.family_id,'number':number,'domain':s.spec.domain,'heldout_rule':s.spec.online_override,
                            'ambiguous':bool(s.truth_at(horizon).pending),'horizon':horizon,'graph_hash':s.graph_hash,
                            'source_hashes':sources,'design':design(kind,number) if kind!='balanced' else None})
        groups[kind]=entries
    result={'groups':groups,'core_manifest_hashes':inputs,'exact_graph_overlap':0,'exact_source_overlap':0,
            'qualification':'Fresh IDs, surface text and exact graphs; the original six-slot ontology and dependency types remain shared.'}
    write(HERE/'fresh_manifest.json',result)
    return result


def verify():
    verify_freeze(ROOT);frozen=read(HERE/'FREEZE.json')
    assert sha256(ROOT/'configs/freeze.json')==frozen['core_freeze_sha256']
    for name,value in frozen['files'].items():
        if sha256(ROOT/name)!=value:raise ValueError('Supplement frozen input changed: '+name)
    return frozen


def freeze():
    verify_freeze(ROOT);manifests()
    paths=[*HERE.glob('*.py'),HERE/'PROTOCOL.md',HERE/'protocol.json',HERE/'requirements-cpu.txt',HERE/'fresh_manifest.json']
    files={str(p.relative_to(ROOT)):sha256(p) for p in sorted(paths)}
    dest=HERE/'FREEZE.json'
    if dest.exists():
        previous=read(dest)
        if previous['files']!=files:raise ValueError('Existing supplement freeze differs; explicit amendment required')
        verify();return previous
    result={'frozen_utc':datetime.now(timezone.utc).isoformat(),
            'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'core_freeze_sha256':sha256(ROOT/'configs/freeze.json'),'files':files,
            'known_outcomes_at_design':'C1 seed17 186/240; C3 seed17 177/240; untrained baselines and historical pilots; no review001 model calls',
            'classification':'Post-review exploratory implementation freeze; concrete timing-based allocation follows profiling without outcome inspection'}
    write(dest,result);return result


def bind():
    frozen=verify();core=verify_freeze(ROOT);overrides=load_overrides(ROOT)
    for original in jobs(core['plan']):
        require_completed(resolve_job(original,overrides)['id'])
    bindings={}
    for condition in ('base','C1','C3','C5'):
        run,meta=require_completed(main_evaluation(condition));adapter=final_checkpoint(condition)
        value=sha256(adapter/'adapter_model.safetensors') if adapter else None
        if adapter and value!=meta['loaded_adapter_sha256']:raise ValueError('Fixed evaluation loaded different final weights')
        bindings[condition]={'evaluation_run_id':run.name,'status_sha256':sha256(run/'status.json'),
            'adapter_path':str(adapter.relative_to(ROOT)) if adapter else None,'adapter_sha256':value,
            'model_revision':meta['model_revision'],'chat_template_sha256':meta['chat_template_sha256']}
    result={'bound_utc':datetime.now(timezone.utc).isoformat(),'supplement_freeze_sha256':sha256(HERE/'FREEZE.json'),
            'bindings':bindings,'selection':'Fixed named final seed-17 checkpoints; no score-based selection'}
    path=ARTIFACTS/'bindings.json'
    if path.exists():
        old=read(path)
        if old['bindings']!=bindings or old['supplement_freeze_sha256']!=result['supplement_freeze_sha256']:
            raise ValueError('Prerequisite binding changed')
        return old
    write(path,result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['manifests','freeze','verify','bind']);a=p.parse_args()
    result=globals()[a.command]();print(json.dumps({'operation':a.command,'files':len(result.get('files',{}))}))
