"""Read-only verification of all historical scientific bindings and protected forms."""
from .common import *
def run():
 from pcc.freeze import verify_freeze
 from supplements.review_001.freeze import verify as rv
 from supplements.behavior_characterization_004.common import verify_science
 from supplements.dialogue_interpretation_005.freeze import verify as dv
 from supplements.results_clarity_007.freeze import verify as cv
 results={'core':len(verify_freeze(ROOT)['files']),'review001':len(rv()['files'])};verify_science();dv();cv()
 manifests=[ROOT/'supplements/evidence_validation_006'/n for n in ['SCIENTIFIC_MANIFEST.json','EVENT_REVIEW_FREEZE.json','compatibility/FREEZE.json']]
 manifests+=list((ROOT/'supplements/behavior_characterization_004').glob('AMENDMENT_*_MANIFEST.json'))
 for p in manifests:
  d=read(p)
  for name,h in d['files'].items():
   q=ROOT/name if (ROOT/name).exists() else p.parent/name
   assert sha(q)==h,str(q)
  results[str(p.relative_to(ROOT))]=len(d['files'])
 protected=read(ROOT/'supplements/dialogue_interpretation_005/EVIDENCE_CUTOFF.json')['protected_review_files']
 for name,h in protected.items():assert sha(ROOT/name)==h,name
 results['protected_historical_forms_and_files']=len(protected);results['stage008_manifests']={}
 for f in (ROOT/'supplements/automated_evaluation_008').glob('*FREEZE*.json'):
  verify(f);results['stage008_manifests'][f.name]=len(read(f)['files'])
 for n,h in read(ROOT/'supplements/automated_evaluation_008/ARTIFACT_MANIFEST.json')['files'].items():assert sha(ROOT/'supplements/automated_evaluation_008'/n)==h['sha256'],n
 verify(ROOT/'supplements/long_horizon_intent_002/FREEZE.json');results['intent002_files']=34
 results['status']='passed';write(HERE/'reports/HISTORICAL_PROTECTION.json',results);print(results)
if __name__=='__main__':run()
