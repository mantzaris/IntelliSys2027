"""Review artifacts from completed analyses only; never invent pending results."""
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from rep_sensitivity.schema import digest

OUT=Path('manuscript/generated');OUT.mkdir(parents=True,exist_ok=True)
source=Path('results/pilot-mechanism-v1');audit=json.loads((source/'analysis.json').read_text())
effects=list(csv.DictReader((source/'effects.csv').open()))
trace=[]


def effect(kind,condition,metric):
    row=next(r for r in effects if r['dimension']=='overall' and r['kind']==kind and
             r['organization']=='hierarchical' and r['condition']==condition and r['metric']==metric)
    trace.append({'source':str(source/'effects.csv'),'row':row})
    return {k:float(row[k]) if row[k] else None for k in ('estimate','lower','upper')}


def interval(row,scale=100,tex=False):
    fmt=lambda n:format(scale*n,'+.1f' if scale==100 else '+.3f')
    value=fmt(row['estimate'])
    return value+(f" [{fmt(row['lower'])}, {fmt(row['upper'])}]" if row.get('lower') is not None else ' [interval unavailable]')


labels={'accuracy_change':'Final correctness','necessary_retention_change':'Necessary claims (incl. objectives)',
        'critical_retention_change':'Boolean-critical claims','selected_retained_change':'Selected report claim'}
fig,axes=plt.subplots(1,2,figsize=(10,3.7),sharex=True,sharey=True)
for ax,kind,title in zip(axes,('schedule','workflow'),('Scheduling: 12 base pairs','Workflow (secondary): 12 base pairs')):
    for j,(condition,color) in enumerate([('exact','#1d5c8c'),('paraphrase','#a74a12')]):
        for i,metric in enumerate(labels):
            r=effect(kind,condition,metric);y=i+(j-.5)*.16
            ax.errorbar(100*r['estimate'],y,xerr=[[100*(r['estimate']-r['lower'])],[100*(r['upper']-r['estimate'])]],
                fmt='o',color=color,capsize=3,label=condition if i==0 else None)
    ax.axvline(0,color='gray',lw=.8);ax.set_title(title,fontsize=10);ax.set_yticks(range(len(labels)),list(labels.values()))
    ax.grid(axis='x',alpha=.2);ax.legend(frameon=False)
axes[0].invert_yaxis();axes[1].tick_params(axis='y',labelleft=False)
fig.supxlabel('Repeated minus single (percentage points)',fontsize=10)
fig.suptitle('Exploratory pilot: decision gains do not imply uniform retention gains',fontsize=10)
fig.tight_layout();(source/'figures').mkdir(exist_ok=True)
fig.savefig(source/'figures/retention-and-decisions.pdf');plt.close(fig)

doc='''# Pilot mechanism audit, amendment v1

This is a dated exploratory reanalysis of the preserved Qwen3 pilot, not a new
held-out test. The original analysis and outputs are unchanged. The original
held-out run had already started when the user introduced the revised question;
no held-out model choices were inspected to design this amendment.

The pilot contains 24 independent base pairs (12 scheduling, 12 secondary
workflow), 1,152 trajectories and 2,304 accepted model calls. Worlds, policies,
renderings and stochastic repetitions from one base remain dependent. Reanalysis
reproduces the original score hash; numerical differences are below 1e-12.

All selected reports were correct. In each population, 3 of 24 selected world-level
reports were Boolean-counterfactual-decisive. Objective reports are outside that
Boolean-flip definition, so the other reports must not all be called irrelevant.
Scheduling repeated each of the four task families in six worlds. Workflow
repeated objectives and delivery in ten worlds each, screening and audit in two
each. No selected objective favored a globally fastest infeasible candidate.
The pilot therefore does not identify false-report effects or systematically test
the proposed target-specificity explanation.

Paired estimates below average ordinary and checklist policies within each base,
then weight bases equally. Intervals resample independent bases within mutation
family and change status (10,000 draws). A positive value means increased
correctness or retention. These are development estimates, not confirmatory tests.

| Population | Repetition | Correctness change, pp [95% CI] | Necessary-claim retention change, pp [95% CI] | Boolean-critical retention change, pp [95% CI] |
|---|---|---:|---:|---:|
'''
for kind in ('schedule','workflow'):
    for condition in ('exact','paraphrase'):
        doc+='| '+kind+' | '+condition+' | '+' | '.join(interval(effect(kind,condition,m)) for m in
              ('accuracy_change','necessary_retention_change','critical_retention_change'))+' |\n'
