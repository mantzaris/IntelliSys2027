"""Deterministic lexical and task-representation audit; no semantic novelty claim."""
from collections import Counter
from pathlib import Path
import re
from pcc.environment import make_family,digest
from pcc.resources import sha256
from .common import ROOT,HERE,REPORTS,read,write
from .scenarios import SCENARIOS,ENGINEERING


def grams(text,n=8):
    tokens=re.findall(r'[a-z0-9]+',text.lower());return {tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1)}


def main():
    manifest=read(HERE/'dataset_manifest.json');old=set();old_messages=set();sources={}
    for split in ('pilot','train','validation','test','natural'):
        path=ROOT/f'data/manifests/{split}.json';sources[str(path.relative_to(ROOT))]=sha256(path)
        for row in read(path)['families']:
            number=int(row['id'].rsplit('-',1)[1])
            for scenario in make_family(split,number,row['horizon']):
                for m in scenario.source_messages():old_messages.add(m.text)
    for text in old_messages:old.update(grams(text))
    seen=set();items=[];all_shared=Counter()
    for entry in manifest['entries']:
        public=read(ROOT/entry['public_path'])
        for message in [public['prior_message'],*public['messages']]:
            if message['text'] in seen:continue
            seen.add(message['text']);g=grams(message['text']);shared=g&old;all_shared.update(shared)
            items.append({'text_sha256':digest(message['text']),'exact_existing_message':message['text'] in old_messages,
              'eight_grams':len(g),'shared_eight_grams':len(shared),'shared_fraction':len(shared)/len(g) if g else 0})
    master_ids={s['id'] for s in SCENARIOS};engineering_ids={s['id'] for s in ENGINEERING};assert not master_ids&engineering_ids
    result={'core_manifest_hashes':sources,'fresh_dataset_manifest_sha256':sha256(HERE/'dataset_manifest.json'),
      'unique_public_messages':len(items),'exact_existing_messages':sum(r['exact_existing_message'] for r in items),
      'messages_with_any_shared_eight_gram':sum(r['shared_eight_grams']>0 for r in items),'maximum_shared_eight_gram_fraction':max(r['shared_fraction'] for r in items),
      'shared_eight_grams':[{'text':' '.join(k),'new_message_count':v} for k,v in all_shared.most_common()],
      'engineering_scientific_id_overlap':0,'old_ontology_output_required':False,
      'qualification':'Exact/transcript and lexical checks do not prove semantic novelty. Both benchmarks deliberately share authorization-versus-proposal mechanisms. New outputs are substantive prose/artifacts across distinct work tasks, not six renamed categorical slots.',
      'source_sha256':sha256(Path(__file__))}
    write(REPORTS/'OVERLAP_AUDIT.json',result);print({k:result[k] for k in ['unique_public_messages','exact_existing_messages','messages_with_any_shared_eight_gram','engineering_scientific_id_overlap']})


if __name__=='__main__':main()
