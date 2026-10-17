"""Populate review tables only from complete immutable-run analyses.

This does not perform scientific review, choose favorable subsets, or submit a paper.
Missing suites produce explicit pending-status text instead of empty numeric tables.
"""
import json
from pathlib import Path

OUT=Path('records/manuscript-sources')
OUT.mkdir(parents=True,exist_ok=True)
TRACE=[]
LABELS={'qwen3':'Qwen3-14B','phi4':'Phi-4','equal_model_average':'Equal-model mean'}


def tex(value):
    return str(value).replace('&',r'\&').replace('_',r'\_').replace('%',r'\%').replace('#',r'\#')


def number(value,scale=1,digits=1):
    if value is None:return '--'
    scaled=scale*value
    if abs(scaled)<.5*10**(-digits):scaled=0.
    return f'{scaled:.{digits}f}'


def interval(row):
    if row is None or row.get('estimate') is None:return '--'
    dagger=r'$^\dagger$' if row.get('degenerate_bootstrap') else ''
    return number(row['estimate'],100)+' ['+number(row['lower'],100)+', '+number(row['upper'],100)+']'+dagger


def remember(suite,field,row):
    TRACE.append({'source':f'results/{suite}/analysis.json','field':field,'record':row})
    return row


def load(suite):
    path=Path('results')/suite/'analysis.json'
    if not path.exists():return None
    result=json.loads(path.read_text())
    return result if result.get('complete') else None


def table(caption,columns,rows,layout,label,long=False):
    environment='longtable' if long else 'tabular'
    start='\\begin{small}\n' if long else '\\begin{table}[ht]\n\\centering\n\\small\n'
    start+='\\setlength{\\tabcolsep}{3pt}\n'
    caption_text='\\caption{'+caption+'}\\label{'+label+'}'
    if not long:start+=caption_text+'\n'
    start+='\\begin{'+environment+'}{'+layout+'}\n'
    if long:start+=caption_text+r'\\'+'\n'
    start+='\\hline\n'+' & '.join(columns)+r'\\'+'\n\\hline\n'
    if long:start+='\\endfirsthead\n'+' & '.join(columns)+r'\\'+'\n\\hline\n\\endhead\n'
    start+='\n'.join(' & '.join(row)+r'\\' for row in rows)
    return start+'\n\\hline\n\\end{'+environment+'}\n'+('\\end{small}\n' if long else '\\end{table}\n')


def replay_tables(result,kind):
    suite=result['suite'];models=sorted({r['model'] for r in result['summary']})
    rows=[]
    for model in models:
        for organization in ('flat','hierarchical'):
            for policy in ('ordinary','checklist','scope'):
                cells=[next(r for r in result['summary'] if
                    (r['model'],r['kind'],r['organization'],r['policy'],r['condition'])==
                    (model,kind,organization,policy,condition)) for condition in ('single','exact','paraphrase')]
                for r in cells:remember(suite,'summary',r)
                rows.append([LABELS.get(model,tex(model)),organization,policy,*[number(r['accuracy'],100) for r in cells]])
    title='Primary scheduling' if kind=='schedule' else 'Secondary workflow'
    text=table(title+' held-out decision accuracy (percent). Operational failures count as errors.',
        ['Model','Organization','Policy','Single','Exact','Paraphrase'],rows,'lllrrr','tab:main-'+kind)
    rows=[]
    for contrast in ('H1_exact','H1_paraphrase','H2','H3','H4_error','H4_retention'):
        for model in models+['equal_model_average']:
            r=next(r for r in result['contrasts'] if (r['kind'],r['model'],r['contrast'])==(kind,model,contrast))
            remember(suite,'contrasts',r)
            rows.append([tex(contrast),LABELS.get(model,tex(model)),interval(r),str(r['clusters'])])
    text+=table(title+' paired contrasts in percentage points with 95\% cluster intervals. '
        'H1--H3 and H4 error concern error increases; H4 retention concerns retention increases. '
        '$\dagger$ denotes a degenerate empirical interval, not proof of a zero population effect.',
        ['Contrast','Model','Estimate [interval]','Clusters'],rows,'llrr','tab:contrasts-'+kind)
    return text


