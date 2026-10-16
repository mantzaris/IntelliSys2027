"""Targeted controls; transformations never consult evaluator correctness labels."""
from dataclasses import replace
from difflib import SequenceMatcher
import random
from .schema import canonical, digest
from .reports import deduplicate, overlap_render, repeat, scope_consolidate, render
from .graphs import partition

CONTROL_ARMS = {
    "packaging": ["low_overlap", "high_overlap"],
    "deduplication": ["exact_removal", "similarity_removal", "scope_consolidation"],
    "branch_placement": ["same_branch", "different_branch"],
    "copy_branch_placement": ["same_branch", "different_branch"],
    "access": ["summaries_only", "summaries_and_reports"],
    "call_count": ["partition_managers", "global_reviewers"],
    "length": ["neutral_padding", "evidential_repetition"],
    "ancestry": ["authentic", "withheld", "corrupted_relationships"],
    "instruction": ["ordinary_without_ancestry", "scope_without_ancestry"],
    "corruption": [policy+'_'+case for policy in ('ordinary','checklist','scope')
                   for case in ('all_correct_with_world','false_favorable_with_world','false_objection_with_world')],
    "unique_clause": ["decisive_high", "decisive_low", "harmless_high", "harmless_low"],
    "version_admission": ["current_only", "current_and_superseded"],
    "dose": ["one", "two", "four", "eight"]
}


def semantic_inventory(reports):
    return sorted({canonical([c.scope(), c.asserted_value]) for r in reports for c in r.claims()})


def place_near_reports(reports, seed, separate=False):
    """Move a prespecified distinct scope, keeping its copies with their parent.

    Prefer reports for different machines of the same candidate. Selection uses
    scope and identifiers, never truth or final-decision relevance. The changed
    branch load is recorded rather than treated as a perfectly matched control.
    """
    originals=sorted((r for r in reports if not r.parent_report_identifiers),key=lambda r:r.identifier)
    eligible=[(a,b) for i,a in enumerate(originals) for b in originals[i+1:]
              if a.claim.task_identifier==b.claim.task_identifier and a.claim.key!=b.claim.key]
    preferred=[(a,b) for a,b in eligible if a.claim.task_identifier=='resource' and
               a.claim.candidate_identifier==b.claim.candidate_identifier and
               a.claim.entity_identifier!=b.claim.entity_identifier]
    choices=preferred or eligible
    if not choices:raise ValueError('No distinct scopes in a shared task family')
    first,second=choices[seed%len(choices)]
    branches=partition(reports,seed)
    owner=next(i for i,rs in enumerate(branches) if any(r.identifier==first.identifier for r in rs))
    moved={second.identifier}
    # Include descendants even if a later corpus permits more than one copy hop.
    while True:
        expanded=moved|{r.identifier for r in reports if moved.intersection(r.parent_report_identifiers)}
        if expanded==moved:break
        moved=expanded
    if separate:
        assignment={r.identifier:i for i,rs in enumerate(branches) for r in rs}
        branches=[[],[]]
        for r in reports:
            branches[1-owner if r.identifier in moved else assignment[r.identifier]].append(r)
    return branches,{'relevant_report_identifiers':[first.identifier,second.identifier],
                     'relevant_scope_keys':[first.claim.key,second.claim.key],
                     'distinct_scopes':True,'same_candidate_different_resource':bool(preferred),
                     'branch_report_counts':list(map(len,branches)),
                     'moved_report_identifiers':sorted(moved) if separate else []}


def decision_from_claims(world, reports, override=None):
    """Evaluator-only conjunction reference; never a model prompt or policy."""
    candidates={cid:{'mandatory':[], 'objective':None} for cid in world['tie_order']}
    for r in reports:
        for c in r.claims():
            value=override[c.key] if override and c.key in override else c.asserted_value
            target=candidates[c.candidate_identifier]
            if c.task_identifier=='objective':target['objective']=value
            else:target['mandatory'].append(value)
    eligible=[cid for cid,vals in candidates.items() if vals['mandatory'] and all(v is True for v in vals['mandatory']) and vals['objective'] is not None]
    return min(eligible,key=lambda cid:(candidates[cid]['objective'],world['tie_order'].index(cid))) if eligible else 'NONE'


def unique_clause_control(world,reports,split,arm,seed):
    """All-correct reports; classify clause relevance by a declared Boolean flip.

    Each target shares one existing claim with an anchor report. Only rendering
    differs between high/low arms; all distinct evidence, slots and order agree.
    """
    baseline=decision_from_claims(world,reports)
    consequential=arm.startswith('decisive')
    decisive=[r for r in reports if type(r.claim.asserted_value) is bool and
              decision_from_claims(world,reports,{r.claim.key:not r.claim.asserted_value})!=baseline]
    harmless=[r for r in reports if type(r.claim.asserted_value) is bool and r not in decisive]
    anchor=sorted(decisive,key=lambda r:r.identifier)[seed%len(decisive)] if decisive else None
    matching=[r for r in harmless if anchor and r.claim.task_identifier==anchor.claim.task_identifier and
              r.claim.entity_identifier==anchor.claim.entity_identifier]
    eligible=decisive if consequential else (matching or harmless)
    if not eligible:return None,{'ineligible':'No clause of requested relevance in this world'}
    target=sorted(eligible,key=lambda r:r.identifier)[seed%len(eligible)]
    common=next(r for r in reports if r.identifier!=target.identifier and r.claim.task_identifier=='objective')
    high=arm.endswith('high')
    changed=[]
    for index,r in enumerate(reports):
        variant=0 if high else index%4
        text=render(r.claim,split,variant)
        if r.identifier==target.identifier:
            text=render(common.claim,split,0 if high else 3)+' '+text
            r=replace(r,additional_claims=(common.claim,),parent_report_identifiers=(common.identifier,),operation_type='partial_overlap')
        changed.append(replace(r,text=text))
    assert semantic_inventory(changed)==semantic_inventory(reports)
    return changed,{'unique_scope':target.claim.key,'shared_scope':common.claim.key,
                    'counterfactual_flip_changes_answer':consequential,'reference_answer':baseline,
                    'decisive_harmless_family_entity_matched':bool(matching),
                    'target_report':target.identifier,'shared_anchor':common.identifier}


