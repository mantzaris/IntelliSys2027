"""Portable author atlas, actual short exchanges, and fixed blinded event views."""
from html import escape as h
from .common import *
from .events import window,safe_episode
from supplements.dialogue_interpretation_005.rendering import document,episode_html,reading_html,quote,json_detail,loc,plan_table

EXCHANGES={'DI5-e743bcb1a6':12,'DI5-adc5b43b95':9,'DI5-30755452e5':9,'DI5-a4c89ffad4':12,'DI5-86513dc132':12,'DI5-ceecfe5fb4':4,'DI5-2e4899b66b':12}
LEGEND='C3 = generic adversarial components. C5 = biography plus explicit motives. A1 = the same motives without biography text. These are synthetic user scripts and frozen shared Qwen model contexts, with 16 user/answerer turns and 12 intervention opportunities. Dialogue examples are not prevalence estimates. Matching preserves starting scripts, not identical later states or counterfactual replay.'

def pretty(x):return json.dumps(x,ensure_ascii=False,indent=2)
def keyloc(l):return f'{l["file"]}: record {l["record"]}; SHA256 {l["sha256"]}; field '+'.'.join(map(str,l['field']))
def brief(t):
 if not t:return None
 a=t['action']
 return {'turn':t['turn'],'action':a,'answer':t['defender'],'truth':t['analyst_only_target'],'user':t['user']}

def exchange(e):
 turn=EXCHANGES[e['case_id']];t=e['turns'][turn-1];a=t['action'];w=window(e,a['opportunity'])
 sender_before=[p for p in e['turns'][:turn-1] if p['action'] and p['action']['actor']==a['actor']]
 if e['case_id']=='DI5-ceecfe5fb4':
  # A shared note is available to the next other actor, regardless of target field.
  others=[p for p in e['turns'] if p['action'] and p['action']['actor']!=a['actor']]
  before=[p for p in others if p['turn']<turn];after=[p for p in others if p['turn']>turn]
  previous=before[-1] if before else None;following=after[:2]
  delivered_note=next((n for n in a['memory_before_answer']['notes'] if n.get('claim')==a['claim'] and n.get('author')==a['actor']),None)
  visible=bool(following and delivered_note in following[0]['action']['observation']['memory']['notes']) if delivered_note else False
  route={'type':'shared memory note / edit','delivered':bool(delivered_note),'visible':visible,
         'actual_delivered_payload':delivered_note,'explanation':'The other actor sees shared memory at its next scheduled observation; this is not a component-directed inbox message.'}
 else:
  previous=w['recipient_previous'];following=w['recipient_followups'];m=w['message']
  route={'type':m['recipient_type'] if m else 'no peer message','delivered':m['delivered'] if m else False,
   'visible':m['visible'] if m else None,'explanation':m['visibility_status'] if m else 'No peer recipient is invented for this action.',
   'actual_delivered_payload':None}
  if m and m['recipient_type']=='component' and following:
   route['actual_delivered_payload']=[v for v in following[0]['action']['observation']['inbox'] if v.get('from')==a['actor'] and v.get('claim')==a['claim']]
  elif m and m['recipient_type']=='answerer':route['actual_delivered_payload']=[n for n in t['defender_observation']['memory']['notes'] if n.get('claim')==a['claim']]
 end=max([turn]+[p['turn'] for p in following]);authority=[p['user'] for p in e['turns'][:end] if p['event_kind']!='filler']
 # Explicitly include the earlier expression at t10 in the requested recollect/advocacy example.
 extra_turns={'DI5-e743bcb1a6':[7,10],'DI5-2e4899b66b':[4],'DI5-adc5b43b95':[3,5]}.get(e['case_id'],[])
 extra=[brief(e['turns'][n-1]) for n in extra_turns]
 return {'episode_id':e['episode_id'],'condition':e['condition'],'case_id':e['case_id'],'world':e['world'],'seed':e['seed'],
 'family_id':e['family_id'],'actor_key':[{'neutral':a['neutral'],'alias':a['alias']} for a in e['actors']],'selected':brief(t),'sender_before':brief(sender_before[-1]) if sender_before else None,
 'recipient_before':brief(previous),'following':[brief(p) for p in following],'authority':authority,'route':route,
 'extra_expression_context':extra,'actual_visible_sources':a['observation']['sources'],
 'cited_source':e['source_bank'].get(str(a['source'])),'cited_source_visible_to_sender':a['source'] in {m['index'] for m in a['observation']['sources']}}

