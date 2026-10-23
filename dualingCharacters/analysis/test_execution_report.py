from execution_report import assessment, effect_text
from finalize_when_done import ready


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
