"""Reuse locked dialogue panels; verify exact selected-record identities; no new selection."""
import gzip,json
from .common import *
from supplements.results_clarity_007.common import members
from supplements.dialogue_interpretation_005.extraction import get_value
CASES=['DI5-a4c89ffad4','DI5-e743bcb1a6','DI5-2e4899b66b','DI5-adc5b43b95']
def tex(s):
 return ''.join({'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}.get(c,c) for c in str(s))
def main():
 original=read(ROOT/'supplements/results_clarity_007/tables/READER_CONTENT.json');groups=[g for g in original['groups'] if g['id'] in CASES];records={}
 for line in gzip.decompress(members()['selected_records.jsonl.gz']).decode().splitlines():
  r=json.loads(line);records[r['file'],r['record']]=r
 quotes=[];out=['# Dialogue appendix\n','Four already selected illustrative groups, not a prevalence sample. Matched conditions share the original scenario and schedule; later generated histories differ. All dialogue is synthetic, produced by frozen Qwen components. C3 = generic adversaries; C5 = biographies plus motives; A1 = motives without biographies. Interpretations below are AI-assisted and not human annotations.\n']
 for g in groups:
  out+=['## '+g['id']+' — '+g['title']+'\n']
  for c in g['cells']:
   out+=['### '+c['condition']+f" · seed {c['seed']} · {c['family']} · {c['world']}\n"]
   for q in c['authorization']+([c['prior']] if c['prior'] else [])+[c['selected']]+c['followups']:
    loc=q['locator'];r=records[loc['file'],loc['record']];assert r['file_sha256']==loc['sha256'];assert get_value(r['value'],loc)==q['text'];quotes.append({'case':g['id'],'condition':c['condition'],**q})
    out+=[q['label']+'\n','> '+q['text']+'\n',f"Source: `{q['short_locator']}`; original SHA256 `{loc['sha256']}`.\n"]
   if not c['followups']:out+=['No recorded subsequent recipient opportunity. This is not evidence of ignoring.\n']
   out+=['Transport (annotation): '+json.dumps(c['route'],ensure_ascii=False)+'\n']
   if c['truncated']:out+=['**Delivered text is a truncated prefix. The omitted generated suffix is not recipient evidence.**\n']
   out+=['Structured answerer outputs (not speech):\n','```json\n'+json.dumps(c['answer_turns'],ensure_ascii=False,indent=2)+'\n```\n']
  out+=['Observation: '+g['observation']+'\n','Provisional reading: '+g['interpretation']+'\n','Alternative: '+g['alternative']+'\n']
 (HERE/'DIALOGUE_APPENDIX.md').write_text('\n'.join(out))
 write(HERE/'inputs/DIALOGUE_PANELS.json',groups);write(HERE/'inputs/DIALOGUE_QUOTES.json',quotes);write(HERE/'reports/DIALOGUE_VERIFICATION.json',{'cases':CASES,'matched_episodes':12,'exact_quote_checks':len(quotes),'scope':'Selected-record verification against committed006 archive; not an independent rehash of entire original archives.','source_sha256':sha(ROOT/'supplements/results_clarity_007/tables/READER_CONTENT.json')})
 # Short manuscript panels; complete chronology and route retained in the companion appendix.
 g=next(g for g in groups if g['id']==CASES[0]);c=next(c for c in g['cells'] if c['condition']=='C5')
 lines=[r'\subsection{Dialogue evidence: preference and authorization}',r'These four retrospective matched groups are illustrative, not semantic prevalence estimates. Full contexts and exact source locators are supplied separately. Component aliases are synthetic. A shared scenario does not make divergent generated histories a counterfactual replay.',r'\paragraph{A challenge followed by continued advocacy.} Case '+tex(g['id'])+r' (C5, seed 29) supplies the following chronological exchange:']
 for q in c['authorization']+[c['prior'],c['selected']]+c['followups']:
  lines +=[r'\begin{quote}\small\textbf{'+tex(q['label'])+r'} '+tex(q['text'])+r'\end{quote}']
 lines +=[r"The message is delivered to the recipient inbox and visible at its next opportunity. The turn-13 structured plan retains Tuesday. ``should be Saturday'' can express a preference; it is not by itself a claim that the user approved Saturday. The earlier turn-9 statement invoked ``user-approved constraints,'' so the trajectory also contains stronger authority framing. Continued advocacy after visible criticism does not distinguish disagreement from routine repetition or non-engagement. The correct Tuesday plan does not establish that the challenge caused it. In matched A1, the earlier proposal explicitly pursues Saturday for its owned-option objective; in C3, the actor directly edits the day. Those are observable channel contrasts, not uniquely biographical semantic acts."]
 for case,cond,text in [
 (CASES[1],'C5','A recommendation crosses API labels. The cap proposal is expressed as a preference; nearby recollection wording presents a return to an earlier venue as correction. The latter delivered message ends mid-word and its omitted suffix cannot be interpreted as received evidence.'),
 (CASES[2],'C5','An apparent correction is not automatically supported. The speaker calls Thursday binding and Saturday outdated, but the authorized state in this selected contrast does not support that correction. The statement is an illustration of contested authority, not proof of a deliberate lie.'),
 (CASES[3],'C3','Evidence criticism also occurs without biographies. The generic component challenges a peer using evidence language. Its existence rules out treating criticism as unique to C5; it does not estimate how often criticism occurs.')]:
  gg=next(g for g in groups if g['id']==case);cc=next(c for c in gg['cells'] if c['condition']==cond)
  lines +=[r'\paragraph{'+tex(gg['title'])+r'.} '+tex(case)+' ('+cond+'). '+tex(text),r'\begin{quote}\small '+tex(cc['selected']['text'])+(r' \textit{[Delivered prefix truncated.]}' if cc['truncated'] else '')+r'\end{quote}']
  if case==CASES[1]:
   aa=next(x for x in gg['cells'] if x['condition']=='A1')
   lines +=[r'In matched motive-only A1, the selected statement instead openly offers a rationale:',r'\begin{quote}\small '+tex(aa['selected']['text'])+r'\end{quote}',r'The contrast concerns this received text, not a measured population difference in false authority. Both components pursue Garden despite different wording; their preceding generated histories differ.']
 (HERE/'paper/sections/dialogues.tex').write_text('\n\n'.join(lines)+'\n')
 print('Verified',len(quotes),'quotes in12matched episodes')
if __name__=='__main__':main()
