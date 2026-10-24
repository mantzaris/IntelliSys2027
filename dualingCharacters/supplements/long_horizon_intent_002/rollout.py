"""Public-only natural-language rollout with one generated response per user turn."""
from dataclasses import dataclass,field
from pathlib import Path
from typing import Callable
from pcc.resources import append_json
from .public import PublicConversation,PublicMessage
from .interface import InterfaceConfig,SCHEMA,observation,accept_output


@dataclass
class Episode:
    public:PublicConversation
    transcript:list[PublicMessage]=field(default_factory=list)
    memory:str=''


def run(backbone,conversations:list[PublicConversation],output:Path,condition:str,seed:int,
        cfg=InterfaceConfig(),before_batch:Callable[[],None]=lambda:None):
    if any(not isinstance(c,PublicConversation) for c in conversations):raise TypeError('Only allowlisted PublicConversation inputs')
    if len({c.horizon for c in conversations})!=1:raise ValueError('Batch one horizon at a time')
    if len({(c.family_id,c.world,c.horizon) for c in conversations})!=len(conversations):raise ValueError('Duplicate public conversation')
    completed=[]
    for offset in range(0,len(conversations),cfg.batch_size):
        episodes=[Episode(c,[c.prior_message]) for c in conversations[offset:offset+cfg.batch_size]]
        for turn in range(1,episodes[0].public.horizon+1):
            before_batch();prompts=[];observations=[]
            for ep in episodes:
                ep.transcript.append(ep.public.messages[turn-1]);prompt,meta=observation(ep.transcript,ep.memory,backbone.tokenizer,cfg)
                prompts.append(prompt);observations.append(meta)
            generated=backbone.generate(prompts,max_new_tokens=cfg.output_tokens,sample=False,response_schema=SCHEMA)
            if len(generated)!=len(episodes):raise ValueError('Backend returned an incomplete batch')
            for ep,prompt,meta,result in zip(episodes,prompts,observations,generated):
                response,new_memory,validation=accept_output(result,backbone.tokenizer,cfg)
                row={'family_id':ep.public.family_id,'domain':ep.public.domain,'world':ep.public.world,'horizon':ep.public.horizon,
                  'turn':turn,'condition':condition,'seed':seed,'prompt':prompt,'observation':meta,'generation':result,
                  'memory_before':ep.memory,'memory_after':new_memory,'response':response,**validation}
                append_json(output,row);ep.memory=new_memory;ep.transcript.append(PublicMessage(turn*2,'assistant',response))
            before_batch()
        completed.extend({'family_id':ep.public.family_id,'world':ep.public.world,'horizon':ep.public.horizon,'turns':ep.public.horizon} for ep in episodes)
    return completed
