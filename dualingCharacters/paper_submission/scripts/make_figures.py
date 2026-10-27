"""Regenerate the four paper figures from the bundled frozen numerical snapshot."""
from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,Patch
P=Path(__file__).resolve().parents[1];D=P/'data';F=P/'figures';F.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,'axes.labelsize':9,'xtick.labelsize':9,'ytick.labelsize':9,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
C={'C3':'#416C9A','C5':'#A85626','A1':'#267B65'};kindcols=['#855BA5','#DA8B36','#337AA1','#82B5AC','#D6D8DA']
read=lambda n:json.loads((D/n).read_text())
def save(fig,n):
 fig.savefig(F/(n+'.pdf'),bbox_inches='tight',metadata={'Creator':'Scientific figure script','CreationDate':None});fig.savefig(F/(n+'.png'),dpi=180,bbox_inches='tight');plt.close(fig)
def box(ax,x,y,w,h,text,color='#EFF3F6'):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.02,rounding_size=.05',fc=color,ec='#455361',lw=1));ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=9)
def arr(ax,a,b,label='',style='-'):
 ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','lw':1.1,'color':'#44515E','linestyle':style});
 if label:ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+.08,label,ha='center',fontsize=9,backgroundcolor='white')
fig,ax=plt.subplots(figsize=(6.3,3.6));ax.set(xlim=(0,10),ylim=(0,5.6));ax.axis('off')
box(ax,2.4,4.5,5.2,.8,'Immutable user / assistant transcript\nSource IDs and authors remain fixed')
box(ax,.15,2.2,2.8,1.45,'Two actors\nRole instructions\nHistory + inbox')
box(ax,3.6,2.2,2.8,1.45,'Working memory\n6 values + evidence\n4 unverified notes')
box(ax,7.05,2.2,2.8,1.45,'Answerer\nSources + memory\nPlan + questions')
arr(ax,(2.7,4.5),(1.55,3.65),'retrieval');arr(ax,(7.3,4.5),(8.45,3.65),'retrieval');arr(ax,(2.98,2.9),(3.58,2.9));arr(ax,(6.42,2.9),(7.03,2.9));arr(ax,(8.45,2.2),(6.15,2.2),'writes state')
ax.text(1.55,1.81,'Peer messages within cast',ha='center',fontsize=9)
ax.text(5.2,1.5,'Edit: state    Recollect / propose: notes',ha='center',fontsize=9)
box(ax,.15,.25,3.35,.95,'Private oracle\nCurrent authorization','#F9EEEE')
box(ax,6.1,.25,3.75,.95,'Score plan vs. oracle\nNo policy feedback','#F9EEEE')
arr(ax,(3.53,.72),(6.05,.72),'evaluation only','--');arr(ax,(8.45,2.2),(8.45,1.22),style='--')
ax.text(5,5.48,'Same frozen backbone, separate role contexts',ha='center',weight='bold')
save(fig,'system')

archive=list(csv.DictReader((D/'archive_channels.csv').open()));metrics=list(csv.DictReader((D/'archive_counts.csv').open()));edge=read('edge_summary.json')
fig,axes=plt.subplots(2,3,figsize=(6.7,4.8),gridspec_kw={'height_ratios':[1.25,1]});titles=['Original Qwen archive\n150 families; 3 seeds','Fresh contexts: Qwen\n16 families; 1 seed','Fresh contexts: Phi\n16 families; 1 seed']
plotdata=[]
for col,title in enumerate(titles):
 ax=axes[0,col];bp=axes[1,col]
 for y,c in enumerate(['C3','C5','A1']):
  if col==0:
   rows=[r for r in archive if r['condition']==c and r['seed'] in ['17','29','43']]
   sums={m:sum(int(r['numerator']) for r in rows if r['metric']==m) for m in set(r['metric'] for r in rows)}
   nums=[sums.get('channel_'+k,0) for k in ['edit','recollect','propose']];nums += [sum(v for m,v in sums.items() if m.startswith('channel_peer')),sums.get('channel_pass',0)+sums.get('channel_malformed',0)+sums.get('channel_unknown',0)]
   denom=10800;rr=[r for r in metrics if r['condition']==c and r['generator_seed'] in ['17','29','43'] and r['metric']=='consecutive_direct_goal_repetition'];rn=sum(int(r['numerator']) for r in rr);rd=sum(int(r['denominator']) for r in rr)
  else:
   r=next(r for r in edge if r['model']==('qwen' if col==1 else 'phi') and r['condition']==c);nums=[r[k] for k in ['edit','recollect','propose','peer','pass']];denom=r['opportunities'];rn,rd=r['repeat_n'],r['repeat_d']
  assert sum(nums)==denom
  left=0
  for n,co in zip(nums,kindcols):
   ax.barh(y,100*n/denom,left=left,color=co,height=.65);left+=100*n/denom
  bp.barh(y,100*rn/rd,color=C[c],height=.58);bp.text(1,y,f'{rn:,}/{rd:,}',va='center',ha='left',color='white',fontsize=9)
  plotdata.append({'population':title,'condition':c,'channels':nums,'opportunities':denom,'repeat':rn,'eligible_transitions':rd})
 ax.set(title=title,xlim=(0,100),yticks=range(3),yticklabels=['C3','C5','A1'],xlabel='Allocated\nopportunities (%)');ax.invert_yaxis()
 bp.set(xlim=(0,102),yticks=range(3),yticklabels=['C3','C5','A1'],xlabel='Typed-goal repetition (%)');bp.invert_yaxis()
 ax.text(.5,-.52,('n = 10,800' if col==0 else 'n = 384'),ha='center',transform=ax.transAxes,fontsize=9)
