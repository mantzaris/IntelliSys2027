"""Export existing selected evidence once; no new run population or semantic labels."""
import gzip,tarfile,io
from .common import *

def archive(path,entries):
 with Path(path).open('wb') as raw:
  with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as z:
   with tarfile.open(fileobj=z,mode='w|') as tar:
    for name,data in sorted(entries.items()):
     info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;info.mtime=0;tar.addfile(info,io.BytesIO(data))
 return {'archive':str(Path(path).relative_to(HERE)),'sha256':sha(path),'bytes':Path(path).stat().st_size,
         'members':{n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in entries.items()}}

def run():
 cutoff=read(OLD/'EVIDENCE_CUTOFF.json');cache=ROOT/'artifacts/dialogue_interpretation_005'
 whole={p:h for b in cutoff['bound_dialogue_runs'].values() for p,h in b['raw_files'].items()}
 for name,h in whole.items():assert sha(ROOT/name)==h
 entries={n:(cache/n).read_bytes() for n in ['episodes.json','selected_records.jsonl.gz','QUOTATIONS.json']}
 statuses={}
 for run_id,b in cutoff['bound_dialogue_runs'].items():
  p=ROOT/'artifacts/runs'/run_id/'status.json';assert sha(p)==b['status_sha256'];r=read(p);assert r['status']=='completed'
  statuses[run_id]={'sha256':sha(p),'raw_text':p.read_text()}
 entries['original_status_records.json']=json.dumps(statuses,ensure_ascii=False,indent=2).encode()
 entries['AI_READINGS.json']=(OLD/'AI_READINGS.json').read_bytes()
 entries['run_provenance.json']=json.dumps({'cutoff_utc':cutoff['cutoff_utc'],'bound_runs':cutoff['bound_dialogue_runs'],
   'whole_archives_verified_locally_utc':now(),'whole_file_hashes':whole,
   'fresh_clone_verification_limit':'Only selected original records are included. Their archive hash and quotation identity can be verified; omitted original records and whole original raw-file hashes cannot be recomputed from this package.'},ensure_ascii=False,indent=2).encode()
 manifest=archive(HERE/'evidence/author_selected_v1.tar.gz',entries)
 manifest.update(selection_sha256=sha(OLD/'SELECTION.json'),original_episodes_sha256=sha(cache/'episodes.json'),
                 contents='48 selected episodes and1344 original selected JSONL records; full original run archives intentionally omitted',
                 no_weights_or_remote_access_details=True)
 write(HERE/'evidence/AUTHOR_MANIFEST.json',manifest)
 print({'author_bytes':manifest['bytes'],'full_original_raw_bytes_omitted':sum((ROOT/n).stat().st_size for n in whole)})

if __name__=='__main__':run()
