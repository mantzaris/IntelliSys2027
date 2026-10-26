"""Create new006 freezes once; never amend a prior scientific manifest in place."""
from .common import *

def freeze(path,names,extra):
 obj={'frozen_utc':now(),'files':{str(p.relative_to(ROOT)):sha(p) for p in names},**extra}
 if path.exists():
  old=read(path);assert old['files']==obj['files'],'Existing freeze differs; a versioned amendment is required';return
 write(path,obj)

def run():
 science=['PROTOCOL.md','EVIDENCE_CUTOFF.json','EVENT_SELECTION.json','common.py','reader.py','events.py','ratings.py','routes.py','context_tables.py','review_package.py','presentation.py','package_inputs.py','review/PROTOCOL.md','review/RUBRIC.md','review/CALIBRATION.md','evidence/AUTHOR_MANIFEST.json','evidence/author_selected_v1.tar.gz']
 freeze(HERE/'SCIENTIFIC_MANIFEST.json',[HERE/n for n in science],{'chronology':'Post-review evidence-access/validation stage. No new human or controlled-model outcomes; prior005 selection and interpretations preserved.'})
 review=['EVENT_SELECTION.json','events.py','ratings.py','review/PROTOCOL.md','review/RUBRIC.md','review/CALIBRATION.md','review/rater_1.csv','review/rater_2.csv','evidence/REVIEWER_MANIFEST.json','evidence/reviewer_events_v1.tar.gz']
 freeze(HERE/'EVENT_REVIEW_FREEZE.json',[HERE/n for n in review],{'planned_items':72,'actual_human_ratings':0,'classification':'Fixed event stimuli, not retrospective original preregistration'})
 own=['__init__.py','common.py','compatibility_design.py','compatibility_rollout.py','compatibility_gate.py','compatibility_worker.py','compatibility_launch.py','compatibility_owner.py','compatibility/DESIGN.json','compatibility/README.md','compatibility/ADMISSION_DISABLED.json']
 deps=[ROOT/'configs/models.json']+sorted((ROOT/'src/pcc').glob('*.py'))+sorted((ROOT/'supplements/review_001').glob('*.py'))+[ROOT/'supplements/review_001/protocol.json']
 freeze(HERE/'compatibility/FREEZE.json',[HERE/n for n in own]+deps,{'budget_identity':'dialogue005-compatibility','state':'disabled and unscheduled','actual_model_calls':0,'run_id':'dialogue005-compat-17-v1','prior_design':'supplements/dialogue_interpretation_005/NEXT_EXPERIMENT.md'})
 print('New scientific, fixed-event, and compatibility manifests frozen; all old freezes unchanged.')
if __name__=='__main__':run()
