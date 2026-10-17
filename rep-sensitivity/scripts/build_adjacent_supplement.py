"""Compact pending/results appendix; numerical claims come only from complete arms."""
import json
from pathlib import Path
from rep_sensitivity.schema import digest


def esc(s):return str(s).replace('_',r'\_').replace('%',r'\%')


config=json.loads(Path('configs/adjacent-explorations-v1.json').read_text())
source=Path('results/adjacent-explorations-v1/analysis.json')
data=json.loads(source.read_text()) if source.exists() else None
stop=Path('artifacts/runs/adjacent-explorations-execution/not-launched.json')
freeze=Path('records/freezes/adjacent-explorations-v1.json')
record=json.loads(freeze.read_text()) if freeze.exists() else None
states={e:data['experiments'].get(e,{}) if data else {} for e in ('feedback','consensus')}
labels={'feedback':'Feedback','fresh':'Fresh','length_control':'Length',
        'single':'Single','same_worker':'Same identity','different_relays':'Different identities','authority_labels':'Role cues'}
tex=[r'\section{Bounded exploratory coordinator studies}',
    'These studies reuse four development base pairs, shared across both experiments. They are not independent confirmation. '
    'They run after the original evaluations, frozen confirmation and numerical-preservation replay. '
    'The combined ceiling is 104 fresh calls and 15 minutes including loading, within the existing cumulative two-hour allowance. '
    'A prospectively specified budget fallback runs only the 72-call feedback experiment; otherwise neither launches. '
    'No outcome determines sample size or allocation.',
    r'\subsection{Frozen interventions}',
    'Feedback uses two numerical-capacity and two resource-identity base pairs. Each has a consequential and a matched harmless update, '
    'three rounds and three conditions (72 calls). Round 2 repeats the unchanged current evidence. Round 3 replaces it with an authoritative '
    'complete version-2 snapshot. Feedback adds the immediately preceding public choice and candidate assessments; fresh evaluation omits them; '
    'a yoked length control receives neutral padding. No independent worker observation is added. All current snapshots determine a unique answer.',
    'The relay experiment uses the same four pairs, two worlds and four conditions (32 calls): one objective report, four copies under one identity, '
    'four copies under different identities, and the same relays with authority-suggesting role labels. Common origin, source and execution identifiers '
    'remain explicit. Labels confer no actual authority. The repeated objective favors a feasible correct candidate in four contexts and an infeasible '
    'candidate in four. The three repeated arms retain identical claim content, report positions and ancestry; residual token differences are recorded.',
    'These controls do not test autonomous discovery of missing information. Harmless edits affect a different nonbinding resource or job than '
    'consequential edits. The public contract does not elicit a reliable source-count estimate. A changed decision therefore does not establish a '
    'source-counting belief, and a null effect cannot establish that explicit provenance caused protection. Prior conclusions and numerical facts '
    'are different interventions. Neither experiment identifies an effect of hierarchy.']
notes=['# Adjacent exploration status','',
       'Four reused development base pairs are shared by both experiments. No new independent confirmation is implied.']
if not any(s.get('complete') for s in states.values()):
    status='Not launched under the protected-work/budget gate.' if stop.exists() else 'GPU results pending; implementation and CPU validation do not count as empirical execution.'
    tex += [r'\subsection{Execution status}',status]
    notes += ['',status]
    if record:
        p=record['projection']['both']
        notes += ['',f"Frozen maximum: 104 calls. Measured-batch planning estimate: {p['mean_seconds_with_loading']/60:.2f}–{p['planning_p95_seconds_with_loading']/60:.2f} minutes including loading. Four-case sample fixed before responses."]
else:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    folder=Path('results/adjacent-explorations-v1/figures');folder.mkdir(parents=True,exist_ok=True)
    selected_effects=[]
    for experiment,s in states.items():
        tex.append(r'\subsection{'+('Feedback and updates' if experiment=='feedback' else 'Relay identities and role cues')+'}')
        if not s.get('complete'):
            tex.append('Not completed. '+esc(s.get('status','pending'))+'.');continue
        tex.append(f"Four reused base pairs; {s['calls']} fresh calls completed. All current evidence was sufficient and consistent by construction. "
                   'The table counts final choices; malformed completed responses remain errors.')
        notes += ['',f"{experiment}: {s['calls']} calls, four base pairs."]
        tex += [r'\begin{center}\small\begin{tabular}{lrrrr}\toprule Condition & Round & Correct / calls & Invalid & Output failures\\\midrule']
        for r in s['absolute']:
            tex.append(f"{labels[r['arm']]} & {r['round']} & {r['correct']}/{r['trajectories']} & {r['invalid_selection']} & {r['operational_failure']}"+r'\\')
        tex += [r'\bottomrule\end{tabular}\end{center}']
        if experiment=='feedback':
            tex += [r'\begin{center}\scriptsize\begin{tabular}{lllccc}\toprule Base & Update & Condition & R1 & R2 & R3\\\midrule']
            for r in s['decision_sequences']:
                choices=[esc(c if c is not None else 'invalid')+(' $\checkmark$' if good else ' $\times$') for c,good in zip(r['choices'],r['correct'])]
                tex.append(' & '.join([r['pair_id'][:6],r['update'][0].upper(),labels[r['arm']],*choices])+r'\\')
            tex += [r'\bottomrule\end{tabular}\end{center}',
                'C/H denote consequential/harmless updates. A check mark means correct for that round; a cross means incorrect or operational failure. '
                'Each row is a dependent three-round sequence, not an independent problem.']
            for arm in config['feedback_arms']:
                ss=[r for r in s['decision_sequences'] if r['arm']==arm]
                initial=[r for r in ss if r['initially_wrong_valid']]
                p2=sum(r['initial_wrong_choice_persists_and_still_wrong_round_2'] is True for r in initial)
                p3=sum(r['initial_wrong_choice_persists_and_still_wrong_round_3'] is True for r in initial)
                d2=sum(r['initial_wrong_followup_valid_round_2'] for r in initial)
                d3=sum(r['initial_wrong_followup_valid_round_3'] for r in initial)
                text=f"{labels[arm]}: {len(initial)} valid initially wrong sequences; unchanged-and-still-wrong with valid follow-up: round 2 {p2}/{d2}, round 3 {p3}/{d3}. "
                for transition in ('1_to_2','2_to_3'):
                    valid=sum(r[transition]['both_valid'] for r in ss)
                    ctw=sum(r[transition]['correct_to_incorrect'] for r in ss)
                    wtc=sum(r[transition]['incorrect_to_correct'] for r in ss)
                    text+=f"{transition.replace('_',' ')}: {ctw} correct-to-wrong and {wtc} wrong-to-correct among {valid} valid transitions. "
                for u in ('consequential','harmless'):
                    group=[r for r in ss if r['update']==u]
                    text+=f"Both pre-update and post-update answers correct ({u}): {sum(r['correct_update_response_or_stability'] for r in group)}/{len(group)}. "
                tex.append(text);notes+=['',text]
            keep={'round_3/both/feedback_minus_fresh','round_3/both/feedback_minus_length_control'}
        else:
            table={}
            for r in s['all_case_decisions']:table.setdefault((r['pair_id'],r['world']),{})[r['arm']]=r
            tex += [r'\begin{center}\scriptsize\begin{tabular}{lrrrrr}\toprule Base/world & Correct choice & Single & Same & Relays & Roles\\\midrule']
            for (pid,w),arms in sorted(table.items()):
                tex.append(' & '.join([pid[:6]+'/'+str(w),arms['single']['oracle_choice'],
                    *[esc(arms[a]['choice'] or 'invalid') for a in config['consensus_arms']]])+r'\\')
            tex += [r'\bottomrule\end{tabular}\end{center}']
            keep={'different_relays_minus_same_worker','authority_labels_minus_different_relays'}
        effects=[r for r in s['contrasts'] if r['metric']=='correct' and r['contrast'] in keep]
        selected_effects+=effects
        for r in effects:
            text=(f"{r['contrast']}: {100*r['estimate']:+.2f} percentage points, descriptive cluster interval "
                  f"[{100*r['lower']:+.2f}, {100*r['upper']:+.2f}]; {r['increases']} corrections, {r['decreases']} regressions, "
                  f"{r['unchanged']} unchanged pairs of decisions.")
            tex.append(esc(text));notes+=['',text]
    if selected_effects:
        fig,axes=plt.subplots(1,2,figsize=(8,3.1),gridspec_kw={'width_ratios':[1.3,1]})
        for i,r in enumerate(selected_effects):
            x=100*r['estimate'];axes[0].errorbar(x,i,xerr=[[x-100*r['lower']],[100*r['upper']-x]],fmt='o',capsize=3)
            axes[1].plot(range(1,5),[100*v for _,v in sorted(r['base_effects'].items())],'.-',label=str(i+1))
        axes[0].set_yticks(range(len(selected_effects)),[r['contrast'].replace('round_3/both/','').replace('_',' ') for r in selected_effects],fontsize=7)
        axes[0].axvline(0,color='grey',lw=1);axes[0].set_xlabel('Accuracy difference (pp)')
        axes[1].axhline(0,color='grey',lw=1);axes[1].set_xticks(range(1,5));axes[1].set_xlabel('Base ID order');axes[1].set_ylabel('Case effect (pp)');axes[1].legend(fontsize=7)
        fig.tight_layout();fig.savefig(folder/'paired-effects.pdf');fig.savefig(folder/'paired-effects.png',dpi=160);plt.close(fig)
        tex += [r'\begin{figure}[ht]\centering\includegraphics[width=\linewidth]{../results/adjacent-explorations-v1/figures/paired-effects.pdf}\caption{Exploratory paired effects and all four base effects. Intervals enumerate whole-base bootstrap draws; four clusters provide limited uncertainty information. Numbered lines follow the contrasts from top to bottom.}\end{figure}']
    tex.append('All cases are shown. Raw-trace references use the smallest lexical base ID in each mutation family, selected before outputs. '
               'A trace illustrates observable messages, not a faithful internal reasoning path. The experiment remains exploratory regardless of effect direction.')
Path('manuscript/generated/adjacent-explorations.tex').write_text('\n\n'.join(tex).rstrip()+'\n')
Path('ADJACENT_EXPLORATIONS_STATUS.md').write_text('\n'.join(notes).rstrip()+'\n')
Path('records/adjacent-report-status.json').write_text(json.dumps({'source_sha256':digest(data) if data else None,
    'experiments':{e:s.get('status','not launched' if stop.exists() else 'pending') for e,s in states.items()},
    'human_scientific_review':'pending'},indent=2)+'\n')
print(json.dumps({'adjacent_supplement':{e:s.get('complete',False) for e,s in states.items()}}))
