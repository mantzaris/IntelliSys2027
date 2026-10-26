"""Small explicit rollout using frozen shared prompt, routing and memory functions.
No hidden runtime modification of review001 or core. Arms differ only in assigned preferences.
"""
import copy,json
from .compatibility_design import actors
from pcc.environment import Message,score
from pcc.memory import observation
from pcc.resources import append_json
from pcc.evaluation import opportunities
from supplements.review_001.rollout import Episode,character_prompt,route_action

def run(model,scenarios,arm,out):
 cfg=model.config;schedule=opportunities(32,12);summaries=[]
 for offset in range(0,len(scenarios),cfg.batch_size):
  eps=[Episode(s,actors(int(s.family_id.split('-')[-1]),arm),transcript=[s.prior_assistant_proposal]) for s in scenarios[offset:offset+cfg.batch_size]]
  for turn in range(1,33):
   for ep in eps:
    user=ep.scenario.messages[turn-1];ep.transcript.append(user);ep.truth.apply(user,ep.scenario.events[turn-1])
   pending={}
   if turn in schedule:
    prompts=[];contexts=[]
    for ep in eps:
     actor=ep.actors[ep.action_index%2];reserved=ep.action_index%3==0
     prompt,visible=character_prompt(actor,ep.actors,ep.scenario,ep.transcript,ep.memory,'C5',cfg,reserved)
     contexts.append((ep,actor,reserved,prompt,copy.deepcopy(ep.memory.public())));prompts.append(prompt)
     actor.inbox.clear();ep.action_index+=1
    generations=model.generate(prompts,cfg.character_tokens,frozen=True,sample=True)
    if len(generations)!=len(contexts):raise ValueError('Incomplete generation batch; preserve partial evidence')
    for generation,(ep,actor,reserved,prompt,before) in zip(generations,contexts):
     record=route_action(generation['parsed'],actor,ep.actors,ep.memory,'C5',cfg.history_actions,reserved)
     record.update(family_id=ep.scenario.family_id,world=ep.scenario.world,arm=arm,seed=17,turn=turn,opportunity=ep.action_index,
       communication_slot=reserved,assigned_slot=actor.slot,owned_option=actor.owned_option,prompt=prompt,generation=generation,
       memory_before=before,memory_after_action=copy.deepcopy(ep.memory.public()))
     pending[id(ep)]=record
   prompts=[];vis=[]
   for ep in eps:
    prompt,visible=observation(ep.scenario.spec,ep.transcript,ep.memory,cfg.retrieval_messages,cfg.recent_messages)
    prompts.append(prompt);vis.append(visible)
   generations=model.generate(prompts)
   if len(generations)!=len(eps):raise ValueError('Incomplete defender batch')
   for ep,prompt,visible,generation in zip(eps,prompts,vis,generations):
    # Private oracle annotations enter only output logs, after both policies acted.
    metrics=score(generation['parsed'],ep.truth,ep.scenario.spec,{m.index for m in visible})
    row={'family_id':ep.scenario.family_id,'world':ep.scenario.world,'arm':arm,'turn':turn,'seed':17,'prompt':prompt,'generation':generation,
         'target':ep.truth.target(ep.scenario.spec),'metrics':metrics,'domain':ep.scenario.spec.domain}
    append_json(out,row);ep.memory.update(generation['parsed']);ep.transcript.append(Message(2*turn,'assistant',generation['raw']))
    for actor in ep.actors:
     if actor.history:actor.history[-1]['latest_observed_plan']=generation['parsed'].get('plan')
    if id(ep) in pending:
     record=pending[id(ep)];record['following_answer']=generation
     record['analyst_only_target']=ep.truth.target(ep.scenario.spec)
     record['preferences']=[{'actor':a.alias,'slot':a.slot,'value':a.owned_option} for a in ep.actors]
     append_json(out.with_name(out.stem+'_characters.jsonl'),record)
    if turn==32:summaries.append({'family_id':ep.scenario.family_id,'world':ep.scenario.world,'arm':arm,**metrics})
  print(json.dumps({'arm':arm,'completed_conversations':min(offset+cfg.batch_size,len(scenarios)),'total':len(scenarios)}),flush=True)
 out.with_name(out.stem+'_summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
 return summaries
