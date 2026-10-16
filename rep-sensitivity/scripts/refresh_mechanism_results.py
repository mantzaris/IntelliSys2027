"""Reanalyze fully mirrored extension suites using the current versioned scorer.

The archived GPU controller retains its original analysis source. A dated,
pre-inference analysis correction narrows the four-dose estimate to the same
world/base subset as the other doses. This hook applies it locally as soon as a
suite is complete; it never alters accepted calls, score rows or primary contrasts.
"""
import json
import subprocess
import sys
from pathlib import Path
from rep_sensitivity.schema import digest
from rep_sensitivity.targeted_analysis import load,summarize
from rep_sensitivity.fresh_analysis import summarize as summarize_fresh
from rep_sensitivity.root_diagnostic import analyze as summarize_root

changed=[]
for suite in ('mechanism-development-v1','fresh-probe-v1','mechanism-validation-v1','mechanism-heldout-v1','root-diagnostic-v1'):
    root=Path('artifacts/runs',suite)
    if not (root/'manifest.json').exists():continue
    manifest=json.loads((root/'manifest.json').read_text());model=manifest['config']['model']
    if suite.startswith(('fresh','root-')):
        rows=[r for p in sorted((root/model/'scores').glob('*.json')) for r in json.loads(p.read_text())]
        complete=len(rows)==manifest['trajectories'];module='fresh_analysis.py';analyze=summarize_fresh
        if suite.startswith('root-'):module='root_diagnostic.py';analyze=summarize_root
    else:
        _,rows,incomplete=load(root);complete=not incomplete;module='targeted_analysis.py';analyze=summarize
    if not complete:continue
    hashes={h for r in rows for h in r['request_hashes']}
    if not all((root/model/'calls'/(h+'.json.gz')).exists() for h in hashes):continue
    destination=Path('results',suite,'analysis.json')
    source=digest(Path('src/rep_sensitivity',module).read_text())
    if destination.exists():
        old=json.loads(destination.read_text())
        supplementary_current=True
        if suite.startswith('root-'):
            extra=destination.parent/'visible-information-v2.json'
            supplementary_current=extra.exists() and json.loads(extra.read_text()).get('analysis_source_sha256')==digest(Path('scripts/audit_root_information_v2.py').read_text()) and json.loads(extra.read_text()).get('scorer_source_sha256')==digest(Path('scripts/visible_information_v2.py').read_text())
        if old.get('complete') and old.get('analysis_source_sha256')==source and supplementary_current:continue
    analyze(root,destination.parent);changed.append(suite)
    if suite.startswith('root-'):
        subprocess.run([sys.executable,'scripts/audit_root_information.py'],check=True)
        subprocess.run([sys.executable,'scripts/audit_root_information_v2.py'],check=True)
if changed:subprocess.run([sys.executable,'scripts/build_mechanism_report.py'],check=True)
print(json.dumps({'refreshed_complete_suites':changed}))

if Path('artifacts/runs/objective-confirmation-v1/manifest.json').exists():
    subprocess.run([sys.executable,'scripts/analyze_objective_confirmation.py'],check=True)

subprocess.run([sys.executable,'scripts/build_completed_extensions.py'],check=True)
