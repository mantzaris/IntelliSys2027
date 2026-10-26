"""Reuse frozen family rates, export a compact sufficient table, check original estimates."""
from collections import defaultdict, Counter
from .common import *
from supplements.behavior_characterization_004.statistics import contrast

METRICS = ('channel_edit','channel_recollect','channel_propose','consecutive_direct_goal_repetition',
           'reference_reference_unavailable','reference_explicit_current_support',
           'visible_typed_next_goal_match','peer_before_goal_match','peer_after_goal_match')

def expand(rows):
    output=[]
    for r in rows:
        for metric in METRICS:
            num=int(r[metric+'_n']);den=int(r[metric+'_d'])
            if num<0 or den<num:raise ValueError('Invalid numerator/denominator')
            output.append({'cohort':'main_round_zero','condition':r['condition'],'seed':int(r['seed']),
                'family_id':r['family_id'],'metric':metric,'numerator':num,'denominator':den,'rate':num/den if den else None})
    keys=[(r['condition'],r['seed'],r['family_id']) for r in rows]
    if len(keys)!=len(set(keys)):raise ValueError('Duplicate family row')
    return output

def run():
    source=ROOT/'artifacts/behavior_characterization_004/family_rates.csv'
    target=HERE/'tables/FAMILY_NUMERATORS.csv'
    if not target.exists():
        records={}
        with source.open() as f:
            for r in csv.DictReader(f):
                if r['cohort']!='main_round_zero' or r['condition'] not in {'C3','C5','A1'} or r['metric'] not in METRICS:continue
                key=(r['condition'],r['seed'],r['family_id']);o=records.setdefault(key,{k:r[k] for k in ['condition','seed','family_id']})
                o[r['metric']+'_n']=int(r['numerator']);o[r['metric']+'_d']=int(r['denominator'])
        csv_write(target,[records[k] for k in sorted(records)])
        write(HERE/'tables/FAMILY_INPUT_PROVENANCE.json',{'source':relative(source),'source_sha256':digest(source),
            'export_sha256':digest(target),'original_population':'behavior004 common-base round-zero; both worlds aggregated inside family',
            'metrics':METRICS,'rows':len(records)})
    rows=list(csv.DictReader(target.open()));expanded=expand(rows)
    expected=read(ROOT/'supplements/behavior_characterization_004/reports/matched_contrasts.json')
    checks=[];results=[]
    for second in ('C3','A1'):
        for metric in METRICS:
            for seeds in ([17],[29],[43],[17,29,43]):
                result=contrast(expanded,seeds,'C5',second,metric,'main_round_zero')
                reference=next(r for r in expected if r['cohort']=='main_round_zero' and r['first']=='C5' and r['second']==second and r['metric']==metric and r['seeds']==seeds)
                for field in ('difference','lower','upper','first_mean','second_mean'):
                    if abs(result[field]-reference[field])>1e-12:raise ValueError('Known estimate failed to reproduce: '+field)
                results.append(result);checks.append(True)
    write(HERE/'tables/REPRODUCED_CONTRASTS.json',results)
    sums=defaultdict(lambda:[0,0])
    for row in expanded:
        key=row['condition'],row['metric'];sums[key][0]+=row['numerator'];sums[key][1]+=row['denominator']
    csv_write(HERE/'tables/KNOWN_BEHAVIOR.csv',[{'condition':c,'metric':m,'numerator':n,'denominator':d,'pooled_rate':n/d if d else None}
        for (c,m),(n,d) in sorted(sums.items())])
    episodes=read(CACHE/'episodes.json');action_rows=[];exposures=[]
    for e in episodes:
        if not e['available']:continue
        for t in e['turns']:
            a=t['action']
            if not a:continue
            action_rows.append({'episode_id':e['episode_id'],'case_id':e['case_id'],'condition':e['condition'],'seed':e['seed'],
                'family_id':e['family_id'],'world':e['world'],'anchor':e['anchor'],'turn':t['turn'],'opportunity':a['opportunity'],
                'speaker':a['neutral_speaker'],'api':a['kind'],'reserved_communication':a['communication_slot'],'applied':a['applied'],
                'truncated':a['truncated'],'input_tokens':a['input_tokens'],'output_tokens':a['output_tokens']})
        features=e['features'];messages=e['messages']
        exposures.append({'episode_id':e['episode_id'],'case_id':e['case_id'],'condition':e['condition'],'anchor':e['anchor'],
            'allocated_opportunities':len(features),'reserved_slots':sum(a['communication_slot'] for a in features),
            'applied':sum(a['applied'] for a in features),'truncated_claims':sum(a['claim_truncated'] for a in features),
            'peer_sent':len(messages),'peer_delivered':sum(m['delivered'] for m in messages),
            'peer_observed':sum(m['visible'] is True for m in messages),'no_later_observation':sum(m['visibility_status']=='no_later_recipient_observation' for m in messages),
            'source_unavailable':sum(a['reference_class']=='reference_unavailable' for a in features),
            'max_own_history':max(a['history_records'] for a in features),
            'state_changes':sum(a['state_changed'] for a in features),'note_changes':sum(a['notes_changed'] for a in features)})
    csv_write(HERE/'tables/SELECTED_ACTIONS.csv',action_rows);csv_write(HERE/'tables/IMPLEMENTATION_EXPOSURES.csv',exposures)
    counts=Counter((r['condition'],r['api']) for r in action_rows if r['anchor'])
    csv_write(HERE/'tables/ANCHOR_API_COUNTS.csv',[{'condition':c,'api':a,'count':n,'allocated_opportunities':144,'anchor_episodes':12}
        for (c,a),n in sorted(counts.items())])
    write(REPORTS/'NUMERICAL_VERIFICATION.json',{'family_rows':len(rows),'matched_original_contrasts':len(checks),
        'interval_method':'Original family/seed two-way or per-seed family bootstrap; both worlds remain within family',
        'semantic_frequency_estimates':'Not produced; annotations are provisional selected-span readings',
        'original_contrast_sha256':digest(ROOT/'supplements/behavior_characterization_004/reports/matched_contrasts.json'),
        'exported_input_sha256':digest(target)})
    print({'family_rows':len(rows),'original_contrasts_reproduced':len(checks),'selected_action_rows':len(action_rows)})

if __name__ == '__main__':run()
