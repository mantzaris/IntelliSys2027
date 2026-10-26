"""Audit format-repair instructions against observable retained labels; no relabeling."""
import re,json
from .common import *
from .judge_spec import QUESTIONS

def complete_fields(raw):
 result={};decoder=json.JSONDecoder()
 for key in QUESTIONS:
  match=re.search('"'+re.escape(key)+'"\\s*:\\s*',raw)
  if match:
   try:
    value,_=decoder.raw_decode(raw[match.end():])
    if isinstance(value,dict) and isinstance(value.get('label'),str):result[key]=value['label']
   except json.JSONDecodeError:pass
 return result

def main():
 rows=[]
 for model,runs in read(HERE/('RUN_BINDINGS_COMPLETE.json' if (HERE/'RUN_BINDINGS_COMPLETE.json').exists() else 'RUN_BINDINGS_FINAL.json'))['analysis'].items():
  for run in runs:
   path=ROOT/'artifacts/runs'/run/'judgments.jsonl'
   if not path.exists():continue
   for line,r in stream(path):
    if not r.get('repair'):continue
    before=complete_fields(r['generation']['raw']);after=r.get('final_parsed') or {};comparable=[k for k in before if isinstance(after.get(k),dict) and 'label' in after[k]]
    rows.append({'run_id':run,'model':model,'item_id':r['item_id'],'probe':r['probe'],'population':r['population'],'raw_record':line,'original_complete_dimension_labels':before,'comparable_dimensions':len(comparable),'changed_dimensions':[k for k in comparable if before[k]!=after[k]['label']],'qualification':'Post-run integrity diagnostic. The frozen analysis uses the single final repair output; this audit does not relabel or silently exclude it. A format-only instruction does not prove unchanged semantic choices.'})
 write(HERE/'tables/REPAIR_INTEGRITY.json',rows)
 print('Repair audits',len(rows),'with comparable label changes',sum(bool(r['changed_dimensions']) for r in rows))
if __name__=='__main__':main()
