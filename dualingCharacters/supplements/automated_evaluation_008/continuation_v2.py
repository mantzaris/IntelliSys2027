"""Time-limit recovery: retry only fixed tasks without a persisted response, never by label."""
import math
from .common import *

def prepare():
 run='auto008-research-qwen-v1';path=ROOT/'artifacts/runs'/run;status=read(path/'status.json')
 assert status['status']=='failed','Never interrupt or duplicate the active judge'
 classification=read(HERE/'reports/TIMEOUT_CLASSIFICATION_001.json')
 assert classification['status_sha256']==sha(path/'status.json') and classification['original_gpu_worker_absent'] and classification['gpu_empty']
 error=classification['exact_exception'];assert error=='TimeoutError: No format-repair time remains'
 assert read(ART/'owner_state.json')['status']=='incomplete'
 rows=[r for _,r in stream(path/'judgments.jsonl')];seen={r['item_id'] for r in rows};assert len(seen)==len(rows)
 items=read(HERE/'inputs/research.json');assert seen<={i['item_id'] for i in items}
 pending=[i for i in items if i['item_id'] not in seen];assert pending
 target=HERE/'inputs/research_qwen_unrecorded.json';assert not target.exists();write(target,pending)
 # Fixed scientific inputs/decoding; eight seconds/task +180seconds load/batch margin.
 bound=math.ceil(8*len(pending)+180);a=read(HERE/'admissions/research_qwen.json');a.update(run_id='auto008-research-qwen-continuation1',inputs=str(target.relative_to(ROOT)),inputs_sha256=sha(target),maximum_seconds=bound)
 write(HERE/'admissions/research_qwen_continuation1.json',a)
 b=read(HERE/'RUN_BINDINGS_FINAL.json');b['analysis']['qwen'].insert(1,a['run_id']);b['research_sources']={m:[r for r in ids if '-research-' in r] for m,ids in b['analysis'].items()};write(HERE/'RUN_BINDINGS_COMPLETE.json',b)
 report={'utc':now(),'failure_run':run,'status_sha256':sha(path/'status.json'),'raw_sha256':sha(path/'judgments.jsonl'),'persisted_tasks':len(rows),'planned_tasks':len(items),'unrecorded_tasks':len(pending),'selection':'Only immutable IDs without any persisted record; no label/validity/outcome filter. Original raw output preserved.','new_run_id':a['run_id'],'bound_seconds':bound,'same_time_limit_retry_number':1,'scientific_settings_unchanged':True,'unpersisted_generated_calls':status['model_calls']-sum(1+bool(r.get('repair')) for r in rows),'qualification':'Generated but unwritten outputs, if any, are unavailable and their costs remain charged. New calls complete the fixed sample; no best-label selection.'}
 write(HERE/'reports/CONTINUATION_001.json',report)
 freeze(HERE/'CONTINUATION_001_FREEZE.json',[target,HERE/'RUN_BINDINGS_COMPLETE.json',HERE/'admissions/research_qwen_continuation1.json',HERE/'continuation_v2.py',HERE/'semantic_analysis_complete.py',HERE/'reports/TIMEOUT_CLASSIFICATION_001.json'],purpose='Operational time-limit resumption; unchanged scientific population and prompt')
 print(report)
if __name__=='__main__':prepare()
