"""Deterministic illustrative core traces; never a human-rated intent result."""
from collections import defaultdict
from hashlib import sha256 as hash_bytes
from pathlib import Path
import json
from pcc.resources import sha256
from pcc.environment import make_family
from supplements.review_001.common import stream,trace_path
from .common import ROOT,REPORTS,ARTIFACTS,read,write,utc
from .trajectory_analysis import correctness


def ranking(value):return hash_bytes(('intent002-core-illustration-v1:'+value).encode()).hexdigest()


def selections(audit):
    episodes=audit['episodes'];final={(r['family_id'],r['world']):r for r in audit['final_audit']};groups=defaultdict(list)
    for e in episodes:
        curve=correctness(e);base={'family_id':e['family_id'],'world':e['world']}
        if curve.all():groups['uninterrupted_preservation'].append({**base,'turns':[1,32,64]})
        regressions=[r for r in e['regressions'] if r['event_kind']=='filler' and not r['truth_changed']]
        if regressions:groups['spontaneous_regression'].append({**base,'turns':[regressions[0]['turn']-1,regressions[0]['turn']]})
        if e['world']=='authorized' and curve[31]:groups['appropriate_authorized_update'].append({**base,'turns':[31,32]})
        if final[e['family_id'],e['world']]['unnecessary_clarification']:groups['unnecessary_clarification'].append({**base,'turns':[64]})
        recovered=[s for s in e['failure_spells'] if s['onset_turn']>1 and s['recovered_turn'] is not None]
        if recovered:
            s=recovered[0];groups['observed_recovery'].append({**base,'turns':[s['onset_turn'],s['recovered_turn']]})
    selected=[]
    for category in ('uninterrupted_preservation','spontaneous_regression','appropriate_authorized_update','unnecessary_clarification','observed_recovery'):
        candidates=groups[category];families={e['family_id'] for e in candidates}
        chosen=min(candidates,key=lambda e:(ranking(category+':'+e['family_id']),e['world'])) if candidates else None
        selected.append({'category':category,'qualifying_families':len(families),'denominator_families':240,'qualifying_conversations':len(candidates),'selected':chosen})
    return selected


