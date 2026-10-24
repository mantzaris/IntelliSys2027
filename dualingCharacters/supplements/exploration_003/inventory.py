"""Lock eligibility before category comparisons; inspect completed local files only."""
from collections import Counter, defaultdict
import argparse
import hashlib
import re
import tarfile
from .common import ROOT,HERE,REPORTS,CACHE,CONDITIONS,read,write,utc,sha256,stream,trace_path,verify_prior,log
from pcc.eligibility import exclusions
from pcc.evaluation import opportunities


def capture():
    destination=HERE/'EVIDENCE_SNAPSHOT.json'
    if destination.exists():
        raise FileExistsError('Snapshot already locked; do not expand it with later completions')
    frozen=verify_prior(); excluded=exclusions(ROOT); included=[]; omitted=[]
    cutoff=utc()
    for path in sorted((ROOT/'artifacts/runs').glob('*/status.json')):
        meta=read(path); run_id=path.parent.name
        if meta.get('task')!='collect' and not run_id.startswith('mechanism-'):
            continue
        reason=excluded.get(run_id)
        if meta.get('status')!='completed':reason='Not completed at snapshot cutoff'
        if reason:
            omitted.append({'run_id':run_id,'status':meta.get('status'),'reason':reason});continue
        cohort=('primary_mechanism' if run_id=='mechanism-final-001' else
                'main_collection' if run_id.startswith('main-') else 'historical_protocol')
        conditions=[c for c in CONDITIONS if (path.parent/f'{c}_summary.json').exists()] if run_id.startswith('mechanism-') else [meta['config']['condition']]
        included.append({'run_id':run_id,'cohort':cohort,'conditions':conditions,
            'status_sha256':sha256(path),'metadata':meta})
    document={'cutoff_utc':cutoff,'prior_freezes':frozen,'included':included,'excluded_or_partial':omitted,
      'selection':'All completed locally available collection/mechanism runs at cutoff, excluding the existing exclusion registry. Older protocols remain separate; primary reference is the final mechanism protocol, selected by protocol identity, not outcomes.',
      'run_exclusions_sha256':sha256(ROOT/'configs/run_exclusions.json')}
    write(destination,document);log(f'Locked evidence population at {cutoff}: {len(included)} completed runs; later completions cannot enter this snapshot.')
    return document


