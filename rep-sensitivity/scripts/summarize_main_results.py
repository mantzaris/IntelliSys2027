"""Compact accuracy report from a completed, audited frozen main evaluation.

Organization-specific breakdowns and transition counts are descriptive. This
does not replace the frozen primary contrasts in analysis.json or select cases.
"""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from rep_sensitivity.analysis import bootstrap


def main():
    directory = Path('results/main-v7')
    analysis_path = directory / 'analysis.json'
    audit_path = Path('records/audits/main-v7.json')
    analysis = json.loads(analysis_path.read_text())
    audit = json.loads(audit_path.read_text())
    assert analysis['complete'] and not analysis['excluded_incomplete_score_files']
    assert not audit['models_without_manifest']
    assert all(m['run_complete'] and m['accepted_calls_match_completed_scores']
               for m in audit['models'].values())
    with (directory / 'decisions.csv').open() as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == analysis['planned_trajectories']
    for row in rows:
        assert row['correct'] in ('True', 'False')
        assert row['decision_changed'] in ('True', 'False')
        row['correct'] = row['correct'] == 'True'
        row['decision_changed'] = row['decision_changed'] == 'True'

    results = []
    for kind in sorted({r['kind'] for r in rows}):
        for model in sorted({r['model'] for r in rows}):
            for organization in ('both', 'flat', 'hierarchical'):
                selected = [r for r in rows if r['kind'] == kind and r['model'] == model
                            and (organization == 'both' or r['organization'] == organization)]
                cells = defaultdict(dict)
                strata = {}
                for row in selected:
                    key = tuple(row[k] for k in ('pair_id', 'world', 'organization', 'policy', 'repetition'))
                    assert row['condition'] not in cells[key]
                    cells[key][row['condition']] = row['correct']
                    strata[row['pair_id']] = (row['family'], row['decision_changed'])
                assert all(set(arms) == {'single', 'exact', 'paraphrase'} for arms in cells.values())
                for treatment, control in (('exact', 'single'), ('paraphrase', 'single'), ('exact', 'paraphrase')):
                    effects = defaultdict(list)
                    corrections = regressions = 0
                    for key, arms in cells.items():
                        effects[key[0]].append(int(arms[treatment]) - int(arms[control]))
                        corrections += arms[treatment] and not arms[control]
                        regressions += arms[control] and not arms[treatment]
                    base_effects = {key: sum(values) / len(values) for key, values in effects.items()}
                    interval = bootstrap(base_effects, strata)
                    n = len(cells)
                    baseline = sum(a[control] for a in cells.values()) / n
                    repeated = sum(a[treatment] for a in cells.values()) / n
                    assert abs(repeated - baseline - interval['estimate']) < 1e-12
                    if organization == 'both' and control == 'single':
                        primary = next(r for r in analysis['contrasts'] if
                                       (r['kind'], r['model'], r['contrast']) == (kind, model, 'H1_' + treatment))
                        assert abs(interval['estimate'] + primary['estimate']) < 1e-12
                        assert abs(interval['lower'] + primary['upper']) < 1e-12
                        assert abs(interval['upper'] + primary['lower']) < 1e-12
                    results.append({
                        'kind': kind, 'model': model, 'organization': organization,
                        'treatment': treatment, 'control': control,
                        'policies': ['ordinary', 'checklist', 'scope'],
                        'independent_base_pairs': len(effects), 'trajectories_per_condition': n,
                        'control_accuracy': baseline, 'treatment_accuracy': repeated,
                        'accuracy_effect': interval, 'corrections': corrections,
                        'regressions': regressions, 'unchanged_correctness': n - corrections - regressions,
                        'base_effects': base_effects,
                    })
    report = {
        'suite': analysis['suite'], 'complete': True,
        'independent_base_pairs_shared_across_models': len({r['pair_id'] for r in rows}),
        'trajectories': len(rows),
        'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (analysis_path, audit_path, directory / 'decisions.csv', Path(__file__))},
        'method': 'Positive effects mean higher accuracy. Equal cell weighting within each base. '
                  'Whole-base bootstrap, 10000 replicates, seed 20271015, family-by-change strata. '
                  'Both organizations reproduces frozen H1 with accuracy rather than error signs. '
                  'Organization breakdowns and exact-minus-paraphrase comparisons are descriptive. '
                  'All completed malformed outputs remain errors. Unchanged correctness may include changed answers.',
        'comparisons': results,
    }
    destination = directory / 'report-summary.json'
    destination.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'report': str(destination), 'comparisons': len(results), 'trajectories': len(rows)}))


if __name__ == '__main__':
    main()
