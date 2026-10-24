"""Once-per-completed-stage remote/local checks; skip verified immutable paths."""
import json
import subprocess
from pathlib import Path
from pcc.resources import sha256
from .common import ROOT,OUT,CACHE,read,write,utc,log
from .monitor import ssh


def main():
    destination=OUT/'MIRROR_CHECKS.json';prior=read(destination,{'runs':{}});changed=[]
    candidates={}
    for mark in sorted((CACHE/'evaluations').glob('*.validation.json')):
        validation=read(mark);name=validation['run_id']
        candidates[name]={k:v for k,v in validation['inputs'].items() if k.startswith('artifacts/runs/') and ('evaluation' in k or k.endswith('status.json') or k.endswith('adapter_model.safetensors'))}
    for provenance in ('collection_provenance.json','exposure_provenance.json'):
        for name,item in read(OUT/provenance)['runs'].items():
            candidates[name]={k:v for k,v in item['inputs'].items() if k.startswith('artifacts/runs/')}
            if provenance=='exposure_provenance.json':
                report=read(ROOT/f'artifacts/runs/{name}/training/training_summary.json')
                for filename,value in report['final_checksums'].items():
                    path=f'artifacts/runs/{name}/training/final/{filename}'
                    candidates[name][path]=value
                # Newly finished overnight fits get an explicit resumable-optimizer mirror check.
                # Do not repeatedly hash optimizer archives from unchanged earlier fits.
                if not item['reused_verified_audit']:
                    path=f'artifacts/runs/{name}/training/optimizer.pt'
                    if name not in prior['runs']:candidates[name][path]=sha256(ROOT/path)
                    elif path in prior['runs'][name]['paths']:candidates[name][path]=prior['runs'][name]['paths'][path]
    already={k:v for entry in prior['runs'].values() for k,v in entry['paths'].items()}
    for name,local in candidates.items():
        if name in prior['runs']:
            assert all(prior['runs'][name]['paths'].get(k)==v for k,v in local.items()), 'Completed stage evidence changed: '+name
            continue
        for path,value in local.items():
            if path in already:assert already[path]==value, 'Contradictory immutable artifact hash'
            else:assert sha256(ROOT/path)==value, 'Local artifact differs from validated evidence: '+path
        unchecked={k:v for k,v in local.items() if k not in already}
        script='import hashlib,json,pathlib\nroot=pathlib.Path("/workspace/dualingCharacters")\npaths='+repr(list(unchecked))+'\nresult={}\nfor name in paths:\n p=root/name\n h=hashlib.sha256()\n with p.open("rb") as f:\n  for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)\n result[name]=h.hexdigest()\nprint(json.dumps(result))\n'
        result=subprocess.run(ssh()+['python -'],input=script,text=True,capture_output=True,timeout=45)
        if result.returncode:raise RuntimeError(result.stderr[-1500:])
        remote=json.loads(result.stdout)
        if remote!=unchecked:raise ValueError('Completed local/remote artifact mismatch: '+name)
        prior['runs'][name]={'verified_utc':utc(),'matches':True,'paths':local};changed.append(name);already.update(remote)
    prior['qualification']='Completed-stage read-only checks: evaluation and collection traces, supervision, status, loss logs, training summaries and final adapters. Newly completed overnight fits additionally verify optimizer checkpoint bytes. Previously checked immutable paths are reused; older unchanged optimizer archives are not repeatedly hashed.'
    write(destination,prior)
    if changed:log('Remote/local completed-stage checksums match for '+', '.join(changed)+'.')
    print(json.dumps({'newly_verified':changed,'total_checked':len(prior['runs'])}))


if __name__=='__main__':main()
