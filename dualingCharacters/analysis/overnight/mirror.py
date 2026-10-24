"""Once-per-completed-evaluation remote/local checksum comparison."""
import json
import subprocess
from pathlib import Path
from pcc.resources import sha256
from .common import ROOT,OUT,CACHE,read,write,utc,log
from .monitor import ssh


def main():
    destination=OUT/'MIRROR_CHECKS.json';prior=read(destination,{'runs':{}});changed=[]
    for mark in sorted((CACHE/'evaluations').glob('*.validation.json')):
        validation=read(mark);name=validation['run_id']
        if name in prior['runs']:continue
        local={k:v for k,v in validation['inputs'].items() if k.startswith('artifacts/runs/') and ('evaluation' in k or k.endswith('status.json') or k.endswith('adapter_model.safetensors'))}
        script='import hashlib,json,pathlib\nroot=pathlib.Path("/workspace/dualingCharacters")\npaths='+repr(list(local))+'\nresult={}\nfor name in paths:\n p=root/name\n h=hashlib.sha256()\n with p.open("rb") as f:\n  for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)\n result[name]=h.hexdigest()\nprint(json.dumps(result))\n'
        result=subprocess.run(ssh()+['python -'],input=script,text=True,capture_output=True,timeout=45)
        if result.returncode:raise RuntimeError(result.stderr[-1500:])
        remote=json.loads(result.stdout)
        if remote!=local:raise ValueError('Completed local/remote artifact mismatch: '+name)
        prior['runs'][name]={'verified_utc':utc(),'matches':True,'paths':remote};changed.append(name)
    prior['qualification']='Read-only checks of completed evaluation status, summary, compressed trace and final adapter. Previously checked immutable artifacts skipped.'
    write(destination,prior)
    if changed:log('Remote/local completed-evaluation checksums match for '+', '.join(changed)+'.')
    print(json.dumps({'newly_verified':changed,'total_checked':len(prior['runs'])}))


if __name__=='__main__':main()
