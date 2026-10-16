"""One prespecified pilot case, retained in every primary pilot aggregate."""
import gzip,json
from pathlib import Path
from collections import defaultdict
from rep_sensitivity.metrics import parse,same_value
from rep_sensitivity.reports import thaw
from rep_sensitivity.schema import canonical,digest
from rep_sensitivity.storage import utcnow

source=Path('artifacts/runs/pilot-v7');pid='e765f8bb5f0e2aad'
pair=next(p for p in json.loads((source/'pairs.json').read_text()) if p['pair_id']==pid)
corpus=json.loads((source/'frozen-reports.json').read_text())[pid]
rows=[r for r in json.loads((source/'qwen3'/'scores'/(pid+'.json')).read_text()) if r['organization']=='hierarchical']
records=[]
for r in rows:
    reports=thaw(corpus['reports'][r['world']]);objectives={x.claim.key:x.claim.asserted_value for x in reports if x.claim.task_identifier=='objective'}
    target=next(x for x in reports if canonical([x.claim.task_identifier,x.claim.candidate_identifier,x.claim.entity_identifier])==corpus['selected'])
    emitted=defaultdict(list)
    for h in r['request_hashes']:
        c=json.loads(gzip.decompress((source/'qwen3'/'calls'/(h+'.json.gz')).read_bytes()))
        if c['stage']=='root':continue
        obj,status=parse(c['response']['text'],pair['worlds'][r['world']]['tie_order'],manager=True)
        if obj:
            for key,value,refs in obj['assertions']:
                if key in objectives:emitted[key].append(value)
    records.append({**{k:r[k] for k in ('trial_id','world','policy','condition','repetition','choice','correct','request_hashes')},
        'all_objectives_boolean_true':all(emitted[k] and all(v is True for v in emitted[k]) for k in objectives),
        'all_objectives_correct_numeric':all(emitted[k] and all(same_value(v,n) for v in emitted[k]) for k,n in objectives.items()),
        'objective_assertions':dict(emitted),'selected_candidate':target.claim.candidate_identifier,
        'selected_value':target.claim.asserted_value,'correct_candidate':pair['evaluation']['oracle'][r['world']]['answer']})
groups=defaultdict(list)
for r in records:groups[r['policy'],r['condition']].append(r)
result={'status':'exploratory_prespecified_influential_case_audit','utc':utcnow(),'pair_id':pid,'independent_base_pairs':1,
    'source_score_sha256':digest(json.loads((source/'qwen3'/'scores'/(pid+'.json')).read_text())),
    'analysis_source_sha256':digest(Path(__file__).read_text()),'world_oracles':pair['evaluation']['oracle'],
    'aggregate':[{'policy':policy,'condition':condition,'trajectories':len(rs),
                 **{k:sum(r[k] for r in rs) for k in ('correct','all_objectives_boolean_true','all_objectives_correct_numeric')}} for (policy,condition),rs in sorted(groups.items())],
    'target':{'candidate':records[0]['selected_candidate'],'objective':records[0]['selected_value']},
    'sole_feature_hypothesis':'Repetition can preserve numerical-objective types/values through summaries; the already frozen root lossless-transport interaction tests the bottleneck. A close margin, attention or arithmetic alone is not isolated by these observations.',
    'records':records}
Path('results/pilot-interpretation-v2/influential-pair-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'pair':pid,'target':result['target'],'aggregate':result['aggregate']}))
