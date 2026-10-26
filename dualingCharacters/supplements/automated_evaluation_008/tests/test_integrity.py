"""Small synthetic fixtures for accounting and evidence boundaries, never result labels."""
import copy
from supplements.automated_evaluation_008.calibration import make_controls
from supplements.automated_evaluation_008.judge_spec_final import prompt,validate
from supplements.automated_evaluation_008.tests.test_semantics import response
from supplements.automated_evaluation_008.repair_audit import complete_fields
from supplements.automated_evaluation_008.analysis import calibration_metrics,binary_range

def test_omitted_generated_suffix_cannot_support_a_quote():
 item=make_controls()[0];out=response(item);out['authorization_assertion'].update(label='yes',ref='selected',quote=item['private']['omitted_generated_suffix'])
 result=validate(out,item);assert result['dimensions']['authorization_assertion']['label'] is None
 assert item['private']['omitted_generated_suffix'] not in prompt(item)[1]['content']

def test_expected_labels_never_become_judge_context():
 item=make_controls()[0];original=prompt(item)
 item['private']['expected']={k:'MUST_NEVER_ENTER_PROMPT' for k in item['private']['expected']}
 item['private']['authorized']['day']='HIDDEN_ORACLE_CHANGE'
 assert prompt(item)==original

def test_calibration_abstentions_are_not_excluded_from_accuracy():
 items=[x for x in make_controls() if x['population']=='synthetic_holdout']
 rs=calibration_metrics(items,[],model='synthetic_fixture',split='holdout')
 for r in rs:
  assert r['planned']==80 and r['invalid_or_missing']==80
  assert r['unconditional_accuracy']==0 and r['substantive_coverage']==0 and not r['screen_pass']

def test_conservative_range_preserves_uncertainty_and_na():
 r=binary_range(['yes','no',None,'uncertain','not_applicable'],['yes','no','no','no','not_applicable'])
 assert r['lower']==.2 and r['upper']==.8 and r['unresolved_or_disagree']==3
 assert binary_range([],[])['lower'] is None

def test_repair_audit_recovers_only_complete_fields():
 raw='{"recommendation":{"label":"yes","ref":"selected","quote":"x"},"authorization_assertion":{"label":"no"'
 assert complete_fields(raw)=={'recommendation':'yes'}
