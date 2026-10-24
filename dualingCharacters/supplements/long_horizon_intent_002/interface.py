"""Common natural-language interface. No oracle, authoring specification or ledger import."""
from dataclasses import dataclass
import json
from pcc.memory import retrieve
from .public import PublicMessage


@dataclass(frozen=True)
class InterfaceConfig:
    input_tokens:int=4096
    output_tokens:int=640
    memory_tokens:int=128
    retrieved_messages:int=8
    recent_messages:int=4
    batch_size:int=32


SYSTEM='''You are assisting a human operator with practical collaborative work. Apply the goals, priorities, constraints, permissions, and revisions supported by the supplied conversation. Source messages retain their original authors and indices. A stakeholder quote, an assistant proposal, a hypothetical, or a rejected option is not an operator decision. Accept explicit operator revisions and preserve unaffected commitments. Acknowledge real uncertainty with a targeted question while continuing work whose requirements are settled. Make useful progress on the current requested artifact; repeating preferences or refusing to act is not a substitute for doing the work.
Return one JSON object with exactly two string fields: "response" and "memory". In response, write the substantive answer or work product requested by the latest user message. In memory, write a compact note for your future self about the current goal, binding requirements, actual approvals, unresolved issues, and useful source indices. The memory note is fallible and should be checked against source messages. Keep memory within 128 tokens. Use the available evidence; do not invent approvals, missing facts, or completed external actions. No other components or private evaluator summaries are available.'''
SCHEMA={'type':'object','properties':{'response':{'type':'string'},'memory':{'type':'string'}},'required':['response','memory'],'additionalProperties':False}


def clip_memory(text,tokenizer,cfg=InterfaceConfig()):
    if not isinstance(text,str):return '',{'invalid_memory_type':True,'memory_tokens_before':0,'memory_tokens_after':0,'memory_clipped':False}
    ids=tokenizer.encode(text,add_special_tokens=False);clipped=len(ids)>cfg.memory_tokens
    value=tokenizer.decode(ids[:cfg.memory_tokens],skip_special_tokens=False) if clipped else text
    return value,{'invalid_memory_type':False,'memory_tokens_before':len(ids),'memory_tokens_after':len(tokenizer.encode(value,add_special_tokens=False)),'memory_clipped':clipped}


def observation(transcript:list[PublicMessage],memory:str,tokenizer,cfg=InterfaceConfig()):
    if not transcript or transcript[-1].author!='user':raise ValueError('Current request must be an actual user message')
    if len({m.index for m in transcript})!=len(transcript):raise ValueError('Duplicate immutable source index')
    latest=transcript[-1];retrieved=retrieve(transcript,latest.text,cfg.retrieved_messages)
    selected={m.index:m for m in retrieved+transcript[-cfg.recent_messages:]};selected[latest.index]=latest
    initial_ids=sorted(selected);dropped=[]
    def render():
        body={'memory':memory,'sources':[selected[k].public() for k in sorted(selected)],'current_request_index':latest.index}
        return [{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps(body,separators=(',',':'),ensure_ascii=False)}]
    while True:
        prompt=render();count=len(tokenizer.apply_chat_template(prompt,tokenize=True,add_generation_prompt=True))
        if count<=cfg.input_tokens:break
        choices=[k for k in sorted(selected) if k!=latest.index]
        if not choices:raise ValueError('Mandatory public request exceeds input budget; no silent truncation')
        key=choices[0];dropped.append(key);del selected[key]
    return prompt,{'selected_before_budget':initial_ids,'visible_source_indices':sorted(selected),'dropped_source_indices':dropped,
      'input_tokens':count,'source_messages':len(selected),'source_authors':{str(k):m.author for k,m in selected.items()},
      'input_budget':cfg.input_tokens,'retrieval_query':latest.text,'retrieval_uses_private_ledger':False}


def accept_output(result,tokenizer,cfg=InterfaceConfig()):
    parsed=result.get('parsed');valid=isinstance(parsed,dict) and set(parsed)=={'response','memory'} and all(isinstance(parsed[k],str) for k in ('response','memory'))
    # No regeneration, condition-specific repair or text filtering. Invalid output
    # stays visible as raw text, and its unavailable memory is explicitly empty.
    response=parsed['response'] if valid else result.get('raw','')
    memory,meta=clip_memory(parsed['memory'] if valid else None,tokenizer,cfg)
    return response,memory,{'interface_valid':valid,'generation_capped':bool(result.get('generation_capped')),**meta}