doc+='''
Gains were not distributed uniformly. The largest scheduling point estimates
occurred in numerical-mutation bases. Both policies benefited on exact copies;
paraphrase gains were larger under ordinary synthesis. The subgroup estimates
below are exploratory, with only four independent bases per mutation family.

| Mutation family | Exact correctness change, pp [95% CI] | Paraphrase change, pp [95% CI] |
|---|---:|---:|
'''
for family in ('numeric','identity','dependency','quantifier','condition','version'):
    values=[]
    for condition in ('exact','paraphrase'):
        row=next(r for r in effects if r['dimension']=='family' and r['family']==family and
                 r['organization']=='hierarchical' and r['condition']==condition and r['metric']=='accuracy_change')
        trace.append({'source':str(source/'effects.csv'),'row':row})
        values.append(interval({k:float(row[k]) if row[k] else None for k in ('estimate','lower','upper')}))
    doc+='| '+family+' | '+' | '.join(values)+' |\n'
doc+='''
Repeated-objective scheduling bases had a +33.3 pp point estimate under each
repetition type, but there were only three such bases and singleton strata prevent
the requested stratified interval. This is not a randomized target comparison.
Four-job versus five-job estimates also differ; job count is entangled with family
and target, so these data do not identify a task-difficulty effect. The new
within-world target comparisons address this limitation directly.
'''
doc+='''
Necessary scopes are those whose removal makes the correct choice underdetermined;
this includes objective values. Boolean-critical scopes are those whose isolated
truth-value flip changes the choice. Retention requires an explicit correct value
at the correct scope, with no contrary value or unresolved flag. Failed summaries
count as losses. Claims and citations are measured separately. These are observable
outputs, not a faithful record of hidden reasoning.

Flat scheduling was at its accuracy ceiling. No pilot output failed parsing or
hit the output cap, so the observed gains were not a reduction in those operational
failures. Valid JSON nevertheless included empty summaries and Boolean values in
objective scopes. Necessary-claim retention is more informative here than a metric
restricted to mandatory Boolean constraints, whose retention was near ceiling.

Calibration and confidence do not move uniformly. In hierarchical scheduling,
the exact-copy Brier change was '''+interval(effect('schedule','exact','brier_change'),1)+''';
the paraphrase Brier change was '''+interval(effect('schedule','paraphrase','brier_change'),1)+'''.
The full CSV retains log loss and confidence changes conditional on an unchanged
choice; conditioning on answer consistency is descriptive and cannot establish
increased reliability. Subgroup estimates by task, family, policy and job count
are also retained. Singleton-stratum intervals are withheld; zero-width empirical
intervals elsewhere do not establish robustness.

The systematic trace selection takes the largest and smallest base-average
accuracy change per mutation family and a hash-selected entirely unchanged base
when one exists. A zero extremum is explicitly labeled, not narrated as a gain or
loss. Selection IDs and all matched outputs are in `trace_selection.csv` and the
ignored, locally mirrored `artifacts/analyses/pilot-mechanism-v1/trace-packets.json`.
The following inspected examples diagnose different failure locations:

| Base pair | Inspection finding | Interpretation |
|---|---|---|
| `e765f8bb5f0e2aad` | Baseline manager reports objectives as Boolean values; repeated input produces numerical 8/9/9 and the correct choice C39. | Numerical meaning/type preservation, despite full Boolean-critical retention in both arms. |
| `973c791a1ea121ee` | The repeated root chooses C20 despite receiving its failed resource finding; C71 is correct. | Integration failure after the decisive information reaches the root. |
| `160bd558b5de3da4` | Repeated-input manager emits an empty assertion list; the root returns INSUFFICIENT instead of C76. | Loss at the summary boundary, despite syntactically valid output. |
| `468f3ff2a65c256b` | The manager on the unchanged branch becomes empty; correct C14 changes to INSUFFICIENT. | An unaffected branch can vary; this individual deterioration cannot be attributed solely to its repeated report. |
| `319832d2a013062e` | Baseline summary omits objectives; paraphrased input retains 5/7/11 and the root chooses C74. | Objective delivery can be a bottleneck. |
| `d875d0de865444e5` | Both inputs select correct C12 despite a lost irrelevant finding. | Answer stability alone does not show complete information preservation. |

The aggregate source files, rather than these selected examples, determine effect
estimates. A new calibration metric does not change the trace-selection hash.

Among paired calls on the unexposed manager branch, prompts and requested seeds
were identical in all 192 comparisons per population. Raw responses differed in
17 scheduling and 20 workflow comparisons; normalized emitted findings differed
in 0 and 2, respectively. The audit does not identify the numerical or batching
cause. The new extension explicitly shares identical manager computations within
a world and stochastic repetition, so bypass sees the same summaries. Separate
stochastic repetitions remain separate. Physical calls and logical decision-graph
costs are reported separately.

The pilot supports a conditional investigation of summary transport and integration.
It does not establish that repetition suppresses exceptions, that selective
repetition generally helps, or that all gains are mediated by claim retention.
The bounded extension separates decisive, nondecisive, favorable-but-limited,
false and uniform repetition; matches overlapping presentations; and uses bypass,
lossless transport, length and position interventions. Existing full live-worker
baselines failed adequacy (Qwen3 4/12; Phi-4 3/12), so the new fresh-execution probe
is explicitly narrow and diagnostic. No new source observations are claimed.

Reproduce with the commands in `README.md`. All numerical statements trace to
`results/pilot-mechanism-v1/` or `records/gates/live-development-v8-*.json`.
'''
Path('PILOT_MECHANISM_AUDIT.md').write_text(doc)

