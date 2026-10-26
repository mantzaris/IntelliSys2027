"""Three descriptive figures, generated only from frozen numeric inputs and exact evidence."""
from .common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
COLORS={'C3':'#3e5c76','C5':'#aa6346','A1':'#48785b'}
def save(fig,name):
 for ext in ['svg','png','pdf']:fig.savefig(HERE/f'figures/{name}.{ext}',dpi=180,bbox_inches='tight',metadata={'Creator':'results_clarity_007'} if ext=='pdf' else None)
 plt.close(fig)
def run():
 rows=csv_read(HERE/'tables/CHANNELS_AND_CHANGES.csv');nums=csv_read(HERE/'tables/MECHANICAL_COUNTS.csv')
 def val(c,metric,seed='all'):return next(r for r in rows if r['condition']==c and r['metric']==metric and r['seed']==seed)
 plt.rcParams.update({'font.size':10,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
 channels=['edit','recollect','propose','peer_component','peer_answerer','pass','malformed','peer_invalid_recipient','unknown']
 labels=['Direct edit','Recollection label','Proposal label','Peer → component','Peer → answerer','Pass','Malformed','Invalid recipient','Unknown']
 fig,axes=plt.subplots(1,3,figsize=(12,4.4),sharey=True)
 for ax,c in zip(axes,['C3','C5','A1']):
  ns=[int(val(c,'channel_'+m)['numerator']) for m in channels];ax.barh(np.arange(len(ns)),np.array(ns)/108,color=COLORS[c]);ax.set_yticks(range(9),labels);ax.invert_yaxis();ax.set_xlim(0,59);ax.set_title(c);ax.set_xlabel('% of all 10,800 opportunities')
  for y,n in enumerate(ns):ax.text(n/108+.6,y,str(n),va='center',fontsize=9)
 fig.suptitle('Emitted action channels — counts, not semantic claim categories',y=1.04);fig.tight_layout();save(fig,'01_action_channels')
 fig,axes=plt.subplots(1,2,figsize=(10,4))
 for ax,metric,title in zip(axes,['consecutive_direct_goal_repetition','state_changed'],['Repeated typed goal among eligible adjacent direct actions','Immediate structured working-state change / all opportunities']):
  for i,c in enumerate(['C3','C5','A1']):
   pool=next(r for r in nums if r['condition']==c and r['generator_seed']=='all' and r['metric']==metric) if metric!='state_changed' else val(c,metric)
   n,d=int(pool['numerator']),int(pool['denominator']);ax.bar(i,100*n/d,color=COLORS[c],alpha=.75,width=.6);ax.text(i,100*n/d+2,f'{n:,}/{d:,}',ha='center',fontsize=9)
   for seed,offset in zip(['17','29','43'],[-.13,0,.13]):
    r=next(r for r in nums if r['condition']==c and r['generator_seed']==seed and r['metric']==metric) if metric!='state_changed' else val(c,metric,seed)
    ax.plot(i+offset,100*float(r['pooled_rate']),'o',mfc='white',mec='black',ms=4)
  ax.set_xticks(range(3),['C3','C5','A1']);ax.set_ylim(0,108);ax.set_ylabel('%');ax.set_title(title,fontsize=10,wrap=True)
 fig.text(.5,-.04,'Bars: pooled fractions. White dots: generator seeds 17, 29, 43; not uncertainty intervals.\n150 paired families repeated across seeds; fixed common-base defender; no causal severity comparison.',ha='center',fontsize=9);fig.tight_layout();save(fig,'03_persistence_and_state')
 fig,ax=plt.subplots(figsize=(10,4.8));ax.axis('off')
 layers=[('1  API action','peer; typed audience = specialists; source = 1'),('2  Textual propositions','“guest group is specialists” + criticism of Saturday\nOne supported audience assertion and a separate day objection.'),('3  Actual delivery','Sender/claim/slot/value/source reach Ellis’s inbox at turn 13.\nBoth the user’s Tuesday approval and this message are visible.'),('4  Observed continuation','Ellis repeats “The event day should be Saturday…”\nThe answerer’s structured plan retains Tuesday.')]
 for j,(title,text) in enumerate(layers):
  y=.87-j*.24;ax.text(.025,y,title,weight='bold',va='top',color='#213d52');ax.text(.30,y,text,va='top',fontsize=11);ax.axhline(y-.18,color='#ccd5dd',lw=.8)
 ax.text(.02,-.10,'DI5-a4c89ffad4 · C5 · turns 12–13. Ellipsis marks a shortened quotation.\nDelivery + continuation do not distinguish disagreement, nonresponse, or causal influence.',fontsize=10);save(fig,'02_four_layers')
 write(HERE/'figures/CAPTIONS.json',{'01_action_channels':'Common-base Qwen round-zero, C3/C5/A1, generator seeds17/29/43. Each condition:900episodes,150unique paired families,10800 allocated opportunities. Counts from CHANNELS_AND_CHANGES.csv; invalid generations retained; no uncertainty bars. API labels are not semantic categories.',
 '02_four_layers':'Selected C5 episode D5E-2fd1ee13eac3, DI5-a4c89ffad4, seed29, authorized world. Exact full quotations and record locators in reader edition. Illustration, not prevalence.',
 '03_persistence_and_state':'Common-base Qwen round-zero, same150paired families and three generator seeds. Pooled denominators printed; per-seed dots. Repetition excludes pairs without eligible direct typed goals as defined by frozen004, while state-change denominator retains all opportunities. Different denominators; no shared composite score.'})
if __name__=='__main__':run()
