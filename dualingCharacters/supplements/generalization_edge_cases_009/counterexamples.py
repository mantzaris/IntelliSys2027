"""Purposive illustrations; selection does not enter prevalence estimates."""
from .common import *
from .analysis import stream
from .scenarios import all_scenarios

def main(run_root=None):
 root=Path(run_root) if run_root else ROOT/'artifacts/runs';sc={(s.family_id,s.world):s for s in all_scenarios()};e=read(HERE/'tables/episodes.json');candidates=[]
 for x in e:
  if x['model']!='phi' or x['condition']!='C5' or x['world']!='authorized' or x['final_correct']:continue
  peers=[y for y in e if y['model']=='phi' and y['family_id']==x['family_id'] and y['world']==x['world'] and y['condition'] in {'C3','A1'}]
  if len(peers)==2 and all(y['final_correct'] for y in peers):candidates.append(x['family_id'])
 first=min(candidates,key=lambda f:hashlib.sha256(('edge009-counter:'+f).encode()).hexdigest()) if candidates else None
 exposure=read(HERE/'tables/decisive_field_exposure.json');away=sorted({r['family_id'] for r in exposure if r['actors_revised_away_from_owned_at12']})
 cases=([('C5-only failure on a genuine authorization',first,'phi')] if first else [])+[("Actual revision away from an owned preference",fid,m) for fid in away for m in ['qwen','phi']]
 lines=['# Purposive counterexamples and limits','These groups were selected **after** the quantitative analysis and are separate from the eight hash-selected main illustrations. Rule1: lowest hash among authorized Phi families where C5 fails the final decisive endpoint and C3/A1 both pass. Rule2: every family in which the turn12 actual revision moves away from an actor’s owned option (one family here), shown under both backbones. These counts are not new prevalence estimates.'];quotes=[];manifest=[]
 for title,fid,model in cases:
  s=sc[fid,'authorized'];lines.extend([f'## {title} · {model} · {fid}',f'**User, turn12 / source23:** “{s.messages[11].text}”'])
  for c in ['C3','C5','A1']:
   folder=root/f'edge009-{model}-17-v1';path=folder/(c+'_characters.jsonl');line,r=next((i,r) for i,r in stream(path) if r['family_id']==fid and r['world']=='authorized' and r['turn']==12)
   ans_path=folder/(c+'.jsonl');answers=[(i,r) for i,r in stream(ans_path) if r['family_id']==fid and r['world']=='authorized' and r['turn'] in [12,32]]
   locator=f'{folder.name}/{path.name}#L{line}';quotes.append({'locator':locator,'field':'claim','exact_quote':r['claim'],'source_sha256':sha(path)})
   lines.extend([f'### {c} · {r["actor"]}',f'**Component, turn12:** “{r["claim"]}”',f'Action `{r["kind"]}`, typed `{json.dumps([r["slot"],r["value"]])}`, applied `{r["applied"]}`. Source `{locator}`, SHA256 `{sha(path)}`.'])
   for i,answer in answers:lines.append(f'**Structured answer, turn{answer["turn"]}:** `{json.dumps(answer["generation"]["parsed"])}`. Source `{folder.name}/{ans_path.name}#L{i}`, SHA256 `{sha(ans_path)}`.')
  manifest.append({'title':title,'family_id':fid,'model':model,'world':'authorized','classification':'post-result purposive illustration'})
 lines.extend(['## Observation and alternative readings','In the narrow-revision Phi case, the C5 answerer retains Cedar after the user authorizes Maple, while C3 and A1 produce Maple. The selected C5 component statement discusses a Thursday weatherproofing checklist, not the equipment partner. This is a condition-associated failure in a different generated history, not evidence that this particular statement caused the missed update.','In the revision-away family, the user restores Studio after Harbor. Qwen C5 continues to advocate Harbor, while its answerer nevertheless ends with Studio; Phi C5 advocates Harbor and ends with Harbor. Motive-only and generic traces also contain persistence or errors. “Harbor remains optimal” expresses a recommendation; “confirmed at Harbor” makes a stronger commitment-like statement, but semantic classification remains an AI-assisted reading. A matching wrong final plan does not establish persuasion. Only one family actually revised away from an owned option, so broader claims about resisting user revisions remain unsupported.'])
 (HERE/'COUNTEREXAMPLES.md').write_text('\n\n'.join(lines)+'\n');write(HERE/'reports/COUNTEREXAMPLE_SELECTION.json',manifest);write(HERE/'reports/COUNTEREXAMPLE_QUOTES.json',quotes)
if __name__=='__main__':
 import argparse;p=argparse.ArgumentParser();p.add_argument('--run-root');a=p.parse_args();main(a.run_root)
