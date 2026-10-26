"""Static, offline author atlas and separate blinded full-episode export."""
from collections import defaultdict
from html import escape
import re
from .common import *
from .annotations import resolve_span
from .blinding import reviewer_episode,review_order,substitutions

CSS='''
:root{--ink:#172c35;--muted:#526772;--paper:#f6f4ed;--line:#d5dedc;--teal:#075d63;--blue:#264e80;--gold:#b27c21}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1480px;margin:auto;padding:36px clamp(18px,4vw,64px)}a{color:var(--teal);text-decoration-thickness:1px;text-underline-offset:3px}a:hover{color:#102e6b}
h1,h2,h3,h4{line-height:1.2;letter-spacing:-.025em}h1{font-size:clamp(34px,4.6vw,60px);max-width:1000px;margin:16px 0 22px}h2{font-size:30px;margin:0 0 16px}h3{font-size:23px}h4{font-size:17px}
p{max-width:90ch}.eyebrow{text-transform:uppercase;letter-spacing:.13em;color:var(--teal);font-size:12px;font-weight:750}.lede{font-size:20px;color:#344f58;max-width:80ch}.muted,small{color:var(--muted)}
.tag{display:inline-block;font-size:12px;border:1px solid var(--line);border-radius:16px;padding:3px 10px;margin:3px;background:#fff}.warning{background:#fff5d9;border-left:4px solid var(--gold);padding:14px 20px}.axes,.matched{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.axis{background:#e7efec;padding:20px;border-radius:12px}.axis strong{display:block;font-size:20px}
.toc{columns:2;column-gap:30px;padding-left:24px}.toc li{break-inside:avoid;margin:9px 0}.case{padding-top:45px;margin-top:42px;border-top:2px solid var(--ink)}.case-header{display:flex;justify-content:space-between;gap:20px;align-items:start}.case-header h2{max-width:900px}.world-controls{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0}button{font:inherit;border:1px solid var(--teal);border-radius:6px;background:#fff;color:var(--teal);padding:7px 15px;cursor:pointer}button[aria-pressed=true]{background:var(--teal);color:#fff}button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid #bd8333;outline-offset:3px}
.interpretation{background:white;border:1px solid var(--line);padding:24px;border-radius:12px;max-width:100%}.interpretation p{max-width:100ch}.boundary{display:grid;grid-template-columns:1fr 1fr;gap:20px}.boundary>div{background:#edf2ef;padding:15px;border-radius:8px}.boundary>div:last-child{background:#f7f0df}
.episode{min-width:0;background:white;border:1px solid var(--line);border-radius:12px;padding:18px}.episode>h3{margin:8px 0}.trace{margin-top:18px}.trace>summary{font-weight:700;color:var(--teal);padding:12px 0}.turn{border-top:1px solid var(--line);padding:12px 0}.turn>summary{font-weight:650;cursor:pointer}.turn[open]>summary{margin-bottom:12px}
.speech{border-left:3px solid var(--teal);padding:8px 12px;margin:12px 0;background:#f1f7f4;white-space:pre-wrap;overflow-wrap:anywhere}.component{border-color:var(--blue);background:#f0f4fb}.speaker{font-size:12px;font-weight:750;text-transform:uppercase;letter-spacing:.05em;margin-top:10px}.action{border:1px solid #b9cbd2;padding:12px;background:#f4f7fa;border-radius:8px;margin:14px 0}.action b{color:var(--blue)}.analyst{background:#fff6e3;border-left:3px solid var(--gold);padding:10px 12px;margin-top:12px}.answer{padding:8px 0}.answer table{font-size:12px}.source{padding:12px;border:1px solid var(--line);margin:8px 0;scroll-margin-top:10px}.locator{font-size:11px;line-height:1.4;color:var(--muted);overflow-wrap:anywhere;margin:4px 0}.locator summary{cursor:pointer}details.evidence{font-size:13px;margin:8px 0}details.evidence>summary{color:var(--teal);cursor:pointer}.linkrow{font-size:12px;line-height:1.8}.missing{font-style:italic;color:#75572e}.mono,code,pre{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}code{font-size:.85em}pre{font-size:11px;line-height:1.45;white-space:pre-wrap;overflow-wrap:anywhere;max-height:480px;overflow:auto;background:#f2f4f3;padding:12px}table{width:100%;border-collapse:collapse;margin:12px 0;font-variant-numeric:tabular-nums}th,td{text-align:left;vertical-align:top;border-bottom:1px solid var(--line);padding:7px;overflow-wrap:anywhere}th{font-weight:650;color:#35515b}.mini{font-size:13px}.excerpt{margin:16px 0}.footer{border-top:1px solid var(--line);padding-top:20px;margin-top:40px;font-size:13px}[hidden]{display:none!important}
@media(max-width:900px){.matched,.axes,.boundary{grid-template-columns:1fr}.case-header{display:block}.toc{columns:1}.episode{padding:16px}main{padding:25px 16px}.case{margin-top:28px;padding-top:28px}}
@media print{body{background:white;font:10pt/1.45 Georgia,serif}main{max-width:none;padding:0}h1{font-size:25pt}h2{font-size:17pt}.case{break-before:page;border:0;padding-top:0}.world-controls,button,.toc{display:none}.matched{display:block}.episode{border:0;padding:0}.interpretation{border:0;padding:0}.boundary{display:block}pre{max-height:none}.footer{font-size:8pt}a{color:inherit}.casebook-case{break-before:page}.casebook-case:first-of-type{break-before:auto}.casebook-case blockquote{break-inside:avoid}}
'''
JS='''
document.querySelectorAll('[data-world-button]').forEach(b=>b.addEventListener('click',()=>{
 const section=b.closest('.case');section.querySelectorAll('[data-world]').forEach(w=>w.hidden=w.dataset.world!==b.dataset.worldButton);
 section.querySelectorAll('[data-world-button]').forEach(x=>x.setAttribute('aria-pressed',x===b?'true':'false'));
}));
document.querySelectorAll('.case').forEach(c=>{const b=c.querySelector('[data-world-button][aria-pressed=true]');if(b)b.click()});
function revealHash(){if(!location.hash)return;let id;try{id=decodeURIComponent(location.hash.slice(1))}catch(e){return}const target=document.getElementById(id);if(!target)return;
 for(let n=target;n;n=n.parentElement){if(n.tagName==='DETAILS')n.open=true;if(n.dataset&&n.dataset.world){const c=n.closest('.case');if(c){const b=Array.from(c.querySelectorAll('[data-world-button]')).find(x=>x.dataset.worldButton===n.dataset.world);if(b)b.click()}n.hidden=false}}
 target.scrollIntoView({block:'start',behavior:'instant'});
}window.addEventListener('hashchange',revealHash);setTimeout(revealHash,50);
'''

