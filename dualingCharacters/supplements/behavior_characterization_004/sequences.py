"""Actor-local runs and fixed event windows, preserving real opportunity gaps."""
from collections import defaultdict
from pcc.environment import make_family
from .records import DIRECT,plan_relation

def direct(action):return action['valid'] and action['kind'] in DIRECT and action['goal'] is not None

def actor_sequences(episode):
    grouped=defaultdict(list)
    for action in episode['actions']:grouped[action['actor']].append(action)
    pairs=[];runs=[];actors=[];losses=[]
    for actor,actions in grouped.items():
        direct_actions=[(i,a) for i,a in enumerate(actions) if direct(a)]
        seen=set();previous_goal=None;returns=0;current_run=[];actor_runs=[]
        for own_index,action in direct_actions:
            goal=tuple(action['goal'])
            if goal!=previous_goal:
                if current_run:actor_runs.append(current_run)
                current_run=[]
                returns+=goal in seen
            current_run.append((own_index,action));seen.add(goal);previous_goal=goal
        if current_run:actor_runs.append(current_run)
        for number,run in enumerate(actor_runs):
            first,last=run[0],run[-1]
            runs.append({'actor':actor,'role':actions[0]['role'],'run_number':number+1,'goal':list(first[1]['goal']),
                'direct_actions':len(run),'own_opportunity_span':last[0]-first[0]+1,
                'conversation_turn_span':last[1]['turn']-first[1]['turn']+1,
                'start_turn':first[1]['turn'],'end_turn':last[1]['turn'],'terminal_censored':number==len(actor_runs)-1})
        own_pairs=list(zip(actions,actions[1:]));strict=sum(direct(a) and direct(b) and a['goal']==b['goal'] for a,b in own_pairs)
        for (i,a),(j,b) in zip(direct_actions,direct_actions[1:]):
            same=a['goal']==b['goal'];relation=plan_relation(b['latest_observed_plan'],a['goal'])
            pairs.append({'actor':actor,'role':a['role'],'previous_turn':a['turn'],'turn':b['turn'],
                'conversation_gap':b['turn']-a['turn'],'own_opportunity_gap':j-i,'same_goal':same,
                'channel_changed':a['kind']!=b['kind'],'same_claim':a['normalized_claim']==b['normalized_claim'],
                'same_reference':a['source']==b['source'],'reference_class_changed':a['reference_class']!=b['reference_class'],
                'source_available_changed':a['reference_available']!=b['reference_available'],
                'observed_defender_relation_to_previous_goal':relation,
                'continued_after_observed_other_value':same if relation=='different' else None})
        for a,b in own_pairs:
            if a['source'] is not None and a['source']==b['source'] and a['reference_available'] is True and b['reference_available'] is False:
                losses.append({'actor':actor,'role':a['role'],'previous_turn':a['turn'],'turn':b['turn'],
                    'same_goal':a['goal'] is not None and a['goal']==b['goal'],'same_claim':a['normalized_claim']==b['normalized_claim'],
                    'same_channel':a['kind']==b['kind'],'same_canonical_authority':a['canonical_reference']==b['canonical_reference']})
        actors.append({'actor':actor,'role':actions[0]['role'],'actor_index':actions[0]['actor_index'],
            'own_opportunities':len(actions),'unrestricted_opportunities':sum(not a['communication_slot'] for a in actions),
            'direct_actions':len(direct_actions),'direct_pairs':max(0,len(direct_actions)-1),
            'repeated_goals':sum(a['goal']==b['goal'] for (_,a),(_,b) in zip(direct_actions,direct_actions[1:])),
            'own_adjacent_pairs':len(own_pairs),'strict_repeated_goals':strict,'goal_runs':len(actor_runs),
            'repeated_goal_runs':sum(len(r)>=2 for r in actor_runs),'longest_run_direct_actions':max(map(len,actor_runs),default=0),
            'returns_after_other_goal':returns,'distinct_goals':len(seen)})
    return {'pairs':pairs,'runs':runs,'actors':actors,'source_losses':losses}

def event_windows(episode,horizon):
    family=episode['family_id'];world=episode['world']
    scenario=next(s for s in make_family(family.split('-')[0],int(family.split('-')[-1]),horizon) if s.world==world)
    by_actor=defaultdict(list)
    for action in episode['actions']:
        if not action['communication_slot']:by_actor[action['actor']].append(action)
    rows=[]
    for turn,event in enumerate(scenario.events,1):
        if turn==1 or event.kind=='filler':continue
        for slot,value in event.updates:
            for actor,actions in by_actor.items():
                selected={'before':[(i,a) for i,a in enumerate(actions) if a['turn']<turn][-2:],
                          'after':[(i,a) for i,a in enumerate(actions) if a['turn']>=turn][:2]}
                assigned=actions[0]['assigned_slot'];owned=actions[0]['owned_option']
                before=scenario.truth_at(turn-1).values;after=scenario.truth_at(turn).values
                alignment=('unrelated_slot' if assigned!=slot else 'away_from_owned' if before[slot]==owned and after[slot]!=owned else
                    'toward_owned' if before[slot]!=owned and after[slot]==owned else 'unchanged_alignment')
                for side,selected_actions in selected.items():
                    for index,(_,a) in enumerate(selected_actions,1):
                        goal=tuple(a['goal']) if a['goal'] is not None else None
                        rows.append({'event_turn':turn,'event_kind':event.kind,'event_slot':slot,'event_value':value,
                            'actor':actor,'role':a['role'],'side':side,'window_index':index,'action_turn':a['turn'],
                            'turn_lag':a['turn']-turn,'assigned_slot_relevant':assigned==slot,'alignment_change':alignment,
                            'valid_direct':direct(a),'event_value_endorsed':direct(a) and goal==(slot,value),
                            'old_value_endorsed':direct(a) and goal==(slot,before[slot]),
                            'owned_value_endorsed':a['owned_goal_endorsed'],'action_value_current':a['value_current'],
                            'insistence_after_revision':side=='after' and event.kind=='set' and alignment=='away_from_owned' and a['owned_goal_endorsed']})
    return rows
