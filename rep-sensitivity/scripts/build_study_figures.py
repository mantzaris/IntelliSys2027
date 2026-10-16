"""Readable standalone figures from completed analyses; no inference or selection."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({'font.size':10,'axes.titlesize':11,'axes.labelsize':10,'xtick.labelsize':9,'ytick.labelsize':9,
                     'pdf.fonttype':42,'ps.fonttype':42})
names={'qwen3':'Qwen3-14B','phi4':'Phi-4','equal_model_average':'Equal-model mean'}
colors={'single':'#606b75','exact':'#2369a0','paraphrase':'#c06e19'}
for suite in ('pilot-v7','main-v7'):
    source=Path('results',suite,'analysis.json')
    if not source.exists():continue
    result=json.loads(source.read_text())
    if not result.get('complete'):continue
    output=source.parent/'figures';output.mkdir(exist_ok=True)
    def save(fig,name):
        fig.savefig(output/(name+'.pdf'),bbox_inches='tight')
        fig.savefig(output/(name+'.png'),dpi=180,bbox_inches='tight');plt.close(fig)
    for name,ids,title in [('repetition',['H1_exact','H1_paraphrase'],'Paired repetition effects'),
                           ('hierarchy',['H3'],'Hierarchy interaction in repetition effects')]:
        data=[r for r in result['contrasts'] if r['kind']=='schedule' and r['contrast'] in ids and r['estimate'] is not None]
        fig,ax=plt.subplots(figsize=(6.2,max(2.3,.32*len(data)+1.0)),layout='constrained')
        labels=[]
        for i,r in enumerate(data):
            condition=r['contrast'].removeprefix('H1_')
            color=colors.get(condition,'#2369a0')
            ax.errorbar(100*r['estimate'],i,xerr=[[100*max(0,r['estimate']-r['lower'])],[100*max(0,r['upper']-r['estimate'])]],
                        fmt='o',capsize=3,color=color)
            labels.append(names.get(r['model'],r['model'])+(' / '+condition if name=='repetition' else '')+(' *' if r['degenerate_bootstrap'] else ''))
        ax.set_yticks(range(len(data)),labels);ax.invert_yaxis();ax.axvline(0,color='#777777',lw=.8)
        ax.set_xlabel('Error-rate difference (percentage points), 95% cluster interval')
        ax.set_title(title);ax.grid(axis='x',alpha=.15);save(fig,name)
    data=[r for r in result['summary'] if r['kind']=='schedule' and r['organization']=='hierarchical']
    groups=sorted({(r['model'],r['policy']) for r in data});conditions=['single','exact','paraphrase']
    matrix=np.array([[next(r['changed_scope_retention_on_consequential_pairs'] for r in data if
                          (r['model'],r['policy'],r['condition'])==(m,p,c)) for c in conditions] for m,p in groups])
    fig,ax=plt.subplots(figsize=(6.2,max(2.8,.38*len(groups)+1.0)),layout='constrained')
    im=ax.imshow(matrix,vmin=0,vmax=1,cmap='Blues',aspect='auto')
    ax.set_xticks(range(3),['Single','Exact copies','Paraphrases'])
    ax.set_yticks(range(len(groups)),[names.get(m,m)+' / '+p for m,p in groups])
    for (i,j),value in np.ndenumerate(matrix):
        ax.text(j,i,f'{100*value:.1f}%',ha='center',va='center',color='white' if value>.55 else 'black',fontsize=10)
    ax.set_title('Explicit changed-scope retention on consequential pairs')
    fig.colorbar(im,ax=ax,fraction=.035,pad=.03,label='Retained fraction');save(fig,'retention')
    data=[r for r in result['summary'] if r['kind']=='schedule'];models=sorted({r['model'] for r in data})
    fig,axes=plt.subplots(1,len(models),figsize=(6.2,3.0),squeeze=False,sharey=True,layout='constrained')
    policy_colors={'ordinary':'#2369a0','checklist':'#c06e19','scope':'#32854a'}
    for ax,model in zip(axes[0],models):
        cells=defaultdict(list)
        for r in data:
            if r['model']==model:cells[(r['organization'],r['policy'])].append(r)
        for (org,policy),rows in sorted(cells.items()):
            n=sum(r['n'] for r in rows)
            tokens=sum(r['n']*(r['input_tokens_per_decision']+r['output_tokens_per_decision']) for r in rows)/n
            accuracy=sum(r['correct'] for r in rows)/n
            ax.scatter(tokens/1000,100*accuracy,s=55,color=policy_colors[policy],marker='o' if org=='flat' else '^',label=org+' / '+policy)
        ax.set_title(names.get(model,model));ax.set_xlabel('Total tokens per decision (thousands)');ax.grid(alpha=.15)
    axes[0,0].set_ylabel('Decision accuracy (%)')
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='outside lower center',ncol=3,fontsize=8)
    save(fig,'resource')
    (output/'sources.json').write_text(json.dumps({'suite':suite,'population':'primary scheduling',
        'analysis_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'plot_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'inference':'No new tests; displays the existing prespecified contrasts and descriptive resource summaries.'},indent=2)+'\n')
