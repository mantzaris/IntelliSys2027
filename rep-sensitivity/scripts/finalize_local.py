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
env=dict(os.environ,PYTHONPATH=str(root/'src'),MPLCONFIGDIR=str(root/'artifacts/matplotlib'))
if Path('records/amendments/mechanism-v1.json').exists():
    subprocess.run([sys.executable,'scripts/refresh_mechanism_results.py'],env=env,check=True)
# Update only completed evidence blocks even while later frozen stages continue.
# This also updates the abstract/conclusion after a complete main analysis arrives.
subprocess.run([sys.executable,'scripts/build_manuscript.py'],env=env,check=True)
from manuscript_content import compile_if_changed
compile_if_changed()
suites=('main-v7','supporting-v7','live-v8')
paths=[Path('results',suite,'analysis.json') for suite in suites]
if not all(p.exists() and json.loads(p.read_text()).get('complete') for p in paths):
    raise SystemExit(0)
extension_suites=('mechanism-development-v1','fresh-probe-v1','mechanism-validation-v1')
if Path('records/amendments/mechanism-v1.json').exists():
    extension_stage=Path('artifacts/runs/mechanism-execution/extension-stage.json')
    if not extension_stage.exists() or json.loads(extension_stage.read_text()).get('returncode')!=0:
        raise SystemExit(0)  # Original completion does not complete the amendment.
    if not all(Path('results',s,'analysis.json').exists() and
            json.loads(Path('results',s,'analysis.json').read_text()).get('complete') for s in extension_suites):
        raise SystemExit(0)
    heldout=Path('results/mechanism-heldout-v1/analysis.json')
    if heldout.exists() and json.loads(heldout.read_text()).get('complete'):
        extension_suites+=('mechanism-heldout-v1',)
    elif not Path('artifacts/runs/mechanism-execution/heldout-not-launched.json').exists():
        raise SystemExit(0)
else:extension_suites=()
if Path('configs/frozen/root-diagnostic-v1.json').exists():
    root_result=Path('results/root-diagnostic-v1/analysis.json')
    if not root_result.exists() or not json.loads(root_result.read_text()).get('complete'):
        raise SystemExit(0)
    extension_suites+=('root-diagnostic-v1',)
if Path('configs/frozen/objective-confirmation-v1.json').exists():
    objective_result=Path('results/objective-confirmation-v1/analysis.json')
    if not objective_result.exists() or not json.loads(objective_result.read_text()).get('complete'):
        raise SystemExit(0)  # A budget stop remains explicitly incomplete, never review-ready.
if Path('configs/frozen/numerical-preservation-v1.json').exists():
    numerical_result=Path('results/numerical-preservation-v1/analysis.json')
    numerical_done=numerical_result.exists() and json.loads(numerical_result.read_text()).get('complete')
    if not numerical_done and not Path('artifacts/runs/numerical-preservation-execution/not-launched.json').exists():
        raise SystemExit(0)  # Keep mirroring while the final-priority diagnostic waits/runs.
if Path('configs/frozen/adjacent-explorations-v1.json').exists():
    adjacent_result=Path('results/adjacent-explorations-v1/analysis.json')
    adjacent_done=adjacent_result.exists() and json.loads(adjacent_result.read_text()).get('complete')
    if not adjacent_done and not Path('artifacts/runs/adjacent-explorations-execution/not-launched.json').exists():
        raise SystemExit(0)  # Protected work completes first; retain the final mirror until this bounded stage resolves.
identity_inputs=sorted(p for suite in ('validation-v7',*suites,'live-development-v8')
                       for p in Path('artifacts/runs',suite).glob('*/scores/*.json'))
identity_inputs += [Path(__file__),Path('manuscript/main.tex'),Path('scripts/build_manuscript.py'),Path('scripts/manuscript_content.py'),
    *[Path('scripts',name) for name in ('build_manuscript_tables.py','build_study_figures.py','build_study_report.py','audit_runs.py','check_manuscript.py','analyze_control_matching.py')],
    *[Path('src/rep_sensitivity',name) for name in ('analysis.py','aux_analysis.py','metrics.py')]]
identity_inputs += [p for suite in extension_suites for p in Path('artifacts/runs',suite).glob('*/scores/*.json')]
identity_inputs += [Path('scripts/build_mechanism_report.py'),*[Path('src/rep_sensitivity',name) for name in
    ('targeted_analysis.py','targeted_audit.py','fresh_analysis.py','mechanism.py','root_diagnostic.py','pilot_interpretation.py')]]
