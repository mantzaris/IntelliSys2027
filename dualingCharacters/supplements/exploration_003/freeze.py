"""A separate pre-summary scientific freeze; no changes to prior freezes."""
import argparse
import subprocess
from .common import ROOT,HERE,read,write,sha256,utc,verify_prior,log

def create():
    path=HERE/'SCIENTIFIC_MANIFEST.json'
    if path.exists():raise FileExistsError('An explicit versioned amendment is required')
    prior=verify_prior()
    names=['PROTOCOL.md','CODEBOOK.md','EVIDENCE_SNAPSHOT.json','DATA_AUDIT.json','SOURCE_AUDIT.json','requirements-cpu.txt']
    files={p.name:sha256(p) for p in sorted([*HERE.glob('*.py'),*(HERE/n for n in names)])}
    result={'frozen_utc':utc(),'files':files,'prior_freezes':prior,
        'code_commit_before_supplement':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'known_outcomes':'Main negative/mixed C5 comparisons and C1 seed reversal, prior intent trajectory results, approximate pilot slot/value repetition C3~74%, C5~89-90%; one C3 raw action inspected for schema. No new comparative descriptor summaries computed.',
        'classification':'Post-outcome exploratory analysis, frozen before its comparative category summaries',
        'new_gpu_calls':0,'model_judge_calls':0}
    write(path,result);log('Froze exploration scientific definitions/code and locked population before first comparative descriptor summaries.')
    return result

def verify():
    from .analysis import verify_science
    return verify_science()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['create','verify']);a=p.parse_args()
    print({'operation':a.command,'files':len(globals()[a.command]() ['files'])})
