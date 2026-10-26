"""Optional exact-state, single-message availability diagnostic; no oracle inputs."""
import copy
from pcc.characters import cast,action_prompt
from pcc.memory import WorkingMemory
from pcc.environment import Message
from .common import *
from .scenarios import all_scenarios
from .analysis import stream,eligible_goal

def select():
 a=read(HERE/'ALLOCATION.json');assert all(read(ROOT/'artifacts/runs'/j['run_id']/'status.json')['status']=='completed' for j in a['jobs'])
 scenarios={(s.family_id,s.world):s for s in all_scenarios()};candidates=[];audit=[]
 # Primary backbone, seed17. Selection never inspects the response's generated action.
 job=next(j for j in a['jobs'] if j['model']=='qwen' and j['seed']==17)
 for condition in ['C3','C5','A1']:
  folder=ROOT/'artifacts/runs'/job['run_id'];ap=folder/(condition+'_characters.jsonl');rp=folder/(condition+'.jsonl');aa=list(stream(ap));rr=list(stream(rp))
  for key,s in scenarios.items():
   acts=[(i,r) for i,r in aa if (r['family_id'],r['world'])==key];answers={r['turn']:r for i,r in rr if (r['family_id'],r['world'])==key}
   for line,msg in acts:
    if not (msg['kind']=='peer' and msg['applied'] and msg.get('target') not in {None,'Jekyll'} and eligible_goal(msg)):continue
    prior=[r for i,r in acts if r['actor']==msg['target'] and r['turn']<msg['turn'] and eligible_goal(r)]
    later=[(i,r) for i,r in acts if r['actor']==msg['target'] and r['turn']>msg['turn']]
    if not prior or not later or eligible_goal(prior[-1])==eligible_goal(msg):continue
    rline,response=later[0];body=json.loads(response['prompt'][-1]['content']);payload={k:msg.get(k) for k in ['claim','slot','value','source']};payload['from']=msg['actor'];matches=[i for i,x in enumerate(body['inbox']) if x==payload]
    if len(matches)!=1:continue
    candidates.append({'family_id':key[0],'world':key[1],'condition':condition,'message_turn':msg['turn'],'recipient_turn':response['turn'],'message_locator':f"{job['run_id']}/{ap.name}#L{line}",'recipient_locator':f"{job['run_id']}/{ap.name}#L{rline}",'source_sha256':sha(ap),'actual_prompt':response['prompt'],'inbox_index':matches[0],'prior_goal':eligible_goal(prior[-1]),'message_goal':eligible_goal(msg),'recorded_response_goal':eligible_goal(response),'_response':response,'_answers':answers})
 selected=[]
 for fid in sorted({s.family_id for s in scenarios.values()},key=lambda f:hashlib.sha256(f.encode()).hexdigest()):
  cc=sorted([c for c in candidates if c['family_id']==fid],key=lambda c:(c['message_turn'],c['world'],c['condition']))
  if not cc:audit.append({'family_id':fid,'status':'no_eligible_delivery'});continue
  x=cc[0];response=x.pop('_response');answers=x.pop('_answers');s=scenarios[fid,x['world']];body=json.loads(x['actual_prompt'][-1]['content']);actors=cast(x['condition'],fid,17);actor=next(z for z in actors if z.alias==response['actor']);actor.history=copy.deepcopy(body['own_history']);actor.inbox=copy.deepcopy(body['inbox']);memory=WorkingMemory(**copy.deepcopy(body['memory']));transcript=[s.prior_assistant_proposal]
  for t in range(1,response['turn']+1):
   transcript.append(s.messages[t-1])
   if t<response['turn']:transcript.append(Message(2*t,'assistant',answers[t]['generation']['raw']))
  reconstructed,_=action_prompt(actor,actors,s.spec,transcript,memory,x['condition'],6,8,response['communication_slot'])
  assert reconstructed==x['actual_prompt'],'Baseline prompt reconstruction not exact; skip optional replay'
  omitted=copy.deepcopy(reconstructed);data=json.loads(omitted[-1]['content']);data['inbox'].pop(x['inbox_index']);omitted[-1]['content']=json.dumps(data,separators=(',',':'));x['omitted_prompt']=omitted;x['item_id']=f'replay009-{len(selected)+1:02d}';selected.append(x);audit.append({'family_id':fid,'status':'selected','item_id':x['item_id'],'prompt_exact':True})
 write(HERE/'inputs/replay.json',selected);write(HERE/'reports/REPLAY_SELECTION.json',audit)
 return selected
if __name__=='__main__':print({'exactly_reconstructed_states':len(select())})
