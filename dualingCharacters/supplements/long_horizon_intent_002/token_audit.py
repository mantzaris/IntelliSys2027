"""Offline token/schedule feasibility. Public-prefix reference is not a model rollout."""
from collections import defaultdict
import hashlib
from transformers import AutoTokenizer
from pcc.resources import sha256
from .common import ROOT,HERE,REPORTS,read,write
from .public import PublicConversation
from .interface import observation,InterfaceConfig
from supplements.review_001.common import write_csv


def source_indices(value):
    if isinstance(value,dict):
        if 'message_index' in value and 'quote' in value:return {value['message_index']}
        return set().union(*(source_indices(v) for v in value.values())) if value else set()
    if isinstance(value,list):return set().union(*(source_indices(v) for v in value)) if value else set()
    return set()


def main():
    directory=ROOT/'artifacts/review_001/tokenizers/qwen'
    tokenizer=AutoTokenizer.from_pretrained(directory,local_files_only=True,trust_remote_code=False)
    template_hash=hashlib.sha256(tokenizer.chat_template.encode()).hexdigest()
    assert template_hash==read(ROOT/'artifacts/runs/base-qwen-eval/status.json')['chat_template_sha256']
    rows=[];entry_tokens=[];manifest=read(HERE/'dataset_manifest.json')
    for entry in manifest['entries']:
        public=PublicConversation.load(read(ROOT/entry['public_path']));private=read(ROOT/entry['ledger_path'])
        entry_tokens.append({**{k:entry[k] for k in ('family_id','world','horizon','collection')},
          'scripted_user_tokens':sum(len(tokenizer.encode(m.text,add_special_tokens=False)) for m in public.messages),
          'scripted_assistant_tokens':len(tokenizer.encode(public.prior_message.text,add_special_tokens=False))})
        for turn in entry['checkpoints']:
            transcript=[public.prior_message,*public.messages[:turn]]
            _,meta=observation(transcript,'',tokenizer)
            ledger=private['ledger'][turn-1]
            canonical=source_indices({k:ledger[k] for k in ('goal','deliverable','binding_constraints','ranked_priorities','approved_direction','side_requirement','unresolved','resolved_issue','task_facts')})
            visible=set(meta['visible_source_indices'])
            rows.append({**{k:entry[k] for k in ('family_id','world','horizon','collection')},'checkpoint_turn':turn,
              'public_prefix_input_tokens':meta['input_tokens'],'visible_source_indices':sorted(visible),
              'canonical_binding_source_indices':sorted(canonical),'canonical_sources_visible':len(canonical&visible),
              'canonical_sources_total':len(canonical),'all_canonical_sources_visible':canonical<=visible,
              'source_lags':{str(i):turn-(i+1)//2 for i in canonical},'dropped_by_budget':meta['dropped_source_indices']})
    write(REPORTS/'script_token_counts.json',entry_tokens);write_csv(REPORTS/'script_token_counts.csv',entry_tokens)
    write(REPORTS/'public_prefix_feasibility.json',rows)
    groups=[]
    for collection in ('scientific','engineering'):
        for horizon in (16,64,128):
            group=[r for r in rows if r['collection']==collection and r['horizon']==horizon]
            tokens=[r['scripted_user_tokens'] for r in entry_tokens if r['collection']==collection and r['horizon']==horizon]
            groups.append({'collection':collection,'horizon':horizon,'observations':len(group),
              'scripted_user_tokens_min':min(tokens),'scripted_user_tokens_max':max(tokens),
              'input_tokens_min':min(r['public_prefix_input_tokens'] for r in group),'input_tokens_max':max(r['public_prefix_input_tokens'] for r in group),
              'all_binding_sources_visible':sum(r['all_canonical_sources_visible'] for r in group),'budget_pruned_inputs':sum(bool(r['dropped_by_budget']) for r in group)})
    write(REPORTS/'TOKEN_FEASIBILITY.json',{'status':'offline_preflight_only','model_calls':0,'groups':groups,
      'tokenizer_hashes':{str(p.relative_to(ROOT)):sha256(p) for p in directory.iterdir() if p.is_file()},
      'template_sha256':template_hash,'interface':vars(InterfaceConfig()),'dataset_manifest_sha256':sha256(HERE/'dataset_manifest.json'),
      'qualification':'Actual pinned tokenizer; public-only source prefixes and empty memory. No model-generated prior responses. These counts are NOT actual rollout context, memory performance, or full-history inference. Ledger is consulted only after the public retriever chooses inputs, to characterize coverage. Real rollout token counts and coverage remain pending.'})
    print({'offline_observations':len(rows),'max_public_prefix_input_tokens':max(r['public_prefix_input_tokens'] for r in rows),'model_calls':0})


if __name__=='__main__':main()
