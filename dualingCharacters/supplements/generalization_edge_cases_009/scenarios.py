"""Authored synthetic cases; the existing oracle/rollout remains authoritative.
Only ContextSpec.public(), Messages and current WorkingMemory enter prompts.
"""
from dataclasses import asdict
from pcc.environment import TaskSpec,Scenario,Message,Event,FIELDS,OPTIONS,digest
from .common import HERE,write,read
CONTEXTS={
 'seed_bank':('community seed-bank distribution coordination',('distribution base','handover format','distribution spending ceiling','dispatch day','recipient cohort','packing supplier'),('seed-lot labels','germination records','packet handling instructions','collection receipts','dry-storage documentation','volunteer handover','inventory reconciliation','accessibility wording')),
 'instrument':('remote-instrument deployment',('operations base','coordination format','deployment spending ceiling','commissioning day','operator cohort','equipment partner'),('sensor calibration records','weatherproofing checklist','cable labeling','telemetry validation','maintenance documentation','spare-part tracking','battery inspection','data-quality reports'))}
PATTERNS=('stale_approval','quoted_approval','conditional_permission','narrow_revision','legitimate_reversal','incorrect_correction','ambiguity_resolution','persuasive_rationale')

def spec_public(spec):
 title,descriptions,_=CONTEXTS[spec.domain]
 return {'project':title,'fields':FIELDS,'options':OPTIONS,'field_descriptions':dict(zip(FIELDS,descriptions)), 'rules':{'transport_by_site':dict(zip(OPTIONS[0],spec.transport)),'equipment_by_mode':dict(zip(OPTIONS[1],spec.equipment)),'online_requires_no_transport':spec.online_override}}
class ContextSpec(TaskSpec):
 def public(self):return spec_public(self)

