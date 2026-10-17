"""Compact audit artifacts; new GPU effects appear only after complete replay."""
from pathlib import Path
from collections import defaultdict
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from rep_sensitivity.schema import digest


root=Path('results/numerical-pipeline-v1');r=json.loads((root/'analysis.json').read_text())
new=Path('results/numerical-preservation-v1/analysis.json')
new_complete=new.exists() and json.loads(new.read_text()).get('complete',False)
not_launched=Path('artifacts/runs/numerical-preservation-execution/not-launched.json').exists()
support_path=root/'visible-support-v3.json'
support_data=json.loads(support_path.read_text()) if support_path.exists() else None
figdir=root/'figures';figdir.mkdir(exist_ok=True)
def save(fig,name):
    fig.savefig(figdir/(name+'.pdf'),bbox_inches='tight')
    fig.savefig(figdir/(name+'.png'),dpi=160,bbox_inches='tight');plt.close(fig)

panels=[('pilot-v7','qwen3','Pilot Qwen3 (2 policies)',12,96),
        ('validation-v7','qwen3','Validation Qwen3 (3 policies)',18,216),
        ('validation-v7','phi4','Validation Phi-4 (3 policies)',18,216)]
pooled=[]
for suite,model,label,n,t in panels:
    for condition in ('single','exact','paraphrase'):
        rs=[x for x in r['groups'] if (x['suite'],x['model'],x['kind'],x['condition'])==(suite,model,'schedule',condition)]
        totals={k:sum(x[k] for x in rs) for k in rs[0] if type(rs[0][k]) in (int,float)}
        pooled.append({'suite':suite,'model':model,'condition':condition,'base_pairs':n,'label':label,**totals})
        pooled[-1]['base_pairs']=n
fig,axes=plt.subplots(1,3,figsize=(10,3.2),sharey=True)
for ax,(suite,model,label,n,t) in zip(axes,panels):
    for offset,(key,name,color) in enumerate([('objective_boolean_replacement','Boolean replacement','#bd4f38'),
                                           ('objective_omitted','Omitted','#deb56c'),('objective_preserved','Preserved','#357ba8')]):
        rows=[x for x in pooled if x['suite']==suite and x['model']==model]
        ax.bar(np.arange(3)+(offset-1)*.25,[100*x[key]/x['objective_fields'] for x in rows],width=.24,label=name,color=color)
    ax.set_title(label,fontsize=9);ax.set_xticks(range(3),['Single','Exact','Paraphrase'],fontsize=8)
    ax.set_xlabel(f'{n} bases; {t} trajectories/condition\n{3*t} objective fields/condition',fontsize=8);ax.grid(axis='y',alpha=.2)
axes[0].set_ylabel('Candidate-objective fields (%)');axes[0].set_ylim(0,103)
fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',ncol=3,fontsize=8)
fig.suptitle('Scheduling objective transmission (field counts are dependent)',fontsize=11)
fig.tight_layout(rect=(0,.12,1,.95));save(fig,'objective-fields')

fig,ax=plt.subplots(figsize=(10,2.7));ax.axis('off')
labels=['Worker report\n8, 9, 9 time units','Manager input\n8, 9, 9 time units',
        'Raw model summary\ntrue, true, true','Parsed summary\ntrue, true, true','Root input\ntrue, true, true']
for i,text in enumerate(labels):
    x=.09+i*.205
    ax.text(x,.65,text,ha='center',va='center',fontsize=13,transform=ax.transAxes,
            bbox=dict(boxstyle='round,pad=.6',facecolor='#f4d8ce' if i>=2 else '#dcecf3',edgecolor='#555555'))
    if i<4:ax.annotate('',xy=(x+.135,.65),xytext=(x+.075,.65),xycoords='axes fraction',arrowprops=dict(arrowstyle='->',lw=1))
ax.text(.5,.20,'Influential pilot case; scopes shown in candidate order C39, C64, C83\n'
        'All 6,336 audited manager summaries: 0 parser value changes; 0 parsed-to-root changes.\n'
        'The schema permits both types; instructions explicitly request numerical objectives.',
        transform=ax.transAxes,ha='center',va='center',fontsize=12)
