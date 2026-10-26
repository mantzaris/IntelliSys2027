"""Artifact-dependent checks, separate from fresh-clone software unit tests."""
from collections import Counter
from urllib.parse import urlsplit,unquote
import re
from .common import *
from .analysis import stream
from .scenarios import all_scenarios

def main(run_root):
 root=Path(run_root);allocation=read(HERE/'ALLOCATION.json');verify(HERE/'SCIENTIFIC_FREEZE.json');verify(HERE/'PROFILE_FREEZE.json');models=read(ROOT/'configs/models.json')
 expected={(s.family_id,s.world) for s in all_scenarios()};results=[];missing=[]
 for job in allocation['jobs']:
  folder=root/job['run_id']
  if not folder.exists():missing.append(job['run_id']);continue
  status=read(folder/'status.json');assert status['status']=='completed';assert status['config']['model']==job['model'];assert status['config']['seed']==job['seed'];assert status['no_adapter']
  assert status['model_revision']==models[job['model']]['revision'];assert status['freeze_sha256']==sha(HERE/'SCIENTIFIC_FREEZE.json')
  for field,value in {'precision':'bf16','engine':'vllm','structured_decoding':True,'max_input_tokens':4096,'answer_tokens':256,'character_tokens':128,'retrieval_messages':8,'recent_messages':4,'history_actions':6,'intervention_opportunities':12}.items():assert status['config'][field]==value
  assert status['model_calls']==4224
  for c in job['conditions']:
   counts=Counter();calls=0;intokens=outtokens=0;maxinput=0
   for suffix,n in [('',32),('_characters',12)]:
    path=folder/(c+suffix+'.jsonl');seen=set()
    for line,r in stream(path):
     key=r['family_id'],r['world'];unit=(*key,r['turn']);assert unit not in seen;seen.add(unit);counts[suffix,key]+=1
     g=r['generation'];calls+=1;intokens+=g['input_tokens'];outtokens+=g['output_tokens'];maxinput=max(maxinput,g['input_tokens'])
     assert g['input_tokens']<=4096
     if suffix:
      text=str(g.get('parsed',{}).get('claim',''))[:240];assert r['claim']==text
      # Evaluator metadata must not appear as fields in actual prompt JSON.
      body=json.loads(r['prompt'][-1]['content']);assert not {'target','truth','expected','following_success','contrary_to_truth'}&body.keys()
     else:
      body=json.loads(r['prompt'][-1]['content']);assert not {'target','truth','expected'}&body.keys()
    assert {k for s,k in counts if s==suffix}==expected
    assert all(counts[suffix,k]==n for k in expected)
   results.append({'run_id':job['run_id'],'condition':c,'conversations':len(expected),'calls':calls,'input_tokens':intokens,'output_tokens':outtokens,'max_input_tokens':maxinput,'no_prompt_limit_hit':maxinput<4096})
  assert status['model_calls']==sum(r['calls'] for r in results if r['run_id']==job['run_id'])
  assert status['input_tokens']==sum(r['input_tokens'] for r in results if r['run_id']==job['run_id'])
  assert status['output_tokens']==sum(r['output_tokens'] for r in results if r['run_id']==job['run_id'])
 if missing:
  write(HERE/'reports/VERIFICATION.json',{'status':'missing_prerequisite','missing_runs':missing});raise SystemExit('Missing research artifacts: '+','.join(missing))
 checked=0
 for q in read(HERE/'reports/QUOTE_CHECK_INPUTS.json')+(read(HERE/'reports/COUNTEREXAMPLE_QUOTES.json') if (HERE/'reports/COUNTEREXAMPLE_QUOTES.json').exists() else []):
  name,line=q['locator'].rsplit('#L',1);path=root/name;assert sha(path)==q['source_sha256'];record=next(r for i,r in stream(path) if i==int(line));assert record[q['field']]==q['exact_quote'];checked+=1
 links=0
 for filename in ['DIALOGUES.html','FULL_DIALOGUES.html']:
  text=(HERE/filename).read_text();assert '<script' not in text and 'file://' not in text
  for target in re.findall(r'href="([^"]+)"',text):
   parsed=urlsplit(target);assert not parsed.scheme,'External dependency'
   path=HERE/unquote(parsed.path) if parsed.path else HERE/filename;assert path.exists(),target
   if parsed.fragment:assert f'id="{parsed.fragment}"' in path.read_text(),target
   links+=1
 replay_checks=0
 if (HERE/'REPLAY_BINDING.json').exists():
  verify(HERE/'REPLAY_FREEZE.json');binding=read(HERE/'REPLAY_BINDING.json');items={r['item_id']:r for r in read(HERE/'inputs/replay.json')};seen=set()
  for _,r in stream(root/binding['run_id']/'replay.jsonl'):
   key=r['item_id'],r['replay_seed'],r['variant'];assert key not in seen;seen.add(key);item=items[r['item_id']]
   assert r['prompt']==item[r['variant']+'_prompt'];assert r['effective_batch_seed']==r['replay_seed'];replay_checks+=1
  assert len(seen)==4*len(items)==binding['planned_calls']
  for item in items.values():
   actual=json.loads(item['actual_prompt'][-1]['content']);omitted=json.loads(item['omitted_prompt'][-1]['content']);actual['inbox'].pop(item['inbox_index']);assert actual==omitted
   assert item['actual_prompt'][0]==item['omitted_prompt'][0]
 report={'status':'passed','research_conversations':sum(r['conversations'] for r in results),'research_calls':sum(r['calls'] for r in results),'unique_families':16,'quoted_claims_verified':checked,'replay_calls_verified':replay_checks,'portable_links_verified':links,'details':results,'scientific_validation':'These are identity, coverage and accounting checks, not semantic or external validation.'};write(HERE/'reports/VERIFICATION.json',report);print({k:v for k,v in report.items() if k!='details'})
if __name__=='__main__':
 import argparse;p=argparse.ArgumentParser();p.add_argument('--run-root',required=True);main(p.parse_args().run_root)
