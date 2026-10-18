"""Exploratory transition analysis of the complete main study, without inference.

Same-index cross-condition comparisons share the recorded seed scheme. Within-
condition comparisons use repetition 0 versus 1 and hence different seeds. Their
rate difference is descriptive, not an identified causal effect on instability.
"""
import csv
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from rep_sensitivity.analysis import bootstrap


def read_rows(path):
    with Path(path).open() as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for field in ('correct', 'operational_failure', 'decision_changed'):
            if row[field] not in ('True', 'False'):
                raise ValueError((field, row[field]))
            row[field] = row[field] == 'True'
        row['repetition'] = int(row['repetition'])
        row['world'] = int(row['world'])
        row['choice'] = row['choice'] or None
    return rows


def transition(a, b):
    valid = (not a['operational_failure'] and not b['operational_failure']
             and a['choice'] is not None and b['choice'] is not None)
    changed = valid and a['choice'] != b['choice']
    return {'correction': int(not a['correct'] and b['correct']),
            'regression': int(a['correct'] and not b['correct']),
            'correctness_change': int(a['correct'] != b['correct']),
            'answer_comparable': int(valid), 'answer_change': int(changed),
            'wrong_to_wrong_answer_change': int(changed and not a['correct'] and not b['correct']),
            'operational_failure_pair': int(a['operational_failure'] or b['operational_failure']),
            'accuracy_effect': int(b['correct']) - int(a['correct'])}


def describe(pairs, strata):
    fields = list(transition(pairs[0][1], pairs[0][2]))
    totals = {field: 0 for field in fields}
    by_base = defaultdict(list)
    for base, a, b in pairs:
        values = transition(a, b)
        by_base[base].append(values)
        for field, value in values.items(): totals[field] += value
    means = {field: {base: sum(r[field] for r in rs)/len(rs) for base, rs in by_base.items()}
             for field in fields}
    return {'base_pairs': len(by_base), 'paired_comparisons': len(pairs),
            'totals': totals, 'unchanged_correctness': len(pairs)-totals['correctness_change'],
            'rates_all_pairs': {field: totals[field]/len(pairs) for field in fields},
            'answer_change_rate_among_comparable': totals['answer_change']/totals['answer_comparable'],
            'intervals': {field: bootstrap(means[field], strata) for field in
                          ('correctness_change', 'answer_change', 'accuracy_effect')},
            'base_rates': {field: means[field] for field in
                           ('correctness_change', 'answer_change', 'accuracy_effect')}}


def analyze(rows):
    groups = []
    for kind in ('schedule', 'workflow'):
        for model in ('qwen3', 'phi4'):
            for organization in ('both', 'flat', 'hierarchical'):
                rs = [r for r in rows if r['kind']==kind and r['model']==model
                      and (organization=='both' or r['organization']==organization)]
                strata = {r['pair_id']:(r['family'],r['decision_changed']) for r in rs}
                cells = defaultdict(dict)
                for r in rs:
                    key = tuple(r[k] for k in ('pair_id','world','organization','policy'))
                    arm = (r['condition'],r['repetition'])
                    if arm in cells[key]: raise ValueError('Duplicate paired cell')
                    cells[key][arm] = r
                expected = {(c,s) for c in ('single','exact','paraphrase') for s in (0,1)}
                if not all(set(c)==expected for c in cells.values()): raise ValueError('Incomplete paired cell')
                comparisons = {}
                for condition in ('single','exact','paraphrase'):
                    pairs=[(key[0],arms[condition,0],arms[condition,1]) for key,arms in cells.items()]
                    comparisons[condition+'_seed1_minus_seed0']=describe(pairs,strata)
                for treatment,control in (('exact','single'),('paraphrase','single'),('exact','paraphrase')):
                    pairs=[(key[0],arms[control,s],arms[treatment,s])
                           for key,arms in cells.items() for s in (0,1)]
                    comparisons[treatment+'_minus_'+control]=describe(pairs,strata)
                excess={}
                within_effects={}
                baseline=comparisons['single_seed1_minus_seed0']
                for treatment in ('exact','paraphrase'):
                    cross=comparisons[treatment+'_minus_single']
                    excess[treatment]={field:bootstrap(
                        {p:cross['base_rates'][field][p]-baseline['base_rates'][field][p] for p in strata},strata)
                        for field in ('correctness_change','answer_change')}
                    within=comparisons[treatment+'_seed1_minus_seed0']
                    within_effects[treatment]={field:bootstrap(
                        {p:within['base_rates'][field][p]-baseline['base_rates'][field][p] for p in strata},strata)
                        for field in ('correctness_change','answer_change')}
                groups.append({'kind':kind,'model':model,'organization':organization,
                    'comparisons':comparisons,'descriptive_cross_minus_within_baseline':excess,
                    'within_condition_disagreement_effects':within_effects})
    return groups


def main():
    source=Path('results/main-v7/decisions.csv')
    original=json.loads(Path('results/main-v7/analysis.json').read_text())
    if not original['complete']: raise ValueError('Main evaluation is incomplete')
    rows=read_rows(source)
    if len(rows)!=original['planned_trajectories']: raise ValueError('Unexpected trajectory count')
    result={'status':'exploratory_post_main_analysis','complete':True,
        'independent_base_pairs':len({r['pair_id'] for r in rows}), 'trajectories':len(rows),
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'analysis_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'seed_scheme':'sha256(pair_id, repetition, stage), excluding treatment, world and policy; cache keys retain trial identity',
        'pairing':'Cross-condition: same repetition index, both indices retained. Within-condition: seed index 0 to 1 once per world/organization/policy.',
        'denominators':'All complete pairs for correctness changes, including operational failures. Answer changes require two valid complete trajectories. Unconditional answer-change rates retain failures in the denominator but do not count a failure as an answer.',
        'uncertainty':'10000 whole-base bootstrap draws stratified by mutation family and decision-change status, seed 20271015. Pointwise intervals; no multiplicity-adjusted tests.',
        'limitation':'Two generations give one within-condition pair. Different-seed within-condition comparisons and common-seed cross-condition comparisons use different random couplings. Their rate difference does not isolate a causal increase in stochastic instability. Within-treatment minus within-baseline disagreement contrasts compare the same two seed indices, but each cell still supplies only one draw pair.',
        'groups':analyze(rows)}
    dest=Path('results/main-transitions-v1');dest.mkdir(exist_ok=True)
    (dest/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    for g in result['groups']:
        if g['kind']=='schedule' and g['organization']=='both':
            print(g['model'],{k:{'pairs':v['paired_comparisons'],'totals':v['totals']} for k,v in g['comparisons'].items()})
            print('descriptive_difference',g['descriptive_cross_minus_within_baseline'])


if __name__=='__main__': main()