def h(value):return escape(str(value),quote=True)
def pretty(value):return h(json.dumps(value,indent=2,ensure_ascii=False))
def loc(location):
    if not location:return ''
    field='.'.join(map(str,location['field']))
    if 'decoded' in location:field+=' → decoded JSON /'+ '/'.join(map(str,location['decoded']))
    return f'<details class="locator"><summary>{h(Path(location["file"]).parent.name)} / {h(Path(location["file"]).name)} : record {location["record"]} · {h(field)}</summary>SHA256 {h(location["sha256"])}<br>One-based decompressed JSONL record; the evidence bundle preserves the exact record.</details>'
def source_links(episode_id,sources):
    return ' '.join(f'<a href="#{h(episode_id)}-source-{m["index"]}">#{m["index"]} {h(m["author"])}</a>' for m in sources)
def json_detail(label,value):return f'<details class="evidence"><summary>{h(label)}</summary><pre>{pretty(value)}</pre></details>'
def quote(text,cls=''):return f'<blockquote class="speech {cls}">{h(text)}</blockquote>'
def plan_table(parsed,catalog):
    fields=catalog['fields']+['transport','equipment'];plan=parsed.get('plan',[])
    rows=''.join(f'<tr><td>{h(name)}</td><td>{h(plan[i] if i<len(plan) else "missing")}</td><td>{h(parsed.get("evidence",[])[i] if i<6 and len(parsed.get("evidence",[]))>i else "—")}</td></tr>' for i,name in enumerate(fields))
    return f'<table><thead><tr><th>Executable field</th><th>Recorded value</th><th>Reference</th></tr></thead><tbody>{rows}</tbody></table><div class="mini">Clarification: {h(parsed.get("clarify",[]))}</div>'

