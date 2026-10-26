"""Short author edition over unchanged006 extraction; quotations retain exact locators."""
from html import escape as h
from .common import *
from .cases import CASES
from .prose import tidy
from supplements.evidence_validation_006.presentation import exchange
from supplements.dialogue_interpretation_005.rendering import document

def run():
 es=episodes();groups=[];sources={};quotations=[]
 def q(text,locator,label):
  assert locator
  key=locator['file']+'|'+locator['sha256'];sources[key]={'file':locator['file'],'sha256':locator['sha256']}
  item={'label':label,'text':text,'locator':locator,'source_key':key};quotations.append(item);return item
 def speech(z,label):
  if not z:return None
  a=z['action'];return q(a['claim'],a['claim_locator'],f"{label}: turn {z['turn']} · {a['neutral_speaker']} ({a['actor']}) · API {a['kind']} · opportunity {a['opportunity']}")
 for original_spec in CASES:
  spec={k:tidy(v) if k in {'title','observation','interpretation','alternative','question'} else v for k,v in original_spec.items()}
  cells=[]
  for c in ['C3','C5','A1']:
   e=next(e for e in es if e['case_id']==spec['id'] and e['condition']==c and e['anchor']);x=exchange(e);a=x['selected']['action'];extra=[]
   if spec['id']=='DI5-a4c89ffad4':extra=[{'turn':9,'action':e['turns'][8]['action']}] if c=='C5' else []
   if spec['id']=='DI5-e743bcb1a6' and c=='A1':extra=x['extra_expression_context']
   if spec['id']=='DI5-2e4899b66b' and c=='C5':extra=x['extra_expression_context']
   cell={'condition':c,'episode_id':e['episode_id'],'seed':e['seed'],'family':e['family_id'],'world':e['world'],'alias_map':x['actor_key'],
    'authorization':[q(u['text'],u['locator'],f"A. User · turn {(u['index']+1)//2} · source #{u['index']}") for u in x['authority'] if u['index'] in spec['user_sources']],
    'prior':speech(x['recipient_before'],'B. Recipient prior'),
    'selected':speech(x['selected'],'C. Selected statement/action'),
    'extra':[speech(z,'Earlier context') for z in extra],
    'followups':[speech(z,'E. First recipient opportunity' if i==0 else 'F. Second opportunity (separate context)') for i,z in enumerate(x['following'])],
    'route':x['route'],'sender_sources':[{'index':s['index'],'author':s['author']} for s in a['observation']['sources']],
    'memory_before':a['memory_before'],'memory_after_action':a['memory_before_answer'],
    'answer_turns':[{'turn':z['turn'],'parsed':z['answer']['parsed'],'locator':z['answer']['locator']} for z in [x['selected']]+x['following']],
    'analyst_truth':x['selected']['truth'],'truncated':a['truncated'],'generated_claim':a['generated_claim'],
    'typed':{'slot':a['slot'],'value':a['value'],'source':a['source']},'full_link':'../evidence_validation_006/extracted/author/DIALOGUE_ATLAS.html#'+e['episode_id']}
   for z in cell['answer_turns']:sources[z['locator']['file']+'|'+z['locator']['sha256']]={'file':z['locator']['file'],'sha256':z['locator']['sha256']}
   cells.append(cell)
  groups.append(dict(spec,cells=cells))
 for i,key in enumerate(sorted(sources)):sources[key]['id']=f'S{i+1:02}'
 for quote in quotations:quote['short_locator']=sources[quote['source_key']]['id']+' record '+str(quote['locator']['record'])+' / '+'.'.join(map(str,quote['locator']['field']))
 data={'title':'Persistent pursuit, expressed claims, and user authorization','selection':'Six retrospective purposive groups from the existing locked48episodes; includes ordinary repetition and the previously declared unsupported-correction contrast. Not random, representative or independently blinded. Each matched group shares a script and schedule, not identical generated histories.','legend':'C3: two generic adversaries. C5: two biography-plus-motive actors. A1: the same motives without biographies. One answerer is additional. All shown episodes use the shared frozen base Qwen model;16 synthetic user/answerer turns,12 actor opportunities.','groups':groups,'sources':list(sources.values())}
 data['legend']=data['legend'].replace(';16','; 16').replace(',12',', 12')
 data['selection']=data['selection'].replace('locked48episodes','locked 48 episodes')
 write(HERE/'tables/READER_CONTENT.json',data);write(HERE/'tables/READER_QUOTATIONS.json',quotations)
 def quote_html(q):return '<p class="label">'+h(q['label'])+'</p><blockquote>'+h(q['text'])+'</blockquote><p class="locator"><a href="#'+sources[q['source_key']]['id']+'">'+h(q['short_locator'])+'</a></p>' if q else '<p>No prior recipient opportunity recorded.</p>'
 def detail(label,obj):return '<details><summary>'+h(label)+'</summary><pre>'+h(json.dumps(obj,ensure_ascii=False,indent=2))+'</pre></details>'
 body='<h1>'+data['title']+'</h1><p class="warning">Author-facing AI-assisted interpretation. Human semantic validation remains pending. Do not give this edition to independent raters.</p><p>'+data['legend']+'</p><p>'+data['selection']+'</p><p><a href="ARCHITECTURE.md">Architecture</a> · <a href="FINDINGS_BRIEF.pdf">Two-page findings</a> · <a href="../evidence_validation_006/CASEBOOK_V2.pdf">Unchanged 62-page evidence casebook</a> · <a href="../evidence_validation_006/extracted/author/DIALOGUE_ATLAS.html">Complete 48-episode atlas (run the documented reader command first)</a></p><ol>'
 for g in groups:body+='<li><a href="#'+g['id']+'">'+g['title']+'</a></li>'
 body+='</ol><p>Quotation boxes are exact logged text. An edit is an action event, not invented speech. JSON is a recorded structured output. Truncation means a generated suffix was not delivered. Analyst truth is never a model input.</p>'
 md=['# '+data['title'],'',data['legend'],'',data['selection'],'','Author-only AI-assisted readings, not validated human annotations. Routine intervening turns are omitted in this edition; full context remains linked.','']
 for g in groups:
  body+='<section class="case" id="'+g['id']+'"><h2>'+g['id']+' — '+h(g['title'])+'</h2><p>Routine intervening turns are omitted here; no events have been reordered within A–H roles. The labels group evidence by function, with turn indices preserving chronology.</p>'
  md+=['## '+g['id']+' — '+g['title'],'']
  for c in g['cells']:
   primary=c['condition']==g['primary'];body+=('<div>' if primary else '<details><summary>Matched '+c['condition']+' trajectory (different generated history)</summary>')+'<h3>'+c['condition']+' · '+c['episode_id']+'</h3><p>'+h('; '.join(a['neutral']+' = '+a['alias'] for a in c['alias_map']))+'</p>'
   md+=['### '+c['condition']+' · '+c['episode_id'],'']
   for q0 in c['authorization']+c['extra']+[c['prior'],c['selected']]:
    body+=quote_html(q0)
    if q0:md+=['**'+q0['label']+'**','', '> '+q0['text'],'',q0['short_locator'],'']
   body+='<h4>D. Actual route and visibility</h4><p>'+h(c['route']['type'])+'; delivered='+str(c['route']['delivered'])+'; visible='+str(c['route']['visible'])+'. '+h(c['route']['explanation'])+'</p>'+detail('Actual delivered payload',c['route']['actual_delivered_payload'])+detail('Sender-visible source IDs and authors',c['sender_sources'])+detail('Direct action: memory before and after',{'before':c['memory_before'],'after':c['memory_after_action']})
   if c['truncated']:body+='<p class="warning">The selected claim is the exact240-character delivered prefix, including its incomplete ending.</p>'+detail('Longer generated claim; suffix not delivered',c['generated_claim'])
   for q0 in c['followups']:
    body+=quote_html(q0)
    if q0:md+=['**'+q0['label']+'**','', '> '+q0['text'],'',q0['short_locator'],'']
   body+='<h4>G. Answerer decisions (structured, not speech)</h4>'
   for z in c['answer_turns']:body+=detail('Turn '+str(z['turn'])+' exact parsed output',z['parsed'])
   body+=detail('Analyst-only current authorized state',c['analyst_truth'])+'<p><a href="'+c['full_link']+'">Complete episode and original record locators</a></p>'+('</div>' if primary else '</details>')
   md+=['D. Route/delivery/visibility: `'+json.dumps(c['route'],ensure_ascii=False)+'`','', 'G. Exact answerer parsed outputs:','```json',json.dumps(c['answer_turns'],ensure_ascii=False,indent=2),'```','', '[Complete trace]('+c['full_link']+')','']
  body+='<div class="interpretation"><h3>H. Provisional interpretation, not independent validation</h3>'
  for key,label in [('observation','Observation'),('interpretation','Reading'),('alternative','Alternative / limit'),('question','Unresolved')]:
   body+='<p><b>'+label+':</b> '+h(g[key])+'</p>';md+=['**'+label+':** '+g[key],'']
  body+='</div></section>'
 body+='<h2 id="sources">Source appendix</h2><p>Source hashes identify original full files. The committed006 archive contains selected records; verifying those records does not verify omitted bytes of entire original traces. Complete field and decoded-source locators are in <a href="tables/READER_QUOTATIONS.json">READER_QUOTATIONS.json</a>.</p>'
 for s in data['sources']:body+='<div id="'+s['id']+'"><h3>'+s['id']+'</h3><code>'+h(s['file'])+'</code><p>SHA256 '+s['sha256']+'</p></div>'
 body+='<p>Reuse the committed006 archives and its reader/verification commands. No machine-specific source directory is required. See START_HERE.md for extraction. Original006 and005 editions remain unchanged.</p>'
 html=document(data['title'],body).replace('</head>','<style>.locator{font-size:.78rem;overflow-wrap:anywhere}.label{font-weight:600}blockquote{white-space:pre-wrap}.case{max-width:1100px}summary{cursor:pointer}pre{overflow-wrap:anywhere;white-space:pre-wrap}</style></head>')
 (HERE/'READER_EDITION.html').write_text(html);(HERE/'READER_EDITION.md').write_text('\n'.join(md))
 print('6 matched case groups /18episodes; exact quotation manifest; author HTML+Markdown.')
if __name__=='__main__':run()