tex='''\\subsection{Dated Pilot Mechanism Audit}
After the pilot and the original held-out freeze, the revised question asks when
repetition protects information from summary loss and when it obscures meaningful
differences. The dated amendment preserves H1--H4 and their original analyses;
new mechanism analyses of those runs are exploratory. No original held-out model
choices were inspected to design the amendment. Its new confirmatory contrasts
require disjoint, prospectively frozen instances.

The pilot comprises 24 independent base pairs, not 1,152 independent observations.
All repeated reports are correct. No selected objective favors a fastest infeasible
candidate. Mandatory Boolean retention is near ceiling; numerical objectives
sometimes become Boolean values or disappear despite syntactically valid JSON.
Other errors occur after the correct failed constraint reaches the root. Therefore
the pilot does not identify a single retention mechanism.
\\begin{figure}[ht]
\\centering
\\includegraphics[width=\\textwidth]{../results/pilot-mechanism-v1/figures/retention-and-decisions.pdf}
\\caption{Exploratory pilot: paired changes in correctness and explicit retention.
Intervals resample independent base pairs, stratified by mutation family and
change status. Necessary scopes include numerical objectives; Boolean-critical
scopes use a truth-value-flip definition. These metrics do not observe hidden reasoning.}
\\label{fig:mechanism-pilot}
\\end{figure}

Unexposed-manager prompts and requested seeds matched in 192 paired comparisons
per population. Normalized findings nevertheless differed in two workflow
comparisons and none in scheduling. New tests share identical manager computations
within a world and stochastic repetition, including the bypass control. This is
a new coupling intervention, not a retrospective repair of pilot outputs.
'''
(OUT/'mechanism-pilot.tex').write_text(tex)

suites=('mechanism-development-v1','fresh-probe-v1','mechanism-validation-v1','mechanism-heldout-v1')
available={}
for suite in suites:
    path=Path('results',suite,'analysis.json')
    if path.exists():
        result=json.loads(path.read_text())
        if result.get('complete'):available[suite]=result
