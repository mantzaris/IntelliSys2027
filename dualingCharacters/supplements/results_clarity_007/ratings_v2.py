"""event006-v2: independent dimension coverage; missing is never a negative label."""
import argparse,collections
from datetime import datetime,timedelta
from .common import *
from supplements.evidence_validation_006.ratings import ALLOWED as V1_LABELS
VERSION='event006-v2'
DIMENSIONS={
 'response':('response',V1_LABELS['response']),
 'statement':('statement_labels',V1_LABELS['statement_labels']),
 'correctness':('correctness',V1_LABELS['correctness']),
 'citation':('citation_support',V1_LABELS['citation_support']),
 'authority':('claimed_authority',V1_LABELS['claimed_authority']),
 'visibility':('visibility',V1_LABELS['visibility'])}
STATUS={'not_assessed','assessed','unratable'}
FIELDS=['item_id']+[f for dim,(value,_) in DIMENSIONS.items() for f in (dim+'_annotation_status',value,dim+'_unratable_reason')]+['confidence','supporting_turns','secondary_response_notes','notes']

def status(row,dim):return row[dim+'_annotation_status'] or 'not_assessed'
def label_set(text):return set(text.split(';')) if text else set()
def schema():
 return {'version':VERSION,'columns':FIELDS,'dimensions':{d:{'value_field':v,'status_field':d+'_annotation_status','reason_field':d+'_unratable_reason','allowed_values':sorted(a),'multilabel':d=='statement'} for d,(v,a) in DIMENSIONS.items()},'assessment_statuses':sorted(STATUS),'blank_status':'not_assessed','assessed_empty_statement':'Explicitly reviewed entire label set; no label applies. Not equivalent to blank/unassessed.','secondary_response':'Free-text secondary_response_notes only. Never incoming statement_labels.','selection_sha256':sha(PREVIOUS/'EVENT_SELECTION.json'),'fixed_items_sha256':read(PREVIOUS/'evidence/REVIEWER_MANIFEST.json')['members']['items.json']['sha256']}

def validate_rows(rows,expected):
 ids=[r.get('item_id') for r in rows]
 if len(ids)!=len(set(ids)):raise ValueError('Duplicate item ID')
 if set(ids)!=set(expected):raise ValueError(f'Unknown IDs={sorted(set(ids)-set(expected))}; missing planned IDs={sorted(set(expected)-set(ids))}. Preserve every planned row.')
 for r in rows:
  if set(r)!=set(FIELDS) or any(not isinstance(v,str) for v in r.values()):raise ValueError('Wrong schema or invalid CSV cells; use event006-v2 blank form')
  for dim,(field,allowed) in DIMENSIONS.items():
   state=status(r,dim);text=r[field];reason=r[dim+'_unratable_reason']
   if state not in STATUS:raise ValueError(f'Unknown assessment status: {dim}')
   if text!=text.strip() or (dim=='statement' and (any(s!=s.strip() or not s for s in text.split(';')) if text else False)):
    raise ValueError('Trim label whitespace and do not use empty semicolon segments')
   values=label_set(text) if dim=='statement' else ({text} if text else set())
   if not values<=allowed:raise ValueError(f'Unknown {field} label: {values-allowed}. Secondary response readings belong in secondary_response_notes.')
   if dim=='statement' and text and len(text.split(';'))!=len(values):raise ValueError('Duplicate statement label')
   if state=='assessed':
    if dim!='statement' and not text:raise ValueError(f'Assessed {dim} needs a value; uncertainty is an assessed category')
    if reason:raise ValueError('Assessed dimension cannot contain an unratable reason')
   elif state=='unratable':
    if text or not reason.strip():raise ValueError('Unratable dimension needs its own reason and no labels')
   elif text or reason:raise ValueError('Unassessed dimension must contain neither labels nor an unratable reason')
  assessed=any(status(r,d)=='assessed' for d in DIMENSIONS)
  if assessed and not r['supporting_turns'].strip():raise ValueError('Assessed item needs supporting turns/source spans')
  if r['confidence'] and r['confidence'] not in {'low','medium','high'}:raise ValueError('Unknown confidence')
  if not assessed and r['confidence']:raise ValueError('No confidence rating without any assessed dimension')
 return rows

