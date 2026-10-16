"""All development result numerals in the draft come from analysis outputs."""
import json
import re
from pathlib import Path

out=Path('manuscript/generated');out.mkdir(parents=True,exist_ok=True)
files=sorted(Path('results').glob('*/analysis.json'))
records=[(p,json.loads(p.read_text())) for p in files if 'interim' not in str(p)]
rows=[]
trace=[]
for p,result in records:
    if not result['complete'] or not result['suite'].startswith('competence'): continue
    by_model={r['model']:{} for r in result['competence']}
    for r in result['competence']:by_model[r['model']][r['kind']]=r
    for model, values in by_model.items():
        label={'qwen':'Qwen2.5-7B','qwen14':'Qwen2.5-14B','qwen3':'Qwen3-14B','mistral':'Mistral-7B','nemo':'Mistral-Nemo-12B'}[model]
        version=re.search(r'v\d+$',result['suite']).group()
        columns=[]
        for kind in ('schedule','workflow'):
            r=values[kind]
            columns.append(f"{round(r['accuracy']*r['n'])}/{r['n']} ({100*r['accuracy']:.1f})")
            trace.append({'source':str(p),'field':'competence','record':r})
        rows.append(' & '.join([label,version,*columns])+r'\\')
table='\\begin{table}[ht]\n\\centering\n\\caption{Completed development competence checks: correct/decisions (percent), ordinary, flat, single presentation. Repeated checks reuse development pairs.}\n\\label{tab:competence}\n\\small\n\\begin{tabular}{llrr}\n\\hline\nModel & Interface & Scheduling & Workflow\\\\\n\\hline\n'
table+='\n'.join(rows) if rows else '\\multicolumn{4}{c}{No complete competence run available at build time.}\\\\'
table+='\n\\hline\n\\end{tabular}\n\\end{table}\n'
(out/'competence.tex').write_text(table)
(out/'numerical_traceability.json').write_text(json.dumps(trace,indent=2)+'\n')
