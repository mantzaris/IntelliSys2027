"""Presentation of frozen metrics; no new population, endpoint or semantic judge."""
from collections import defaultdict,Counter
import csv
import json
import os
from .common import *

def rows(name):
    with (REPORTS/name).open() as f:return list(csv.DictReader(f))

def compact_counts(name,keys):
    grouped=Counter()
    for row in rows(name):grouped[tuple(row[k] for k in keys)]+=int(row['count'])
    return [dict(zip(keys,key),count=n) for key,n in sorted(grouped.items())]

def mean_rate(summary,cohort,condition,metric):
    selected=[r for r in summary if r['cohort']==cohort and r['condition']==condition and r['metric']==metric]
    n=sum(int(r['numerator']) for r in selected);d=sum(int(r['denominator']) for r in selected)
    return n,d,n/d if d else None

def run():
    verify_science();summary=rows('metric_summary.csv');contrasts=read(REPORTS/'matched_contrasts.json')
    primary=('channel_edit','channel_recollect','channel_propose','consecutive_direct_goal_repetition')
    keybase=['cohort','condition','seed']
    channel=[]
    for r in summary:
        if r['metric'].startswith('channel_') or r['metric'] in {'structurally_valid','applied','rejected','state_changed','notes_changed'}:
            channel.append(r)
    write_csv(REPORTS/'CHANNELS.csv',channel)
    groups={}
    for r in rows('action_flow.csv'):
        key=tuple(r[k] for k in keybase+['channel']);n=int(r['count'])
        out=groups.setdefault(key,dict(zip(keybase+['channel'],key),allocated_with_this_channel=0))
        out['allocated_with_this_channel']+=n
        for field in ('valid','applied','state_changed','evidence_changed','notes_changed'):
            for value in ('True','False',''):
                column=field+'_'+({'True':'yes','False':'no','':'missing'}[value]);out[column]=out.get(column,0)+(n if r[field]==value else 0)
        for value in ('same','different','unknown_value',''):
            column='following_adoption_'+(value or 'missing');out[column]=out.get(column,0)+(n if r['following_adoption']==value else 0)
    write_csv(REPORTS/'ACTION_CHAIN.csv',list(groups.values()))
    write_csv(REPORTS/'EVIDENCE.csv',compact_counts('evidence_relations.csv',keybase+['reference_class','reference_available','reference_exists_in_transcript','indexed_reference_author','value_current','current_value_inappropriate_citation']))
    write_csv(REPORTS/'PEER_RESPONSE.csv',compact_counts('peer_responses.csv',keybase+['recipient_type','delivered','visible','visibility_status','previous_response','next_response','next_same_slot_type','paired_reference_eligible']))
    context=compact_counts('event_responsiveness.csv',keybase+['event_kind','side','assigned_slot_relevant','alignment_change','event_value_endorsed','old_value_endorsed','owned_value_endorsed','insistence_after_revision'])
    for row in context:
        row['applicability']='fixed assigned option' if row['condition']!='C2' else 'random control: owned-goal/alignment fields not applicable; see Amendment003'
        if row['condition']=='C2':
            for field in ('assigned_slot_relevant','alignment_change','owned_value_endorsed','insistence_after_revision'):row[field]='not_applicable'
    write_csv(REPORTS/'CONTEXT.csv',context)
    persistence=[]
    for r in rows('actor_persistence.csv'):
        out={k:r[k] for k in keybase+['role','actor_index']}
        for k in ('actor_episodes','own_opportunities','unrestricted_opportunities','direct_actions','direct_pairs','repeated_goals','goal_runs','repeated_goal_runs','returns_after_other_goal','distinct_goals'):out[k]=int(r[k])
        out['repetition_rate']=out['repeated_goals']/out['direct_pairs'] if out['direct_pairs'] else None
        out['mean_longest_run_actions']=int(r['longest_run_direct_actions'])/out['actor_episodes']
        persistence.append(out)
    write_csv(REPORTS/'PERSISTENCE.csv',persistence)
    # Fixed display subset of the prespecified metrics; the full table remains available.
    display=[r for r in contrasts if r['metric'] in primary and r['cohort']=='main_round_zero']
    write_csv(REPORTS/'PRIMARY_DESCRIPTIVE_CONTRASTS.csv',display)
    values={}
    for c in ('C3','C5','A1'):
        values[c]={m:dict(zip(('numerator','denominator','pooled_rate'),mean_rate(summary,'main_round_zero',c,m))) for m in {r['metric'] for r in summary}}
    write(REPORTS/'DISPLAY_VALUES.json',{'population':'main round zero; 150 unique families repeated over seeds17/29/43, both worlds','conditions':values,
        'pointwise_intervals':'Matched family rates; one seed family bootstrap, combined independent family/observed-seed resampling. Not simultaneous; no formal significance claims.',
        'rare_conditional_stratum':'The across-seed insistence contrast has only two families with nonzero exposure in every seed. Its mechanically generated interval is not interpreted; report per-seed counts and exposure instead.'})
    make_figures(summary,contrasts)
    inputs=['metric_summary.csv','matched_contrasts.json','action_flow.csv','actor_persistence.csv','event_responsiveness.csv','evidence_relations.csv','peer_responses.csv']
    outputs=['CHANNELS.csv','ACTION_CHAIN.csv','EVIDENCE.csv','PEER_RESPONSE.csv','CONTEXT.csv','PERSISTENCE.csv','PRIMARY_DESCRIPTIVE_CONTRASTS.csv','DISPLAY_VALUES.json']
    write(REPORTS/'PRESENTATION_PROVENANCE.json',{'script_sha256':sha256(Path(__file__)),'inputs':{n:sha256(REPORTS/n) for n in inputs},'outputs':{n:sha256(REPORTS/n) for n in outputs}})