def memory_delta(action):
    before=action['memory_before'];after=action['memory_before_answer'];changes=[]
    for i,(a,b) in enumerate(zip(before['state'],after['state'])):
        if a!=b:changes.append(f'{action["observation"]["catalog"]["fields"][i]}: {a} → {b}')
    refs=[f'{i}: {a} → {b}' for i,(a,b) in enumerate(zip(before['evidence'],after['evidence'])) if a!=b]
    return f'<div class="mini">Same-turn state change: {h("; ".join(changes) or "none")}. Reference change: {h("; ".join(refs) or "none")}. Notes changed: {before["notes"]!=after["notes"]}.</div>'+json_detail('Exact memory before action',before)+json_detail('Exact memory supplied to answerer after action',after)

def episode_html(e,blinded=False):
    eid=e.get('episode_id',e.get('item_id'));out=[]
    if not e.get('available',True):return f'<article class="episode"><h3>{h(e["condition"])}</h3><p class="missing">Missing at cutoff: {h(e["reason"])}</p></article>'
    title=eid if blinded else e['condition']+' · '+eid
    out.append(f'<article class="episode" id="{h(eid)}"><p class="eyebrow">Recorded full episode</p><h3>{h(title)}</h3>')
    if not blinded:
        out.append(f'<div class="mini">Seed {e["seed"]} · {h(e["family_id"])} · {h(e["world"])} · 16 turns / 12 opportunities</div>')
        out.append('<p class="mini">'+h('; '.join(f'{a["neutral"]} = {a["alias"]}' for a in e['actors']))+'</p>')
        out.append(json_detail('Author key: role and owned option (not reviewer material)',e['actors']))
        if e['old_window_id']:out.append(f'<p class="mini">Expanded stimulus; linked old window {h(e["old_window_id"])}. No ratings transfer.</p>')
    else:out.append('<p class="mini">'+h(e['identity_note'])+'</p>')
    out.append(json_detail('Public task catalog and dependency rules',e['catalog']))
    initial=e['source_bank'].get('0')
    if initial:out.append('<details class="evidence"><summary>Prior assistant suggestion #0 — not a user decision</summary>'+quote(initial['text'])+loc(initial.get('locator'))+'</details>')
    out.append('<details class="trace"><summary>Open complete chronological transcript</summary>')
    actions={t['action']['opportunity']:t for t in e['turns'] if t['action']}
    for t in e['turns']:
        a=t['action'];routine=t['event_kind']=='filler' and not a and t['turn']!=16
        out.append(f'<details class="turn" id="{h(eid)}-t{t["turn"]}"'+('' if routine else ' open')+f'><summary>Turn {t["turn"]} · '+('background discussion' if routine else 'recorded interaction')+'</summary>')
        out.append(f'<div class="speaker">Scripted user · source #{t["user"]["index"]}</div>'+quote(t['user']['text'])+loc(t['user'].get('locator')))
        if a:
            out.append(f'<div class="action"><b>Opportunity {a["opportunity"]} · {h(a["neutral_speaker"])} · {h(a["kind"])}</b><div class="mini">'+('Reserved communication slot' if a['communication_slot'] else 'Unrestricted opportunity')+f' · applied={a["applied"]} · target={h(a.get("target"))} · slot={h(a["slot"])} · value={h(a["value"])} · cited source #{h(a["source"])}</div>')
            if a.get('rejected_reason'):out.append('<p class="missing">Rejected: '+h(a['rejected_reason'])+'</p>')
            out.append('<div class="speaker">Actual logged claim · not invented dialogue</div>'+quote(a['claim'],'component')+loc(a.get('claim_locator')))
            if a['truncated']:out.append('<div class="warning mini">The generated claim exceeded the 240-character delivery limit. Only the claim above was applied/delivered.</div>'+json_detail('Full generated claim — suffix was not delivered',a['generated_claim'])+loc(a.get('generated_claim_locator')))
            message=next((m for m in e['messages'] if m['turn']==t['turn']),None)
            if message:
                if message['recipient_type']=='answerer':status='Answerer route: note visible in this turn’s supplied memory.' if message['visible'] else 'Answerer route: note not observed.'
                elif message['visible'] is True:status='Delivered; verified in the recipient’s actual next observation.'
                elif message['visible'] is None:status='Delivered, but no later recipient observation is available. This does not establish ignoring.'
                else:status='Not observed / not delivered; inspect routing record.'
                out.append(f'<p class="mini"><b>Message chain:</b> {h(status)}</p>')
                for key,label in [('previous_recipient_opportunity','Recipient before message'),('next_recipient_opportunity','Recipient next opportunity')]:
                    op=message[key]
                    out.append(f'<div class="mini">{label}: '+(f'<a href="#{h(eid)}-t{actions[op]["turn"]}">opportunity {op}, turn {actions[op]["turn"]}</a>' if op in actions else 'not recorded / not a component route')+'</div>')
            out.append(memory_delta(a))
            out.append('<details class="evidence"><summary>What this component actually observed</summary><div class="linkrow">Visible immutable sources: '+source_links(eid,a['observation']['sources'])+'</div>'+json_detail('Exact incoming inbox (cleared after observation)',a['observation'].get('inbox',[]))+json_detail('Recorded private action/outcome history — not hidden reasoning',a['observation'].get('own_history',[]))+loc(a.get('observation_locator'))+'</details></div>')
        out.append('<div class="answer"><div class="speaker">Answerer · recorded structured plan</div>'+plan_table(t['defender']['parsed'],e['catalog'])+json_detail('Exact generated answer and remembered state',{'raw':t['defender']['raw'],'parsed':t['defender']['parsed']})+loc(t['defender'].get('locator'))+'</div>')
        out.append('<details class="evidence"><summary>Answerer’s actual input evidence and memory</summary><div class="linkrow">'+source_links(eid,t['defender_observation']['sources'])+'</div>'+json_detail('Supplied memory',t['defender_observation']['memory'])+json_detail('Memory after answerer update',t['memory_after_answer'])+loc(t.get('defender_observation_locator'))+'</details>')
        out.append('<details class="analyst"><summary>Analyst-only current authorized state · never a policy input</summary><pre>'+pretty(t['analyst_only_target'])+'</pre>'+loc(t.get('target_locator'))+'</details></details>')
    out.append('</details><details class="evidence"><summary>Complete immutable source index for this episode</summary>')
    for index,source in sorted(e['source_bank'].items(),key=lambda kv:int(kv[0])):
        out.append(f'<div class="source" id="{h(eid)}-source-{index}"><b>Source #{index} · {h(source["author"])}</b>'+quote(source['text'])+loc(source.get('locator'))+'</div>')
    out.append('</details></article>');return ''.join(out)

