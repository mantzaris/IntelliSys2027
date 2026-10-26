"""Portable selected evidence and exact judge outputs, never weights or credentials."""
import argparse,tarfile,io
from .common import *

def selected_episodes():
 source=ART/'broad_episodes.json.gz';stamp=read(ART/'broad_cache.json');assert sha(source)==stamp['sha256']
 rows=json.loads(gzip.decompress(source.read_bytes()));families=set(read(HERE/'ALLOCATION.json')['family_order']);selected=[r for r in rows if r['family_id'] in families];assert len(selected)==270
 p=HERE/'inputs/selected_episodes.json.gz';p.write_bytes(gzip.compress(json.dumps(selected,separators=(',',':'),ensure_ascii=False).encode(),mtime=0))
 return p

def build():
 files=[selected_episodes()]
 files += [HERE/'inputs'/n for n in ['research.json','probes.json','compatibility_semantic.json','CORE_CUTOFF.json','core_summary_outcomes.json']]
 if (HERE/'inputs/research_qwen_unrecorded.json').exists():files.append(HERE/'inputs/research_qwen_unrecorded.json')
 runs=[p for p in (ROOT/'artifacts/runs').iterdir() if p.name.startswith('auto008-') or p.name=='dialogue005-compat-17-v1']
 allowed={'status.json','config.json','judgments.jsonl','input_manifest.json','completion.json','batches.jsonl','gpu_telemetry.jsonl','compatible.jsonl','incompatible.jsonl','compatible_characters.jsonl','incompatible_characters.jsonl','compatible_summary.json','incompatible_summary.json'}
 for run in runs:
  assert (run/'status.json').exists();assert read(run/'status.json')['status']!='running'
  files += [p for p in run.iterdir() if p.name in allowed]
 manifest={str(p.relative_to(ROOT)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)}
 target=HERE/'evidence/RAW_AND_INPUTS.tar.gz';target.parent.mkdir(exist_ok=True)
 with target.open('wb') as out,gzip.GzipFile(fileobj=out,mode='wb',mtime=0,filename='') as gz,tarfile.open(fileobj=gz,mode='w') as tar:
  for p in sorted(files):
   name=str(p.relative_to(ROOT));data=p.read_bytes();info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;info.mtime=0;tar.addfile(info,io.BytesIO(data))
 write(HERE/'evidence/MANIFEST.json',{'archive':'RAW_AND_INPUTS.tar.gz','sha256':sha(target),'bytes':target.stat().st_size,'members':manifest,'scope':'Exact new judge/compatibility raw records and statuses; selected reconstructed archive episodes and sufficient core outcomes. Original full common-base archives and model weights are not included. Their historical hashes remain provenance, not fresh full-archive verification.','source_type':'automated_model / controlled_experiment / deterministic_trace','no_human_annotations':True})
 print('Evidence bundle',target.stat().st_size,'bytes',len(files),'members')

def extract():
 manifest=read(HERE/'evidence/MANIFEST.json');p=HERE/'evidence'/manifest['archive'];assert sha(p)==manifest['sha256']
 with tarfile.open(p,'r:gz') as tar:
  assert {m.name for m in tar.getmembers()}==set(manifest['members'])
  for m in tar.getmembers():
   assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
   assert m.name.startswith(('supplements/automated_evaluation_008/inputs/','artifacts/runs/auto008-','artifacts/runs/dialogue005-compat-17-v1/'))
   data=tar.extractfile(m).read();expected=manifest['members'][m.name];assert len(data)==expected['bytes'] and hashlib.sha256(data).hexdigest()==expected['sha256']
   dest=ROOT/m.name;dest.parent.mkdir(exist_ok=True,parents=True)
   if dest.exists():assert sha(dest)==expected['sha256'],'Preserve differing existing file: '+m.name
   else:dest.write_bytes(data)
 print('Offline extraction verified',len(manifest['members']),'members')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--extract',action='store_true');a=p.parse_args()
 if a.build:build()
 elif a.extract:extract()
 else:p.error('Choose --build or --extract; no inference is performed')
