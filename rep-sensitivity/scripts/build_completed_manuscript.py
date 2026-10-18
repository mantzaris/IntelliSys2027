"""Refresh the scoped, completed-evidence manuscript without adding study arms.

All paper text and bibliography remain in manuscript/main.tex. Only marked
result blocks are replaced. Optional unfinished suites never create placeholders.
"""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from manuscript_content import ROOT, PAPER, sha, update_blocks
from build_manuscript import checked_example, architecture, table, save

MODELS=('qwen3','phi4')
LABELS={'qwen3':'Qwen3-14B','phi4':'Phi-4'}
CONDS=('single','exact','paraphrase')
COLORS={'single':'#58656d','exact':'#216b9b','paraphrase':'#bd6b22'}
POLICIES='ordinary+checklist+scope'
TRACE={}


def read(path):
    path=ROOT/path
    data=json.loads(path.read_text())
    if 'complete' in data and not data['complete']: raise ValueError('Incomplete manuscript evidence: '+str(path))
    TRACE[str(path.relative_to(ROOT))]=sha(path)
    return data


def pct(value): return f'{100*value:.2f}'
def signed(value): return f'{100*value:+.2f}' if abs(value)>1e-12 else '0.00'
def ci(row): return signed(row['estimate'])+' ['+signed(row['lower'])+', '+signed(row['upper'])+']'
def reverse(row): return {**row,'estimate':-row['estimate'],'lower':-row['upper'],'upper':-row['lower']}

def one(rows,**fields):
    found=[r for r in rows if all(r.get(k)==v for k,v in fields.items())]
    if len(found)!=1: raise ValueError((fields,len(found)))
    return found[0]


def absolute(data,model,condition,org='both',policies=POLICIES,kind='schedule'):
    return one(data['absolute'],model=model,condition=condition,organization=org,policies=policies,kind=kind)


def effect(data,model,condition,org='both',policies=POLICIES,kind='schedule'):
    return one(data['effects'],model=model,condition=condition,organization=org,policies=policies,kind=kind)


def primary(data,model,contrast,kind='schedule',accuracy=True):
    row=one(data['contrasts'],model=model,contrast=contrast,kind=kind)
    return reverse(row) if accuracy and contrast!='H4_retention' else row


def aggregate_numeric(data):
    groups=[]
    for suite,model,label in [('pilot-v7','qwen3','Pilot / Qwen3'),('validation-v7','qwen3','Validation / Qwen3'),('validation-v7','phi4','Validation / Phi-4')]:
        for cond in CONDS:
            rs=[r for r in data['groups'] if (r['suite'],r['model'],r['kind'],r['condition'])==(suite,model,'schedule',cond)]
            fields=('trajectories','objective_fields','objective_preserved','objective_boolean_replacement','objective_omitted','objective_number_changed','objective_scope_citation_mismatch','constraint_fields','constraint_preserved','constraint_omitted','constraint_distorted')
            groups.append(dict(suite=suite,model=model,label=label,condition=cond,base_pairs=rs[0]['base_pairs'],
                               **{k:sum(r[k] for r in rs) for k in fields}))
    return groups


