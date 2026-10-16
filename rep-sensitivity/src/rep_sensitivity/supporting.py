"""Targeted replay controls; requires a frozen configuration and source corpus."""
from dataclasses import asdict
from pathlib import Path
import json
from .controls import packaging,corrupt_ancestry,dedup_audit,neutral_report_control,unique_clause_control,superseded_reports
from .generation import oracle
from .graphs import partition
from .metrics import parse,score_root,score_assertions
from .models import LocalModel
from .policies import make_prompt
from .reports import thaw,repeat,registry,deduplicate,corrupt_report,ancestry_registry
from .schema import canonical,digest
from .storage import immutable_json,Ledger
from .replay import execute_requests


def run_controls(config,alias):
    if config.get('status') not in ('frozen','development_controls') or config.get('interface_version')!=5:
        raise ValueError('Supporting protocol must be frozen before held-out outcomes')
    source=Path(config['source_corpus'])
    pairs=json.loads((source/'pairs.json').read_text())
    corpus=json.loads((source/'frozen-reports.json').read_text())
    pairs=[p for p in pairs if p['index'] in config['pair_indices']]
    if config['status']=='development_controls' and any(p['split'] not in ('development','validation') for p in pairs):
        raise ValueError('Development controls may not use held-out instances')
    directory=Path('artifacts/runs')/config['name'];ledger=Ledger(directory/alias)
    immutable_json(directory/'config.json',config)
    model=LocalModel(alias,config['max_context_tokens'],config['max_output_tokens'],
                     config['temperature'],config['top_p'],config['batch_size'],True)
    for pair in pairs:
        for wi in (0,1):
            world=pair['worlds'][wi];original=thaw(corpus[pair['pair_id']]['reports'][wi])
            selected=corpus[pair['pair_id']]['selected']
            for contrast,arms in config['contrasts'].items():
                for arm in arms:
                    for repetition in range(config['stochastic_repetitions']):
                        trial={'suite':config['name'],'pair_id':pair['pair_id'],'world':wi,'model':alias,
                               'contrast':contrast,'arm':arm,'repetition':repetition}
                        trial['trial_id']=digest(trial)[:24]
                        rs=list(original);policy='ordinary';ancestry=True;extra=None;audit={};task_context=''
                        if contrast in ('deduplication','branch_placement','access','call_count','ancestry','instruction','length'):
                            rs=repeat(rs,selected,'exact',pair['split'])
                        if contrast=='packaging': rs,audit=packaging(rs,pair['split'],arm,model.tokenizer)
                        if contrast=='unique_clause':
                            rs,audit=unique_clause_control(world,rs,pair['split'],arm,pair['seed'])
                            if rs is None:
                                ledger.event('control_ineligible',trial=trial,reason=audit['ineligible']);continue
                        if contrast=='version_admission':
                            if pair['evaluation']['family']!='version' or world.get('version')!=2:
                                ledger.event('control_ineligible',trial=trial,reason='Requires version-2 workflow world');continue
                            old=thaw(corpus[pair['pair_id']]['reports'][1-wi])
                            task_context=('Explicit task update rule: effective version is 2. Version 2 replaces version 1 for this task. '
                                          'Only version-2 findings are mandatory/current. Version-1 findings are historical and inapplicable.\n')
                            if arm=='current_and_superseded':rs=superseded_reports(rs,old)
                            audit={'superseded_scopes':[r.claim.key for r in old],'effective_version':2}
                        if contrast=='deduplication':
                            audit=dedup_audit(rs,config['similarity_threshold'])
                            if arm=='exact_removal':rs=deduplicate(rs,'exact')
                            elif arm=='similarity_removal':rs=deduplicate(rs,'similarity',config['similarity_threshold'])
                            elif arm=='scope_consolidation':policy='scope'  # Model policy; no oracle grouping.
                        if contrast=='ancestry':
                            if arm=='withheld':ancestry=False
                            if arm=='corrupted_relationships':rs=corrupt_ancestry(rs,pair['seed'])
                        if contrast=='instruction':
                            ancestry=False;policy='scope' if arm=='scope_without_ancestry' else 'ordinary'
                        if contrast=='length' and arm=='neutral_padding':
                            evidential=rs
                            rs=neutral_report_control(rs,model.tokenizer)
                            def tokens(text):return len(model.tokenizer.encode(model.prepare(text),add_special_tokens=False))
                            before_branches=partition(evidential,pair['seed'])
                            after_branches=partition(rs,pair['seed'])
                            residual=[tokens(make_prompt(world,a,policy,role='manager'))-tokens(make_prompt(world,b,policy,role='manager'))
                                      for a,b in zip(after_branches,before_branches)]
                            audit={'full_manager_prompt_token_residual':residual,'same_report_slots':True}
                        if contrast=='dose':rs=repeat(rs,selected,'exact',pair['split'],{'one':1,'two':2,'four':4,'eight':8}[arm])
                        if contrast=='corruption':
                            extra=world
                            if arm!='all_correct_with_world':
                                wanted=arm=='false_objection_with_world'
                                eligible=[r for r in rs if type(r.claim.asserted_value) is bool and r.claim.asserted_value==wanted]
                                if not eligible:
                                    ledger.event('control_ineligible',trial=trial,reason='No report with required truth polarity');continue
                                target=sorted(eligible,key=lambda r:r.identifier)[pair['index']%len(eligible)]
                                audit={'injected_scope':target.claim.key,'true_value':wanted}
                                rs=corrupt_report(rs,target.identifier)
                        # Controls focus on the summary boundary, with a flat dose supplement.
                        branches=partition(rs,pair['seed'],spread_copies=arm=='different_branch')
                        if arm=='global_reviewers':branches=[rs,rs]
                        calls={};summaries=[]
                        if contrast!='dose':
                            requests=[{'trial':trial,'stage':'manager'+str(i),
                                       'prompt':task_context+make_prompt(world,b,policy,role='manager',ancestry=ancestry,extra_evidence=extra)} for i,b in enumerate(branches)]
                            calls=execute_requests(requests,model,ledger)
                            for i in range(2):
                                raw=calls[(trial['trial_id'],'manager'+str(i))]['response']
                                obj,status=parse(raw['text'],world['tie_order']+['NONE'],manager=True)
                                if raw['finish_reason']=='length':obj=None;status='truncated'
                                summaries.append({'manager':i,'summary':obj if obj else raw['text'],'parse_status':status})
                        root_reports=rs if contrast=='dose' or arm=='summaries_and_reports' else []
                        prompt=task_context+make_prompt(world,root_reports,policy,summaries=summaries or None,
                                           ancestry=ancestry,public_registry=registry(rs if contrast=='version_admission' else original),extra_evidence=extra,
                                           public_ancestry=ancestry_registry(rs) if config.get('root_ancestry_registry',False) else None)
                        calls.update(execute_requests([{'trial':trial,'stage':'root','prompt':prompt}],model,ledger))
                        raw=calls[(trial['trial_id'],'root')]['response']
                        score=score_root(raw,world,pair['evaluation']['oracle'][wi],original)
                        if any(s['parse_status']!='valid' for s in summaries):score['correct']=False;score['operational_failure']=True
                        obj,_=parse(raw['text'],world['tie_order']+['NONE'])
                        if contrast=='corruption' and 'injected_scope' in audit:
                            score['false_assertion_adopted']=any(k==audit['injected_scope'] and v!=audit['true_value'] for k,v,refs in obj['assertions']) if obj else False
                        if contrast=='unique_clause':
                            key=audit['unique_scope']
                            truth=next(c.asserted_value for r in rs for c in r.claims() if c.key==key)
                            retained=[any(k==key and type(v)==type(truth) and v==truth for k,v,refs in s['summary']['assertions'])
                                      for s in summaries if isinstance(s['summary'],dict)]
                            score['unique_clause_retained']=any(retained)
                            score['unique_clause_denominator']=1
                        if contrast=='version_admission':
                            score['superseded_assertions_emitted']=sum(k in audit['superseded_scopes'] for k,v,refs in obj['assertions']) if obj else 0
                            # Emitting a historical claim is not necessarily adopting it for a decision.
                            old_choice=pair['evaluation']['oracle'][1-wi]['answer']
                            score['choice_matches_superseded_when_distinct']=(score['choice']==old_choice) if old_choice!=pair['evaluation']['oracle'][wi]['answer'] else None
                        result={**trial,**score,'kind':pair['evaluation']['kind'],'family':pair['evaluation']['family'],
                                'decision_changed':pair['evaluation']['decision_changed'],'audit':audit,
                                'summary_scores':[{**score_assertions(s['summary'] if isinstance(s['summary'],dict) else None,b),
                                                   'parse_status':s['parse_status']} for s,b in zip(summaries,branches)],
                                'delivered_reports':len(rs),'retained_distinct_scopes':len(registry(rs)),
                                'input_tokens':sum(c['response']['input_tokens'] for c in calls.values()),
                                'output_tokens':sum(c['response']['output_tokens'] for c in calls.values()),
                                'inference_seconds_allocated':sum(c['response']['allocated_inference_seconds'] for c in calls.values()),
                                'request_hashes':[c['request_hash'] for c in calls.values()]}
                        immutable_json(directory/alias/'scores'/(trial['trial_id']+'.json'),result)
