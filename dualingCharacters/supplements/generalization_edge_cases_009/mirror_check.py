"""Hash only completed new records; leave active core files untouched."""
import os,shlex,subprocess
from .common import *
def main():
 from supplements.review_001.controller import connection
 os.environ.update(read(ART/'original_owner_private.json')['environment']);ssh,target,remote=connection()
 runids=[j['run_id'] for j in read(HERE/'ALLOCATION.json')['jobs']]+['edge009-profile-qwen-v1','edge009-profile-phi-v1','edge009-exclusive-overhead-v1']
 if (HERE/'REPLAY_BINDING.json').exists():runids.append(read(HERE/'REPLAY_BINDING.json')['run_id'])
 script="import pathlib,json,hashlib; root=pathlib.Path('artifacts/runs'); ids="+repr(runids)+"; result={};\nfor name in ids:\n for p in (root/name).iterdir():\n  if p.is_file() and p.suffix in {'.json','.jsonl'}: result[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()\nprint(json.dumps(result))"
 raw=subprocess.check_output(ssh+[target,'cd '+shlex.quote(remote)+' && python3 -c '+shlex.quote(script)],text=True,timeout=45);hashes=json.loads(raw)
 for n,h in hashes.items():assert sha(ROOT/'artifacts/runs'/n)==h,n
 write(HERE/'reports/MIRROR_HASHES.json',{'utc':now(),'completed_new_files':len(hashes),'hashes':hashes,'status':'matched','active_core_files_read':False});print({'new_files_matched':len(hashes)})
if __name__=='__main__':main()
