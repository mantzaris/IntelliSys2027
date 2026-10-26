"""Offline extraction, source verification and portable regeneration from committed inputs."""
import argparse,gzip,tarfile,io
from .common import *

def extract(which='author'):
 manifest=read(HERE/'evidence'/('AUTHOR_MANIFEST.json' if which=='author' else 'REVIEWER_MANIFEST.json'))
 source=HERE/manifest['archive'];assert sha(source)==manifest['sha256'],'Archive hash mismatch'
 destination=WORK/which;destination.mkdir(parents=True,exist_ok=True)
 with tarfile.open(source,'r:gz') as archive:
  members=archive.getmembers();assert {m.name for m in members}==set(manifest['members'])
  for m in members:
   assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
   data=archive.extractfile(m).read();assert hashlib.sha256(data).hexdigest()==manifest['members'][m.name]['sha256']
   target=destination/m.name;target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists():
    if target.read_bytes()!=data:raise FileExistsError('Preserve changed extracted file, including any ratings: '+str(target))
   else:target.write_bytes(data)
 return destination

def verify():
 from supplements.dialogue_interpretation_005.extraction import get_value,validate_pair
 from supplements.dialogue_interpretation_005.annotations import validate
 from pcc.environment import make_family
 from pcc.characters import cast,apply_action
 from pcc.memory import WorkingMemory
 from supplements.behavior_characterization_004.records import action_features,memory_before
 from supplements.behavior_characterization_004.peers import reconstruct
 import copy
 prov=read(WORK/'author/run_provenance.json');statuses=read(WORK/'author/original_status_records.json')
 for run_id,saved in statuses.items():
  assert hashlib.sha256(saved['raw_text'].encode()).hexdigest()==saved['sha256']==prov['bound_runs'][run_id]['status_sha256']
  status=json.loads(saved['raw_text']);assert status['status']=='completed' and status['model_revision']==prov['bound_runs'][run_id]['model_revision']
  assert status['config']==prov['bound_runs'][run_id]['config'] and not status.get('loaded_adapter_path')
 records={}
 with gzip.open(WORK/'author/selected_records.jsonl.gz','rt') as f:
  for line in f:
   r=json.loads(line);key=r['file'],r['record'];assert key not in records;records[key]=r
 def check(loc,text):
  r=records[loc['file'],loc['record']];assert loc['sha256']==r['file_sha256'];assert get_value(r['value'],loc)==text
 quotes=read(WORK/'author/QUOTATIONS.json')
 for q in quotes:check(q['locator'],q['text'])
 es=episodes();validate_pair(es);index={e['episode_id']:e for e in es};assert len(index)==48
 for e in es:
  scenario=next(s for s in make_family('train',int(e['family_id'].split('-')[-1]),16) if s.world==e['world'])
  actors=cast(e['condition'],e['family_id'],e['seed']);aliases=[a.alias for a in actors]
  assert [{'alias':a.alias,'neutral':f'Speaker {i+1}','role':a.role,'slot':a.slot,'owned_option':a.owned_option} for i,a in enumerate(actors)]==e['actors']
  previous=None;features=[]
  assert [t['turn'] for t in e['turns']]==list(range(1,17))
  for s in e['source_bank'].values():check(s['locator'],s['text'])
  for t in e['turns']:
   check(t['user']['locator'],t['user']['text']);check(t['defender']['locator'],t['defender']['raw'])
   loc=t['defender_observation_locator'];raw=records[loc['file'],loc['record']]['value']
   assert json.loads(get_value(raw,loc))==t['defender_observation']
   assert t['analyst_only_target']==raw['target']==scenario.truth_at(t['turn']).target(scenario.spec)
   assert t['defender']['parsed']==raw['generation']['parsed']
   assert t['memory_after_answer']==memory_before(raw)
   assert t['user']['text']==scenario.messages[t['turn']-1].text
   assert t['event_kind']==scenario.events[t['turn']-1].kind
   if t['action']:
    a=t['action'];check(a['claim_locator'],a['claim']);check(a['generated_claim_locator'],a['generated_claim'])
    assert a['claim']==a['generated_claim'][:240]
    loc=a['observation_locator'];araw=records[loc['file'],loc['record']]['value'];assert json.loads(get_value(araw,loc))==a['observation']
    for key in ['kind','slot','value','source','target','claim','applied','communication_slot']:assert a[key]==araw.get(key)
    assert a['memory_before']==a['observation']['memory']
    assert a['memory_before_answer']==t['defender_observation']['memory']
    memory=WorkingMemory(**copy.deepcopy(a['memory_before']));actor=next(actor for actor in actors if actor.alias==a['actor'])
    actor.inbox.clear()
    applied=apply_action(araw['generation']['parsed'],actor,actors,memory,e['condition'],6,a['communication_slot'])
    assert memory.public()==a['memory_before_answer'],'Transport/memory mismatch'
    assert applied['applied']==a['applied']
    features.append(action_features(araw,raw,previous,scenario,aliases,len(features)+1,aliases.index(a['actor'])))
   previous=raw
  assert json.loads(json.dumps(features))==e['features'],'Derived action features disagree with original selected records'
  messages,checks=reconstruct({'actions':features},6)
  assert json.loads(json.dumps(messages))==e['messages'] and checks==e['inbox_checks']
  assert all(c['queue_matches'] for c in e['inbox_checks'])
 validate(read(WORK/'author/AI_READINGS.json'),index)
 result={'status':'passed','episodes':len(es),'original_selected_records':len(records),'quotes_exact':len(quotes),'completed_original_status_records':len(statuses),
 'verification_scope':'Selected-package bytes and included original-record/derived-view identity; not recomputation of omitted whole original archives.'}
 write(HERE/'reports/SELECTED_EVIDENCE_VERIFICATION.json',result);print(result)

def main():
 p=argparse.ArgumentParser();p.add_argument('--reviewer-only',action='store_true');p.add_argument('--extract-only',action='store_true');args=p.parse_args()
 extract('reviewer' if args.reviewer_only else 'author')
 if args.reviewer_only:print('Open extracted/reviewer/REVIEW.html. No author keys or AI readings are in this archive.');return
 verify()
 if not args.extract_only:
  from .presentation import run
  run()
if __name__=='__main__':main()