extension='\\section{Prospective Mechanism Extension}\n'
extension+='The amendment separates decisive, nondecisive, limited favorable and resolvable false findings, uniform repetition, and no added repetition. Development uses one model and 24 reused base pairs; all wider searches are exploratory. The narrow fresh-verification probe shares an initial report and source data across conditions and makes no independence claim. Fresh held-out allocation uses separate validation, a fixed precision/resource rule and disjoint identifiers.\\par\n'
extension+='The three prospective scheduling contrasts are decisive versus common-finding repetition (correctness), common-finding repetition versus single presentation (unrepeated necessary-claim retention), and the repetition-by-raw-access interaction (correctness). Bypass input growth and observed matching residuals limit mechanism attribution.\\par\n'
for suite in suites:
    result=available.get(suite)
    label=suite.replace('-',' ')
    if result is None:
        extension+='\\textbf{'+label+':} no complete model analysis is available; no numerical result is claimed.\\par\n'
        continue
    extension+='\\textbf{'+label+':} '+str(result['analyzed_trajectories'])+' completed trajectories. '
    if suite.startswith('fresh'):
        extension+='This is a six-base development diagnostic; singleton-stratum confidence intervals are unavailable.\\par\n'
        continue
    extension+='Development and validation remain exploratory.\\par\n' if result['phase']!='heldout' else 'Only the three prespecified scheduling contrasts are confirmatory.\\par\n'
    chosen=[r for r in result['contrasts'] if r['kind']=='schedule' and
            (r['contrast'],r['metric']) in [('P1','correct'),('P2','unrepeated_necessary_retention'),('P3','correct')]]
    if chosen:
        extension+='\\begin{center}\\small\\begin{tabular}{lrr}\\toprule Contrast & Change, pp [95\\% interval] & Bases\\\\\\midrule\n'
        for row in chosen:
            extension+=row['contrast']+' & '+interval(row)+' & '+str(row['clusters'])+'\\\\\n'
            trace.append({'source':'results/'+suite+'/analysis.json','row':row})
        extension+='\\bottomrule\\end{tabular}\\end{center}\n'
    fig,ax=plt.subplots(figsize=(7,3.3))
    plotted=[]
    for name in ('decisive_repetition','nondecisive_repetition','favorable_infeasible_repetition','uniform_repetition','P3'):
        for metric,color,offset in [('correct','#1d5c8c',-.08),('unrepeated_necessary_retention','#a74a12',.08)]:
            row=next((r for r in result['contrasts'] if r['kind']=='schedule' and r['contrast']==name and r['metric']==metric),None)
            if row is None:continue
            y=len(plotted) if name not in plotted else plotted.index(name)
            if name not in plotted:plotted.append(name)
            x=100*row['estimate'];err=None if row['lower'] is None else [[x-100*row['lower']],[100*row['upper']-x]]
            ax.errorbar(x,y+offset,xerr=err,fmt='o',color=color,capsize=2,label=metric if y==0 else None)
    ax.set_yticks(range(len(plotted)),[n.replace('_',' ') for n in plotted]);ax.invert_yaxis();ax.axvline(0,color='gray',lw=.8)
    ax.set_xlabel('Paired change (percentage points)');ax.legend(frameon=False);fig.tight_layout()
    folder=Path('results',suite,'figures');folder.mkdir(exist_ok=True);fig.savefig(folder/'targets-and-retention.pdf');plt.close(fig)
    trace.append({'source':'results/'+suite+'/analysis.json','figure':'targets-and-retention.pdf','source_sha256':digest(result)})
(OUT/'mechanism-extension.tex').write_text(extension)
(OUT/'mechanism_numerical_traceability.json').write_text(json.dumps({'pilot_analysis_sha256':digest(audit),
    'figure_data_sha256':digest(effects),'entries':trace},indent=2)+'\n')
status={'amendment':'mechanism-v1','complete_extension_analyses':list(available),
        'pending_extension_analyses':[s for s in suites if s not in available],
        'human_scientific_review':'pending','submission_ready':False}
Path('records/mechanism-report-status.json').write_text(json.dumps(status,indent=2)+'\n')
print(json.dumps(status))
