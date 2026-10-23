"""CPU-only integration gate against the installed inference grammar."""
from pathlib import Path
import json
from importlib.metadata import version
import xgrammar
from xgrammar.testing import _is_grammar_accept_string
from pcc.schemas import defender_schema
from pcc.training import serialize_completion
from pcc.resources import sha256

root=Path.cwd();grammar=xgrammar.Grammar.from_json_schema(json.dumps(defender_schema()))
rows=[]
for name in ('main-qwen-c1-17-r0-collect','main-qwen-c1-17-r1-collect','pilot-v4-qwen-c3-collect','pilot-v4-qwen-c5-collect','pilot-v4-phi-c5-collect'):
    path=root/'artifacts/runs'/name/'supervision.jsonl'
    examples=[json.loads(line) for line in path.read_text().splitlines()]
    original=corrected=0
    for example in examples:
        target=example['completion'];fixed=serialize_completion(target)
        assert json.loads(fixed)==target
        original+=_is_grammar_accept_string(grammar,json.dumps(target,separators=(',',':')))
        corrected+=_is_grammar_accept_string(grammar,fixed)
    if corrected!=len(examples):raise ValueError('Corrected supervision violates inference grammar')
    rows.append({'run_id':name,'examples':len(examples),'original_accepted':original,'corrected_accepted':corrected,'supervision_sha256':sha256(path)})
result={'xgrammar_version':version('xgrammar'),'vllm_version':version('vllm'),'checks':rows,'gpu_model_calls':0,
        'source_hashes':{name:sha256(root/name) for name in ('src/pcc/training.py','src/pcc/schemas.py','analysis/audit_serialization.py')}}
(root/'artifacts/corrected_serialization_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
