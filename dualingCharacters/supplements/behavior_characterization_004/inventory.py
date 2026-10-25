"""Lock complete eligible evidence before inspecting new behavioral summaries."""
from collections import defaultdict
import argparse
import re
import tarfile
import hashlib
from pcc.eligibility import exclusions
from pcc.evaluation import opportunities
from .common import *

def capture():
    verify_previous();destination=HERE/'EVIDENCE_SNAPSHOT.json'
    if destination.exists():raise FileExistsError('Evidence cutoff already locked')
    cutoff=utc();excluded=exclusions(ROOT);included=[];omitted=[];evaluations=[]
    for path in sorted((ROOT/'artifacts/runs').glob('*/status.json')):
        meta=read(path);name=path.parent.name
        modern=(name.startswith('main-') and meta.get('task')=='collect') or name=='mechanism-final-001'
        evaluation=(name.startswith('main-') or name.startswith('base-')) and meta.get('task')=='evaluate'
        if not modern and not evaluation:continue
        reason=excluded.get(name)
        if meta.get('status')!='completed':reason='Incomplete at this snapshot cutoff'
        if reason:
            omitted.append({'run_id':name,'reason':reason,'status':meta.get('status')});continue
        row={'run_id':name,'metadata':meta,'status_sha256':sha256(path)}
        (included if modern else evaluations).append(row)
    write(destination,{'cutoff_utc':cutoff,'included_runs':included,'secondary_evaluations':evaluations,
        'excluded_or_incomplete':omitted,'selection':'All completed eligible main collections and the final mechanism protocol at cutoff; older protocols remain in exploration003 historical records, not pooled here.',
        'exclusion_registry_sha256':sha256(ROOT/'configs/run_exclusions.json'),
        'previous_scientific_manifest_sha256':sha256(ROOT/'supplements/exploration_003/SCIENTIFIC_MANIFEST.json')})
    log(f'Locked evidence cutoff {cutoff}: {len(included)} collection/mechanism runs and {len(evaluations)} completed secondary evaluations. No new comparative summaries.')

