"""Render only completed standalone stages; safe from the periodic mirror hook."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from rep_sensitivity.schema import digest
from rep_sensitivity.pilot_interpretation import write_csv

tex=['% Generated only from complete stage/model analyses.'];status=[]
root=Path('results/root-diagnostic-v1/visible-information-v2.json')
if root.exists() and json.loads(root.read_text()).get('complete'):
    data=json.loads(root.read_text());folder=root.parent/'figures';folder.mkdir(exist_ok=True)
    effects=[r for r in data['effects'] if r['contrast'] in [x+' - F' for x in ('objective0','objective1','objective2','constraint','uniform_objectives')]]
    fig,axes=plt.subplots(1,2,figsize=(9.2,3.9))
    for i,transport in enumerate(('frozen_summaries','lossless')):
        rs=[r for r in effects if r['transport']==transport]
        for j,r in enumerate(rs):
            axes[i].errorbar(100*r['estimate'],j,xerr=[[100*(r['estimate']-r['lower'])],[100*(r['upper']-r['estimate'])]],fmt='o',capsize=3)
        axes[i].set_yticks(range(len(rs)),[r['contrast'].replace('_',' ') for r in rs],fontsize=8)
        axes[i].axvline(0,color='grey',lw=1);axes[i].set_title(transport.replace('_',' '));axes[i].set_xlabel('Accuracy effect (percentage points)')
    fig.suptitle('Root-only diagnostic: six development bases; descriptive cluster intervals',fontsize=10)
    fig.tight_layout();fig.savefig(folder/'root-effects.pdf');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(9.2,3.4))
    for ax,transport in zip(axes,('frozen_summaries','lossless')):
        for arm in ('objective0','objective1','objective2','uniform_objectives'):
            r=next(x for x in effects if x['transport']==transport and x['contrast']==arm+' - F')
            ax.plot(range(1,7),[100*r['base_effects'][p] for p in sorted(r['base_effects'])],'.-',lw=.7,label=arm.replace('_',' '))
        ax.axhline(0,color='grey',lw=1);ax.set_title(transport.replace('_',' '));ax.set_xlabel('Base identifier order');ax.set_ylabel('Paired accuracy effect (pp)')
    axes[1].legend(fontsize=6);fig.tight_layout();fig.savefig(folder/'root-base-distribution.pdf');plt.close(fig)
    write_csv(root.parent/'visible-information-v2.csv',[{k:v for k,v in r.items() if not isinstance(v,dict)} for r in data['aggregate']])
    write_csv(root.parent/'root-paired-effects-v2.csv',[{k:v for k,v in r.items() if not isinstance(v,dict)} for r in data['effects']])
    status.append({'stage':'root-diagnostic-v1','status':'complete diagnostic','independent_base_pairs':6,'trajectories':data['trajectories'],'source_sha256':digest(data)})
    tex+=['\\subsection{Completed root diagnostic}',
        'This diagnostic contains six reused development bases and 192 new root calls. Within each transport interface, repetition changes no distinct supplied proposition. Each objective is repeated selectively, and all objectives are also repeated uniformly. It contains no paraphrase arm. World correctness and agreement with uniquely supported visible decisions are separate outcomes; contradictory and ill-typed inputs are not silently repaired.',
        '\\begin{figure}[ht]\\centering\\includegraphics[width=\\linewidth]{../results/root-diagnostic-v1/figures/root-effects.pdf}\\caption{Root-only effects with descriptive unstratified whole-base intervals. Six bases support diagnostic interpretation only; the original stratified intervals remain unavailable.}\\end{figure}']
else:status.append({'stage':'root-diagnostic-v1','status':'pending'})

path=Path('results/objective-confirmation-v1/analysis.json')
models=json.loads(path.read_text()).get('model_results',[]) if path.exists() else []
for result in models:
    if not result['complete']:continue
    model=result['model'];folder=path.parent/model/'figures';folder.mkdir(parents=True,exist_ok=True)
    rs=result['contrasts'];chosen=[r for r in rs if r['primary']]
    fig,ax=plt.subplots(figsize=(7.0,3.0))
    for i,r in enumerate(chosen):ax.errorbar(100*r['estimate'],i,xerr=[[100*(r['estimate']-r['lower'])],[100*(r['upper']-r['estimate'])]],fmt='o',capsize=3)
    ax.set_yticks(range(len(chosen)),[r['contrast'].replace('_',' ') for r in chosen],fontsize=8)
    ax.axvline(0,color='grey',lw=1);ax.set_xlabel('Accuracy effect (percentage points)');ax.set_title(model+': 24 fresh scheduling bases')
    fig.tight_layout();fig.savefig(folder/'confirmation-effects.pdf');plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.0,3.0))
    for r in chosen:
        keys=sorted(r['base_effects']);ax.plot(range(1,len(keys)+1),[100*r['base_effects'][k] for k in keys],'.-',lw=.7,label=r['contrast'].replace('_',' '))
    ax.axhline(0,color='grey',lw=1);ax.set_xlabel('Base identifier order');ax.set_ylabel('Paired effect (pp)');ax.legend(fontsize=7)
    fig.tight_layout();fig.savefig(folder/'confirmation-base-distribution.pdf');plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.0,3.1))
    for r in result['absolute']:
        x=r['inference_seconds_allocated']/r['trajectories'];y=100*r['metrics']['correct']['mean']
        ax.scatter(x,y,s=35,label=r['arm'].replace('_',' '))
    ax.set_xlabel('Logical allocated batch seconds / decision');ax.set_ylabel('Accuracy (%)');ax.legend(fontsize=7)
    fig.tight_layout();fig.savefig(folder/'confirmation-cost-accuracy.pdf');plt.close(fig)
    tex+=['\\subsection{Fresh objective confirmation: '+model+'}',
        str(result['independent_base_pairs'])+' independent scheduling pairs, '+str(result['trajectories'])+' trajectories and '+str(result['physical_calls'])+' physical calls completed. All five arms use the same required claims and hierarchy. Balanced repetition adds more tokens than selective repetition; its contrast combines balance with length/dose. Both-world correctness and complete-proposition retention are separately reported in the reproducibility artifacts.',
        '\\begin{center}\\small\\begin{tabular}{lrrr}\\toprule Arm & Accuracy (\\%) & Invalid (\\%) & Objective retained (\\%)\\\\\\midrule']
    for r in result['absolute']:
        tex.append(r['arm'].replace('_',' ')+' & '+f"{100*r['metrics']['correct']['mean']:.2f} & {100*r['metrics']['invalid_selection']['mean']:.2f} & {100*r['metrics']['objective_retention']['mean']:.2f}"+'\\\\')
    tex+=['\\bottomrule\\end{tabular}\\end{center}',
        '\\begin{figure}[ht]\\centering\\includegraphics[width=.95\\linewidth]{../results/objective-confirmation-v1/'+model+'/figures/confirmation-effects.pdf}\\caption{Prespecified repetition and balance contrasts for '+model+'. Intervals resample whole base pairs within mutation-family and change-status strata.}\\end{figure}']
    status.append({'stage':'objective-confirmation-v1','model':model,'status':'complete model','independent_base_pairs':24,'trajectories':result['trajectories'],'source_sha256':digest(result)})
if not models:status.append({'stage':'objective-confirmation-v1','status':'pending'})
Path('manuscript/generated/completed-extensions.tex').write_text('\n'.join(tex)+'\n')
Path('records/completed-extensions-status.json').write_text(json.dumps({'stages':status,'human_scientific_review':'pending'},indent=2)+'\n')
print(json.dumps({'completed_models':len(models),'root_complete':root.exists()}))
