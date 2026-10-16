"""Long-running sequential controller. Uses only the existing local GPU."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from rep_sensitivity.study_execution import execute_stage
from rep_sensitivity.storage import immutable_json,utcnow

p=argparse.ArgumentParser();p.add_argument('--templates',required=True)
p.add_argument('--stage',choices=['all','secondary_validation','primary_main','secondary_main'],default='all')
p.add_argument('--after-pid',type=int);a=p.parse_args()
while a.after_pid:
    try:os.kill(a.after_pid,0)
    except ProcessLookupError:break
    time.sleep(5)
root=Path('artifacts/runs/study-execution');root.mkdir(parents=True,exist_ok=True)
try:
    if a.stage=='all':
        for stage in ('secondary_validation','primary_main','secondary_main'):
            if (root/'STOP_AFTER_CURRENT_STAGE').exists():raise RuntimeError('Explicit stop file present')
            path=Path('logs')/('study-'+stage+'.log');path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('a') as log:
                subprocess.run([sys.executable,__file__,'--templates',a.templates,'--stage',stage],
                               stdout=log,stderr=subprocess.STDOUT,check=True)
            immutable_json(root/(stage+'-complete.json'),{'stage':stage,'complete':True})
    else:execute_stage(a.stage,a.templates)
except Exception as error:
    immutable_json(root/('failure-'+str(time.time_ns())+'.json'),{
        'utc':utcnow(),'stage':a.stage,'exception':repr(error),'action':'Stopped; accepted outputs remain immutable. No automatic resampling.'})
    raise
