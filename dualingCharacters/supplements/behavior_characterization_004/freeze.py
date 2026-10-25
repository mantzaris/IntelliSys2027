"""One-time scientific freeze; never silently replaces an existing manifest."""
from .common import *

def create():
    verify_previous();target=HERE/'SCIENTIFIC_MANIFEST.json'
    if target.exists():raise FileExistsError('Scientific freeze already exists; preserve it and document amendments')
    names=['PROTOCOL.md','DEFINITIONS.md','EVIDENCE_SNAPSHOT.json','DATA_AUDIT.json','SECONDARY_SOURCES.json']
    names+=sorted(p.name for p in HERE.glob('*.py'))
    write(target,{'version':1,'frozen_utc':utc(),'evidence_cutoff_utc':read(HERE/'EVIDENCE_SNAPSHOT.json')['cutoff_utc'],
        'comparison_summaries_computed':False,'engineering_validation':'20 focused unit tests and one real C3 episode, without comparative aggregation',
        'known_observations':'Prior pilot counts, negative/mixed task comparisons and inconclusive breadth recorded in PROTOCOL.md; no newly completed behavioral aggregates inspected.',
        'files':{name:sha256(HERE/name) for name in names},'previous_scientific_files':127,
        'prior_scientific_manifest_sha256':sha256(ROOT/'supplements/exploration_003/SCIENTIFIC_MANIFEST.json')})
    log('Froze '+str(len(names))+' scientific files before new comparative summaries. No GPU/model-judge calls.')
    print({'files':len(names),'manifest_sha256':sha256(target),'frozen_utc':read(target)['frozen_utc']})

if __name__=='__main__':create()
