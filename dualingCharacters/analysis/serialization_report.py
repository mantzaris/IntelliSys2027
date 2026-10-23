"""Deterministic repair-pilot report; validity gates never require higher scores."""
from pathlib import Path
import json
import statistics
from pcc.analysis import paired_success,contrast
from pcc.resources import sha256
from pcc.study_analysis import write_csv


def regenerate(root: Path):
    rows=[];inputs={};effects=[];evaluations={}
    grammar=root/'artifacts/corrected_serialization_audit.json'
    if grammar.exists():
        report=json.loads(grammar.read_text());inputs[str(grammar.relative_to(root))]=sha256(grammar)
        (root/'reports/tables/corrected_serialization_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    for model,condition in [('qwen','C3'),('qwen','C5'),('phi','C5')]:
        stem=f'pilot-format2-{model}-{condition.lower()}'
        row={'model':model,'condition':condition,'fit_run':stem+'-fit','eval_run':stem+'-eval','status':'pending',
             'optimizer_steps':None,'training_input_tokens':None,'supervised_tokens':None,'adapter_changed':None,
             'paired_success':None,'families':None,'malformed_turns':None,'reserved_gpu_seconds':None}
        fit=root/'artifacts/runs'/(stem+'-fit');evaluation=root/'artifacts/runs'/(stem+'-eval')
        if (fit/'status.json').exists() and json.loads((fit/'status.json').read_text())['status']=='completed':
            train=json.loads((fit/'training/training_summary.json').read_text())
            assert train['completion_serialization']=='public_defender_schema_order_v1'
            assert train['adapter_changed'] and train['optimizer_steps']==32 and train['input_tokens']==131072
            weights=fit/'training/final/adapter_model.safetensors'
            assert sha256(weights)==train['final_checksums']['adapter_model.safetensors']
            row.update(optimizer_steps=train['optimizer_steps'],training_input_tokens=train['input_tokens'],supervised_tokens=train['supervised_tokens'],adapter_changed=True,status='fit_complete')
            for path in (fit/'status.json',fit/'training/training_summary.json',weights):inputs[str(path.relative_to(root))]=sha256(path)
        if (evaluation/'status.json').exists() and json.loads((evaluation/'status.json').read_text())['status']=='completed':
            from pcc.diagnostics import jsonlines,trace_path
            summary=evaluation/'evaluation_summary.json';data=json.loads(summary.read_text());pairs=paired_success(data)
            assert len(pairs)==16 and len(data)==32 and {r['horizon'] for r in data}=={32}
            trace=trace_path(evaluation/'evaluation.jsonl');turns=jsonlines(trace)
            assert len(turns)==1024
            malformed=sum(not r['generation']['parsed'] for r in turns)
            if any(not r['generation']['parsed'] and not r['generation']['generation_capped'] for r in turns):
                raise ValueError('Uncapped output violates the structured interface')
            meta=json.loads((evaluation/'status.json').read_text())
            assert meta['loaded_adapter_sha256']==train['final_checksums']['adapter_model.safetensors']
            row.update(paired_success=statistics.mean(pairs.values()),families=len(pairs),malformed_turns=malformed,status='completed',
                       reserved_gpu_seconds=meta['gpu_reserved_seconds']+json.loads((fit/'status.json').read_text())['gpu_reserved_seconds'])
            evaluations[model,condition]=data
            for path in (evaluation/'status.json',summary,trace):inputs[str(path.relative_to(root))]=sha256(path)
        rows.append(row)
    for model in ('qwen','phi'):
        name=f'pilot-format2-{model}-base';run=root/'artifacts/runs'/name
        row={'model':model,'condition':'base','fit_run':None,'eval_run':name,'status':'pending',
             'optimizer_steps':0,'training_input_tokens':0,'supervised_tokens':0,'adapter_changed':False,
             'paired_success':None,'families':None,'malformed_turns':None,'reserved_gpu_seconds':None}
        if (run/'status.json').exists() and json.loads((run/'status.json').read_text())['status']=='completed':
            from pcc.diagnostics import jsonlines,trace_path
            summary=run/'evaluation_summary.json';data=json.loads(summary.read_text());pairs=paired_success(data)
            assert len(pairs)==16 and len(data)==32 and {r['horizon'] for r in data}=={32}
            trace=trace_path(run/'evaluation.jsonl');turns=jsonlines(trace);assert len(turns)==1024
            row.update(status='completed',paired_success=statistics.mean(pairs.values()),families=len(pairs),
                       malformed_turns=sum(not r['generation']['parsed'] for r in turns),
                       reserved_gpu_seconds=json.loads((run/'status.json').read_text())['gpu_reserved_seconds'])
            evaluations[model,'base']=data
            for path in (run/'status.json',summary,trace):inputs[str(path.relative_to(root))]=sha256(path)
        rows.append(row)
    if all(('qwen',c) in evaluations for c in ('C3','C5')):
        effects.append({'comparison':'Qwen C5-C3','qualification':'Corrected engineering pilot; one seed, 16 families, 32 turns; not H1 confirmation',**contrast(evaluations['qwen','C5'],evaluations['qwen','C3'])})
    for model,condition in [('qwen','C3'),('qwen','C5'),('phi','C5')]:
        if (model,condition) in evaluations and (model,'base') in evaluations:
            effects.append({'comparison':f'{model} {condition}-base','qualification':'Matched current-source engineering before/after; one seed, 16 families, 32 turns',**contrast(evaluations[model,condition],evaluations[model,'base'])})
    out=root/'reports/tables';write_csv(out/'serialization_pilots.csv',rows)
    (out/'serialization_pilots.json').write_text(json.dumps(rows,indent=2)+'\n')
    (out/'serialization_pilot_contrasts.json').write_text(json.dumps(effects,indent=2)+'\n')
    inputs['analysis/serialization_report.py']=sha256(Path(__file__))
    (out/'serialization_pilot_trace.json').write_text(json.dumps(inputs,indent=2)+'\n')
    tex=[r'\begin{table}[ht]\centering',r'\caption{Corrected serialization pilots: 32 optimizer steps, one seed, 16 paired families at 32 turns; engineering validation only.}',r'\begin{tabular}{llrr}\toprule Model & Condition & Paired success & GPU min.\\\midrule']
    for row in rows:
        value='--' if row['paired_success'] is None else f"{row['paired_success']:.4f}"
        seconds='--' if row['reserved_gpu_seconds'] is None else f"{row['reserved_gpu_seconds']/60:.2f}"
        tex.append(f"{row['model']} & {row['condition']} & {value} & {seconds}\\\\")
    tex.extend([r'\bottomrule\end{tabular}\end{table}','Pilot gates require compatible interfaces, complete outputs and changed parameters; they do not require an accuracy gain.'])
    (root/'paper/generated_serialization_pilots.tex').write_text('\n'.join(tex)+'\n')
    print(json.dumps({'corrected_completed_pilots':sum(r['status']=='completed' for r in rows)}))
    return rows

if __name__=='__main__':regenerate(Path(__file__).resolve().parents[1])
