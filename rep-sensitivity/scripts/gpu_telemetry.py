"""Read-only GPU sampling; records occupancy and power, not kernel-time claims."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess
import time

p=argparse.ArgumentParser();p.add_argument('--duration-seconds',type=int,default=43200)
p.add_argument('--interval-seconds',type=float,default=10)
a=p.parse_args()
root=Path('artifacts/runs/telemetry');root.mkdir(parents=True,exist_ok=True)
path=root/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.jsonl')
start=time.monotonic()
with path.open('x') as f:
    while time.monotonic()-start<a.duration_seconds:
        sampled=datetime.now(timezone.utc).isoformat()
        gpu=subprocess.run(['nvidia-smi','--query-gpu=name,memory.used,memory.total,utilization.gpu,power.draw,temperature.gpu',
                            '--format=csv,noheader,nounits'],capture_output=True,text=True)
        processes=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory',
                                  '--format=csv,noheader,nounits'],capture_output=True,text=True)
        f.write(json.dumps({'utc':sampled,'elapsed_seconds':time.monotonic()-start,
                            'gpu_csv':gpu.stdout.strip(),'process_csv':processes.stdout.strip(),
                            'query_exit_codes':[gpu.returncode,processes.returncode]})+'\n')
        f.flush();os.fsync(f.fileno())
        time.sleep(a.interval_seconds)
