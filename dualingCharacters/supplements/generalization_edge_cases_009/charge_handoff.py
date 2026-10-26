"""Charge only unrecorded exclusive-window overhead; zero inference, idempotent."""
import os,shlex,subprocess
from .common import *
def main():
 if (HERE/'reports/HANDOFF_ACCOUNTING.json').exists():
  print('Already reconciled; no duplicate charge');return
 from supplements.review_001.controller import connection
 r=read(HERE/'reports/RESOURCES.json');row={'run_id':'edge009-exclusive-overhead-v1','status':'completed','accounting_only':True,'stage009':True,'started_utc':read(ART/'handoff.json')['exclusive_start_utc'],'ended_utc':read(HERE/'reports/CORE_RESUMPTION.json')['utc'],'gpu_reserved_seconds':r['additional_unledgered_stage009_seconds'],'model_calls':0,'input_tokens':0,'output_tokens':0,'train_tokens':0,'peak_vram_bytes':0,'code_commit':read(HERE/'SESSION.json')['input_commit'],'reason':'Full exclusive handoff window minus all five measured stage009 model/supervisor reservations. No inference or GPU ownership change.','source_window_seconds':r['exclusive_handoff_seconds'],'already_charged_model_seconds':r['stage_ledger_seconds']}
 assert row['gpu_reserved_seconds']>0 and row['source_window_seconds']<=5400
 os.environ.update(read(ART/'original_owner_private.json')['environment']);ssh,target,remote=connection()
 script="from pathlib import Path; import json; from pcc.resources import append_json,used_seconds; row="+repr(row)+"; root=Path('artifacts'); p=root/'runs'/row['run_id']/'status.json'\nif p.exists():\n assert json.loads(p.read_text())==row\nelse:\n assert used_seconds(root/'run_registry.jsonl')+row['gpu_reserved_seconds']<345600\n p.parent.mkdir();p.write_text(json.dumps(row,indent=2)+'\\n');append_json(root/'run_registry.jsonl',row)\nprint(json.dumps({'accounting_only':True,'charged_seconds':row['gpu_reserved_seconds']}))"
 out=subprocess.check_output(ssh+[target,'cd '+shlex.quote(remote)+' && PYTHONPATH=src .venv-infer/bin/python -c '+shlex.quote(script)],text=True,timeout=40)
 subprocess.run(['bash','scripts/sync.sh','pull'],cwd=ROOT,check=True,timeout=90)
 write(HERE/'reports/HANDOFF_ACCOUNTING.json',row);print(out)
if __name__=='__main__':main()
