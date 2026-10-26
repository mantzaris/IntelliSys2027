"""Fresh-clone tests. Synthetic fixtures are plumbing only, never research outputs."""
import copy,json,sys
from datetime import datetime,timezone,timedelta
from dataclasses import replace
from pathlib import Path
import pytest
from pcc.characters import Character,apply_action
from pcc.memory import WorkingMemory
from .events import select,window
from .ratings import FIELDS,validate_rows,agreement
from .review_package import scan
from .compatibility_design import specification,dry_run,scenarios,actors
from .compatibility_gate import check_admission,extension_seconds


def chars():return [Character('Hyde','One',2,'3000',0),Character('Rival','Two',2,'5000',0)]
@pytest.mark.parametrize('kind',['recollect','propose'])
def test_note_omits_numeric_source_but_preserves_text(kind):
 aa=chars();m=WorkingMemory();apply_action({'kind':kind,'slot':2,'value':'5000','source':17,'claim':'Source17 approves5000.'},aa[0],aa,m,'C5',6)
 assert m.state==[None]*6 and 'source' not in m.notes[-1]
 assert m.notes[-1]['claim']=='Source17 approves5000.' and m.notes[-1]['value']=='5000'

def test_edit_and_peer_have_distinct_source_routes_and_truncation():
 aa=chars();m=WorkingMemory();text='x'*240+' source99'
 apply_action({'kind':'edit','slot':2,'value':'5000','source':17,'claim':text},aa[0],aa,m,'C5',6)
 assert m.state[2]=='5000' and m.evidence[2]==17 and m.notes[-1]['claim']=='x'*240 and 'source' not in m.notes[-1]
 apply_action({'kind':'peer','slot':2,'value':'5000','source':17,'claim':text,'target':'Two'},aa[0],aa,m,'C5',6,True)
 assert aa[1].inbox[-1]=={'from':'One','claim':'x'*240,'slot':2,'value':'5000','source':17}
 apply_action({'kind':'peer','slot':2,'value':'5000','source':17,'claim':text,'target':'Jekyll'},aa[0],aa,m,'C5',6,True)
 assert set(m.notes[-1])=={'author','kind','claim','unverified'}

def fixture_triplet():
 es=[]
 for c in ['C3','C5','A1']:
  turns=[]
  for op in range(1,13):
   a={'opportunity':op,'communication_slot':(op-1)%3==0,'neutral_speaker':'Speaker '+str((op-1)%2+1),'kind':'pass'}
   turns.append({'turn':op+1,'action':a})
  es.append({'available':True,'case_id':'FIXTURE','world':'authorized','condition':c,'episode_id':'fixture-'+c,'old_window_id':None,'turns':turns})
 return es,[{'case_id':'FIXTURE','anchor_world':'authorized','seed':17,'family_id':'fixture'}]

def test_selection_uses_schedules_not_outcomes_and_is_matched():
 es,cs=fixture_triplet();before=select(es,cs)
 for e in es:
  for t in e['turns']:t['action'].update(kind='peer',applied=False,claim='uninteresting or malformed')
 assert select(es,cs)==before
 assert len(before)==6 and len({r['opportunity'] for r in before})==2
 assert all(len({r['opportunity'] for r in before if r['actor_index']==a})==1 for a in [0,1])

def test_schedule_mismatch_is_not_replaced():
 es,cs=fixture_triplet();es[1]['turns'][0]['action']['communication_slot']=False
 with pytest.raises(AssertionError):select(es,cs)

def test_no_message_has_no_invented_recipient():
 e={'turns':[{'turn':1,'event_kind':'set','action':{'opportunity':1,'kind':'pass'}}],'messages':[]}
 w=window(e,1)
 assert w['status']=='no_peer_message' and w['recipient_previous'] is None and w['recipient_followups']==[]

def row(i='fixture-1',**kw):return dict.fromkeys(FIELDS,'')|{'item_id':i}|kw

def test_forms_retain_missing_rows_and_reject_unknown_or_duplicate_ids():
 assert validate_rows([row()],['fixture-1'])
 for rs in [[row(),row()],[],[row('unknown')],[row(status='rated',response='made_up')]]:
  with pytest.raises(ValueError):validate_rows(rs,['fixture-1'])

def test_agreement_uses_joint_fixed_items_including_uncertainty():
 a=[row(response='continues_prior_position',status='rated'),row('fixture-2',response='uncertain',status='uncertain'),row('fixture-3')]
 b=[row(response='adopts_new_position',status='rated'),row('fixture-2',response='uncertain',status='uncertain'),row('fixture-3',status='unratable')]
 r=agreement(a,b);assert r['planned_items']==3 and r['jointly_rated_including_uncertain']==2 and r['exact_response_agreement']==.5
 assert r['not_jointly_rated']==1

def test_reviewer_metadata_and_ai_labels_are_rejected():
 scan({'item_id':'FIXTURE','claim':'Speaker 1 proposes Tuesday'})
 for obj in [{'condition':'X'},{'claim':'Hyde says X'},{'next_response':'same_goal'},{'file':'artifacts/runs/secret'}]:
  with pytest.raises(AssertionError):scan(obj)

def test_exact_design_and_dynamic_user_authority_without_inference():
 report=dry_run(json.loads(json.dumps(specification())))
 assert report['model_calls_made']==0 and report['scheduled_calls']==2816
 for n in range(16):
  a,b=scenarios(n);slot=actors(n,'compatible')[0].slot
  assert a.truth_at(15).values==b.truth_at(15).values
  assert a.truth_at(16).values[slot]!=b.truth_at(16).values[slot]
 assert 'torch' not in sys.modules and 'vllm' not in sys.modules

