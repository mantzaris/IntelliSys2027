"""Supply the official v3 SentencePiece file under Transformers' expected name."""
from pathlib import Path
import hashlib
import json
from transformers import AutoTokenizer

source=Path(Path('artifacts/models/mistral_path.txt').read_text().strip())
target=Path('artifacts/models/mistral-tokenizer-transformers').resolve()
target.mkdir(parents=True,exist_ok=True)
mapping={'tokenizer.json':'tokenizer.json','tokenizer_config.json':'tokenizer_config.json',
         'special_tokens_map.json':'special_tokens_map.json','config.json':'config.json',
         'tokenizer.model':'tokenizer.model.v3'}
hashes={}
for name,original in mapping.items():
    src=source/original
    if not src.exists(): raise RuntimeError('Missing official tokenizer component: '+str(src))
    dst=target/name
    if not dst.exists():dst.symlink_to(src.resolve())
    hashes[name]={'source_name':original,'sha256':hashlib.sha256(src.read_bytes()).hexdigest()}
t=AutoTokenizer.from_pretrained(target)
tokens=t.apply_chat_template([{'role':'user','content':'Return a JSON object.'}],tokenize=True,add_generation_prompt=True)
assert tokens and len(t)==32768
Path('artifacts/models/mistral_tokenizer_path.txt').write_text(str(target))
Path('records/models/mistral-tokenizer-layout.json').write_text(json.dumps({'files':hashes,
    'vocabulary_size':len(t),'change':'Unmodified official tokenizer.model.v3 is aliased to tokenizer.model for Transformers legacy=False loader; no vocabulary modification.'},indent=2)+'\n')
print('Official Mistral v3 tokenizer loaded:',len(t),'tokens')
