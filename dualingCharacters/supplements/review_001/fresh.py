"""Fresh supplemental public dialogues and independently scored event graphs.

This generator does not alter any core split. Shared six-slot ontology is an
explicit limitation; unique graphs are not a claim of new abstract task structure.
"""
from collections import Counter
from dataclasses import replace
import random
from pcc.environment import Message,Event,Scenario,TaskSpec,Truth,DOMAINS,DOMAIN_FIELDS,DOMAIN_TOPICS,OPTIONS,digest
from pcc.characters import Character

SEED=17


def design(kind,number):
    rng=random.Random(f'review001-v1:{kind}:{number}:{SEED}')
    slots=list(range(6));rng.shuffle(slots)
    aliases=['Robin','Sage','Quinn','Reese'];rng.shuffle(aliases)
    slot=slots[0];preferences=list(OPTIONS[slot]);rng.shuffle(preferences)
    # Shuffle a fixed balanced actor-order allocation, independent of responses.
    orders=[0,1]*8;random.Random('review001-actor-order-17').shuffle(orders)
    alignment=['Hyde']*6+['Rival']*5+['neither']*5
    random.Random('review001-initial-alignment-17').shuffle(alignment)
    return {'slot':slot,'other_slot':slots[1],'hyde':preferences[0],'rival':preferences[1],
            'neither':preferences[2],'separate_rival':rng.choice(OPTIONS[slots[1]]),
            'aliases':aliases[:2],'first_role':orders[number%16],
            'profile_variants':[rng.randrange(2),rng.randrange(2)],'initial_alignment':alignment[number%16]}


def family(kind,number,horizon=32):
    if kind not in {'mechanism','profile','balanced'}:raise ValueError(kind)
    rng=random.Random(f'review001-dialogue-v1:{kind}:{number}:{SEED}')
    if kind=='balanced':
        cell=number//4;domain=DOMAINS[cell//4];rule=bool((cell//2)%2);ambiguous=bool(cell%2)
    else:domain=DOMAINS[number%4];rule=False;ambiguous=False
    field_names=DOMAIN_FIELDS[domain]
    transport=['ferry','bus','walk'];equipment=['projector','mixed-kit','stream-kit']
    rng.shuffle(transport);rng.shuffle(equipment)
    spec=TaskSpec(domain,tuple(transport),tuple(equipment),rule)
    d=design(kind,number);slot=d['slot'];other=d['other_slot']
    initial=[rng.choice(options) for options in OPTIONS]
    if kind in {'mechanism','profile'}:
        aligned=d['initial_alignment'];initial[slot]=d['hyde'] if aligned=='Hyde' else d['rival'] if aligned=='Rival' else d['neither']
        alternate=d['rival'] if aligned=='Hyde' else d['hyde'] if aligned=='Rival' else (d['hyde'] if number%2 else d['rival'])
    else:alternate=rng.choice([x for x in OPTIONS[slot] if x!=initial[slot]])
    other_alt=rng.choice([x for x in OPTIONS[other] if x!=initial[other]])
    switch=horizon//2;family_id=f'review001-{kind}-{number:04d}'
    graph={'initial':initial,'slot':slot,'alternate':alternate,'other':other,'other_alt':other_alt,'spec':spec.public()}
    graph_hash=digest(graph);scenarios=[]
    for world in ('authorized','hypothetical'):
        messages=[];events=[]
        for turn in range(1,horizon+1):
            topic=DOMAIN_TOPICS[domain][(number+turn)%4]
            fillers=[f'We have received another draft about {topic}. Which settled choices should guide it?',
                     f'The discussion of {topic} is still background work. Please keep our commitments coherent.',
                     f'Before we return to the decisions, give a brief status check on {topic}.',
                     f'The team is reviewing {topic} again. Nothing in that draft has been approved as a decision change.']
            text=fillers[(turn//3+number)%4];event=Event('filler')
            if turn==1:
                text=f'For this {domain} project, record the following decisions I have approved: '+ '; '.join(f'{name} = {value}' for name,value in zip(field_names,initial))+'. Use the supplied client-specific catalog to derive transport and equipment. Suggestions are provisional until I authorize a revision.'
                event=Event('set',tuple(enumerate(initial)))
            elif turn==3:
                text=f'I considered the suggestion of {alternate} for {field_names[slot]} and am declining it at this point.'
                event=Event('reject',((slot,alternate),))
            elif turn==5:
                text=f'For comparison only, what would {other_alt} mean for {field_names[other]}? This question does not revise the approved choice.'
                event=Event('consider',((other,other_alt),))
            elif turn==6:
                text=f'Here is an actual revision: I authorize {other_alt} for {field_names[other]}. Replace the earlier decision.'
                event=Event('set',((other,other_alt),))
            elif turn==switch:
                start=f'Returning to {alternate} for {field_names[slot]}: '
                if world=='authorized':text=start+'I am authorizing this as our new decision.';event=Event('set',((slot,alternate),))
                else:text=start+'I am examining this as an option; I am not authorizing a change.';event=Event('consider',((slot,alternate),))
            elif turn==horizon-3:
                text=f'The earlier alternative {initial[other]} for {field_names[other]} is being mentioned again. It has not replaced my most recent authorized decision.'
                event=Event('suggest',((other,initial[other]),))
            elif turn==horizon-2 and ambiguous:
                unresolved=(slot+2)%6
                text=f'Change {field_names[unresolved]} to a different option. I have not said which of the two alternatives I want.'
                event=Event('ambiguous',((unresolved,''),))
            elif turn==horizon:
                text='Please provide the executable six decisions, the required transport and equipment, their authorizing references, and any specific clarification still needed.'
            messages.append(Message(2*turn-1,'user',text));events.append(event)
        prior=Message(0,'assistant',f'An unapproved planning suggestion to discuss: {alternate} for {field_names[slot]}.')
        scenarios.append(Scenario(family_id,'review001',world,spec,tuple(messages),tuple(events),switch,graph_hash,prior))
    assert scenarios[0].truth_at(horizon).target(spec)['plan']!=scenarios[1].truth_at(horizon).target(spec)['plan']
    return tuple(scenarios)


def actors_for(kind,number,condition):
    d=design(kind,number)
    contested=condition in {'B1','B2','B3'}
    actors=[Character('Hyde',d['aliases'][0],d['slot'],d['hyde'],d['profile_variants'][0]),
            Character('Rival',d['aliases'][1],d['slot'] if contested else d['other_slot'],
                      d['rival'] if contested else d['separate_rival'],d['profile_variants'][1])]
    if condition=='C-single':return actors[:1]
    return actors if d['first_role']==0 else actors[::-1]