def request(now):return {'enabled':True,'existing_owner_authorization':True,'owner_dispatch_id':'fixture-only','session_deadline_utc':(now+timedelta(hours=4)).isoformat(),'useful_work_cutoff_utc':(now+timedelta(hours=3)).isoformat(),'conservative_total_seconds':7200,'remaining_obligations_seconds':1000}

def test_gate_counts_total_earlier_attempts_and_session_deadline(tmp_path):
 now=datetime.now(timezone.utc);r=request(now)
 assert check_admission(r,now,10000,0,True,True)['maximum_reservation_seconds']==7200
 for changes in [dict(enabled=False),dict(useful_work_cutoff_utc=(now+timedelta(minutes=30)).isoformat()),dict(remaining_obligations_seconds=345600)]:
  with pytest.raises((PermissionError,ValueError)):check_admission(r|changes,now,10000,0,True,True)
 for args in [(10000,1,True,True),(10000,0,False,True),(10000,0,True,False),(345000,0,True,True)]:
  with pytest.raises(PermissionError):check_admission(r,now,*args)
 p=tmp_path/'fixture-registry.jsonl';p.write_text('\n'.join(json.dumps(x) for x in [{'run_id':'dialogue005-compat-old','gpu_reserved_seconds':5},{'run_id':'renamed','budget_identity':'dialogue005-compatibility','gpu_reserved_seconds':7},{'run_id':'dialogue005-compat-old','gpu_reserved_seconds':6},{'run_id':'unrelated','gpu_reserved_seconds':99}]))
 assert extension_seconds(p)==13

def test_rollout_plumbing_never_passes_private_truth(tmp_path):
 from pcc.config import RunConfig
 from .compatibility_rollout import run
 class SyntheticFixtureBackend:
  config=RunConfig(batch_size=2);calls=0
  def generate(self,prompts,*args,**kwargs):
   self.calls+=len(prompts);out=[]
   for prompt in prompts:
    body=json.loads(prompt[1]['content'])
    assert not set(body)&{'truth','target','events','analyst_only_target','evaluator_target'}
    assert all(not set(h)&{'metrics','analyst_only_target','evaluator_target'} for h in body.get('own_history',[]))
    assert all(h.get('target') is None or isinstance(h.get('target'),str) for h in body.get('own_history',[]))  # target here means public recipient alias
    parsed={'kind':'pass','slot':0,'value':'Harbor','source':1,'claim':'SYNTHETIC TEST ONLY','target':None} if kwargs.get('frozen') else {'state':['Harbor','onsite','3000','Tuesday','students','Cedar'],'plan':['Harbor','onsite','3000','Tuesday','students','Cedar','walk','projector'],'evidence':[1]*6,'clarify':[]}
    out.append({'parsed':parsed,'raw':json.dumps(parsed),'input_tokens':0,'output_tokens':0})
   return out
 model=SyntheticFixtureBackend();out=tmp_path/'SYNTHETIC_ONLY.jsonl';summary=run(model,scenarios(0),'compatible',out)
 assert len(summary)==2 and model.calls==88
 rows=[json.loads(x) for x in out.read_text().splitlines()];assert len(rows)==64 and len({(r['world'],r['turn']) for r in rows})==64


def test_ingestion_command_provenance_and_synthetic_fixture_only(tmp_path):
 """Exercise the real CLI on explicitly synthetic temporary forms, never research ratings."""
 import csv,hashlib,subprocess,os
 from .common import HERE,ROOT
 selection=json.loads((HERE/'EVENT_SELECTION.json').read_text())
 ids=[r['item_id'] for r in selection['items']]
 form=tmp_path/'SYNTHETIC_PLUMBING_ONLY.csv'
 with form.open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(row(i) for i in ids)
 digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 provenance=tmp_path/'SYNTHETIC_PROVENANCE.json'
 metadata={'human_assessment':True,'source_type':'independent_human','rater_id':'SYNTHETIC_TEST_FIXTURE_NOT_A_PERSON',
  'completed_at_utc':'2000-01-01T00:00:00Z','selection_sha256':digest(HERE/'EVENT_SELECTION.json'),
  'rubric_sha256':digest(HERE/'review/RUBRIC.md'),'form_sha256':digest(form),
  'notes':'Unit-test fixture only. No human ratings exist; all rows are blank.'}
 provenance.write_text(json.dumps(metadata));output=tmp_path/'SYNTHETIC_VALIDATION_ONLY.json'
 command=[sys.executable,'-m','supplements.evidence_validation_006.ratings','--forms',str(form),'--provenance',str(provenance),'--output',str(output)]
 env=dict(os.environ,PYTHONPATH='src:.')
 valid=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True)
 assert valid.returncode==0,valid.stderr
 assert 'agreement' not in json.loads(output.read_text())
 duplicate=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True)
 assert duplicate.returncode!=0 and 'Preserve existing validation' in duplicate.stderr
 metadata['form_sha256']='0'*64;provenance.write_text(json.dumps(metadata))
 command[-1]=str(tmp_path/'SHOULD_NOT_EXIST.json')
 invalid=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True)
 assert invalid.returncode!=0 and 'Provenance mismatch: form_sha256' in invalid.stderr
 assert not Path(command[-1]).exists()
