"""Compact review artifacts from complete validation and later diagnostic outputs."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from rep_sensitivity.schema import digest

root=Path('results/validation-repetition-v1');r=json.loads((root/'analysis.json').read_text())
root_complete=Path('artifacts/runs/root-diagnostic-execution/complete.json').exists()
confirmation_complete=Path('results/objective-confirmation-v1/analysis.json').exists() and json.loads(Path('results/objective-confirmation-v1/analysis.json').read_text()).get('complete')
figures=root/'figures';figures.mkdir(exist_ok=True)
models=['qwen3','phi4'];labels={'qwen3':'Qwen3-14B','phi4':'Phi-4'}
colors={'exact':'#2166ac','paraphrase':'#b35806'}
focus=[x for x in r['comparisons'] if x['kind']=='schedule' and x['organization']=='hierarchical' and x['policy']=='ordinary+checklist']
allpol=[x for x in r['comparisons'] if x['kind']=='schedule' and x['organization']=='hierarchical' and x['policy']=='ordinary+checklist+scope']
def save(fig,name,bottom=0):
    fig.tight_layout(rect=(0,bottom,1,1));fig.savefig(figures/(name+'.pdf'));fig.savefig(figures/(name+'.png'),dpi=140);plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(9.1,3.3))
y=0
for model in models:
    subset=[x for x in focus if x['model']==model]
    for condition in ('exact','paraphrase'):
        x=next(x for x in subset if x['contrast']==condition+' - single')
        axes[0].plot([100*x['baseline'],100*x['repeated']],[y,y],color=colors[condition],lw=2)
        axes[0].scatter(100*x['baseline'],y,marker='o',facecolors='white',edgecolors=colors[condition],s=45,zorder=3)
        axes[0].scatter(100*x['repeated'],y,color=colors[condition],marker='s',s=35,zorder=3)
        axes[1].errorbar(100*x['estimate'],y,xerr=[[100*(x['estimate']-x['lower'])],[100*(x['upper']-x['estimate'])]],fmt='o',color=colors[condition],capsize=3)
        y+=1
names=[labels[m]+' / '+c for m in models for c in ('exact','paraphrase')]
for ax in axes:
    ax.set_yticks(range(4),names);ax.invert_yaxis();ax.grid(axis='x',alpha=.2)
axes[0].set_xlabel('Accuracy (%) — circle: single; square: repeated')
axes[0].set_xlim(65,85);axes[1].axvline(0,color='grey',lw=1);axes[1].set_xlabel('Repeated − single (percentage points)')
fig.suptitle('Original validation: 18 scheduling pairs; 144 decisions per arm\nEqual ordinary/checklist policies; whole-base 95% intervals',fontsize=10)
save(fig,'paired-effects')

fig,axes=plt.subplots(1,2,figsize=(9.1,3.2),sharey=True)
for ax,model in zip(axes,models):
    data={c:next(x for x in focus if x['model']==model and x['contrast']==c+' - single')['base_effects'] for c in ('exact','paraphrase')}
    keys=sorted(data['exact'])
    for c,offset in [('exact',-.12),('paraphrase',.12)]:
        ax.scatter(np.arange(1,len(keys)+1)+offset,[100*data[c][k] for k in keys],color=colors[c],s=23,label=c)
    ax.axhline(0,color='grey',lw=1);ax.set_xticks([1,6,12,18]);ax.set_title(labels[model]);ax.set_xlabel('Base pair (fixed identifier order)');ax.grid(axis='y',alpha=.2)
axes[0].set_ylabel('Paired accuracy effect (points)')
handles,names=axes[1].get_legend_handles_labels();fig.legend(handles,names,loc='lower center',ncol=2,fontsize=8)
fig.suptitle('All 18 validation scheduling bases retained; no outcome-selected exclusions',fontsize=10)
save(fig,'base-distribution',bottom=.13)

fig,axes=plt.subplots(1,2,figsize=(9.1,3.5),sharey=True)
keys=['necessary_fact_omitted','necessary_value_wrong_or_conflicted','visible_false_constraint_ignored','strictly_suboptimal_objective','response_contract_failure']
names=['Omitted\nfact','Distorted\nvalue','Delivered FAIL\nignored','Feasible but\nsuboptimal','Contract\nfailure']
for ax,model in zip(axes,models):
    for index,condition in enumerate(('single','exact','paraphrase')):
        row=next(x for x in r['failure_locations'] if (x['model'],x['kind'],x['organization'],x['condition'])==(model,'schedule','hierarchical',condition))
        ax.bar(np.arange(len(keys))+(index-1)*.24,[100*row[k]/row['trajectories'] for k in keys],width=.23,label=condition)
    ax.set_xticks(range(len(keys)),names,fontsize=7);ax.set_title(labels[model]);ax.grid(axis='y',alpha=.2)
axes[0].set_ylabel('Trajectories with label (%)');axes[1].legend(fontsize=7)
fig.suptitle('Observable failures: 216 decisions/arm/model, all three policies\nLabels can overlap; generated assertions are not private reasoning',fontsize=10)
save(fig,'failure-locations')

fig,axes=plt.subplots(1,2,figsize=(9.1,3.3),sharey=True)
for ax,model in zip(axes,models):
    for org,marker in [('flat','o'),('hierarchical','s')]:
        for condition,color in [('single','#555555'),('exact',colors['exact']),('paraphrase',colors['paraphrase'])]:
            row=next(x for x in r['absolute'] if (x['model'],x['kind'],x['organization'],x['condition'])==(model,'schedule',org,condition))
            ax.scatter(row['inference_seconds_allocated']/row['trajectories'],100*row['accuracy'],marker=marker,color=color,s=45,label=org+' / '+condition)
    ax.set_title(labels[model]);ax.set_xlabel('Allocated batch seconds per decision');ax.grid(alpha=.2)
axes[0].set_ylabel('World accuracy (%)')
handles,names=axes[1].get_legend_handles_labels();fig.legend(handles,names,loc='lower center',ncol=3,fontsize=7)
fig.suptitle('Original validation: accuracy and measured inference cost\n18 scheduling bases; equal ordinary/checklist/scope policies',fontsize=10)
save(fig,'cost-accuracy',bottom=.22)

lines=['# Validation repetition results','',
 'This is a new offline analysis of **already completed original validation**: 36 independent base pairs, 5,184 trajectories and 10,368 accepted calls across two models. It uses no new GPU calls and reads no unfinished main-test choices. Scheduling and workflow results remain separate.','',
 'The table matches the pilot’s ordinary/checklist policies. Each row uses 18 scheduling pairs, 144 trajectories per condition, two worlds and two stochastic repetitions. Estimates average complete base clusters; 95% intervals resample bases within mutation-family × decision-change strata.','',
 '| Model | Repetition | Single % | Repeated % | Difference, points [95% interval] | Corrections / regressions / unchanged |',
 '|---|---|---:|---:|---:|---:|']
for x in focus:
    if x['contrast']=='exact - paraphrase':continue
    lines.append(f"| {labels[x['model']]} | {x['contrast'].split(' - ')[0]} | {100*x['baseline']:.2f} | {100*x['repeated']:.2f} | {100*x['estimate']:+.2f} [{100*x['lower']:.2f}, {100*x['upper']:.2f}] | {x['improvements']} / {x['regressions']} / {x['unchanged']} |")
lines += ['', 'The pilot’s large mean benefit does not reproduce in this validation aggregate. The intervals allow modest benefits and harms; this does not establish that repetition is ineffective. Validation uses different job sizes, parameter ranges and renderings, and includes NONE/tie cases absent from parts of the pilot. These are exploratory validation estimates, not a replacement for the frozen held-out test.','',
 'With all three policies, scheduling hierarchy accuracy is '+ '; '.join(f"{labels[m]} {100*next(x for x in allpol if x['model']==m and x['contrast']=='exact - single')['baseline']:.2f}% → {100*next(x for x in allpol if x['model']==m and x['contrast']=='exact - single')['repeated']:.2f}% (exact)" for m in models)+'. Full policy, task, direct exact-versus-paraphrase, hierarchy-interaction and paired-world tables are in the machine-readable analysis.','',
 'Failure labels distinguish omitted propositions, wrong scoped values, ignored delivered constraints, feasible-but-suboptimal choices, erroneous support and response-contract failures. Labels overlap. They describe observable outputs; they do not identify an internal reasoning process or causal mediation.','',
 ('The root diagnostic has completed; its separate analysis is available. ' if root_complete else 'The root diagnostic remains pending until the current Qwen stage finishes. ')+'Its frozen inputs contain 8 sufficient-consistent and 4 ill-typed contexts; lossless transport has 12 sufficient-consistent contexts. Repetition holds these states fixed. It includes each candidate objective selectively and all objectives uniformly, but no paraphrase arm. The analysis now distinguishes no consistent completion from multiple possible answers and from a uniquely justified decision.','',
 'The influential pilot base `e765f8bb5f0e2aad` remains included. Both worlds have feasible objective values 8, 9, 9. All eight unrepeated hierarchical contexts emit Boolean `true` in every objective slot; only one final answer is correct. Exact repetition restores numeric objectives in all eight and all eight choices are correct. The repeated report concerns C64 (9), whereas C39 (8) is correct. The sole feature hypothesis is improved numerical-objective preservation, tested by the already frozen lossless-transport interaction. This case alone does not isolate arithmetic, position or attention.','',
 'Reproduce: `PYTHONPATH=src .venv/bin/python scripts/analyze_validation_repetition.py` and `PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python scripts/build_empirical_update.py`. Raw calls remain under ignored `artifacts/runs/validation-v7/`; compact tables and figures are under `results/validation-repetition-v1/`.','']
Path('VALIDATION_REPETITION_RESULTS.md').write_text('\n'.join(lines))
tex=['% Generated solely from complete validation analysis.','\\subsection{Exploratory validation replication}',
 'Original validation contains 36 independent bases (18 scheduling, 18 workflow), with 2,592 trajectories per model. This analysis was added after the pilot interpretation; validation is not post-amendment held-out confirmation. Table~\\ref{tab:validation-repetition} matches the pilot by averaging ordinary synthesis and checklist policies. Each scheduling arm contains 144 decisions from 18 bases. The large pilot benefit does not reproduce in this aggregate; intervals include modest benefits and harms.',
 '\\par\n\\begin{table}[ht]\\centering\\small\\caption{Validation hierarchical scheduling; whole-base 95\\% intervals. Differences are repeated minus single.}\\label{tab:validation-repetition}',
 '\\begin{tabular}{llrrr}\\toprule Model & Repetition & Single \\% & Repeated \\% & Change, pp [95\\% CI]\\\\\\midrule']
for x in focus:
    if x['contrast']=='exact - paraphrase':continue
    tex.append(f"{labels[x['model']]} & {x['contrast'].split(' - ')[0]} & {100*x['baseline']:.2f} & {100*x['repeated']:.2f} & {100*x['estimate']:+.2f} [{100*x['lower']:.2f}, {100*x['upper']:.2f}]\\\\")
tex+=['\\bottomrule\\end{tabular}\\end{table}\\par',
 'All original comparisons, including scope consolidation, remain in the archived analysis. Policy pooling is explicit; validation and pilot aggregates are not interchangeable. Changes in graph size, parameters, rendering and tie/NONE composition limit a direct causal explanation of the difference between splits.',
 '\\begin{figure}[ht]\\centering\\includegraphics[width=\\linewidth]{../results/validation-repetition-v1/figures/base-distribution.pdf}\\caption{Validation effects across all 18 scheduling bases; paired worlds, policies and repetitions stay within each base. No outcome-selected exclusions.}\\end{figure}',
 ('The root-only diagnostic and fresh objective confirmation have separate completion records. ' if root_complete and confirmation_complete else 'The root-only diagnostic and fresh objective confirmation remain partially or wholly pending. ')+'The strict input audit separates contradictory or ill-typed summaries from incomplete consistent information; a correct world answer under inadequate evidence is not evidence of successful integration. The frozen root diagnostic includes selective repetition of each candidate objective and balanced repetition of all objectives, with incoming distinct claims fixed. Its lossless interface is an idealized information-preservation intervention.','']
Path('manuscript/generated/validation-repetition.tex').write_text('\n'.join(tex))
Path('manuscript/generated/validation-repetition-traceability.json').write_text(json.dumps({'analysis_sha256':digest(r),'table_rows':focus,'source':'results/validation-repetition-v1/analysis.json'},indent=2)+'\n')
print(json.dumps({'figures':4,'source':str(root/'analysis.json'),'new_gpu_calls':0}))
