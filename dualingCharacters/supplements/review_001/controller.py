"""One CPU waiter, then serialized review diagnostics and final reporting."""
from pathlib import Path
import fcntl
import os
import shlex
import subprocess
import sys
import time
from pcc.campaign import run_and_mirror,commit_generated_package
from pcc.resources import sha256,used_seconds
from .common import ROOT,HERE,ARTIFACTS,read,write
from .freeze import verify,bind
from .allocation import review_seconds,freeze_allocation


def state(status,**values):
    write(ARTIFACTS/'controller_state.json',{'status':status,'pid':os.getpid(),'updated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
      'controller_sha256':sha256(Path(__file__)),**values})


def core_marker_ready():
    try:return read(ROOT/'artifacts/campaign_state.json').get('status')=='scheduled_grid_complete'
    except (FileNotFoundError,ValueError):return False


def connection():
    host=os.environ['PCC_SSH_HOST'];port=os.environ['PCC_SSH_PORT'];remote=os.environ.get('PCC_REMOTE_DIR','/workspace/dualingCharacters')
    ssh=['ssh','-F','/dev/null','-i',os.environ.get('PCC_SSH_KEY',str(Path.home()/'.ssh/id_rsa')),'-p',port,
      '-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+os.environ.get('PCC_KNOWN_HOSTS','/tmp/intellisys-runpod-known-hosts')]
    return ssh,'root@'+host,remote


def upload(ssh,target,remote):
    # Source outside the 58 frozen paths only; never run broad source sync.
    subprocess.run(ssh+[target,'mkdir -p '+shlex.quote(remote+'/supplements/review_001')+' '+shlex.quote(remote+'/artifacts/review_001')],check=True)
    for source,dest in [(HERE,remote+'/supplements/review_001/'),(ARTIFACTS/'inputs',remote+'/artifacts/review_001/inputs/')]:
        subprocess.run(['rsync','-az','--exclude=__pycache__','--exclude=results','-e',shlex.join(ssh),str(source)+'/',target+':'+dest],check=True)
    files=[ARTIFACTS/name for name in ('bindings.json','allocation.json') if (ARTIFACTS/name).exists()]
    subprocess.run(['rsync','-az','-e',shlex.join(ssh),*[str(p) for p in files],target+':'+remote+'/artifacts/review_001/'],check=True)
    # Core may have an authorized infrastructure-resume map; prerequisites use it.
    resume=ROOT/'artifacts/campaign_resume.json'
    if resume.exists():subprocess.run(['rsync','-az','-e',shlex.join(ssh),str(resume),target+':'+remote+'/artifacts/'],check=True)


def execute(stage,ssh,target,remote):
    run_id=f'review001-{stage}-17-v1';status=ROOT/f'artifacts/runs/{run_id}/status.json'
    if status.exists():
        if read(status)['status']=='completed':return
        raise RuntimeError('Existing incomplete review run requires explicit audit; no automatic retry: '+run_id)
    state('running',stage=stage,run_id=run_id)
    env=['env','PYTHONPATH=src',f'HF_HOME={remote}/artifacts/hf-cache',f'PCC_CODE_COMMIT={verify()["code_commit"]}','VLLM_WORKER_MULTIPROC_METHOD=spawn']
    cmd='cd '+shlex.quote(remote)+' && '+shlex.join([*env,'.venv-infer/bin/python','-m','supplements.review_001.gpu',stage])
    rc=run_and_mirror(ssh+[target,cmd],ROOT,ARTIFACTS/(run_id+'.log'))
    subprocess.run(['bash','scripts/sync.sh','pull'],cwd=ROOT,check=True)
    if rc:raise RuntimeError('Supplement failed; raw evidence/costs retained and mirrored: '+run_id)
    if read(status)['status']!='completed':raise RuntimeError('Missing completed mirrored run: '+run_id)


def main():
    ARTIFACTS.mkdir(parents=True,exist_ok=True)
    own=(ARTIFACTS/'controller.lock').open('a+');fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
    verify();state('waiting_for_core',gpu_operations_started=0)
    while not core_marker_ready():time.sleep(30)
    shared=(ROOT/'artifacts/campaign.lock').open('a+')
    while True:
        try:fcntl.flock(shared,fcntl.LOCK_EX|fcntl.LOCK_NB);break
        except BlockingIOError:time.sleep(30)
    review_failed=False
    try:
        bind() # checks all actual core run statuses and fixed checkpoint bytes
        from .inputs import prepare
        from .severity import prepare as severity_inputs
        prepare();severity_inputs()
        remaining=min(7200-review_seconds(),96*3600-1800-used_seconds(ROOT/'artifacts/run_registry.jsonl'))
        # Fixed 15-minute profiling launch reserve, not a spending target.
        if remaining<900:
            state('not_executed_budget_gate',available_seconds=remaining,reason='Less than fixed 15-minute profiling launch reserve after contingency')
        else:
            ssh,target,remote=connection();upload(ssh,target,remote);execute('profile',ssh,target,remote)
            allocation=freeze_allocation() # reads timing and costs only, never task scores
            write(HERE/'results/allocation.json',allocation);upload(ssh,target,remote)
            for stage in allocation['stages']:execute(stage,ssh,target,remote)
            state('review_complete' if allocation['stages'] else 'not_executed_post_profile_budget_gate',allocation=allocation)
    except Exception as error:
        review_failed=True;state('review_incomplete',error=str(error))
    finally:
        fcntl.flock(shared,fcntl.LOCK_UN);shared.close()
    # This is the sole coordinated path for the former optional waiter.
    remaining=96-used_seconds(ROOT/'artifacts/run_registry.jsonl')/3600
    if not review_failed and remaining>=4+90/3600:
        rc=subprocess.run([sys.executable,'analysis/run_unseen_profiles.py'],cwd=ROOT).returncode
        if rc:write(ARTIFACTS/'unseen_followup_error.json',{'returncode':rc,'reason':'Prior supplement failed; preserve existing artifacts'})
    else:
        write(ROOT/'artifacts/unseen_profiles_controller_state.json',{'status':'not_executed_review_priority_or_contingency',
          'remaining_hours':remaining,'review_failed':review_failed,'reason':'Review has priority; old 3.5-hour gate plus 0.5-hour contingency and 90-second final-batch margin required'})
    shared=(ROOT/'artifacts/campaign.lock').open('a+');fcntl.flock(shared,fcntl.LOCK_EX)
    subprocess.run(['bash','analysis/regenerate_all.sh'],cwd=ROOT,check=True)
    subprocess.run([sys.executable,'-m','supplements.review_001.regenerate'],cwd=ROOT,check=True)
    commit_generated_package(ROOT,'Core complete; review execution, resource gates and any failures recorded under the two-hour cap; inspect review_001 status for omitted/failed modules. Human ratings and scientific author review pending')
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()!='main':raise RuntimeError('Main required')
    paths=['supplements/review_001']
    subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
    if subprocess.run(['git','diff','--cached','--quiet','--',*paths],cwd=ROOT).returncode:
        subprocess.run(['git','commit','--only','-m','Record exploratory review diagnostics and provenance','--',*paths],cwd=ROOT,check=True)
    write(ARTIFACTS/'final_report_state.json',{'status':'completed','review_state':read(ARTIFACTS/'controller_state.json'),'gpu_operations_in_final_reporting':0})


if __name__=='__main__':main()