save(fig,'pipeline-origin')

fig,axes=plt.subplots(1,3,figsize=(10,3.2),sharey=True)
for ax,(suite,model,label,n,t) in zip(axes,panels):
    x=next(x for x in r['comparisons'] if (x['suite'],x['model'],x['kind'],x['policy'],x['contrast'],x['metric'])==
           (suite,model,'schedule','ordinary+checklist','exact - single','correct'))
    ids=sorted(x['base_effects']);values=[100*x['base_effects'][p] for p in ids]
    ax.bar(range(1,len(ids)+1),values,color=['#357ba8' if v>=0 else '#bd4f38' for v in values]);ax.axhline(0,color='black',lw=.6)
    if 'e765f8bb5f0e2aad' in ids:
        i=ids.index('e765f8bb5f0e2aad')+1;ax.text(i,values[i-1]+2,'*',ha='center')
    ax.set_title(label.replace('3 policies','matched 2 policies'),fontsize=9);ax.set_xlabel('Base pair (identifier order)',fontsize=8)
    ax.set_xticks([1,6,12] if len(ids)==12 else [1,6,12,18])
    ax.text(.02,.96,f"Corrections {x['improvements']}; regressions {x['regressions']}",transform=ax.transAxes,va='top',fontsize=7)
    ax.grid(axis='y',alpha=.2)
axes[0].set_ylabel('Exact − single accuracy (points)');axes[0].set_ylim(-50,105)
fig.suptitle('All base problems retained; * influential pilot pair',fontsize=11)
fig.tight_layout(rect=(0,0,1,.94));save(fig,'base-effects')

fig,ax=plt.subplots(figsize=(7.3,3.3))
matched=[]
for i,(suite,model,label,n,t) in enumerate(panels):
    for offset,(metric,name,color) in enumerate([('correct','Decision accuracy','#555555'),('objective_retention','Objective preservation','#357ba8')]):
        x=next(x for x in r['comparisons'] if (x['suite'],x['model'],x['kind'],x['policy'],x['contrast'],x['metric'])==
               (suite,model,'schedule','ordinary+checklist','exact - single',metric))
        matched.append(x)
        ax.errorbar(100*x['estimate'],i+(offset-.5)*.18,xerr=[[100*(x['estimate']-x['lower'])],[100*(x['upper']-x['estimate'])]],
                    fmt='o',color=color,capsize=3,label=name if i==0 else None)
ax.axvline(0,color='grey',lw=1);ax.set_yticks(range(3),['Pilot Qwen3 (12 bases)','Validation Qwen3 (18)','Validation Phi-4 (18)'])
ax.set_xlabel('Exact − single (percentage points), whole-base 95% interval');ax.invert_yaxis();ax.grid(axis='x',alpha=.2)
ax.set_title('Same ordinary/checklist policies; outcomes remain distinct',fontsize=10)
fig.legend(*ax.get_legend_handles_labels(),loc='lower center',ncol=2,fontsize=8)
fig.tight_layout(rect=(0,.12,1,1));save(fig,'retention-effects')

lines=['# Numerical-information pipeline audit','',
 'This completed CPU analysis uses immutable pilot and validation outputs: 60 independent base pairs (24 development plus 36 validation, shared across the validation models), 3,168 hierarchical trajectories and 6,336 manager summaries. No partial main outcomes or new GPU responses were used.','',
 'The first numerical-to-Boolean change is in the **raw model-generated manager response**. Every audited manager input matches its frozen report text and scope registry; raw assertion values match the parsed values, and parsed summaries match the actual root inputs. All construction, parsing, transport and primary-choice-score discrepancy counts are zero. No manager output was truncated. Representative raw summary text, full objective scope fields, report excerpts and immutable call hashes are in `results/numerical-pipeline-v1/representative-traces.json`. Unaffected controls are included.','',
 'The original prompt states that objectives are numbers. Its assertion example uses `true` with an explicit placeholder warning, and its common JSON schema permits Boolean or number at every key. The schema therefore fails to prevent the observed semantic type error. The audit does not establish that the example or schema caused the behavior. Parsing changes object assertions into triples without converting their values. Type-safe scoring distinguishes Boolean `true` from numeric 1; integral floats remain legitimate numbers. The earlier integer/float retention-scoring correction remains separate from this audit. No additional score correction or GPU rerun is indicated.','',
 '| Scheduling group | Condition | Bases | Trajectories | Objective fields | Boolean | Omitted | Preserved |',
 '|---|---|---:|---:|---:|---:|---:|---:|']
