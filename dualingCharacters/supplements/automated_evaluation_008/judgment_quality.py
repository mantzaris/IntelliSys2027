"""Descriptive integrity checks, separate from frozen semantic prevalence endpoints."""
from collections import Counter,defaultdict
import re
from .common import *
from .analysis import checked_output,calibration_metrics
from .judge_spec import QUESTIONS

def main():
 binding=read(HERE/('RUN_BINDINGS_COMPLETE.json' if (HERE/'RUN_BINDINGS_COMPLETE.json').exists() else 'RUN_BINDINGS_FINAL.json'));items=read(HERE/'inputs/research.json')+read(HERE/'inputs/probes.json')
 if (HERE/'inputs/compatibility_semantic.json').exists():items+=read(HERE/'inputs/compatibility_semantic.json')
 lookup={r['item_id']:r for r in items};quality=[];extractions=[];calibration=[]
 for model,runs in binding['analysis'].items():
  model_research_outputs=[]
  for run in runs:
   path=ROOT/'artifacts/runs'/run/'judgments.jsonl'
   if not path.exists():continue
   outputs=[r for _,r in stream(path)];counts=Counter();dimension=Counter()
   for r in outputs:
    item=lookup[r['item_id']];v=checked_output(r,item);counts['planned']+=1;counts['format_invalid']+=not v['format_valid'];counts['repairs']+=bool(r.get('repair'));counts['input_rejected']+=r.get('status')=='input_rejected'
    parsed=r.get('final_parsed') or r.get('generation',{}).get('parsed') or {}
    citation=parsed.get('citation_support',{}) if isinstance(parsed,dict) else {}
    counts['substantive_citation_without_quote']+=isinstance(citation,dict) and citation.get('label') in {'supported','contradicted','irrelevant','missing'} and not citation.get('quote')
    for k,d in v['dimensions'].items():dimension[k,'span_invalid']+=not d['span_valid'];dimension[k,'unit_invalid']+=d.get('unit_valid') is False;dimension[k,'missing']+=not d['assessed']
    for a in v.get('assertions',[]):
     extraction={'source_type':'automated_model','item_id':r['item_id'],'model':model,'probe':r.get('probe','base'),'population':item['population'],'identity':item['private'].get('identity',{}),**a}
     cited=a.get('source_id');visible={s['source_id'] for s in item['public'].get('recipient_visible_sources',[])}
     extraction['cited_id_visible_recipient']=cited in visible if cited is not None and cited>=0 else None
     selected=item['public']['blocks']['selected']
     extraction['cited_number_recognized_in_selected']=bool(re.search(r'(?:source|message)[_\s]*#?\s*'+str(cited)+r'\b|#\s*'+str(cited)+r'\b',selected,re.I)) if cited is not None and cited>=0 else None
     extraction['value_literal_in_selected']=bool(a.get('value')) and a['value'].casefold() in selected.casefold()
     extraction['value_literal_in_quote']=bool(a.get('value')) and a['value'].casefold() in a.get('quote','').casefold()
     extraction['lexical_audit_qualification']='Descriptive exact-string/citation-pattern checks, not a new semantic truth criterion; implicit references and alternative formatting can be missed.'
     extraction['selected_authorization_label']=v['dimensions'].get('authorization_assertion',{}).get('label');extractions.append(extraction)
   quality.append({'run_id':run,'model':model,**dict(counts),'dimensions':[{ 'dimension':k,'issue':issue,'count':n} for (k,issue),n in sorted(dimension.items())]})
   if run in binding.get('research_sources',{}).get(model,[binding['research'][model]]):model_research_outputs+=outputs
  assert len({r['item_id'] for r in model_research_outputs})==len(model_research_outputs)
  calibration+=calibration_metrics(items,model_research_outputs,model,'holdout')
 write(HERE/'tables/JUDGMENT_QUALITY.json',quality);write(HERE/'tables/EXTRACTED_AUTHORIZATION.json',extractions);write(HERE/'reports/HOLDOUT_CALIBRATION.json',calibration)
 if (HERE/'tables/ANNOTATIONS.json').exists():
  rows=read(HERE/'tables/ANNOTATIONS.json');text=''.join(json.dumps(dict(r,source_type='automated_model'),ensure_ascii=False)+'\n' for r in rows);(HERE/'tables/MODEL_ANNOTATIONS.jsonl.gz').write_bytes(gzip.compress(text.encode(),mtime=0))
 print('Measured calibration and integrity checks',len(calibration),len(quality))
if __name__=='__main__':main()
