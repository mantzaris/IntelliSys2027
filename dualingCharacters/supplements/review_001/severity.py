"""Training-only matched input construction; no selection by attack success."""
import copy
import json
from pcc.characters import cast,apply_action
from pcc.memory import WorkingMemory
from pcc.evaluation import opportunities
from .common import ARTIFACTS,ROOT,read,write,rank,stable_rows,require_completed


def prepare():
    selected=sorted(sorted(range(150),key=lambda n:rank('review001-severity-v1',f'train-{n:04d}'))[:16])
    ids={f'train-{n:04d}' for n in selected};inputs={};actions={};prompts={}
    turns=[t for i,t in enumerate(sorted(opportunities(16,12))) if i%3!=0]
    chosen={turns[0],turns[-1]}
    for c in ('C1','C3','C5'):
        run,_=require_completed(f'main-qwen-{c.lower()}-17-r0-collect')
        if c=='C1':
            for row in stable_rows(run/'collection.jsonl',inputs):
                if row['family_id'] in ids and row['turn'] in chosen:prompts[row['family_id'],row['world'],row['turn']]=row['prompt']
        else:
            for row in stable_rows(run/'collection_characters.jsonl',inputs):
                if row['family_id'] in ids and row['turn'] in chosen:actions[c,row['family_id'],row['world'],row['turn']]=row
    result=[]
    for key,prompt in sorted(prompts.items()):
        for c in ('none','C3','C5'):
            modified=copy.deepcopy(prompt);action=None
            if c!='none':
                action=actions[(c,*key)];body=json.loads(modified[-1]['content']);memory=WorkingMemory()
                memory.state=copy.deepcopy(body['memory']['state']);memory.evidence=copy.deepcopy(body['memory']['evidence']);memory.notes=copy.deepcopy(body['memory']['notes'])
                actors=cast(c,key[0],17);actor=next(a for a in actors if a.alias==action['actor'])
                applied=apply_action(action,actor,actors,memory,c,6,False)
                body['memory']=memory.public();modified[-1]['content']=json.dumps(body,separators=(',',':'))
            result.append({'family_id':key[0],'world':key[1],'turn':key[2],'action_condition':c,'prompt':modified,'original_action':action})
    assert len(result)==16*2*2*3
    write(ARTIFACTS/'inputs/severity.json',result)
    write(ARTIFACTS/'inputs/severity_manifest.json',{'families':selected,'turns':sorted(chosen),'inputs':inputs,
          'qualification':'Fixed common C1 round-zero states. Existing actions may have been generated from different role states; replay estimates their effects at these common inputs, not a matched attack-generation curriculum.'})


if __name__=='__main__':prepare()
