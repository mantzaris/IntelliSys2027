"""Typed mutation records distinguish affected checks from changed truth values."""
from dataclasses import dataclass,asdict
from .reports import make_reports


@dataclass(frozen=True)
class MutationRecord:
    base_pair_identifier:str
    family:str
    preconditions:str
    preconditions_verified:bool
    changed_fields:list
    dependent_scoped_predicates:list
    truth_changed_predicates:list
    intermediate_results:list
    correct_final_answers:list
    decision_changed:bool
    report_relationship:dict


def describe(pair):
    before,after=pair['worlds'];ev=pair['evaluation'];family=ev['family']
    edits=ev['changed_fields']
    if family=='numeric':
        valid=len(edits)==1 and edits[0]['path'].startswith('/capacities/') and abs(edits[0]['after']-edits[0]['before'])==1
        tasks={'resource'};entities={edits[0]['path'].split('/')[-1]}
    elif family=='identity':
        a,b=before['jobs'][1],after['jobs'][1]
        valid=(a['identifier']==b['identifier'] and a['duration']==b['duration'] and
               len(a['demands'])==len(b['demands'])==1 and list(a['demands'].values())==list(b['demands'].values()) and a['demands']!=b['demands'])
        tasks={'resource'};entities=set(a['demands'])|set(b['demands'])
    elif family=='dependency':
        a={tuple(e) for e in before['precedence']};b={tuple(e) for e in after['precedence']}
        valid=len(a-b)==len(b-a)==1
        tasks={'precedence_release'};entities=None
    elif family=='quantifier':
        a,b=before['rules']['screening'],after['rules']['screening']
        valid={a['op'],b['op']}=={'all','any'} and a['args']==b['args'] and bool(a['args'])
        tasks={'screening'};entities=None
    elif family=='condition':
        a,b=[w['rules']['screening']['condition'] for w in (before,after)]
        valid=a=={'op':'not','arg':b} or b=={'op':'not','arg':a}
        tasks={'screening'};entities=None
    elif family=='version':
        valid={before['version'],after['version']}=={1,2} and before['rules']==after['rules'] and before['rules']['screening']['effective']==2
        tasks={k for k,v in before['rules'].items() if v['op']=='version'};entities=None
    else:raise ValueError('Unsupported mutation family')
    if not valid:raise ValueError('Mutation preconditions failed: '+pair['pair_id'])
    split='live' if pair['split']=='live_development' else pair['split']
    reports=[make_reports(w,split,pair['seed']) for w in (before,after)]
    dependent=sorted({(r.claim.task_identifier,r.claim.candidate_identifier,r.claim.entity_identifier)
                      for rs in reports for r in rs if r.claim.task_identifier in tasks and
                      (entities is None or r.claim.entity_identifier in entities)})
    claims=[{r.claim.key:r.claim.asserted_value for r in rs} for rs in reports]
    common=set(claims[0])&set(claims[1])
    relationship={'equivalent_scope_and_value_keys':sorted(k for k in common if claims[0][k]==claims[1][k]),
                  'same_scope_changed_value_keys':sorted(k for k in common if claims[0][k]!=claims[1][k]),
                  'before_only_scope_keys':sorted(set(claims[0])-common),
                  'after_only_scope_keys':sorted(set(claims[1])-common),
                  'note':'A criterion or authorized version may change scope even when its Boolean result is unchanged.'}
    return asdict(MutationRecord(pair['pair_id'],family,ev['preconditions'],valid,edits,
        [dict(zip(('task_identifier','candidate_identifier','entity_identifier'),scope)) for scope in dependent],
        ev['affected_predicates'],[x['candidates'] for x in ev['oracle']],
        [x['answer'] for x in ev['oracle']],ev['decision_changed'],relationship))