def reading_html(reading,episodes,compact=False):
    out=['<div class="interpretation"><p class="eyebrow">AI-assisted interpretation · unvalidated · author review</p>']
    for p in reading['interpretation'].split('\n\n'):out.append('<p>'+h(p)+'</p>')
    out.append('<div class="boundary"><div><b>Strongest supported observation</b><p>'+h(reading['strongest_supported'])+'</p></div><div><b>Not established</b><p>'+h(reading['not_established'])+'</p></div></div><p class="mini"><b>Alternative reading:</b> '+h(reading['alternative'])+'</p>')
    out.append('<div class="matched">')
    for condition in ['C3','C5','A1']:
        spans=[s for s in reading['statements'] if episodes[s['episode_id']]['condition']==condition]
        span=spans[0];q=span['quote']
        truncated=episodes[span['episode_id']]['turns'][span['turn']-1]['action']['truncated']
        limit_note='<p class="mini">Logged text ends at the 240-character delivery limit; the generated suffix was not delivered.</p>' if truncated else ''
        out.append('<div class="excerpt"><b>'+condition+' · turn '+str(span['turn'])+'</b>'+quote(q['text'],'component')+limit_note+f'<a href="#{h(span["episode_id"])}-t{span["turn"]}">Full chronological context</a>'+loc(q['locator'])+'</div>')
    out.append('</div>')
    if not compact:
        out.append('<details class="evidence"><summary>All selected statement readings and source evidence</summary>')
        for s in reading['statements']:
            q=s['quote'];out.append('<div class="source"><b>'+h(q['condition'])+' · turn '+str(s['turn'])+'</b>'+quote(q['text'],'component')+'<p>'+h('; '.join(s['labels']))+'</p><p>'+h(s['note'])+'</p><p class="mini">'+h(s['uncertainty'])+'</p>'+loc(q['locator']))
            if episodes[s['episode_id']]['turns'][s['turn']-1]['action']['truncated']:
                out.append('<p class="mini">This is the complete logged prefix at the delivery limit; the generated suffix was not delivered.</p>')
            out.append(f'<div class="mini">Typed value current={s["typed_value_current"]}; cited source visible now={s["cited_source_visible_now"]}; mechanical reference category={h(s["mechanical_reference_class"])}. These are distinct from semantic support.</div>')
            for evidence in s['supporting_source_context']:
                m=evidence['source'];out.append('<details class="evidence"><summary>Source #'+str(m['index'])+' '+h(m['author'])+' · visible now='+str(evidence['visible_to_actor_now'])+'</summary>'+quote(m['text'])+loc(m.get('locator'))+'</details>')
            out.append('</div>')
        out.append('</details><details class="evidence"><summary>Peer message, prior position and next action — provisional readings</summary>')
        for p in reading['peer_readings']:
            e=episodes[p['episode_id']];out.append('<div class="source"><b>'+e['condition']+' · message turn '+str(p['message_turn'])+'</b>'+quote(p['message_quote']['text'],'component')+f'<p class="mini">Delivered={p["delivered"]}; actually visible={p["visible"]}.</p>')
            for label,key in [('Recipient before','before'),('Recipient after','after')]:
                x=p[key]
                if x:out.append('<b>'+label+' · turn '+str(x['turn'])+'</b>'+quote(x['action']['claim'],'component')+f'<a href="#{h(e["episode_id"])}-t{x["turn"]}">Exact observation and following plan</a>')
                else:out.append('<p class="missing">'+label+': no recorded eligible opportunity.</p>')
            out.append('<p><b>'+h(p['response'])+'</b>: '+h(p['note'])+'</p></div>')
        out.append('</details>')
    out.append('</div>');return ''.join(out)

