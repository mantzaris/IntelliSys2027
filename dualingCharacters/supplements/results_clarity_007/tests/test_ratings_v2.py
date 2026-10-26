"""SYNTHETIC software fixtures only; these are never human research annotations."""
import copy
import pytest
from supplements.results_clarity_007 import ratings_v2 as r

def row(**changes):
 return dict.fromkeys(r.FIELDS,'')|{'item_id':'SYNTHETIC-1'}|changes

def assessed(label='',**changes):
 return row(statement_annotation_status='assessed',statement_labels=label,supporting_turns='authored fixture turn 1',**changes)

def compare(a,b):return r.agreement([a],[b])['dimensions']

def test_both_optional_blank_are_missing_not_negative():
 a=row(response_annotation_status='assessed',response='another_response',supporting_turns='fixture')
 d=compare(a,a)
 assert d['response']['jointly_assessed']==1
 assert d['statement']['jointly_assessed']==0
 assert d['statement']['exact_agreement'] is None
 assert all(x['both_negative']==0 and x['negative_agreement'] is None for x in d['statement']['labels'])

def test_one_blank_and_explicit_none_are_distinct():
 d=compare(row(),assessed())['statement']
 assert d['jointly_assessed']==0 and d['rater2']['assessed_empty_set']==1
 d=compare(assessed(),assessed())['statement']
 assert d['exact_agreement']==1 and d['exact_agreement_denominator']==1
 assert all(x['negative_agreement']==1 and x['positive_agreement'] is None for x in d['labels'])

def test_positive_negative_disagreement():
 d=compare(assessed('open_preference'),assessed())['statement']
 x=next(x for x in d['labels'] if x['label']=='open_preference')
 assert d['exact_agreement']==0 and x['positive_agreement']==0 and x['negative_agreement']==0
 assert x['rater1_only']==1

def test_unratable_reason_and_uncertainty_are_distinct():
 a=row(statement_annotation_status='unratable',statement_unratable_reason='fixture missing text')
 d=compare(a,assessed('insufficient_evidence'))['statement']
 assert d['jointly_assessed']==0 and d['rater1']['unratable']==1
 assert d['rater2']['uncertain_value']==1
 assert d['rater1']['unratable_reasons']=={'SYNTHETIC-1':'fixture missing text'}
 b=row(response_annotation_status='assessed',response='uncertain',supporting_turns='fixture')
 assert compare(b,b)['response']['rater1']['uncertain_value']==1

def test_secondary_response_does_not_enter_claim_labels():
 a=assessed('open_preference',response_annotation_status='assessed',response='continues_prior_position',secondary_response_notes='Second opportunity: explicit acknowledgment.')
 assert compare(a,a)['statement']['jointly_assessed']==1
 with pytest.raises(ValueError,match='Unknown statement_labels'):
  r.validate_rows([assessed('explicit_acknowledgment')],['SYNTHETIC-1'])

@pytest.mark.parametrize('changes',[
 {'statement_labels':'open_preference'},
 {'statement_annotation_status':'unratable'},
 {'statement_annotation_status':'unratable','statement_labels':'open_preference','statement_unratable_reason':'missing'},
 {'statement_annotation_status':'assessed','statement_unratable_reason':'missing','supporting_turns':'fixture'},
 {'response_annotation_status':'assessed','supporting_turns':'fixture'},
 {'statement_annotation_status':'invented'},
 {'statement_annotation_status':'assessed','statement_labels':'open_preference;open_preference','supporting_turns':'fixture'},
 {'statement_annotation_status':'assessed','statement_labels':'open_preference'},
 {'correctness_annotation_status':'assessed','correctness':'mixed','supporting_turns':''},
])
def test_malformed_combinations(changes):
 with pytest.raises(ValueError):r.validate_rows([row(**changes)],['SYNTHETIC-1'])

def test_mixed_claim_and_normative_categories_remain_available():
 for value in ['mixed','normative_preference']:
  r.validate_rows([row(correctness_annotation_status='assessed',correctness=value,supporting_turns='two quoted fixture clauses')],['SYNTHETIC-1'])

def test_identity_coverage_and_duplicates():
 with pytest.raises(ValueError,match='Duplicate'):r.validate_rows([row(),row()],['SYNTHETIC-1'])
 with pytest.raises(ValueError,match='missing'):r.validate_rows([],['SYNTHETIC-1'])
 with pytest.raises(ValueError,match='Unknown'):r.validate_rows([row(item_id='UNKNOWN')],['SYNTHETIC-1'])

def test_route_strata_not_pooled_peer_influence():
 a=assessed('open_preference');b=assessed('open_preference',item_id='SYNTHETIC-2')
 d=r.agreement([a,b],[a,b],{'SYNTHETIC-1':'component','SYNTHETIC-2':'answerer'})
 assert d['by_recipient_route']['component']['statement']['planned_items']==1
 assert d['by_recipient_route']['answerer']['statement']['planned_items']==1

@pytest.mark.parametrize('defect',['code_hash','source_type','form_hash','naive_time'])
def test_submission_provenance_rejects_stale_or_nonhuman_metadata(tmp_path,monkeypatch,defect):
 # SYNTHETIC plumbing fixture. human_assessment=True exercises validation only;
 # it is not a claim that any person rated an experimental item.
 from supplements.results_clarity_007.common import csv_write,write,sha
 monkeypatch.setattr(r,'event_selection',lambda:[{'item_id':'SYNTHETIC-1'}])
 form=tmp_path/'SYNTHETIC-form.csv';meta=tmp_path/'SYNTHETIC-provenance.json'
 csv_write(form,[assessed('open_preference')],r.FIELDS)
 d={**r.provenance_expected(),'source_type':'independent_human','human_assessment':True,'rater_id':'SYNTHETIC-test-only','completed_at_utc':'2026-01-01T00:00:00Z','form_sha256':sha(form)}
 write(meta,d);assert r.validate_file(form,meta)[0][0]['item_id']=='SYNTHETIC-1'
 if defect=='code_hash':d['ingestion_code_sha256']='stale-version'
 if defect=='source_type':d['source_type']='AI_assisted'
 if defect=='form_hash':d['form_sha256']='wrong'
 if defect=='naive_time':d['completed_at_utc']='2026-01-01T00:00:00'
 write(meta,d)
 with pytest.raises(ValueError):r.validate_file(form,meta)