def figures(main,detail,transitions,numeric,root_support):
    plt.rcParams.update({'font.size':11,'axes.titlesize':11,'axes.labelsize':11,'xtick.labelsize':10,
        'ytick.labelsize':10,'pdf.fonttype':42,'ps.fonttype':42})
    architecture()
    specs=[('Both organizations','both',POLICIES),('Flat, all policies','flat',POLICIES),
           ('Hierarchy, all policies','hierarchical',POLICIES),
           ('Flat / synthesis','flat','ordinary'),('Flat / checklist','flat','checklist'),
           ('Flat / scope','flat','scope'),('Hierarchy / synthesis','hierarchical','ordinary'),
           ('Hierarchy / checklist','hierarchical','checklist'),('Hierarchy / scope','hierarchical','scope')]
    fig,axes=plt.subplots(1,2,figsize=(6.6,4.5),sharey=True)
    for ax,model in zip(axes,MODELS):
        for y,(_,org,pol) in enumerate(specs):
            for shift,condition,marker in [(-.13,'exact','o'),(.13,'paraphrase','s')]:
                r=effect(detail,model,condition,org,pol)
                ax.errorbar(100*r['estimate'],y+shift,
                    xerr=[[100*(r['estimate']-r['lower'])],[100*(r['upper']-r['estimate'])]],
                    color=COLORS[condition],fmt=marker,capsize=2.4,ms=4,label=condition if y==0 else None)
        ax.axvline(0,color='#666',lw=.8);ax.axhline(2.5,color='#aaa',lw=.6)
        ax.set(xlim=(-10,10),xticks=[-10,-5,0,5,10],xlabel='Accuracy change (pp)',title=LABELS[model])
        ax.grid(axis='x',alpha=.2)
    axes[0].set_yticks(range(len(specs)),[s[0] for s in specs]);axes[0].invert_yaxis()
    fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',ncol=2,frameon=False)
    fig.tight_layout(rect=(0,.07,1,1));save(fig,'heldout-repetition-effects.pdf')

    fig,axes=plt.subplots(1,2,figsize=(6.35,3.25),sharey=True)
    names=['single_seed1_minus_seed0','exact_seed1_minus_seed0','exact_minus_single']
    for ax,model in zip(axes,MODELS):
        g=one(transitions['groups'],kind='schedule',model=model,organization='both')
        for i,key in enumerate(names):
            r=g['comparisons'][key];n=r['paired_comparisons'];a=100*r['totals']['correction']/n;b=100*r['totals']['regression']/n
            ax.bar(i,a,color='#216b9b',width=.65,label='Correction' if i==0 else None)
            ax.bar(i,b,bottom=a,color='#bd6b22',width=.65,label='Regression' if i==0 else None)
            e=r['intervals']['correctness_change'];v=100*e['estimate']
            ax.errorbar(i,v,yerr=[[v-100*e['lower']],[100*e['upper']-v]],fmt='none',ecolor='#222',capsize=3,lw=1)
        ax.set_xticks(range(3),['No repeat\n0 vs 1','Exact\n0 vs 1','Exact vs single\nsame index'])
        ax.set_title(LABELS[model]);ax.set_ylim(0,20);ax.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('Correctness changes (%)')
    fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',ncol=2,frameon=False)
    fig.tight_layout(rect=(0,.08,1,1));save(fig,'correctness-transitions.pdf')

    nrows=aggregate_numeric(numeric)
    fig,axes=plt.subplots(1,3,figsize=(6.6,2.9),sharey=True)
    for ax,(suite,model,title) in zip(axes,[('pilot-v7','qwen3','Pilot / Qwen3\n12 bases; 288 fields/arm'),('validation-v7','qwen3','Validation / Qwen3\n18 bases; 648 fields/arm'),('validation-v7','phi4','Validation / Phi-4\n18 bases; 648 fields/arm')]):
        rows=[one(nrows,suite=suite,model=model,condition=c) for c in CONDS]
        for offset,key,label,color in [(-.24,'objective_preserved','Preserved','#216b9b'),(0,'objective_boolean_replacement','Boolean','#bd6b22'),(.24,'objective_omitted','Omitted','#9ca7ac')]:
            ax.bar(np.arange(3)+offset,[100*r[key]/r['objective_fields'] for r in rows],width=.23,color=color,label=label)
        ax.set_xticks(range(3),['Single','Exact','Para.']);ax.set_ylim(0,105);ax.set_title(title,fontsize=10)
        ax.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('Objective fields (%)')
    fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',ncol=3,frameon=False)
    fig.tight_layout(rect=(0,.12,1,1));save(fig,'numerical-fidelity.pdf')

    fig,ax=plt.subplots(figsize=(6.35,3.2))
    bars=[('Frozen summaries\nno repetition','frozen_summaries','F'),
          ('Frozen summaries\nall objectives repeated','frozen_summaries','uniform_objectives'),
          ('Lossless delivery\nno repetition','lossless','F')]
    colors=['#216b9b','#76b7b2','#bd6b22','#b4babe']
    names=['Correct, uniquely supported','Correct, underdetermined','Wrong, uniquely supported','Wrong, underdetermined']
    for i,(_,org,arm) in enumerate(bars):
        r=one(root_support['groups'],organization=org,arm=arm)
        vals=[r['agreement_count'],r['correct']-r['agreement_count'],r['violates_uncontested_unique_decision'],
              r['trajectories']-r['correct']-r['violates_uncontested_unique_decision']]
        bottom=0
        for value,color,name in zip(vals,colors,names):
            ax.bar(i,value,bottom=bottom,color=color,width=.62,label=name if i==0 else None)
            if value:ax.text(i,bottom+value/2,str(value),ha='center',va='center',color='white' if color in (colors[0],colors[2]) else '#172b36',fontsize=11)
            bottom+=value
    ax.set_xticks(range(3),[r[0] for r in bars]);ax.set_ylim(0,12.6);ax.set_yticks([0,3,6,9,12]);ax.set_ylabel('World decisions (12 total)')
    fig.legend(*ax.get_legend_handles_labels(),loc='lower center',ncol=2,frameon=False,fontsize=9)
    fig.tight_layout(rect=(0,.2,1,1));save(fig,'root-delivery-diagnostic.pdf')

    fig,axes=plt.subplots(2,1,figsize=(6.35,3.7),sharex=True,sharey=True)
    for ax,model in zip(axes,MODELS):
        r=effect(detail,model,'exact');values=[100*r['base_effects'][p] for p in sorted(r['base_effects'])]
        ax.bar(range(1,len(values)+1),values,color=['#216b9b' if v>=0 else '#bd6b22' for v in values],width=.85)
        ax.axhline(0,color='#666',lw=.8);ax.set_title(LABELS[model]);ax.set_ylabel('Change (pp)');ax.grid(axis='y',alpha=.2)
    axes[-1].set_xticks([1,24,48,72,96]);axes[-1].set_xlabel('Independent base problem, fixed identifier order')
    fig.tight_layout();save(fig,'heldout-case-effects.pdf')