def document(title,body,script=True):
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; script-src \'unsafe-inline\'; img-src data:; font-src \'none\'; connect-src \'none\'"><title>'+h(title)+'</title><style>'+CSS+'</style></head><body><main>'+body+'</main>'+('<script>'+JS+'</script>' if script else '')+'</body></html>'

def make_markdown(episodes,readings,cases):
    short=['# Matched cases: completed AI-assisted readings','',
        'All 16 matched triplet readings are provisional AI assistance, not human annotations. Twelve anchor triplets plus four linked opposite worlds cover 11 unique families. No semantic prevalence is inferred.','']
    complete=['# Dialogue atlas — accessible full text','',
        'Author version. Source quotations are exact; actor aliases are original neutral names. JSON plans and actions are not invented speech. Analyst truth is separate. See MATCHED_CASES.md for comparative readings.','']
    for r in readings:
        short += [f'## {r["case_id"]} / {r["world"]}: {r["title"]}','',r['interpretation'],'',
                  '**Supported:** '+r['strongest_supported'],'','**Not established:** '+r['not_established'],'','**Alternative:** '+r['alternative'],'']
        for s in r['statements']:
            q=s['quote'];l=q['locator'];short += [f'**{q["condition"]}, turn {s["turn"]}:**','', '> '+q['text'],'',
                f'Exact source: `{l["file"]}`, decompressed record {l["record"]}, `claim`, SHA256 `{l["sha256"]}`.',
                'Provisional labels: '+', '.join(s['labels'])+'. '+s['note'],'',
                f'[Full trace](DIALOGUE_ATLAS.html#{s["episode_id"]}-t{s["turn"]})','']
            if episodes[s['episode_id']]['turns'][s['turn']-1]['action']['truncated']:
                short += ['Logged text ends at the 240-character delivery limit; no generated suffix was delivered.','']
    for e in episodes.values():
        if not e['available']:continue
        complete += [f'## {e["episode_id"]}: {e["condition"]}, seed {e["seed"]}, {e["family_id"]}, {e["world"]}','',
                     'Public catalog: '+json.dumps(e['catalog'],ensure_ascii=False),'']
        for t in e['turns']:
            complete += [f'### Turn {t["turn"]}','',f'**Scripted user #{t["user"]["index"]}:**','', '> '+t['user']['text'],'']
            a=t['action']
            if a:
                complete += [f'**{a["neutral_speaker"]} ({a["actor"]}), opportunity {a["opportunity"]}: {a["kind"]}**',
                    '',f'Action: slot={a["slot"]}, value={a["value"]}, target={a["target"]}, cited source={a["source"]}, applied={a["applied"]}.','',
                    '> '+a['claim'],'', 'Locator: '+json.dumps(a['claim_locator'],ensure_ascii=False),'',
                    'Visible sources: '+str([m['index'] for m in a['observation']['sources']]),
                    'Actual inbox: '+json.dumps(a['observation']['inbox'],ensure_ascii=False),
                    'Private recorded history: '+json.dumps(a['observation']['own_history'],ensure_ascii=False),
                    'Memory before: '+json.dumps(a['memory_before'],ensure_ascii=False),
                    'Memory after action: '+json.dumps(a['memory_before_answer'],ensure_ascii=False),'']
                message=next((m for m in e['messages'] if m['turn']==t['turn']),None)
                if message:complete += ['**Observed message chain:** '+json.dumps(message,ensure_ascii=False),'']
                if a['truncated']:complete += ['**Full generated claim (not all delivered):** '+a['generated_claim'],'']
            complete += ['**Recorded answer — structured, not spoken dialogue:**','', '```json',t['defender']['raw'],'```','',
                         'Answer locator: '+json.dumps(t['defender']['locator']),
                         '**Analyst-only current authorized target, never policy input:** '+json.dumps(t['analyst_only_target']), '']
        complete += ['### Exact source index','']
        for i,m in sorted(e['source_bank'].items(),key=lambda kv:int(kv[0])):
            complete += [f'**Source #{i}, {m["author"]}:**','', '> '+m['text'],'','Locator: '+json.dumps(m['locator']),'']
    (HERE/'MATCHED_CASES.md').write_text('\n'.join(short));(HERE/'DIALOGUE_ATLAS.md').write_text('\n'.join(complete))

