"""Paired contrasts and stratified base-cluster uncertainty, never row bootstrap."""
from collections import defaultdict
import csv
import gzip
import json
import math
from pathlib import Path
import statistics
import importlib.metadata
from .schema import canonical, digest
from .reports import thaw,repeat
from .graphs import partition
from .metrics import parse,score_assertions


def average(xs):
    values = list(xs)
    return sum(values) / len(values) if values else None


def bootstrap(values, strata, replicates=10000, seed=20271015, difference=False):
    """One value per base cluster. H2 separately contrasts changing vs preserving."""
    import numpy as np
    empty={"estimate":None,"lower":None,"upper":None,"clusters":len(values),"cluster_sd":None,
           "degenerate_bootstrap":None}
    if not values: return empty
    groups = defaultdict(list)
    for key, val in values.items(): groups[tuple(strata[key])].append(val)
    rng = np.random.default_rng(seed)
    sums = np.zeros(replicates)
    denom = len(values)
    if difference:
        n_change = sum(len(v) for k, v in groups.items() if k[-1])
        n_preserve = denom - n_change
        if not n_change or not n_preserve:
            return empty
    estimate = 0.0
    for stratum, vals in groups.items():
        a = np.asarray(vals, dtype=float)
        weight = len(a) / denom
        if difference: weight = (len(a)/n_change if stratum[-1] else -len(a)/n_preserve)
        sums += rng.choice(a, size=(replicates, len(a)), replace=True).mean(axis=1) * weight
        estimate += a.mean() * weight
    lo, hi = np.quantile(sums, [0.025, 0.975])
    sd = statistics.stdev(values.values()) if len(values) > 1 else None
    return {"estimate": float(estimate), "lower": float(lo), "upper": float(hi),
            "clusters": len(values), "cluster_sd": sd,
            "degenerate_bootstrap":bool(lo==hi)}


def repetition_values(rows, condition=None, interaction=False, pair_failure=False):
    """Average within each paired cell before giving each base cluster one vote."""
    units = defaultdict(dict)
    for r in rows:
        key = (r["pair_id"], r["model"], r["policy"], r["organization"], r["repetition"])
        if not pair_failure: key += (r["world"],)
        if pair_failure:
            units[key].setdefault(r["condition"], {})[r["world"]] = bool(r["correct"])
        else: units[key][r["condition"]] = 1 - int(r["correct"])
    effects = defaultdict(list)
    wanted = [condition] if condition else ["exact", "paraphrase"]
    for key, arms in units.items():
        if pair_failure:
            arms = {c: 1-int(all(v.values())) for c, v in arms.items() if set(v) == {0, 1}}
        if not all(c in arms for c in ["single"] + wanted): continue
        harm = average(arms[c] for c in wanted) - arms["single"]
        if interaction:
            effects[(key[0],key[3])].append(harm)
        else: effects[key[0]].append(harm)
    if interaction:
        return {p: average(effects[(p,"hierarchical")])-average(effects[(p,"flat")])
                for p in {k[0] for k in effects} if (p,"hierarchical") in effects and (p,"flat") in effects}
    return {p: average(v) for p,v in effects.items()}


def changed_keys(corpus, pair_id, world):
    current, other = [thaw(corpus[pair_id]["reports"][w]) for w in (world,1-world)]
    def coord(r): return (r.claim.task_identifier,r.claim.candidate_identifier,r.claim.entity_identifier)
    old = {coord(r):r.claim for r in other}
    return {r.claim.key for r in current if coord(r) not in old or
            old[coord(r)].scope()!=r.claim.scope() or old[coord(r)].asserted_value!=r.claim.asserted_value}


