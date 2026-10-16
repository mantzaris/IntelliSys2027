"""Oracle-only corpus balance audit; never consults model outcomes."""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
from rep_sensitivity.generation import generate
from rep_sensitivity.reports import freeze,thaw,repeat
from rep_sensitivity.schema import canonical,digest

p=argparse.ArgumentParser();p.add_argument('--split',choices=['development','validation','heldout','live'],required=True)
p.add_argument('--pairs',type=int,required=True);p.add_argument('--benchmark-version',type=int,default=2)
p.add_argument('--output',required=True);a=p.parse_args()
pairs=generate(a.split,a.pairs,a.benchmark_version)
groups=defaultdict(list);selected=Counter();invariance=Counter();sizes=Counter()
for pair in pairs:
    frozen=freeze(pair)
    worlds=[thaw(x) for x in frozen['reports']]
    picked=[next(r for r in rs if canonical([r.claim.task_identifier,r.claim.candidate_identifier,r.claim.entity_identifier])==frozen['selected']) for rs in worlds]
    selected[(pair['evaluation']['kind'],picked[0].claim.task_identifier)]+=1
    invariance['selected_scope_and_value_unchanged']+=picked[0].claim.scope()==picked[1].claim.scope() and picked[0].claim.asserted_value==picked[1].claim.asserted_value
    for wi,rs in enumerate(worlds):
        truth=pair['evaluation']['oracle'][wi]
        objective=min(c['objective'] for c in truth['candidates'].values())
        fastest=[c for c in truth['candidates'].values() if c['objective']==objective]
        eligible=[c for c in truth['candidates'].values() if c['feasible']]
        best=min((c['objective'] for c in eligible),default=None)
        ties=sum(c['objective']==best for c in eligible)>1
        groups[(pair['evaluation']['kind'],pair['evaluation']['family'],pair['evaluation']['decision_changed'])].append({
            'none':truth['answer']=='NONE','tied_best_feasible':ties,'at_least_one_fastest_feasible':any(c['feasible'] for c in fastest),
            'fastest_all_infeasible':all(not c['feasible'] for c in fastest),
            'winning_tie_priority_rank':pair['worlds'][wi]['tie_order'].index(truth['answer']) if truth['answer']!='NONE' else None})
        sizes[(pair['evaluation']['kind'],len(rs))]+=1
        for condition in ('exact','paraphrase'):
            repeated=repeat(rs,frozen['selected'],condition,pair['split'])
            assert len(repeated)==len(rs)+3
            assert {c.key for r in repeated for c in r.claims()}=={c.key for r in rs for c in r.claims()}
result={'split':a.split,'benchmark_version':a.benchmark_version,'independent_base_pairs':len(pairs),
        'pairs_sha256':digest(pairs),'selected_report_invariance':dict(invariance),
        'selected_task_counts':[{'kind':k[0],'task':k[1],'pairs':n} for k,n in sorted(selected.items())],
        'report_sizes':[{'kind':k[0],'original_reports':k[1],'worlds':n} for k,n in sorted(sizes.items())],
        'strata':[],'interpretation':'Deterministic corpus audit, not model performance; the generator has limited structural diversity.'}
for key,rows in sorted(groups.items()):
    result['strata'].append({'kind':key[0],'family':key[1],'decision_changed':key[2],
        'worlds':len(rows),'base_pairs':len(rows)//2,
        **{k:sum(r[k] for r in rows) for k in ('none','tied_best_feasible','at_least_one_fastest_feasible','fastest_all_infeasible')},
        'winning_tie_priority_rank_counts':dict(Counter(r['winning_tie_priority_rank'] for r in rows if r['winning_tie_priority_rank'] is not None))})
output=Path(a.output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'split':a.split,'independent_base_pairs':len(pairs),'pairs_sha256':result['pairs_sha256']}))
