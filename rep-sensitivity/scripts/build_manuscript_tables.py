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
    if not result.get('suite','').startswith('competence') or not result.get('complete'): continue
    by_model={r['model']:{} for r in result['competence']}
    for r in result['competence']:by_model[r['model']][r['kind']]=r
    for model, values in by_model.items():
        label={'qwen':'Qwen2.5-7B','qwen14':'Qwen2.5-14B','qwen3':'Qwen3-14B','mistral':'Mistral-7B','nemo':'Mistral-Nemo-12B','mistral24':'Mistral-Small-24B (INT8)','phi4':'Phi-4 (BF16)'}[model]
        version=re.search(r'v\d+$',result['suite']).group()
        columns=[]
        for kind in ('schedule','workflow'):
            r=values[kind]
            columns.append(f"{round(r['accuracy']*r['n'])}/{r['n']} ({100*r['accuracy']:.1f})")
            trace.append({'source':str(p),'field':'competence','record':r})
        rows.append(' & '.join([label,version,*columns])+r'\\')
table='\\begin{table}[ht]\n\\centering\n\\caption{Completed development checks: correct/decisions (percent), ordinary, flat, single presentation. Checks reuse development pairs. Historical Mistral-7B/Nemo rows reflect their original tokenizer interface and are not clean model rankings.}\n\\label{tab:competence}\n\\small\n\\begin{tabular}{llrr}\n\\hline\nModel & Interface & Scheduling & Workflow\\\\\n\\hline\n'
table+='\n'.join(rows) if rows else '\\multicolumn{4}{c}{No complete competence run available at build time.}\\\\'
table+='\n\\hline\n\\end{tabular}\n\\end{table}\n'
(out/'competence.tex').write_text(table)
pilot=next(((p,r) for p,r in records if r.get('suite')=='pilot-v7' and r.get('complete')),None)
if pilot:
    path,result=pilot
    table='\\begin{table}[ht]\n\\centering\n\\caption{Completed development pilot accuracy (percent); not a held-out hypothesis test. Each cell retains both worlds and both stochastic repetitions.}\n\\label{tab:pilot}\n\\small\n\\begin{tabular}{lllrrr}\n\\hline\nTask & Organization & Policy & Single & Exact & Paraphrase\\\\\n\\hline\n'
    for kind in ('schedule','workflow'):
        for organization in ('flat','hierarchical'):
            for policy in ('ordinary','checklist'):
                cells=[next(r for r in result['summary'] if (r['kind'],r['organization'],r['policy'],r['condition'])==(kind,organization,policy,condition))
                       for condition in ('single','exact','paraphrase')]
                table+=' & '.join([kind,organization,policy,*[f"{100*r['accuracy']:.1f}" for r in cells]])+r'\\'+'\n'
                for r in cells:trace.append({'source':str(path),'field':'summary','record':r})
    table+='\\hline\n\\end{tabular}\n\\end{table}\n'
    # The interpretation figure now combines absolute accuracy and paired
    # effects; preserve the original figures on disk without repeating them.
    for figure in ('hierarchy','resource'):
        table+='\\begin{figure}[ht]\n\\centering\n\\includegraphics[width=\\textwidth]{../results/pilot-v7/figures/'+figure+'.pdf}\n\\caption{Development-only primary scheduling: '+figure+'. Intervals, where shown, resample base-instance clusters.}\n\\label{fig:pilot-'+figure+'}\n\\end{figure}\n'
    (out/'pilot.tex').write_text(table)
    for r in result['contrasts']:trace.append({'source':str(path),'field':'contrasts','record':r})
(out/'numerical_traceability.json').write_text(json.dumps(trace,indent=2)+'\n')
