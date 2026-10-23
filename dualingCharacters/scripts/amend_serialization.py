"""Record amendment 002 after format/learning gates, without altering the design."""
from datetime import datetime,timezone
from pathlib import Path
import json
import subprocess
from pcc.resources import sha256,used_seconds
from pcc.campaign import jobs,load_overrides,resolve_job
from pcc.environment import digest
from pcc.diagnostics import jsonlines,trace_path

root=Path(__file__).resolve().parents[1]
prior=root/'configs/freeze_before_serialization_repair.json'
if sha256(prior)!='7a08b91e1e881a9780b30216f18711995fde48c54c1da17402d7688457c4cde2':raise ValueError('Prior freeze differs')
if (root/'configs/freeze.json').read_bytes()!=prior.read_bytes():raise PermissionError('Current freeze already changed; audit before another amendment')
if not (root/'artifacts/campaign_boundary_hold.json').exists():raise PermissionError('Main queue must remain held')
subprocess.run([str(root/'.venv/bin/python'),'-m','pytest','-q'],cwd=root,check=True)
frozen=json.loads(prior.read_text());evidence={}
def read(path):
    evidence[str(path.relative_to(root))]=sha256(path)
    return json.loads(path.read_text())
audit=read(root/'artifacts/corrected_serialization_audit.json')
assert all(row['corrected_accepted']==row['examples'] for row in audit['checks'])
assert audit['source_hashes']['src/pcc/training.py']==sha256(root/'src/pcc/training.py')
for model,condition in [('qwen','c3'),('qwen','c5'),('phi','c5')]:
    stem=f'pilot-format2-{model}-{condition}'
    fit=root/'artifacts/runs'/(stem+'-fit');evaluation=root/'artifacts/runs'/(stem+'-eval')
    status=read(fit/'status.json');assert status['status']=='completed'
    report=read(fit/'training/training_summary.json')
    assert report['completion_serialization']=='public_defender_schema_order_v1'
    assert report['adapter_changed'] and report['optimizer_steps']==32 and report['input_tokens']==131072
    assert sha256(fit/'training/final/adapter_model.safetensors')==report['final_checksums']['adapter_model.safetensors']
    status=read(evaluation/'status.json');assert status['status']=='completed'
    assert status['loaded_adapter_sha256']==report['final_checksums']['adapter_model.safetensors']
    summary=read(evaluation/'evaluation_summary.json')
    assert len(summary)==32 and {r['horizon'] for r in summary}=={32}
    trace=trace_path(evaluation/'evaluation.jsonl');evidence[str(trace.relative_to(root))]=sha256(trace)
    turns=jsonlines(trace);assert len(turns)==1024
    assert all(r['generation']['parsed'] or r['generation']['generation_capped'] for r in turns)
    # A capped incomplete response is a retained scored failure, not a broken grammar.
    # Deliberately no task-success threshold or model/condition selection.
refresh=root/'artifacts/runs/pilot-format2-refresh'
status=read(refresh/'status.json');assert status['status']=='completed'
assert status['loaded_adapter_sha256']==json.loads((root/'artifacts/runs/pilot-format2-qwen-c5-fit/training/training_summary.json').read_text())['final_checksums']['adapter_model.safetensors']
counts=read(refresh/'supervision.counts.json');assert counts['clean_valid'] and counts['failed_eligible']
# Pure design and queue hashes remain identical; only four restart paths differ.
assert json.loads((root/'configs/study_plan.json').read_text())==frozen['plan']
assert digest(list(jobs(frozen['plan'])))==frozen['queue_hash']
overrides=load_overrides(root)
assert len(overrides)==4 and all(name.startswith('main-qwen-c1-17-') for name in overrides)
forecast=read(root/'reports/tables/serialization_budget_reforecast.json')
assert forecast['total_core_forecast_hours']<=96
names=sorted(set(frozen['files'])|{'src/pcc/eligibility.py','configs/serialization_restarts.json','scripts/amend_serialization.py'})
if subprocess.run(['git','branch','--show-current'],cwd=root,capture_output=True,text=True,check=True).stdout.strip()!='main':raise PermissionError('Author requires main')
dirty=subprocess.run(['git','status','--porcelain','--',*names],cwd=root,capture_output=True,text=True,check=True).stdout
if dirty:raise PermissionError('Commit amended inputs before freezing: '+dirty)
commit=subprocess.run(['git','rev-parse','HEAD'],cwd=root,capture_output=True,text=True,check=True).stdout.strip()
changed={name:{'old':frozen['files'].get(name),'new':sha256(root/name)} for name in names if frozen['files'].get(name)!=sha256(root/name)}
frozen['files']={name:sha256(root/name) for name in names};frozen['code_commit']=commit
frozen['amendments'].append({'id':'002','recorded_utc':datetime.now(timezone.utc).isoformat(),'reason':'Repair persisted-supervision order to match the unchanged inference grammar; explicit exclusions and frozen rerun aliases; no design or estimator change.',
    'report':'reports/SERIALIZATION_AMENDMENT_002.md','source_commit':commit,'previous_freeze_sha256':sha256(prior),'changed_files':changed,'gate_evidence':evidence,
    'test_access_at_decision':'Baseline and historical pilot outcomes known. Hold and exclusions decided by CPU syntax audit before completed trained locked-test metrics were inspected.',
    'reserved_gpu_hours_at_amendment':used_seconds(root/'artifacts/run_registry.jsonl')/3600,
    'resolved_queue_hash':digest([resolve_job(job,overrides) for job in jobs(frozen['plan'])])})
frozen['gates']['saved_target_inference_grammar_compatibility']=True
frozen['gates']['corrected_parameter_updates_and_evaluations_both_families']=True
frozen['gates']['corrected_trained_defender_refresh']=True
(root/'configs/freeze.json').write_text(json.dumps(frozen,indent=2)+'\n')
print(json.dumps({'amendment':'002','freeze_sha256':sha256(root/'configs/freeze.json'),'code_commit':commit,'files':len(names),'changed_files':list(changed)},indent=2))
