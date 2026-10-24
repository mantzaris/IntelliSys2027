"""Measured pipeline compute, separated from billed uptime and extra attempts."""
from collections import defaultdict
from pathlib import Path
from pcc.campaign import jobs, load_overrides, resolve_job
from pcc.freeze import verify_freeze
from pcc.eligibility import exclusions
from pcc.resources import sha256
from supplements.review_001.common import write_csv
from .common import ROOT,OUT,read,write
from .plots import plt,finish,COLORS


def main():
    queue=[resolve_job(j,load_overrides(ROOT)) for j in jobs(verify_freeze(ROOT)['plan'])]
    groups=defaultdict(list); source_paths=[]
    active=read(ROOT/'artifacts/campaign_state.json',{}).get('active_job',{}).get('id')
    for job in queue:
        if job['command'] not in {'collect','fit','evaluate'} or job['id']==active:continue
        path=ROOT/f'artifacts/runs/{job["id"]}/status.json';m=read(path,{})
        if m.get('status')!='completed':continue
        groups[job['model'],job['condition'],job['seed']].append((job,m));source_paths.append(path)
    invalid=exclusions(ROOT); extras=defaultdict(list);resolved={j['id'] for j in queue}
    for path in sorted((ROOT/'artifacts/runs').glob('main-*/status.json')):
        if path.parent.name in resolved:continue
        m=read(path,{});cfg=m.get('config',{})
        if not cfg:continue
        extras[cfg['model'],cfg['condition'],cfg['seed']].append({'run_id':path.parent.name,
          'reserved_seconds':m.get('gpu_reserved_seconds',0),'status':m.get('status'),
          'reason':invalid.get(path.parent.name,'Unscheduled attempt; excluded from eligible pipeline totals')})
        source_paths.append(path)
    outcomes={(r['model'],r['condition'],r['seed']):r for r in read(OUT/'per_seed_results.json')}
    bases={r['model']:r['paired_success'] for r in outcomes.values() if r['condition']=='base'}
    rows=[]
    for key,values in sorted(groups.items()):
        model,condition,seed=key;outcome=outcomes.get(key);trained=[(j,m) for j,m in values if j['command']!='evaluate']
        row={'model':model,'condition':condition,'seed':seed,'character_count':{'C4':2,'C5':3,'C6':5}.get(condition),
          'completed_pipeline_stages':len(trained),'planned_pipeline_stages':0 if condition=='base' else 4,
          'complete_main_evaluation':outcome is not None,
          'eligible_collection_seconds':sum(m['gpu_reserved_seconds'] for j,m in values if j['command']=='collect'),
          'eligible_training_seconds':sum(m['gpu_reserved_seconds'] for j,m in values if j['command']=='fit'),
          'eligible_evaluation_seconds':sum(m['gpu_reserved_seconds'] for j,m in values if j['command']=='evaluate'),
          'collection_input_tokens':sum(m.get('input_tokens',0) for j,m in values if j['command']=='collect'),
          'collection_output_tokens':sum(m.get('output_tokens',0) for j,m in values if j['command']=='collect'),
          'collection_model_calls':sum(m.get('model_calls',0) for j,m in values if j['command']=='collect'),
          'peak_reported_vram_bytes':max(m.get('peak_vram_bytes',0) for j,m in values),
          'paired_success':outcome['paired_success'] if outcome else None,
          'gain_over_shared_base':outcome['paired_success']-bases[model] if outcome else None,
          'other_attempt_reserved_seconds':sum(x['reserved_seconds'] for x in extras[key]),
          'other_attempts':extras[key],'eligible_run_ids':[j['id'] for j,m in values]}
        row['eligible_pipeline_seconds']=row['eligible_collection_seconds']+row['eligible_training_seconds'];rows.append(row)
    write(OUT/'compute_by_condition.json',rows);write_csv(OUT/'compute_by_condition.csv',rows)
    write(OUT/'compute_provenance.json',{'status_hashes':{str(p.relative_to(ROOT)):sha256(p) for p in source_paths},
      'exclusions_sha256':sha256(ROOT/'configs/run_exclusions.json'),'code_sha256':sha256(Path(__file__)),
      'qualification':'Completed eligible pipeline compute is separate from excluded/other attempts, which remain charged to the whole-study ledger. No FLOP or billed-cost equivalence is asserted.'})
    fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
    for ax,model in zip(axes,('qwen','phi')):
        selected=[r for r in rows if r['model']==model and r['condition']!='base' and r['complete_main_evaluation'] and r['completed_pipeline_stages']==4]
        for row in selected:
            x=row['eligible_pipeline_seconds']/3600;y=row['gain_over_shared_base']*100
            ax.scatter(x,y,color=COLORS[row['seed']],s=45)
            ax.annotate(f'{row["condition"]} s{row["seed"]}',(x,y),xytext=(5,6),textcoords='offset points',fontsize=8)
        if not selected:ax.text(.5,.5,'Trained evaluations pending',ha='center',transform=ax.transAxes)
        ax.axhline(0,color='#777',lw=.8);ax.set(title=model.upper(),xlabel='Eligible collection + fit reservation (GPU h)')
        ax.margins(.2);ax.set_xlim(left=0)
        if not selected:ax.set_xlim(0,1)
        ax.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('Paired success gain over shared base (pp)')
    caption='Actual completed condition/seed pipelines only, at 64 turns and 240 paired test families. Horizontal values include both eligible collections, both fixed fits and their model loads; evaluation time and other/excluded attempts are reported separately in the table, and all attempts count toward the study ceiling. Vertical values are descriptive point differences from the one shared untrained reference per architecture. No fitted trend, missing-seed error bars, FLOP matching, billed-uptime estimate or causal efficiency claim is implied.'
    manifest={};finish(fig,'gain_vs_compute',caption,[OUT/'compute_by_condition.json',OUT/'per_seed_results.json'],manifest)
    write(OUT/'COMPUTE_FIGURE_MANIFEST.json',manifest)
    (OUT/'COMPUTE.md').write_text('# Measured compute and descriptive gain\n\n'+caption+'\n\n[Table](compute_by_condition.csv) · [PDF](figures/gain_vs_compute.pdf) · [SVG](figures/gain_vs_compute.svg) · [PNG](figures/gain_vs_compute.png)\n')


if __name__=='__main__':main()
