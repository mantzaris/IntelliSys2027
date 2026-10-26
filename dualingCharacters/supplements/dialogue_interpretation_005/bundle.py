"""Create a portable local evidence archive, never weights or access credentials."""
import gzip
import tarfile
from .common import *

def run():
    census=read(HERE/'EVIDENCE_CUTOFF.json');files={}
    for run,b in census['bound_dialogue_runs'].items():
        for name,sha in b['raw_files'].items():verified(ROOT/name,sha);files[name]=sha
        for leaf,key in [('source_snapshot.tar.gz','source_archive_sha256'),('status.json','status_sha256')]:
            name=f'artifacts/runs/{run}/{leaf}';verified(ROOT/name,b[key]);files[name]=b[key]
    # Selected derivative records and the reviewer payload are small when compressed.
    for leaf in ['episodes.json','selected_records.jsonl.gz','QUOTATIONS.json','EXTRACTION_CACHE.json']:
        path=CACHE/leaf;files[relative(path)]=digest(path)
    for path in (CACHE/'human_review').rglob('*'):
        if path.is_file():files[relative(path)]=digest(path)
    for leaf in ['DIALOGUE_ATLAS.html','DIALOGUE_ATLAS.md','CASEBOOK.html','AI_READINGS.json']:
        path=HERE/leaf;files[relative(path)]=digest(path)
    entries=[{'path':n,'sha256':sha,'bytes':(ROOT/n).stat().st_size} for n,sha in sorted(files.items())]
    target=CACHE/'EVIDENCE_BUNDLE.tar.gz'
    with target.open('wb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|') as archive:
                for row in entries:
                    path=ROOT/row['path'];info=tarfile.TarInfo(row['path']);info.size=row['bytes'];info.mode=0o644;info.mtime=0
                    with path.open('rb') as source:archive.addfile(info,source)
    write(HERE/'EVIDENCE_BUNDLE_MANIFEST.json',{'created_utc':now(),'bundle_path':relative(target),'bundle_sha256':digest(target),
        'bundle_bytes':target.stat().st_size,'uncompressed_bytes':sum(r['bytes'] for r in entries),'entries':entries,
        'purpose':'Author-only full provenance and renderer inputs. Share only human_review/reviewer with raters; the archive contains private condition keys and AI readings.',
        'restore':'Verify archive hash; extract only into a separate empty staging directory. Verify each entry before copying a missing file; never overwrite existing artifacts or rating forms.',
        'no_weights_or_credentials':True})
    print({'entries':len(entries),'bundle_bytes':target.stat().st_size,'sha256':digest(target)})

if __name__=='__main__':run()
