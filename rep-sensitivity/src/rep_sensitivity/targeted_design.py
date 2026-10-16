"""Bounded post-pilot experiments; target relevance is evaluator-only."""
from dataclasses import asdict,replace
from .controls import (decision_from_claims,semantic_inventory,unique_clause_control,
                       neutral_report_control,place_near_reports,superseded_reports)
from .generation import generate_pair
from .graphs import partition
from .mechanism import critical_keys,relevance
from .reports import make_reports,repeat,deduplicate,corrupt_report,render
from .schema import canonical,digest


def coordinates(report):
    c=report.claim
    return canonical([c.task_identifier,c.candidate_identifier,c.entity_identifier])


def targets(world,reports,seed):
    decisive=critical_keys(world,reports)
    def choose(items):
        items=sorted(items,key=lambda r:r.identifier)
        return items[seed%len(items)] if items else None
    a=choose([r for r in reports if r.claim.key in decisive and r.claim.asserted_value is False])
    a=a or choose([r for r in reports if r.claim.key in decisive])
    b=choose([r for r in reports if type(r.claim.asserted_value) is bool and r.claim.key not in decisive])
    c=choose([r for r in reports if relevance(world,reports,r)['objective_favoring_infeasible_candidate']])
    # Prefer a feasible result for an infeasible candidate if no lowest objective
    # belongs to one. Neither statement entails whole-candidate feasibility.
    c=c or choose([r for r in reports if r.claim.asserted_value is True and not relevance(world,reports,r)['candidate_feasible']])
    return {'A':a,'B':b,'C':c,'COMMON':c or b}


def repeat_selected(reports,target,dose=4,paraphrase=False,split='development',position='adjacent'):
    if dose==1:return list(reports)
    # Identity selection is essential when true and false reports share a scope.
    copies=repeat([target],coordinates(target),'paraphrase' if paraphrase else 'exact',split,dose)[1:]
    position_index=next(i for i,r in enumerate(reports) if r.identifier==target.identifier)+1
    rs=list(reports);rs[position_index:position_index]=copies
    if position=='end':
        copies=[r for r in rs if r.parent_report_identifiers==(target.identifier,) and r.operation_type in ('copy','paraphrase')]
        ids={r.identifier for r in copies};rs=[r for r in rs if r.identifier not in ids]+copies
    return rs


def uniform_repeat(reports,dose,split):
    return [r for original in reports for r in repeat_selected([original],original,dose,split=split)]


def source_pairs(config):
    return [generate_pair(config['split'],i,2) for i in range(config['pair_start'],config['pair_start']+config['base_pairs'])]


