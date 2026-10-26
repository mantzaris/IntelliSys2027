"""Bind analysis choices before new AI-assisted comparative readings."""
from .common import *

FILES=['PROTOCOL.md','SEMANTIC_CODEBOOK.md','SELECTION.json','EVIDENCE_CUTOFF.json',
       '__init__.py','common.py','selection.py','inventory.py','extraction.py','statistics.py',
       'annotations.py','blinding.py','test_unit.py','freeze.py',
       'tables/FAMILY_NUMERATORS.csv','tables/FAMILY_INPUT_PROVENANCE.json']

def verify():
    for name,value in read(HERE/'SCIENTIFIC_MANIFEST.json')['files'].items(): verified(HERE/name,value)

def run():
    if (HERE/'SCIENTIFIC_MANIFEST.json').exists():raise FileExistsError('Scientific freeze exists')
    write(HERE/'SCIENTIFIC_MANIFEST.json',{'frozen_utc':now(),'files':{name:digest(HERE/name) for name in FILES},
        'known_before_new_readings':'Behavior004 channels/persistence/evidence and exploration003 inconclusive breadth; numerical reuse verified. No new comparative semantic readings yet.',
        'evidence_cutoff':read(HERE/'EVIDENCE_CUTOFF.json')['cutoff_utc'],
        'correction_policy':'Version any scientific correction explicitly; retain original frozen files and prior outputs.'})

if __name__=='__main__':run()
