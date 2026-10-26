"""CPU fixtures; no inference and no synthetic research results."""
from supplements.automated_evaluation_008.common import read,ROOT,HERE,verify
from supplements.evidence_validation_006.compatibility_design import dry_run
from supplements.automated_evaluation_008.gpu_worker import stage_seconds
from supplements.automated_evaluation_008.judge_spec_final import prompt
import json
import pytest
pytestmark=pytest.mark.skipif(not (HERE/'inputs/research.json').exists(),reason="Artifact prerequisite: run automated_evaluation_008.bundle --extract before integration checks.")

def test_frozen_full_compatibility_design():
 d=read(ROOT/'supplements/evidence_validation_006/compatibility/DESIGN.json');dry_run(d)
 assert d['conversations']==64 and d['scheduled_calls']==2816 and d['opportunities']==12
 assert len(read(HERE/'inputs/COMPATIBILITY_SEMANTIC_SELECTION.json'))==32

def test_final_allocation_is_complete_and_under_cap():
 d=read(HERE/'ALLOCATION.json');assert d['tier_families']==15 and d['broad_events']==540
 assert d['total_worst_admitted_stage_seconds']<=14400
 assert d['project_used_seconds_at_freeze']+d['remaining_obligations_seconds']+sum(d['bounds_seconds'].values())+d['contingency_seconds']<=96*3600
 verify(HERE/'SCIENTIFIC_FREEZE.json')

def test_input_identity_matching_and_no_private_ledger():
 items=[r for r in read(HERE/'inputs/research.json') if r['population']=='broad'];pairs={}
 for r in items:
  i=r['private']['identity'];key=(i['family_id'],i['world'],i['seed'],i['stratum'],i['opportunity']);pairs.setdefault(key,set()).add(i['condition'])
  payload=json.loads(prompt(r)[1]['content']);assert 'private' not in payload and 'expected' not in payload
  assert payload['evidence']['blocks']['selected']==r['public']['blocks']['selected']
 assert len(pairs)==180 and all(v=={'C3','C5','A1'} for v in pairs.values())

def test_reservations_count_failed_and_repeated_heartbeat_once(tmp_path):
 p=tmp_path/'ledger.jsonl';rows=[{'run_id':'auto008-x','gpu_reserved_seconds':2,'status':'running'},{'run_id':'auto008-x','gpu_reserved_seconds':5,'status':'failed'},{'run_id':'dialogue005-compat-x','budget_identity':'dialogue005-compatibility','gpu_reserved_seconds':3},{'run_id':'core','gpu_reserved_seconds':100}];p.write_text(''.join(json.dumps(r)+'\n' for r in rows));assert stage_seconds(p)==8
