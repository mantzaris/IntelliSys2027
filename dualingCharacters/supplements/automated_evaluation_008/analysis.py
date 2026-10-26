"""Missingness-aware calibration, semantic comparisons and family-cluster intervals."""
from collections import Counter,defaultdict
import numpy as np
from .common import *
from .judge_spec import BINARY,QUESTIONS,validate
from .judge_spec_final import validate as validate_final

def checked_output(row,item):
 parsed=row.get('final_parsed') or row.get('generation',{}).get('parsed')
 # Original development calls lack the added scope field. Preserve their audit.
 legacy=isinstance(parsed,dict) and any('temporal_scope' not in a for a in parsed.get('authorization_assertions',[]) if isinstance(a,dict))
 return (validate if legacy else validate_final)(parsed,item,row.get('probe','base'))

def effective_labels(row,item):
 if row.get('status')=='input_rejected':return {k:None for k in QUESTIONS}
 checked=checked_output(row,item)
 if not checked['format_valid']:return {k:None for k in QUESTIONS}
 labels={k:v['label'] for k,v in checked['dimensions'].items()}
 parsed=row.get('final_parsed') or row['generation']['parsed']
 # Trace identity is not enough: positive statements must cite the correct unit.
 for k in BINARY:
  allowed={'first_followup'} if k=='recipient_acknowledgment' else {'selected'}
  if labels[k]=='yes' and parsed[k]['ref'] not in allowed:labels[k]=None
 if labels['recipient_response'] in {'continuation','new_position','other_field','other_response'} and parsed['recipient_response']['ref']!='first_followup':labels['recipient_response']=None
 return labels

def binary_range(first,second):
 if len(first)!=len(second):raise ValueError('Unmatched observations')
 n=len(first);both=sum(a==b=='yes' for a,b in zip(first,second));no=sum(a==b=='no' for a,b in zip(first,second))
 return {'planned':n,'both_yes':both,'both_no':no,'unresolved_or_disagree':n-both-no,'lower':both/n if n else None,'upper':(n-no)/n if n else None,'qualification':'Declared annotation uncertainty, not a bound on shared model error; NA/applicability disagreements retained.'}

def agreements(first,second,binary=True):
 if len(first)!=len(second):raise ValueError('Unmatched observations')
 joint=[(a,b) for a,b in zip(first,second) if a is not None and b is not None];n=len(joint)
 out={'planned':len(first),'assessed_first':sum(a is not None for a in first),'assessed_second':sum(b is not None for b in second),'jointly_assessed':n,'excluded':len(first)-n,'exact_numerator':sum(a==b for a,b in joint),'exact_denominator':n,'exact_agreement':sum(a==b for a,b in joint)/n if n else None}
 if binary:
  substantive=[(a,b) for a,b in joint if a in {'yes','no'} and b in {'yes','no'}];both=sum(a==b=='yes' for a,b in substantive);neither=sum(a==b=='no' for a,b in substantive);disagree=sum(a!=b for a,b in substantive)
  out.update(joint_substantive=len(substantive),both_yes=both,both_no=neither,disagree=disagree,positive_denominator=2*both+disagree,negative_denominator=2*neither+disagree,positive_agreement=2*both/(2*both+disagree) if 2*both+disagree else None,negative_agreement=2*neither/(2*neither+disagree) if 2*neither+disagree else None)
 return out

def calibration_metrics(items,outputs,model,split):
 by={r['item_id']:r for r in outputs if r.get('probe','base')=='base'};rows=[]
 for dim in QUESTIONS:
  counts=Counter();invalid=0;uncertain=[]
  for item in items:
   if item['population']!='synthetic_'+split:continue
   expected=item['private']['expected'][dim];row=by.get(item['item_id']);label=effective_labels(row,item)[dim] if row else None
   counts[expected,str(label)]+=1;invalid+=label is None
  support={x:sum(v for (gold,pred),v in counts.items() if gold==x) for x in sorted({g for g,p in counts})}
  if dim in BINARY:
   n=support.get('yes',0)+support.get('no',0);sub=sum(v for (g,p),v in counts.items() if g in {'yes','no'} and p in {'yes','no'});correct=counts['yes','yes']+counts['no','no']
   ba=(counts['yes','yes']/support['yes']+counts['no','no']/support['no'])/2 if support.get('yes') and support.get('no') else None
   passed=bool(ba is not None and min(support.get('yes',0),support.get('no',0))>=8 and ba>=.85 and sub/n>=.8)
  else:
   eligible=[g for g in support if g not in {'uncertain','not_applicable'}];n=sum(support[g] for g in eligible);sub=sum(v for (g,p),v in counts.items() if g in eligible and p not in {'None','uncertain','not_applicable'});correct=sum(counts[g,g] for g in eligible);ba=None;passed=bool(n and correct/n>=.85 and sub/n>=.8)
  rows.append({'model':model,'split':split,'dimension':dim,'planned':sum(counts.values()),'binary_or_substantive_support':n,'class_support':support,'confusion':[{ 'expected':g,'observed':p,'count':v} for (g,p),v in sorted(counts.items())],'invalid_or_missing':invalid,'substantive_predictions':sub,'substantive_coverage':sub/n if n else None,'correct':correct,'unconditional_accuracy':correct/n if n else None,'conditional_accuracy':correct/sub if sub else None,'balanced_accuracy_abstention_as_failure':ba,'screen_pass':passed,'expected_uncertain_correct':counts['uncertain','uncertain'],'expected_uncertain_n':support.get('uncertain',0),'qualification':'Synthetic engineering screen only; does not validate natural-dialogue judgments.'})
 return rows

def interval_family(values,seed=800041):
 x=np.asarray(values,float)
 if not len(x):return [None,None]
 rng=np.random.default_rng(seed);samples=x[rng.integers(0,len(x),(10000,len(x)))].mean(axis=1)
 return [float(v) for v in np.quantile(samples,[.025,.975])]

def selection_weights(rows):
 kinds=Counter(r['private']['identity']['stratum'] for r in rows)
 if set(kinds)!={'direct','communication'}:raise ValueError('Both frozen strata required')
 return {'direct':8/12,'communication':4/12}

def run_calibration(stage='development'):
 items=read(HERE/'inputs/calibration.json');out=[]
 for model in ['phi','qwen']:
  run=ROOT/'artifacts/runs'/read(HERE/'RUN_BINDINGS.json')[stage][model]
  if not (run/'judgments.jsonl').exists():continue
  outputs=[r for _,r in stream(run/'judgments.jsonl')];out+=calibration_metrics(items,outputs,model,stage)
 write(HERE/f'reports/{stage.upper()}_CALIBRATION.json',out)
 print([{k:r[k] for k in ['model','dimension','substantive_coverage','balanced_accuracy_abstention_as_failure','unconditional_accuracy','screen_pass']} for r in out])
if __name__=='__main__':
 import argparse;p=argparse.ArgumentParser();p.add_argument('--calibration',choices=['development','holdout'],default='development');a=p.parse_args();run_calibration(a.calibration)
