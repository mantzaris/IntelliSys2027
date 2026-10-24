"""Descriptive joins of validated aggregates; no curriculum causal estimator."""
from collections import defaultdict
from pathlib import Path
from pcc.resources import sha256
from supplements.review_001.common import write_csv
from .common import ROOT, OUT, read, write


def aggregate(results, exposures, pools, collections, routing):
    """Keep partial fits visible without treating their token totals as final."""
    groups = defaultdict(list)
    for row in exposures:
        if row['status'] == 'reconstructed_and_verified':
            groups[row['model'], row['condition'], row['seed']].append(row)
    result_index = {(r['model'], r['condition'], r['seed']): r for r in results}
    rows = []
    for key in sorted(set(groups) | set(result_index)):
        model, condition, seed = key
        fits = groups[key]
        evaluated = result_index.get(key)
        selected = [r for r in collections if (r['model'], r['condition'], r['seed']) == key]
        ids = {r['run_id'] for r in selected}
        routes = [r for r in routing if r['run_id'] in ids]
        recovery = [r for r in pools if r['run_id'] in {f['run_id'] for f in fits} and r['pool'] == 'recovery']
        row = dict(model=model, condition=condition, seed=seed,
            completed_fits=len(fits), planned_fits=0 if condition == 'base' else 2,
            completed_collections=len(selected), final_evaluation_available=evaluated is not None,
            training_input_tokens=sum(r['training_input_tokens'] for r in fits),
            supervised_target_tokens=sum(r['supervised_target_tokens'] for r in fits),
            recovery_target_tokens=sum(r['target_tokens'] for r in recovery),
            verified_model_recovery_target_tokens=sum(r.get('target_tokens_by_label_source', {}).get('verified_model_recovery', 0) for r in fits),
            action_opportunities=sum(r['opportunities'] for r in routes),
            shared_memory_changes=sum(r['shared_memory_changed'] for r in routes),
            source_visible_contradiction_flags=sum(r['source_visible_contradiction_flags'] for r in routes),
            direct_peer_notes_to_jekyll=sum(r['direct_peer_notes_to_jekyll'] for r in routes),
            antagonist_peer_deliveries=sum(r['antagonist_recipient_deliveries'] for r in routes),
            paired_success=evaluated['paired_success'] if evaluated else None,
            canonical_source_coverage=evaluated['all_canonical_sources_visible'] / evaluated['conversations'] if evaluated else None,
            fit_run_ids=[r['run_id'] for r in fits], collection_run_ids=sorted(ids))
        for rnd in (0, 1):
            r = next((r for r in recovery if f'-r{rnd}-' in r['run_id']), None)
            c = next((c for c in selected if f'-r{rnd}-' in c['run_id']), None)
            row.update({f'r{rnd}_recovery_{name}': r[name] if r else None for name in
                        ('eligible_windows', 'loss_contributing_unique_windows', 'loss_contributing_unique_families',
                         'loss_contributing_occurrences', 'top1_token_share', 'top5_token_share')})
            row[f'r{rnd}_failed_eligible_families'] = c['eligible_failed_families'] if c else None
        rows.append(row)
    return rows


def main():
    names = ['per_seed_results', 'supervision_exposure', 'supervision_pools', 'collections', 'routing_counts']
    inputs = [OUT / (name + '.json') for name in names]
    rows = aggregate(*(read(p) for p in inputs))
    write(OUT / 'curriculum_associations.json', rows)
    write_csv(OUT / 'curriculum_associations.csv', rows)
    write(OUT / 'association_provenance.json', {'inputs': {str(p.relative_to(ROOT)): sha256(p) for p in inputs},
          'code_sha256': sha256(Path(__file__)), 'qualification': 'Descriptive cross-condition joins only; no causal or mediation estimate.'})
    lines = ['# Curriculum and outcome associations — descriptive only\n',
      'Each row joins completed, eligible artifacts for one model/condition/training seed. '
      'Partially completed training budgets are explicitly marked. Differences in curriculum, prompt length, '
      'target exposure and routing are entangled; this table does not identify a causal mechanism. '
      'Source-visible contradictions are observable flags, not proof of deliberate deception.\n',
      '| Model | Condition | Seed | Fits | Input tokens | Target tokens | R1 recovery windows / families contributing loss | R1 top-five recovery-token share | Shared memory changes / opportunities | Paired success |',
      '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        windows = r['r1_recovery_loss_contributing_unique_windows']; families = r['r1_recovery_loss_contributing_unique_families']
        pool = f'{windows} / {families}' if windows is not None else 'pending' if r['condition'] != 'base' else 'n/a'
        top = r['r1_recovery_top5_token_share']; top_text = f'{100*top:.1f}%' if top is not None else '—'
        result = f'{100*r["paired_success"]:.2f}%' if r['paired_success'] is not None else 'pending'
        lines.append(f'| {r["model"]} | {r["condition"]} | {r["seed"]} | {r["completed_fits"]}/{r["planned_fits"]} | '
          f'{r["training_input_tokens"]:,} | {r["supervised_target_tokens"]:,} | {pool} | {top_text} | '
          f'{r["shared_memory_changes"]}/{r["action_opportunities"]} | {result} |')
    lines += ['\nEqual packed input-token budgets do not imply equal supervised target-token exposure. '
      'The 50:50 sampler alternates examples; it does not guarantee a 50:50 target-token split. '
      'Repeated recovery occurrences are not independent recovery examples. Source coverage is an analysis-only measurement; '
      'it did not determine policy inputs or select an outcome subset.\n',
      'The CSV/JSON retain per-round eligibility, distinct loss-contributing windows/families, repeats, '
      'top-one and top-five shares, actual verified-model-recovery target tokens, peer routing and canonical-source coverage. '
      'Counts of changed memory include bounded notes as implemented, not necessarily false commitments.\n']
    (OUT / 'CURRICULUM_ASSOCIATIONS.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
