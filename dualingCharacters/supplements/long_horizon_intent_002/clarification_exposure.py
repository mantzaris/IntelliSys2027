"""Join exact loss exposure to clarification target classes, without replaying unchanged fits."""
from collections import Counter,defaultdict
from pathlib import Path
from pcc.resources import sha256
from supplements.review_001.common import stream,write_csv
from supplements.review_001.exposure import concentration
from .common import ROOT,REPORTS,ARTIFACTS,read,write,utc


def main():
    provenance=read(REPORTS/'exposure_provenance.json')['runs'];rows=[];sources={}
    for run_id,record in provenance.items():
        run=ROOT/'artifacts/runs'/run_id;meta=read(run/'status.json');cfg=meta['config']
        supervision=next(ROOT/k for k in record['inputs'] if k.endswith('/supervision.jsonl'))
        detail=ROOT/record['detail_path'];assert sha256(detail)==record['detail_sha256']
        examples={(r['family_id'],r['world'],r['turn']):r for r in stream(supervision)}
        grouped=defaultdict(list);detail_rows=[]
        for loss in stream(detail):
            key=loss['family_id'],loss['world'],loss['turn'];example=examples[key];target=example['completion']
            category='nonempty' if target['clarify'] else 'empty'
            annotated={**loss,'clarification_target_class':category,'clarification_target':target['clarify'],
              'candidate_clarification':example.get('candidate',{}).get('clarify'),
              'original_success':example['metrics']['success']}
            grouped[category,loss['pool']].append(annotated);detail_rows.append(annotated)
        for category in ('empty','nonempty'):
            for pool in ('clean','recovery'):
                group=grouped[category,pool];active=[r for r in group if r.get('unmasked_target_tokens',0)>0]
                rows.append({'run_id':run_id,'model':cfg['model'],'condition':cfg['condition'],'seed':cfg['seed'],
                  'round':1 if '-r1-' in run_id else 0,'clarification_target_class':category,'pool':pool,
                  'eligible_examples':sum((bool(x['completion']['clarify'])==(category=='nonempty')) and (('clean' if x['metrics']['success'] else 'recovery')==pool) for x in examples.values()),
                  'loss_contributing_unique_examples':len(active),'loss_contributing_unique_families':len({r['family_id'] for r in active}),
                  'contributing_occurrences':sum(r.get('occurrences_contributing_loss',0) for r in active),
                  'orphaned_target_tokens_masked':sum(r.get('orphaned_target_tokens_masked',0) for r in group),
                  **concentration([r.get('unmasked_target_tokens',0) for r in active]),
                  'qualification':'Target tokens are all unmasked completion tokens in examples of this clarification class, not tokens attributed specifically to the clarify field. Loaded-only examples excluded. Exposure/outcome associations are noncausal.'})
        assert sum(r['target_tokens'] for r in rows if r['run_id']==run_id)==read(run/'training/training_summary.json')['supervised_tokens']
        write(ARTIFACTS/'clarification_exposure'/f'{run_id}.json',detail_rows)
        sources[run_id]={str(supervision.relative_to(ROOT)):sha256(supervision),str(detail.relative_to(ROOT)):sha256(detail)}
    write(REPORTS/'clarification_exposure.json',rows);write_csv(REPORTS/'clarification_exposure.csv',rows)
    write(REPORTS/'clarification_exposure_provenance.json',{'generated_utc':utc(),'inputs':sources,'source_sha256':sha256(Path(__file__)),'sampling_reconstructed_previously':True})
    print({'fits':len(provenance),'clarification_pool_rows':len(rows),'repeated_optimizer_reconstruction':False})


if __name__=='__main__':main()
