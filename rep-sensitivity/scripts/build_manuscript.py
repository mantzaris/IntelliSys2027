"""Refresh completed-result blocks and figures in the single-file manuscript.

No model calls, selection of cases, or reading of partial held-out choices.
Narrative outside marked blocks and the inline bibliography are preserved.
"""
from collections import defaultdict
import json
from pathlib import Path
import re
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

from manuscript_content import ROOT, PAPER, completed, copy_figure, sha, update_blocks
sys.path.insert(0, str(ROOT / 'src'))
from rep_sensitivity.schema import Job, Candidate, ScheduleWorld
from rep_sensitivity.verification import verify, reference_verify

LABELS = {'qwen3': 'Qwen3-14B', 'phi4': 'Phi-4'}
CONDITIONS = ('single', 'exact', 'paraphrase')
COLORS = {'single': '#59656d', 'exact': '#226c9d', 'paraphrase': '#b66a20'}
TRACE = {}
plt.rcParams.update({'font.size': 11, 'axes.titlesize': 11, 'axes.labelsize': 11,
                     'xtick.labelsize': 10, 'ytick.labelsize': 10,
                     'pdf.fonttype': 42, 'ps.fonttype': 42})


def read(suite, name='analysis.json'):
    p = ROOT / 'results' / suite / name
    d = json.loads(p.read_text())
    TRACE[str(p.relative_to(ROOT))] = sha(p)
    return d


def pct(x):
    return f'{100*x:.2f}'


def ci(x):
    if any(x.get(k) is None for k in ('estimate','lower','upper')):
        return 'not estimable'
    value=f"{100*x['estimate']:+.2f} [{100*x['lower']:+.2f}, {100*x['upper']:+.2f}]"
    return value+(r'$^{\dagger}$' if x.get('degenerate_bootstrap') else '')


def table(caption, label, columns, rows, layout):
    return '\n'.join([r'\begin{table}[htbp]', r'\centering\small', r'\setlength{\tabcolsep}{4pt}',
        r'\caption{' + caption + r'}\label{' + label + '}',
        r'\begin{tabular}{' + layout + r'}\toprule',
        ' & '.join(columns) + r'\\\midrule',
        *[' & '.join(map(str, row)) + r'\\' for row in rows],
        r'\bottomrule\end{tabular}', r'\end{table}'])


def save(fig, name):
    fig.savefig(PAPER.parent / name, bbox_inches='tight',
                metadata={'CreationDate': None, 'ModDate': None})
    plt.close(fig)


def checked_example():
    answers = {}
    for capacity in (1, 2):
        w = ScheduleWorld(
            [Job('A', 2, {'M': 1}), Job('B', 2, {'M': 1}),
             Job('C', 1, {'N': 1})], {'M': capacity, 'N': 1},
            [('A', 'C'), ('B', 'C')],
            [Candidate('P', {'A': 0, 'B': 0, 'C': 2}),
             Candidate('Q', {'A': 0, 'B': 2, 'C': 4})], ['P', 'Q'])
        a, b = verify(w), reference_verify(w)
        assert a['answer'] == b['answer'] == ('Q' if capacity == 1 else 'P')
        assert {c: v['objective'] for c, v in a['candidates'].items()} == b['objective'] == {'P': 3, 'Q': 5}
        assert {c: v['feasible'] for c, v in a['candidates'].items()} == b['feasible']
        answers[str(capacity)] = a
    return answers


def architecture():
    fig, ax = plt.subplots(figsize=(6.35, 2.65))
    ax.set(xlim=(0, 10), ylim=(-.2, 4.2)); ax.axis('off')
    def box(x, y, w, h, text, color='#e5eff5'):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.08',
                     facecolor=color, edgecolor='#46616f', linewidth=.9))
        ax.text(x+w/2, y+h/2, text, ha='center', va='center', fontsize=10)
    def arrow(x1,y1,x2,y2):
        ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                    arrowprops={'arrowstyle':'->','lw':1,'color':'#46616f'})
    ax.text(0,3.95,'Flat: one model call',fontweight='bold',fontsize=11)
    box(.15,2.75,3.1,.72,'All worker reports\n+ selected copies')
    box(6.6,2.75,2.9,.72,'Root decision', '#e9eee6')
    arrow(3.35,3.11,6.5,3.11)
    ax.text(4.9,3.35,'raw reports',ha='center',fontsize=9)
    ax.text(0,2.18,'Hierarchy: three model calls',fontweight='bold',fontsize=11)
    box(.15,.6,2.1,.85,'Worker reports\nand copies')
    box(3.05,1.25,2.0,.62,'Manager 1')
    box(3.05,.05,2.0,.62,'Manager 2')
    box(6.6,.6,2.9,.85,'Root decision\nsummaries only', '#e9eee6')
    arrow(2.35,1.2,2.95,1.55); arrow(2.35,.85,2.95,.38)
    arrow(5.15,1.55,6.5,1.15); arrow(5.15,.38,6.5,.85)
    ax.text(5.85,1.95,'summary',ha='center',fontsize=9)
    save(fig,'aggregation-architecture.pdf')


