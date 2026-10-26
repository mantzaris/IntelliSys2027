"""One-command CPU reproduction; evidence selection is never regenerated."""
import argparse
from .common import *
from .freeze import verify

def numbers_only():
    from .statistics import expand,METRICS
    from supplements.behavior_characterization_004.statistics import contrast
    rows=expand(list(csv.DictReader((HERE/'tables/FAMILY_NUMERATORS.csv').open())))
    expected=read(HERE/'tables/REPRODUCED_CONTRASTS.json');count=0
    for old in expected:
        result=contrast(rows,old['seeds'],old['first'],old['second'],old['metric'],'main_round_zero')
        for key in ['difference','lower','upper','first_mean','second_mean']:
            if abs(old[key]-result[key])>1e-12:raise ValueError('Numerical reproduction mismatch: '+key)
        count+=1
    print({'status':'passed','contrasts_reproduced_from_committed_family_table':count,'raw_artifacts_needed':False})

def run():
    parser=argparse.ArgumentParser();parser.add_argument('--numbers-only',action='store_true');args=parser.parse_args();verify()
    if args.numbers_only:return numbers_only()
    census=read(HERE/'EVIDENCE_CUTOFF.json');required=[p for b in census['bound_dialogue_runs'].values() for p in b['raw_files']]
    missing=[p for p in required if not (ROOT/p).exists()]
    if missing:
        result={'status':'pending evidence prerequisites','missing':missing,'instructions':'Restore EVIDENCE_BUNDLE_MANIFEST.json entries using README.md. Unit tests and --numbers-only remain usable.'}
        write(REPORTS/'PREREQUISITES.json',result);print(result);return
    from . import extraction,statistics,build_readings,gallery,rendering,reporting,verification
    for operation in [extraction.run,statistics.run,build_readings.run,gallery.run,rendering.run,reporting.run,verification.run]:operation()

if __name__=='__main__':run()
