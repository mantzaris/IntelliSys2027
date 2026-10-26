"""Publication figures from explicit saved sufficient tables; no imputed results."""
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .common import *
COLORS={'C3':'#385b83','C5':'#b3542b','A1':'#50856a'}
def save(fig,name):
 out=HERE/'figures';out.mkdir(exist_ok=True)
 fig.savefig(out/(name+'.pdf'),bbox_inches='tight');fig.savefig(out/(name+'.png'),dpi=180,bbox_inches='tight');plt.close(fig)
def main():
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
 with (HERE/'tables/CHANNELS_AND_CHANGES.csv').open() as f:rows=list(csv.DictReader(f))
 fig,ax=plt.subplots(figsize=(5.2,3.5));keys=['edit','recollect','propose','peer_component','peer_answerer','other'];x=np.arange(len(keys));width=.24
 for n,c in enumerate(['C3','C5','A1']):
  vals=[];nums=[]
  for kind in keys:
   names=['channel_'+kind] if kind!='other' else ['channel_pass','channel_malformed','channel_unknown','channel_peer_invalid_recipient'];num=sum(int(r['numerator']) for r in rows if r['condition']==c and r['seed']=='all' and r['metric'] in names);nums.append(num);vals.append(100*num/10800)
  bars=ax.barh(x+(n-1)*width,vals,width,color=COLORS[c],label=c)
  for b,k in zip(bars,nums):ax.text(b.get_width()+.7,b.get_y()+b.get_height()/2,str(k),va='center',fontsize=7.5)
 ax.set_yticks(x,['Edit','Recollect','Propose','Peer → component','Peer → answerer','Pass / invalid']);ax.invert_yaxis();ax.set_xlabel('% of all allocated opportunities');ax.set_xlim(0,65);ax.legend(frameon=False,ncol=3,loc='lower right');fig.tight_layout();save(fig,'channels')
 core=read(HERE/'tables/CORE_CONTRASTS.json');fig,ax=plt.subplots(figsize=(6.6,2.7));labels=[]
 for y,(m,c) in enumerate([(m,c) for m in ['qwen','phi'] for c in ['C3','C1']]):
  r=next(r for r in core if r['model']==m and r['comparison']=='C5-'+c);v=100*r['difference'];lo,hi=np.array(r['ci95'])*100;ax.errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt='o',color=COLORS['C5'],capsize=3);labels.append(m.capitalize()+' C5 − '+c);ax.text(hi+.6,y,f'{v:+.2f} [{lo:+.2f}, {hi:+.2f}]',va='center',fontsize=8)
 ax.set_yticks(range(4),labels);ax.axvline(0,color='gray',lw=.8);ax.set_xlim(-12,35);ax.set_xlabel('Paired task-success difference (percentage points)');ax.set_title('Antagonists removed; 240 families × 3 training seeds');ax.invert_yaxis();fig.tight_layout();save(fig,'core_contrasts')
 if (HERE/'reports/HOLDOUT_CALIBRATION.json').exists():
  cal=read(HERE/'reports/HOLDOUT_CALIBRATION.json');dims=['recommendation','authorization_assertion','evidence_challenge','acknowledges_user_conflict','recipient_acknowledgment'];names=['Recommendation','User authorization','Evidence challenge','User-conflict recognition','Recipient acknowledgment'];fig,ax=plt.subplots(figsize=(6.6,2.8));x=np.arange(5)
  for j,m in enumerate(['phi','qwen']):
   vals=[next(r['balanced_accuracy_abstention_as_failure'] for r in cal if r['model']==m and r['dimension']==d) for d in dims];ax.barh(x+(j-.5)*.32,vals,height=.32,label=m.capitalize(),color=['#385b83','#b3542b'][j])
  ax.axvline(.85,ls='--',color='gray',label='Screen threshold');ax.set_yticks(x,names);ax.set_xlim(0,1);ax.invert_yaxis();ax.set_xlabel('Balanced accuracy; abstentions count as errors');ax.legend(frameon=False,ncol=3,fontsize=8,loc='lower left',bbox_to_anchor=(0,1.02));fig.tight_layout();save(fig,'calibration')
 if (HERE/'tables/SEMANTIC_RATES.json').exists():
  rates=read(HERE/'tables/SEMANTIC_RATES.json');fig,axs=plt.subplots(1,2,figsize=(6.6,2.8),sharey=True)
  for ax,stratum in zip(axs,['direct','communication']):
   for j,m in enumerate(['phi','qwen']):
    vals=[]
    for c in ['C3','C5','A1']:
     r=next(r for r in rates if r['population']=='broad' and r['model']==m and r['condition']==c and r['stratum']==stratum and r['dimension']=='authorization_assertion');vals.append(100*r['yes']/r['planned'])
    ax.bar(np.arange(3)+(j-.5)*.3,vals,.3,label=m.capitalize(),color=['#385b83','#b3542b'][j])
   ax.set_xticks(range(3),['C3','C5','A1']);ax.set_title(stratum.capitalize());ax.set_ylim(0,100)
  axs[0].set_ylabel('Positive classifications (%)');axs[1].legend(frameon=False);fig.suptitle('Authorization labels: unvalidated natural-dialogue measurements',fontsize=9);fig.tight_layout();save(fig,'semantic_authorization')
 control=read(HERE/'tables/COMPATIBILITY_COUNTS.json');fig,axs=plt.subplots(1,2,figsize=(6.6,2.4));z=[next(r for r in control if r['arm']==a and r['world']=='all') for a in ['compatible','incompatible']]
 for ax,key,den,label in [(axs[0],'successes',32,'Conversation task success'),(axs[1],'preferred_option_adoption',384,'Preferred value in following plan')]:
  vals=[r[key] for r in z];ax.bar([0,1],[100*v/den for v in vals],color=['#385b83','#b3542b']);ax.set_xticks([0,1],['Compatible','Incompatible']);ax.set_ylim(0,100);ax.set_title(label,fontsize=9);ax.set_ylabel('%');
  for i,v in enumerate(vals):ax.text(i,100*v/den+2,f'{v}/{den}',ha='center')
 fig.tight_layout();save(fig,'compatibility')
 write(HERE/'figures/CAPTIONS.json',{'channels':'Frozen Qwen common-base round zero, seeds17/29/43; 150 unique paired families,900episodes and10800allocated opportunities/condition. Bar labels are counts. Malformed/rejected actions are not removed; omitted kinds, if any, remain in complete table. No intervals shown for dependent raw counts.','core_contrasts':'Original paired endpoint,240families×3trainingseeds/model; frozen two-way family/seed95%percentile bootstrap. Three seeds limit variability inference.','calibration':'80heldout syntheticcontrols per model; primary binary support excludes expected uncertain/NA only as predeclared. Screen also requires coverage≥.80. Natural-dialogue validity is not established.','semantic_authorization':'15hash-selected families×2worlds×3generatorseeds=90opportunities/condition/stratum/model. Missing/uncertain remain in denominator and are separately tabulated. Classifications are not deterministic truth.','compatibility':'16pairedfamilies,32conversations/arm;384scheduled actoropportunities/arm. Descriptive counts. Paired both-world success5/16vs7/16; family95%interval for incompatible-minus-compatible difference−12.5to37.5pp. This is not a delivery intervention.'})
 print('Figures regenerated from measured tables')
if __name__=='__main__':main()