def plan_pair(pair,config):
    """No model outcomes are consulted. Missing eligible targets remain explicit."""
    jobs=[];ineligible=[];local=pair['index']-config['pair_start'];phase=config['phase']
    subset=local in config['targeted_subset_indices']
    for wi in config['worlds']:
        world=pair['worlds'][wi];split=pair['split'];rs=make_reports(world,split,pair['seed'])
        ts=targets(world,rs,pair['seed']);common_class='C' if ts['C'] else 'B'
        def add(arm,reports=None,architecture='hierarchical',policy='ordinary',target=None,aliases=(),**extra):
            for rep in range(config['stochastic_repetitions']):
                trial={'suite':config['name'],'pair_id':pair['pair_id'],'world':wi,'model':config['model'],
                       'arm':arm,'repetition':rep,'organization':architecture,'policy':policy}
                trial['trial_id']=digest(trial)[:24]
                jobs.append({'trial':trial,'reports':list(rs if reports is None else reports),
                    'required':rs,'world':world,'target_key':target.claim.key if target else None,
                    'aliases':list(aliases),'common_class':common_class,'audit':{},**extra})
        common=ts['COMMON']
        add('hier_F',target=common,aliases=['hier_common1'])
        selected=('A','B','C') if phase=='development' else ('A','COMMON')
        for name in selected:
            target=ts[name]
            if target is None:
                ineligible.append({'world':wi,'target':name,'reason':'No report meets prespecified oracle relevance definition'});continue
            aliases=['hier_common4'] if name=='COMMON' or name==common_class else []
            add('hier_'+name+'4',repeat_selected(rs,target,split=split),target=target,aliases=aliases)
        add('hier_E4',uniform_repeat(rs,4,split),target=common)
        if phase=='validation':add('flat_F',architecture='flat',target=common)
        if phase!='development' or subset:
            architectures=('flat','bypass','lossless','global') if phase=='development' else ('bypass',)
            for architecture in architectures:
                add(architecture+'_F',architecture=architecture,target=common,aliases=[architecture+'_common1'])
                add(architecture+'_common4',repeat_selected(rs,common,split=split),architecture=architecture,target=common)
        if phase!='development' or wi!=0:continue
        if local<12:
            target=ts['A'] or ts['B']
            false=corrupt_report([target],target.identifier)[0]
            false=replace(false,identifier='r'+digest([pair['pair_id'],wi,'altered'])[:9],parent_report_identifiers=(target.identifier,))
            mixed=rs+[false]
            context={'world':world,'authority_rule':'The supplied task data determine truth; report assertions may be erroneous. Repetition confers no authority.'}
            add('false_visible_correct_control',target=target,extra_evidence=context)
            add('false_visible1',mixed,target=target,extra_evidence=context,injected_key=target.claim.key,true_value=target.claim.asserted_value)
            add('false_visible4',repeat_selected(mixed,false,split=split),target=target,extra_evidence=context,injected_key=target.claim.key,true_value=target.claim.asserted_value)
        if not subset:continue
        numeric=next(r for r in rs if r.claim.task_identifier=='objective' and
                     r.claim.candidate_identifier==decision_from_claims(world,rs))
        changed=replace(numeric.claim,asserted_value=numeric.claim.asserted_value+1,operation_type='assertion')
        changed_report=replace(numeric,identifier='r'+digest([pair['pair_id'],'numeric'])[:9],claim=changed,
                               text=render(changed,split),parent_report_identifiers=(numeric.identifier,),operation_type='assertion')
        numeric_decisive=decision_from_claims(world,rs,{numeric.claim.key:changed.asserted_value})!=decision_from_claims(world,rs)
        for overlap in ('high','low'):
            mixed=[replace(r,text=render(r.claim,split,0 if overlap=='high' else i%4)) for i,r in enumerate(rs+[changed_report])]
            altered=next(r for r in mixed if r.identifier==changed_report.identifier)
            for dose in (1,4):
                add('numeric_'+overlap+str(dose),repeat_selected(mixed,altered,dose,split=split),target=numeric,
                    extra_evidence={'world':world,'authority_rule':'Task data determine the numerical objective; an unsupported conflicting report does not override them.'},
                    audit={'numeric_difference':1,'counterfactual_numeric_edit_changes_choice':numeric_decisive,
                           'false_numeric_key':numeric.claim.key,'true_numeric_value':numeric.claim.asserted_value})
        for policy in ('checklist','scope'):
            add(policy+'_F',policy=policy,target=common)
            add(policy+'_common4',repeat_selected(rs,common,split=split),policy=policy,target=common)
        for dose in (2,4,8,16):
            repeated=repeat_selected(rs,common,dose,split=split)
            if dose!=4:add('dose'+str(dose),repeated,target=common,dose=dose)
            add('neutral'+str(dose),repeated,target=common,dose=dose,neutral=True)
        for dose in (4,16):
            add('end'+str(dose),repeat_selected(rs,common,dose,split=split,position='end'),target=common,dose=dose)
        add('copies_across_branches4',repeat_selected(rs,common,split=split),target=common,spread_copies=True)
        for importance in ('decisive','harmless'):
            for overlap in ('high','low'):
                mixed,audit=unique_clause_control(world,rs,split,importance+'_'+overlap,pair['seed'])
                if mixed is None:
                    ineligible.append({'world':wi,'target':importance+'_'+overlap,'reason':audit['ineligible']});continue
                anchor=next(r for r in mixed if r.identifier==audit['shared_anchor'])
                for dose in (1,4):
                    reports=repeat_selected(mixed,anchor,dose,split=split)
                    add('near_'+importance+'_'+overlap+str(dose),reports,target=anchor,audit=audit,designated_unique_key=audit['unique_scope'])
                    if importance=='decisive' and overlap=='high' and dose==4:
                        for mode in ('exact','similarity'):
                            kept=deduplicate(reports,mode)
                            add('dedup_'+mode,kept,target=anchor,audit={**audit,'distinct_claims_lost':len(set(semantic_inventory(reports))-set(semantic_inventory(kept)))},
                                designated_unique_key=audit['unique_scope'])
                        add('dedup_scope_policy',reports,policy='scope',target=anchor,audit=audit,designated_unique_key=audit['unique_scope'])
        if pair['evaluation']['family']=='version':
            current_index=next(i for i,w in enumerate(pair['worlds']) if w['version']==2)
            current=pair['worlds'][current_index]
            old=make_reports(pair['worlds'][1-current_index],split,pair['seed'])
            current_reports=make_reports(current,split,pair['seed'])
            old_target=next(r for r in old if r.claim.task_identifier=='screening')
            evidence={'authority_rule':'Only reports with effective version 2 are applicable. The task explicitly authorizes version 2; recency alone is not authority.','current_version':'2'}
            for dose in (1,4):
                reports=repeat_selected(superseded_reports(current_reports,old),old_target,dose,split=split)
                add('superseded'+str(dose),reports,target=old_target,world=current,required=current_reports,extra_evidence=evidence,
                    superseded_keys=[r.claim.key for r in old])
    return jobs,ineligible


def branches_for(job,pair):
    reports=job['reports']
    if job['trial']['organization']=='global':return [reports,reports]
    return partition(reports,pair['seed'],spread_copies=job.get('spread_copies',False))
