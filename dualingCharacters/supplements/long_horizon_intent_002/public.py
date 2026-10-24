"""Allowlisted public inputs. This module has no private-ledger dependency."""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PublicMessage:
    index:int
    author:Literal['user','assistant']
    text:str

    def __post_init__(self):
        if self.author not in {'user','assistant'} or type(self.index) is not int or self.index<0 or not isinstance(self.text,str):
            raise ValueError('Invalid immutable public source')

    def public(self):return {'index':self.index,'author':self.author,'text':self.text}


@dataclass(frozen=True)
class PublicConversation:
    family_id:str
    domain:str
    world:str
    horizon:int
    prior_message:PublicMessage
    messages:tuple[PublicMessage,...]

    def __post_init__(self):
        if self.world not in {'authorized','hypothetical'} or self.horizon!=len(self.messages):raise ValueError('Invalid conversation metadata')
        if self.prior_message.author!='assistant' or self.prior_message.index!=0:raise ValueError('Invalid prior assistant source')
        if any(m.author!='user' or m.index!=2*i+1 for i,m in enumerate(self.messages)):raise ValueError('User source author/index changed')

    @classmethod
    def load(cls,record):
        allowed={'family_id','domain','world','horizon','prior_message','messages'}
        if set(record)!=allowed:raise ValueError('Public conversation contains unapproved fields')
        return cls(**{k:record[k] for k in ('family_id','domain','world','horizon')},
                   prior_message=PublicMessage(**record['prior_message']),messages=tuple(PublicMessage(**m) for m in record['messages']))