def build():
    TRACE.clear()
    main=read('results/main-reproducible-v2/analysis.json')
    detail=read('results/manuscript-main-v7/analysis.json')
    transitions=read('results/main-transitions-v1/analysis.json')
    audit=read('records/audits/main-v7.json')
    numeric=read('results/numerical-pipeline-v1/analysis.json')
    support=read('results/numerical-pipeline-v1/visible-support-v3.json')
    root=read('results/root-diagnostic-v1/analysis.json')
    root_support=read('results/root-diagnostic-v1/visible-support-v3.json')
    mechanism=read('results/mechanism-heldout-v1/analysis.json')
    pilot=read('results/pilot-interpretation-v2/analysis.json')
    validation=read('results/validation-repetition-v1/analysis.json')
    assert main['complete'] and main['analyzed_trajectories']==27648
    assert all(m['run_complete'] for m in audit['models'].values())
    assert sum(m['accepted_calls'] for m in audit['models'].values())==55296
    example=checked_example();figures(main,detail,transitions,numeric,root_support)
    blocks={}
    q=primary(main,'qwen3','H1_exact');p=primary(main,'phi4','H1_exact')
    blocks['abstract']=(
        'Repeated reports can help information survive communication, but can also change how a decision maker weighs it. '
        'We study these effects in a controlled benchmark for selecting the best feasible candidate schedule and a separate rule-based workflow task. '
        'Frozen worker reports distinguish repeated presentation from fresh computation and new evidence. '
        'Paired worlds test correct responses to consequential changes and correct stability under harmless edits. '
        'A held-out evaluation of Qwen3-14B and Phi-4 uses 192 independent base pairs shared across models, '
        '27,648 decision trajectories, and 55,296 model calls. '
        f'On scheduling, exact repetition changes accuracy by {signed(q["estimate"])} percentage points for Qwen3 and {signed(p["estimate"])} for Phi-4, '
        f'with 95\\% base-cluster intervals of [{signed(q["lower"])}, {signed(q["upper"])}] and [{signed(p["lower"])}, {signed(p["upper"])}]. '
        'Corrections and regressions largely offset, and the direct hierarchy interaction is uncertain. '
        'An audit of 6,336 development and validation summaries locates numerical objectives becoming Boolean values in raw manager output. '
        'A six-pair diagnostic separates missing information from failures to apply a uniquely supported decision. '
        'A separate 48-pair mechanism study further tests repetition targets and access to original reports. '
        'The results support separate measurement of representation fidelity, decision sufficiency, and final accuracy, while limiting conclusions to the tested tasks, models, and structured interface.')
    rows=[['Pilot','Qwen3','24','12','1,152','2,304'],['Validation','Both','36','18','5,184','10,368'],
          ['Main held-out','Both','192','96','27,648','55,296'],['Mechanism held-out','Qwen3','48','24','576','1,152'],
          ['Root diagnostic','Qwen3','6 reused','6','192','192']]
    blocks['stage-table']=table('Reported stages. Bases are shared across models; calls count accepted executions.',
        'tab:stages',['Stage','Models','Bases','Sched.','Trajectories','Calls'],rows,'llrrrr')
    rows=[]
    for model in MODELS:
        baseline=absolute(detail,model,'single')
        for condition in ('exact','paraphrase'):
            r=absolute(detail,model,condition);e=effect(detail,model,condition)
            rows.append([LABELS[model],condition,pct(baseline['accuracy']['estimate']),pct(r['accuracy']['estimate']),ci(e)])
    blocks['main-headline']=table('Primary scheduling accuracy and paired changes. Each arm has 96 bases and 2,304 trajectories.',
        'tab:headline',['Model','Repetition','Single \\%','Repeated \\%','Change, pp [95\\% CI]'],rows,'llrrr')
    blocks['organization-findings']='\n\n'.join(
        f"For {LABELS[m]}, unrepeated accuracy is {pct(absolute(detail,m,'single','flat')['accuracy']['estimate'])}\\% in the flat organization and "
        f"{pct(absolute(detail,m,'single','hierarchical')['accuracy']['estimate'])}\\% in the hierarchy. "
        f"The hierarchical exact-copy effect is {ci(effect(detail,m,'exact','hierarchical'))} percentage points. "
        f"The prespecified hierarchy interaction, averaging exact copies and paraphrases, is {ci(primary(main,m,'H3'))} points on the accuracy scale."
        for m in MODELS)
    blocks['policy-findings']='\n\n'.join(
        f"For {LABELS[m]}, scope-aware consolidation minus the checklist changes accuracy on repeated consequential scheduling cases by "
        f"{ci(primary(main,m,'H4_error'))} points. Its change in retention of altered claims across all hierarchical consequential cases is "
        f"{ci(primary(main,m,'H4_retention'))} points. Each comparison uses 48 independent bases."
        for m in MODELS)
    rows=[]
    for m in MODELS:
        for change in (False,True):
            e=one(detail['paired_success'],kind='schedule',model=m,condition='exact',decision_changed=change)
            para=one(detail['paired_success'],kind='schedule',model=m,condition='paraphrase',decision_changed=change)
            rows.append([LABELS[m],'consequential' if change else 'harmless',pct(e['single']),pct(e['repeated']),pct(para['repeated']),ci(e)])
    blocks['paired-results']=table('Both worlds correct (\\%), scheduling. Each row has 48 bases and 576 paired cells per arm.',
        'tab:paired',['Model','Edit','Single','Exact','Para.','Exact change, pp [95\\% CI]'],rows,'llrrrr')
    blocks['paired-results']+='\n\n'+' '.join(
        f"For {LABELS[m]}, the direct consequential-minus-harmless difference in the repetition effect on paired success is "
        f"{ci(primary(main,m,'H2'))} points, averaging exact and paraphrased repetition."
        for m in MODELS)
    rows=[];text=[]
    for m in MODELS:
        g=one(transitions['groups'],kind='schedule',model=m,organization='both')
        for key,label in [('single_seed1_minus_seed0','Single, 0 to 1'),('exact_seed1_minus_seed0','Exact, 0 to 1'),('exact_minus_single','Single to exact')]:
            r=g['comparisons'][key];t=r['totals']
            rows.append([LABELS[m],label,str(r['paired_comparisons']),str(t['correction']),str(t['regression']),str(t['wrong_to_wrong_answer_change']),f"{t['answer_change']}/{t['answer_comparable']}"])
        cross=g['comparisons']['exact_minus_single'];same=g['comparisons']['single_seed1_minus_seed0'];rep=g['comparisons']['exact_seed1_minus_seed0']
        e=g['within_condition_disagreement_effects']['exact']['answer_change']
        text.append(f"{LABELS[m]} has {cross['totals']['correction']} corrections and {cross['totals']['regression']} regressions under exact repetition. "
            f"Its within-condition answer-change rate is {pct(same['rates_all_pairs']['answer_change'])}\\% without repetition and "
            f"{pct(rep['rates_all_pairs']['answer_change'])}\\% with exact repetition. The latter minus the former is {ci(e)} percentage points.")
    blocks['transition-results']=table('Scheduling transitions. Answer changes require two valid trajectories; counts are paired comparisons.',
        'tab:transitions',['Model','Comparison','N','Corrected','Spoiled','Wrong/wrong','Answer changes'],rows,'llrrrrr')+'\n\n'+'\n\n'.join(text)
    matched=effect(detail,'qwen3','exact','hierarchical','ordinary+checklist')
    v=one(validation['comparisons'],model='qwen3',kind='schedule',organization='hierarchical',policy='ordinary+checklist',contrast='exact - single')
    pil=one(pilot['comparisons'],dimension='overall',kind='schedule',organization='hierarchical',condition='exact')
    blocks['stage-comparison']=(
        f"Under the shared synthesis/checklist policies, the hierarchical Qwen3 exact-copy effect is {ci(pil)} points in the 12-base pilot, "
        f"{ci(v)} in the 18-base validation subset, and {ci(matched)} in the 96-base main subset. "
        'These averages retain both worlds and both stochastic generations. The main two-policy estimate therefore differs from the three-policy headline. '
        'One pilot base contributes seven of 14 corrections. It remains included in every primary estimate. '
        'The pilot pattern is less pronounced in the later evaluations, which also change graph patterns, parameter combinations, and language templates. '
        'This establishes a limit on generalization of the development finding, without identifying which changed feature explains it.')
    rows=[]
    for m in MODELS:
        a=absolute(detail,m,'single',kind='workflow')
        for c in ('exact','paraphrase'):
            b=absolute(detail,m,c,kind='workflow');e=effect(detail,m,c,kind='workflow')
            rows.append([LABELS[m],c,pct(a['accuracy']['estimate']),pct(b['accuracy']['estimate']),ci(e)])
    blocks['workflow-results']=table('Secondary workflow accuracy. Each arm has 96 bases and 2,304 trajectories.',
        'tab:workflow',['Model','Repetition','Single \\%','Repeated \\%','Change, pp [95\\% CI]'],rows,'llrrr')
    nr=aggregate_numeric(numeric);rows=[]
    for suite,m,label in [('pilot-v7','qwen3','Pilot Qwen3'),('validation-v7','qwen3','Validation Qwen3'),('validation-v7','phi4','Validation Phi-4')]:
        a=one(nr,suite=suite,model=m,condition='single');b=one(nr,suite=suite,model=m,condition='exact')
        rows.append([label,str(a['objective_fields']),f"{a['objective_preserved']} / {b['objective_preserved']}",f"{a['objective_boolean_replacement']} / {b['objective_boolean_replacement']}",f"{a['objective_omitted']} / {b['objective_omitted']}"])
    blocks['numeric-results']=table('Objective-field audit. Entries give single / exact counts; field denominators are per arm.',
        'tab:numeric',['Scheduling subset','Fields','Preserved','Boolean','Omitted'],rows,'lrrrr')
    rows=[]
    for suite,m,label in [('pilot-v7','qwen3','Pilot Qwen3'),('validation-v7','qwen3','Validation Qwen3'),('validation-v7','phi4','Validation Phi-4')]:
        rs=[r for r in support['groups'] if r['suite']==suite and r['model']==m]
        totals={k:sum(r[k] for r in rs) for k in ('trajectories','decision_determined_from_uncontested_facts','determinate_despite_representation_errors','violates_uncontested_unique_decision')}
        rows.append([label,*[str(totals[k]) for k in ('trajectories','decision_determined_from_uncontested_facts','determinate_despite_representation_errors','violates_uncontested_unique_decision')]])
    blocks['sufficiency-results']=table('Decision support from uncontested summary fields. Representation-error cases remain flagged.',
        'tab:sufficiency',['Scheduling subset','Trajectories','Unique choice','With invalid fields','Violations'],rows,'lrrrr')
    a=one(root['aggregate'],transport='frozen_summaries',arm='F');b=one(root['aggregate'],transport='lossless',arm='F')
    ai=a['input_tokens']/a['trajectories'];bi=b['input_tokens']/b['trajectories']
    fs=one(root_support['groups'],organization='frozen_summaries',arm='F')
    fu=one(root_support['groups'],organization='frozen_summaries',arm='uniform_objectives')
    lu=one(root_support['groups'],organization='lossless',arm='uniform_objectives')
    determined=fs['decision_determined_from_uncontested_facts']
    blocks['root-results']=(
        f"Without root-level repetition, frozen model summaries yield {a['correct']} correct decisions out of {a['trajectories']} and lossless delivery yields {b['correct']} out of {b['trajectories']}. "
        f"Of the frozen contexts, {determined} determine a unique choice from uncontested values, including {fs['determinate_despite_representation_errors']} with irrelevant invalid objective fields. "
        f"The root violates that unique choice in {fs['violates_uncontested_unique_decision']} cases. The other {fs['trajectories']-determined} contexts remain underdetermined. "
        f"Mean root input length is {ai:,.0f} tokens for frozen summaries and {bi:,.0f} for lossless delivery. "
        'The latter changes the represented information and its presentation, so the comparison is an idealized preservation intervention. '
        'It does not isolate the effect of repairing only numerical objectives.\n\n'
        f"Repeating all objective assertions already present in the frozen summaries yields {fu['correct']} correct world decisions out of {fu['trajectories']}. "
        f"However, only {fu['agreement_count']} are uniquely supported by that input. The other {fu['correct']-fu['agreement_count']} correct choices remain unsupported by a unique visible answer. "
        'Uniform repetition also repeats any existing Boolean objective values rather than replacing them with hidden numbers. '
        f"With lossless delivery, the unrepeated baseline and uniform repetition both yield {lu['correct']} out of {lu['trajectories']}. "
        'Individual-objective and neutral-material arms include regressions, as reported in Appendix \\ref{app:root}. '
        'These six reused development bases support a diagnosis of observable failure locations, not a precise population effect or a complete mediation analysis.')
    rows=[]
    arm_labels=[('hier_F','No repetition'),('hier_COMMON4','Common finding, four'),('hier_A4','Decisive finding, four'),('hier_E4','All reports, four each'),('bypass_F','Raw access, no repetition'),('bypass_common4','Raw access, common four')]
    for arm,label in arm_labels:
        sr=one(mechanism['summary'],kind='schedule',arm=arm);wr=one(mechanism['summary'],kind='workflow',arm=arm)
        rows.append([label,pct(sr['accuracy']),pct(wr['accuracy']),pct(sr['unrepeated_necessary_retention_mean'])])
    blocks['mechanism-results']=table('Separate Qwen3 mechanism test. Each task has 24 fresh bases and 48 decisions per arm.',
        'tab:mechanism',['Arm','Schedule \\%','Workflow \\%','Sched. retention \\%'],rows,'lrrr')
    ps=[one(mechanism['contrasts'],kind='schedule',contrast=c,primary=True) for c in ('P1','P2','P3')]
    blocks['mechanism-results']+='\n\n'+(
        f"The primary decisive-minus-common accuracy contrast is {ci(ps[0])} points. "
        f"Repeating a common finding changes retention of unrepeated necessary claims by {ci(ps[1])} points. "
        f"The repetition-by-raw-access interaction is {ci(ps[2])} points. "
        'Neither accuracy contrast establishes a general benefit from emphasizing decisive findings or from bypassing summaries. '
        'The retention estimate is small and does not demonstrate equivalence.\n\n')
    uni=one(mechanism['contrasts'],kind='workflow',contrast='uniform_repetition',metric='correct')
    wf=one(mechanism['summary'],kind='workflow',arm='hier_F');we=one(mechanism['summary'],kind='workflow',arm='hier_E4')
    blocks['mechanism-results']+=(f"On the secondary workflow population, uniform repetition lowers accuracy from {pct(wf['accuracy'])}\\% to {pct(we['accuracy'])}\\%, a change of {ci(uni)} points. "
        'This is a secondary comparison in a single-model extension. Repeating every report also substantially lengthens the input, '
        'and these arms do not isolate exceptions or context length. The result therefore cannot establish general harm to exception handling.')
    rows=[]
    for m in MODELS:
        for org in ('flat','hierarchical'):
            for policy in ('ordinary','checklist','scope'):
                cs=[one(main['summary'],kind='schedule',model=m,organization=org,policy=policy,condition=c) for c in CONDS]
                rows.append([LABELS[m], 'hierarchy' if org=='hierarchical' else org, 'synthesis' if policy=='ordinary' else policy,*[pct(r['accuracy']) for r in cs]])
    blocks['policy-table']=table('Main scheduling accuracy (\\%) by policy. Each cell has 96 bases and 384 trajectories.',
        'tab:policies',['Model','Organization','Policy','Single','Exact','Para.'],rows,'lllrrr')
    rows=[]
    for arm,label in [('F','No repetition'),('objective0','Objective 1'),('objective1','Objective 2'),('objective2','Objective 3'),('constraint','Constraint'),('uniform_objectives','All objectives'),('neutral','Neutral material'),('end','Objective at end')]:
        fs=one(root_support['groups'],organization='frozen_summaries',arm=arm);ls=one(root_support['groups'],organization='lossless',arm=arm)
        rows.append([label,f"{fs['correct']}/12",f"{fs['agreement_count']}/10",f"{ls['correct']}/12",f"{ls['agreement_count']}/12"])
    blocks['root-table']=table('All root-diagnostic arms. Agreement uses only uniquely determined contexts.',
        'tab:root-all',['Arm','Frozen correct','Agreement','Lossless correct','Agreement'],rows,'lrrrr')
    rows=[]
    for m in MODELS:
        for org in ('flat','hierarchical'):
            a=absolute(detail,m,'single',org);b=absolute(detail,m,'exact',org)
            rows.append([LABELS[m],'hierarchy' if org=='hierarchical' else org,
                f"{(a['input_tokens']+a['output_tokens'])/a['trajectories']:,.0f}",f"{(b['input_tokens']+b['output_tokens'])/b['trajectories']:,.0f}",
                f"{a['inference_seconds']/a['correct']:.2f}",f"{b['inference_seconds']/b['correct']:.2f}"])
    blocks['cost-table']=table('Scheduling resources, single / exact. Time is allocated batch seconds per correct decision.',
        'tab:cost',['Model','Organization','Single tokens','Exact tokens','Single time','Exact time'],rows,'llrrrr')
    blocks['conclusion']=(
        'Across two models and 192 independent held-out base pairs, selective repetition has small, uncertain average scheduling effects '
        'and does not reproduce the large hierarchical pilot gain. Corrections and regressions can offset, so average accuracy alone '
        'does not describe how decisions change. The secondary workflow results and targeted repetition study further limit any claim of a universal benefit. '
        'Trace audits identify numerical-to-Boolean transformations in raw summaries, while the root diagnostic separates lost information '
        'from errors made despite a uniquely supported choice. These findings support evaluating the complete communication path through '
        'three distinct outcomes: faithful propositions, sufficient information, and correct decisions. '
        'They motivate interfaces that preserve required values and scopes, with their decision benefit assessed separately.')
    changed=update_blocks(blocks)
    record={'version':7,'evidence_scope':'Completed main replay, original pilot/validation audits, frozen root diagnostic, separate mechanism heldout; unfinished optional stages excluded.',
        'sources':TRACE,'example':example,'blocks':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in blocks.items()},
        'figure_files':['aggregation-architecture.pdf','heldout-repetition-effects.pdf','correctness-transitions.pdf','numerical-fidelity.pdf','root-delivery-diagnostic.pdf','heldout-case-effects.pdf'],
        'updated_source':changed,'human_scientific_review':'pending'}
    (ROOT/'records/manuscript-content-v7.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'manuscript_version':7,'updated':changed,'figures':len(record['figure_files'])}))
    return record


if __name__=='__main__':build()
