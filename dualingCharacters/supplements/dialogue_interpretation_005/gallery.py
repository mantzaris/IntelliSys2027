"""Purposive diagnostic illustrations from the locked episodes, never prevalence."""
from collections import defaultdict
import re
from .common import *
from .annotations import resolve_span

EXPLANATIONS = {
 'source loss, unchanged wording': 'The claim is identical to this actor’s preceding statement, while its cited source leaves the immediate retrieved list. A reference-availability descriptor changes; the words and expressed position do not. Prior history can still contain the earlier action, so unavailable-now is not never-seen.',
 'correct typed value, inappropriate citation': 'The mechanical flag is triggered because source1 is unavailable in this immediate observation. Its original text actually does authorize specialists. This is not a demonstrated false citation: the source existed and supported the value, while retrieval availability changed. The label must not be silently read as semantic falsity.',
 'apparent correction': 'The word “Correcting” introduces a team-base change, not a direct response to a peer. At this turn the user has approved online format but has not yet approved Harbor; that later approval cannot retroactively support the current claim. The lexical filter finds correction language, without establishing a supported correction or interpersonal challenge.',
 'truncated generated claim': 'Only the logged prefix is delivered. The generated continuation contains additional criticism, but attributing a recipient response to that suffix would use evidence the recipient did not receive.',
 'missing recipient follow-up': 'This late message has no later scheduled recipient opportunity in the episode. Delivery is recorded, but acknowledgment or rejection cannot be observed. The missing response is not evidence of ignoring.',
 'typed agreement already present': 'The recipient had already expressed the matching position before this message. A subsequent match therefore need not be adoption of anything new; the pre-message and next actions are available in the full trace.',
 'same statement, recollect versus propose': 'The exact same advocacy appears under both action names. Both APIs append unverified notes in this implementation. The changed API measures a tool-label choice, without establishing a new semantic tactic in this example.',
 'continued other-field pursuit': 'The recipient’s next statement continues its own earlier option while the message concerns another field. The observed output does not substantively answer that message, but this cannot establish absence of an internal effect or general inability to interact.'
}

def run():
    episodes={e['episode_id']:e for e in read(CACHE/'episodes.json')};candidates=defaultdict(list)
    for eid,e in episodes.items():
        previous={}
        for f in e['features']:
            before=previous.get(f['actor']);turn=f['turn'];key={'episode_id':eid,'turn':turn}
            if before and before['claim']==f['claim'] and before['reference_available'] is True and f['reference_available'] is False:
                candidates['source loss, unchanged wording'].append(dict(key,previous_turn=before['turn']))
            if f['current_value_inappropriate_citation']:candidates['correct typed value, inappropriate citation'].append(key)
            if re.search(r'correct|incorrect|misrec|misattribution',f['claim'],re.I):candidates['apparent correction'].append(key)
            if f['claim_truncated']:candidates['truncated generated claim'].append(key)
            if before and before['claim']==f['claim'] and {before['kind'],f['kind']}=={'recollect','propose'}:
                candidates['same statement, recollect versus propose'].append(dict(key,previous_turn=before['turn']))
            previous[f['actor']]=f
        for m in e['messages']:
            key={'episode_id':eid,'turn':m['turn']}
            if m['visibility_status']=='no_later_recipient_observation':candidates['missing recipient follow-up'].append(key)
            if m['previous_response']=='same_goal':candidates['typed agreement already present'].append(key)
    for r in read(HERE/'AI_READINGS.json'):
        for p in r['peer_readings']:
            if p['response']!='continuation of an existing position' or not p['after']:continue
            e=episodes[p['episode_id']];m=next(m for m in e['messages'] if m['turn']==p['message_turn'])
            if m['next_response']=='other_or_untyped':candidates['continued other-field pursuit'].append({'episode_id':p['episode_id'],'turn':p['message_turn'],'provisional_reading':p['note']})
    kinds=['source loss, unchanged wording','correct typed value, inappropriate citation','apparent correction','truncated generated claim',
           'missing recipient follow-up','typed agreement already present','same statement, recollect versus propose','continued other-field pursuit']
    chosen=[]
    for kind in kinds:
        items=candidates[kind]
        if not items:chosen.append({'kind':kind,'status':'No qualifying example in locked selection'});continue
        item=min(items,key=lambda a:rank('dialogue005-gallery-v1',f'{kind}|{a["episode_id"]}|{a["turn"]}'))
        e=episodes[item['episode_id']];a=e['turns'][item['turn']-1]['action'];f=next(f for f in e['features'] if f['turn']==item['turn'])
        chosen.append({'kind':kind,'status':'purposive illustration, not a frequency estimate',**item,'case_id':e['case_id'],'condition':e['condition'],'world':e['world'],
            'quote':resolve_span(episodes,item),'action_api':a['kind'],'typed_value':a['value'],'cited_source':a['source'],
            'source_visible':f['reference_available'],'reference_class':f['reference_class'],'generated_claim':a['generated_claim'],
            'cited_source_text':e['source_bank'].get(str(a['source']),{}).get('text')})
    write(HERE/'DIAGNOSTIC_GALLERY.json',chosen)
    lines=['# Purposive diagnostic gallery','',
        'At most eight selected examples. Filters were declared before new readings; within each filter, lowest SHA256(dialogue005-gallery-v1:filter|episode|turn) selects the illustration. Some entries can overlap. Counts here are not prevalence and no new independent episodes are created.','']
    for item in chosen:
        lines += ['## '+item['kind'],'']
        if 'quote' not in item:lines += [item['status'],''];continue
        q=item['quote'];l=q['locator'];lines += [f'{item["case_id"]}, {item["condition"]}, {item["world"]}, turn {item["turn"]}.','',
            '**AI-assisted interpretation, unvalidated:** '+EXPLANATIONS[item['kind']],'',
            '> '+q['text'],'',f'API={item["action_api"]}; typed value={item["typed_value"]}; cited source={item["cited_source"]}; visible={item["source_visible"]}.',
            '',f'Locator: `{l["file"]}`, record {l["record"]}, `claim`; SHA256 `{l["sha256"]}`.',
            '',f'[Full chronological context](DIALOGUE_ATLAS.html#{item["episode_id"]}-t{item["turn"]})','']
        if item.get('cited_source_text'):lines += ['**Actual cited source (not necessarily available at this turn):**','', '> '+item['cited_source_text'],'']
        if item['generated_claim']!=q['text']:lines += ['**Generated text beyond the delivery limit is not recipient evidence:** '+item['generated_claim'],'']
        if item.get('previous_turn'):lines += ['Compare the same actor at turn '+str(item['previous_turn'])+'.','']
        if item.get('provisional_reading'):lines += ['AI-assisted reading: '+item['provisional_reading'],'']
    (HERE/'DIAGNOSTIC_GALLERY.md').write_text('\n'.join(lines))
    print([{k:r.get(k) for k in ['kind','case_id','condition','turn','status']} for r in chosen])

if __name__=='__main__':run()
