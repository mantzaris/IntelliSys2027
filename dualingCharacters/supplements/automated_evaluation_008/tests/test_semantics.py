"""Synthetic software fixtures only, never research annotations."""
import copy
import pytest
from supplements.automated_evaluation_008.analysis import binary_range,agreements,effective_labels,selection_weights
from supplements.automated_evaluation_008.calibration import make_controls
from supplements.automated_evaluation_008.judge_spec import prompt,validate,QUESTIONS,BINARY

def response(item):
 out={k:{'label':'no' if k in BINARY else 'not_applicable','ref':'','quote':'','explanation':'Synthetic fixture.'} for k in QUESTIONS};out['authorization_assertions']=[];return out

def test_missing_not_negative():
 r=agreements([None,None],['no',None]);assert r['jointly_assessed']==0 and r['exact_agreement'] is None
 assert binary_range([None,'yes'],['no','yes'])['upper']==1

def test_positive_negative_denominators():
 r=agreements(['yes','no','yes'],['yes','no','no']);assert r['positive_denominator']==3 and r['negative_denominator']==3
 assert r['positive_agreement']==2/3

def test_controls_split_support_and_no_gold_prompt():
 rows=make_controls();assert len(rows)==120
 dev={r['template_family'] for r in rows if r['population']=='synthetic_development'};hold={r['template_family'] for r in rows if r['population']=='synthetic_holdout'};assert not dev&hold
 for r in rows:
  text=str(prompt(r));assert 'expected' not in text and 'omitted_generated_suffix' not in text
 for d in BINARY:
  for label in ['yes','no']:assert sum(r['private']['expected'][d]==label and r['population']=='synthetic_holdout' for r in rows)>=8

def test_span_identity_and_unit():
 item=make_controls()[0];out=response(item);out['recommendation'].update(label='yes',ref='selected',quote=item['public']['blocks']['selected'][:20]);assert validate(out,item)['dimensions']['recommendation']['assessed']
 out['recommendation']['quote']='Invented quotation';assert not validate(out,item)['dimensions']['recommendation']['assessed']
 out['recommendation'].update(ref='source_1',quote=item['public']['blocks']['source_1']);assert effective_labels({'final_parsed':out},item)['recommendation'] is None

def test_ledger_comparison_uses_current_truth_not_proposal():
 item=make_controls()[2];out=response(item);out['authorization_assertions']=[{'slot':'day','value':'Saturday','source_id':3,'quote':item['public']['blocks']['selected'],'ambiguous':False}]
 assert validate(out,item)['assertions'][0]['ledger_matches'] is False
 out['authorization_assertions'][0]['ambiguous']=True;assert validate(out,item)['assertions'][0]['ledger_matches'] is None

def test_alias_probe_preserves_chronology():
 item=make_controls()[0];a=prompt(item);b=prompt(item,'alias_permutation');assert 'source_3' in b[1]['content'] and 'Speaker 1' in b[1]['content']
 assert a[0]==b[0]

def test_weighting_and_pair_failure():
 assert selection_weights([{'private':{'identity':{'stratum':s}}} for s in ['direct','communication']])=={'direct':2/3,'communication':1/3}
 with pytest.raises(ValueError):agreements(['no'],[])

def test_temporal_authorization_scope():
 from supplements.automated_evaluation_008.judge_spec_final import validate as check
 item=make_controls()[2];out=response(item)
 a={'slot':'day','value':'Saturday','source_id':3,'quote':item['public']['blocks']['selected'],'ambiguous':False,'temporal_scope':'earlier'}
 out['authorization_assertions']=[a];assert check(out,item)['assertions'][0]['ledger_matches'] is None
 a['temporal_scope']='current';assert check(out,item)['assertions'][0]['ledger_matches'] is False

def test_missing_prose_is_not_invented_negative():
 item=make_controls()[0];assert all(x is None for x in effective_labels({'status':'input_rejected'},item).values())


def test_paired_family_blocks_and_independent_synthetic_population():
 from supplements.automated_evaluation_008.semantic_analysis import paired_contrasts
 rows=[]
 for f in ['a','b']:
  for world in ['authorized','hypothetical']:
   for seed in [17,29,43]:
    for c in ['C3','C5','A1']:
     rows.append(dict(population='broad',probe='base',model='phi',stratum='communication',family=f,world=world,seed=seed,condition=c,labels={d:'yes' if c=='C5' else 'no' for d in BINARY}))
 result=paired_contrasts(rows);assert result[0]['families']==2 and result[0]['paired_events']==12
 assert result[0]['difference_all_opportunities']==1
 assert paired_contrasts([dict(r,population='synthetic_holdout') for r in rows])==[]

def test_unrecorded_planned_judgments_remain_missing(tmp_path,monkeypatch):
 from supplements.automated_evaluation_008 import semantic_analysis_v2 as module
 item=make_controls()[0]
 monkeypatch.setattr(module,'ROOT',tmp_path)
 rows,provenance=module.load_runs({'phi':['auto008-research-phi-fixture']},[item])
 assert len(rows)==1 and rows[0]['record_status']=='not_recorded'
 assert all(v is None for v in rows[0]['labels'].values())
 assert provenance[0]['status']=='not_started'
