"""Synthetic source records only: partial-run merging never chooses a preferred label."""
import pytest
from supplements.automated_evaluation_008 import semantic_analysis_complete as module

def row(status,label=None):
 return {'item_id':'synthetic-fixture','model':'fixture','probe':'base','record_status':status,'labels':{'question':label}}

def test_merge_replaces_only_unrecorded_placeholder(monkeypatch):
 data={'original':[row('not_recorded')],'continuation':[row('recorded','no')]}
 monkeypatch.setattr(module.base,'load_runs',lambda binding,items:(data[next(iter(binding.values()))[0]],[]))
 rows,_=module.load_complete({'fixture':['original','continuation']},[])
 assert len(rows)==1 and rows[0]['labels']['question']=='no'

def test_merge_preserves_missing_label_in_actual_record(monkeypatch):
 data={'original':[row('recorded',None)],'continuation':[row('not_recorded')]}
 monkeypatch.setattr(module.base,'load_runs',lambda binding,items:(data[next(iter(binding.values()))[0]],[]))
 rows,_=module.load_complete({'fixture':['original','continuation']},[])
 assert rows[0]['record_status']=='recorded' and rows[0]['labels']['question'] is None

def test_duplicate_actual_answers_fail_even_if_one_is_invalid(monkeypatch):
 data={'original':[row('recorded',None)],'continuation':[row('recorded','yes')]}
 monkeypatch.setattr(module.base,'load_runs',lambda binding,items:(data[next(iter(binding.values()))[0]],[]))
 with pytest.raises(ValueError,match='never select a better label'):
  module.load_complete({'fixture':['original','continuation']},[])
