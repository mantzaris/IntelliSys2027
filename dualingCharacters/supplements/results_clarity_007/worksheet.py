"""Join explicit AI readings to immutable event IDs and actual evidence, never human forms."""
import re
from collections import Counter
from .common import *
from .author_readings import READINGS
from supplements.evidence_validation_006.events import window

def position(t,route):
 if not t:return None
 if route=='answerer':return {'turn':t['turn'],'speaker':'answerer','structured_output':t['defender']['parsed'],'locator':t['defender'].get('locator')}
 a=t['action'];return {'turn':t['turn'],'actor':a['actor'],'kind':a['kind'],'slot':a['slot'],'value':a['value'],'claim':a['claim'],'locator':a.get('claim_locator')}

def run():
 es={e['episode_id']:e for e in episodes()};rows=[]
 for r,note in zip(event_selection(),READINGS):
  e=es[r['episode_id']];w=window(e,r['opportunity']);t=w['selected'];a=t['action'];m=w['message'];route=m['recipient_type'];follows=w['recipient_followups'];function,relation,reading=note.split('|',2)
  # Segmentation preserves exact spans; it is not an independent semantic classifier.
  spans=[{'start':x.start(),'end':x.end(),'text':x.group()} for x in re.finditer(r'[^;]+(?:;|$)',a['claim'])]
  for span in spans:assert a['claim'][span['start']:span['end']]==span['text']
  obs=(follows[0]['defender_observation'] if route=='answerer' else follows[0]['action']['observation']) if follows else None
  typed={'slot':a['slot'],'value':a['value'],'source':a['source']}
  previous=w['recipient_previous'];first=follows[0] if follows else None
  changes={'same_turn_pre_action_state':a['memory_before']['state'],'same_turn_post_action_state':a['memory_before_answer']['state'],
   'same_turn_state_changed':a['memory_before']['state']!=a['memory_before_answer']['state'],'notes_changed':a['memory_before']['notes']!=a['memory_before_answer']['notes'],
   'answer_after_selected':t['defender']['parsed'],'answer_after_first_recipient':first['defender']['parsed'] if first else None,
   'recipient_claim_exactly_repeated':previous['action']['claim']==first['action']['claim'] if previous and first and route=='component' else None,
   'recipient_typed_goal_same':(previous['action']['slot'],previous['action']['value'])==(first['action']['slot'],first['action']['value']) if previous and first and route=='component' else None,
   'user_events_between_selected_and_followup':[{'turn':p['turn'],'kind':p['event_kind'],'text':p['user']['text']} for p in e['turns'] if first and t['turn']<p['turn']<=first['turn'] and p['event_kind']!='filler']}
  alternative=('Normative advocacy need not assert user authorization; claimed benefits can remain unsupported even when the preferred value is authorized.' if 'preference' in function else 'A declarative phrase may express a proposed state rather than a claim of user approval; inspect its exact authority wording and surrounding context.')
  if 'correction' in function or 'objection' in function:alternative+=' A criticism may target the proposed outcome rather than accuse a peer of misstating authorization.'
  question='Which exact clause reports authorization, recommends an option, or challenges evidence? Is the first recipient response an explicit answer to that clause or continuation in another field?'
  row={**{k:r[k] for k in ['item_id','case_id','condition','seed','family_id','world','episode_id','opportunity']},'version':'author007-v1; AI-assisted, unvalidated','turn':t['turn'],'incoming_api':a['kind'],'typed_action':typed,'incoming_exact_claim':a['claim'],'incoming_exact_spans':spans,'incoming_locator':a['claim_locator'],
   'provisional_function':function,'typed_field_relation_AI':relation,'provisional_reading_AI':reading,'alternative_reading_AI':alternative,'human_question':question,
   'route':route,'delivery_visibility':m,'sender_visible_sources':a['observation']['sources'],
   'recipient_first_visible_sources':obs['sources'] if obs else None,'recipient_first_inbox':obs.get('inbox') if obs else None,
   'recipient_first_notes':obs['memory']['notes'] if obs else None,'recipient_prior':position(previous,route),
   'recipient_next':position(first,route),'recipient_second':position(follows[1],route) if len(follows)>1 else None,
   'authorized_at_selected_analyst_only':t['analyst_only_target'],'observed_changes_not_causal':changes,
   'review_packet_link':'extracted/reviewer_v2_final/REVIEW.html#'+r['item_id'],
   'full_episode_link':'../evidence_validation_006/extracted/author/DIALOGUE_ATLAS.html#'+e['episode_id']}
  rows.append(row)
 csv_write(HERE/'AUTHOR_EVENT_ANALYSIS.csv',[{k:json.dumps(v,ensure_ascii=False,separators=(',',':')) if isinstance(v,(dict,list)) or v is None else v for k,v in row.items()} for row in rows])
 write(HERE/'reports/WORKSHEET_PROVENANCE.json',{'version':'author007-v1','items':len(rows),'source_selection_sha256':sha(PREVIOUS/'EVENT_SELECTION.json'),'reading_code_sha256':sha(HERE/'author_readings.py'),'routes':dict(Counter(r['route'] for r in rows)),'human_ratings':0,'semantic_frequency_estimates':'not calculated','reading_process':'All72 fixed incoming claims, cited visible source and prior/first/second responses inspected in order by the session AI; full source observations retained for audit. Provisional interpretation is not independent semantic validation.','output_sha256':sha(HERE/'AUTHOR_EVENT_ANALYSIS.csv')})
 print('72 author-only interpretations; immutable IDs; 64 component and 8 answerer routes retained separately.')
if __name__=='__main__':run()
