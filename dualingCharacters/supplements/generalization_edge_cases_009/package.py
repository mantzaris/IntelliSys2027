"""Compact portable evidence, no weights/private access records/redundant old runs."""
import tarfile
from .common import *
def main():
 allocation=read(HERE/'ALLOCATION.json');runids=[j['run_id'] for j in allocation['jobs']]+['edge009-profile-qwen-v1','edge009-profile-phi-v1','edge009-exclusive-overhead-v1'];files=[]
 for rid in runids:
  folder=ROOT/'artifacts/runs'/rid
  for p in sorted(folder.iterdir()):
   if p.is_file() and p.suffix in {'.json','.jsonl'}:files.append(p)
 # Optional replay, if executed, is separately identified and never enters main endpoints.
 replay=HERE/'REPLAY_BINDING.json'
 if replay.exists():
  for p in sorted((ROOT/'artifacts/runs'/read(replay)['run_id']).glob('*')):
   if p.is_file() and p.suffix in {'.json','.jsonl'}:files.append(p)
 archive=HERE/'evidence/edge009_records.tar.gz';manifest={}
 with tarfile.open(archive,'w:gz',compresslevel=9) as out:
  for p in files:
   name='runs/'+str(p.relative_to(ROOT/'artifacts/runs'));out.add(p,arcname=name);manifest[name]={'sha256':sha(p),'bytes':p.stat().st_size}
 write(HERE/'evidence/MANIFEST.json',{'archive':archive.name,'sha256':sha(archive),'bytes':archive.stat().st_size,'files':manifest,'scope':'Complete new run JSON/JSONL records. Original source trees are bound by the prospective freeze in Git. No prior large raw archives or weights.'});print({'archive_bytes':archive.stat().st_size,'files':len(files)})
if __name__=='__main__':main()
