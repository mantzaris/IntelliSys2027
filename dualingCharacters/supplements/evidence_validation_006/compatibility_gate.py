"""Fail-closed operational admission; no new waiter or inference on import."""
from datetime import datetime,timezone
from .common import *
from .compatibility_design import IDENTITY

def extension_seconds(registry):
 latest={}
 if Path(registry).exists():
  for line in Path(registry).read_text().splitlines():
   r=json.loads(line);latest[r['run_id']]=r
 # Explicit budget identity OR original lineage prefix; renaming never resets allowance.
 return sum(float(r.get('gpu_reserved_seconds',0)) for r in latest.values() if r.get('budget_identity')==IDENTITY or r['run_id'].startswith('dialogue005-compat'))

def check_admission(request,now_utc,project_used,extension_used,core_complete,review_complete):
 if request.get('enabled') is not True:raise PermissionError('Extension disabled and unscheduled')
 if not core_complete or not review_complete:raise PermissionError('Required core and review mechanism work must be complete')
 if not request.get('existing_owner_authorization') or not request.get('owner_dispatch_id'):raise PermissionError('Existing owner authorization is missing')
 deadline=datetime.fromisoformat(request['session_deadline_utc']);cutoff=datetime.fromisoformat(request['useful_work_cutoff_utc'])
 if deadline.tzinfo is None or cutoff.tzinfo is None:raise ValueError('UTC-aware absolute deadlines required')
 if (deadline-cutoff).total_seconds()<2700:raise ValueError('Reserve final45 minutes for verification')
 bound=float(request['conservative_total_seconds']);obligations=float(request['remaining_obligations_seconds'])
 if bound<=0 or obligations<0:raise ValueError('Invalid resource estimate')
 if bound<7200:raise PermissionError('Unprofiled fixed grid retains conservative two-hour admission bound; no scope reduction')
 if bound>(cutoff-now_utc).total_seconds():raise PermissionError('Full grid bound does not fit useful-work window')
 if extension_used+bound>7200:raise PermissionError('Cumulative compatibility cap exceeded; earlier attempts count')
 if project_used+bound+obligations+1800>96*3600:raise PermissionError('Project obligations and contingency do not fit')
 return {'maximum_reservation_seconds':bound,'worker_seconds':int(bound)-30,'hard_timeout_seconds':int(bound)-15,'contingency_seconds':1800}

def verify_freeze():
 doc=read(HERE/'compatibility/FREEZE.json')
 for path,expected in doc['files'].items():assert sha(ROOT/path)==expected,'Frozen compatibility dependency changed: '+path
 return doc

def prerequisites():
 from pcc.freeze import verify_freeze as core_freeze
 from pcc.campaign import jobs,resolve_job,load_overrides
 actual=[resolve_job(j,load_overrides(ROOT))['id'] for j in jobs(core_freeze(ROOT)['plan'])]
 complete=all((ROOT/f'artifacts/runs/{r}/status.json').exists() and read(ROOT/f'artifacts/runs/{r}/status.json').get('status')=='completed' for r in actual)
 state=ROOT/'artifacts/review_001/controller_state.json';allocation=ROOT/'artifacts/review_001/allocation.json'
 review=False
 if state.exists() and allocation.exists():
  alloc=read(allocation);stages=alloc.get('stages',[])
  # Mechanism work is a prerequisite, not skipped to make room for this extension.
  review=read(state).get('status')=='review_complete' and 'conflict' in stages and all(
   (ROOT/f'artifacts/runs/review001-{s}-17-v1/status.json').exists() and read(ROOT/f'artifacts/runs/review001-{s}-17-v1/status.json').get('status')=='completed' for s in ['profile']+stages)
 return complete,review