def run():
    episodes={e['episode_id']:e for e in read(CACHE/'episodes.json')};readings=read(HERE/'AI_READINGS.json');cases=read(HERE/'SELECTION.json')['cases']
    body='<p class="eyebrow">Dialogue interpretation 005 · offline author atlas</p><h1>Persistent motives, visible behavior</h1><p class="lede">What components pursue, what their statements assert, and what happens after another component speaks.</p>'
    body+='<p>48 recorded episodes · 12 anchor triplets + 4 opposite-world triplets · 11 unique synthetic scenario families · three generator seeds. Frozen shared Qwen weights; no fresh model calls.</p><div class="warning">Author view: includes condition identities, provisional AI readings and separately labeled evaluator truth. These are synthetic scripted conversations, not live human interactions. Human semantic ratings are pending.</div>'
    body+='<div class="axes"><div class="axis"><strong>Pursuit</strong>Which option is advanced? Does it remain, switch or return?</div><div class="axis"><strong>Expression</strong>What does the text claim? A tool label alone cannot answer this.</div><div class="axis"><strong>Responsiveness</strong>What follows delivered evidence? Continuation is not necessarily influence.</div></div>'
    body+='<h2 style="margin-top:32px">Known quantitative context</h2><table><thead><tr><th>Common-base round-zero</th><th>C3 generic</th><th>C5 biographies + motives</th><th>A1 motives only</th></tr></thead><tbody><tr><td>Direct edits / all opportunities</td><td>50.07%</td><td>4.42%</td><td>8.69%</td></tr><tr><td>Recollection actions / all opportunities</td><td>7.67%</td><td>42.76%</td><td>12.94%</td></tr><tr><td>Consecutive direct-action typed goals</td><td>67.09%</td><td>92.48%</td><td>94.95%</td></tr></tbody></table><p class="mini">150 paired families, three generator seeds; 10,800 opportunities per condition. Repetition uses consecutive direct actions within each actor; intervening peer messages do not create a new direct-action pair boundary. Denominators are actor-local eligible pairs. These reproduce behavior004; they are not new semantic ratings. C5−C3 edit difference −45.66 percentage points, pointwise family/seed 95% interval [−48.20, −43.06]. C5 task performance remains below C3 at all three completed Qwen training seeds; descriptor breadth advantage was not established.</p>'
    body+='<h2>Matched cases</h2><ol class="toc">'
    for c in cases:
        r=next(r for r in readings if r['case_id']==c['case_id'] and r['world']==c['anchor_world'])
        body+=f'<li><a href="#{c["case_id"]}">{h(r["title"])}</a><br><small>{c["case_id"]}'+(' · preselected main-paper case' if c['main_paper_theme'] else '')+'</small></li>'
    body+='</ol>'
    for c in cases:
        anchor=next(r for r in readings if r['case_id']==c['case_id'] and r['world']==c['anchor_world'])
        body+=f'<section class="case" id="{c["case_id"]}"><div class="case-header"><div><p class="eyebrow">{c["case_id"]} · {h(c["family_id"])} · seed {c["seed"]}</p><h2>{h(anchor["title"])}</h2></div><a href="#">Back to overview</a></div>'
        if c['main_paper_theme']:body+='<p class="mini">Preassigned paper theme: '+h(c['main_paper_theme'])+'. This theme does not guarantee the phenomenon is present.</p>'
        worlds=[c['anchor_world']]+(['hypothetical' if c['anchor_world']=='authorized' else 'authorized'] if c['opposite_world_included'] else [])
        body+='<div class="world-controls" aria-label="Paired world selection">'+''.join(f'<button data-world-button="{w}" aria-pressed="{str(i==0).lower()}">{h(w.title())}'+(' · anchor' if i==0 else ' · linked opposite world')+'</button>' for i,w in enumerate(worlds))+'</div>'
        for w in worlds:
            r=next(r for r in readings if r['case_id']==c['case_id'] and r['world']==w)
            body+=f'<div data-world="{w}" id="{c["case_id"]}-{w}"><h3>{h(r["title"])}</h3>'+reading_html(r,episodes)+'<h3>Matched full traces</h3><div class="matched">'
            for condition in ['C3','C5','A1']:
                e=next(e for e in episodes.values() if e['case_id']==c['case_id'] and e['world']==w and e['condition']==condition)
                body+=episode_html(e)
            body+='</div></div>'
        body+='</section>'
    body+='<div class="footer">No network resources or external services. Every quotation identifies an exact record and file hash; the local evidence bundle contains the recorded inputs. Original packets are unchanged. AI interpretation is provisional and supplies no human agreement scores.</div>'
    (HERE/'DIALOGUE_ATLAS.html').write_text(document('Persistent motives — dialogue atlas',body))
    make_markdown(episodes,readings,cases)
    reviewer=CACHE/'human_review/reviewer';private=CACHE/'human_review/private';reviewer.mkdir(parents=True,exist_ok=True);private.mkdir(exist_ok=True)
    safe=review_order([reviewer_episode(e) for e in episodes.values() if e['available'] and e['anchor']])
    write(reviewer/'items.json',safe)
    key=[{'item_id':e['episode_id'],'condition':e['condition'],'seed':e['seed'],'family_id':e['family_id'],'world':e['world'],
          'old_window_id':e['old_window_id'],'case_id':e['case_id'],'identity_substitutions':substitutions(e)} for e in episodes.values() if e['anchor']]
    write(private/'mapping.json',key)
    rubric=(HERE/'SEMANTIC_CODEBOOK.md').read_text();(reviewer/'CODEBOOK.md').write_text(rubric)
    reviewbody='<p class="eyebrow">Independent behavioral review · first batch</p><h1>Claims, evidence and response</h1><p>36 full episodes. Read each independently. Identify what is asserted and what evidence supports the reading; do not rank systems. The two forms are blank. Use the accompanying codebook and preserve item IDs.</p><p class="warning">Speaker aliases are substituted consistently. Cast structure and style may still reveal a condition. Analyst-only current truth is labeled separately. No AI interpretations or condition keys are included.</p><ol class="toc">'+''.join(f'<li><a href="#{e["item_id"]}">{e["item_id"]}</a></li>' for e in safe)+'</ol>'
    reviewbody+=''.join('<section class="case">'+episode_html(e,True)+'</section>' for e in safe)
    (reviewer/'REVIEW.html').write_text(document('Independent dialogue review',reviewbody))
    fields=['item_id','status','episode_labels','confidence','statement_annotations_json','peer_annotations_json','notes']
    for rater in [1,2]:
        path=reviewer/f'rater_{rater}.csv'
        if path.exists():
            rows=list(csv.DictReader(path.open()))
            if [r['item_id'] for r in rows]!=[e['item_id'] for e in safe]:raise ValueError('Would change existing rating identities')
        else:csv_write(path,[dict.fromkeys(fields,'')|{'item_id':e['item_id']} for e in safe],fields)
    # The printable casebook contains only the six preselected anchor cases.
    casebody='<p class="eyebrow">Author-review casebook · AI-assisted readings</p><h1>Persistent motives in recorded dialogues</h1><p>Six cases selected by a frozen hash rule before their new interpretation. Full author atlas and source bundle provide every turn. No human ratings or causal message effects are asserted. Structured outputs remain plans, not invented speech.</p>'
    for c in cases:
        if not c['main_paper_theme']:continue
        r=next(r for r in readings if r['case_id']==c['case_id'] and r['world']==c['anchor_world'])
        casebody+=f'<section class="casebook-case"><p class="eyebrow">{c["case_id"]} · {h(c["anchor_world"])} · {h(c["family_id"])} · seed {c["seed"]}</p><h2>{h(r["title"])}</h2>'+reading_html(r,episodes,True)+'</section>'
    # PDF sits beside the atlas. Link expanded context to that separate document.
    casebody=re.sub(r'href="#(D5E-[^"]+)"', r'href="DIALOGUE_ATLAS.html#\1"', casebody)
    print_style='<style>@media print{body{font-size:9.5pt;line-height:1.3}h1{font-size:21pt;margin:8px 0}h2{font-size:15pt;margin:8px 0}.interpretation{padding:0}.interpretation p{margin:7px 0}.boundary{display:grid;grid-template-columns:1fr 1fr;gap:10px}.boundary>div{padding:8px}.excerpt{margin:8px 0}.speech{padding:5px 9px;margin:6px 0}.eyebrow,.mini{font-size:8pt}.locator{font-size:7pt}}</style>'
    (HERE/'CASEBOOK.html').write_text(document('Dialogue casebook',print_style+casebody,False))
    effort=[]
    for e in safe:
        visible=' '.join(t['user']['text']+' '+(t['action']['claim'] if t['action'] else '')+' '+json.dumps(t['defender']['parsed']) for t in e['turns'])
        base=len(re.findall(r'\w+',visible));expanded=len(re.findall(r'\w+',json.dumps(e,ensure_ascii=False)))
        effort.append({'item_id':e['item_id'],'core_word_units':base,'expanded_word_units':expanded,'core_minutes_at_200_plus4':base/200+4,'core_plus_targeted_checks_minutes':base/200+7,'fully_expanded_minutes_at_200_plus4':expanded/200+4})
    csv_write(REPORTS/'REVIEW_EFFORT.csv',effort)
    write(REPORTS/'REVIEW_STATUS.json',{'items':len(safe),'ratings':'pending','forms_blank':all(not any(v for k,v in r.items() if k!='item_id') for n in [1,2] for r in csv.DictReader((reviewer/f'rater_{n}.csv').open())),
        'reviewer_path':relative(reviewer),'private_key_path':relative(private/'mapping.json'),
        'estimated_hours_per_rater_core':sum(x['core_minutes_at_200_plus4'] for x in effort)/60,
        'estimated_hours_per_rater_with_targeted_checks':sum(x['core_plus_targeted_checks_minutes'] for x in effort)/60,
        'estimated_hours_per_rater_fully_expanded':sum(x['fully_expanded_minutes_at_200_plus4'] for x in effort)/60,
        'assumption':'200 word-units/minute plus4 coding minutes/item, or plus7 including targeted source/history checks. Fully expanded JSON counts repeat evidence and are a worst-case inventory, not expected workload. Planning estimates, not measured rater times.',
        'source_of_stimuli':'36 full anchor episodes; expanded context gets new IDs; old ratings never transferred',
        'reviewer_file_hashes':{p.name:digest(p) for p in reviewer.iterdir() if p.is_file()},'private_key_sha256':digest(private/'mapping.json')})
    write(REPORTS/'RENDERING_PROVENANCE.json',{'rendered_utc':now(),'episodes_sha256':digest(CACHE/'episodes.json'),'readings_sha256':digest(HERE/'AI_READINGS.json'),
        'outputs':{n:digest(HERE/n) for n in ['DIALOGUE_ATLAS.html','DIALOGUE_ATLAS.md','MATCHED_CASES.md']},
        'casebook_html':relative(HERE/'CASEBOOK.html'),'casebook_html_sha256':digest(HERE/'CASEBOOK.html'),'no_external_resources':True})
    print({'atlas_bytes':(HERE/'DIALOGUE_ATLAS.html').stat().st_size,'reviewer_bytes':(reviewer/'REVIEW.html').stat().st_size,'review_items':len(safe)})

if __name__=='__main__':run()
