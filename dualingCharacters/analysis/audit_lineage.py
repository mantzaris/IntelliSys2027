"""Check executed checkpoint and supervision links; never inspect task scores."""
from pathlib import Path
import json
from pcc.campaign import jobs,load_overrides,resolve_job
from pcc.freeze import verify_freeze
from pcc.resources import sha256


def audit(root: Path):
    frozen=verify_freeze(root);overrides=load_overrides(root);rows=[];hashes={};initializations={}
    def checksum(path):
        if path not in hashes:hashes[path]=sha256(path)
        return hashes[path]
    for original in jobs(frozen['plan']):
        job=resolve_job(original,overrides);run=root/'artifacts/runs'/job['id'];status=run/'status.json'
        if not status.exists():continue
        meta=json.loads(status.read_text())
        if meta['status']!='completed':continue
        cfg=meta['config']
        assert (cfg['model'],cfg['condition'],cfg['seed'])==(job['model'],job['condition'],job['seed'])
        row={'run_id':job['id'],'original_scheduled_id':original['id'],'status_sha256':checksum(status),'model':cfg['model'],
             'condition':cfg['condition'],'seed':cfg['seed'],'parent_adapter':job.get('adapter'),'parent_sha256':None}
        if job.get('adapter'):
            parent=root/job['adapter']/'adapter_model.safetensors';value=checksum(parent)
            assert meta['loaded_adapter_sha256']==value, 'Loaded weights differ from scheduled parent'
            row['parent_sha256']=value
            if job['command']=='fit':
                initial=run/'training/initial/adapter_model.safetensors'
                assert checksum(initial)==value, 'Round continuation reset the adapter'
        else:assert not meta.get('loaded_adapter_sha256'), 'Unadapted stage unexpectedly loaded an adapter'
        if job['command']=='fit':
            supervision=root/job['supervision'];value=checksum(supervision)
            assert meta['supervision_sha256']==value
            report_path=run/'training/training_summary.json';report=json.loads(report_path.read_text())
            assert report['completion_serialization']=='public_defender_schema_order_v1'
            assert report['input_tokens']==report['optimizer_steps']*cfg['train_tokens_per_step']
            assert report['adapter_changed']
            final=run/'training/final/adapter_model.safetensors'
            assert checksum(final)==report['final_checksums']['adapter_model.safetensors']
            losses=[json.loads(line) for line in (run/'training/loss.jsonl').read_text().splitlines()]
            assert losses[-1]['step']==cfg['train_steps'], 'Fixed final checkpoint not reached'
            row.update(supervision_sha256=value,training_summary_sha256=checksum(report_path),final_adapter_sha256=checksum(final),
                       optimizer_steps_in_process=report['optimizer_steps'],input_tokens_in_process=report['input_tokens'])
            if not job.get('adapter'):
                value=checksum(run/'training/initial/adapter_model.safetensors');key=(cfg['model'],cfg['seed'])
                if key in initializations:assert initializations[key]==value, 'Conditions used different initial adapter weights'
                initializations[key]=value
                row['initial_adapter_sha256']=value
        rows.append(row)
    report={'scope':'Completed eligible scheduled stages only; compares actual parent/supervision bytes, recorded loaded checksums, round continuation and fixed last optimizer step. Failed/excluded costs remain in the resource ledger. Optimizer-checkpoint resumes additionally require their separate interruption audit.',
            'analysis_source_sha256':sha256(Path(__file__)),'freeze_sha256':sha256(root/'configs/freeze.json'),
            'verified_runs':rows,'shared_initializations':{f'{model}:{seed}':value for (model,seed),value in initializations.items()}}
    (root/'reports/tables/adapter_lineage.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'eligible_completed_stage_lineages_verified':len(rows),'distinct_model_seed_initializations':len(initializations)}))
    return report

if __name__=='__main__':audit(Path(__file__).resolve().parents[1])