def figures(p, v, numeric):
    architecture()
    fig, axes = plt.subplots(1,2,figsize=(6.35,3.25),sharey=True)
    groups=[('Pilot / Qwen3',p, 'qwen3'),('Validation / Qwen3',v,'qwen3'),('Validation / Phi-4',v,'phi4')]
    for ax, org in zip(axes, ('flat','hierarchical')):
        for i,(label,data,model) in enumerate(groups):
            for delta,c in ((-.11,'exact'),(.11,'paraphrase')):
                if data is p:
                    r=next(x for x in p['comparisons'] if (x['dimension'],x['kind'],x['organization'],x['condition'])==('overall','schedule',org,c))
                else:
                    r=next(x for x in v['comparisons'] if (x['model'],x['kind'],x['organization'],x['policy'],x['contrast'])==(model,'schedule',org,'ordinary+checklist',c+' - single'))
                ax.errorbar(100*r['estimate'],i+delta,
                    xerr=[[100*(r['estimate']-r['lower'])],[100*(r['upper']-r['estimate'])]],
                    fmt='o' if c=='exact' else 's',color=COLORS[c],capsize=3,label=c if i==0 else None)
        ax.axvline(0,color='#888888',lw=.8);ax.grid(axis='x',alpha=.2)
        ax.set_title('Flat' if org=='flat' else 'Hierarchical')
        ax.set_xlabel('Accuracy change (pp)');ax.set_xlim(-15,26)
        ax.set_xticks([-10,0,10,20])
    axes[0].set_yticks(range(3),[g[0]+'\n'+('12 bases' if i==0 else '18 bases') for i,g in enumerate(groups)])
    axes[0].invert_yaxis()
    fig.legend(*axes[1].get_legend_handles_labels(),loc='lower center',ncol=2,fontsize=9)
    fig.tight_layout(rect=(0,.12,1,1));save(fig,'repetition-accuracy-effects.pdf')

    fig, axes=plt.subplots(1,3,figsize=(6.35,2.45),sharey=True)
    for ax,(title,data,model) in zip(axes,groups):
        if data is p:
            r=next(x for x in p['comparisons'] if (x['dimension'],x['kind'],x['organization'],x['condition'])==('overall','schedule','hierarchical','exact'))
        else:
            r=next(x for x in v['comparisons'] if (x['model'],x['kind'],x['organization'],x['policy'],x['contrast'])==(model,'schedule','hierarchical','ordinary+checklist','exact - single'))
        ids=sorted(r['base_effects']);vals=[100*r['base_effects'][b] for b in ids]
        ax.bar(range(1,len(ids)+1),vals,color=[COLORS['exact'] if x>=0 else '#b64c3c' for x in vals],width=.8)
        ax.axhline(0,color='#888888',lw=.8);ax.set_title(title.replace(' / ','\n'))
        ax.set_xticks([1,6,12] if len(ids)==12 else [1,9,18])
        ax.set_xlabel('Base problem');ax.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('Accuracy change (pp)');axes[0].set_ylim(-50,100)
    fig.tight_layout();save(fig,'case-level-repetition-effects.pdf')

    fig=plt.figure(figsize=(6.35,4.15))
    gs=fig.add_gridspec(2,3,height_ratios=[.8,2],hspace=.55,wspace=.15)
    top=fig.add_subplot(gs[0,:]);top.axis('off')
    texts=['Worker reports\n8, 9, 9','Raw manager\ntrue, true, true','Parsed / root input\ntrue, true, true']
    for i,t in enumerate(texts):
        top.text(.15+.35*i,.5,t,ha='center',va='center',fontsize=10,
            bbox={'boxstyle':'round,pad=.45','facecolor':'#e5eff5' if i==0 else '#f4e5df','edgecolor':'#68747b'})
        if i<2:top.annotate('',xy=(.35+.35*i,.5),xytext=(.28+.35*i,.5),
            arrowprops={'arrowstyle':'->','color':'#68747b'})
    top.set_title('Observed example: the change is already in raw model output',fontsize=10,pad=10)
    panels=[('pilot-v7','qwen3','Pilot Qwen3\n12 bases, 288 fields/arm'),('validation-v7','qwen3','Validation Qwen3\n18 bases, 648 fields/arm'),('validation-v7','phi4','Validation Phi-4\n18 bases, 648 fields/arm')]
    for i,(suite,model,title) in enumerate(panels):
        ax=fig.add_subplot(gs[1,i])
        rows=[{k:sum(x[k] for x in numeric['groups'] if (x['suite'],x['model'],x['kind'],x['condition'])==(suite,model,'schedule',c))
               for k in ('objective_fields','objective_boolean_replacement','objective_omitted','objective_preserved')} for c in CONDITIONS]
        for offset,key,label,color in [(-.25,'objective_preserved','Preserved','#226c9d'),(0,'objective_boolean_replacement','Boolean','#b64c3c'),(.25,'objective_omitted','Omitted','#d3ad61')]:
            ax.bar(np.arange(3)+offset,[100*r[key]/r['objective_fields'] for r in rows],width=.24,color=color,label=label)
        ax.set_xticks(range(3),['Single','Exact','Para.']);ax.set_title(title,fontsize=9)
        ax.set_ylim(0,105);ax.set_yticks([0,50,100]);ax.grid(axis='y',alpha=.2)
        if i==0:ax.set_ylabel('Objective fields (%)')
        else:ax.set_yticklabels([])
    fig.legend(*ax.get_legend_handles_labels(),loc='lower center',ncol=3,fontsize=9)
    fig.subplots_adjust(bottom=.17);save(fig,'numerical-preservation-pipeline.pdf')

    fig, axes=plt.subplots(1,2,figsize=(6.35,2.9),sharey=True)
    for ax,model in zip(axes,('qwen3','phi4')):
        for org,marker in (('flat','o'),('hierarchical','s')):
            for c in CONDITIONS:
                r=next(x for x in v['absolute'] if (x['model'],x['kind'],x['organization'],x['condition'])==(model,'schedule',org,c))
                ax.scatter((r['input_tokens']+r['output_tokens'])/r['trajectories']/1000,
                           100*r['accuracy'],marker=marker,color=COLORS[c],s=45,
                           label=('Flat' if org=='flat' else 'Hierarchy')+' / '+c)
        ax.set_title(LABELS[model]);ax.set_xlabel('Tokens / decision (thousands)');ax.grid(alpha=.2)
        ax.set_ylim(60,100)
    axes[0].set_ylabel('Accuracy (%)')
    fig.legend(*axes[1].get_legend_handles_labels(),loc='lower center',ncol=3,fontsize=8)
    fig.tight_layout(rect=(0,.18,1,1));save(fig,'validation-cost-accuracy.pdf')


