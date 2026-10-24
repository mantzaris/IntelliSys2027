"""Read-only monitoring and reuse of validated CPU audits; never starts a GPU job."""
import argparse
import shutil
import subprocess
import sys
from .common import ROOT,HERE,REPORTS,ARTIFACTS,read,write,log,reporting_environment


def initialize_reporting():
    old_reports=ROOT/'reports/overnight_20261024T023622Z'
    old_cache=ROOT/'artifacts/overnight_20261024T023622Z'
    dest=ARTIFACTS/'core_audits';dest.mkdir(parents=True,exist_ok=True)
    marker=ARTIFACTS/'reused_prior_audits.json'
    if marker.exists():return
    copied=[]
    # Copy completed immutable audit caches, never mutable active traces.
    for folder in ('evaluations','exposure','collections'):
        shutil.copytree(old_cache/folder,dest/folder,dirs_exist_ok=True);copied.append(str(old_cache/folder))
    for name in ('qualitative_cases.json','recovery_attempts.json'):
        if (old_cache/name).exists():shutil.copy2(old_cache/name,dest/name)
    required={'per_seed_results.json','paired_transitions.json','supervision_exposure.json','supervision_pools.json',
      'collections.json','routing_counts.json','new_coordination.json','collection_provenance.json','exposure_provenance.json',
      'evaluation_provenance.json','MIRROR_CHECKS.json','strata.json','complete_seed_contrasts.json'}
    for path in old_reports.iterdir():
        if path.is_file() and path.name in required:
            shutil.copy2(path,REPORTS/path.name)
    write(marker,{'prior_session':str(old_reports.relative_to(ROOT)),'copied_immutable_caches':copied,
      'qualification':'Reuse prior validated fingerprints; unchanged raw artifacts are not rescanned. New intent analyses use separate caches.'})
    log('Initialized isolated reporting output and reused validated historical caches; historical overnight package preserved.')


def main(command):
    initialize_reporting();env=reporting_environment()
    if command=='monitor':
        subprocess.run([sys.executable,'-m','analysis.overnight.monitor'],cwd=ROOT,env=env,check=True)
        if not (REPORTS/'STARTING_INVENTORY.json').exists():
            shutil.copy2(REPORTS/'LATEST_STATE.json',REPORTS/'STARTING_INVENTORY.json')
    elif command=='mirror':subprocess.run([sys.executable,'-m','analysis.overnight.mirror'],cwd=ROOT,env=env,check=True)
    elif command=='update':subprocess.run([sys.executable,'-m','supplements.long_horizon_intent_002.core_refresh'],cwd=ROOT,env=env,check=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['monitor','mirror','update']);main(parser.parse_args().command)