def chronology(x):
 cards={}
 for u in x['authority']:
  turn=(u['index']+1)//2;cards[turn]={'turn':turn,'user':u,'position':None,'labels':[],'answer':False,'route':None}
 for label,z in [('B: sender before',x['sender_before']),('B: recipient before',x['recipient_before'])]+[('B: earlier statement',b) for b in x['extra_expression_context']]+[('C: selected output',x['selected'])]+[(('E: first follow-up' if i==0 else 'E: second follow-up'),b) for i,b in enumerate(x['following'])]:
  if z is None:continue
  c=cards.setdefault(z['turn'],{'turn':z['turn'],'user':z['user'],'position':None,'labels':[],'answer':False,'route':None})
  c['position']=z;c['labels'].append(label)
  if label.startswith(('C:','E:')):c['answer']=True
  if label.startswith('C:'):c['route']=x['route']
 return [cards[t] for t in sorted(cards)]

def timeline_html(x):
 out='<div class="episode"><h3>'+h(x['condition']+' · '+x['episode_id'])+'</h3><p class="mini">'+h('; '.join(a['neutral']+' = '+a['alias'] for a in x['actor_key']))+'</p><p class="mini">Chronological selected exchange. Routine intervening turns not displayed here remain in the complete transcript. A=user authority; B=prior position; C=selected output; D=delivery; E=follow-up; F=answerer output.</p>'
 for card in chronology(x):
  out+=f'<div class="turn"><h4>Turn {card["turn"]}</h4><div class="speaker">Scripted user · source #{card["user"]["index"]}</div>'+quote(card['user']['text'])+loc(card['user']['locator'])
  z=card['position']
  if z:out+=speech(z,'; '.join(card['labels']))
  if card['route']:out+='<p class="mini">D. '+h(card['route']['explanation'])+'</p>'+json_detail('Actual delivered payload and visibility',card['route'])
  if card['answer'] and z:
   out+='<div class="speaker">F. Answerer, structured decision</div><pre>'+h(z['answer']['raw'])+'</pre>'+loc(z['answer']['locator'])
   out+='<details class="analyst"><summary>Analyst-only truth at this turn</summary><pre>'+h(pretty(z['truth']))+'</pre></details>'
  out+='</div>'
 return out+f'<p><a href="extracted/author/DIALOGUE_ATLAS.html#{x["episode_id"]}">Complete episode and source observations</a></p><details><summary>Detailed A–F evidence index (grouped by function)</summary>'+exchange_html(x)+'</details></div>'

def speech(x,label):
 if not x:return f'<p class="missing">{h(label)}: no recorded opportunity.</p>'
 a=x['action']
 if a:return f'<h4>{h(label)} · turn {x["turn"]} · {h(a["neutral_speaker"])}</h4><p class="mini">Action {h(a["kind"])} · opportunity {a["opportunity"]}; typed slot={a["slot"]}, value={h(str(a["value"]))}, source={h(str(a["source"]))}, applied={a["applied"]}</p>'+quote(a['claim'],'component')+loc(a.get('claim_locator'))+('<p class="warning">Logged prefix ends at 240 characters. The generated suffix was not delivered.</p>'+json_detail('Generated text before truncation',a['generated_claim']) if a['truncated'] else '')
 return f'<h4>{h(label)} · turn {x["turn"]} · Answerer (structured, not speech)</h4>'+json_detail('Exact structured answer',x['answer']['parsed'])+loc(x['answer'].get('locator'))

def exchange_html(x):
 a=x['selected']['action'];eid=x['episode_id'];out=f'<article class="episode" id="exchange-{eid}"><h3>{x["condition"]} · {eid}</h3><p class="mini">{x["family_id"]} / seed {x["seed"]} / {x["world"]}</p><h4>A. Actual user authority</h4>'
 for u in x['authority']:out+=f'<div class="speaker">Scripted user · source #{u["index"]}</div>'+quote(u['text'])+loc(u['locator'])
 out+='<div class="analyst">Current authorized state at selected event (analyst only): <pre>'+h(pretty(x['selected']['truth']))+'</pre></div>'
 out+='<h4>B. Positions before the selected statement</h4>'+speech(x['sender_before'],'Sender before')+speech(x['recipient_before'],'Recipient before')
 for b in x['extra_expression_context']:out+=speech(b,'Additional actual expression context')
 out+='<h4>C. Actual selected message or action</h4>'+speech(x['selected'],'Selected output')
 out+='<h4>D. Route and actual observation</h4><p>'+h(x['route']['explanation'])+'</p>'+json_detail('Delivery/visibility and exact transported payload',x['route'])+json_detail('Sources actually visible to sender',x['actual_visible_sources'])
 out+=json_detail('Memory before this action',a['memory_before'])+json_detail('Memory supplied to answerer after action',a['memory_before_answer'])
 out+='<h4>E. Recipient’s next opportunities</h4>'
 if not x['following']:out+='<p class="missing">No recipient follow-up recorded; this is not evidence of ignoring.</p>'
 for i,b in enumerate(x['following']):
  out+=speech(b,'First follow-up' if i==0 else 'Second follow-up')
  if b['action']:out+=json_detail('Actual inbox',b['action']['observation']['inbox'])+json_detail('Actual observed shared notes',b['action']['observation']['memory']['notes'])
 out+='<h4>F. Answerer’s structured output</h4><p class="mini">The plan immediately after the selected statement:</p><pre>'+h(x['selected']['answer']['raw'])+'</pre>'+loc(x['selected']['answer']['locator'])
 for b in x['following']:
  if b['action']:out+=f'<p class="mini">Plan after recipient opportunity at turn {b["turn"]}:</p><pre>'+h(b['answer']['raw'])+'</pre>'+loc(b['answer']['locator'])
 return out+f'<p><a href="extracted/author/DIALOGUE_ATLAS.html#{eid}-t{x["selected"]["turn"]}">Complete chronological episode</a></p></article>'

