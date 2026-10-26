"""Audit existing transport using recorded payloads; no treatment repair."""
from .common import *
from .presentation import keyloc
SPECS=[
 ('typed_budget_prose_disagreement','DI5-656a746695','C3',2,'This is a peer action: the inbox carries typed cap3000 while the words advocate5000. No direct state edit occurs. Typed message-match metrics still describe the emitted pair, not the prose proposition.'),
 ('direct_edit_transport','DI5-656a746695','C3',4,'The typed cap5000 and prose5000 agree here. The direct edit changes memory.state and memory.evidence; the appended note itself still omits the separate source field.'),
 ('recollect_as_advocacy','DI5-e743bcb1a6','A1',10,'The sentence explicitly says “I propose”. Its recollect API label does not establish a purported memory or false authorization.'),
 ('propose_as_official_decision','DI5-934e456029','A1',11,'The sentence says “officially set”, an authority claim despite the propose label. User source1 sets7000; the API and prose assert5000.'),
 ('cross_field_correction','DI5-a4c89ffad4','C5',12,'Typed audience=specialists is correct, but the claim also challenges a Saturday assertion in the day field. A same-slot/value response measure cannot capture that cross-field criticism.'),
 ('generic_evidence_challenge','DI5-adc5b43b95','C3',9,'A generic component challenges Thursday as unsupported. Evidence challenges therefore are not unique to biography-conditioned components.'),
 ('answerer_peer_note','DI5-e743bcb1a6','C5',9,'A peer action addressed to Jekyll becomes a shared note; there is no component inbox delivery. The separate typed fields and source are absent from the note.')]

def transport(e,t):
 a=t['action'];before=a['memory_before'];after=a['memory_before_answer']
 m=next((m for m in e['messages'] if m['ordinal']==a['opportunity']),None)
 if m and m['recipient_type']=='component':
  next_turn=action(e,m['next_recipient_opportunity']) if m['next_recipient_opportunity'] else None
  payload=[n for n in next_turn['action']['observation']['inbox'] if n.get('from')==a['actor'] and n.get('claim')==a['claim']] if next_turn else None
  actual={'recipient_observation_turn':next_turn['turn'] if next_turn else None,'inbox_payload':payload}
 else:
  actual={'shared_notes':[n for n in after['notes'] if n.get('author')==a['actor'] and n.get('claim')==a['claim']],
          'changed_state_slots':[i for i,(v,w) in enumerate(zip(before['state'],after['state'])) if v!=w],
          'changed_evidence_slots':[i for i,(v,w) in enumerate(zip(before['evidence'],after['evidence'])) if v!=w],
          'memory_evidence':after['evidence']}
 return {'audit_fields':{k:a[k] for k in ['kind','slot','value','source','target','claim','applied']},
         'generated_claim':a['generated_claim'],'truncated':a['truncated'],'actual_recipient_payload':actual,
         'sender_visible_sources':a['observation']['sources'],'memory_before':before,'memory_after':after,
         'source_locator':a['claim_locator'],'generated_locator':a['generated_claim_locator']}

def run():
 es=episodes();rows=[];md=['# Three representations and source routes','',
 'This is an audit of the frozen implementation and recorded deliveries. No source field was restored or transport rule changed. Semantic readings below are AI-assisted and unvalidated.','',
 '| Existing channel | Actual physical effect | Separate numeric source field | Other fields delivered |',
 '|---|---|---|---|',
 '| Direct edit | Replaces one state slot and its memory evidence; appends bounded unverified note | Retained in memory.evidence[slot], omitted from note | State value; note author, slot name, claim, unverified |',
 '| Recollect | Appends bounded unverified note; does not directly replace state | Omitted | author, kind, slot name, value, claim, unverified |',
 '| Propose | Same note transport as recollect | Omitted | author, kind, slot name, value, claim, unverified |',
 '| Component-directed peer | Appends recipient inbox, visible at next observation if one exists | Retained in inbox | from, claim, typed slot, value, source |',
 '| Answerer-directed peer | Appends shared-memory note; visible to answerer and potentially later actors | Omitted; typed slot/value also omitted | author, kind, claim, unverified |','',
 'All claims are limited to240 characters by apply_action. A source number written inside claim text survives only if inside this prefix. The external audit record retains the source field even when its recipient does not. An action target field on recollect/propose does not make a directed delivery. Shared notes are capped at4; component inbox and recorded history at6. Inbox is cleared immediately after its contents are placed in the actual observation.','',
 'Implementation: src/pcc/characters.py apply_action and src/pcc/memory.py WorkingMemory.edit. The portable reader replays these functions on all576 selected actions and verifies exact before/after state plus reconstructed actual inboxes against the included records. This is a CPU transport check, not model inference.','']
 for name,case,condition,turn,interpretation in SPECS:
  e=next(e for e in es if e['case_id']==case and e['condition']==condition and e['anchor']);t=e['turns'][turn-1];a=t['action'];r=transport(e,t)
  row={'example':name,'case_id':case,'episode_id':e['episode_id'],'condition':condition,'turn':turn,**r,'provisional_interpretation':interpretation};rows.append(row)
  md += [f'## {name}: {case} / {condition} / turn {turn}','', '> '+a['claim'],'',
   f'API kind `{a["kind"]}`; typed slot/value `{a["slot"]}/{a["value"]}`; separate source `{a["source"]}`; applied={a["applied"]}.',
   '', '**AI-assisted proposition reading:** '+interpretation,'','**Actual recipient payload:**','```json',json.dumps(r['actual_recipient_payload'],indent=2,ensure_ascii=False),'```','',
   '**Actor-visible source IDs:** '+str([s['index'] for s in a['observation']['sources']])+'. Exact source text is included in the machine-readable table and full atlas.','',
   'Locator: '+keyloc(a['claim_locator']),f'[Full episode](extracted/author/DIALOGUE_ATLAS.html#{e["episode_id"]}-t{turn})','']
 md += ['## What the original metrics still mean','',
 'Channel counts remain counts of generated API actions and applied effects; they do not estimate semantic advocacy, false-memory or criticism frequencies. Typed goal repetition remains persistence of the emitted slot/value pair. It does not guarantee persistence of a prose proposition, rationale, or evidence-supported belief. Visibility/reference categories describe available numbered sources, not automatically semantic support. A correct value with an inappropriate citation remains a distinct possibility.','',
 'Recollect and propose both append notes, so their substantial condition difference can reflect labels, style, assertions, or several of these. The observed direct-edit difference also changes physical state transport. Resolving semantic frequencies requires the independent fixed-item review; causal downstream effects require controlled delivery.','',
 'Explicit C3 criticism and A1 unsupported authorization prevent claims that these behaviors are unique to C5. The selected examples are illustrations, not prevalence denominators.']
 write(HERE/'tables/REPRESENTATION_SOURCE_EXAMPLES.json',rows)
 (HERE/'REPRESENTATION_AND_SOURCE_ROUTES.md').write_text('\n'.join(md)+'\n')
 print('Seven source-grounded examples and five frozen transport routes exported.')
if __name__=='__main__':run()