identity_inputs += [Path('scripts/build_pilot_interpretation.py'),Path('scripts/audit_root_information.py'),Path('scripts/audit_root_information_v2.py'),Path('scripts/visible_information_v2.py')]
identity_inputs += list(Path('artifacts/runs/objective-confirmation-v1').glob('*/scores/*.json'))
identity_inputs += [Path('scripts/analyze_objective_confirmation.py'),Path('scripts/build_empirical_update.py'),Path('scripts/build_completed_extensions.py')]
identity_inputs += list(Path('artifacts/runs/numerical-preservation-v1').glob('*/scores/*.json'))
identity_inputs += [Path('scripts/analyze_numerical_preservation.py'),Path('scripts/build_numerical_report.py'),
                    Path('results/numerical-pipeline-v1/analysis.json'),Path('scripts/visible_information_v3.py'),
                    Path('scripts/audit_visible_support_v3.py')]
identity_inputs += list(Path('artifacts/runs/adjacent-explorations-v1').glob('*/scores/*.json'))
identity_inputs += [Path('scripts/build_adjacent_supplement.py'),Path('src/rep_sensitivity/adjacent_analysis.py')]
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
for suite in extension_suites:
    module='fresh_analysis' if suite.startswith('fresh') else 'targeted_analysis'
    if suite.startswith('root-'):
        from rep_sensitivity.root_diagnostic import analyze
        analyze('artifacts/runs/'+suite,'results/'+suite)
        subprocess.run([sys.executable,'scripts/audit_root_information.py'],env=env,check=True)
        subprocess.run([sys.executable,'scripts/audit_root_information_v2.py'],env=env,check=True)
    else:subprocess.run([sys.executable,'-m','rep_sensitivity.'+module,'artifacts/runs/'+suite,'results/'+suite],env=env,check=True)
    audit=json.loads(Path('results',suite,'analysis.json').read_text())['physical_resource_inventory']
    if audit['unscored_accepted_calls']:raise RuntimeError('Incomplete raw inventory: '+suite)
subprocess.run([sys.executable,'scripts/build_mechanism_report.py'],env=env,check=True)
subprocess.run([sys.executable,'scripts/interpret_pilot.py'],env=env,check=True)
subprocess.run([sys.executable,'scripts/build_pilot_interpretation.py'],env=env,check=True)
subprocess.run([sys.executable,'scripts/build_empirical_update.py'],env=env,check=True)
subprocess.run([sys.executable,'scripts/build_numerical_report.py'],env=env,check=True)
subprocess.run([sys.executable,'scripts/build_adjacent_supplement.py'],env=env,check=True)
subprocess.run(['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','main.tex'],cwd='manuscript',env=env,check=True)
subprocess.run([sys.executable,'scripts/check_manuscript.py'],env=env,check=True)
files=sorted(p for folder in ('results','records/audits','records/freezes','records/manuscript-sources')
             for p in Path(folder).rglob('*') if p.is_file() and 'interim' not in str(p))
files+=[Path('manuscript/main.tex'),*Path('manuscript').glob('*.pdf')]
record={'assembled_utc':datetime.now(timezone.utc).isoformat(),'completion_input_sha256':identity,
        'completed_analysis_stages':list(suites)+list(extension_suites)+(['objective-confirmation-v1'] if Path('results/objective-confirmation-v1/analysis.json').exists() else []),'human_scientific_review':'pending','submission_ready':False,
        'amendment_heldout_not_launched':Path('artifacts/runs/mechanism-execution/heldout-not-launched.json').exists(),
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
           'records/manuscript-checks.json','records/mechanism-report-status.json','records/completed-extensions-status.json','records/planning',
           'records/manuscript-sources','records/manuscript-content-v6.json',
           'manuscript/main.tex',*[str(p) for p in Path('manuscript').glob('*.pdf')],
           'PILOT_MECHANISM_AUDIT.md','PILOT_INTERPRETATION.md']
    # Restrict staging to compact, generated study records. Source/user edits remain untouched.
    subprocess.run(['git','add','--',*paths],check=True)
    subprocess.run(['git','diff','--cached','--check'],check=True)
    if subprocess.check_output(['git','diff','--cached','--name-only'],text=True).strip():
        subprocess.run(['git','commit','-m','Assemble completed frozen study results for scientific review'],check=True)
    commit_marker.write_text(json.dumps({'completion_input_sha256':identity,
        'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()},indent=2)+'\n')
print(json.dumps({'review_package_assembled':True,'human_scientific_review':'pending','submitted':False}))
