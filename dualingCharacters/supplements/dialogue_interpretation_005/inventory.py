"""One dated status census; only selected completed traces enter interpretation."""
from .common import *
from pcc.eligibility import exclusions
from supplements.behavior_characterization_004.common import verify_science

def run():
    target = HERE / 'EVIDENCE_CUTOFF.json'
    if target.exists(): raise FileExistsError('Evidence census already locked')
    verify_science()
    cutoff = now(); excluded = exclusions(ROOT); census = []
    selected = {e['run_id'] for c in read(HERE/'SELECTION.json')['cases'] for e in c['episodes']}
    prior = read(ROOT/'supplements/behavior_characterization_004/DATA_AUDIT.json')
    prior_cells = {c['run_id']: c for c in prior['cells'] if c['cohort'] == 'main_round_zero'}
    bound = {}; protected = {}
    for path in sorted((ROOT/'artifacts/runs').glob('*/status.json')):
        meta = read(path); name = path.parent.name
        if not (name.startswith(('main-', 'base-', 'mechanism-'))): continue
        eligible = meta.get('status') == 'completed' and name not in excluded
        cfg = meta.get('config', {})
        census.append({'run_id': name, 'status': meta.get('status'), 'eligible': eligible,
            'exclusion': excluded.get(name), 'status_sha256': digest(path), 'task': meta.get('task'),
            'model': cfg.get('model'), 'condition': cfg.get('condition'), 'seed': cfg.get('seed'),
            'model_revision': meta.get('model_revision'), 'defender_adapter_sha256': meta.get('loaded_adapter_sha256'),
            'config': cfg, 'horizon': meta.get('horizon'), 'families': meta.get('families'),
            'source_snapshot_sha256': meta.get('source_snapshot_sha256'),
            'model_calls': meta.get('model_calls'), 'input_tokens': meta.get('input_tokens'),
            'output_tokens': meta.get('output_tokens'), 'reserved_seconds': meta.get('gpu_reserved_seconds'),
            'use': 'selected common-base dialogue' if name in selected else 'inventory only; not added to previous quantitative populations'})
        if name not in selected: continue
        if not eligible: bound[name] = {'available': False, 'reason': 'Incomplete or excluded at cutoff'}; continue
        old = prior_cells[name]
        assert meta.get('loaded_adapter_path') is None, 'Common-base defender required'
        raw = {}
        for filename, value in old['raw_hashes'].items():
            file = path.parent / filename; verified(file, value)
            raw[relative(file)] = value
        verified(path.parent/'source_snapshot.tar.gz', old['source_archive_sha256'])
        bound[name] = {'available': True, 'raw_files': raw, 'status_sha256': digest(path),
            'source_archive_sha256': old['source_archive_sha256'], 'source_hashes': meta['source_hashes'],
            'model_revision': meta['model_revision'], 'defender': 'untrained base; no adapter',
            'generator': 'same frozen base weights in separate role contexts', 'config': cfg,
            'schedule': old['schedule'], 'family_ids': old['family_ids'], 'horizon': old['horizon'],
            'prior_complete_pair_and_order_audit': relative(ROOT/'supplements/behavior_characterization_004/DATA_AUDIT.json')}
    for supplement in ['review_001', 'exploration_003', 'behavior_characterization_004', 'long_horizon_intent_002']:
        directory = ROOT/'artifacts'/supplement
        for path in directory.rglob('*'):
            if path.is_file() and ('human_review' in str(path) or ('rater' in path.name and path.suffix == '.csv')):
                protected[relative(path)] = digest(path)
    for path in (ROOT/'supplements/behavior_characterization_004').glob('AMENDMENT_*_MANIFEST.json'):
        for name, value in read(path)['files'].items(): verified(path.parent/name, value)
    write(target, {'cutoff_utc': cutoff, 'selection_sha256': digest(HERE/'SELECTION.json'),
        'excluded_registry_sha256': digest(ROOT/'configs/run_exclusions.json'), 'census': census,
        'bound_dialogue_runs': bound, 'protected_review_files': protected,
        'prior_quantitative_audit_sha256': digest(ROOT/'supplements/behavior_characterization_004/DATA_AUDIT.json'),
        'quantitative_population': 'Reuse behavior004 and exploration003 frozen estimates; newer census entries are not silently pooled.'})
    print({'cutoff': cutoff, 'census_runs': len(census), 'bound_runs': len(bound), 'protected_review_files': len(protected)})

if __name__ == '__main__': run()