for x in pooled:
    lines.append(f"| {x['label']} | {x['condition']} | {x['base_pairs']} | {x['trajectories']} | {x['objective_fields']} | {x['objective_boolean_replacement']} | {x['objective_omitted']} | {x['objective_preserved']} |")
lines+=['','Fields are unique full-scope candidate objectives per trajectory. Copies are not extra denominator units. Boolean, omission, unresolved/conflict and citation labels are reported separately and can overlap; preserved requires every emitted value at the correct scope to match and no unresolved flag. A number at the wrong candidate is not preserved. Numeric errors, scope-citation mismatches, workflow results and all policy strata are in `analysis.json` and `field-summary.csv`. Every number emitted at a known objective key in these intermediate summaries matched its source; failures included Boolean replacement, omission or unresolved information.','',
 'The anomaly recurs across bases and models, but the pilot reduction in Boolean replacement does not generalize to validation. Correctly delivered information also does not guarantee a correct root choice. In scheduling validation, with all three policies, Qwen3 made '+str(next(x for x in pooled if x['suite']=='validation-v7' and x['model']=='qwen3' and x['condition']=='single')['wrong_despite_sufficient_correct_visible'])+' wrong choices among '+str(next(x for x in pooled if x['suite']=='validation-v7' and x['model']=='qwen3' and x['condition']=='single')['sufficient_correct_visible'])+' unrepeated contexts with sufficient, consistent, correctly delivered facts. This is an observational conditional denominator, not an estimate of mediation. Workflow sufficiency is conservatively restricted to completely preserved propositions; no unvalidated scheduling scorer is applied to that task.','',
 'The direct, exploratory Qwen3 change in the exact-repetition effect from pilot to validation is '+next(f"{100*x['estimate']:+.2f} points [95% interval {100*x['lower']:.2f}, {100*x['upper']:.2f}]" for x in r['stage_effect_changes'] if x['kind']=='schedule' and x['contrast']=='exact - single')+'. It compares 12 pilot with 18 validation scheduling bases, ordinary/checklist policies, two worlds and two repetitions, resampling independent stage clusters. Different graph/parameter/template and NONE/tie distributions preclude attributing this stage difference to one feature. Exact-versus-paraphrase direct contrasts are also reported.','',
 ('The separately frozen numerical-preservation replay is complete; see `NUMERICAL_PRESERVATION_RESULTS.md`. ' if new_complete else
  'The numerical-preservation replay was not launched; the execution record states the protected-work or cumulative-budget reason. ' if not_launched else
  'The focused numerical-preservation replay is separately frozen and pending. ')+
 'It reuses the six previously selected diagnostic bases, including two with baseline objective loss and four without, rather than selecting new cases by decision outcomes. Its 48 fresh root calls cross cached upstream single/exact treatments with ordinary/objective-only repaired delivery. All eligible branch-visible objectives are handled equally; every replacement, addition and objective-specific unresolved-flag removal is logged. Other summary content remains intact. The comparison estimates repair of fixed summaries and an interaction conditional on cached manager outputs, not a fresh complete-hierarchy experiment or full causal mediation. Existing fresh confirmation does not independently confirm this repair interaction.','',
 'Reproduce with `PYTHONPATH=src .venv/bin/python scripts/audit_numerical_pipeline.py` and `PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python scripts/build_numerical_report.py`. Detailed field records stay in the mirrored, ignored artifact package; compact results and representative traces are versioned.','']
lines += ['Paired objective-preservation estimates below use the **same two policies** in all stages. Each trajectory contributes the fraction of its three objective propositions preserved. Improvements/regressions compare that fraction; they are not counts of corrected final answers. Calls count all three original hierarchy calls in both paired conditions.','',
 '| Group | Bases | Trajectories per arm | Calls, both arms | Single % | Exact % | Difference, points [95% interval] | Improved / regressed / unchanged |',
 '|---|---:|---:|---:|---:|---:|---:|---:|']