def validate():
    snapshot=read(HERE/'EVIDENCE_SNAPSHOT.json');cells=[];adapter_hashes={};sources=[]
    for run in snapshot['included_runs']:
        folder=ROOT/'artifacts/runs'/run['run_id'];meta=run['metadata'];cfg=meta['config']
        if sha256(folder/'status.json')!=run['status_sha256']:raise ValueError('Completed status changed')
        archive=folder/'source_snapshot.tar.gz';verified=0
        if not archive.exists():raise ValueError('Modern evidence missing archived source')
        if sha256(archive)!=meta['source_snapshot_sha256']:raise ValueError('Archived source mismatch')
        with tarfile.open(archive) as bundle:
            for path,digest in meta['source_hashes'].items():
                if hashlib.sha256(bundle.extractfile(path).read()).hexdigest()!=digest:raise ValueError('Source bytes mismatch')
                verified+=1
        sources.append({'run_id':run['run_id'],'verified_source_files':verified,'archive_sha256':meta['source_snapshot_sha256']})
        adapter=meta.get('loaded_adapter_path');identity='untrained_base'
        if adapter:
            path=ROOT/adapter/'adapter_model.safetensors'
            if str(path) not in adapter_hashes:adapter_hashes[str(path)]=sha256(path)
            identity=adapter_hashes[str(path)]
            if identity!=meta['loaded_adapter_sha256']:raise ValueError('Defender adapter mismatch')
        conditions=CONDITIONS if run['run_id']=='mechanism-final-001' else [cfg['condition']]
        for condition in conditions:
            prefix=condition if run['run_id']=='mechanism-final-001' else 'collection'
            summary=read(folder/(prefix+'_summary.json'));keys={(r['family_id'],r['world']) for r in summary}
            if len(keys)!=len(summary):raise ValueError('Duplicate episode')
            families=sorted({f for f,w in keys});horizon=summary[0]['horizon']
            if any({w for f,w in keys if f==family}!={'authorized','hypothetical'} for family in families):raise ValueError('Unpaired family')
            raw={};turns=defaultdict(list);actions=defaultdict(list);order=defaultdict(list)
            for name in (prefix+'.jsonl',prefix+'_characters.jsonl',prefix+'_interventions.jsonl',prefix+'_summary.json'):
                path=trace_path(folder/name)
                if path.exists():raw[path.name]=sha256(path)
            for row in stream(folder/(prefix+'.jsonl')):
                turns[row['family_id'],row['world']].append(row['turn'])
                if row['condition']!=condition or row['seed']!=cfg['seed']:raise ValueError('Run identity mismatch')
            if set(turns)!=keys or any(v!=list(range(1,horizon+1)) for v in turns.values()):raise ValueError('Incomplete/out-of-order episode')
            path=trace_path(folder/(prefix+'_characters.jsonl'))
            if path.exists():
                for row in stream(path):
                    key=row['family_id'],row['world'];actions[key].append(row['turn'])
                    order[key].append([row['turn'],row['actor'],row.get('communication_slot')])
            schedule=sorted(opportunities(horizon,cfg['intervention_opportunities']))
            if condition=='C1':
                if actions:raise ValueError('Clean collection has character actions')
            elif set(actions)!=keys or any(v!=schedule for v in actions.values()):raise ValueError('Incomplete opportunity schedule')
            rnd=re.search(r'-r(\d)-',run['run_id']);round_number=int(rnd.group(1)) if rnd else None
            cohort='mechanism_pilot' if rnd is None else ('main_round_zero' if round_number==0 else 'main_refreshed')
            identity_key=run['run_id']+'__'+condition;order_path=CACHE/'action_orders'/(identity_key+'.json')
            write(order_path,[{'family_id':f,'world':w,'action_order':order[f,w]} for f,w in sorted(keys)])
            cells.append({'id':identity_key,'run_id':run['run_id'],'condition':condition,'cohort':cohort,'seed':cfg['seed'],'round':round_number,
                'prefix':prefix,'model':cfg['model'],'model_revision':meta['model_revision'],'defender_identity':identity,
                'adapter_path':adapter,'character_generator':'same pinned untrained base; defender adapter disabled for character calls',
                'horizon':horizon,'family_ids':families,'families':len(families),'worlds':2,'schedule':schedule,
                'opportunities_per_episode':len(schedule) if condition!='C1' else 0,'config':cfg,'raw_hashes':raw,
                'status_sha256':run['status_sha256'],'source_archive_sha256':meta['source_snapshot_sha256'],
                'action_order_path':str(order_path.relative_to(ROOT)),'action_order_sha256':sha256(order_path)})
    evaluation_rows=[]
    for run in snapshot['secondary_evaluations']:
        folder=ROOT/'artifacts/runs'/run['run_id'];summary=folder/'evaluation_summary.json'
        if not summary.exists():raise ValueError('Completed evaluation summary missing')
        rows=read(summary);keys={(r['family_id'],r['world']) for r in rows}
        if len(keys)!=480 or len(rows)!=480 or any({w for f,w in keys if f==family}!={'authorized','hypothetical'} for family in {f for f,w in keys}):raise ValueError('Incomplete secondary paired summary')
        evaluation_rows.append({**run,'summary_path':str(summary.relative_to(ROOT)),'summary_sha256':sha256(summary)})
    write(HERE/'DATA_AUDIT.json',{'cutoff_utc':snapshot['cutoff_utc'],'snapshot_sha256':sha256(HERE/'EVIDENCE_SNAPSHOT.json'),
        'cells':cells,'secondary_evaluations':evaluation_rows,'excluded_or_incomplete':snapshot['excluded_or_incomplete'],
        'source_archives':sources,'missing_main_conditions':[c for c in CONDITIONS if c not in {x['condition'] for x in cells if x['cohort'].startswith('main_')}],
        'cost_accounting':'Actual action/defender generation records include input/history overhead; run loading and recovery calls are separate. No new model calls.',
        'routing':'Reserved communication APIs are peer/pass. Other slots also permit peer actions. Jekyll remains an accepted recipient even when the text requests another antagonist.',
        'scheduler':'Fixed role order, neutral aliases randomized; actor ordinal is opportunity_index modulo cast_size. Role timing is not randomized.'})
    log(f'Validated {len(cells)} cells, {len(evaluation_rows)} secondary summaries, source/adapter hashes and complete paired/action coverage; no behavioral aggregates read.')
    print({'cells':len(cells),'evaluations':len(evaluation_rows),'cutoff':snapshot['cutoff_utc']})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['capture','validate']);args=parser.parse_args();globals()[args.command]()
