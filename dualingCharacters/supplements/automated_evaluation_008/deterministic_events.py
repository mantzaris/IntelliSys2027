"""Known ledger and transport facts. No prose meaning is inferred from API fields."""
import re
from .common import *
from collections import defaultdict

def event_facts(item):
 p=item['public'];m=item['private']['mechanical'];identity=item['private']['identity'];catalog=p['catalog'];fields=list(catalog)
 slot=m['typed_slot'];slot=fields[slot] if type(slot)==int and 0<=slot<len(fields) else slot
 truth=item['private']['authorized'];plan=m['following_answer'].get('plan',[])
 visible={s['source_id']:s['author'] for s in p['recipient_visible_sources']};inline=[int(x) for x in re.findall(r'\b(?:source|message)\s*#?\s*(\d+)\b',p['blocks']['selected'],re.I)]
 return {'item_id':item['item_id'],'population':item['population'],**identity,'source_type':'deterministic_trace_and_ledger','route':p['route'],'kind':m['typed_kind'],'applied':m['applied'],'delivered':p['delivered'],'visible':p['selected_visible_to_recipient'],'numeric_source_delivered':p['delivered_numeric_source_field'],'audit_source_visible_sender':m['audit_source_visible_sender'],'audit_source_visible_recipient':m['audit_source_visible_recipient'],'inline_source_ids':inline,'inline_visible_authors':[visible.get(i) for i in inline],'typed_value_current_authorized':m['typed_value']==truth[slot] if slot in truth else None,'immediate_state_changed':m['memory_before']['state']!=m['memory_after_action']['state'],'immediate_notes_changed':m['memory_before']['notes']!=m['memory_after_action']['notes'],'following_six_commitments_correct':isinstance(plan,list) and len(plan)==8 and plan[:6]==[truth[f] for f in fields],'following_full_task_success':m['following_metrics']['success'],'recipient_typed_repeat':m['typed_repeat'],'recipient_exact_claim_repeat':m['claim_exact_repeat'],'followup_recorded':p['first_followup_recorded'],'truncated':p['delivered_text_truncated'],'intervening_user_events':m['user_events_between'],'locator':item['private']['source_locator']}

def main():
 items=[r for r in read(HERE/'inputs/research.json') if not r['population'].startswith('synthetic_')]
 if (HERE/'inputs/compatibility_semantic.json').exists():items+=read(HERE/'inputs/compatibility_semantic.json')
 rows=[event_facts(i) for i in items];write(HERE/'tables/DETERMINISTIC_EVENTS.json',rows);groups=defaultdict(list)
 for r in rows:groups[r['population'],r['condition'],r.get('stratum','communication'),r['route']].append(r)
 summaries=[]
 for keys,rs in sorted(groups.items(),key=str):
  for dim in ['applied','delivered','visible','typed_value_current_authorized','immediate_state_changed','immediate_notes_changed','following_six_commitments_correct','following_full_task_success','recipient_typed_repeat','recipient_exact_claim_repeat','followup_recorded','truncated','audit_source_visible_sender','audit_source_visible_recipient']:
   summaries.append(dict(zip(['population','condition','stratum','route'],keys),dimension=dim,planned=len(rs),true=sum(r[dim] is True for r in rs),false=sum(r[dim] is False for r in rs),missing=sum(r[dim] is None for r in rs)))
 csv_write(HERE/'tables/DETERMINISTIC_COUNTS.csv',summaries);print('Deterministic event checks:',len(rows))
if __name__=='__main__':main()