def make_figures(summary,contrasts):
    os.environ['MPLCONFIGDIR']=str(CACHE/'matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','svg.hashsalt':'behavior004','pdf.fonttype':42,'savefig.dpi':180})
    out=REPORTS/'figures';out.mkdir(exist_ok=True);captions={}
    colors={'C3':'#4063a1','C5':'#bc5d35','A1':'#3b8067'}
    def save(fig,name,caption):
        fig.tight_layout()
        for suffix in ('pdf','svg','png'):
            metadata={'Date':None} if suffix=='svg' else {'CreationDate':None,'ModDate':None} if suffix=='pdf' else None
            fig.savefig(out/(name+'.'+suffix),bbox_inches='tight',metadata=metadata)
            if suffix=='svg':
                path=out/(name+'.svg');path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
        plt.close(fig);captions[name]=caption
    conditions=('C3','C5','A1');channels=('edit','recollect','propose','peer_component','peer_answerer','pass','malformed','unknown','peer_invalid_recipient')
    palette=['#3d5f93','#d59039','#5b9279','#9a79b0','#c16c85','#aaa','#333','#ddd','#777']
    fig,axes=plt.subplots(1,3,figsize=(10,3.5),sharey=True)
    for ax,seed in zip(axes,(17,29,43)):
        bottom=np.zeros(3)
        for ch,color in zip(channels,palette):
            values=[next(float(r['pooled_rate']) for r in summary if r['cohort']=='main_round_zero' and r['condition']==c and r['seed']==str(seed) and r['metric']=='channel_'+ch)*100 for c in conditions]
            ax.bar(conditions,values,bottom=bottom,color=color,label=ch.replace('_',' '));bottom+=values
        ax.set_title('Generator seed '+str(seed));ax.set_ylim(0,100)
    axes[0].set_ylabel('% of all allocated opportunities')
    axes[-1].legend(bbox_to_anchor=(1.02,1),loc='upper left',fontsize=8)
    save(fig,'action_channels','Qwen base defender, round zero; 150 paired families per seed, 12 opportunities per world (3,600 per condition/seed). All generated channels retained, including invalid/malformed attempts. Descriptive stacked proportions; no action-independent error bars. Same common schedule, not equal total tokens.')
    fig,axes=plt.subplots(1,3,figsize=(10,3.2))
    metrics=[('consecutive_direct_goal_repetition','Repeated typed goal\n/ consecutive direct actions'),('same_goal_channel_change','API change\n/ repeated-goal pairs'),('owned_goal_insistence_after_revision','Owned-option endorsement\n/ opportunities after revision away')]
    for ax,(metric,title) in zip(axes,metrics):
        for i,c in enumerate(conditions):
            selected=sorted([r for r in summary if r['cohort']=='main_round_zero' and r['condition']==c and r['metric']==metric],key=lambda r:int(r['seed']))
            for j,r in enumerate(selected):ax.scatter(i+(j-1)*.13,float(r['pooled_rate'])*100,color=colors[c],marker=('o','s','^')[j],s=40)
        ax.set_xticks(range(3),conditions);ax.set_ylim(0,105);ax.set_title(title,fontsize=9)
    axes[0].set_ylabel('%; individual seeds 17 ○, 29 □, 43 △')
    save(fig,'goal_persistence','Qwen round-zero collections, same 150 paired families and seeds17/29/43. Points are pooled per-seed rates, no error bars. Denominators differ for direct pairs and update-alignment exposure; exact counts are in metric_summary.csv and CONTEXT.csv. API change is not validated semantic development. After-revision exposure depends on fixed assigned options, and is descriptive.')
    fig,axes=plt.subplots(1,2,figsize=(9.5,3.6))
    classes=('explicit_current_support','explicit_contradiction','explicit_superseded_support','assistant_reference','reference_unavailable')
    bottom=np.zeros(3)
    for ref,color in zip(classes,['#5b9279','#bd6352','#cda75e','#8c79ab','#777']):
        vals=[mean_rate(summary,'main_round_zero',c,'reference_'+ref)[2]*100 for c in conditions]
        axes[0].bar(conditions,vals,bottom=bottom,label=ref.replace('_',' '),color=color);bottom+=vals
    axes[0].bar(conditions,100-bottom,bottom=bottom,label='other / absent / untyped',color='#ddd')
    axes[0].set_ylabel('% of all allocated opportunities');axes[0].set_title('Reference relation to typed value')
    axes[0].legend(loc='upper left',bbox_to_anchor=(0,-.2),fontsize=7)
    for i,c in enumerate(conditions):
        for j,(metric,label) in enumerate([('peer_before_goal_match','Before message'),('peer_after_goal_match','Next opportunity')]):
            n,d,value=mean_rate(summary,'main_round_zero',c,metric)
            axes[1].bar(i+(j-.5)*.32,value*100,width=.3,color=colors[c],alpha=1 if j else .45)
            axes[1].text(i+(j-.5)*.32,value*100+.2,f'{n}/{d}',ha='center',fontsize=7,rotation=45)
    axes[1].set_xticks(range(3),conditions);axes[1].set_ylim(0,10);axes[1].set_ylabel('% typed goal match');axes[1].set_title('Pale: before; solid: after message')
    save(fig,'evidence_and_peer_response','Qwen round zero, all three seeds, 150 paired families. Left: structural reference categories, not semantic deception labels; unavailable means absent from the actor source list. Right: only delivered visible typed messages with both prior and next recipient opportunities; counts printed. This temporal reference is observational, not randomized; matching is not acknowledgment, influence or coalition formation.')
    fig,axes=plt.subplots(4,2,figsize=(8,9),sharex=True)
    labels=[('channel_edit','Direct edit'),('channel_recollect','Recollection'),('channel_propose','Proposal'),('consecutive_direct_goal_repetition','Typed goal repetition')]
    for row,(metric,label) in enumerate(labels):
        for col,control in enumerate(('C3','A1')):
            ax=axes[row,col]
            for i,seeds in enumerate(([17],[29],[43],[17,29,43])):
                r=next(r for r in contrasts if r['cohort']=='main_round_zero' and r['second']==control and r['metric']==metric and r['seeds']==seeds)
                value=r['difference']*100;lo=r['lower']*100;hi=r['upper']*100
                ax.errorbar(value,i,xerr=[[value-lo],[hi-value]],fmt='o',color='#222' if i==3 else colors['C5'],capsize=3)
            ax.axvline(0,color='#aaa',linewidth=.8);ax.set_yticks(range(4),['17','29','43','combined']);ax.invert_yaxis()
            ax.set_title(label+'; C5 − '+control,fontsize=9)
            if row==3:ax.set_xlabel('Percentage-point difference')
    save(fig,'cross_seed_contrasts','Qwen round-zero C5−C3 and C5−A1, 150 matched paired families. Points compare mean family rates, pooling worlds within each family. Bars: 95% pointwise intervals from10,000 paired-family resamples (one seed) or independent family/observed-seed resamples (combined), seed400041. No formal tests or simultaneous coverage claim; only three generator seeds. Differences are not improvement scores.')
    (out/'CAPTIONS.md').write_text('# Figure captions\n\n'+'\n\n'.join('## '+name+'\n\n'+caption for name,caption in captions.items())+'\n')
    write(REPORTS/'FIGURE_PROVENANCE.json',{'script_sha256':sha256(Path(__file__)),'inputs':{n:sha256(REPORTS/n) for n in ('metric_summary.csv','matched_contrasts.json')},'files':{p.name:sha256(p) for p in out.iterdir() if p.is_file()}})

if __name__=='__main__':run()
