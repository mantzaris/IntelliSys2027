"""Reproducible intent-follow-up figures: actual levels, changes, and pending cells."""
from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[2]/'artifacts/matplotlib-cache'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pcc.resources import sha256
from .common import ROOT,REPORTS,read,write

COLORS={'base':'#777777','C1':'#236A9B','C3':'#D66D26','C5':'#6B498C'}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'intent002','pdf.fonttype':42})


def save(fig,name,caption,inputs,manifest):
    directory=REPORTS/'intent_figures';directory.mkdir(exist_ok=True)
    fig.tight_layout()
    for extension in ('pdf','svg','png'):
        kwargs={'dpi':180} if extension=='png' else {'metadata':{'CreationDate':None,'ModDate':None}} if extension=='pdf' else {'metadata':{'Date':None}}
        fig.savefig(directory/f'{name}.{extension}',bbox_inches='tight',**kwargs)
    plt.close(fig)
    svg=directory/f'{name}.svg';svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    manifest[name]={'caption':caption,'inputs':{str(p.relative_to(ROOT)):sha256(p) for p in inputs},
      'outputs':{ext:sha256(directory/f'{name}.{ext}') for ext in ('pdf','svg','png')}}


def main():
    manifest={};levels=read(REPORTS/'core_horizon_levels.json');interactions=read(REPORTS/'core_horizon_interactions.json')
    fig,axes=plt.subplots(1,2,figsize=(10,3.8))
    for method in ('C1','C3','C5'):
        values=[r for r in levels if r['condition']==method and r['status']=='completed'];xs=[r['horizon'] for r in values];ys=[r['paired_success'] for r in values]
        axes[0].scatter(xs,ys,label=method,color=COLORS[method],s=55)
        if len(values)==3:axes[0].plot(xs,ys,color=COLORS[method],alpha=.6)
    for horizon in (32,64,128):
        if not any(r['horizon']==horizon and r['status']=='completed' for r in levels):axes[0].text(horizon,.06,'pending',ha='center',color='#777')
    axes[0].set(xticks=[32,64,128],xlim=(24,136),ylim=(0,1),xlabel='Separately scripted horizon (user turns)',ylabel='Paired success',title='Absolute performance: fixed 48 families');axes[0].legend(frameon=False)
    any_complete=False
    for i,r in enumerate(interactions):
        if r['status']=='completed':
            any_complete=True;x=100*r['interaction'];lo,hi=[100*v for v in r['interaction_ci95']]
            axes[1].errorbar(x,i,xerr=[[x-lo],[hi-x]],fmt='o',color=COLORS['C5'],capsize=3)
        else:axes[1].text(.05,i,'pending 32- and 128-turn runs',va='center',fontsize=9)
    axes[1].set(yticks=[0,1],yticklabels=['C5 versus C3','C5 versus C1'],ylim=(-.6,1.6),xlabel='128-minus-32 interaction (percentage points)',title='Change with horizon is a separate question')
    axes[1].axvline(0,color='#777',lw=.8)
    if not any_complete:axes[1].set_xlim(-.1,1);axes[1].set_xticks([])
    save(fig,'core_horizon_level_and_change','Original Qwen seed17 horizon study; same preselected 48 paired families. Current completed 64-turn cells are subsets of main evaluations. Missing horizons are pending; no trend is inferred through missing cells. When complete, exploratory interaction bars use paired family bootstrap (10,000 draws, seed720021), preserving worlds and horizons. A positive change interaction does not establish superior absolute 128-turn performance.',[REPORTS/'core_horizon_levels.json',REPORTS/'core_horizon_interactions.json'],manifest)
    curves=read(REPORTS/'trajectory_by_turn.json');fig,axes=plt.subplots(1,3,figsize=(12,3.7),sharey=True)
    for ax,seed in zip(axes,(17,29,43)):
        found=False
        for method in ('C1','C3','C5'):
            rows=[r for r in curves if r['model']=='qwen' and r['condition']==method and r['seed']==seed]
            if rows:
                found=True;ax.plot([r['turn'] for r in rows],[r['success']/r['conversations'] for r in rows],color=COLORS[method],label=method,lw=1.25)
        if not found:ax.text(.5,.5,'pending',ha='center',transform=ax.transAxes,color='#777')
        ax.axvline(32,color='#777',ls=':',lw=.8);ax.set(title=f'Training seed {seed}',xlabel='User turn within the 64-turn script',ylim=(0,1),xlim=(1,64));ax.grid(axis='y',alpha=.15)
    axes[0].set_ylabel('Unconditional conversation correctness');axes[0].legend(frameon=False,fontsize=8)
    save(fig,'dynamic_core_trajectories','Qwen C1/C3/C5, every completed seed, 480 conversations (240 paired families) at each of 64 user turns. Each response is scored against the oracle state at that turn, not the final target. Lines show descriptive marginal conversation correctness, not independent-turn inference or qualitative helpfulness. The dotted line marks the paired authorized/hypothetical event; other events and public request wording also vary by turn. Final-turn success cannot substitute for trajectory correctness. Missing seed cells remain pending.',[REPORTS/'trajectory_by_turn.json'],manifest)
    contrasts=[r for r in read(REPORTS/'paired_trajectory_contrasts.json') if r['metric']=='mean_world_all_turn_success'];fig,ax=plt.subplots(figsize=(8,3.4))
    for i,r in enumerate(contrasts):
        x=100*r['difference'];lo,hi=100*r['ci95_low'],100*r['ci95_high'];ax.errorbar(x,i,xerr=[[x-lo],[hi-x]],fmt='o',color=COLORS['C5'],capsize=3)
    ax.set(yticks=range(len(contrasts)),yticklabels=[f'{r["contrast"]}, seed {r["seed"]}' for r in contrasts],xlabel='Difference in mean all-turn correctness (percentage points)');ax.axvline(0,color='#777',lw=.8);ax.invert_yaxis()
    save(fig,'dynamic_core_contrasts','Exploratory C5-minus-control difference in mean correctness across all 64 turns and both worlds, all 240 families per completed Qwen seed. Intervals resample whole paired families (10,000 draws, seed720023); no seed-population uncertainty is represented. Methods visit different endogenous error states, so these are trajectory associations rather than matched-state repair effects. All initially incorrect and never-correct episodes remain.',[REPORTS/'paired_trajectory_contrasts.json'],manifest)
    clarifications=read(REPORTS/'clarification_audit.json');fig,axes=plt.subplots(1,3,figsize=(12,3.5),sharey=True)
    fields=[('unnecessary_clarification','Unnecessary','#236A9B'),('missed_necessary_clarification','Missed','#D66D26'),('wrong_issue_clarification','Wrong issue','#6B498C')]
    for ax,seed in zip(axes,(17,29,43)):
        for i,method in enumerate(('C1','C3','C5')):
            row=next((r for r in clarifications if r['model']=='qwen' and r['condition']==method and r['seed']==seed),None)
            if row:
                for j,(field,label,color) in enumerate(fields):ax.bar(i+(j-1)*.22,row[field],.21,color=color,label=label if i==0 else None)
            else:ax.text(i,2,'pending',rotation=90,ha='center',color='#777',fontsize=8)
        ax.set(xticks=range(3),xticklabels=['C1','C3','C5'],title=f'Seed {seed}')
    axes[0].set_ylabel('Final conversation flags / 480');axes[0].legend(frameon=False,fontsize=8)
    save(fig,'clarification_types','Final-turn structured clarification audit, completed Qwen C1/C3/C5 seeds, 480 conversations each. Flags overlap and are not stacked or summed. Wrong-issue clarification can both add an unnecessary issue and miss the necessary one. Structured nulling/clarification does not reveal prose uncertainty acknowledgment or human-rated helpfulness. All original scorer results remain unchanged.',[REPORTS/'clarification_audit.json'],manifest)
    exposure=[r for r in read(REPORTS/'clarification_exposure.json') if r['model']=='qwen' and r['condition'] in ('C1','C3','C5') and r['pool']=='recovery'];fits=sorted({r['run_id'] for r in exposure});fig,axes=plt.subplots(2,1,figsize=(11,6),sharex=True)
    labels=[]
    for i,run_id in enumerate(fits):
        rows=[r for r in exposure if r['run_id']==run_id];nonempty=next(r for r in rows if r['clarification_target_class']=='nonempty');empty=next(r for r in rows if r['clarification_target_class']=='empty');total=nonempty['target_tokens']+empty['target_tokens']
        axes[0].bar(i,nonempty['target_tokens']/total if total else 0,color=COLORS[nonempty['condition']]);axes[1].bar(i-.15,nonempty['loss_contributing_unique_examples'],.3,color='#236A9B',label='Unique windows' if i==0 else None);axes[1].bar(i+.15,nonempty['contributing_occurrences'],.3,color='#D66D26',label='Loss-contributing occurrences' if i==0 else None)
        labels.append(f'{nonempty["condition"]} s{nonempty["seed"]}\nr{nonempty["round"]}')
    axes[0].set(ylabel='Nonempty-clarification examples:\nshare of recovery target tokens',ylim=(0,1.05));axes[1].set(ylabel='Nonempty-clarification\nrecovery exposure',xticks=range(len(fits)),xticklabels=labels);axes[1].legend(frameon=False,fontsize=8)
    save(fig,'clarification_supervision_exposure','Exact reconstructed supervised loss exposure for completed Qwen C1/C3/C5 fits by seed and round. Tokens are whole completion targets in examples whose clarification target is nonempty, not tokens specifically in the clarification field. Loaded-only examples and masked orphan suffixes are excluded. Exposure/outcome associations are not causal evidence. Counts show repetition and diversity separately.',[REPORTS/'clarification_exposure.json'],manifest)
    evidence=[r for r in read(REPORTS/'evidence_audit.json') if r['model']=='qwen' and r['condition'] in ('C1','C3','C5')];fig,axes=plt.subplots(1,2,figsize=(11,3.6));x=np.arange(len(evidence));labels=[f'{r["condition"]}\ns{r["seed"]}' for r in evidence]
    axes[0].bar(x,[r['original_source_error_conversations']/480 for r in evidence],color=[COLORS[r['condition']] for r in evidence]);axes[0].set(xticks=x,xticklabels=labels,ylabel='Original source-error fraction / 480',ylim=(0,1))
    fields=[('assistant_authority_references','Assistant source','#236A9B'),('not_visible_references','Unavailable','#D66D26'),('anaphoric_user_reaffirmation_needs_semantic_review_references','Anaphoric / unresolved','#6B498C')]
    for j,(field,label,color) in enumerate(fields):axes[1].bar(x+(j-1)*.23,[r[field] for r in evidence],.22,color=color,label=label)
    axes[1].set(xticks=x,xticklabels=labels,ylabel='Reference flags / 2,880');axes[1].legend(frameon=False,fontsize=8)
    save(fig,'source_reference_types','Original source-error flags per 480 conversations (left) and separate overlapping flags per 2,880 slot references (right), completed Qwen C1/C3/C5 seeds. References can be both assistant-authored and unavailable. Anaphoric user support remains semantically unresolved; no automatic rescoring or validated human annotation is claimed.',[REPORTS/'evidence_audit.json'],manifest)
    dynamics=read(REPORTS/'source_dynamics_by_turn.json');seeds=sorted({r['seed'] for r in dynamics});fig,axes=plt.subplots(3,len(seeds),figsize=(5*len(seeds),8),sharex=True,sharey=True,squeeze=False)
    for mi,method in enumerate(('C1','C3','C5')):
        for si,seed in enumerate(seeds):
            ax=axes[mi,si];rows=[r for r in dynamics if r['condition']==method and r['seed']==seed]
            if rows:
                ax.plot([r['turn'] for r in rows],[r['all_canonical_visible']/480 for r in rows],color='#777777',ls='--',label='All canonical user sources visible')
                ax.plot([r['turn'] for r in rows],[r['recall_correct']/480 for r in rows],color=COLORS[method],label='Correct output state')
            else:ax.text(.5,.5,'pending',ha='center',transform=ax.transAxes)
            ax.set(title=f'{method}, seed {seed}',ylim=(0,1),xlim=(1,64));ax.grid(axis='y',alpha=.15)
            if si==0:ax.set_ylabel('Fraction of 480 conversations')
            if mi==2:ax.set_xlabel('User turn in the 64-turn script')
    axes[0,0].legend(frameon=False,fontsize=7)
    save(fig,'source_access_and_state','Post-curve exploratory temporal source audit, completed Qwen C1/C3/C5 seeds, 240 paired families / 480 conversations at each turn. Grey dashed lines characterize the supplied source set using oracle annotations only after generation; colored lines show correct six-value output state. State recall is distinct from executable-plan success. Canonical-source absence does not imply all evidence is absent: working memory and retrieved assistant responses can carry it. Source access and state accuracy are associated, not a randomized causal contrast. No retrieval or memory policy changed.',[REPORTS/'source_dynamics_by_turn.json'],manifest)
    write(REPORTS/'INTENT_FIGURE_MANIFEST.json',manifest)
    text=['# Intent follow-up figures','']
    for name,v in manifest.items():text += [f'## {name}','',v['caption'],'',f'[PDF](intent_figures/{name}.pdf) · [SVG](intent_figures/{name}.svg) · [PNG](intent_figures/{name}.png)','']
    text+=['Fresh intent scores and method-by-horizon plots are pending actual complete outputs and human ratings; no synthetic results are plotted.']
    (REPORTS/'INTENT_FIGURES.md').write_text('\n'.join(text)+'\n')
    print({'figures':len(manifest),'new_intent_scores_plotted':False})


if __name__=='__main__':main()
