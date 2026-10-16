"""Paired contrasts and stratified base-cluster uncertainty, never row bootstrap."""
from collections import defaultdict
import csv
import json
import math
from pathlib import Path
import statistics
import importlib.metadata
from .schema import canonical, digest
from .reports import thaw


def average(xs):
    values = list(xs)
    return sum(values) / len(values) if values else None


def bootstrap(values, strata, replicates=10000, seed=20271015, difference=False):
    """One value per base cluster. H2 separately contrasts changing vs preserving."""
    import numpy as np
    if not values: return {"estimate": None, "lower": None, "upper": None, "clusters": 0}
    groups = defaultdict(list)
    for key, val in values.items(): groups[tuple(strata[key])].append(val)
    rng = np.random.default_rng(seed)
    sums = np.zeros(replicates)
    denom = len(values)
    if difference:
        n_change = sum(len(v) for k, v in groups.items() if k[-1])
        n_preserve = denom - n_change
        if not n_change or not n_preserve:
            return {"estimate": None, "lower": None, "upper": None, "clusters": len(values)}
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
            "approx_halfwidth_at_48": 1.96*sd/math.sqrt(48) if sd is not None else None,
            "approx_halfwidth_at_96": 1.96*sd/math.sqrt(96) if sd is not None else None}


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
    config = manifest["config"]
    expected = len(config["worlds"])*len(config["repetition_conditions"])*len(config["organizations"])*len(config["policies"])*config["stochastic_repetitions"]
    rows, incomplete = [], []
    for alias in config["models"]:
        for path in sorted((directory/alias/"scores").glob("*.json")):
            records = json.loads(path.read_text())
            if len(records) != expected or len({r['trial_id'] for r in records}) != expected:
                incomplete.append(str(path)); continue
            for r in records:
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
                        'mean_brier':average(r['brier'] for r in rs if r['brier'] is not None),
                        'mean_log_loss':average(r['log_loss'] for r in rs if r['log_loss'] is not None),
                        'input_tokens_per_decision':average(r['input_tokens'] for r in rs),
                        'output_tokens_per_decision':average(r['output_tokens'] for r in rs),
                        'allocated_seconds_per_decision':average(r['inference_seconds_allocated'] for r in rs),
                        'tokens_per_correct':sum(r['input_tokens']+r['output_tokens'] for r in rs)/correct if correct else None,
                        'summary_retention':sum(s['retained_count'] for r in rs for s in r['summary_scores'])/
                            max(1,sum(s['required_claims'] for r in rs for s in r['summary_scores'])) if org=='hierarchical' else None})
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
    competence=[]
    for model in sorted({r['model'] for r in rows}):
        for kind in ('schedule','workflow'):
            rs=[r for r in rows if r['model']==model and r['kind']==kind and r['organization']=='flat' and r['policy']=='ordinary' and r['condition']=='single']
            competence.append({'model':model,'kind':kind,'n':len(rs),'accuracy':average(r['correct'] for r in rs),
                               'passes_85_percent':average(r['correct'] for r in rs)>=0.85 if rs else None})
    for filename, data in [('summary.csv',summary),('contrasts.csv',contrasts),('competence.csv',competence)]:
        if data:
            with (output/filename).open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n'); writer.writeheader(); writer.writerows(data)
    result={'suite':manifest['config']['name'],'manifest_sha256':digest(manifest),
            'planned_trajectories':manifest['trajectories'],'analyzed_trajectories':len(rows),
            'complete':len(rows)==manifest['trajectories'],'excluded_incomplete_score_files':incomplete,
            'source_scores_sha256':digest([json.loads(p.read_text()) for p in sorted(directory.glob('*/scores/*.json'))]),
            'summary':summary,'contrasts':contrasts,'competence':competence,
            'analysis_settings':{'bootstrap_replicates':replicates,'seed':20271015,'cluster':'base_pair','p_values':None,
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
            ax.errorbar(r['estimate'],i,xerr=[[r['estimate']-r['lower']],[r['upper']-r['estimate']]],fmt='o')
        ax.set_yticks(range(len(data)),[r['model']+' '+r['contrast'] for r in data]);ax.axvline(0,color='grey',lw=1)
        ax.set_title(title);ax.set_xlabel('Error-rate difference; cluster 95% CI')
    data=[r for r in result['summary'] if r['kind']=='schedule' and r['organization']=='hierarchical']
    axes[1,0].bar(range(len(data)),[r['summary_retention'] for r in data])
    axes[1,0].set_xticks(range(len(data)),[r['policy']+'\n'+r['condition'] for r in data],rotation=40,ha='right',fontsize=7)
    axes[1,0].set_ylim(0,1);axes[1,0].set_title('Explicit summary-claim retention')
    data=[r for r in result['summary'] if r['kind']=='schedule']
    for r in data:
        axes[1,1].scatter(r['input_tokens_per_decision']+r['output_tokens_per_decision'],r['accuracy'],
                         marker='o' if r['organization']=='flat' else '^')
    axes[1,1].set_title('Accuracy and measured token use');axes[1,1].set_xlabel('Input + output tokens per decision');axes[1,1].set_ylabel('Accuracy')
    fig.suptitle(result['suite']+(' — complete' if result['complete'] else ' — incomplete development results'))
    fig.savefig(output/'overview.pdf');fig.savefig(output/'overview.png',dpi=150);plt.close(fig)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('output');p.add_argument('--bootstrap',type=int,default=10000)
    a=p.parse_args();r=summarize(a.directory,a.output,a.bootstrap)
    print(canonical({k:r[k] for k in ('suite','planned_trajectories','analyzed_trajectories','complete','competence')}))
