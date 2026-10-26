"""Requires committed archive extraction; missing inputs are explicit prerequisites."""
import csv,json
import pytest
from .common import *
from .reader import verify
from .review_package import scan
from .events import select

@pytest.fixture(scope='module')
def inputs():
 if not (WORK/'author/episodes.json').exists():pytest.skip('Prerequisite: python -m supplements.evidence_validation_006.reader --extract-only')
 return episodes()

def test_all_selected_quotes_routes_and_temporal_truth(inputs):verify()

def test_fixed_selections_are_exactly_reproducible(inputs):
 assert select(inputs,read(OLD/'SELECTION.json')['cases'])==read(HERE/'EVENT_SELECTION.json')['items']

def test_previous_protected_science_and_forms_unchanged():
 doc=read(HERE/'PRIOR_PROTECTION.json')
 # Lists include existing scientific manifests and original human forms/PDF.
 missing=[]
 for path,value in doc['protected_files'].items():
  if not (ROOT/path).exists():missing.append(path);continue
  assert sha(ROOT/path)==value,path
 if missing:pytest.skip(f'{len(missing)} historical packet files are outside selected package; all present protected files passed')


def test_blinded_package_and_blank_forms():
 path=WORK/'reviewer_build' if (WORK/'reviewer_build').exists() else WORK/'reviewer'
 if not path.exists():pytest.skip('Prerequisite: events, presentation and review_package regeneration')
 for n in ['items.json','episodes.json']:scan(read(path/n))
 for n in [1,2]:
  rows=list(csv.DictReader((path/f'rater_{n}.csv').open()))
  assert len(rows)==72 and len({r['item_id'] for r in rows})==72
  assert all(not value for row in rows for key,value in row.items() if key!='item_id')


def test_shared_note_matches_sender_not_an_older_identical_claim(inputs):
 from .presentation import exchange
 e=next(e for e in inputs if e['case_id']=='DI5-ceecfe5fb4' and e['anchor'] and e['condition']=='C3')
 x=exchange(e);assert x['route']['actual_delivered_payload']['author']==x['selected']['action']['actor']
 assert x['route']['visible'] is True


def test_short_exchanges_preserve_turn_order_and_exact_positions(inputs):
 from .presentation import exchange,chronology,EXCHANGES
 for e in inputs:
  if not e['anchor'] or e['case_id'] not in EXCHANGES:continue
  x=exchange(e);cards=chronology(x)
  assert [c['turn'] for c in cards]==sorted({c['turn'] for c in cards})
  for c in cards:
   original=e['turns'][c['turn']-1]
   assert c['user']==original['user']
   if c['position']:assert c['position']['action']==original['action']
  assert all(z['turn']>x['selected']['turn'] or x['route']['type']=='answerer' for z in x['following'])
