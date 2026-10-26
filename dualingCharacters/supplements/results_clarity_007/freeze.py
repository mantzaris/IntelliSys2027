"""Handoff binding for v2 review and this post hoc author edition, not preregistration."""
from .common import *

def verify():
 m=read(HERE/'SCIENTIFIC_MANIFEST.json')
 for name,value in m['files'].items():assert sha(HERE/name)==value,name
 for name,value in m['inputs'].items():assert sha(ROOT/name)==value,name
 return {'status':'passed','scientific_files':len(m['files']),'bound_inputs':len(m['inputs'])}

def create():
 path=HERE/'SCIENTIFIC_MANIFEST.json'
 if path.exists():print(verify());return
 names=['PROTOCOL.md','EVIDENCE_CUTOFF.json','AMENDMENTS.md','ARCHITECTURE.md','ANNOTATION_V2.md','MANUSCRIPT_REVISION.md','AUTHOR_EVENT_ANALYSIS.csv','CLAIM_TO_EVIDENCE.csv']
 names += [p.name for p in HERE.glob('*.py')]
 names += [str(p.relative_to(HERE)) for p in (HERE/'review').glob('*') if p.is_file()]
 names += [str(p.relative_to(HERE)) for p in (HERE/'tests').glob('*.py')]
 names += [str(p.relative_to(HERE)) for p in (HERE/'tables').glob('*') if p.is_file()]
 inputs={**read(HERE/'EVIDENCE_CUTOFF.json')['source_hashes'],**read(HERE/'reports/NUMERIC_VERIFICATION.json')['input_hashes']}
 for name in ['src/pcc/characters.py','src/pcc/memory.py','src/pcc/evaluation.py','supplements/evidence_validation_006/events.py','supplements/evidence_validation_006/presentation.py','supplements/behavior_characterization_004/statistics.py']:
  inputs[name]=sha(ROOT/name)
 write(path,{'version':'results_clarity007-v1 / event006-v2 / author007-v1','bound_utc':now(),'purpose':'Handoff binding, before any independent human ratings. This is a retrospective clarification after known results, not a prospective statistical preregistration. Existing72 event identities and evidence windows unchanged.','files':{n:sha(HERE/n) for n in sorted(set(names))},'inputs':inputs,'amendment_policy':'Preserve this version; record and version any later change to rubric, stimuli, ingestion or analytical interpretation. Do not infer labels from previous forms.'})
 print(verify())
if __name__=='__main__':create()