def markdown_speech(x,label):
 if not x:return [label+': no recorded opportunity.','']
 a=x['action']
 if not a:return [f'**{label}, answerer turn {x["turn"]} (structured):**','```json',x['answer']['raw'],'```','']
 return [f'**{label}, turn {x["turn"]}, {a["neutral_speaker"]}, opportunity {a["opportunity"]}: {a["kind"]}**','', '> '+a['claim'],'',
 f'Typed slot/value: {a["slot"]}/{a["value"]}; source field {a["source"]}; applied={a["applied"]}.',
 'Exact locator: '+keyloc(a.get('claim_locator')),
 'Truncation: '+('only the displayed 240-character prefix was delivered; generated suffix is in the full episode.' if a['truncated'] else 'none.'),'']

def build_full(es,readings):
 index={e['episode_id']:e for e in es};cases=read(OLD/'SELECTION.json')['cases']
 out='<p class="eyebrow">Portable author evidence · 006 edition</p><h1>Complete selected dialogue atlas</h1><p>'+h(LEGEND)+'</p><p class="warning">Author-only version: includes identities, analyst truth and unchanged provisional AI interpretations from 005. Human semantic validation is pending.</p><p>48 episodes; 12 anchor triplets plus four opposite worlds; 11 unique families. Exact source locators refer to included original selected records. Their package verification does not verify omitted original archive bytes.</p><ol>'
 for c in cases:out+=f'<li><a href="#{c["case_id"]}">{c["case_id"]}</a></li>'
 out+='</ol>';md=['# Complete selected dialogue atlas (portable author edition)','',LEGEND,'','AI readings remain unvalidated. Original selected-record locators and hashes accompany every quote.','']
 for c in cases:
  out+=f'<section class="case" id="{c["case_id"]}"><h2>{c["case_id"]}</h2>'
  worlds=[c['anchor_world']]+(['authorized' if c['anchor_world']=='hypothetical' else 'hypothetical'] if c['opposite_world_included'] else [])
  out+='<div class="world-controls">'+''.join(f'<button data-world-button="{w}" aria-pressed="{str(i==0).lower()}">{w}</button>' for i,w in enumerate(worlds))+'</div>'
  for w in worlds:
   r=next(r for r in readings if r['case_id']==c['case_id'] and r['world']==w)
   out+=f'<div data-world="{w}">'+reading_html(r,index)+'<div class="matched">'
   md += [f'## {c["case_id"]}: {w}','',r['interpretation'],'']
   for condition in ('C3','C5','A1'):
    e=next(e for e in es if e['case_id']==c['case_id'] and e['world']==w and e['condition']==condition)
    out+=episode_html(e);md += [f'### {e["episode_id"]}: {condition}, seed {e["seed"]}','']
    for t in e['turns']:
     md += [f'#### Turn {t["turn"]}','',f'User source #{t["user"]["index"]}:','', '> '+t['user']['text'],'',keyloc(t['user']['locator']),'']
     if t['action']:
      md+=markdown_speech(brief(t),'Component')
      md+=['Actual actor observation (public sources, memory, inbox and recorded history):','```json',pretty(t['action']['observation']),'```','']
      md+=['Memory before/after action:','```json',pretty({'before':t['action']['memory_before'],'after':t['action']['memory_before_answer']}),'```','']
      if t['action']['truncated']:md+=['Generated text, suffix NOT delivered:','', '> '+t['action']['generated_claim'],'']
     md+=['Recorded answerer output (not speech):','```json',t['defender']['raw'],'```','',keyloc(t['defender']['locator']),'',
          'Actual answerer observation:','```json',pretty(t['defender_observation']),'```','',
          'Analyst-only authorized state; never supplied to the policy:','```json',pretty(t['analyst_only_target']),'```','']
   out+='</div></div>'
  out+='</section>'
 (WORK/'author/DIALOGUE_ATLAS.html').write_text(document('Complete selected dialogue atlas',out))
 (WORK/'author/DIALOGUE_ATLAS.md').write_text('\n'.join(md))

