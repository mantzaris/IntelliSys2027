"""Mechanical manuscript tables from saved aggregates; no new statistical tests."""
from pathlib import Path
import json
from pcc.resources import sha256


def regenerate(root: Path):
    inputs={}
    def read(name,default):
        path=root/'reports/tables'/name
        if not path.exists():return default
        inputs[str(path.relative_to(root))]=sha256(path)
        return json.loads(path.read_text())
    main=read('main_results.json',[]);effects=read('main_contrasts.json',[])
    transfer=read('transfer.json',[]);external=read('external.json',[])
    unseen=read('unseen_profiles.json',{'results':[]})['results']
    def number(value):return '--' if value is None else f'{value:.3f}'
    def save(name,caption,columns,header,rows,note):
        lines=[r'\begin{table}[ht]\centering\small',r'\caption{'+caption+'}',
               r'\begin{tabular}{'+columns+r'}\toprule',header+r'\\\midrule',
               *[' & '.join(map(str,row))+r'\\' for row in rows],r'\bottomrule\end{tabular}\end{table}',note]
        (root/'paper'/name).write_text('\n'.join(lines)+'\n')
    rows=[]
    for condition in ('C5','A1','A2','A3'):
        row=next((r for r in main if r['model']=='qwen' and r['condition']==condition),{})
        effect=next((r for r in effects if r['model']=='qwen' and r['contrast']=='C5-'+condition),{})
        interval='--' if not effect else f"{effect['difference']:+.3f} [{effect['ci95'][0]:+.3f}, {effect['ci95'][1]:+.3f}]"
        rows.append((condition,row.get('executed_seeds',0),number(row.get('paired_success')),interval,number(effect.get('holm_p_secondary'))))
    save('generated_ablations.tex','Qwen three-character ablations: antagonist-free paired success at 64 turns.','lrrlr',
         r'Condition & Seeds & Paired & C5 minus row [95\% CI] & Holm $p$',rows,
         'A1 uses explicit motives; A2 removes private history; A3 blocks peer delivery. Intervals are pointwise paired seed/family intervals; the displayed secondary p-values use the prespecified seven-comparison Holm family. Missing comparisons are pending, not zero effects.')
    rows=[]
    for condition in ('base','C1','C3','C4','C5'):
        values=[]
        for setting in ('horizon64-subset','larger-memory','unfamiliar'):
            candidates=[r for r in transfer if r['model']=='qwen' and r['condition']==condition and r['seed']==17 and r['setting']==setting]
            if len(candidates)>1:raise ValueError('Duplicate eligible publication cell')
            if candidates:assert candidates[0]['families']==48
            values.append(number(candidates[0]['paired_success']) if candidates else '--')
        candidates=[r for r in unseen if r['condition']==condition and r['seed']==17]
        if candidates and candidates[0]['status']=='completed':assert candidates[0]['families']==48
        profile='n/a' if condition=='C4' else number(candidates[0]['paired_success']) if candidates else '--'
        rows.append((condition,*values,profile))
    save('generated_transfer.tex','Qwen robustness references: paired success on the same 48 families at 64 turns, seed 17.','lrrrr',
         'Condition & No opponents & Larger memory & Cache faults & New profiles',rows,
         'The first three settings belong to the original fixed extensions. New profiles are a separately declared exploratory supplement with antagonists present and a remaining-budget gate. No C4 profile test was scheduled (n/a); dashes indicate unexecuted cells. These seed-17 references do not replace the full three-seed primary endpoint.')
    rows=[]
    for model in ('qwen','phi'):
        for condition in ('base','C1','C3','C5'):
            matches=[]
            for result in external:
                source=root/'artifacts/runs'/result['source_run']/'status.json'
                meta=json.loads(source.read_text());cfg=meta['config'];inputs[str(source.relative_to(root))]=sha256(source)
                if cfg['model']==model and cfg['condition']==condition:matches.append(result)
            if len(matches)>1:raise ValueError('Duplicate external publication cell')
            result=matches[0] if matches else {}
            if result:assert result['questions']==50
            flag='--' if not result else 'pass' if result['calibration_threshold_passed'] else 'fail'
            rows.append((model,condition,result.get('questions','--'),number(result.get('adapted_judge_accuracy')),flag))
    save('generated_external.tex','Fixed 50-question LongMemEval subset: adapted cross-family automatic scoring.','llrrl',
         'Generator & Condition & Questions & Judge accuracy & Calibration',rows,
         'These are exploratory adapted scores, not official comparable LongMemEval results. A calibration pass concerns 80 structured-planning examples and does not validate open-ended memory QA judging. A fail means the stated calibration threshold was not met. Human agreement and official scoring remain pending; missing scores are not zero.')
    rows=[]
    for condition,count in (('C4',2),('C5',3),('C6',5)):
        row=next((r for r in main if r['model']=='qwen' and r['condition']==condition),{})
        hours=None if not row.get('executed_seeds') else row.get('gpu_reserved_seconds',0)/3600
        rows.append((condition,count,row.get('executed_seeds',0),number(row.get('paired_success')),number(hours)))
    save('generated_character_compute.tex','Qwen character count and measured condition-level study cost.','lrrrr',
         'Condition & Characters & Seeds & Paired & GPU hours',rows,
         'Jekyll is included in the character count. Characters divide a common intervention and generation-token cap. Costs include all recorded attempts, collection, training and primary evaluation; they are realized project costs and do not isolate intrinsic algorithmic efficiency or exactly match FLOPs.')
    inputs['analysis/publication_tables.py']=sha256(Path(__file__))
    (root/'reports/tables/publication_tables_trace.json').write_text(json.dumps({'classification':'Post-baseline mechanical presentation of existing aggregates; no new estimators, tests or condition selection','inputs':inputs},indent=2)+'\n')
    print(json.dumps({'manuscript_tables_regenerated':4,'all_missing_cells_explicit':True}))

if __name__=='__main__':regenerate(Path(__file__).resolve().parents[1])
