"""Small deterministic illustration, separate from blinded human evaluation."""
from collections import defaultdict
import json
from pcc.resources import sha256
from supplements.review_001.common import rank
from .common import ROOT,OUT,CACHE,read,write


def main():
    path=CACHE/'qualitative_cases.json';cases=read(path,[]);chosen={}
    for case in cases:
        if case['contrast'] not in {'C5-C3','C5-C1'}:continue
        key=case['model'],case['seed'],case['contrast'],case['category']
        if key not in chosen or rank('overnight-qual-v1',f'{case["model"]}:{case["seed"]}:{case["contrast"]}:{case["category"]}:{case["family_id"]}')<rank('overnight-qual-v1',f'{case["model"]}:{case["seed"]}:{case["contrast"]}:{case["category"]}:{chosen[key]["family_id"]}'):
            chosen[key]=case
    text=['# Illustrative paired cases — not human validation\n',
      'Selection: the lowest SHA256-ranked family in each available paired transition category for C5−C3 and C5−C1, separately by model and seed. The declared tag is `overnight-qual-v1:model:seed:contrast:category:family_id`. Categories and their prevalence use all 240 families. Both worlds and both methods are retained. No example changes training, checkpoint selection or any test denominator. These selected cases are qualitative illustrations, not a new estimate of prevalence or a blinded rating packet.\n']
    if not chosen:text.append('Pending the first complete fixed C5 evaluation. No substitute condition or synthetic case is inserted.\n')
    selected=[]
    for key,case in sorted(chosen.items()):
        selected.append({k:v for k,v in case.items() if k!='observations'})
        text.append(f'## {case["model"]} seed {case["seed"]}: {case["contrast"]}, {case["category"]}, {case["family_id"]}\n\nCategory prevalence: {case["category_families"]}/240 paired families.\n')
        for world in ('authorized','hypothetical'):
            rows=[r for r in case['observations'] if r['world']==world];target=rows[0]['target']
            text.append(f'**{world} world.** Oracle executable target: `{json.dumps(target["plan"])}`; required clarification: `{target["clarify"]}`. The oracle appears here for analysis only.\n')
            text.append('| Method | Actual executable plan | Correct task | Overlapping flags |\n|---|---|---|---|')
            for row in rows:
                flags=', '.join(k for k,v in row['flags'].items() if v) or 'none'
                text.append(f'| {row["condition"]} | `{json.dumps(row["prediction"].get("plan"))}` | {row["success"]} | {flags} |')
            text.append('\nPublic dependency rules: `'+json.dumps(rows[0]['catalog']['rules'],sort_keys=True)+'`.\n')
            for row in rows:
                source_ids={m['index'] for m in row['visible_sources']}
                missing=sorted({i for i in target['evidence'] if i is not None and i not in source_ids})
                text.append(f'- Trace: `{row["source_run"]}/evaluation.jsonl[.gz]`, family `{case["family_id"]}`, world `{world}`, turn 64. Recalled state: `{json.dumps(row["prediction"].get("state"))}`. Canonical references absent from this prompt: `{missing}`.')
            text.append('')
    (OUT/'QUALITATIVE_APPENDIX.md').write_text('\n'.join(text)+'\n')
    write(OUT/'QUALITATIVE_SELECTION.json',{'selected':selected,'candidate_cache_sha256':sha256(path) if path.exists() else None,
      'classification':'Outcome-stratified deterministic illustration; separate from blinded human evaluation','worlds_preserved':True})


if __name__=='__main__':main()