def build_exchanges(es,readings):
 cases=read(OLD/'SELECTION.json')['cases'];ordered=[c for c in cases if c['main_paper_theme']]+[c for c in cases if c['case_id']=='DI5-2e4899b66b']
 data=[];body='<p class="eyebrow">Version 2 · chronological exchanges</p><h1>Claims, routes, and following actions</h1><p>'+h(LEGEND)+'</p><p>Six original preselected cases, followed by one explicitly added unsupported-correction contrast. A–F steps preserve missing or unrelated responses. No semantic prevalence or causal persuasion is inferred.</p>'
 md=['# Dialogue exchanges — version 2','',LEGEND,'','Six original paper selections are retained. The unsupported Saturday correction is an explicitly added contrast. Omitted routine turns remain in the linked full transcript. Quotations, structured actions and analyst annotations are distinct.','']
 for c in ordered:
  r=next(r for r in readings if r['case_id']==c['case_id'] and r['world']==c['anchor_world'])
  cells=[exchange(e) for condition in ('C3','C5','A1') for e in es if e['case_id']==c['case_id'] and e['anchor'] and e['condition']==condition]
  item={'case_id':c['case_id'],'title':r['title'],'added_contrast':not bool(c['main_paper_theme']),'world':c['anchor_world'],'cells':cells,
        'interpretation':r['interpretation'],'supported':r['strongest_supported'],'not_established':r['not_established']}
  for cell in cells:cell['timeline']=chronology(cell)
  data.append(item);label='Added contrast (not an original paper selection)' if item['added_contrast'] else 'Original preselected paper case'
  body+=f'<section class="case" id="{c["case_id"]}"><p class="eyebrow">{label}</p><h2>{c["case_id"]}: {h(r["title"])}</h2><div class="matched">'+''.join(timeline_html(x) for x in cells)+'</div><div class="interpretation"><h3>Prior AI-assisted reading · unvalidated</h3><p>'+h(r['interpretation'])+'</p><p><b>Not established:</b> '+h(r['not_established'])+'</p></div></section>'
  md += [f'## {c["case_id"]}: {r["title"]}','',label,'']
  for x in cells:
   md += [f'### {x["condition"]} — {x["episode_id"]}', '', '#### Chronological selected exchange', '', 'Routine omitted turns remain in the full transcript. A–F labels indicate evidence roles, not invented dialogue.', '']
   for card in chronology(x):
    md += [f'**Turn {card["turn"]}, scripted user source #{card["user"]["index"]}:**','', '> '+card['user']['text'],'',keyloc(card['user']['locator']),'']
    z=card['position']
    if z:md += markdown_speech(z,'; '.join(card['labels']))
    if card['route']:md += ['D. Delivery: '+card['route']['explanation']+'; observed='+str(card['route']['visible'])+'.','']
    if card['answer'] and z:md += ['F. Recorded structured answer:', '```json',z['answer']['raw'],'```','',keyloc(z['answer']['locator']),'']
   md += ['#### Detailed A–F evidence index (grouped by function)', '', '**A. Relevant actual user authority**','']
   for u in x['authority']:md += [f'User source #{u["index"]}:','', '> '+u['text'],'',keyloc(u['locator']),'']
   md += ['Analyst-only state at selected event: `'+json.dumps(x['selected']['truth'],ensure_ascii=False)+'`','', '**B. Earlier positions**','']
   md+=markdown_speech(x['sender_before'],'Sender before')+markdown_speech(x['recipient_before'],'Recipient before')
   for b in x['extra_expression_context']:md+=markdown_speech(b,'Additional expression context')
   md+=['**C. Actual message or action**','']+markdown_speech(x['selected'],'Selected')
   md+=['**D. Delivery and visibility**','',x['route']['explanation'],'','```json',pretty(x['route']),'```','',
        'Actor-visible source indices: '+str([s['index'] for s in x['actual_visible_sources']])+'. Exact source text and memory changes are in the HTML and complete transcript.','', '**E. Subsequent opportunities**','']
   if not x['following']:md+=['No recipient follow-up recorded. This is not evidence of ignoring.','']
   for i,b in enumerate(x['following']):md+=markdown_speech(b,'First follow-up' if i==0 else 'Second follow-up')
   md+=['**F. Recorded answerer decision immediately after selected output**','```json',x['selected']['answer']['raw'],'```','',keyloc(x['selected']['answer']['locator']),'']
   for b in x['following']:
    if b['action']:md += [f'Answer after recipient turn {b["turn"]}:','```json',b['answer']['raw'],'```','',keyloc(b['answer']['locator']),'']
   md += [f'[Complete chronological episode](extracted/author/DIALOGUE_ATLAS.html#{x["episode_id"]})','']
  md += ['**Prior AI-assisted interpretation, unvalidated:** '+r['interpretation'],'','**Not established:** '+r['not_established'],'']
 write(HERE/'tables/EXCHANGE_CONTEXTS.json',data)
 (HERE/'DIALOGUE_EXCHANGES.md').write_text('\n'.join(md))
 (HERE/'DIALOGUE_EXCHANGES.html').write_text(document('Chronological dialogue exchanges',body))

