"""Publication-style interim plots; missing seeds are explicitly pending."""
from collections import defaultdict
from pathlib import Path
import json
import os
os.environ.setdefault("MPLCONFIGDIR",str(Path(__file__).resolve().parents[2]/"artifacts/matplotlib-cache"))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pcc.resources import sha256
from .common import ROOT,OUT,read,write

COLORS={17:'#1768A5',29:'#C65B25',43:'#3D8C62'}
CONDITIONS=['base','C1','C3','C4','C5','C6','A1','A2','A3','C2']


def finish(fig,name,caption,inputs,manifest):
    directory=OUT/'figures';directory.mkdir(exist_ok=True)
    fig.savefig(directory/(name+'.pdf'),bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None})
    fig.savefig(directory/(name+'.svg'),bbox_inches='tight',metadata={'Date':None})
    fig.savefig(directory/(name+'.png'),bbox_inches='tight',dpi=170)
    plt.close(fig)
    svg=directory/(name+'.svg');svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    manifest[name]={'caption':caption,'inputs':{str(p.relative_to(ROOT)):sha256(p) for p in inputs},
      'outputs':{extension:sha256(directory/(name+'.'+extension)) for extension in ('pdf','svg','png')}}


def main():
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'overnight-001','pdf.fonttype':42})
    table=OUT/'per_seed_results.json';rows=read(table);contrasts=read(OUT/'paired_transitions.json');strata=read(OUT/'strata.json');pools=read(OUT/'supervision_pools.json');manifest={}
    fig,axes=plt.subplots(1,2,figsize=(11,4.2),sharey=True)
    for ax,model in zip(axes,('qwen','phi')):
        available=[r for r in rows if r['model']==model];conditions=CONDITIONS if model=='qwen' else ['base','C1','C3','C5']
        for i,c in enumerate(conditions):
            matches=[r for r in available if r['condition']==c]
            for r in matches:
                shift=0 if c=='base' else {17:-.16,29:0,43:.16}[r['seed']]
                ax.scatter(i+shift,r['paired_success'],s=48,c=COLORS[r['seed']],marker='D' if c=='base' else 'o',zorder=3)
            complete=len(matches)
            if not matches:ax.text(i,.02,'pending',rotation=90,ha='center',va='bottom',color='#777',fontsize=8)
            elif c!='base':ax.text(i,1.015,f'{complete}/3',ha='center',fontsize=8,color='#666')
        ax.set(xticks=range(len(conditions)),xticklabels=conditions,ylim=(-.015,1.09),title=model.upper(),ylabel='Paired task success' if model=='qwen' else '')
        ax.grid(axis='y',alpha=.2)
    handles=[plt.Line2D([],[],linestyle='',marker='o',color=color,label=f'Seed {s}') for s,color in COLORS.items()]
    axes[0].legend(handles=handles,loc='upper right',frameon=False)
    finish(fig,'paired_success','Antagonist-free 64-turn paired success, 240 families per model/condition/seed. Each point is one actual seed; diamonds are the single untrained reference. No seed-error bars are invented. Counts show completed/planned trained seeds; missing cells are pending.',[table],manifest)
    key=[r for r in contrasts if r['contrast'] in {'C5-C3','C5-C1','C5-C4','C5-A1','C5-A2','C5-A3','C3-C1'}]
    fig,ax=plt.subplots(figsize=(9,max(3,len(key)*.38+1)))
    if key:
        for i,r in enumerate(key):
            mean=100*r['difference'];ax.errorbar(mean,i,xerr=[[mean-100*r['ci95_low']],[100*r['ci95_high']-mean]],fmt='o',color=COLORS[r['seed']],capsize=3)
        ax.set(yticks=range(len(key)),yticklabels=[f'{r["model"]} {r["contrast"]}, seed {r["seed"]}' for r in key])
    else:ax.text(.5,.5,'Key trained comparisons pending',ha='center',transform=ax.transAxes);ax.set_yticks([])
    missing=[c for c in ('C5-C3','C5-C1','C5-C4','C5-A1','C5-A2','C5-A3') if not any(r['contrast']==c for r in key)]
    ax.axvline(0,color='#555',lw=1);ax.set_xlabel('Difference in paired success (percentage points)');ax.invert_yaxis()
    fig.text(.02,-.04,'Pending: '+', '.join(missing) if missing else 'All listed comparisons have at least one seed.',fontsize=9)
    finish(fig,'paired_contrasts','Individual-seed contrasts on common 240 paired families, 64 turns. Bars are exploratory family-bootstrap 95% intervals (10,000 draws, seed 40721). They do not capture training-seed variation; an interval containing zero is not equivalence. Complete planned-seed inference uses the separate frozen two-way analysis.',[OUT/'paired_transitions.json'],manifest)
    fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
    for ax,model in zip(axes,('qwen','phi')):
        groups=defaultdict(dict)
        for r in strata:
            if r['model']==model and r['dimension']=='heldout_rule':groups[r['condition'],r['seed']][r['level']]=r
        for i,((condition,seed),levels) in enumerate(groups.items()):
            for rule,marker,shift in [(False,'o',-.13),(True,'^',.13)]:
                r=levels[rule];ax.scatter(i+shift,r['paired_successes']/r['n_families'],color=COLORS[seed],marker=marker,s=45)
        ax.set(xticks=range(len(groups)),xticklabels=[f'{c}\ns{s}' for c,s in groups],ylim=(0,1.05),title=model.upper())
        ax.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('Paired task success');axes[0].legend(handles=[plt.Line2D([],[],marker=m,linestyle='',color='#333',label=l) for m,l in [('o','Familiar'),('^','Held-out rule')]],frameon=False)
    finish(fig,'rule_structure','Separate familiar versus held-out conditional rules, 120 paired families in each stratum, 64 turns; actual completed seed values only. These are descriptive strata with no independent-turn uncertainty. All ambiguous locked-test families are creative/held-out, so ambiguity is confounded.',[OUT/'strata.json'],manifest)
    fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
    for ax,model in zip(axes,('qwen','phi')):
        subset=[r for r in rows if r['model']==model];x=np.arange(len(subset))
        ax.bar(x-.18,[r['recall_correct_conversations']/480 for r in subset],.36,label='All commitments recalled',color='#7899B7')
        ax.bar(x+.18,[r['conversation_successes']/480 for r in subset],.36,label='Executable task success',color='#253B51')
        ax.set(xticks=x,xticklabels=[f'{r["condition"]}\ns{r["seed"]}' for r in subset],ylim=(0,1.05),title=model.upper())
    axes[0].set_ylabel('Fraction of conversations');axes[0].legend(frameon=False,fontsize=8)
    finish(fig,'recall_behavior','Recall and behavioral success are separate endpoints over the same 480 conversations/seed at 64 turns. Recall requires six correct state values; behavioral success requires the eight executable decisions and correct clarification. Worlds are paired; these bars are descriptive, not independent-sample inference.',[table],manifest)
    recovery=[r for r in pools if r['pool']=='recovery'];fig,axes=plt.subplots(2,1,figsize=(11,6.5),sharex=True)
    x=np.arange(len(recovery));axes[0].bar(x,[r['loss_contributing_unique_windows'] for r in recovery],color='#1768A5',label='Unique recovery windows contributing loss')
    axes[0].scatter(x,[r['loss_contributing_occurrences'] for r in recovery],color='#C65B25',s=26,label='Occurrences contributing loss')
    axes[0].set_ylabel('Recovery exposure counts');axes[0].legend(frameon=False,fontsize=8)
    axes[1].bar(x,[r['top5_token_share'] or 0 for r in recovery],color='#3D8C62');axes[1].set(ylabel='Top-five recovery-window\nshare of recovery target tokens',ylim=(0,1.05),xticks=x)
    labels=[]
    for r in recovery:
        round_name='r1' if '-r1-' in r['run_id'] else 'r0';labels.append(f'{r["model"]} {r["condition"]}\ns{r["seed"]} {round_name}')
    axes[1].set_xticklabels(labels,rotation=35,ha='right')
    finish(fig,'recovery_exposure','Exact reconstructed optimizer-loss exposure per completed fit, by model/condition/seed/round. Loaded buffer windows are excluded unless they contribute unmasked target loss. Repeated occurrences and top-five token shares quantify concentration, not additional independent recovery examples. Resume-prefix and orphaned suffix masking follow the frozen code.',[OUT/'supervision_pools.json'],manifest)
    write(OUT/'FIGURE_MANIFEST.json',manifest)
    captions=['# Figure captions and provenance\n']
    for name,entry in manifest.items():captions.append(f'## {name}\n\n{entry["caption"]}\n\n[PDF](figures/{name}.pdf) · [SVG](figures/{name}.svg) · [PNG](figures/{name}.png)\n')
    captions.append('Memory-removal and contested-goal plots remain pending; no supplementary model outcomes exist yet.\n')
    (OUT/'FIGURES.md').write_text('\n'.join(captions))
    print(json.dumps({'figures':len(manifest),'completed_seed_points':len(rows)}))


if __name__=='__main__':main()
