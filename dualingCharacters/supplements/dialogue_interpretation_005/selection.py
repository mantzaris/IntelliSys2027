"""Lock inherited windows, corresponding full episodes, and outcome-blind contrasts."""
from collections import defaultdict
from .common import *

CONDITIONS = ('C3', 'C5', 'A1')

def choose(mapping):
    groups = defaultdict(dict)
    for row in mapping:
        key = row['seed'], row['family_id'], row['world']
        if row['condition'] in groups[key]: raise ValueError('Duplicate anchor condition')
        groups[key][row['condition']] = row['item_id']
    if len(groups) != 12 or any(set(v) != {'C3', 'C5'} for v in groups.values()):
        raise ValueError('Expected twelve intact C3/C5 anchor pairs')
    ordered = sorted(groups, key=lambda k: rank('dialogue005-opposite-v1', '|'.join(map(str, k))))
    opposites = set(ordered[:4]); cases = []
    for key in sorted(groups):
        seed, family, world = key
        case_id = 'DI5-' + rank('dialogue005-case-v1', '|'.join(map(str, key)))[:10]
        worlds = [world] + ([('hypothetical' if world == 'authorized' else 'authorized')] if key in opposites else [])
        episodes = []
        for included_world in worlds:
            for condition in CONDITIONS:
                episodes.append({'episode_id': 'D5E-' + rank('dialogue005-episode-v1', f'{case_id}|{included_world}|{condition}')[:12],
                    'condition': condition, 'seed': seed, 'family_id': family, 'world': included_world,
                    'anchor': included_world == world,
                    'old_window_id': groups[key].get(condition) if included_world == world else None,
                    'run_id': f'main-qwen-{condition.lower()}-{seed}-r0-collect'})
        cases.append({'case_id': case_id, 'seed': seed, 'family_id': family, 'anchor_world': world,
                      'opposite_world_included': key in opposites, 'episodes': episodes})
    # Themes are assigned to cases before reading dialogue, not selected for successful examples.
    paper = sorted(cases, key=lambda c: rank('dialogue005-paper-v1', c['case_id']))[:6]
    themes = ['advocacy versus authorization', 'repetition and little observable interaction',
              'biography removal and expression', 'user revision versus hypothetical discussion',
              'peer evidence and prior recipient position', 'tool action versus following answer']
    for case in cases:
        case['main_paper_theme'] = themes[paper.index(case)] if case in paper else None
    return cases

def run():
    destination = HERE / 'SELECTION.json'
    if destination.exists(): raise FileExistsError('Selection is already frozen')
    mapping = ROOT / 'artifacts/behavior_characterization_004/human_review/private/mapping.json'
    expected = read(ROOT / 'supplements/behavior_characterization_004/reports/SEMANTIC_REVIEW_STATUS.json')
    verified(mapping, expected['private_mapping_sha256'])
    cases = choose(read(mapping))
    write(destination, {'selected_utc': now(), 'source': relative(mapping), 'source_sha256': digest(mapping),
        'rule': 'All twelve inherited anchor pairs; add A1 without substitution. Four opposite worlds and six paper cases use fixed SHA256 rankings.',
        'unique_families': len({c['family_id'] for c in cases}), 'anchor_triplets': 12,
        'anchor_episodes_requested': 36, 'opposite_episodes_requested': 12, 'cases': cases})

if __name__ == '__main__': run()
