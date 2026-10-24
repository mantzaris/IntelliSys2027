"""Clarification supervision by actual oracle situation and exact loss contribution."""
from collections import Counter,defaultdict
from pathlib import Path
from pcc.environment import make_family
from pcc.resources import sha256
from supplements.review_001.common import stream,write_csv
from .common import ROOT,REPORTS,ARTIFACTS,read,write,utc


def main():
    provenance=read(REPORTS/'exposure_provenance.json')['runs'];records=[];top_examples=[];inputs={}
    for run_id,entry in provenance.items():
        meta=read(ROOT/'artifacts/runs'/run_id/'status.json');cfg=meta['config'];supervision=next(ROOT/k for k in entry['inputs'] if k.endswith('/supervision.jsonl'))
        collection=read(supervision.parent/'status.json');horizon=collection['horizon'];examples={(r['family_id'],r['world'],r['turn']):r for r in stream(supervision)}
        detail=list(stream(ROOT/entry['detail_path']));groups=defaultdict(list)
        for loss in detail:
            k=loss['family_id'],loss['world'],loss['turn'];ex=examples[k];number=int(k[0].split('-')[-1]);s=make_family('train',number,horizon)[0 if k[1]=='authorized' else 1];truth=s.truth_at(k[2]);target=truth.target(s.spec)
            if ex['target']!=target or ex['completion']['clarify']!=target['clarify']:raise ValueError('Clarification supervision disagrees with independent dynamic oracle')
            case='necessary_clarification' if truth.pending else 'no_clarification_needed'
            situation=(case,s.spec.domain,s.events[k[2]-1].kind,k[2],loss['pool'],loss['label_source'])
            row={**loss,'case':case,'domain':s.spec.domain,'event_kind':s.events[k[2]-1].kind,'horizon':horizon,
              'target_clarification':target['clarify'],'candidate_clarification':ex['candidate'].get('clarify'),
              'pending_slots':len(truth.pending)}
            groups[situation].append(row)
        for (case,domain,event,turn,pool,label),group in groups.items():
            active=[r for r in group if r.get('unmasked_target_tokens',0)>0]
            records.append({'run_id':run_id,'model':cfg['model'],'condition':cfg['condition'],'seed':cfg['seed'],'round':1 if '-r1-' in run_id else 0,
              'case':case,'domain':domain,'event_kind':event,'turn':turn,'horizon':horizon,'pool':pool,'label_source':label,
              'loaded_unique_examples':len(group),'loss_contributing_unique_examples':len(active),'loss_contributing_families':len({r['family_id'] for r in active}),
              'contributing_occurrences':sum(r.get('occurrences_contributing_loss',0) for r in active),'supervised_target_tokens':sum(r.get('unmasked_target_tokens',0) for r in active)})
        nonempty=[r for values in groups.values() for r in values if r['case']=='necessary_clarification' and r.get('unmasked_target_tokens',0)>0]
        denominator=sum(r['unmasked_target_tokens'] for r in nonempty)
        for rank,row in enumerate(sorted(nonempty,key=lambda r:(-r['unmasked_target_tokens'],r['family_id'],r['world'],r['turn']))[:5],1):
            top_examples.append({'run_id':run_id,'model':cfg['model'],'condition':cfg['condition'],'seed':cfg['seed'],'round':1 if '-r1-' in run_id else 0,
              'rank':rank,'family_id':row['family_id'],'world':row['world'],'turn':row['turn'],'pool':row['pool'],'label_source':row['label_source'],
              'domain':row['domain'],'target_clarification':row['target_clarification'],'candidate_clarification':row['candidate_clarification'],
              'supervised_target_tokens':row['unmasked_target_tokens'],'contributing_occurrences':row['occurrences_contributing_loss'],
              'share_of_all_nonempty_clarification_target_tokens':row['unmasked_target_tokens']/denominator})
        if sum(r['supervised_target_tokens'] for r in records if r['run_id']==run_id)!=read(ROOT/'artifacts/runs'/run_id/'training/training_summary.json')['supervised_tokens']:raise ValueError('Loss contribution did not reconcile')
        inputs[run_id]={str(supervision.relative_to(ROOT)):sha256(supervision),entry['detail_path']:entry['detail_sha256']}
    final_strata=[]
    for path in sorted((ARTIFACTS/'core_trajectory').glob('*.json')):
        audit=read(path);header=audit['metadata'];finals=audit['final_audit'];cached=read(ARTIFACTS/'core_audits/evaluations'/f'{header["run_id"]}.json');expected={(r['family_id'],r['world']):bool(r['target']['clarify']) for r in cached}
        for needed in (False,True):
            group=[r for r in finals if expected[r['family_id'],r['world']]==needed]
            final_strata.append({**header,'clarification_actually_needed':needed,'conversations':len(group),
              **{field:sum(r[field] for r in group) for field in ('clarification_error','unnecessary_clarification','missed_necessary_clarification','wrong_issue_clarification','unnecessary_clarification_with_settled_nulls')}})
    for name,rows in [('clarification_training_situations',records),('clarification_top_examples',top_examples),('clarification_necessity_strata',final_strata)]:
        write(REPORTS/(name+'.json'),rows);write_csv(REPORTS/(name+'.csv'),rows)
    write(REPORTS/'training_situations_provenance.json',{'generated_utc':utc(),'inputs':inputs,'source_sha256':sha256(Path(__file__)),
      'qualification':'Exact completion-token exposure joined to independently recomputed training truth. All necessary-clarification examples share the original benchmark ambiguity grammar; domain/event confounding is retained and reported. Highest-exposure examples are diagnostics, not independent samples or causal proof.'})
    print({'completed_fits':len(provenance),'supervision_situation_rows':len(records),'final_necessity_strata':len(final_strata)})


if __name__=='__main__':main()