def load_complete(directory):
    directory = Path(directory)
    manifest = json.loads((directory/"manifest.json").read_text())
    corpus = json.loads((directory/"frozen-reports.json").read_text())
    pairs={p['pair_id']:p for p in json.loads((directory/'pairs.json').read_text())}
    config = manifest["config"]
    expected = len(config["worlds"])*len(config["repetition_conditions"])*len(config["organizations"])*len(config["policies"])*config["stochastic_repetitions"]
    rows, incomplete = [], []
    for alias in config["models"]:
        for path in sorted((directory/alias/"scores").glob("*.json")):
            records = json.loads(path.read_text())
            if len(records) != expected or len({r['trial_id'] for r in records}) != expected:
                incomplete.append(str(path)); continue
            for r in records:
                # Raw responses and original scores remain immutable. Analysis v2
                # equates numeric 4 and 4.0, while preserving Boolean type safety.
                original=thaw(corpus[r['pair_id']]['reports'][r['world']])
                reports=repeat(original,corpus[r['pair_id']]['selected'],r['condition'],config['split'])
                pair=pairs[r['pair_id']]
                branches=partition(reports,pair['seed'])
                for key in r['request_hashes']:
                    call=json.loads(gzip.decompress((directory/r['model']/'calls'/(key+'.json.gz')).read_bytes()))
                    manager=call['stage']!='root'
                    obj,_=parse(call['response']['text'],pair['worlds'][r['world']]['tie_order']+['NONE'],manager=manager)
                    if call['response']['finish_reason']=='length':obj=None
                    if manager:
                        index=int(call['stage'].replace('manager',''))
                        r['summary_scores'][index].update(score_assertions(obj,branches[index]))
                    else:
                        r.update(score_assertions(obj,reports))
                        r['choice_confidence']=obj['probabilities'].get(obj['choice']) if obj and r['probability_valid'] else None
                keys=changed_keys(corpus,r['pair_id'],r['world'])
                retained=set(k for s in r['summary_scores'] for k in s['retained_keys'])
                r['changed_scope_denominator']=len(keys)
                r['changed_scope_retained']=len(keys&retained) if r['organization']=='hierarchical' else None
            rows.extend(records)
    return manifest, rows, incomplete


def policy_difference(rows, outcome, condition_filter=lambda r: True):
    cells=defaultdict(dict)
    for r in rows:
        if not condition_filter(r): continue
        key=(r['pair_id'],r['model'],r['condition'],r['organization'],r['world'],r['repetition'])
        val=outcome(r)
        if val is not None: cells[key][r['policy']]=val
    effects=defaultdict(list)
    for key, v in cells.items():
        if 'scope' in v and 'checklist' in v: effects[key[0]].append(v['scope']-v['checklist'])
    return {p:average(v) for p,v in effects.items()}


