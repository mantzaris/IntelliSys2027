"""Rebuild the local review package after every required study stage completes.

Safe to invoke repeatedly from the mirror loop. It neither runs inference nor
submits/pushes anything. A blocked/incomplete study stays explicitly incomplete.
"""
import hashlib
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime,timezone

root=Path(__file__).resolve().parents[1]
os.chdir(root)
parser=argparse.ArgumentParser();parser.add_argument('--commit',action='store_true');args=parser.parse_args()
suites=('main-v7','supporting-v7','live-v8')
paths=[Path('results',suite,'analysis.json') for suite in suites]
if not all(p.exists() and json.loads(p.read_text()).get('complete') for p in paths):
    raise SystemExit(0)
identity_inputs=sorted(p for suite in ('validation-v7',*suites,'live-development-v8')
                       for p in Path('artifacts/runs',suite).glob('*/scores/*.json'))
identity_inputs += [Path(__file__),Path('manuscript/main.tex'),Path('manuscript/abstract-development.tex'),
    *[Path('scripts',name) for name in ('build_manuscript_tables.py','build_study_figures.py','build_study_report.py','audit_runs.py','check_manuscript.py','analyze_control_matching.py')],
    *[Path('src/rep_sensitivity',name) for name in ('analysis.py','aux_analysis.py','metrics.py')]]
identity=hashlib.sha256(b''.join(hashlib.sha256(p.read_bytes()).digest() for p in identity_inputs)).hexdigest()
marker=Path('records/review-package.json')
commit_marker=Path('artifacts/review-package-commit.json')
already_committed=commit_marker.exists() and json.loads(commit_marker.read_text()).get('completion_input_sha256')==identity
if marker.exists() and json.loads(marker.read_text()).get('completion_input_sha256')==identity and (not args.commit or already_committed):
    raise SystemExit(0)
env=dict(os.environ,PYTHONPATH=str(root/'src'),MPLCONFIGDIR=str(root/'artifacts/matplotlib'))
for suite in ('supporting-v7','live-v8','controls-development-v7','live-development-v8'):
    # Recompute only deterministic analysis fields; accepted responses/scores stay immutable.
    subprocess.run([sys.executable,'-m','rep_sensitivity.aux_analysis','artifacts/runs/'+suite,'results/'+suite],env=env,check=True)
subprocess.run([sys.executable,'scripts/analyze_control_matching.py','artifacts/runs/supporting-v7','results/supporting-v7'],env=env,check=True)
for suite in ('validation-v7',*suites):
    subprocess.run([sys.executable,'scripts/audit_runs.py','artifacts/runs/'+suite],env=env,check=True)
    audit=json.loads(Path('records/audits',suite+'.json').read_text())
    if audit['models_without_manifest'] or any(not r['run_complete'] or not r['accepted_calls_match_completed_scores']
            or r['scored_trajectories']!=r['planned_trajectories'] for r in audit['models'].values()):
        raise RuntimeError('Raw outputs are not yet fully mirrored and audited: '+suite)
for script in ('build_study_figures.py','build_manuscript_tables.py','build_study_report.py'):
    subprocess.run([sys.executable,'scripts/'+script],env=env,check=True)
subprocess.run(['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','main.tex'],cwd='manuscript',env=env,check=True)
subprocess.run([sys.executable,'scripts/check_manuscript.py'],env=env,check=True)
files=sorted(p for folder in ('results','records/audits','records/freezes','manuscript/generated')
             for p in Path(folder).rglob('*') if p.is_file() and 'interim' not in str(p))
files+=[Path('manuscript/main.pdf'),Path('manuscript/main.tex')]
record={'assembled_utc':datetime.now(timezone.utc).isoformat(),'completion_input_sha256':identity,
        'completed_analysis_stages':list(suites),'human_scientific_review':'pending','submission_ready':False,
        'raw_completeness_checked':True,
        'compiled_pdf':'manuscript/main.pdf','review_points':'SCIENTIFIC_REVIEW.md',
        'raw_artifacts':'artifacts/runs/; locally mirrored, excluded from Git',
        'files':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
marker.write_text(json.dumps(record,indent=2)+'\n')
if args.commit:
    branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip()
    if branch!='main':raise RuntimeError('Automatic checkpoint requires existing main branch; no branch is created')
    if subprocess.check_output(['git','diff','--cached','--name-only'],text=True).strip():
        raise RuntimeError('Existing staged user changes; package is built but its commit requires review')
    paths=['results','configs/frozen','records/freezes','records/manifests','records/environment',
           'records/audits','records/study-report-status.json','records/review-package.json',
           'records/manuscript-checks.json','manuscript/generated','manuscript/main.pdf']
    # Restrict staging to compact, generated study records. Source/user edits remain untouched.
    subprocess.run(['git','add','--',*paths],check=True)
    subprocess.run(['git','diff','--cached','--check'],check=True)
    if subprocess.check_output(['git','diff','--cached','--name-only'],text=True).strip():
        subprocess.run(['git','commit','-m','Assemble completed frozen study results for scientific review'],check=True)
    commit_marker.write_text(json.dumps({'completion_input_sha256':identity,
        'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()},indent=2)+'\n')
print(json.dumps({'review_package_assembled':True,'human_scientific_review':'pending','submitted':False}))
