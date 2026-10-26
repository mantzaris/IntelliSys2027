"""Compact publication tables; separate mechanical facts from provisional readings."""
from collections import Counter, defaultdict
from .common import *

def run():
    episodes={e['episode_id']:e for e in read(CACHE/'episodes.json')}
    readings=read(HERE/'AI_READINGS.json');rows=[]
    for r in readings:
        for s in r['statements']:
            e=episodes[s['episode_id']];a=e['turns'][s['turn']-1]['action'];l=s['quote']['locator']
            rows.append({'case_id':r['case_id'],'episode_id':e['episode_id'],'world':r['world'],'anchor':e['anchor'],
                'condition':e['condition'],'seed':e['seed'],'turn':s['turn'],'api':a['kind'],'exact_statement':a['claim'],
                'ai_assisted_labels':'; '.join(s['labels']),'interpretation':s['note'],'uncertainty':s['uncertainty'],
                'typed_value_current':s['typed_value_current'],'reference_visible':s['cited_source_visible_now'],
                'mechanical_reference_class':s['mechanical_reference_class'],'raw_file':l['file'],'raw_sha256':l['sha256'],'raw_record':l['record']})
    csv_write(HERE/'tables/API_VERSUS_STATEMENT.csv',rows)
    context=ROOT/'supplements/behavior_characterization_004/reports/secondary_defender_results.csv'
    original=list(csv.DictReader(context.open()))
    csv_write(HERE/'tables/PRIOR_DEFENDER_CONTEXT.csv',[r for r in original if r.get('model')=='qwen' and r.get('condition') in {'base','C1','C3','C5','A1'}])
    breadth=ROOT/'supplements/exploration_003/reports/primary_paired_contrasts.json'
    write(HERE/'tables/PRIOR_EXPLORATION_CONTEXT.json',read(breadth))
    exposures=list(csv.DictReader((HERE/'tables/IMPLEMENTATION_EXPOSURES.csv').open()))
    totals=defaultdict(Counter)
    for r in exposures:
        for name in ['allocated_opportunities','reserved_slots','applied','truncated_claims','peer_sent','peer_delivered','peer_observed','no_later_observation','source_unavailable','state_changes','note_changes']:
            totals[r['condition'],r['anchor']][name]+=int(r[name])
    csv_write(HERE/'tables/EXPOSURE_TOTALS.csv',[{'condition':c,'anchor':a,**v} for (c,a),v in sorted(totals.items())])
    peer=[];schedule=[]
    for e in episodes.values():
        if not e['available']:continue
        for m in e['messages']:
            peer.append({'episode_id':e['episode_id'],'condition':e['condition'],'anchor':e['anchor'],
                         **{k:m[k] for k in ['turn','ordinal','recipient_type','delivered','visible','visibility_status','previous_recipient_opportunity','next_recipient_opportunity','previous_response','next_response']}})
        for t in e['turns']:
            a=t['action']
            if a:schedule.append({'episode_id':e['episode_id'],'condition':e['condition'],'anchor':e['anchor'],'turn':t['turn'],
                'opportunity':a['opportunity'],'speaker':a['neutral_speaker'],'reserved':a['communication_slot'],
                'history_entries':len(a['observation']['own_history']),'inbox_entries':len(a['observation']['inbox']),
                'event_kind':t['event_kind'],'cited_reference':a['source'],'notes_changed':a['memory_before']['notes']!=a['memory_before_answer']['notes']})
    csv_write(HERE/'tables/PEER_CHAIN.csv',peer);csv_write(HERE/'tables/SCHEDULE_AND_EXPOSURE.csv',schedule)
    write(REPORTS/'PUBLICATION_INPUTS.json',{'created_utc':now(),'selected_statement_spans':len(rows),
        'anchor_statement_spans':sum(r['anchor'] for r in rows),'total_anchor_actions':432,'total_selected_actions':576,
        'semantic_frequencies':'Not estimated; quoted spans are purposive within a fixed episode sample. Unselected actions are not rated negatives.',
        'human_ratings':0,'context_sources':{relative(p):digest(p) for p in [context,breadth]},
        'outputs':{p.name:digest(p) for p in (HERE/'tables').iterdir() if p.is_file()}})
    print({'selected_statement_rows':len(rows),'peer_chains':len(peer),'schedule_rows':len(schedule)})

if __name__=='__main__':run()