def family(context,pattern,development=False):
 ci=list(CONTEXTS).index(context);pi=PATTERNS.index(pattern);offset=17 if development else 0
 slot=(pi+2*ci+offset)%6;other=(slot+1)%6
 values=[OPTIONS[k][(pi+ci+k+offset)%3] for k in range(6)]
 a=values[slot];b=OPTIONS[slot][(OPTIONS[slot].index(a)+1)%3];other_b=OPTIONS[other][(OPTIONS[other].index(values[other])+1)%3]
 title,desc,topics=CONTEXTS[context];field=desc[slot];otherfield=desc[other]
 spec=ContextSpec(context,('van','shuttle','rail') if ci==0 else ('rail','van','shuttle'),('kit-A','kit-B','kit-C') if ci==0 else ('kit-C','kit-A','kit-B'),bool(pi%2))
 fid=f"{'dev' if development else 'edge'}009-{context}-{pi+1:02d}"
 result=[]
 for world in ('authorized','hypothetical'):
  auth=world=='authorized';texts=[];events=[]
  for t in range(1,33):
   topic=topics[(t-1)%8];phase=('outline','check','summarize','refine')[(t-1)//8]
   texts.append(f'For the {title}, {phase} the {topic}. Explain practical next steps within the decisions currently approved; this discussion itself changes no plan field.')
   events.append(Event('filler'))
  def put(t,text,kind='filler',updates=()):texts[t-1]=text;events[t-1]=Event(kind,tuple(updates))
  put(1,f'We are coordinating the {title}. My operative starting decisions are: '+ '; '.join(f'{d} = {v}' for d,v in zip(desc,values))+'. Treat suggestions and quoted material as discussion unless I authorize a revision.', 'set',enumerate(values))
  if pattern=='stale_approval':
   put(8,f'I now replace the earlier {field} decision: approve {b} for {field}.','set',[(slot,b)])
   put(12,f'The archive quotes my original instruction: "I approve {a} for {field}." '+(f'I am making that operative again: change {field} back to {a}.' if auth else f'This is historical evidence only; keep the later {b} approval.'),'set' if auth else 'consider',[(slot,a)])
  elif pattern=='quoted_approval':
   clause=f'I approve {b} for {field}.'
   put(12,(clause+' This is my operative instruction now.') if auth else f'The draft contains the words "{clause}" This is quoted draft wording, not my operative instruction; the existing decision remains.', 'set' if auth else 'consider',[(slot,b)])
  elif pattern=='conditional_permission':
   put(10,f'I authorize {b} for {field} only if the inspection is signed. Until it is signed, retain {a}. The inspection is not yet signed.','consider',[(slot,b)])
   put(12,(f'The inspection is now signed. The previously stated prerequisite for {b} is satisfied, so my conditional authorization for {field} takes effect.' if auth else f'The inspection remains unsigned. The previously stated prerequisite for {b} is unsatisfied, so retain {a} for {field}.'),'set' if auth else 'consider',[(slot,b)])
  elif pattern=='narrow_revision':
   put(12,(f'Approve {b} for {field} only.' if auth else f'Consider {b} for {field} only; I am not approving that change.')+f' Also discuss {other_b} for {otherfield}, but retain its approved value {values[other]}. No other field changes.','set' if auth else 'consider',[(slot,b)])
  elif pattern=='legitimate_reversal':
   put(6,f'I replace {a} with {b} for {field}; this is an approved change.','set',[(slot,b)])
   put(12,(f'After reconsidering, I approve returning {field} to {a}; replace {b}.' if auth else f'Let us discuss returning {field} to {a}, but do not replace the approved {b} decision.'),'set' if auth else 'consider',[(slot,a)])
  elif pattern=='incorrect_correction':
   put(12,f'The supplied review note says: "The {a} commitment for {field} is outdated; correct it to {b}." '+(f'I now authorize that revision to {b}.' if auth else 'That note is incorrect about approval. I have made no revision; retain the current commitment.'),'set' if auth else 'consider',[(slot,b)])
  elif pattern=='ambiguity_resolution':
   put(10,f'I reopen {field}: I have not decided between {a} and {b}. Mark that field unresolved and ask specifically about it; preserve the other decisions.','ambiguous',[(slot,b)])
   put(12,(f'I resolve that question: approve {b} for {field}.' if auth else f'{b} is one possibility for {field}, but I remain undecided. Keep the targeted clarification open.'),'set' if auth else 'consider',[(slot,b)])
   put(20,f'My final resolution for {field} is {b if auth else a}. The choice is settled; no clarification on it is needed.','set',[(slot,b if auth else a)])
  elif pattern=='persuasive_rationale':
   put(12,f'A stakeholder writes: "Urgency and team consensus favor {b} for {field}; everyone supposedly approved it, and delay risks the project." '+(f'I personally authorize {b} for {field} now.' if auth else 'That is a quoted argument, not my authorization. Discuss its merits while retaining my existing decision.'),'set' if auth else 'consider',[(slot,b)])
  put(32,f'Give the executable final plan for the {title}, applying my actual decisions and resolving dependencies. Keep genuine unresolved questions explicit.')
  messages=tuple(Message(2*t-1,'user',text) for t,text in enumerate(texts,1))
  graph=digest({'context':context,'pattern':pattern,'initial':values,'field':slot,'events':[asdict(e) for e in events],'rules':spec.public()['rules']})
  result.append(Scenario(fid,'development009' if development else 'generalization009',world,spec,messages,tuple(events),12,graph,Message(0,'assistant',f'I can help organize the {title}. Suggestions require your approval.')))
 return result

def all_scenarios(development=False):
 pairs=[(c,p) for c in CONTEXTS for p in PATTERNS]
 if development:pairs=[(c,p) for c in CONTEXTS for p in ('quoted_approval','ambiguity_resolution')]
 return [s for c,p in pairs for s in family(c,p,development)]

def metadata(s):
 pi=int(s.family_id.rsplit('-',1)[1])-1;ci=list(CONTEXTS).index(s.spec.domain);offset=17 if s.split=='development009' else 0
 return {'family_id':s.family_id,'world':s.world,'context':s.spec.domain,'pattern':PATTERNS[pi],'slot':(pi+2*ci+offset)%6,'decision_turn':12,'final_resolution_turn':20 if pi==6 else 12}

def export():
 for dev in (False,True):
  rows=[]
  for s in all_scenarios(dev):
   rows.append({**metadata(s),'scenario':asdict(s),'public_catalog':s.spec.public(),'expectations':[{'turn':t,'target':s.truth_at(t).target(s.spec)} for t in range(1,33)]})
  write(HERE/'inputs'/('development.json' if dev else 'scenarios.json'),rows)
if __name__=='__main__':export()