def coverage(rows,dim):
 counts=collections.Counter(status(r,dim) for r in rows)
 return {'planned':len(rows),'unratable_reasons':{r['item_id']:r[dim+'_unratable_reason'] for r in rows if status(r,dim)=='unratable'},**{s:counts[s] for s in sorted(STATUS)},
         'uncertain_value':sum(status(r,dim)=='assessed' and (bool(label_set(r[DIMENSIONS[dim][0]]) & {'insufficient_evidence'}) if dim=='statement' else r[DIMENSIONS[dim][0]] in {'uncertain','unknown'}) for r in rows),
         'assessed_empty_set':sum(status(r,dim)=='assessed' and not r[DIMENSIONS[dim][0]] for r in rows) if dim=='statement' else None}

def dimension_agreement(first,second,dim):
 a={r['item_id']:r for r in first};b={r['item_id']:r for r in second}
 if set(a)!=set(b):raise ValueError('Fixed planned item identities must match')
 joint=[i for i in a if status(a[i],dim)==status(b[i],dim)=='assessed'];n=len(joint)
 field,allowed=DIMENSIONS[dim];multi=dim=='statement'
 result={'dimension':dim,'planned_items':len(a),'rater1':coverage(first,dim),'rater2':coverage(second,dim),
  'jointly_assessed':n,'excluded_from_agreement':len(a)-n,'joint_item_ids':joint,
  'exclusion_status_pairs':dict(collections.Counter(status(a[i],dim)+' / '+status(b[i],dim) for i in a if i not in joint)),
  'exact_agreement_numerator':None,'exact_agreement_denominator':n,'exact_agreement':None,'labels':[]}
 get=lambda r:label_set(r[field]) if multi else r[field]
 if n:
  equal=sum(get(a[i])==get(b[i]) for i in joint)
  result.update(exact_agreement_numerator=equal,exact_agreement=equal/n)
 for label in sorted(allowed):
  positive=lambda r:label in label_set(r[field]) if multi else r[field]==label
  both=sum(positive(a[i]) and positive(b[i]) for i in joint);neither=sum(not positive(a[i]) and not positive(b[i]) for i in joint)
  only1=sum(positive(a[i]) and not positive(b[i]) for i in joint);only2=sum(not positive(a[i]) and positive(b[i]) for i in joint)
  posden=2*both+only1+only2;negden=2*neither+only1+only2
  result['labels'].append({'label':label,'both_positive':both,'both_negative':neither,'rater1_only':only1,'rater2_only':only2,
   'positive_agreement_numerator':2*both,'positive_agreement_denominator':posden,'positive_agreement':2*both/posden if posden else None,
   'negative_agreement_numerator':2*neither,'negative_agreement_denominator':negden,'negative_agreement':2*neither/negden if negden else None})
 return result

def agreement(first,second,routes=None):
 expected=[r['item_id'] for r in first];validate_rows(first,expected);validate_rows(second,expected)
 result={'version':VERSION,'planned_items':len(expected),'dimensions':{d:dimension_agreement(first,second,d) for d in DIMENSIONS},
  'qualification':'Agreement describes independent assessment of fixed units, not peer influence. Unassessed is missing; unratable reasons retained in input forms. Each dimension has its own joint denominator. Unselected labels count absent only after explicit complete-set assessment. Uncertainty remains an assessed category; zero denominators are null. No action-iid confidence interval.'}
 if routes:
  assert set(expected)<=set(routes)
  result['by_recipient_route']={route:{d:dimension_agreement([r for r in first if routes[r['item_id']]==route],[r for r in second if routes[r['item_id']]==route],d) for d in DIMENSIONS} for route in sorted({routes[i] for i in expected})}
 return result