def validate():
    snap=read(HERE/'EVIDENCE_SNAPSHOT.json'); entries=[]; cache_hashes={}; historical=[]
    for entry in snap['included']:
        run=ROOT/'artifacts/runs'/entry['run_id'];meta=entry['metadata']
        if sha256(run/'status.json')!=entry['status_sha256']:raise ValueError('Completed status changed')
        config=meta['config']; hashes={'status.json':entry['status_sha256']}
        for name in ('config.json','source_snapshot.tar.gz','batches.jsonl'):
            if (run/name).exists():hashes[name]=sha256(run/name)
        adapter=meta.get('loaded_adapter_path'); adapter_check=None
        if adapter:
            ap=ROOT/adapter/'adapter_model.safetensors'
            if str(ap) not in cache_hashes:cache_hashes[str(ap)]=sha256(ap)
            digest=cache_hashes[str(ap)]
            if digest!=meta.get('loaded_adapter_sha256'):raise ValueError('Adapter mismatch')
            adapter_check={'path':str(ap.relative_to(ROOT)),'sha256':digest}
        round_match=re.search(r'-r(\d)-',entry['run_id'])
        for condition in entry['conditions']:
            prefix=condition if entry['run_id'].startswith('mechanism-') else 'collection'
            summary_path=run/f'{prefix}_summary.json'; summary=read(summary_path)
            horizon=summary[0]['horizon']; expected={(r['family_id'],r['world']) for r in summary}
            if len(expected)!=len(summary):raise ValueError('Duplicate episode summary')
            for family in {k[0] for k in expected}:
                if {w for f,w in expected if f==family}!={'authorized','hypothetical'}:raise ValueError('Incomplete paired worlds')
            turns=defaultdict(list); counts=Counter();sources={}; full_hashes=dict(hashes)
            for name in (f'{prefix}.jsonl',f'{prefix}_characters.jsonl',f'{prefix}_interventions.jsonl',f'{prefix}_summary.json'):
                p=trace_path(run/name)
                if p.exists():full_hashes[p.name]=sha256(p)
            for row in stream(run/f'{prefix}.jsonl'):
                key=row['family_id'],row['world']; turns[key].append(row['turn'])
                if row['condition']!=condition:raise ValueError('Condition mismatch')
            if set(turns)!=expected or any(sorted(ts)!=list(range(1,horizon+1)) for ts in turns.values()):
                raise ValueError('Missing/duplicate turn coverage: '+entry['run_id'])
            actions=defaultdict(list); missing=Counter(); action_order={}; actor_order={}
            ap=trace_path(run/f'{prefix}_characters.jsonl')
            if ap.exists():
                for row in stream(ap):
                    key=row['family_id'],row['world'];actions[key].append(row['turn']);counts['actions']+=1
                    actor_order.setdefault(key,[]).append(row['actor'])
                    for field in ('generation','prompt','communication_slot','memory_changed','assigned_slot','owned_option'):
                        missing[field]+=field not in row
                    counts['input_tokens']+=row.get('generation',{}).get('input_tokens',0)
                    counts['output_tokens']+=row.get('generation',{}).get('output_tokens',0)
                    counts['generation_records']+='generation' in row
            schedule=sorted(opportunities(horizon,config['intervention_opportunities']))
            if condition!='C1' and (set(actions)!=expected or any(ts!=schedule for ts in actions.values())):
                raise ValueError('Missing, duplicated or out-of-order opportunities: '+entry['run_id']+condition)
            if condition=='C1' and actions:raise ValueError('Clean condition has actions')
            # Full keys and observed order are retained compactly, not inferred from actor counts.
            episode_rows=[{'family_id':f,'world':w,'turns':actions.get((f,w),[]),'actors':actor_order.get((f,w),[])} for f,w in sorted(expected)]
            identity=entry['run_id']+'__'+condition
            order_path=CACHE/'action_orders'/f'{identity}.json'
            write(order_path,episode_rows)
            row={'id':identity,'run_id':entry['run_id'],'condition':condition,'cohort':entry['cohort'],
                'model':config['model'],'model_revision':meta.get('model_revision'),'seed':config['seed'],
                'round':int(round_match.group(1)) if round_match else None,'prefix':prefix,
                'horizon':horizon,'families':len(expected)//2,'conversations':len(expected),'defender_rows':sum(map(len,turns.values())),
                'opportunities_per_episode':len(schedule) if condition!='C1' else 0,'schedule':schedule,
                'defender_identity':meta.get('loaded_adapter_sha256','untrained_base'),'adapter_verified':adapter_check,
                'character_generator':'frozen base; no LoRA for character calls in audited backend',
                'source_hashes':meta.get('source_hashes'), 'raw_hashes':full_hashes,'missing_fields':dict(missing),
                'action_accounting':dict(counts),'order_manifest':str(order_path.relative_to(ROOT)),
                'order_manifest_sha256':sha256(order_path),'family_ids':sorted({f for f,w in expected}),
                'interpretation':('Same frozen base weights, endogenous condition-specific states; one pilot seed' if entry['cohort']=='primary_mechanism' else
                  'Round-zero shared base weights; observational training collection' if round_match and round_match.group(1)=='0' else
                  'Condition-specific trained defender and distinct second-round families; observational only' if round_match else
                  'Earlier protocol; archived separately, never pooled with the final protocol')}
            entries.append(row)
    primary=[x for x in entries if x['cohort']=='primary_mechanism']
    a,b=[next(x for x in primary if x['condition']==c) for c in ('C3','C5')]
    for key in ('model_revision','seed','horizon','family_ids','schedule','defender_identity'):
        if a[key]!=b[key]:raise ValueError('Primary matchedness failed: '+key)
    cap=min(a['opportunities_per_episode'],b['opportunities_per_episode'])
    doc={'audit_utc':utc(),'cutoff_utc':snap['cutoff_utc'],'snapshot_sha256':sha256(HERE/'EVIDENCE_SNAPSHOT.json'),
        'included_cells':entries,'excluded_or_partial':snap['excluded_or_partial'],
        'primary_common_budget':cap,'prefix_budgets':list(range(1,cap+1)),
        'novelty_segments':[[1,cap//3],[cap//3+1,2*cap//3],[2*cap//3+1,cap]],
        'primary_matchedness':'C3/C5 final pilot share base weights, revision, seed, scenario identities and schedule. Their realized states and stochastic call offsets differ. This is not identical-state attack replay.',
        'main_missing_conditions':[c for c in CONDITIONS if c not in {e['condition'] for e in entries if e['cohort']=='main_collection'}],
        'historical_qualification':'V2/V3 and earlier collection protocols inventoried with hashes and completeness; only coarse action/repetition diagnostics are reused, because source and routing revisions differ. No historical efficacy exclusion was newly imposed.',
        'tokens':'Actual per-generation input/output tokens include prompts, histories and biographies. C2 deterministic corruption makes no character model calls; missing generation records are not measured zero-token LLM calls.'}
    write(HERE/'DATA_AUDIT.json',doc)
    log(f'Validated {len(entries)} cells, paired/turn/action coverage and adapters. Mechanical primary prefix budget {cap}. No category summaries computed.')
    return doc


def sources():
    rows=[]
    for entry in read(HERE/'EVIDENCE_SNAPSHOT.json')['included']:
        meta=entry['metadata'];archive=ROOT/'artifacts/runs'/entry['run_id']/'source_snapshot.tar.gz'
        row={'run_id':entry['run_id'],'archive_present':archive.exists(),'verified_files':0,'mismatches':[]}
        if archive.exists():
            row['archive_digest_matches_record']=sha256(archive)==meta.get('source_snapshot_sha256')
            with tarfile.open(archive) as bundle:
                for name,digest in meta.get('source_hashes',{}).items():
                    try:actual=hashlib.sha256(bundle.extractfile(name).read()).hexdigest()
                    except KeyError:actual=None
                    if actual!=digest:row['mismatches'].append(name)
                    else:row['verified_files']+=1
            if row['mismatches'] or not row['archive_digest_matches_record']:raise ValueError('Archived source integrity failed')
        rows.append(row)
    write(HERE/'SOURCE_AUDIT.json',rows)
    return {'included_cells':rows}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['capture','validate','sources']);args=parser.parse_args()
    result=globals()[args.command]();print({'operation':args.command,'cells':len(result.get('included_cells',result.get('included',[])))})