def future_results():
    """Small evidence-only completion blocks. Pending stages produce no tables."""
    main, mechanism, appendix = [], [], []
    d=completed('main-v7')
    if d:
        TRACE['results/main-v7/analysis.json']=sha(ROOT/'results/main-v7/analysis.json')
        main.append(r'\subsection{Completed Main Held-Out Evaluation}')
        for kind in ('schedule','workflow'):
            dest=main if kind=='schedule' else appendix
            if kind=='workflow':dest.append(r'\section{Held-Out Workflow Results}')
            rows=[]
            for model in ('qwen3','phi4'):
                for org in ('flat','hierarchical'):
                    rs=[x for x in d['summary'] if (x['model'],x['kind'],x['organization'])==(model,kind,org)]
                    if not rs:continue
                    cells=[]
                    for c in CONDITIONS:
                        cs=[x for x in rs if x['condition']==c]
                        cells.append(pct(sum(x['correct'] for x in cs)/sum(x['n'] for x in cs)))
                    n=sum(x['n'] for x in rs if x['condition']=='single')
                    rows.append([LABELS[model],org,str(rs[0]['clusters']),str(n),*cells])
            dest.append(table('Held-out '+kind+' accuracy (percent), equally averaged over policies.',
                'tab:heldout-'+kind,['Model','Organization','Bases','N/arm','Single','Exact','Para.'],rows,'llrrrrr'))
            dest.append('Table \\ref{tab:heldout-'+kind+'} compares absolute performance within each organization. '
                        'Each condition retains the same independent bases and essential information.')
            rows=[]
            for model in ('qwen3','phi4'):
                for contrast in ('H1_exact','H1_paraphrase','H2','H3','H4_error','H4_retention'):
                    r=next(x for x in d['contrasts'] if (x['model'],x['kind'],x['contrast'])==(model,kind,contrast))
                    rows.append([LABELS[model],contrast.replace('_',r'\_'),ci(r),r['clusters']])
            dest.append(table('Frozen held-out contrasts (pp). Positive H1 values indicate harm.',
                'tab:heldout-effects-'+kind,['Model','Contrast','Estimate [95\\% CI]','Bases'],rows,'llrr'))
            dest.append('Table \\ref{tab:heldout-effects-'+kind+'} gives direct paired contrasts. '
                        'H1 averages organizations and policies. H2 contrasts the repetition effect on paired-world failure between consequential and harmless edits. '
                        'H3 is the hierarchy-minus-flat repetition-harm interaction, averaging exact and paraphrased repetition. '
                        'H4 compares scope-aware consolidation with the checklist, on error under repeated consequential cases and on changed-scope retention under consequential hierarchy. '
                        'Positive H4 retention values favor consolidation. A dagger marks a collapsed empirical interval, not certainty about the population. '
                        'These model-specific completed estimates remain distinct from development. The intervals are base-cluster intervals; '
                        'error contrasts retain the original error scale and retention contrasts retain the retention scale.')
    # Each standalone result must be complete under its own raw-inventory audit.
    d=completed('numerical-preservation-v1')
    if d:
        TRACE['results/numerical-preservation-v1/analysis.json']=sha(ROOT/'results/numerical-preservation-v1/analysis.json')
        mechanism.append(r'\subsection{Objective-Preservation Replay}')
        mechanism.append(f"The completed exploratory replay uses {d['base_pairs']} reused development bases and {d['trajectories']} fresh root calls. "
            'It crosses cached summaries from single and exact-copy upstream presentation with objective-only repair from the worker reports available to each branch. '
            'Repair preserves candidate, units, scope, and applicability and adds no hidden final answer or new feasibility conclusion. '
            'All four arms have fresh root responses. This estimates interventions on fixed summaries, not causal mediation through a fresh complete hierarchy.')
        rows=[]
        for r in d['absolute']:
            if r.get('population','all')!='all':continue
            rows.append([r['arm'],pct(r['accuracy']),str(r['trajectories'])])
        mechanism.append(table('Objective-preservation replay. A/B are ordinary delivery and C/D repair.',
            'tab:preservation-replay',['Arm','Accuracy (\\%)','Root calls'],rows,'lrr'))
        r=next(x for x in d['contrasts'] if (x['population'],x['contrast'],x['metric'])==('all','repetition_by_preservation','correct'))
        mechanism.append('Table \\ref{tab:preservation-replay} separates absolute performance from the paired contrast. '
            'The repetition-by-preservation interaction is '+ci(r)+
            ' percentage points. Six reused clusters provide diagnostic evidence only. The targeted sample includes two bases with baseline numerical loss and four without it.')
    d=completed('root-diagnostic-v1')
    vis=ROOT/'results/root-diagnostic-v1/visible-information-v2.json'
    if d and vis.exists() and json.loads(vis.read_text()).get('complete'):
        x=json.loads(vis.read_text());TRACE[str(vis.relative_to(ROOT))]=sha(vis)
        mechanism.append(r'\subsection{Fixed-Input Root Diagnostic}')
        mechanism.append('This exploratory diagnostic uses six reused development bases and 192 fresh root calls. '
            'Within each summary-delivery interface the incoming summaries stay fixed. Selective repetition targets each candidate objective separately, '
            'and uniform repetition targets all objectives. The separate lossless interface preserves worker-report facts and is an information intervention. '
            'The diagnostic contains no paraphrase treatment.')
        rows=[[r['transport'].replace('_',' '),r['contrast'].replace('_',' '),ci(r)] for r in x['effects']
              if r['contrast'] in ('objective0 - F','objective1 - F','objective2 - F','uniform_objectives - F')]
        mechanism.append(table('Root-only accuracy effects (pp), with descriptive six-base intervals.',
            'tab:root-diagnostic',['Delivery','Repetition contrast','Effect [95\\% CI]'],rows,'llr'))
        mechanism.append('Table \\ref{tab:root-diagnostic} compares repetition with a newly generated baseline root response under the same delivery condition. '
            'Its intervals resample six whole bases without stratification and are exploratory. Information support and world correctness are scored separately.')
    obj=ROOT/'results/objective-confirmation-v1/analysis.json'
    if obj.exists():
        data=json.loads(obj.read_text())
        for d in data.get('model_results',[]):
            if not d.get('complete'):continue
            TRACE[str(obj.relative_to(ROOT))]=sha(obj)
            mechanism.append(r'\subsection{Fresh Objective Confirmation: '+LABELS[d['model']]+'}')
            mechanism.append(f"This completed model evaluation contains {d['independent_base_pairs']} fresh scheduling bases, "
                f"{d['trajectories']} trajectories, and {d['physical_calls']} accepted calls. "
                'The frozen arms compare selective and balanced repetition in the same hierarchy. Balanced repetition has a greater presentation dose and input length.')
            rows=[[r['arm'].replace('_',' '),pct(r['metrics']['correct']['mean']),pct(r['metrics']['invalid_selection']['mean'])]
                  for r in d['absolute']]
            mechanism.append(table('Fresh confirmation accuracy and infeasible selections (percent).',
                'tab:confirmation-'+d['model'],['Arm','Accuracy','Infeasible'],rows,'lrr'))
            mechanism.append('Table \\ref{tab:confirmation-'+d['model']+'} reports all frozen arms. '
                'The following direct contrasts retain matched worlds and stochastic repetitions within each base.')
            for r in d['contrasts']:
                if r['primary']:mechanism.append(r['contrast'].replace('_',r'\_')+': '+ci(r)+' percentage points.')
    # Other frozen extensions retain their complete tables in the analysis package;
    # expose compact counts and primary effects without inventing a conclusion.
    for suite,title in [('mechanism-development-v1','Targeted Development'),
                        ('fresh-probe-v1','Fresh-Verification Diagnostic'),
                        ('mechanism-validation-v1','Mechanism Validation'),
                        ('mechanism-heldout-v1','Mechanism Confirmation'),
                        ('supporting-v7','Held-Out Supporting Controls'),
                        ('live-v8','Held-Out Live Workers')]:
        d=completed(suite)
        if not d:continue
        TRACE[f'results/{suite}/analysis.json']=sha(ROOT/'results'/suite/'analysis.json')
        appendix.append(r'\section{'+title+'}')
        appendix.append('The complete frozen analysis is available in the reproducibility package. '
            'The following estimates are retained with their original outcomes and cluster definitions.')
        # Designs have different contrast schemas, so do not silently relabel them.
        rows=[]
        for r in d.get('contrasts',[]):
            if r.get('kind','schedule')!='schedule' or r.get('model')=='equal_model_average':continue
            if r.get('estimate') is None or not r.get('interval_available',True):continue
            name=r.get('difference',r.get('contrast','contrast'))
            if isinstance(name,str):name=name.replace('_',r'\_')
            rows.append([LABELS.get(r.get('model'),r.get('model','Qwen3-14B')),name,ci(r),r.get('clusters','--')])
            if len(rows)>=6:break  # Fixed manifest order, never selection by effect.
        if rows:
            appendix.append(table(title+' contrasts in fixed manifest order (pp).',
                'tab:'+suite,['Model','Contrast','Estimate [95\\% CI]','Bases'],rows,'lp{.32\\linewidth}rr'))
            appendix.append('Table \\ref{tab:'+suite+'} retains the first six eligible contrasts in their frozen order. '
                            'The full result record contains the remaining contrasts and their denominators.')
    d=completed('adjacent-explorations-v1')
    if d:
        TRACE['results/adjacent-explorations-v1/analysis.json']=sha(ROOT/'results/adjacent-explorations-v1/analysis.json')
        appendix.append(r'\section{Exploratory Feedback and Apparent Consensus}')
        appendix.append('These studies reuse four development bases and are exploratory. Feedback compares prior public decisions with fresh evaluation and a length control across three rounds, including a defined consequential or harmless update. '
                        'The relay comparison preserves explicit common ancestry and varies worker identity and authority-suggesting role labels, without independent verification.')
        for name,s in d.get('experiments',{}).items():
            if not s.get('complete'):continue
            appendix.append(name.replace('_',r'\_')+': '+str(s.get('calls','recorded'))+' model calls.')
            rows=[]
            for r in s.get('contrasts',[]):
                if r.get('metric')=='correct' and len(rows)<4:
                    rows.append([r['contrast'].replace('_',r'\_'),ci(r),r.get('increases','--'),r.get('decreases','--')])
            if rows:
                appendix.append(table('Exploratory paired accuracy effects from four reused bases.',
                    'tab:adjacent-'+name,['Contrast','Effect [95\\% CI]','Corrections','Regressions'],rows,'p{.38\\linewidth}rrr'))
                appendix.append('Table \\ref{tab:adjacent-'+name+'} reports paired decision effects. '
                    'A change in choice alone does not establish a belief about source independence or a feedback mechanism.')
    return '\n\n'.join(main),'\n\n'.join(mechanism),'\n\n'.join(appendix)


