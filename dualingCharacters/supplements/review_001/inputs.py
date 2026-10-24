"""Policy-input transformations with no oracle-dependent source selection."""
import copy
import json
from pcc.environment import make_family
from pcc.memory import WorkingMemory,observation
from .common import ROOT,ARTIFACTS,RESULTS,read,write,rank,stable_rows,require_completed,main_evaluation,record_source


def memory_variant(prompt,variant):
    result=copy.deepcopy(prompt)
    if variant=='A0':return result
    if variant not in {'A1','A2'}:raise ValueError(variant)
    body=json.loads(result[-1]['content'])
    body['memory']=WorkingMemory().public()
    if variant=='A2':body['sources']=[m for m in body['sources'] if m['author']!='assistant']
    assert any(m['index']==body['latest_user_index'] and m['author']=='user' for m in body['sources'])
    result[-1]['content']=json.dumps(body,separators=(',',':'))
    return result


def selected_families(count):
    if count%8 or not 0<count<=240:raise ValueError('Whole balanced domain/rule cells required')
    cells={}
    for n in range(240):
        s=make_family('test',n,64)[0];cells.setdefault((s.spec.domain,s.spec.online_override),[]).append(n)
    return sorted(n for group in cells.values() for n in sorted(group,key=lambda n:rank('review001-A-family-v1',f'test-{n:04d}'))[:count//8])


def collapsed_prompt(spec,original_user_messages):
    if any(m.author!='user' for m in original_user_messages):raise ValueError('Common input accepts immutable user messages only')
    # Exactly the original public query, eight lexical selections plus four recent
    # USER messages here, not four mixed transcript messages. No truth is consulted.
    return observation(spec,list(original_user_messages),WorkingMemory(),8,4)[0]


def prepare():
    inputs={};manifest={'classification':'Post-C1 exploratory inputs; no model calls','conditions':{},'selection_orders':{str(n):selected_families(n) for n in (16,32,64,120,240)}}
    output=ARTIFACTS/'inputs';output.mkdir(parents=True,exist_ok=True)
    for condition in ('C1','C3','C5'):
        name=main_evaluation(condition)
        status=ROOT/'artifacts/runs'/name/'status.json'
        if not status.exists() or read(status)['status']!='completed':
            manifest['conditions'][condition]={'status':'pending_fixed_prerequisite','run_id':name};continue
        run,meta=require_completed(name);record_source(inputs,status)
        assert meta['config']['seed']==17 and meta['model_revision']=='cdbee75f17c01a7cc42f958dc650907174af0554'
        finals=[row for row in stable_rows(run/'evaluation.jsonl',inputs) if row['turn']==64]
        assert len(finals)==480 and len({(r['family_id'],r['world']) for r in finals})==480
        records=[]
        for row in finals:
            for variant in ('A0','A1','A2'):
                prompt=memory_variant(row['prompt'],variant)
                records.append({'family_id':row['family_id'],'world':row['world'],'model_condition':condition,'variant':variant,
                                'prompt':prompt,'saved_answer':row['generation']['raw'],'saved_parsed':row['generation']['parsed'],
                                'saved_input_tokens':row['generation']['input_tokens'],'saved_adapter_sha256':meta['loaded_adapter_sha256']})
        path=output/f'memory-{condition}.json';write(path,records);record_source(inputs,path)
        manifest['conditions'][condition]={'status':'ready','run_id':name,'prompts':len(records),'adapter_sha256':meta['loaded_adapter_sha256']}
    common=[]
    for n in range(240):
        for scenario in make_family('test',n,64):
            common.append({'family_id':scenario.family_id,'world':scenario.world,'variant':'common-user-only',
                           'prompt':collapsed_prompt(scenario.spec,scenario.messages)})
    path=output/'common-user-only.json';write(path,common);record_source(inputs,path)
    manifest['inputs']=inputs;write(RESULTS/'input_manifest.json',manifest)
    print(json.dumps({'prerequisites':manifest['conditions'],'common_source_prompts':len(common)}))


if __name__=='__main__':prepare()
