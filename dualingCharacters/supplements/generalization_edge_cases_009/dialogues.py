"""Exact generated dialogue/action excerpts with complete chronological companions."""
from collections import defaultdict
import html
from .common import *
from .analysis import stream
from .scenarios import all_scenarios,metadata
ESC=html.escape
STYLE='body{font:17px/1.5 system-ui;max-width:1150px;margin:auto;padding:24px;color:#17212b}article,section{border:1px solid #bbc;padding:16px;margin:16px 0}blockquote{background:#edf4f8;border-left:4px solid #357;padding:12px;white-space:pre-wrap}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f4f4;padding:12px;font-size:13px}small{overflow-wrap:anywhere}.annotation{background:#fff3cf;padding:10px}summary{cursor:pointer;font-weight:bold}nav a{margin-right:12px}img{max-width:100%}'
def code(x):return json.dumps(x,ensure_ascii=False)
def make(run_root=None):
 run_root=Path(run_root) if run_root else ROOT/'artifacts/runs';a=read(HERE/'ALLOCATION.json');scenarios={(s.family_id,s.world):s for s in all_scenarios()};index={};hashes={};selected=set(a['examples'].values());panels=[];checks=[]
 for job in a['jobs']:
  for c in job['conditions']:
   base=run_root/job['run_id'];p=base/(c+'.jsonl');ap=base/(c+'_characters.jsonl')
   if not p.exists() or not ap.exists():continue
   hashes[str(p.relative_to(run_root))]=sha(p);hashes[str(ap.relative_to(run_root))]=sha(ap)
   for kind,path in [('answer',p),('action',ap)]:
    for line,r in stream(path):
     if r['family_id'] not in selected:continue
     key=(job['model'],job['seed'],c,r['family_id'],r['world']);entry=index.setdefault(key,{'answers':{},'actions':{}});entry['answers' if kind=='answer' else 'actions'][r['turn']]={'row':r,'locator':str(path.relative_to(run_root))+f'#L{line}','hash':hashes[str(path.relative_to(run_root))]}
 full=['<!doctype html><meta charset="utf-8"><title>Complete stage009 selected trajectories</title><style>'+STYLE+'</style><h1>Complete selected trajectories</h1><p>Authored synthetic user scripts, generated structured answers, and internal action events. Quoted text is unedited. Analyst truth is separate and never fed into policy inputs.</p>'];md=['# Eight matched dialogue groups','Selection was frozen by family hash, one family per pattern, seed17 and Qwen authorized world. C3/C5/A1 share scripts/catalogs but have different generated histories. Phi and opposite worlds are in the full chronological companion. Examples are illustrations, not prevalence estimates.','Full-context links use a compressed companion: first run `gzip -dc evidence/FULL_DIALOGUES.html.gz > FULL_DIALOGUES.html` from this supplement directory. Then open [Complete selected trajectories](FULL_DIALOGUES.html) · [Results](RESULTS.md)']
 for key,entry in sorted(index.items()):
  model,seed,c,fid,world=key;s=scenarios[fid,world];eid=f'{model}-{seed}-{c}-{fid}-{world}'
  full.append(f'<article id="{ESC(eid)}"><h2>{ESC(eid)}</h2><details><summary>Complete chronological transcript,32 user turns and recorded actions</summary>')
  for t in range(1,33):
   answer=entry['answers'].get(t);act=entry['actions'].get(t);msg=s.messages[t-1]
   full.append(f'<section><h3>Turn {t} · user source {msg.index}</h3><blockquote>{ESC(msg.text)}</blockquote>')
   if act:
    r=act['row'];body=json.loads(r['prompt'][-1]['content']);after=json.loads(answer['row']['prompt'][-1]['content'])['memory'] if answer else None
    full.append(f'<h4>Internal action · {ESC(r["actor"])} · {ESC(r["kind"])}</h4><blockquote>{ESC(r["claim"])}</blockquote><p>Typed slot/value: {ESC(code([r.get("slot"),r.get("value")]))}; applied: {r["applied"]}; target: {ESC(str(r.get("target")))}.</p><pre>Before: {ESC(code(body["memory"]))}\nAfter intervention: {ESC(code(after))}</pre><details><summary>Actual actor observation, source IDs, inbox and generated text</summary><pre>{ESC(code(body))}</pre><pre>Generated response: {ESC(r["generation"]["raw"])}</pre></details><small>{ESC(act["locator"])} · SHA256 {act["hash"]}</small>')
   if answer:
    r=answer['row'];full.append(f'<h4>Answerer structured decision</h4><pre>{ESC(code(r["generation"].get("parsed",{})))}</pre><details><summary>Answerer observation and raw output</summary><pre>{ESC(code(r["prompt"]))}</pre><pre>{ESC(r["generation"]["raw"])}</pre></details><p class="annotation">Analyst-only time-indexed target: {ESC(code(r["target"]))}</p><small>{ESC(answer["locator"])} · SHA256 {answer["hash"]}</small>')
   else:full.append('<p>Answer missing; no substitute generated.</p>')
   full.append('</section>')
  full.append('</details></article>')
 (HERE/'FULL_DIALOGUES.html').write_text('\n'.join(full))
 compact=['<!doctype html><meta charset="utf-8"><title>Stage009 matched dialogues</title><style>'+STYLE+'</style><h1>Eight matched dialogue groups</h1><p>Exact quotations, action events and structured decisions. These are fixed scripted synthetic cases; the explanatory readings are AI-assisted illustrations.</p><p>Before following full-context links, extract the offline companion from this directory: <code>gzip -dc evidence/FULL_DIALOGUES.html.gz &gt; FULL_DIALOGUES.html</code>.</p>']
 for pattern,fid in a['examples'].items():
  s=scenarios[fid,'authorized'];m=metadata(s);k=m['slot'];md.extend([f'## {pattern} — {fid}',f'User turn 12, source 23: **“{s.messages[11].text}”**',f'Analyst expectation: {code(s.truth_at(12).target(s.spec))}. The opposite world says: “{scenarios[fid,"hypothetical"].messages[11].text}”'])
  compact.append(f'<section id="{ESC(pattern)}"><h2>{ESC(pattern.replace("_"," ").capitalize())} · {ESC(fid)}</h2><h3>User turn 12 · source 23</h3><blockquote>{ESC(s.messages[11].text)}</blockquote><details><summary>Paired non-authorizing instruction</summary><blockquote>{ESC(scenarios[fid,"hypothetical"].messages[11].text)}</blockquote></details>')
  reading=read(HERE/'CASE_READINGS.json')['readings'].get(pattern) if (HERE/'CASE_READINGS.json').exists() else None
  if reading:
   md.append('**AI-assisted comparative reading:** '+reading);compact.append('<p class="annotation"><strong>AI-assisted comparative reading:</strong> '+ESC(reading)+'</p>')
  for c in ['C3','C5','A1']:
   key=('qwen',17,c,fid,'authorized');entry=index.get(key);eid='-'.join(map(str,key))
   if not entry:md.append(f'### {c}: missing');compact.append(f'<h3>{c}: missing</h3>');continue
   eligible=[t for t,r in entry['actions'].items() if t>=12 and not r['row']['communication_slot']]
   if not eligible:md.append(f'### {c}: no subsequent direct opportunity');continue
   t=min(eligible);act=entry['actions'][t];r=act['row'];ans=entry['answers'].get(t);body=json.loads(r['prompt'][-1]['content']);after=json.loads(ans['row']['prompt'][-1]['content'])['memory'] if ans else None;final=entry['answers'].get(32)
   prior=[x for tt,x in entry['actions'].items() if tt<t and x['row']['actor']==r['actor']];prior=max(prior,key=lambda x:x['row']['turn']) if prior else None
   before=body['memory'];generated=r['generation'].get('parsed',{}).get('claim','');truncated=str(generated)!=r['claim']
   priorquote=prior['row']['claim'] if prior else '[No earlier recorded opportunity]'
   observation=f"At this opportunity the API is {r['kind']}, typed goal {code([r.get('slot'),r.get('value')])}; applied={r['applied']}. Structured memory values {'change' if before['state']!=after['state'] else 'do not change'} immediately. The following plan's decisive value is {code(ans['row']['generation'].get('parsed',{}).get('plan',[])[k:k+1]) if ans else 'missing'}; current authorized value is {code(s.truth_at(t).target(s.spec)['plan'][k])}."
   interpretation='This records tool choice and a stated position. It does not establish persuasion, deliberate deception, or whether a peer message caused the next action. A recommendation may disagree with the user without claiming user authorization; use the exact compound text to assess that distinction.'
   panel={'case_id':eid,'pattern':pattern,'family_id':fid,'condition':c,'turn':t,'actor':r['actor'],'user_message':s.messages[11].public(),'prior_claim':priorquote,'claim':r['claim'],'generated_claim':generated,'truncated':truncated,'api_kind':r['kind'],'typed_slot':r.get('slot'),'typed_value':r.get('value'),'source':r.get('source'),'visible_inbox':body['inbox'],'visible_sources':body['sources'],'before_memory':before,'after_memory':after,'following_answer':ans['row']['generation'].get('parsed',{}) if ans else None,'final_answer':final['row']['generation'].get('parsed',{}) if final else None,'locator':act['locator'],'sha256':act['hash'],'observation':observation,'interpretation':interpretation}
   panels.append(panel);checks.append({'locator':act['locator'],'field':'claim','exact_quote':r['claim'],'source_sha256':act['hash']})
   md.extend([f'### {c} · {r["actor"]} · turn {t}',f'Previous own statement: “{priorquote}”',f'Actually visible inbox: `{code(body["inbox"])}`',f'Exact delivered claim: **“{r["claim"]}”**'+(' **[Truncated to240 characters; generated suffix in full trace.]**' if truncated else ''),f'API `{r["kind"]}`; typed `{code([r.get("slot"),r.get("value")])}`; source `{r.get("source")}`; applied `{r["applied"]}`.',f'Before memory: `{code(before)}`\n\nAfter action: `{code(after)}`',f'Following structured answer: `{code(panel["following_answer"])}`',f'Final structured answer: `{code(panel["final_answer"])}`',f'**Observation:** {observation}\n\n**Provisional reading / limit:** {interpretation}',f'Source `{act["locator"]}`, SHA256 `{act["hash"]}`. [Full chronological context](FULL_DIALOGUES.html#{eid}).'])
   compact.append(f'<article><h3>{c} · {ESC(r["actor"])} · turn {t}</h3><p>Prior own position:</p><blockquote>{ESC(priorquote)}</blockquote><details><summary>Actual visible inbox and sources</summary><pre>{ESC(code({"inbox":body["inbox"],"sources":body["sources"]}))}</pre></details><p>Selected statement:</p><blockquote>{ESC(r["claim"])}</blockquote><p>{"Delivered prefix truncated to240 characters; generated suffix only in full trace." if truncated else "No delivered-claim truncation."}</p><p>API {r["kind"]}; typed {ESC(code([r.get("slot"),r.get("value")]))}; source {r.get("source")}; applied {r["applied"]}.</p><details><summary>Memory and following/final structured answers</summary><pre>{ESC(code({"before":before,"after":after,"following":panel["following_answer"],"final":panel["final_answer"]}))}</pre></details><p class="annotation">Observation: {ESC(observation)}</p><p>Provisional interpretation: {ESC(interpretation)}</p><small>{ESC(act["locator"])} · SHA256 {act["hash"]}</small><p><a href="FULL_DIALOGUES.html#{ESC(eid)}">Complete chronological context</a></p></article>')
  compact.append('</section>')
 (HERE/'DIALOGUES.md').write_text('\n\n'.join(md)+'\n');(HERE/'DIALOGUES.html').write_text('\n'.join(compact));write(HERE/'tables/dialogue_panels.json',panels);write(HERE/'reports/QUOTE_CHECK_INPUTS.json',checks);write(HERE/'reports/DIALOGUE_SOURCE_HASHES.json',hashes)
 print({'matched_groups':len(a['examples']),'panels':len(panels),'complete_episode_views':len(index),'exact_selected_quotes':len(checks)})
if __name__=='__main__':
 import argparse;p=argparse.ArgumentParser();p.add_argument('--run-root');a=p.parse_args();make(a.run_root)