SHORT_CONTROLS={
 ('packaging','high_overlap - low_overlap'):'High minus low overlap',
 ('deduplication','similarity_removal - exact_removal'):'Similarity minus exact removal',
 ('deduplication','scope_consolidation - similarity_removal'):'Scope policy minus similarity removal',
 ('branch_placement','different_branch - same_branch'):'Distinct scopes: across minus within branch',
 ('copy_branch_placement','different_branch - same_branch'):'Copies: across minus within branch',
 ('access','summaries_and_reports - summaries_only'):'Raw-report bypass minus summaries',
 ('call_count','global_reviewers - partition_managers'):'Global reviewers minus partition managers',
 ('length','evidential_repetition - neutral_padding'):'Evidential repetition minus neutral material',
 ('ancestry','withheld - authentic'):'Withheld minus authentic ancestry',
 ('ancestry','corrupted_relationships - authentic'):'Corrupted minus authentic ancestry',
 ('instruction','scope_without_ancestry - ordinary_without_ancestry'):'Scope instructions minus ordinary; ancestry hidden',
 ('unique_clause','decisive_high - decisive_low'):'Decisive clause: high minus low overlap',
 ('unique_clause','harmless_high - harmless_low'):'Harmless clause: high minus low overlap',
 ('version_admission','current_and_superseded - current_only'):'Historical plus current minus current only',
}


def control_tables(result,kind):
    suite=result['suite'];models=sorted({r['model'] for r in result['summary']})
    rows=[]
    keys=sorted({(r['contrast'],r['difference']) for r in result['contrasts'] if r['kind']==kind})
    for contrast,difference in keys:
        label=SHORT_CONTROLS.get((contrast,difference))
        if label is None:
            label=difference.replace('_all_correct_with_world',' correct').replace('_false_favorable_with_world',' false favorable').replace('_false_objection_with_world',' false objection')
        cells=[]
        for model in models:
            r=next((r for r in result['contrasts'] if (r['kind'],r['model'],r['contrast'],r['difference'])==(kind,model,contrast,difference)),None)
            if r:remember(suite,'contrasts',r)
            cells.append(interval(r))
        counts=sorted({r['clusters'] for r in result['contrasts'] if (r['kind'],r['contrast'],r['difference'])==(kind,contrast,difference)})
        label+=' (clusters '+('/'.join(map(str,counts)))+')'
        rows.append([tex(label),*cells])
    return table(('Primary scheduling' if kind=='schedule' else 'Secondary workflow')+
        ' supporting error contrasts: percentage points and 95\% cluster intervals. '
        'These small-subset estimates are exploratory; $\dagger$ marks degenerate empirical intervals.',
        ['Contrast',*[LABELS.get(m,tex(m)) for m in models]],rows,'p{0.45\\linewidth}'+''.join('p{'+str(0.46/len(models))+'\\linewidth}' for m in models),
        'tab:controls-'+kind,long=True)


def live_tables(result):
    rows=[]
    for r in result['summary']:
        remember(result['suite'],'summary',r)
        rows.append([LABELS.get(r['model'],tex(r['model'])),tex(r['arm'].replace('_',' ')),
                     number(r['accuracy'],100),number(r['root_supported_correct_mean'],100),
                     number((r['input_tokens']+r['output_tokens'])/r['n']),number(r['tokens_per_correct'])])
    return table('Live scheduling results. Accuracy and input-supported correct decisions are percentages; '
        'token cost includes worker and root calls. A truth match unsupported by delivered claims is not integration success.',
        ['Model','Assignment / allowance','Acc.','Supported',r'\shortstack{Tokens/\\decision}',r'\shortstack{Tokens/\\correct}'],rows,
        'lp{0.25\\linewidth}rrrr','tab:live')