def summarize(directory, output, replicates=10000):
    directory, output = Path(directory), Path(output)
    output.mkdir(parents=True,exist_ok=True)
    manifest, rows, incomplete = load_complete(directory)
    summary=[]
    group=defaultdict(list)
    for r in rows: group[(r['kind'],r['model'],r['organization'],r['policy'],r['condition'])].append(r)
    for (kind,model,org,policy,condition), rs in sorted(group.items()):
        correct=sum(r['correct'] for r in rs)
        summary.append({'kind':kind,'model':model,'organization':org,'policy':policy,'condition':condition,
                        'n':len(rs),'clusters':len({r['pair_id'] for r in rs}), 'correct':correct,
                        'accuracy':correct/len(rs), 'invalid_selection_rate':average(r['invalid_selection'] for r in rs),
                        'operational_failure_rate':average(r['operational_failure'] for r in rs),
                        'valid_probability_rate':average(r['probability_valid'] for r in rs),
                        'calibration_denominator':sum(r['probability_valid'] for r in rs),
                        'candidate_selection_denominator':sum(r['choice'] not in (None,'NONE','INSUFFICIENT') for r in rs),
                        'invalid_selected_candidates':sum(r['invalid_selection'] for r in rs),
                        'emitted_claim_denominator':sum(r['emitted_claims'] for r in rs),
                        'scope_transfer_count':sum(r['scope_transfer_count'] for r in rs),
                        'incompatible_scope_merge_count':sum(r['incompatible_scope_merge_count'] for r in rs),
                        'unconsolidated_equivalent_count':sum(r['unconsolidated_equivalent_count'] for r in rs),
                        'mean_brier':average(r['brier'] for r in rs if r['brier'] is not None),
                        'mean_log_loss':average(r['log_loss'] for r in rs if r['log_loss'] is not None),
                        'input_tokens_per_decision':average(r['input_tokens'] for r in rs),
                        'output_tokens_per_decision':average(r['output_tokens'] for r in rs),
                        'allocated_seconds_per_decision':average(r['inference_seconds_allocated'] for r in rs),
                        'tokens_per_correct':sum(r['input_tokens']+r['output_tokens'] for r in rs)/correct if correct else None,
                        'changed_scope_retention_on_consequential_pairs':
                            sum(r['changed_scope_retained'] for r in rs if r['decision_changed'])/
                            max(1,sum(r['changed_scope_denominator'] for r in rs if r['decision_changed'])) if org=='hierarchical' else None,
                        'summary_retention':sum(s['retained_count'] for r in rs for s in r['summary_scores'])/
                            max(1,sum(s['required_claims'] for r in rs for s in r['summary_scores'])) if org=='hierarchical' else None})
    paired=defaultdict(dict)
    for r in rows:
        key=tuple(r[k] for k in ('kind','model','organization','policy','condition','decision_changed','pair_id','repetition'))
        paired[key][r['world']]=r['correct']
    pair_groups=defaultdict(list)
    for key,worlds in paired.items():
        if set(worlds)=={0,1}:pair_groups[key[:6]].append((key[6],all(worlds.values())))
    pair_summary=[dict(zip(('kind','model','organization','policy','condition','decision_changed'),key),
                       paired_cells=len(vals),clusters=len({pid for pid,ok in vals}),
                       both_worlds_correct=sum(ok for pid,ok in vals),paired_accuracy=average(ok for pid,ok in vals))
                  for key,vals in sorted(pair_groups.items())]
    confidence_cells=defaultdict(dict)
    for r in rows:
        key=tuple(r[k] for k in ('kind','model','organization','policy','pair_id','world','repetition'))
        confidence_cells[key][r['condition']]=r
    confidence_groups=defaultdict(list)
    for key,arms in confidence_cells.items():
        for condition in ('exact','paraphrase'):
            if 'single' not in arms or condition not in arms:continue
            a,b=arms[condition],arms['single']
            valid=a['choice_confidence'] is not None and b['choice_confidence'] is not None
            confidence_groups[key[:4]+(condition,)].append({
                'pair_id':key[4],'same_choice':a['choice']==b['choice'],
                'confidence_delta':a['choice_confidence']-b['choice_confidence'] if valid and a['choice']==b['choice'] else None})
    confidence_summary=[]
    for key,vals in sorted(confidence_groups.items()):
        deltas=[v['confidence_delta'] for v in vals if v['confidence_delta'] is not None]
        confidence_summary.append(dict(zip(('kind','model','organization','policy','condition'),key),
            matched_cells=len(vals),same_choice_cells=sum(v['same_choice'] for v in vals),
            valid_same_choice_distributions=len(deltas),mean_confidence_delta_same_choice=average(deltas),
            interpretation='Descriptive conditioning on unchanged choice; not a primary causal contrast'))
    contrasts=[]
    for kind in sorted({r['kind'] for r in rows}):
        models=sorted({r['model'] for r in rows if r['kind']==kind})
        for model in models+(['equal_model_average'] if len(models)>1 else []):
            selected=[r for r in rows if r['kind']==kind and (model=='equal_model_average' or r['model']==model)]
            if model=='equal_model_average':
                by_pair=defaultdict(set)
                for r in selected: by_pair[r['pair_id']].add(r['model'])
                selected=[r for r in selected if by_pair[r['pair_id']]==set(models)]
            strata={r['pair_id']:(r['family'],r['decision_changed']) for r in selected}
            contrasts_spec={
                'H1_exact': repetition_values(selected,'exact'),
                'H1_paraphrase': repetition_values(selected,'paraphrase'),
                'H2': repetition_values(selected,pair_failure=True),
                'H3': repetition_values(selected,interaction=True),
                'H4_error':policy_difference(selected,lambda r:1-int(r['correct']),lambda r:r['decision_changed'] and r['condition']!='single'),
                'H4_retention':policy_difference(selected,lambda r:r['changed_scope_retained']/r['changed_scope_denominator'] if r['changed_scope_retained'] is not None and r['changed_scope_denominator'] else None,
                                                lambda r:r['decision_changed'] and r['organization']=='hierarchical')}
            for contrast, vals in contrasts_spec.items():
                contrasts.append({'kind':kind,'model':model,'contrast':contrast,
                                  **bootstrap(vals,strata,replicates=replicates,difference=contrast=='H2')})
    guardrails=[]
    for kind in sorted({r['kind'] for r in rows}):
        for model in sorted({r['model'] for r in rows if r['kind']==kind}):
            selected=[r for r in rows if r['kind']==kind and r['model']==model]
            vals=policy_difference(selected,lambda r:1-int(r['correct']),lambda r:not r['decision_changed'])
            strata={r['pair_id']:(r['family'],r['decision_changed']) for r in selected}
            guardrails.append({'kind':kind,'model':model,'comparison':'scope - checklist error on preserving pairs',
                               'provisional_margin':0.05,**bootstrap(vals,strata,replicates=replicates)})
    competence=[]
    for model in sorted({r['model'] for r in rows}):
        for kind in ('schedule','workflow'):
            rs=[r for r in rows if r['model']==model and r['kind']==kind and r['organization']=='flat' and r['policy']=='ordinary' and r['condition']=='single']
            competence.append({'model':model,'kind':kind,'n':len(rs),'accuracy':average(r['correct'] for r in rs),
                               'passes_85_percent':average(r['correct'] for r in rs)>=0.85 if rs else None})
    for filename, data in [('summary.csv',summary),('contrasts.csv',contrasts),('competence.csv',competence),
                           ('paired_correctness.csv',pair_summary),('confidence_changes.csv',confidence_summary),('guardrails.csv',guardrails)]:
        if data:
            with (output/filename).open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n'); writer.writeheader(); writer.writerows(data)
    result={'suite':manifest['config']['name'],'manifest_sha256':digest(manifest),
            'planned_trajectories':manifest['trajectories'],'analyzed_trajectories':len(rows),
            'complete':len(rows)==manifest['trajectories'],'excluded_incomplete_score_files':incomplete,
            'source_scores_sha256':digest([json.loads(p.read_text()) for p in sorted(directory.glob('*/scores/*.json'))]),
            'summary':summary,'contrasts':contrasts,'competence':competence,
            'paired_correctness':pair_summary,'confidence_changes':confidence_summary,
            'guardrails':guardrails,
            'interval_caution':'A degenerate empirical bootstrap interval indicates no sampled variation in the contrast; it does not prove zero population effect.',
            'analysis_settings':{'bootstrap_replicates':replicates,'seed':20271015,'cluster':'base_pair','p_values':None,
                                 'claim_scoring_version':2,'claim_scoring_source_sha256':digest(Path(__file__).with_name('metrics.py').read_text()),
                                 'analysis_source_sha256':digest(Path(__file__).read_text()),
                                 'dependencies':{p:importlib.metadata.version(p) for p in ('numpy','matplotlib')}}}
    (output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    # Compact trial data preserves numerical traceability without duplicating prompts.
    fields=['trial_id','pair_id','kind','family','decision_changed','model','world','condition','organization','policy','repetition','correct','choice','oracle_choice','operational_failure','input_tokens','output_tokens','inference_seconds_allocated']
    with (output/'decisions.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(rows)
    figures(result,output)
    return result


def figures(result, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(10,7),layout='constrained')
    for ax,ids,title in [(axes[0,0],['H1_exact','H1_paraphrase'],'Paired repetition harm'),
                         (axes[0,1],['H3'],'Hierarchy interaction')]:
        data=[r for r in result['contrasts'] if r['kind']=='schedule' and r['contrast'] in ids and r['estimate'] is not None]
        for i,r in enumerate(data):
            ax.errorbar(r['estimate'],i,xerr=[[max(0,r['estimate']-r['lower'])],[max(0,r['upper']-r['estimate'])]],fmt='o')
        ax.set_yticks(range(len(data)),[r['model']+' '+r['contrast'] for r in data]);ax.axvline(0,color='grey',lw=1)
        ax.set_title(title);ax.set_xlabel('Error-rate difference; cluster 95% CI')
    data=[r for r in result['summary'] if r['kind']=='schedule' and r['organization']=='hierarchical']
    axes[1,0].bar(range(len(data)),[r['changed_scope_retention_on_consequential_pairs'] for r in data])
    axes[1,0].set_xticks(range(len(data)),[r['model']+'\n'+r['policy']+'\n'+r['condition'] for r in data],rotation=40,ha='right',fontsize=6)
    axes[1,0].set_ylim(0,1);axes[1,0].set_title('Changed-scope retention; consequential pairs')
    data=[r for r in result['summary'] if r['kind']=='schedule']
    models=sorted({r['model'] for r in data});colors={m:plt.get_cmap('tab10')(i) for i,m in enumerate(models)}
    resource_groups=defaultdict(list)
    for r in data:resource_groups[(r['model'],r['organization'],r['policy'])].append(r)
    labeled=set()
    for (model,organization,policy),rs in resource_groups.items():
        denominator=sum(r['n'] for r in rs)
        tokens=sum(r['n']*(r['input_tokens_per_decision']+r['output_tokens_per_decision']) for r in rs)/denominator
        accuracy=sum(r['correct'] for r in rs)/denominator
        label=model+' '+organization
        axes[1,1].scatter(tokens,accuracy,color=colors[model],marker='o' if organization=='flat' else '^',
                          label=label if label not in labeled else None)
        axes[1,1].annotate(policy,(tokens,accuracy),fontsize=6,xytext=(3,3),textcoords='offset points')
        labeled.add(label)
    if labeled:axes[1,1].legend(fontsize=6)
    axes[1,1].set_title('Accuracy and measured token use');axes[1,1].set_xlabel('Input + output tokens per decision');axes[1,1].set_ylabel('Accuracy')
    fig.suptitle(result['suite']+(' — complete' if result['complete'] else ' — incomplete development results'))
    fig.savefig(output/'overview.pdf');fig.savefig(output/'overview.png',dpi=150);plt.close(fig)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('output');p.add_argument('--bootstrap',type=int,default=10000)
    a=p.parse_args();r=summarize(a.directory,a.output,a.bootstrap)
    print(canonical({k:r[k] for k in ('suite','planned_trajectories','analyzed_trajectories','complete','competence')}))