def superseded_reports(current,old):
    """Admit old versioned reports with accurate provenance, never overwrite them."""
    if not all(r.claim.effective_time_or_version=='2' for r in current):
        raise ValueError('Version-admission control requires explicit current version 2')
    if not all(r.claim.effective_time_or_version=='1' for r in old):
        raise ValueError('Historical report set must be version 1')
    return list(current)+list(old)


def lineage_edges(reports):
    return {(p,r.identifier) for r in reports for p in r.parent_report_identifiers} | {
        (s,r.claim.verification_execution_identifier) for r in reports for s in r.claim.source_identifiers}


def corrupt_ancestry(reports, seed):
    """Deliberately changes dependence, not merely source/parent identifier names."""
    rng=random.Random(seed)
    originals=[r for r in reports if not r.parent_report_identifiers]
    out=[]
    for index,r in enumerate(reports):
        if r.parent_report_identifiers:
            # A copied statement is falsely presented as an independent extraction/root.
            new=replace(r.claim,source_identifiers=('independent_'+r.identifier,),
                        verification_execution_identifier='fresh_'+r.identifier)
            out.append(replace(r,claim=new,parent_report_identifiers=(),operation_type='verification'))
        else:
            # Distinct scopes are falsely linked as derived from one previous report.
            parent=originals[0].identifier
            out.append(r if r.identifier==parent else replace(r,parent_report_identifiers=(parent,),operation_type='relay'))
    assert lineage_edges(out)!=lineage_edges(reports)
    assert semantic_inventory(out)==semantic_inventory(reports)
    return out


def packaging(reports,split,level,tokenizer=None):
    changed=overlap_render(reports,split,'high' if level=='high_overlap' else 'low')
    assert semantic_inventory(changed)==semantic_inventory(reports)
    assert [r.identifier for r in changed]==[r.identifier for r in reports]
    lengths=[len(tokenizer.encode(r.text)) if tokenizer else len(r.text) for r in changed]
    similarities=[SequenceMatcher(None,a.text,b.text).ratio() for i,a in enumerate(changed) for b in changed[i+1:]]
    return changed, {'lengths':lengths,'length_unit':'tokens' if tokenizer else 'characters',
                     'mean_pairwise_similarity':sum(similarities)/len(similarities) if similarities else 0,
                     'distinct_claims':len(semantic_inventory(changed))}


def unique_clause_reports(reports):
    """Add identical, non-evidential framing; keep the scoped clause verbatim."""
    prefix='This report records one required verification finding for the supplied candidate set. '
    suffix=' This report alone does not establish overall feasibility.'
    return [replace(r,text=prefix+'Scoped finding: '+r.text+suffix) for r in reports]


def neutral_padding(tokenizer, target_tokens):
    """Clearly non-evidential status material; measure residual tokenizer mismatch."""
    text='Administrative status: message delivered. This status contains no task result. '
    padding=''
    while len(tokenizer.encode(padding,add_special_tokens=False)) < target_tokens:
        padding+=text
    tokens=tokenizer.encode(padding,add_special_tokens=False)
    # Token-level truncation is allowed only for deliberately generated neutral filler.
    padding=tokenizer.decode(tokens[:target_tokens])
    return padding, len(tokenizer.encode(padding,add_special_tokens=False))-target_tokens


def neutral_report_control(reports,tokenizer):
    """Keep report slots/ordering; replace only added copies by neutral messages."""
    changed=[]
    for r in reports:
        if r.operation_type in ('copy','paraphrase'):
            count=len(tokenizer.encode(r.text,add_special_tokens=False))
            text,_=neutral_padding(tokenizer,count)
            r=replace(r,text=text,operation_type='administrative')
        changed.append(r)
    return changed


def dedup_audit(reports,threshold=0.9):
    baseline=set(semantic_inventory(reports))
    results={}
    for mode in ('exact','similarity'):
        retained=deduplicate(reports,mode,threshold)
        inv=set(semantic_inventory(retained))
        results[mode]={'retained_reports':len(retained),'distinct_claims_lost':len(baseline-inv),
                       'retained_ids':[r.identifier for r in retained]}
    consolidated=scope_consolidate(reports)
    results['scope']={'retained_groups':len(consolidated),'distinct_claims_lost':0}
    return results