def provenance_expected():
 return {'annotation_version':VERSION,'selection_sha256':sha(PREVIOUS/'EVENT_SELECTION.json'),
  'stimulus_items_sha256':read(PREVIOUS/'evidence/REVIEWER_MANIFEST.json')['members']['items.json']['sha256'],
  'schema_sha256':sha(HERE/'review/SCHEMA.json'),'rubric_sha256':sha(HERE/'review/RUBRIC.md'),'ingestion_code_sha256':sha(HERE/'ratings_v2.py')}

def validate_file(form,provenance):
 p=read(provenance)
 if p.get('human_assessment') is not True or p.get('source_type')!='independent_human' or not p.get('rater_id','').strip():raise ValueError('Real independent-human provenance required. Blank templates remain pending.')
 try:t=datetime.fromisoformat(p['completed_at_utc'].replace('Z','+00:00'))
 except (KeyError,ValueError,AttributeError) as e:raise ValueError('Valid UTC completion timestamp required') from e
 if t.utcoffset()!=timedelta(0):raise ValueError('Completion time must be UTC')
 for key,value in provenance_expected().items():
  if p.get(key)!=value:raise ValueError('Provenance mismatch: '+key)
 if p.get('form_sha256')!=sha(form):raise ValueError('Provenance mismatch: form_sha256')
 return validate_rows(csv_read(form),[r['item_id'] for r in event_selection()]),p

def prepare_forms():
 rows=[dict.fromkeys(FIELDS,'')|{'item_id':r['item_id']} for r in source_json('items.json','reviewer')]
 for n in [1,2]:
  path=HERE/f'review/rater_{n}_event006_v2.csv'
  if path.exists():assert csv_read(path)==rows,'Never overwrite filled or changed forms'
  else:csv_write(path,rows,FIELDS)
  p=HERE/f'review/rater_{n}_provenance_TEMPLATE.json'
  template={**provenance_expected(),'human_assessment':None,'source_type':'independent_human','rater_id':'','completed_at_utc':'','form_sha256':'','notes':''}
  if p.exists():assert read(p)==template,'Preserve changed provenance template'
  else:write(p,template)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--forms',nargs='+',required=True);parser.add_argument('--provenance',nargs='+');parser.add_argument('--output');parser.add_argument('--check-blank',action='store_true');args=parser.parse_args()
 ids=[r['item_id'] for r in event_selection()]
 if args.check_blank:
  for path in args.forms:
   rows=validate_rows(csv_read(path),ids);assert all(not v for r in rows for k,v in r.items() if k!='item_id'),'Not a blank template'
  print('Blank fixed templates verified. No agreement calculated; no human ratings.');return
 if not args.output or not args.provenance or len(args.forms)!=len(args.provenance) or len(args.forms) not in {1,2}:parser.error('One or two forms, matching independent provenance files, and new --output required')
 target=Path(args.output)
 if target.exists():raise FileExistsError('Preserve earlier submissions/adjudication: choose a new output')
 pairs=[validate_file(f,p) for f,p in zip(args.forms,args.provenance)]
 if len(pairs)==2 and pairs[0][1]['rater_id']==pairs[1][1]['rater_id']:raise ValueError('Independent rater identities must differ')
 has_assessment=any(status(r,d)=='assessed' for rows,_ in pairs for r in rows for d in DIMENSIONS)
 result={'status':'validated submission' if has_assessment else 'pending: no assessed judgments','version':VERSION,'input_hashes':{str(p):sha(p) for p in args.forms+args.provenance},'coverage':[ {d:coverage(rows,d) for d in DIMENSIONS} for rows,_ in pairs]}
 if len(pairs)==2 and has_assessment:
  routes={r['item_id']:(r['window']['message'] or {}).get('recipient_type','no_message') for r in source_json('items.json','reviewer')}
  result['agreement']=agreement(pairs[0][0],pairs[1][0],routes)
 write(target,result);print('Validated dimension missingness, fixed units and provenance; human authorship still requires actual provenance review.')
if __name__=='__main__':main()