fig.legend([Patch(fc=c) for c in kindcols],['Edit','Recollect','Propose','Peer','Pass / invalid'],loc='upper center',bbox_to_anchor=(.5,.99),ncol=5,frameon=False,fontsize=9)
fig.subplots_adjust(top=.81,bottom=.16,hspace=.85,wspace=.35)
fig.text(.5,.025,'Phi reserved slots not applied: C3 23/128; C5 64/128; A1 88/128.\nBars retain all allocated opportunities. Lower panels use eligible direct transitions.',ha='center',fontsize=9)
save(fig,'channels_persistence');(D/'figure2_values.json').write_text(json.dumps(plotdata,indent=2)+'\n')

tr=read('ambiguity_trajectory.json');fig,axes=plt.subplots(2,1,figsize=(6.3,3.5),sharex=True,gridspec_kw={'height_ratios':[.65,2.2]});a,b=axes
for start,end,label,color in [(1,9,'3000 approved','#D5E6DE'),(10,19,'Unresolved\nNull plan + question required','#F4D6BC'),(20,32,'3000 explicitly resolved','#D5E6DE')]:
 a.axvspan(start-.5,end+.5,color=color);a.text((start+end)/2,.5,label,ha='center',va='center',fontsize=9)
a.set(ylim=(0,1),yticks=[]);a.spines[['left','bottom']].set_visible(False)
labels=[]
for y,(m,c) in enumerate((m,c) for m in ['qwen','phi'] for c in ['C3','C5','A1']):
 rr=sorted([r for r in tr if r['model']==m and r['condition']==c],key=lambda x:x['turn']);labels.append(m.title()+' '+c)
 for r in rr:
  premature=r['expected_cap'] is None and r['executable_cap'] is not None
  correct=r['executable_cap']==r['expected_cap'];co='#C66D36' if premature else ('#337F70' if correct else '#754E86')
  b.barh(y,.95,left=r['turn']-.475,height=.72,color=co)
  if r['clarify_cap']:b.plot(r['turn'],y,'o',mfc='white',mec='#152E36',ms=3.4,zorder=4)
b.set(yticks=range(6),yticklabels=labels,xlim=(.5,32.5),xticks=[1,5,10,15,20,25,32],xlabel='User turn');b.invert_yaxis();b.spines['left'].set_visible(False)
fig.legend([Patch(fc='#337F70'),Patch(fc='#C66D36'),Patch(fc='#754E86'),plt.Line2D([],[],marker='o',mfc='white',color='none',mec='#152E36',markersize=4)],['Correct plan value','Premature commitment','Wrong settled value','Asks about budget'],loc='lower center',ncol=2,frameon=False,fontsize=9)
fig.subplots_adjust(left=.16,right=.99,top=.96,bottom=.24,hspace=.22);save(fig,'ambiguity_trajectory')

contr=read('core_contrasts.json');chosen=[next(r for r in contr if r['model']==m and r['comparison']==c) for m,c in [('qwen','C5-C3'),('qwen','C5-C1'),('qwen','C5-A1'),('phi','C5-C3'),('phi','C5-C1')]]
fig,ax=plt.subplots(figsize=(6.3,3.2));ax.axvline(0,color='#666',lw=.8)
for y,r in enumerate(chosen):
 v=100*r['difference'];lo,hi=[100*x for x in r['ci95']];color='#416C9A' if r['model']=='qwen' else '#A85626';ax.errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt='o',color=color,capsize=3,ms=5)
 for s,mk,dy in [('17','|',-.13),('29','|',0),('43','|',.13)]:ax.plot(100*r['per_seed'][s],y+dy,marker=mk,color=color,ms=7,alpha=.65)
 ax.text(23,y,f'{v:+.2f} [{lo:+.2f}, {hi:+.2f}]',ha='left',va='center',fontsize=9)
ax.set(yticks=range(5),yticklabels=[r['model'].title()+'  '+r['comparison'].replace('C5-','C5 minus ') for r in chosen],xlim=(-21,47),xlabel='Paired success difference (percentage points)');ax.invert_yaxis();ax.set_xticks([-20,-10,0,10,20]);ax.text(.02,1.04,'Dots: three-seed mean and 95% interval. Ticks: individual seeds.',transform=ax.transAxes,fontsize=9)
fig.subplots_adjust(left=.24,right=.99,top=.87,bottom=.2);save(fig,'trained_outcomes')
print('Generated four PDF figures and PNG previews from bundled data.')