def control_diagnostics(result):
    rows=[]
    for r in result['summary']:
        if r['kind']!='schedule' or r['contrast']!='corruption' or 'all_correct' in r['arm']:continue
        if 'false_assertion_emitted_mean' not in r:continue
        policy=r['arm'].split('_',1)[0]
        injection='favorable' if 'favorable' in r['arm'] else 'objection'
        remember(result['suite'],'summary',r)
        rows.append([LABELS.get(r['model'],tex(r['model'])),policy,injection,
                     number(r['false_assertion_emitted_mean'],100),number(r['false_assertion_adopted_mean'],100),
                     str(r['false_assertion_adopted_denominator'])])
    text=table('Primary false-finding diagnostics (percent). Uncontested means no contrary true finding and no unresolved flag for the scope. '
               'N counts valid root outputs; malformed outputs remain primary trajectory failures. Neither column measures hidden belief.',
        ['Model','Policy','Injection','Emitted','Uncontested','N'],rows,'lllrrr','tab:false-findings') if rows else ''
    rows=[]
    for r in result['summary']:
        if r['kind']!='schedule' or r['contrast']!='unique_clause':continue
        remember(result['suite'],'summary',r)
        rows.append([LABELS.get(r['model'],tex(r['model'])),tex(r['arm'].replace('_',' ')),
                     number(r['unique_clause_retained_mean'],100),str(r['unique_clause_retained_denominator'])])
    if rows:text+=table('Primary designated-clause retention across the summary boundary (percent). '
        'Each denominator counts eligible delivered clauses, including failed summaries as losses. Decisive means a single Boolean flip changes the oracle decision.',
        ['Model','Clause / overlap','Retained','N'],rows,'llrr','tab:unique-retention')
    path=Path('results',result['suite'],'matching_audit.json')
    if path.exists():
        matching=json.loads(path.read_text())
        if matching.get('complete'):
            rows=[]
            metrics={'packaging_report_token_difference_high_minus_low':'High minus low report tokens',
                     'packaging_character_similarity_difference_high_minus_low':'High minus low similarity',
                     'neutral_minus_repeat_manager_prompt_tokens':'Neutral minus repeat input tokens',
                     'distinct_scope_branch_absolute_report_load_change':'Absolute branch load change',
                     'similarity_admission_fraction_of_required_claims_lost':'Similarity admission: fraction lost'}
            for r in matching['summary']:
                if r['kind']!='schedule' or r['metric'] not in metrics:continue
                TRACE.append({'source':str(path),'field':'summary','record':r})
                digits=3 if 'similarity' in r['metric'] or 'fraction' in r['metric'] else 1
                rows.append([LABELS.get(r['model'],tex(r['model'])),metrics[r['metric']],
                             number(r['cluster_weighted_mean'],digits=digits),number(r['minimum'],digits=digits)+' to '+number(r['maximum'],digits=digits)])
            text+=table('Measured matching residuals and deterministic admission loss. Means weight base clusters equally; ranges cover observed matched cells or branches. '
                'Residual length and branch-load differences limit attribution to overlap alone.',
                ['Model','Diagnostic','Mean','Range'],rows,'lp{0.42\\linewidth}rr','tab:matching')
    return text


main=load('main-v7');support=load('supporting-v7');live=load('live-v8')
pending=[name for name,result in [('main-v7',main),('supporting-v7',support),('live-v8',live)] if result is None]
status=('The main held-out replay is complete. ' if main else
        'The implemented benchmark and completed development experiments are distinct from the uncompleted held-out replay. No held-out result is claimed. ')
status+=('Supporting and live evaluations are complete. ' if not pending else
         'The following study stages do not yet have complete analysis outputs: '+', '.join(tex(n) for n in pending)+'. ')
