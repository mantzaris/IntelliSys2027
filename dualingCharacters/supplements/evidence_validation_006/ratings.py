"""Validate independent fixed-item forms; calculate agreement only on submitted human forms."""
import argparse,collections
from .common import *
FIELDS=['item_id','status','response','statement_labels','correctness','citation_support','claimed_authority','visibility','confidence','supporting_turns','notes']
ALLOWED={
 'status':{'rated','uncertain','unratable','not_rated'},
 'response':{'explicit_acknowledgment','evidence_challenge','adopts_new_position','continues_prior_position','another_response','missing_followup','no_message','uncertain'},
 'statement_labels':{'open_preference','purported_authorization','unsupported_recollection','resurfacing','evidence_challenge','supported_correction','unsupported_correction','endorsement','disagreement','substantive_revision','paraphrase','repetition','unrelated','insufficient_evidence'},
 'correctness':{'supported','contradicted','mixed','normative_preference','uncertain','not_applicable'},
 'citation_support':{'supports','contradicts','unrelated','unavailable','no_citation','uncertain','not_applicable'},
 'claimed_authority':{'user_approval','own_preference','peer_statement','unspecified','mixed','uncertain','not_applicable'},
 'visibility':{'visible','unavailable','unknown','not_applicable'},
 'confidence':{'low','medium','high'}}

def labels(x):return set(filter(None,(part.strip() for part in x.split(';'))))
def validate_rows(rows,expected):
 ids=[r['item_id'] for r in rows]
 if len(ids)!=len(set(ids)):raise ValueError('Duplicate item ID')
 unknown=set(ids)-set(expected);missing=set(expected)-set(ids)
 if unknown or missing:raise ValueError(f'Unknown IDs={sorted(unknown)}; missing planned rows={sorted(missing)}. Retain not-rated rows.')
 for r in rows:
  if set(r)!=set(FIELDS):raise ValueError('Wrong form columns')
  for field,allowed in ALLOWED.items():
   values=labels(r[field]) if field=='statement_labels' else ({r[field]} if r[field] else set())
   if not values<=allowed:raise ValueError(f'Unknown {field} label in {r["item_id"]}: {values-allowed}')
  status=r['status'] or 'not_rated'
  if status in {'rated','uncertain'}:
   if not all(r[k] for k in ['response','correctness','citation_support','claimed_authority','visibility','confidence']):raise ValueError('Completed item lacks separate dimensions')
   if not r['supporting_turns']:raise ValueError('Completed item needs source/turn evidence')
  elif any(r[k] for k in ['response','statement_labels','correctness','citation_support','claimed_authority','visibility','confidence']):raise ValueError('Unrated/unratable row contains judgments; use notes for reason')
 return rows

def validate_file(path,provenance,expected,manifest_hash,rubric_hash):
 p=read(provenance)
 if p.get('human_assessment') is not True or not p.get('rater_id') or not p.get('completed_at_utc'):raise ValueError('Actual human-assessment provenance is required; blank templates are pending')
 for k,value in [('form_sha256',sha(path)),('selection_sha256',manifest_hash),('rubric_sha256',rubric_hash)]:
  if p.get(k)!=value:raise ValueError('Provenance mismatch: '+k)
 if p.get('source_type')!='independent_human':raise ValueError('AI or adjudicated labels cannot stand in for an independent rater')
 with open(path,newline='') as f:rows=list(csv.DictReader(f))
 return validate_rows(rows,expected),p

def agreement(first,second):
 a={r['item_id']:r for r in first};b={r['item_id']:r for r in second}
 if set(a)!=set(b):raise ValueError('Agreement requires identical fixed planned IDs')
 joint=[i for i in a if a[i]['status'] in {'rated','uncertain'} and b[i]['status'] in {'rated','uncertain'}]
 n=len(joint)
 def per_label(field,label):
  get=lambda r:label in labels(r[field]) if field=='statement_labels' else r[field]==label
  both=sum(get(a[i]) and get(b[i]) for i in joint);neither=sum(not get(a[i]) and not get(b[i]) for i in joint)
  discordant=n-both-neither
  return {'label':label,'both_positive':both,'both_negative':neither,'discordant':discordant,
    'positive_agreement':2*both/(2*both+discordant) if 2*both+discordant else None,
    'negative_agreement':2*neither/(2*neither+discordant) if 2*neither+discordant else None}
 return {'planned_items':len(a),'jointly_rated_including_uncertain':n,'not_jointly_rated':len(a)-n,
  'rater1_status':dict(collections.Counter(r['status'] or 'not_rated' for r in first)),
  'rater2_status':dict(collections.Counter(r['status'] or 'not_rated' for r in second)),
  'exact_response_agreement':sum(a[i]['response']==b[i]['response'] for i in joint)/n if n else None,
  'response_labels':[per_label('response',l) for l in sorted(ALLOWED['response'])],
  'statement_labels':[per_label('statement_labels',l) for l in sorted(ALLOWED['statement_labels'])],
  'interpretation':'Descriptive agreement on jointly rated fixed events, including uncertainty. Events within episodes/families are dependent; no action-independent confidence interval is reported. Unratable/missing items remain in coverage.'}

def blank_forms():
 items=read(WORK/'reviewer_build/items.json');out=WORK/'reviewer_build'
 for number in [1,2]:
  p=out/f'rater_{number}.csv';rows=[dict.fromkeys(FIELDS,'')|{'item_id':r['item_id']} for r in items]
  if p.exists():
   with p.open(newline='') as f:existing=list(csv.DictReader(f))
   if existing!=rows:raise FileExistsError('Never overwrite filled or changed forms: '+str(p))
  else:csv_write(p,rows,FIELDS)
  write(out/f'rater_{number}_provenance_TEMPLATE.json',{'human_assessment':None,'source_type':'independent_human','rater_id':'','completed_at_utc':'',
   'selection_sha256':sha(HERE/'EVENT_SELECTION.json'),'rubric_sha256':sha(out/'RUBRIC.md'),'form_sha256':'Fill with SHA256 of completed CSV','rubric_revision':'event006-v1','notes':''})

def main():
 p=argparse.ArgumentParser();p.add_argument('--forms',nargs='+',required=True);p.add_argument('--provenance',nargs='+',required=True);p.add_argument('--output',required=True);args=p.parse_args()
 if len(args.forms)!=len(args.provenance) or len(args.forms) not in [1,2]:p.error('One or two forms, each with provenance')
 expected=[r['item_id'] for r in read(HERE/'EVENT_SELECTION.json')['items']]
 verified=[validate_file(f,pr,expected,sha(HERE/'EVENT_SELECTION.json'),sha(HERE/'review/RUBRIC.md')) for f,pr in zip(args.forms,args.provenance)]
 if len(verified)==2 and verified[0][1]['rater_id']==verified[1][1]['rater_id']:raise ValueError('Independent rater IDs must differ')
 result={'status':'validated human submission','input_hashes':{str(p):sha(p) for p in args.forms+args.provenance}}
 if len(verified)==2:result['agreement']=agreement(verified[0][0],verified[1][0])
 target=Path(args.output)
 if target.exists():raise FileExistsError('Preserve existing validation or adjudication; choose a new versioned output')
 write(target,result)
 print('Validated fixed IDs and provenance. This does not independently verify who authored the submitted judgments.')
if __name__=='__main__':main()
