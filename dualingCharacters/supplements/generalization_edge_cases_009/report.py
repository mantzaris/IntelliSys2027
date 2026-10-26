"""Readable summaries of the prospectively defined measurements; no semantic judge."""
from collections import defaultdict
import html
import numpy as np
from .common import *
from .analysis import interval,csvwrite,stream
from .scenarios import PATTERNS

def table(headers,rows):
 return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])
def pct(n,d):return f'{n}/{d} ({100*n/d:.1f}%)' if d else 'unavailable (0 eligible)'
def build(run_root=None):
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 plt.rcParams.update({'font.size':10,'svg.fonttype':'none','pdf.fonttype':42})
 episodes=read(HERE/'tables/episodes.json');families=read(HERE/'tables/families.json');contrasts=read(HERE/'tables/contrasts.json');allocation=read(HERE/'ALLOCATION.json');models=allocation['models'];conditions=['C3','C5','A1']
 summaries=[];case_rows=[];effects=[];strata=[]
 for model in models:
  for c in conditions:
   e=[x for x in episodes if x['model']==model and x['condition']==c];f=[x for x in families if x['model']==model and x['condition']==c]
   sums={key:sum(x[key] for x in e) for key in ['edit','recollect','propose','peer','pass','opportunities','direct_state_changes','note_changes','repeat_n','repeat_d','last8_correct','last8_denominator','full_plan_success','collateral_wrong','collateral_denominator','clarification_correct','clarification_denominator','component_deliveries','answerer_notes','cited_source_unavailable','final_decisive_source_visible','input_tokens','output_tokens']}
   summaries.append({'model':model,'condition':c,'episodes':len(e),'unique_families':len({x['family_id'] for x in e}),'paired_success':sum(x['paired_success'] for x in f),'paired_denominator':len(f),**sums,'never_wrong':sum(x['recovery_status']=='never_wrong' for x in e),'recovered':sum(x['recovery_status']=='recovered' for x in e),'unrecovered':sum(x['recovery_status']=='unrecovered' for x in e)})
   for p in PATTERNS:
    g=[x for x in f if x['pattern']==p];case_rows.append({'model':model,'condition':c,'pattern':p,'paired_success':sum(x['paired_success'] for x in g),'families':len(g)})
  for control in ['C3','A1']:
   for metric,denom in [('edit','opportunities'),('recollect','opportunities'),('propose','opportunities'),('direct_state_changes','opportunities'),('repeat_n','repeat_d')]:
    differences=[]
    for fid in sorted({x['family_id'] for x in families if x['model']==model}):
     groups={c:[r for r in families if r['model']==model and r['family_id']==fid and r['condition']==c] for c in ['C5',control]}
     rates={c:sum(x[metric] for x in rs)/sum(x[denom] for x in rs) if sum(x[denom] for x in rs) else None for c,rs in groups.items()}
     if all(v is not None for v in rates.values()):differences.append(rates['C5']-rates[control])
    effects.append({'model':model,'comparison':'C5-'+control,'metric':metric,'family_mean_difference':float(np.mean(differences)) if differences else None,'ci95':interval(differences),'families':len(differences),'denominator_definition':denom})
 run_root=Path(run_root) if run_root else ROOT/'artifacts/runs'
 # Direct/communication strata are prespecified; passes and invalids retain denominator.
 for job in allocation['jobs']:
  for c in job['conditions']:
   p=run_root/job['run_id']/(c+'_characters.jsonl')
   if not p.exists():continue
   aa=[r for _,r in stream(p)]
   for communication in [False,True]:
    a=[r for r in aa if r['communication_slot']==communication];strata.append({'model':job['model'],'seed':job['seed'],'condition':c,'stratum':'communication' if communication else 'direct','opportunities':len(a),**{k:sum(r['kind']==k for r in a) for k in ['edit','recollect','propose','peer','pass']},'malformed':sum(not r.get('generation',{}).get('parsed') for r in a),'not_applied':sum(not r['applied'] for r in a)})
 context_rows=[]
 for m in models:
  for c in conditions:
   for context in ['seed_bank','instrument']:
    ff=[r for r in families if r['model']==m and r['condition']==c and r['context']==context]
    context_rows.append({'model':m,'condition':c,'context':context,'paired_success':sum(r['paired_success'] for r in ff),'families':len(ff)})
 csvwrite(HERE/'tables/by_context.csv',context_rows)
 write(HERE/'tables/summary.json',summaries);csvwrite(HERE/'tables/summary.csv',summaries);csvwrite(HERE/'tables/by_pattern.csv',case_rows);write(HERE/'tables/behavior_contrasts.json',effects);csvwrite(HERE/'tables/opportunity_strata.csv',strata)
 lines=['# Fresh contexts and unusual cases: measured results',f"**{len(episodes)}/{allocation['planned_conversations']} conversations**; {len(set(x['family_id'] for x in episodes))} unique families; {', '.join(models)}; rollout seeds {allocation['seeds']}. Base models, no adapters, training or semantic judges. The planned tier was selected from development timing, not task outcomes.",'## Paired decisive-field success',table(['Backbone','Condition','Both worlds correct','Full-plan conversations correct','Final-eight decisive observations correct'],[[s['model'],s['condition'],pct(s['paired_success'],s['paired_denominator']),pct(s['full_plan_success'],s['episodes']),pct(s['last8_correct'],s['last8_denominator'])] for s in summaries]),'Paired success requires the final decisive field and its clarification status correct in both worlds. Full-plan success is the unchanged original score. They are different endpoints.',table(['Backbone','Contrast','Difference (pp)','95% family interval (pp)','Family-seed pairs'],[[c['model'],c['comparison'],f"{100*c['difference']:+.2f}" if c['difference'] is not None else 'pending',str([round(100*x,2) for x in c['interval95_family_bootstrap']]) if c['difference'] is not None else 'pending',c['family_seed_pairs']] for c in contrasts]),'Intervals resample whole paired families, preserving conditions/worlds/seeds. Only 16 families and one/two rollout seeds: no precise pattern-specific or training-seed inference. An interval spanning zero is not equivalence.','## Channels and persistence',table(['Backbone','Condition','Edits / opportunities','Recollections','Proposals','Peer','Pass','Repeated / eligible direct pairs','Immediate state changes'],[[s['model'],s['condition'],pct(s['edit'],s['opportunities']),str(s['recollect']),str(s['propose']),str(s['peer']),str(s['pass']),pct(s['repeat_n'],s['repeat_d']),pct(s['direct_state_changes'],s['opportunities'])] for s in summaries]),'Repetition is typed slot/value repetition within actor/episode between valid applied direct actions, not semantic tactic continuity. API recollect/propose both append unverified notes; direct state changes compare memory immediately before/after an intervention, before the answer.','## Case patterns',table(['Backbone','Pattern','C3 paired','C5 paired','A1 paired'],[[m,p]+[pct(next(r for r in case_rows if r['model']==m and r['pattern']==p and r['condition']==c)['paired_success'],next(r for r in case_rows if r['model']==m and r['pattern']==p and r['condition']==c)['families']) for c in conditions] for m in models for p in PATTERNS]),'Two families per pattern; counts are descriptive and no narrow pattern-level intervals are presented.','## Trajectory and limits',table(['Backbone','Condition','Never wrong after final decisive event','Three-observation recovery','Unrecovered','Collateral wrong / final 8 untouched fields','Clarification correct / post-event observations'],[[s['model'],s['condition'],s['never_wrong'],s['recovered'],s['unrecovered'],pct(s['collateral_wrong'],s['collateral_denominator']),pct(s['clarification_correct'],s['clarification_denominator'])] for s in summaries]),'Recovery is after an observed error, requiring three consecutive correct observations. It does not guarantee no later relapse; full trajectories are exported. Unrecovered latency is missing/censored, not zero. Never-wrong cases are not counted as recoveries. Pattern7 is ambiguous at10; only one world resolves at12, and both settle at20. Correct uncertainty is not failure.', 'This is new context and conversational composition within the old six-field schema. Each backbone governs both actors and answerer. No isolated generator-backbone effect, training benefit, broad real-world transfer, hidden intention or causal peer influence is established. Earlier negative trained C5−C3 effects and failed semantic screens remain unchanged.','[Eight matched dialogue groups](DIALOGUES.md) · [Protocol](PROTOCOL.md) · [Reproduction](REPRODUCE.md) · [Raw provenance](reports/RAW_PROVENANCE.json)']
 (HERE/'RESULTS.md').write_text('\n\n'.join(lines)+'\n')
 def save(fig,name):
  fig.tight_layout();fig.savefig(HERE/'figures'/f'{name}.svg');fig.savefig(HERE/'figures'/f'{name}.png',dpi=170);plt.close(fig)
 fig,axes=plt.subplots(1,len(models),figsize=(10,3.8),squeeze=False)
 for ax,m in zip(axes[0],models):
  ss=[next(s for s in summaries if s['model']==m and s['condition']==c) for c in conditions];values=[s['paired_success']/s['paired_denominator'] for s in ss];ax.bar(conditions,values,color=['#4e79a7','#e15759','#59a14f']);ax.set_ylim(0,1.12);ax.set_title(m+' · seed17 ·16 paired families');ax.set_ylabel('Final decisive-field paired success')
  for i,s in enumerate(ss):ax.text(i,values[i]+.025,f"{s['paired_success']}/{s['paired_denominator']}",ha='center')
 save(fig,'task_outcomes')
 fig,axes=plt.subplots(1,len(models),figsize=(11,4),squeeze=False)
 for ax,m in zip(axes[0],models):
  bottom=np.zeros(3)
  for kind,color in zip(['edit','recollect','propose','peer','pass'],['#e15759','#f28e2b','#59a14f','#4e79a7','#bab0ac']):
   vals=np.array([next(s for s in summaries if s['model']==m and s['condition']==c)[kind]/next(s for s in summaries if s['model']==m and s['condition']==c)['opportunities'] for c in conditions]);ax.bar(conditions,vals,bottom=bottom,label=kind,color=color);bottom+=vals
  ax.set_title(m+' ·384 allocated opportunities/condition');ax.set_ylabel('API action share');ax.set_ylim(0,1);ax.legend(ncol=3,fontsize=8,loc='upper center',bbox_to_anchor=(.5,-.12))
 save(fig,'action_channels')
 fig,axes=plt.subplots(len(models),2,figsize=(11,6.5),squeeze=False)
 for i,m in enumerate(models):
  for j,w in enumerate(['authorized','hypothetical']):
   ax=axes[i,j]
   for c,color in zip(conditions,['#4e79a7','#e15759','#59a14f']):
    ee=[e for e in episodes if e['model']==m and e['world']==w and e['condition']==c];v=[np.mean([int(e['trajectory'][t-1]) for e in ee]) for t in range(1,33)];ax.plot(range(1,33),v,label=c,color=color)
   ax.axvline(12,color='gray',ls='--');ax.axvline(20,color='gray',ls=':');ax.set_ylim(-.02,1.04);ax.set_title(m+' · '+w+' ·16 episodes/condition');ax.set_ylabel('Decisive-field correctness');ax.set_xlabel('User turn');ax.legend()
 save(fig,'trajectories')
 fig,axes=plt.subplots(1,len(models),figsize=(10,3.8),squeeze=False)
 for ax,m in zip(axes[0],models):
  ss=[next(s for s in summaries if s['model']==m and s['condition']==c) for c in conditions];vv=[s['repeat_n']/s['repeat_d'] if s['repeat_d'] else 0 for s in ss];ax.bar(conditions,vv,color=['#4e79a7','#e15759','#59a14f']);ax.set_ylim(0,1.13);ax.set_title(m+' · eligible actor-local direct pairs');ax.set_ylabel('Typed goal repetition')
  for i,s in enumerate(ss):ax.text(i,vv[i]+.02,f"{s['repeat_n']}/{s['repeat_d']}",ha='center')
 save(fig,'persistence')
if __name__=='__main__':
 import argparse;p=argparse.ArgumentParser();p.add_argument('--run-root');a=p.parse_args();build(a.run_root)