status+='Human scientific review, interpretation and submission eligibility remain pending.\n'
pass  # The one-file paper is refreshed below.
supplement=''
if main:
    text='\\section{Held-Out Replay Results}\n'
    text+=replay_tables(main,'schedule')
    for figure in ('repetition','hierarchy','retention','resource'):
        text+='\\begin{figure}[ht]\n\\centering\n\\includegraphics[width=\\textwidth]{../results/main-v7/figures/'+figure+'.pdf}\n'
        text+='\\caption{Primary scheduling: '+figure+'. Estimates preserve complete base-instance clusters; an asterisk marks a degenerate empirical interval. Tokens are a measured cost proxy, not FLOPs.}\n\\end{figure}\n'
    text+='Model-specific results and the equal-weight model average are reported together. A higher overall hierarchical error rate alone is not amplification; H3 tests the repetition interaction. Harmless-pair guardrails, calibration and confidence-only changes are retained in the accompanying analysis CSVs.\n'
    pass  # The one-file paper is refreshed below.
    supplement+='\\section{Secondary Workflow Results}\n'+replay_tables(main,'workflow')
    average_rows={r['contrast']:r for r in main['contrasts'] if r['kind']=='schedule' and r['model']=='equal_model_average'}
    h1=average_rows['H1_exact'];h3=average_rows['H3']
    abstract='''Similar agent reports can restate one observation, describe fresh executions,
or contain complementary requirements whose differences determine a decision.
We develop a controlled benchmark for these distinctions in hierarchical
language-model systems. The primary task selects the minimum-makespan feasible
schedule from supplied candidates using executable truth and an independent checker.
A separate rule-workflow population tests quantifiers, conditions and explicit
revisions. Frozen reports compare single presentations, exact copies and
claim-preserving paraphrases under flat and summary-only hierarchical aggregation.
Ordinary synthesis, required-task checklists and scope-aware consolidation share
information access and a lightweight structured output contract.
'''
    abstract+=f"The completed held-out scheduling replay covers {h1['clusters']} independent base pairs and two model families. "
    abstract+=f"Equal-weight model estimates give an exact-repetition error change of {100*h1['estimate']:.1f} percentage points (95\\% cluster interval {100*h1['lower']:.1f} to {100*h1['upper']:.1f}) and a hierarchy interaction of {100*h3['estimate']:.1f} points ({100*h3['lower']:.1f} to {100*h3['upper']:.1f}). "
    abstract+='''We separately report changed-scope retention, operational failures, confidence
changes and measured resource costs. Supporting controls distinguish summary access,
ancestry and report packaging; live assignments separate replay copies from fresh
verification. Conclusions are limited to these synthetic tasks, local models and
communication interfaces. This working manuscript requires human scientific
review before submission.
'''
else:
    pass  # The one-file paper is refreshed below.
    abstract=Path('manuscript/main.tex').read_text().split(r'\begin{abstract}',1)[1].split(r'\keywords',1)[0]
pass  # The one-file paper is refreshed below.
if support:
    pass  # The one-file paper is refreshed below.
    supplement+='\\section{Secondary Supporting Controls}\n'+control_tables(support,'workflow')
else:pass  # The one-file paper is refreshed below.
if live:
    text='\\section{Live Worker Results}\n'
    development=load('live-development-v8')
    if development:
        for row in development['summary']:
            if row['arm']!='nonoverlap_added':continue
            remember(development['suite'],'summary',row)
            text+=LABELS.get(row['model'],tex(row['model']))+' corrected development baseline accuracy was '+number(row['accuracy'],100)+'\\% over '+str(row['n'])+' decisions from '+str(row['clusters'])+' base instances. '
            if row['accuracy']<.85:text+='This fails the prespecified adequacy threshold; its live comparisons describe task/interface limitations rather than an identified redundancy mechanism. '
        text+='\n'
    text+=live_tables(live)
    pass  # The one-file paper is refreshed below.
else:pass  # The one-file paper is refreshed below.
pass  # The one-file paper is refreshed below.
(OUT/'study_numerical_traceability.json').write_text(json.dumps(TRACE,indent=2)+'\n')
Path('records/study-report-status.json').write_text(json.dumps({'complete_analysis_stages':[r['suite'] for r in (main,support,live) if r],
    'pending_analysis_stages':pending,'human_scientific_review':'pending','submission_ready':False},indent=2)+'\n')
print(json.dumps({'complete_stages':3-len(pending),'pending':pending}))

# Preserve the single-source manuscript under manual and automatic refreshes.
from manuscript_content import refresh
refresh()