def main():
    all_items=[];provenance={};semantic=[]
    for path in sorted((ARTIFACTS/'core_trajectory').glob('*.json')):
        audit=read(path);header=audit['metadata']
        if header['model']!='qwen' or header['condition'] not in ('C1','C3','C5'):continue
        selected=selections(audit);run_id=header['run_id'];source=trace_path(ROOT/'artifacts/runs'/run_id/'evaluation.jsonl')
        cache=ARTIFACTS/'illustrations'/f'{run_id}.json';signature={'audit_sha256':sha256(path),'selection':selected}
        if cache.exists() and read(cache)['signature']==signature:packet=read(cache)
        else:
            wanted={(e['selected']['family_id'],world,turn) for e in selected if e['selected'] for world in ('authorized','hypothetical') for turn in e['selected']['turns']}
            found={}
            for row in stream(source):
                k=row['family_id'],row['world'],row['turn']
                if k in wanted:
                    if k in found:raise ValueError('Duplicate illustrative source turn')
                    found[k]=row
            if set(found)!=wanted:raise ValueError('Illustration missing actual source trace')
            packet={'signature':signature,'source_path':str(source.relative_to(ROOT)),'source_sha256':sha256(source),'rows':list(found.values())};write(cache,packet)
        lookup={(r['family_id'],r['world'],r['turn']):r for r in packet['rows']}
        for chosen in selected:
            records=[]
            if chosen['selected']:
                f=chosen['selected']['family_id']
                for world in ('authorized','hypothetical'):
                    for turn in chosen['selected']['turns']:
                        row=lookup[f,world,turn];body=json.loads(row['prompt'][-1]['content']);scenario=make_family('test',int(f.split('-')[-1]),64)[0 if world=='authorized' else 1]
                        records.append({'family_id':f,'world':world,'turn':turn,'current_user_message':scenario.messages[turn-1].text,
                          'actual_structured_output':row['generation']['parsed'],'time_specific_target':row['target'],'metrics':row['metrics'],
                          'visible_source_indices':[m['index'] for m in body['sources']],
                          'prior_ledger_or_gold_used_by_policy':False})
            all_items.append({**header,**chosen,'observations':records})
        # Semantic-source illustrations use completed final-prompt caches only.
        final_rows=read(ARTIFACTS/'core_audits/evaluations'/f'{run_id}.json');by_final={(r['family_id'],r['world']):r for r in final_rows}
        for category in ('assistant_authority','nonexistent_or_future','wrong_explicit_user_authorization','anaphoric_user_reaffirmation_needs_semantic_review','generic_user_request_not_authorization','alternative_unsuperseded_user_authorization'):
            candidates=[(r,ref) for r in audit['final_audit'] for ref in r['references'] if ref[category]]
            picked=sorted(candidates,key=lambda pair:ranking(':'.join([category,pair[0]['family_id'],pair[0]['world'],pair[1]['slot']])))[:2]
            examples=[]
            for r,ref in picked:
                final_row=by_final[r['family_id'],r['world']];body=json.loads(final_row['prompt'][-1]['content']);visible={m['index']:m for m in body['sources']}
                scenario=make_family('test',int(r['family_id'].split('-')[-1]),64)[0 if r['world']=='authorized' else 1]
                users={m.index:m.public() for m in scenario.messages};source_message=visible.get(ref['reference']) or users.get(ref['reference'])
                examples.append({'family_id':r['family_id'],'world':r['world'],**ref,'referenced_message':source_message,
                  'reference_text_status':'actual visible/source user text' if source_message else 'assistant message not present in final prompt; wording not reconstructed',
                  'canonical_user_message':users.get(ref['canonical']),
                  'assessment':'Anaphoric reaffirmation may support a decision only with its antecedent; human semantic assessment remains pending.' if category=='anaphoric_user_reaffirmation_needs_semantic_review' else 'Structural source-role/category evidence only; no automatic canonical rescoring.'})
            semantic.append({**header,'category':category,'reference_count':len(candidates),'reference_denominator':2880,'examples':examples})
        provenance[run_id]={'audit_sha256':sha256(path),'source_sha256':packet['source_sha256'],'selected_raw_cache_sha256':sha256(cache)}
    write(REPORTS/'core_illustrations.json',all_items);write(REPORTS/'semantic_source_examples.json',semantic)
    lines=['# Structured-core illustrations — exploratory, not human validation','',
      'One lowest-hash family per declared category and completed Qwen C1/C3/C5 seed. Both worlds and actual selected responses are retained. Counts describe all 240 families; examples are illustrative, not a prevalence sample. Intermediate targets use the time-varying oracle. Recovery states are endogenous and differ by method. Fresh natural-language examples remain pending.','',
      '| Condition | Seed | Category | Families / 240 | Selected family |','|---|---:|---|---:|---|']
    for r in all_items:lines.append(f'| {r["condition"]} | {r["seed"]} | {r["category"]} | {r["qualifying_families"]} | {r["selected"]["family_id"] if r["selected"] else "None qualify"} |')
    lines+=['','Actual outputs, dynamic targets and paired worlds: [core_illustrations.json](core_illustrations.json). Source-reference examples: [semantic_source_examples.json](semantic_source_examples.json). No hidden intention or causal repair claim is inferred.']
    (REPORTS/'ILLUSTRATIVE_APPENDIX.md').write_text('\n'.join(lines)+'\n')
    write(REPORTS/'illustration_provenance.json',{'generated_utc':utc(),'inputs':provenance,'source_sha256':sha256(Path(__file__)),'selection_uses_outcome_categories':True,'qualification':'Transparent category-conditioned illustration only; never a primary estimate or blinded sample'})
    print({'condition_seed_runs':len(provenance),'category_rows':len(all_items),'new_natural_language_examples':0})


if __name__=='__main__':main()
