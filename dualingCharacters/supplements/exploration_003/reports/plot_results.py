"""Compact vector figures rendered only from saved frozen-analysis tables."""
from collections import defaultdict
from pathlib import Path
from datetime import datetime
import csv
import json
import statistics
import os
from supplements.exploration_003.common import HERE,REPORTS,CACHE,read,write,sha256
os.environ.setdefault('MPLCONFIGDIR',str(CACHE/'matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from supplements.exploration_003.analysis import verify_science

COLORS={'C3':'#2166ac','C5':'#b35806','balanced_mixture':'#5e3c99'}

def rows(name):
    with (REPORTS/name).open() as f:return list(csv.DictReader(f))

def save(fig,name):
    out=REPORTS/'figures';out.mkdir(exist_ok=True)
    fig.tight_layout()
    frozen_at=read(HERE/'SCIENTIFIC_MANIFEST.json')['frozen_utc']
    for ext in ('pdf','svg','png'):
        metadata=None
        if ext=='pdf':metadata={'Creator':'exploration003 saved-data plotting','CreationDate':datetime.fromisoformat(frozen_at),'ModDate':datetime.fromisoformat(frozen_at)}
        if ext=='svg':metadata={'Creator':'exploration003 saved-data plotting','Date':frozen_at}
        fig.savefig(out/f'{name}.{ext}',dpi=190,bbox_inches='tight',metadata=metadata)
        if ext=='svg':
            path=out/f'{name}.{ext}'
            path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
    plt.close(fig)

def main():
    verify_science()
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,
       'pdf.fonttype':42,'ps.fonttype':42,'svg.hashsalt':'exploration003','figure.facecolor':'white'})
    curve=[r for r in rows('coverage_curves.csv') if r['cohort']=='primary_mechanism' and r['condition'] in ('C3','C5')]
    contrasts=read(REPORTS/'primary_paired_contrasts.json')
    fig,axes=plt.subplots(1,2,figsize=(8.4,3.1))
    for condition in ('C3','C5'):
        r=[x for x in curve if x['condition']==condition]
        axes[0].plot([int(x['budget']) for x in r],[float(x['mean_episode_coverage']) for x in r],marker='o',ms=3,label=condition,color=COLORS[condition])
    axes[0].set(xlabel='Consumed intervention opportunities',ylabel='Mean distinct categories / episode',ylim=(0,8),title='Observable breadth')
    axes[0].legend(frameon=False)
    selected=[r for r in contrasts if r['metric']=='coverage']
    x=[r['budget'] for r in selected];y=[r['difference'] for r in selected]
    axes[1].axhline(0,color='.5',lw=.8);axes[1].plot(x,y,color=COLORS['C5'])
    axes[1].fill_between(x,[r['family_interval'][0] for r in selected],[r['family_interval'][1] for r in selected],color=COLORS['C5'],alpha=.2)
    axes[1].set(xlabel='Consumed intervention opportunities',ylabel='C5 − C3 categories / episode',title='Paired difference; pointwise 95% intervals')
    for ax in axes:ax.set_xticks([1,4,8,12]);ax.grid(axis='y',alpha=.15)
    save(fig,'coverage_vs_budget')

    novelty=rows('primary_novelty.csv');archive=rows('archive_rarefaction.csv')
    fig,axes=plt.subplots(1,2,figsize=(8.4,3.1))
    for j,condition in enumerate(('C3','C5')):
        values=[statistics.mean(int(r['new_categories']) for r in novelty if r['condition']==condition and int(r['segment_start'])==s) for s in (1,5,9)]
        axes[0].bar(np.arange(3)+(j-.5)*.34,values,width=.32,label=condition,color=COLORS[condition])
    axes[0].set(xticks=np.arange(3),xticklabels=['1–4','5–8','9–12'],xlabel='Opportunity segment',ylabel='Mean newly reached categories',title='New categories over time',ylim=(0,4))
    axes[0].legend(frameon=False)
    for condition in ('C3','C5','balanced_mixture'):
        means=[];low=[];high=[]
        for n in range(1,9):
            v=[int(r['categories']) for r in archive if r['condition']==condition and int(r['families'])==n]
            means.append(statistics.mean(v));low.append(min(v));high.append(max(v))
        axes[1].plot(range(1,9),means,label=condition.replace('_',' '),color=COLORS[condition])
        axes[1].fill_between(range(1,9),low,high,color=COLORS[condition],alpha=.1)
    axes[1].set(xlabel='Whole paired families (24 opportunities each)',ylabel='Pooled categories',title='Archive ordering / allocation sensitivity',ylim=(0,42))
    axes[1].legend(frameon=False,fontsize=8)
    for ax in axes:ax.grid(axis='y',alpha=.15)
    save(fig,'novelty_and_archive')

    persistence=rows('persistence_by_role.csv')
    chosen=[next(r for r in persistence if r['id']==f'mechanism-final-001__{c}' and r['role']==role) for c,role in [('C3','Generic'),('C5','Hyde'),('C5','Rival')]]
    fig,axes=plt.subplots(1,2,figsize=(8.4,3.1));labels=['C3 generic\n(two contexts)','C5 Hyde','C5 Rival'];palette=[COLORS['C3'],COLORS['C5'],COLORS['C5']]
    for ax,numerator,denominator,title in [(axes[0],'same_goal','goal_comparisons','Repeated slot/value goal'),(axes[1],'same_goal_tactic_changes','same_goal','API/reference change within repeated goals')]:
        values=[int(r[numerator])/int(r[denominator]) for r in chosen]
        ax.bar(range(3),values,color=palette)
        for i,r in enumerate(chosen):ax.text(i,values[i]+.025,f"{r[numerator]}/{r[denominator]}",ha='center',fontsize=8)
        ax.set(xticks=range(3),xticklabels=labels,ylim=(0,1.12),ylabel='Descriptive fraction',title=title)
        ax.grid(axis='y',alpha=.15)
    save(fig,'repetition_and_persistence')

    overlap=read(REPORTS/'primary_category_overlap.json');episode=rows('primary_overlap.csv')
    fig,axes=plt.subplots(1,2,figsize=(8.4,3.1))
    shared=len(overlap['shared']);only=[len(overlap['C3_only']),len(overlap['C5_only'])]
    axes[0].bar([0,1],[shared,shared],color='#bdbdbd',label='Shared')
    axes[0].bar([0,1],only,bottom=[shared,shared],color=[COLORS['C3'],COLORS['C5']],label='Method-only')
    for i,n in enumerate(only):axes[0].text(i,shared+n+.6,str(shared+n),ha='center')
    axes[0].set(xticks=[0,1],xticklabels=['C3','C5'],ylabel='Pooled categories',title='Archive overlap at 192 opportunities each',ylim=(0,43));axes[0].legend(frameon=False,loc='upper center',ncol=2,fontsize=8)
    means=[statistics.mean(float(r[k]) for r in episode) for k in ('C3','C5','mixture_half_prefix')]
    axes[1].bar(range(3),means,color=[COLORS['C3'],COLORS['C5'],COLORS['balanced_mixture']])
    for i,n in enumerate(means):axes[1].text(i,n+.12,f'{n:.2f}',ha='center')
    axes[1].set(xticks=range(3),xticklabels=['C3: 12','C5: 12','C3: 6 + C5: 6'],ylabel='Mean categories / episode',title='Equal opportunity prefix mixture',ylim=(0,8))
    for ax in axes:ax.grid(axis='y',alpha=.15)
    save(fig,'overlap_and_complementarity')

    captions={
      'coverage_vs_budget':'Pinned Qwen base defender and generator, seed17, eight paired families (16 episodes), final mechanism pilot. Endpoint: distinct valid observable descriptors. Right panel uses10,000paired-family bootstrap draws preserving both worlds; intervals are pointwise and omit generator-seed uncertainty. Passes, rejected actions and invalid generations consume opportunities.',
      'novelty_and_archive':'Same Qwen pilot, eight paired families, seed17. Left: episode-level newly reached descriptors in fixed four-opportunity segments, descriptive means. Right:100predefined whole-family orderings; actions retain temporal order and both worlds travel together. Shading is the minimum–maximum ordering/allocation range, not a confidence interval. The mixture alternates methods across families at equal total opportunities; token costs can differ.',
      'repetition_and_persistence':'Same Qwen pilot, eight paired families, seed17. Consecutive direct actions are compared within actor and episode. Numerators/denominators are printed; these dependent action comparisons are descriptive, without action-level error bars. API/reference variation is not validated semantic tactic development.',
      'overlap_and_complementarity':'Same Qwen pilot, eight paired families, seed17. Left: each full archive spends192opportunities; their union would spend384and is not used as a fair gain. Right: each arm spends12opportunities per episode, but the6+6mixture uses two archived prefixes and has separately reported token overhead. No human semantic validation is available.'}
    lines=['# Exploration figures','']
    for name,caption in captions.items():
        lines.extend([f'![{name}](figures/{name}.png)','',caption,'',f'[PDF](figures/{name}.pdf) · [SVG](figures/{name}.svg)',''])
    (REPORTS/'FIGURES.md').write_text('\n'.join(lines).rstrip()+'\n')
    write(REPORTS/'FIGURE_PROVENANCE.json',{'plot_script_sha256':sha256(Path(__file__)),
        'inputs':{n:sha256(REPORTS/n) for n in ['coverage_curves.csv','primary_paired_contrasts.json','primary_novelty.csv','archive_rarefaction.csv','persistence_by_role.csv','primary_category_overlap.json','primary_overlap.csv']},
        'figures':{p.name:sha256(p) for p in sorted((REPORTS/'figures').iterdir())},'captions':captions})
    print({'figures':len(captions),'formats':['PDF','SVG','PNG']})

if __name__=='__main__':main()