def build():
    TRACE.clear()
    p=read('pilot-interpretation-v2')
    v=read('validation-repetition-v1')
    numeric=read('numerical-pipeline-v1')
    support=read('numerical-pipeline-v1','visible-support-v3.json')
    validation=read('validation-v7')
    assert v['complete'] and numeric['complete'] and validation['complete']
    assert p['trajectories']==1152 and p['base_pairs']==24
    example=checked_example()
    figures(p,v,numeric)
    blocks={}
    blocks['stage-table']=table('Completed replay stages. Bases are independent problems, shared across models.',
        'tab:stages',['Stage','Model',r'\shortstack{All\\bases}',r'\shortstack{Scheduling\\bases}','Trajectories'],
        [['Pilot','Qwen3-14B','24','12','1,152'],
         ['Validation','Qwen3-14B','36','18','2,592'],
         ['Validation','Phi-4','same 36','same 18','2,592']],'llrrr')
    pending=[title for suite,title in [('main-v7','the main held-out replay'),('objective-confirmation-v1','fresh objective confirmation'),
        ('root-diagnostic-v1','the root-only diagnostic'),('numerical-preservation-v1','the objective-preservation replay')]
        if completed(suite) is None]
    blocks['result-status']=('This draft reports the completed pilot, exploratory validation reanalysis, and trace audits. '
        'The pilot contains 24 independent base pairs and 1,152 trajectories. Validation contains 36 additional independent pairs shared across two models and 5,184 trajectories. '
        'The smaller development controls and live-worker checks are diagnostic rather than confirmation. '+
        (r'\textbf{Pending results.} Results remain pending for '+', '.join(pending)+', and the remaining frozen supporting evaluations. '
         'No partial held-out outcomes enter the results below.' if pending else
         'Completed held-out and intervention results are reported separately below.'))
    focus=[]
    for c in ('exact','paraphrase'):
        r=next(x for x in p['comparisons'] if (x['dimension'],x['kind'],x['organization'],x['condition'])==('overall','schedule','hierarchical',c))
        focus.append(('Pilot Qwen3',c,r))
    for model in ('qwen3','phi4'):
        for c in ('exact','paraphrase'):
            r=next(x for x in v['comparisons'] if (x['model'],x['kind'],x['organization'],x['policy'],x['contrast'])==(model,'schedule','hierarchical','ordinary+checklist',c+' - single'))
            focus.append(('Validation '+('Qwen3' if model=='qwen3' else 'Phi-4'),c,r))
    blocks['accuracy-results']=(
        'For hierarchical scheduling, the pilot compares 96 decisions per presentation condition from 12 independent bases. '
        'Each base contributes two worlds, two policies, and two stochastic repetitions. Validation contributes 144 decisions per condition and model from 18 bases under the same two-policy average.\n\n'+
        table('Hierarchical scheduling, two shared policies. Changes use paired base-cluster 95\\% intervals.',
        'tab:accuracy',['Stage / model','Repeat','Single \\%','Repeated \\%','Change, pp [95\\% CI]'],
        [[name,c,pct(r['baseline']),pct(r['repeated']),ci(r)] for name,c,r in focus],'llrrr')+
        '\n\n'+table('Paired decision transitions for Table \\ref{tab:accuracy}. Unchanged includes correct and incorrect choices.',
        'tab:transitions',['Stage / model','Repeat','Bases','Corrections','Regressions','Unchanged'],
        [[name,c,r['clusters'],r['improvements'],r['regressions'],r['unchanged']] for name,c,r in focus],'llrrrr')+
        '\n\nTable \\ref{tab:transitions} separates corrections from regressions. '
        'Exact repetition raises pilot accuracy from 81.25\\% to 94.79\\%, a gain of 13.54 percentage points '
        '(95\\% interval 4.17 to 22.92). Paraphrases raise it to 91.67\\%, a gain of 10.42 points (1.04 to 19.79). '
        'In validation, the corresponding exact-copy effects are -3.47 points for Qwen3 and +1.39 for Phi-4. '
        'Both validation intervals span zero. No parsing or truncation change explains these pilot corrections.\n\n'
        'Pilot exact-copy effects are positive on six bases, negative on one, and zero on five. '
        'One base contributes seven of the 14 corrections. Leaving it out descriptively lowers the gain to 6.82 points, '
        'but it remains in every primary estimate. Across all single-base omissions, the pilot exact-copy gain ranges from 6.82 to 15.91 points. '
        'Figure \\ref{fig:cases} displays every base rather than selecting favorable examples.')
    direct=[]
    inter=[]
    for model in ('qwen3','phi4'):
        r=next(x for x in v['comparisons'] if (x['model'],x['kind'],x['organization'],x['policy'],x['contrast'])==(model,'schedule','hierarchical','ordinary+checklist','exact - paraphrase'))
        direct.append(LABELS[model]+' '+ci(r))
        r=next(x for x in v['hierarchy_interactions'] if (x['model'],x['kind'],x['policy'],x['contrast'])==(model,'schedule','ordinary+checklist','exact - single'))
        inter.append(LABELS[model]+' '+ci(r))
    blocks['organization-results']=(
        'The flat pilot scheduling arms all achieve 100\\% on these 12 bases, leaving no observed room for improvement. '
        'Validation flat accuracy under the shared policies changes from 94.44\\% to 90.28\\% with exact copies for Qwen3, '
        'and from 93.75\\% to 90.97\\% for Phi-4. The exact-copy hierarchy interactions are '+
        ', and '.join(inter)+' percentage points. These direct differences of effects do not establish that hierarchy consistently amplifies or suppresses repetition.\n\n'
        'The direct hierarchical exact-minus-paraphrase contrasts in validation are '+ ', and '.join(direct)+
        ' percentage points. Separate significance judgments for the two repetition arms would not test this difference.')
    prs=[r for r in v['paired_world'] if r['kind']=='schedule' and r['organization']=='hierarchical' and r['contrast']=='exact - single']
    blocks['paired-world-results']=table('Both worlds correct in hierarchical validation. Each row has nine bases and 54 paired trials per arm.',
        'tab:paired-worlds',['Model','Edit','Single \\%','Exact \\%','Change, pp [95\\% CI]'],
        [[LABELS[r['model']],'consequential' if r['decision_changed'] else 'harmless',pct(r['baseline']),pct(r['repeated']),ci(r)] for r in prs],'llrrr')
    for model in ('qwen3','phi4'):
        r=next(x for x in v['consequential_minus_harmless'] if (x['model'],x['kind'],x['organization'],x['contrast'])==(model,'schedule','hierarchical','exact - single'))
        blocks['paired-world-results']+='\n\n'+LABELS[model]+': the consequential-minus-harmless difference in repetition effects is '+ci(r)+' percentage points.'
    blocks['paired-world-results']+='\n\nQwen3 has a lower paired-world success rate with exact copies on consequential edits, but the direct contrast with harmless edits remains uncertain. The corresponding Phi-4 contrast is also imprecise. Neither comparison establishes a general selective loss of consequential differences.'
    blocks['policy-results']='In validation, more elaborate consolidation instructions do not produce a uniform ordering across models, organizations, and presentation conditions. The full policy table retains improvements and regressions. The shared structured response contract and the small number of independent bases limit claims about one policy being generally preferable.'
    rows=[]
    for suite,model,label,n in [('pilot-v7','qwen3','Pilot Qwen3',12),('validation-v7','qwen3','Validation Qwen3',18),('validation-v7','phi4','Validation Phi-4',18)]:
        rr=[]
        for c in CONDITIONS:
            rs=[x for x in numeric['groups'] if (x['suite'],x['model'],x['kind'],x['condition'])==(suite,model,'schedule',c)]
            rr.append((sum(x['objective_boolean_replacement'] for x in rs),sum(x['objective_fields'] for x in rs)))
        rows.append([label,*[str(a)+'/'+str(b) for a,b in rr]])
    blocks['numerical-results']=table('Boolean objective fields in hierarchical scheduling. Pilot uses two policies, validation three.',
        'tab:boolean',['Group','Single','Exact','Paraphrase'],rows,'lrrr')
    blocks['numerical-results']+=('\n\nFigure \\ref{fig:numerical} separates preserved numerical fields from Boolean replacements and omissions. '
        'Table \\ref{tab:boolean} counts each candidate objective once per trajectory, regardless of copies. '
        'The pilot reduction in Boolean replacements is not repeated in validation: Qwen3 has 53 such fields without repetition and 64 with exact copies, while Phi-4 has 156 in both arms. '
        'Every numerical value emitted at a known objective key in the audited summaries matches its source. This does not count omitted, unresolved, or ill-typed values as preserved.\n\n')
    nr=[]
    for suite,model,label in [('pilot-v7','qwen3','Pilot Qwen3'),('validation-v7','qwen3','Validation Qwen3'),('validation-v7','phi4','Validation Phi-4')]:
        x=next(x for x in numeric['comparisons'] if (x['suite'],x['model'],x['kind'],x['policy'],x['contrast'],x['metric'])==(suite,model,'schedule','ordinary+checklist','exact - single','objective_retention'))
        nr.append(label+' '+ci(x))
    blocks['numerical-results']+='Using the same two policies as Table \\ref{tab:accuracy}, exact-copy effects on objective preservation are '+ ', '.join(nr)+' percentage points. These are retention effects, not accuracy effects.'
    rows=[]
    for suite,model,label in [('pilot-v7','qwen3','Pilot Qwen3'),('validation-v7','qwen3','Validation Qwen3'),('validation-v7','phi4','Validation Phi-4')]:
        rs=[x for x in support['groups'] if (x['suite'],x['model'],x['condition'])==(suite,model,'single')]
        total=lambda k:sum(x[k] for x in rs)
        rows.append([label,total('trajectories'),total('decision_determined_from_uncontested_facts'),total('determinate_despite_representation_errors'),total('violates_uncontested_unique_decision')])
    blocks['sufficiency-results']=table('Unrepeated hierarchical scheduling. Violations use the uniquely supported contexts as denominator.',
        'tab:sufficiency',['Group','Trajectories','Unique choice','With invalid fields','Violations'],
        [[r[0],r[1],r[2],r[3],str(r[4])+'/'+str(r[2])] for r in rows],'lrrrr')
    blocks['sufficiency-results']+='\n\nPilot counts use two policies and validation counts use all three. The invalid-field column is a subset of contexts with a unique supported choice, not a repair of their representation. In validation, Qwen3 violates 24 of 195 uniquely supported choices and Phi-4 violates 15 of 133. These are conditional descriptive counts, not causal mediation estimates.'
    fr=[r for r in v['failure_locations'] if r['kind']=='schedule' and r['organization']=='hierarchical' and r['condition']=='single']
    columns=['necessary_fact_omitted','necessary_value_wrong_or_conflicted','visible_false_constraint_ignored','strictly_suboptimal_objective','response_contract_failure']
    blocks['failure-results']=table('Unrepeated hierarchical validation failure labels. Each model has 216 trajectories from 18 bases.',
        'tab:failures',['Model','Omission','Distortion','FAIL ignored','Suboptimal','Contract'],
        [[LABELS[r['model']],*[r[k] for k in columns]] for r in fr],'lrrrrr')
    blocks['failure-results']+='\n\nTable \\ref{tab:failures} separates communication and application failures. Omission and distortion concern propositions whose individual removal from the complete report set makes the answer undetermined. FAIL ignored means an infeasible selected candidate has a correctly delivered mandatory failure. Suboptimal means a feasible selection has a strictly worse objective than the best feasible candidate. Labels can overlap and should not be summed.'
    rows=[]
    for model in ('qwen3','phi4'):
        for org in ('flat','hierarchical'):
            for pol in ('ordinary','checklist','scope'):
                rs=[r for r in validation['summary'] if (r['model'],r['kind'],r['organization'],r['policy'])==(model,'schedule',org,pol)]
                rows.append([LABELS[model],'flat' if org=='flat' else 'hierarchy',pol,*[pct(next(r['accuracy'] for r in rs if r['condition']==c)) for c in CONDITIONS]])
    blocks['policy-table']=table('Validation scheduling accuracy (percent). Each cell has 18 bases and 72 trajectories.',
        'tab:policies',['Model','Organization','Policy','Single','Exact','Paraphrase'],rows,'lllrrr')
    cost=[]
    for model in ('qwen3','phi4'):
        r=next(x for x in v['absolute'] if (x['model'],x['kind'],x['organization'],x['condition'])==(model,'schedule','hierarchical','single'))
        cost.append(LABELS[model]+f" {r['allocated_seconds_per_correct']:.2f}")
    blocks['cost-results']=('Figure \\ref{fig:cost} includes every repetition arm under the three-policy validation average. '
        'Hierarchy consumes more tokens per decision and has lower accuracy than the corresponding flat organization in these data. '
        'This descriptive comparison combines access, summarization, and call-count changes. '
        'For unrepeated hierarchy, allocated batch seconds per correct decision are '+ ' and '.join(cost)+
        '. These values sum the recorded share of inference batch time and divide by correct decisions. They exclude model-loading overhead and are not per-request latency or monetary cost.')
    blocks['completed-main'],blocks['completed-mechanisms'],blocks['completed-supplement']=future_results()
    main=completed('main-v7')
    heldout_sentence=''
    if main:
        values=[x for x in main['contrasts'] if x['kind']=='schedule' and x['contrast']=='H1_exact' and x['model'] in LABELS]
        heldout_sentence='Completed held-out exact-copy error effects are '+ ', and '.join(LABELS[x['model']]+' '+ci(x) for x in values)+' percentage points.'
    development_result=(
        'Completed pilot and validation evaluations cover 24 and 36 independent base problems, respectively. '
        'On hierarchical scheduling, exact copies improve Qwen3 pilot accuracy from 81.25\\% to 94.79\\%, but validation effects are -3.47 percentage points for Qwen3 and +1.39 for Phi-4, with both cluster intervals spanning zero. ')
    if main:
        total_bases=sum(max(x['clusters'] for x in main['summary'] if x['kind']==kind)
                        for kind in {x['kind'] for x in main['summary']})
        central_result=(f'The completed held-out evaluation covers {total_bases} independent base problems shared across two models. '
                        +heldout_sentence+' Positive values indicate increased error. Earlier development benefits did not consistently generalize to validation. ')
    else:
        central_result=development_result
    blocks['abstract']=(
        'Repeated reports are common in language-model agent systems, but repeating a finding can both preserve it during communication and change how a decision maker uses it. '
        'We study these effects with a deterministic benchmark for selecting the best feasible candidate schedule, alongside a separate rule-based workflow task. '
        'Frozen worker reports isolate repeated presentation from fresh computation and new evidence. Paired worlds test correct responses to consequential edits and correct stability under harmless changes. '
        'Flat aggregation is compared with two intermediate managers whose summaries form the root input. '
        +central_result+
        'An audit of 6,336 manager summaries locates numerical objectives becoming Boolean values in raw generated summaries, with no subsequent parser or transport changes. '
        'This loss does not always make the decision ambiguous, and correct delivery does not guarantee a correct choice. '
        'The results motivate separate evaluation of representation fidelity, decision sufficiency, and decision accuracy.'+
        ('' if main else ' Main held-out and intervention results remain pending in this working draft.')+
        ' Conclusions are limited to the evaluated models, tasks, and structured communication interface.')
    blocks['conclusion']=(
        'Controlled replay separates repeated presentation from additional evidence. A large hierarchical pilot benefit is followed by smaller, mixed validation effects. '
        'Numerical objectives sometimes become Boolean assertions in manager output, but repetition does not reliably prevent this loss. '
        'Delivered information can remain sufficient despite a representation error, and a root can decide incorrectly despite a uniquely supported choice. '+
        (heldout_sentence+' ' if main else '')+
        'Separating fidelity, sufficiency, and accuracy gives a more informative account of reliability. '
        'It also identifies a practical goal for future interventions. Preserve the required propositions, then verify that the decision follows from them.')
    changed=update_blocks(blocks)
    record={'source':'manuscript/main.tex','single_file':True,'new_gpu_calls':0,'analysis_sources':TRACE,
            'builder_sha256':sha(Path(__file__)),'worked_example':example,
            'generated_blocks':list(blocks),'figure_basenames':re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}',PAPER.read_text()),
            'block_sha256':{k:__import__('hashlib').sha256(t.encode()).hexdigest() for k,t in blocks.items()},
            'human_scientific_review':'pending','submission_ready':False}
    (ROOT/'records/manuscript-content-v6.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'single_source_updated':changed,'complete_heldout':main is not None,'figures':len(record['figure_basenames'])}))
    return record


if __name__=='__main__':
    build()