for x in matched:
    if x['metric']!='objective_retention':continue
    lines.append(f"| {x['suite']} / {x['model']} | {x['clusters']} | {x['matched_cells']} | {3*x['trajectories']} | {100*x['baseline']:.2f} | {100*x['repeated']:.2f} | {100*x['estimate']:+.2f} [{100*x['lower']:.2f}, {100*x['upper']:.2f}] | {x['improvements']} / {x['regressions']} / {x['unchanged']} |")
lines.append('')
lines += ['Representation validity and decision support are distinct. The v3 analysis-only supplement retains the strict v2 invalid/contradictory labels but also asks whether the answer is unchanged under **every admissible completion of the unknown or disputed fields**, holding uncontested supplied assertions fixed. It never supplies missing truth. Two of the four invalid baseline contexts in the fixed root diagnostic still identify the only feasible candidate; the other two permit several answers. Thus objective loss is not automatically decision-critical, and correctness in the former contexts is not merely lucky guessing. The six-base repair design stays unchanged; only one of its two baseline-loss bases has decision-relevant numerical uncertainty. This further limits precision and interpretation.','',
 'The strict v2 files and original primary world-correctness scores are preserved. `visible-support-v3.json` reports the supplemental denominators. Raw summaries are not repaired by the scorer; it does not settle a disputed field simply because that field is irrelevant to the choice.','']
if support_data:
    lines += ['| Scheduling baseline, all available policies | Trajectories | Uniquely supported decisions | Root choices violating that decision | Determinate despite representation errors |',
              '|---|---:|---:|---:|---:|']
    for suite,model,label,n,t in panels:
        rs=[x for x in support_data['groups'] if (x['suite'],x['model'],x['condition'])==(suite,model,'single')]
        lines.append(f"| {label} | {sum(x['trajectories'] for x in rs)} | {sum(x['agreement_denominator'] for x in rs)} | {sum(x['violates_uncontested_unique_decision'] for x in rs)} | {sum(x['determinate_despite_representation_errors'] for x in rs)} |")
    lines += ['', 'These are descriptive, dependent trajectory counts. A supported choice is conditional on uncontested supplied assertions; world correctness remains separately scored.','']
Path('NUMERICAL_PIPELINE_AUDIT.md').write_text('\n'.join(lines))
tex=[r'\subsection{Numerical information at the summary boundary}',
 'A new audit follows every intermediate response in the completed pilot and validation: 6,336 summaries from 3,168 hierarchical trajectories and 60 independent bases. Frozen worker reports match actual manager inputs; raw values match parsed assertions and actual root inputs throughout. The numerical-to-Boolean transformation is already present in raw model output (Fig.~\\ref{fig:numeric-origin}), not introduced by parsing or serialization. Primary choice scores agree with raw answers. No rerun is indicated by this audit.',
 r'\begin{figure}[ht]\centering\includegraphics[width=\linewidth]{../results/numerical-pipeline-v1/figures/pipeline-origin.pdf}\caption{Observed transformation in a representative pilot trace. Scope and source references remain traceable; the numerical value is replaced in model output.}\label{fig:numeric-origin}\end{figure}',
 'The instructions request numerical objectives, but the common assertion schema allows either Boolean or numeric values at each scope. This protocol permits the semantic error rather than enforcing scope-dependent types. Its Boolean example may be relevant, but that causal explanation is untested. These results are conditional on this interface.',
 r'\begin{table}[ht]\centering\small\caption{Boolean objective replacements in hierarchical scheduling. Denominators count full-scope candidate-objective fields, not independent samples. Pilot averages two policies; validation averages all three.}\label{tab:numeric-boolean}',
 r'\begin{tabular}{lrrr}\toprule Group & Single & Exact & Paraphrase\\\midrule']
