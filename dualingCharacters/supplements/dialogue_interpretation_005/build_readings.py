"""Attach exact evidence to the explicitly authored AI-assisted interpretation file."""
from .common import *
from .annotations import validate,resolve_span
from .readings_data import READINGS as FIRST
from .readings_middle import READINGS as MIDDLE
from .readings_final import READINGS as FINAL
from .freeze import verify

def run():
    verify();episodes={e['episode_id']:e for e in read(CACHE/'episodes.json')};output=[]
    choices=read(HERE/'SELECTION.json')['cases']
    for authored in FIRST+MIDDLE+FINAL:
        case_id='DI5-'+authored['case'];world=authored['world']
        group={e['condition']:e for e in episodes.values() if e['case_id']==case_id and e['world']==world}
        item={'case_id':case_id,'world':world,'title':authored['title'],'interpretation':authored['text'],
              'strongest_supported':authored['supported'],'not_established':authored['not_established'],
              'alternative':authored['alternative'],'status':'AI-assisted, unvalidated; not human annotation',
              'main_paper_theme':next(c['main_paper_theme'] for c in choices if c['case_id']==case_id),
              'statements':[],'peer_readings':[]}
        for condition,turn,labels,note in authored['statements']:
            episode=group[condition];t=episode['turns'][turn-1];action=t['action'];f=next(a for a in episode['features'] if a['turn']==turn)
            supporting_indices=sorted(set(i for i in [action['source']]+t['analyst_only_target']['evidence'] if i is not None))
            sources=[{'source':episode['source_bank'][str(i)],'visible_to_actor_now':i in [m['index'] for m in action['observation']['sources']]} for i in supporting_indices if str(i) in episode['source_bank']]
            item['statements'].append({'episode_id':episode['episode_id'],'turn':turn,'kind':'claim','labels':labels,
                'note':note,'uncertainty':'Provisional semantic reading; inspect exact span and separate authority, truth and citation.',
                'typed_value_current':f['value_current'],'mechanical_reference_class':f['reference_class'],
                'cited_source_visible_now':f['reference_available'],'supporting_source_context':sources,
                'quote':resolve_span(episodes,{'episode_id':episode['episode_id'],'turn':turn})})
        for condition,message_turn,response,note in authored['peers']:
            episode=group[condition];message=next(m for m in episode['messages'] if m['turn']==message_turn)
            a=episode['turns'][message_turn-1]['action']
            def context(op):
                if op is None:return None
                t=next(t for t in episode['turns'] if t['action'] and t['action']['opportunity']==op)
                return {'turn':t['turn'],'action':t['action'],'following_answer':t['defender']['parsed']}
            item['peer_readings'].append({'episode_id':episode['episode_id'],'message_turn':message_turn,
                'response':response,'note':note,'previous_opportunity':message['previous_recipient_opportunity'],
                'next_opportunity':message['next_recipient_opportunity'],'delivered':message['delivered'],'visible':message['visible'],
                'message_quote':resolve_span(episodes,{'episode_id':episode['episode_id'],'turn':message_turn}),
                'before':context(message['previous_recipient_opportunity']),'after':context(message['next_recipient_opportunity'])})
        output.append(item)
    validate(output,episodes)
    write(HERE/'AI_READINGS.json',output)
    write(REPORTS/'AI_READING_PROVENANCE.json',{'written_utc':now(),'status':'AI-assisted author interpretation; no independent ratings',
        'triplet_readings':len(output),'selected_statement_spans':sum(len(r['statements']) for r in output),
        'selected_peer_exchanges':sum(len(r['peer_readings']) for r in output),
        'word_counts':{r['case_id']+'/'+r['world']:len(r['interpretation'].split()) for r in output},
        'episodes_sha256':digest(CACHE/'episodes.json'),'readings_sha256':digest(HERE/'AI_READINGS.json'),
        'authored_sources':{n:digest(HERE/n) for n in ['readings_data.py','readings_middle.py','readings_final.py']},
        'semantic_prevalence':'Not estimated; exact selected-span denominators do not represent all actions.',
        'new_model_judge_calls':0,'human_ratings':0})
    print({r['case_id']+'/'+r['world']:len(r['interpretation'].split()) for r in output})

if __name__=='__main__':run()
