"""Accessible presentation only; item JSON and human forms are never rewritten."""
import html
from .common import *

def run():
    status=read(REPORTS/'SEMANTIC_REVIEW_STATUS.json');reviewer=ROOT/status['reviewer_directory'];items=read(reviewer/'items.json')
    old=read(ROOT/'supplements/exploration_003/reports/HUMAN_REVIEW_V2_MANIFEST.json')
    old_paths={str((ROOT/old['reviewer_directory']/name).relative_to(ROOT)):sha256(ROOT/old['reviewer_directory']/name) for name in old['files']}
    for name,digest in old['files'].items():
        if sha256(ROOT/old['reviewer_directory']/name)!=digest:raise ValueError('Prior v2 packet changed')
    fragments=['<!doctype html><meta charset="utf-8"><title>Behavioral interpretation review</title>',
        '<style>body{font:16px system-ui;max-width:1000px;margin:2rem auto;padding:1rem}article{border-top:3px solid #555;margin-top:3rem}section{border-left:3px solid #ddd;padding:1rem;margin:1rem 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f6f6f6;padding:1rem}summary{cursor:pointer}h1,h2,h3{line-height:1.2}</style>',
        '<h1>Behavioral interpretation review</h1><p>Use RUBRIC.md and your independent blank CSV form. No method ranking is requested. Item identities and source context are preserved. Open details as needed; truth is offline reviewer material.</p>']
    for item in items:
        fragments.append('<article><h2>'+item['item_id']+'</h2><details><summary>Catalog</summary><pre>'+html.escape(json.dumps(item['catalog'],indent=2))+'</pre></details>')
        for w in item['window']:
            a=w['action'];fragments.append(f"<section><h3>Turn {w['turn']} · {html.escape(w['speaker'])}</h3><p>"+html.escape(str(a['kind'])+' · '+str(a['slot'])+' = '+str(a['value']))+'</p><blockquote>'+html.escape(str(a['claim']))+'</blockquote>')
            reference=next((s for s in w['visible_sources'] if s['index']==a['source']),None)
            fragments.append('<p>Referenced source: '+html.escape(json.dumps(reference,ensure_ascii=False) if reference else 'Not present in this observation')+'</p>')
            for label,key in [('Actual received messages','received_messages'),('Current truth for review only','time_indexed_truth_for_review_only'),('Following answer','following_answer'),('Full recorded context','all')]:
                content=w if key=='all' else w[key]
                fragments.append('<details><summary>'+label+'</summary><pre>'+html.escape(json.dumps(content,indent=2,ensure_ascii=False))+'</pre></details>')
            fragments.append('</section>')
        fragments.append('</article>')
    destination=reviewer/'PACKET.html';destination.write_text('\n'.join(fragments)+'\n')
    readings=read(HERE/'AI_ASSISTED_READINGS.json');mapping=read(ROOT/status['private_mapping']);selected={r['item_id'] for r in mapping if r['ai_reading_selected']}
    if {r['item_id'] for r in readings['items']}!=selected:raise ValueError('AI readings depart from frozen deterministic subset')
    text=['# AI-assisted illustrative readings','',readings['classification']+'.', '',readings['selection'],'']
    for item in readings['items']:
        text+=['## '+item['item_id'],'',item['reading'],'','Evidence: '+item['support'],'','Limits: '+item['limits'],'']
    (HERE/'AI_ASSISTED_READINGS.md').write_text('\n'.join(text))
    write(REPORTS/'REVIEW_PRESENTATION_PROVENANCE.json',{'prior_v2_files_preserved':old_paths,'new_html_sha256':sha256(destination),
        'items_sha256':sha256(reviewer/'items.json'),'forms':{f'rater_{n}.csv':sha256(reviewer/f'rater_{n}.csv') for n in (1,2)},
        'ai_readings_sha256':sha256(HERE/'AI_ASSISTED_READINGS.json'),'selected_ai_items':sorted(selected),
        'reviewer_delivery_directory':str(reviewer.relative_to(ROOT)),'human_ratings_pending':True,'no_model_judge_calls':True})

if __name__=='__main__':run()