for suite,model,label,n,t in panels:
    rows=[x for x in pooled if x['suite']==suite and x['model']==model]
    tex.append(label.split(' (')[0]+' & '+' & '.join(f"{x['objective_boolean_replacement']}/{x['objective_fields']}" for x in rows)+r'\\')
tex += [r'\bottomrule\end{tabular}\end{table}',
 'The failure recurs beyond the influential pilot pair, but its reduction with repetition does not reproduce in validation (Table~\\ref{tab:numeric-boolean}). Every number emitted at a known objective key in these intermediate summaries matched its source; omission and Boolean replacement were the dominant objective failures. Correctly delivered facts can still be misapplied: the complete analysis separates strict visible sufficiency from world correctness and reports both denominators. Associations conditioned on retention do not identify mediation.',
 'Representation validity is distinct from decision support. In two of the four ill-typed baseline contexts in the fixed diagnostic, uncontested constraints already identify the sole feasible candidate. The remaining two admit multiple choices without objectives. An analysis-only supplement retains the strict invalidity labels while testing whether all admissible completions of the disputed or missing fields yield the same decision. No hidden value is restored. Missing numerical information is therefore not necessarily decision-critical; only one of the two baseline-loss bases in this small diagnostic has decision-relevant numerical uncertainty.',
 'A separate prospective exploratory diagnostic uses six previously fixed development pairs, two with baseline objective loss and four without. Forty-eight fresh root calls cross the original upstream repetition treatment with branch-limited objective repair. Repair preserves source scope and does not add feasibility conclusions or the correct choice. It is an idealized information intervention conditional on cached summaries. '+
 ('Results follow below. ' if new_complete else 'It was not launched under the protected-work/cumulative-budget rule. ' if not_launched else 'Its result is pending. ')+'The existing fresh repetition confirmation does not independently confirm this interaction.','']
pass  # The one-file paper is refreshed below.
Path('records/manuscript-sources/numerical-pipeline-traceability.json').write_text(json.dumps({'analysis_sha256':digest(r),'table_rows':pooled,'source':'results/numerical-pipeline-v1/analysis.json',
    'visible_support_analysis_sha256':digest(support_data) if support_data else None,
    'decision_support_preflight_sha256':digest(json.loads(Path('records/preflight/visible-support-v3.json').read_text()))},indent=2)+'\n')

if new_complete:
    d=json.loads(new.read_text());destination=new.parent/'figures';destination.mkdir(exist_ok=True)
    fig,ax=plt.subplots(figsize=(5.5,3))
    absolute=[x for x in d['absolute'] if x['population']=='all']
    ax.bar([x['arm'] for x in absolute],[100*x['accuracy'] for x in absolute],color=['#888888','#357ba8','#b99554','#457753'])
    ax.set_ylim(0,105);ax.set_ylabel('World accuracy (%)');ax.set_xlabel('A: ordinary/single; B: ordinary/exact\nC: repair/single; D: repair/exact',fontsize=8)
    ax.set_title('Six-base cached-summary diagnostic; 12 calls/arm')
    fig.tight_layout();fig.savefig(destination/'four-conditions.pdf');fig.savefig(destination/'four-conditions.png',dpi=160);plt.close(fig)
    # Completion prose derives only from the complete immutable-output analysis.
    interaction=next(x for x in d['contrasts'] if x['population']=='all' and x['contrast']=='repetition_by_preservation' and x['metric']=='correct')
    text=f"\nCompleted diagnostic: {d['base_pairs']} independent bases, {d['trajectories']} fresh root calls. Accuracy A/B/C/D: "+'/'.join(f"{100*x['accuracy']:.2f}%" for x in absolute)+f". Repetition-by-preservation interaction: {100*interaction['estimate']:+.2f} points [{100*interaction['lower']:.2f}, {100*interaction['upper']:.2f}]. Exploratory six-base uncertainty; no causal-mediation claim.\n"
    Path('NUMERICAL_PRESERVATION_RESULTS.md').write_text(text)
    pass  # The one-file paper is refreshed below.
print(json.dumps({'pipeline_figures':4,'gpu_diagnostic_complete':new_complete}))

# Preserve the single-source manuscript under manual and automatic refreshes.
from manuscript_content import refresh
refresh()