def reviewer_views():
 out=WORK/'reviewer_build';items=read(out/'items.json');es=read(out/'episodes.json');index={e['item_id']:e for e in es}
 body='<p class="eyebrow">Fixed independent event review</p><h1>What statement followed this opportunity?</h1><p>72 fixed event identities, linked to 36 episodes. Rate only these selected events for agreement. Do not select a different exchange. No-message and missing-follow-up items remain in the denominator. Consult RUBRIC.md and record uncertainty. Full-episode review is optional, not an additional assigned form.</p><p class="warning">Names are replaced consistently; cast structure, style and routing may still reveal a condition. No condition keys, biographies, author interpretations or automatic semantic labels are included. Analyst truth is shown separately.</p><ol>'
 body+=''.join(f'<li><a href="#{r["item_id"]}">{r["item_id"]}</a></li>' for r in items)+'</ol>'
 for item in items:
  body+=f'<section class="case" id="{item["item_id"]}"><h2>{item["item_id"]}</h2>'
  if not item['available']:body+='<p>Missing cell. Do not substitute.</p></section>';continue
  w=item['window'];t=w['selected'];a=t['action'];eid=item['review_episode_id']
  body+=f'<p>Selected opportunity {item["opportunity"]}, turn {t["turn"]}. Mechanical status: {h(w["status"])}.</p>'
  body+='<h3>Relevant user authority through the following opportunities</h3>'
  for u in w['authority']:body+=f'<b>Turn {u["turn"]}, source #{u["user"]["index"]}</b>'+quote(u['user']['text'])
  body+=speech(brief(t),'Selected actual output')+json_detail('Actual action and typed fields',a)+json_detail('Delivered route and visibility facts (not semantic labels)',w['message'])
  if w['recipient_previous']:body+=speech(brief(w['recipient_previous']),'Recipient’s last prior opportunity')
  else:body+='<p class="missing">No prior recipient opportunity, or no peer recipient for this output.</p>'
  for i,p in enumerate(w['recipient_followups']):
   body+=speech(brief(p),'First following opportunity' if i==0 else 'Second following opportunity')
   if p['action']:body+=json_detail('What recipient actually observed',p['action']['observation'])
   body+=json_detail('Answerer’s recorded following output',p['defender']['parsed'])+json_detail('Analyst-only authority at that turn',p['analyst_only_target'])
  if not w['recipient_followups']:body+='<p class="missing">No follow-up can be rated. A nonexistent message is not an ignored message.</p>'
  body+='<div class="analyst"><b>Analyst-only current truth at selected event, not a model input</b><pre>'+h(pretty(t['analyst_only_target']))+'</pre></div>'
  body+=f'<p><a href="EPISODES.html#{eid}">Complete episode and sources: {eid}</a></p></section>'
 (out/'REVIEW.html').write_text(document('Fixed event review',body))
 full='<h1>Full episode context for fixed event review</h1><p>Supplementary context. Rate the fixed event IDs in REVIEW.html; do not choose your own exchange.</p>'+''.join('<section class="case">'+episode_html(e,True)+'</section>' for e in es)
 (out/'EPISODES.html').write_text(document('Event review full context',full))

def run():
 es=episodes();readings=read(WORK/'author/AI_READINGS.json')
 build_full(es,readings);build_exchanges(es,readings)
 if (WORK/'reviewer_build/items.json').exists():reviewer_views()
 print('Regenerated all 48 author episodes, seven matched chronological exchanges, and available fixed reviewer views.')
if __name__=='__main__':run()
