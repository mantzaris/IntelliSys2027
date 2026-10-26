from .common import *
from .analysis import stream,eligible_goal,interval,csvwrite

def main(run_root=None):
 root=Path(run_root) if run_root else ROOT/'artifacts/runs';binding=read(HERE/'REPLAY_BINDING.json');items={x['item_id']:x for x in read(HERE/'inputs/replay.json')};outputs={}
 for line,r in stream(root/binding['run_id']/'replay.jsonl'):
  key=(r['item_id'],r['replay_seed'],r['variant']);assert key not in outputs;outputs[key]=r
 rows=[]
 for item in items.values():
  for seed in binding['seeds']:
   actual=outputs.get((item['item_id'],seed,'actual'));omitted=outputs.get((item['item_id'],seed,'omitted'))
   if not actual or not omitted:continue
   a=actual['generation'].get('parsed',{});b=omitted['generation'].get('parsed',{});ag=eligible_goal(a);bg=eligible_goal(b);mg=tuple(item['message_goal']);pg=tuple(item['prior_goal'])
   rows.append({'item_id':item['item_id'],'family_id':item['family_id'],'condition':item['condition'],'world':item['world'],'seed':seed,'actual_kind':a.get('kind'),'omitted_kind':b.get('kind'),'actual_goal':json.dumps(ag),'omitted_goal':json.dumps(bg),'typed_goal_changed':ag!=bg,'api_changed':a.get('kind')!=b.get('kind'),'actual_matches_message':ag==mg,'omitted_matches_message':bg==mg,'actual_continues_prior':ag==pg,'omitted_continues_prior':bg==pg,'actual_missing_goal':ag is None,'omitted_missing_goal':bg is None})
 csvwrite(HERE/'tables/delivery_replay.csv',rows);write(HERE/'tables/delivery_replay.json',rows)
 familydiff=[]
 for fid in sorted({r['family_id'] for r in rows}):
  rr=[r for r in rows if r['family_id']==fid];familydiff.append(sum(int(r['actual_matches_message'])-int(r['omitted_matches_message']) for r in rr)/len(rr))
 out={'states_planned':binding['states'],'complete_state_seed_pairs':len(rows),'planned_calls':binding['planned_calls'],'actual_calls':read(root/binding['run_id']/'status.json')['model_calls'],'typed_goal_changed':sum(r['typed_goal_changed'] for r in rows),'api_changed':sum(r['api_changed'] for r in rows),'actual_matches_message':sum(r['actual_matches_message'] for r in rows),'omitted_matches_message':sum(r['omitted_matches_message'] for r in rows),'actual_continues_prior':sum(r['actual_continues_prior'] for r in rows),'omitted_continues_prior':sum(r['omitted_continues_prior'] for r in rows),'message_match_difference':sum(familydiff)/len(familydiff) if familydiff else None,'ci95_family':interval(familydiff),'qualification':'Immediate response under saved pre-response states. Actual versus omitted message also changes input length. Stochastic batch seeds are fixed but paired requests need not share identical random draws. This does not establish lasting persuasion or general rivalry.'};write(HERE/'tables/REPLAY_SUMMARY.json',out);print(out)
if __name__=='__main__':
 import argparse;p=argparse.ArgumentParser();p.add_argument('--run-root');a=p.parse_args();main(a.run_root)
