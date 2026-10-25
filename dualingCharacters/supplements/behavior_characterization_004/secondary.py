"""Reuse verified exposure and defender audits; do not infer a channel effect."""
from collections import defaultdict
import csv
import re
from .common import *
from .statistics import paired_worlds

def csv_rows(path):
    with path.open() as f:return list(csv.DictReader(f))

def run():
    verify_science();audit=read(HERE/'DATA_AUDIT.json');sources=read(HERE/'SECONDARY_SOURCES.json')['files'];verified={}
    for path,digest in sources.items():
        if sha256(ROOT/path)!=digest:raise ValueError('Secondary report source changed: '+path)
    old=ROOT/'supplements/long_horizon_intent_002/reports'
    exposure=read(old/'exposure_provenance.json');exposure_rows=csv_rows(old/'supervision_exposure.csv');reuse=[]
    for run_id,record in exposure['runs'].items():
        for path,digest in record['inputs'].items():
            if path not in verified:verified[path]=sha256(ROOT/path)
            if verified[path]!=digest:raise ValueError('Exposure source changed: '+path)
        if sha256(ROOT/record['detail_path'])!=record['detail_sha256']:raise ValueError('Exposure reconstruction changed')
        reuse.append(run_id)
    # Existing final-answer audits contain fully reconstructed source judgments.
    # Revalidate their completed raw trace hashes once, locally; never recompute them.
    for record in read(old/'core_intent_audit_provenance.json')['runs'].values():
        for path,digest in record.items():
            if path not in verified:verified[path]=sha256(ROOT/path)
            if verified[path]!=digest:raise ValueError('Existing defender audit trace changed')
    current=[];pairs={};eval_ids=set()
    for item in audit['secondary_evaluations']:
        if sha256(ROOT/item['summary_path'])!=item['summary_sha256']:raise ValueError('Secondary evaluation changed')
        meta=item['metadata'];cfg=meta['config'];rows=read(ROOT/item['summary_path']);families=paired_worlds(rows)
        if sha256(ROOT/'artifacts/runs'/item['run_id']/'status.json')!=item['status_sha256']:raise ValueError('Completed evaluation status changed')
        adapter=meta.get('loaded_adapter_path')
        if adapter:
            path=ROOT/adapter/'adapter_model.safetensors'
            if str(path) not in verified:verified[str(path)]=sha256(path)
            if verified[str(path)]!=meta['loaded_adapter_sha256']:raise ValueError('Evaluation checkpoint mismatch')
        paired={f:all(r['success'] for r in rows if r['family_id']==f) for f in families}
        pairs[cfg['model'],cfg['condition'],cfg['seed']]=paired;eval_ids.add(item['run_id'])
        current.append({'run_id':item['run_id'],'model':cfg['model'],'condition':cfg['condition'],'seed':cfg['seed'],
            'paired_successes':sum(paired.values()),'families':len(paired),'paired_rate':sum(paired.values())/len(paired),
            'conversation_successes':sum(r['success'] for r in rows),'conversations':len(rows),'horizon':meta['horizon'],
            'checkpoint_sha256':meta.get('loaded_adapter_sha256'),'qualification':'Secondary antagonist-free endpoint; frozen main analysis remains authoritative.'})
    transitions=[]
    for (model,condition,seed),first in pairs.items():
        if condition!='C5':continue
        for control in ('C3','C1','A1'):
            second=pairs.get((model,control,seed))
            if second is None:continue
            if set(first)!=set(second):raise ValueError('Unmatched final evaluation families')
            counts=defaultdict(int)
            for family in first:
                counts['both' if first[family] and second[family] else 'only_C5' if first[family] else 'only_control' if second[family] else 'neither']+=1
            transitions.append({'model':model,'seed':seed,'first':'C5','second':control,'families':len(first),
                **{k:counts[k] for k in ('both','only_C5','only_control','neither')},'difference':(counts['only_C5']-counts['only_control'])/len(first)})
    exposure_index={r['run_id']:r for r in exposure_rows};joins=[]
    for cell in audit['cells']:
        if not cell['cohort'].startswith('main_'):continue
        stem=cell['run_id'].removesuffix('-collect')+'-fit';candidates=[stem,stem+'-format2']
        matches=[exposure_index[k] for k in candidates if k in exposure_index]
        if len(matches)>1:raise ValueError('Ambiguous eligible exposure join')
        row={'collection_id':cell['id'],'condition':cell['condition'],'seed':cell['seed'],'round':cell['round'],
            'exposure_audit_status':'verified_existing' if matches else 'not_reconstructed_at_prior_cutoff'}
        if matches:
            match=matches[0];row.update({k:match[k] for k in ('run_id','training_input_tokens','supervised_target_tokens','loss_contributing_unique_windows','loss_contributing_unique_families','orphaned_target_tokens_masked','resume_replay_input_tokens_not_optimized','label_sources_contributing_loss')})
        joins.append(row)
    write_csv(REPORTS/'secondary_defender_results.csv',current);write_csv(REPORTS/'secondary_paired_transitions.csv',transitions);write_csv(REPORTS/'supervision_join.csv',joins)
    for name in ('clarification_audit.csv','evidence_audit.csv','clarification_exposure.csv'):
        rows=csv_rows(old/name)
        selected=[r for r in rows if r.get('run_id') in eval_ids|set(reuse)]
        write_csv(REPORTS/('reused_'+name),selected)
    write(REPORTS/'SECONDARY_PROVENANCE.json',{'report_sources':sources,'verified_raw_inputs':verified,'reused_exposure_runs':reuse,
        'missing_new_exposure_audits':[j['collection_id'] for j in joins if j['exposure_audit_status']!='verified_existing'],
        'no_new_exposure_reconstruction':True,'interpretation':'Condition/seed joins only; no causal mediation or attribution of learning outcomes to generator channels.'})

if __name__=='__main__':run()
