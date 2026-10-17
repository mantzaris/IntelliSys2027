"""Compact tables and figures from the versioned interpretation output only."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root = Path('results/pilot-interpretation-v2')
r = json.loads((root / 'analysis.json').read_text())
figdir = root / 'figures'; figdir.mkdir(exist_ok=True)
overall = [x for x in r['comparisons'] if x['dimension'] == 'overall']
focus = next(x for x in overall if (x['kind'], x['organization'], x['condition']) == ('schedule', 'hierarchical', 'exact'))
fmt = lambda x: f'{100*x:.2f}'
ci = lambda x: f"[{fmt(x['lower'])}, {fmt(x['upper'])}]" if x['lower'] is not None else 'unavailable (small strata)'
lines = ['# Pilot interpretation: absolute outcomes and observable failure locations', '',
    'Exploratory reanalysis of immutable `pilot-v7` outputs; no new model calls. The original protocol and audit remain intact.', '',
    f"The complete pilot contains {r['base_pairs']} independent base pairs (12 scheduling and 12 secondary workflow), {r['trajectories']} trajectories and {r['accepted_calls']} calls. All results below are Qwen3-14B BF16, non-thinking, with the original fixed settings.", '',
    'Each scheduling hierarchical condition has 96 trajectories: 12 bases × two worlds × two policies × two stochastic repetitions. The 13.54-point result compares exact copies with single presentation, averaging matched cells within a base, then giving each base equal weight. It pools ordinary synthesis and checklist, both worlds, and both repetitions. The selected report was frozen before evaluation, correct in both worlds, and unchanged across the pair. It was not chosen to favor the correct answer.', '',
    '| Population / organization / condition | Single accuracy % | Repeated accuracy % | Difference pp [95% cluster interval] | Bases | Trajectories, both arms | Improve / regress / unchanged |',
    '|---|---:|---:|---|---:|---:|---|']
for x in overall:
    lines.append(f"| {x['kind']} / {x['organization']} / {x['condition']} | {fmt(x['baseline'])} | {fmt(x['repeated'])} | {fmt(x['estimate'])} {ci(x)} | {x['clusters']} | {x['trajectories']} | {x['improvements']} / {x['regressions']} / {x['unchanged']} |")
lines += ['', 'Policy and task strata (hierarchical scheduling):', '',
    '| Stratum | Repeat | Single % | Repeated % | Difference pp [95% interval] | Bases | Improved / regressed / unchanged |',
    '|---|---|---:|---:|---|---:|---|']
for x in r['comparisons']:
    if x['kind'] == 'schedule' and x['organization'] == 'hierarchical' and x['dimension'] in ('policy', 'target', 'family'):
        label = x.get('policy', x.get('selected_task', x.get('family')))
        lines.append(f"| {label} | {x['condition']} | {fmt(x['baseline'])} | {fmt(x['repeated'])} | {fmt(x['estimate'])} {ci(x)} | {x['clusters']} | {x['improvements']} / {x['regressions']} / {x['unchanged']} |")
largest = max(focus['base_effects'], key=focus['base_effects'].get)
lines += ['', f"Exact-copy base means are positive for {focus['base_positive']} bases, negative for {focus['base_negative']}, and zero for {focus['base_zero']}. The largest contributor is `{largest}`: seven of the 14 improved cells. Leaving that base out gives {fmt(focus['leave_one_base_out'][largest])} pp. Across all single-base omissions the estimate ranges from {fmt(focus['leave_one_base_out_min'])} to {fmt(focus['leave_one_base_out_max'])} pp. This is descriptive sensitivity, not another significance search. Per-base values and every omission are in `analysis.json`.", '',
    'The bootstrap resamples whole bases within mutation-family × decision-change strata; it retains dependent worlds, policies and stochastic repetitions. The fixed stratum composition is part of the estimand. Singleton-stratum intervals are withheld. Flat scheduling is at a ceiling in this pilot; a zero-width empirical interval does not establish robustness.', '',
    'Paired-world success requires both answers to be correct. Changing an answer or keeping it stable alone is insufficient.', '',
    '| Scheduling hierarchy | Repeat | Both correct, single % | Both correct, repeated % | Difference pp [95% interval] | Bases | Matched world-pairs |',
    '|---|---|---:|---:|---|---:|---:|']
for x in r['paired_world']:
    if x['kind'] == 'schedule' and x['organization'] == 'hierarchical':
        lines.append(f"| {'Consequential' if x['decision_changed'] else 'Harmless'} | {x['condition']} | {fmt(x['baseline'])} | {fmt(x['repeated'])} | {fmt(x['estimate'])} {ci(x)} | {x['clusters']} | {x['matched_cells']} |")
failures = []
for condition in ('single', 'exact', 'paraphrase'):
    rows = [x for x in r['failure_locations'] if (x['kind'], x['organization'], x['condition']) == ('schedule', 'hierarchical', condition)]
    failures.append({'condition': condition, **{k: sum(x[k] for x in rows) for k, v in rows[0].items() if type(v) is int and k != 'base_pairs'}})
labels = [('necessary_fact_omitted', 'Necessary proposition absent'), ('necessary_value_wrong_or_conflicted', 'Necessary value wrong or conflicted'),
          ('visible_false_constraint_ignored', 'Invalid choice despite delivered failed constraint'), ('feasible_but_not_preferred', 'Feasible but not preferred'),
          ('correct_choice_erroneous_support', 'Correct choice with erroneous support'), ('response_contract_failure', 'Response-contract failure')]
lines += ['', 'Observable labels below have 96 trajectories per column. Labels overlap and are not causal categories. A correct choice may coexist with an omitted fact or an erroneous supporting assertion.', '',
          '| Observation | Single | Exact | Paraphrase |', '|---|---:|---:|---:|']
for key, label in labels:
    lines.append('| ' + label + ' | ' + ' | '.join(str(x[key]) for x in failures) + ' |')
lines += ['', r['scope_contract'], '', r['annotation_limits'], '',
    'No pilot output was truncated or contract-invalid. Numerical objective errors and omissions are visible, but this pilot alone cannot assign the aggregate accuracy gain to transmission versus root application. A baseline root also makes a wrong decision after receiving enough correct information. Lossless and bypass interventions test this distinction directly; their completion status and results are reported separately in `records/mechanism-report-status.json` and the manuscript extension section.', '',
    'The frozen development extension already covers exact/paraphrase copying, selective/uniform emphasis, false visible assertions, same-input scope differences, branch/padding/position controls, summary bypass, deterministic transport and call-matched global reviewers. A separately versioned root-only diagnostic fills the gap for numerical objectives, covering every candidate rather than selecting only favorable or correct-choice objectives. It will run after the protected original evaluations. Additional boundary investigations are not selected before the core extension finishes.', '',
    'Machine-readable evidence: `results/pilot-interpretation-v2/analysis.json`, `accuracy.csv`, `paired-world.csv`, `failure-locations.csv`. Detailed trajectory annotations are locally mirrored/derived in ignored `artifacts/analyses/pilot-interpretation-v2/`. Reproduce with `scripts/interpret_pilot.py` and `scripts/build_pilot_interpretation.py`.']
Path('PILOT_INTERPRETATION.md').write_text('\n'.join(lines) + '\n')

fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), layout='constrained')
groups = [x for x in overall if x['kind'] == 'schedule']
for i, x in enumerate(groups):
    axes[0].plot([100*x['baseline'], 100*x['repeated']], [i, i], '-o', color='#176c80')
    axes[1].errorbar(100*x['estimate'], i, xerr=[[100*(x['estimate']-x['lower'])], [100*(x['upper']-x['estimate'])]], fmt='o', color='#176c80', capsize=3)
names = [x['organization'] + ' / ' + x['condition'] for x in groups]
for ax in axes:
    ax.set_yticks(range(len(groups)), names); ax.invert_yaxis(); ax.grid(axis='x', alpha=.2)
axes[0].set_xlabel('Accuracy (%)'); axes[0].set_title('Single → repeated'); axes[0].set_xlim(75, 102)
axes[1].set_xlabel('Accuracy change (percentage points)'); axes[1].set_title('Whole-base cluster intervals'); axes[1].axvline(0, color='gray', lw=1)
fig.savefig(figdir / 'absolute-and-paired-effects.pdf'); fig.savefig(figdir / 'absolute-and-paired-effects.png', dpi=150); plt.close(fig)
fig, ax = plt.subplots(figsize=(8, 3.7), layout='constrained')
for i, row in enumerate(failures):
    ax.barh([j+(i-1)*.24 for j in range(len(labels))], [100*row[k]/row['trajectories'] for k, _ in labels], height=.23, label=row['condition'])
ax.set_yticks(range(len(labels)), [label for _, label in labels], fontsize=9); ax.invert_yaxis()
ax.set_xlabel('Trajectories with observation (%)'); ax.legend(ncol=3, loc='lower right'); ax.grid(axis='x', alpha=.2)
fig.savefig(figdir / 'observable-failure-locations.pdf'); fig.savefig(figdir / 'observable-failure-locations.png', dpi=150); plt.close(fig)

tex = [r'\subsection{Absolute Pilot Outcomes and Concentration}',
    r'This additional interpretation is exploratory. In hierarchical scheduling, the single condition has accuracy '+fmt(focus['baseline'])+r'\%, versus '+fmt(focus['repeated'])+r'\% with exact repetition. Each arm has '+str(focus['matched_cells'])+r' trajectories from '+str(focus['clusters'])+r' independent bases, pooling both worlds, two policies and two stochastic repetitions. Matched outcomes comprise '+str(focus['improvements'])+' improvements, '+str(focus['regressions'])+' regression and '+str(focus['unchanged'])+' unchanged outcomes. No contract failures or truncations explain this difference.',
    'Six bases improve on average, one regresses and five have zero net change. One base accounts for seven improved cells. Excluding it reduces the gain to '+fmt(focus['leave_one_base_out'][largest])+' percentage points; the full leave-one-base-out range is '+fmt(focus['leave_one_base_out_min'])+'--'+fmt(focus['leave_one_base_out_max'])+' points. These omissions are descriptive, not additional significance tests.',
    r'Figure~\ref{fig:absolute-pilot} shows absolute accuracy and paired effects. Table~\ref{tab:paired-world-detail} requires correct decisions in both worlds. Figure~\ref{fig:failure-locations} distinguishes observable failure locations.',
    r'\begin{figure}[tb]\centering\includegraphics[width=\textwidth]{../results/pilot-interpretation-v2/figures/absolute-and-paired-effects.pdf}\caption{Pilot scheduling accuracy and paired repetition effects.}\label{fig:absolute-pilot}\end{figure}',
    r'\begin{table}[tb]\centering\small\caption{Both paired-world answers correct; scheduling hierarchy.}\label{tab:paired-world-detail}',
    r'\begin{tabular}{llrrr}\toprule Edit & Repeat & Single (\%) & Repeated (\%) & Difference [95\% CI]\\\midrule']
for x in r['paired_world']:
    if x['kind'] == 'schedule' and x['organization'] == 'hierarchical':
        tex.append(f"{'Consequential' if x['decision_changed'] else 'Harmless'} & {x['condition'].capitalize()} & {fmt(x['baseline'])} & {fmt(x['repeated'])} & {fmt(x['estimate'])} {ci(x)}"+r'\\')
tex += [r'\bottomrule\end{tabular}\end{table}',
    r'Each paired-world row uses six bases and 24 matched world-pair cells per arm. Success requires both correct answers. Merely changing or retaining a choice does not count. Intervals resample bases within family and edit-status strata.',
    r'\begin{figure}[tb]\centering\includegraphics[width=\textwidth]{../results/pilot-interpretation-v2/figures/observable-failure-locations.pdf}\caption{Observable pilot failures; labels overlap.}\label{fig:failure-locations}\end{figure}',
    r'Keyed assertions bind the full public scope, including entity, units, condition, criterion and version. Numerical preservation at another key does not count. These deterministic labels describe messages and choices; they do not identify internal reasoning or causal mediation. Correct final choices can coexist with incorrect supporting assertions. The extension section reports completion status for the transport and root-only interventions.']
pass  # The one-file paper is refreshed below.
Path('records/manuscript-sources/pilot-interpretation-traceability.json').write_text(json.dumps({
    'source': str(root / 'analysis.json'), 'fields': ['comparisons', 'paired_world', 'failure_locations'],
    'generated': ['pilot-interpretation.tex', 'PILOT_INTERPRETATION.md'], 'human_review': 'pending'}, indent=2) + '\n')

# Preserve the single-source manuscript under manual and automatic refreshes.
from manuscript_content import refresh
refresh()
