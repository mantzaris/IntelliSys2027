from execution_report import assessment, effect_text
from finalize_when_done import ready
from resource_snapshot import snapshot
import json


def test_pending_seed_comparison_is_not_an_effect():
    assert effect_text(None).startswith('Pending:')
    assert 'incomplete' in assessment(False, {'ci95': [.1, .2]})
    assert 'requires audit' in assessment(True, None)


def test_factual_interval_interpretation_keeps_null_and_negative_findings():
    assert 'not established' in assessment(True, {'ci95': [-.1, .2]})
    assert 'favors generic' in assessment(True, {'ci95': [-.2, -.1]})
    assert 'own controls' in assessment(True, {'ci95': [.1, .2]})


def test_finalizer_requires_core_completion_and_terminal_supplement_decision():
    assert not ready({}, {'status': 'controller_error'})
    assert not ready({'status': 'scheduled_grid_complete'}, {'status': 'waiting_for_core'})
    assert ready({'status': 'scheduled_grid_complete'}, {'status': 'not_executed_budget_gate'})
    assert ready({'status': 'scheduled_grid_complete'}, {'status': 'scheduled_supplement_complete'})


def test_resource_snapshot_replaces_stale_totals_and_counts_latest_attempt_once(tmp_path):
    for name,seconds,status in [('good',100,'completed'),('bad',20,'failed')]:
        folder=tmp_path/'artifacts/runs'/name;folder.mkdir(parents=True)
        (folder/'status.json').write_text(json.dumps({'started_utc':'2026-10-24T00:00:00Z',
          'gpu_reserved_seconds':seconds,'status':status,'input_tokens':10,'output_tokens':2,
          'train_tokens':4,'model_calls':1}))
    (tmp_path/'artifacts/run_registry.jsonl').write_text('\n'.join(json.dumps(r) for r in [
      {'run_id':'good','gpu_reserved_seconds':50}, {'run_id':'good','gpu_reserved_seconds':100},
      {'run_id':'bad','gpu_reserved_seconds':20}])+'\n')
    target=tmp_path/'reports/tables/resource_totals.json';target.parent.mkdir(parents=True)
    target.write_text('{"reserved_gpu_hours":999}')
    observed=snapshot(tmp_path)
    assert observed['reserved_gpu_hours']==120/3600
    assert observed['inference_input_tokens']==20
    assert observed['completed']==1 and observed['runs']==2
    assert json.loads(target.read_text())['reserved_gpu_hours']==120/3600
    assert len(observed['input_hashes'])==3
