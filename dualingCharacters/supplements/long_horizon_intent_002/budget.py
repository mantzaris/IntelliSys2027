"""Pure cumulative-budget and one-session deadline gates; no implicit launch."""
from datetime import datetime,timezone
from pathlib import Path
import math
from pcc.resources import used_seconds
from pcc.campaign import jobs,resolve_job,load_overrides
from pcc.freeze import verify_freeze
from .common import ROOT,HERE,ARTIFACTS,read,write,utc


CAP_SECONDS=7200
CONTINGENCY_SECONDS=1800
EXIT_MARGIN_SECONDS=90
PROFILE_RESERVATION_SECONDS=900
TIERS=((3,16),(3,12),(3,8),(1,16),(1,12),(1,8))


def timestamp(value):return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()


def cumulative_extension_seconds(registry:Path):
    latest={}
    if registry.exists():
        for line in registry.read_text().splitlines():
            r=__import__('json').loads(line)
            if r['run_id'].startswith('intent002-'):latest[r['run_id']]=r
    return sum(float(r.get('gpu_reserved_seconds',0)) for r in latest.values())


def allowance(session,now_seconds,total_used_seconds,intent_used_seconds):
    if not all(math.isfinite(x) for x in (now_seconds,total_used_seconds,intent_used_seconds)) or min(total_used_seconds,intent_used_seconds)<0:raise ValueError('Invalid clock/resource accounting')
    useful=timestamp(session['useful_work_deadline_utc'])-now_seconds
    hard=timestamp(session['deadline_utc'])-now_seconds
    available=max(0,min(CAP_SECONDS-intent_used_seconds,96*3600-CONTINGENCY_SECONDS-total_used_seconds,useful-EXIT_MARGIN_SECONDS))
    return {'available_seconds':available,'hard_deadline_seconds_remaining':max(0,hard),'useful_seconds_remaining':max(0,useful),
      'intent_seconds_used':intent_used_seconds,'project_seconds_used':total_used_seconds,
      'contingency_seconds':CONTINGENCY_SECONDS,'exit_margin_seconds':EXIT_MARGIN_SECONDS}


def admit(reservation_seconds,session,now_seconds,total_used_seconds,intent_used_seconds,core_complete,review_complete,enabled):
    value=allowance(session,now_seconds,total_used_seconds,intent_used_seconds)
    reasons=[]
    if not core_complete:reasons.append('required_core_incomplete')
    if not review_complete:reasons.append('review001_not_resolved')
    if not enabled:reasons.append('extension_disabled')
    if not math.isfinite(reservation_seconds) or reservation_seconds<=0 or reservation_seconds>value['available_seconds']:reasons.append('reservation_does_not_fit_budget_and_session')
    return {**value,'admitted':not reasons,'reasons':reasons,'reservation_seconds':reservation_seconds}


def choose_tier(profile_seconds_per_generated_token,mean_tokens_per_call,load_seconds,available_seconds):
    if not all(math.isfinite(x) for x in (profile_seconds_per_generated_token,mean_tokens_per_call,load_seconds,available_seconds)) or min(profile_seconds_per_generated_token,mean_tokens_per_call)<=0 or min(load_seconds,available_seconds)<0:raise ValueError('Invalid timing')
    rows=[]
    for seeds,families in TIERS:
        calls=seeds*3*families*2*(16+64+128)
        estimate=1.5*(calls*profile_seconds_per_generated_token*mean_tokens_per_call+seeds*3*load_seconds)+EXIT_MARGIN_SECONDS
        rows.append({'seeds':[17,29,43] if seeds==3 else [17],'families':families,'model_calls':calls,'conservative_seconds':estimate})
    selected=next((r for r in rows if r['conservative_seconds']<=available_seconds),None)
    return {'candidate_tiers':rows,'selected':selected,'uses_task_scores':False}


def prerequisites():
    frozen=verify_freeze(ROOT);queue=[resolve_job(j,load_overrides(ROOT)) for j in jobs(frozen['plan'])]
    missing=[j['id'] for j in queue if read(ROOT/'artifacts/runs'/j['id']/'status.json',{}).get('status')!='completed']
    marker=read(ROOT/'artifacts/campaign_state.json',{}).get('status')=='scheduled_grid_complete'
    review=read(ROOT/'artifacts/review_001/controller_state.json',{})
    return {'core_complete':not missing and marker,'missing_core_runs':missing,'review_complete':review.get('status') in {'review_complete','not_executed_budget_gate','not_executed_post_profile_budget_gate'},'review_status':review.get('status')}


def readiness():
    session=read(HERE/'SESSION.json');state=read(ARTIFACTS/'activation.json',{'enabled':False});p=prerequisites();now=datetime.now(timezone.utc).timestamp()
    result=admit(PROFILE_RESERVATION_SECONDS,session,now,used_seconds(ROOT/'artifacts/run_registry.jsonl'),cumulative_extension_seconds(ROOT/'artifacts/run_registry.jsonl'),p['core_complete'],p['review_complete'],state.get('enabled') is True)
    result.update(checked_utc=utc(),**p,session_deadline_utc=session['deadline_utc'],launches_performed=0)
    write(HERE/'reports/INTENT_READINESS.json',result);return result


if __name__=='__main__':
    value=readiness();print({k:value[k] for k in ['admitted','reasons','intent_seconds_used','session_deadline_utc']})
