"""Small fresh-execution diagnostic, with explicit shared-source limitations."""
from collections import defaultdict
import csv
import json
from pathlib import Path
from .analysis import bootstrap,average
from .schema import digest
from .targeted_analysis import cluster_values,clustered_interval
from .targeted_audit import inventory


def summarize(directory,output,replicates=10000):
    directory=Path(directory);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((directory/'manifest.json').read_text());config=manifest['config']
    rows=[r for p in sorted((directory/config['model']/'scores').glob('*.json')) for r in json.loads(p.read_text())]
    groups=defaultdict(list)
    for row in rows:groups[row['arm']].append(row)
    summary=[];effects=[]
    for arm,rs in sorted(groups.items()):
        correct=sum(r['correct'] for r in rs)
        record={'arm':arm,'base_pairs':len({r['pair_id'] for r in rs}),'trajectories':len(rs),'correct':correct,
            'accuracy':average(r['correct'] for r in rs),'operational_failures':sum(r['operational_failure'] for r in rs),
            'displaced_trajectories':sum(r['resource_displacement'] is not None for r in rs),
            'initial_incorrect_or_invalid':sum(not r['initial_worker'].get('correct',False) for r in rs),
            'fresh_correct_after_initial_error':sum(r['fresh_correct_after_initial_error'] for r in rs),
            'additional_incorrect_findings':sum(r['additional_errors'] for r in rs),
            'logical_worker_calls':sum(r['worker_calls'] for r in rs),
            'valid_worker_calls':sum(d['valid'] for r in rs for d in r['worker_diagnostics']),
            'correct_worker_calls':sum(d.get('correct',False) for r in rs for d in r['worker_diagnostics']),
            'tokens':sum(r['total_tokens'] for r in rs),
            'inference_seconds':sum(r['inference_seconds_allocated'] for r in rs)}
        record['tokens_per_correct']=record['tokens']/correct if correct else None
        summary.append(record)
    strata={r['pair_id']:(r['family'],r['decision_changed']) for r in rows}
    for arm in ('copies','paraphrases','fresh_added','fresh_fixed'):
        for reference in (('original','copies') if arm.startswith('fresh') else ('original',)):
            values,n=cluster_values(rows,{arm:1,reference:-1},'correct')
            if values:effects.append({'contrast':arm+' - '+reference,'metric':'correct','paired_cells':n,
                                       **clustered_interval(values,strata,replicates=replicates)})
    result={'suite':config['name'],'complete':len(rows)==manifest['trajectories'],
        'base_pairs':manifest['base_pairs'],'analyzed_trajectories':len(rows),'source_scores_sha256':digest(rows),
        'analysis_source_sha256':digest(Path(__file__).read_text()),'manifest_sha256':digest(manifest),
        'summary':summary,'contrasts':effects,'physical_resource_inventory':inventory(directory,rows),
        'limitations':['Six development bases only; one per scheduling family/change stratum. Stratified bootstrap cannot estimate within-stratum uncertainty from one base. Intervals are withheld when any contributing stratum is a singleton.',
            'Roots see authoritative task data in every arm; correctness cannot be attributed solely to workers.',
            'Fresh executions share source data. Assigned procedures are instructions, not observed algorithms. No verified witnesses or additional evidence acquisition are measured.',
            'Fixed resources bound total input plus maximum output tokens for the entire baseline trajectory. Inability to fit full input is resource displacement, not a redundancy effect.']}
    (output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    for name,data in [('summary',summary),('contrasts',effects)]:
        if data:
            with (output/(name+'.csv')).open('w',newline='') as f:
                writer=csv.DictWriter(f,list(data[0]),lineterminator='\n');writer.writeheader();writer.writerows(data)
    return result


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('output');a=p.parse_args()
    print(json.dumps({k:v for k,v in summarize(a.directory,a.output).items() if k in ('suite','complete','analyzed_trajectories')}))
