import unittest
import json
import tempfile
import gzip
from pathlib import Path
from unittest.mock import patch
from copy import deepcopy
from dataclasses import replace
from rep_sensitivity.generation import generate_pair
from rep_sensitivity.reports import make_reports, freeze, thaw, repeat, registry, ancestry_registry
from rep_sensitivity.graphs import partition
from rep_sensitivity.policies import make_prompt
from rep_sensitivity.metrics import parse, same_value
from rep_sensitivity.schema import canonical
from rep_sensitivity.schema import digest
from rep_sensitivity.targeted_replay import lossless_summary
from rep_sensitivity.objective_preservation import repair_objectives
from rep_sensitivity.objective_preservation import plan, input_inventory, run
from rep_sensitivity.numerical_audit import assertion_triples, field_records, summarize_fields


class NumericalPreservationTests(unittest.TestCase):
    def fixture(self):
        pair=generate_pair('development',6,2)
        reports=make_reports(pair['worlds'][0],'development',pair['seed'])
        obj,_=parse(canonical(lossless_summary(reports)),pair['worlds'][0]['tie_order'],manager=True)
        return reports,[{'manager':0,'summary':obj,'parse_status':'valid'}]

    def test_boolean_is_raw_model_value_not_numeric_one(self):
        reports,summary=self.fixture();obj=summary[0]['summary']
        objective=next(a for a in obj['assertions'] if '/objective/' in a[0]);objective[1]=True
        raw=deepcopy(obj);raw['assertions']=[dict(zip(('key','value','reports'),a)) for a in raw['assertions']]
        parsed,status=parse(canonical(raw),[],manager=True)
        self.assertEqual(status,'valid')  # Shared frozen JSON schema is permissive.
        self.assertEqual(canonical(assertion_triples(raw)),canonical(parsed['assertions']))
        self.assertFalse(same_value(True,1));self.assertFalse(same_value(1,True));self.assertTrue(same_value(1.0,1))
        counts=summarize_fields(field_records(reports,[parsed]))
        self.assertEqual(counts['objective_boolean_replacement'],1)
        self.assertEqual(counts['objective_number_changed'],0)

    def test_repair_only_uses_accessible_source_and_keeps_unrelated_content(self):
        reports,summary=self.fixture();obj=summary[0]['summary']
        eligible=[r for r in reports if r.claim.task_identifier=='objective']
        # Only two objectives available to this branch; a third must stay missing.
        branch=[r for r in reports if r!=eligible[2]]
        obj['assertions']=[a for a in obj['assertions'] if a[0]!=eligible[2].claim.key]
        target=next(a for a in obj['assertions'] if a[0]==eligible[0].claim.key);target[1]=True
        obj['assertions']=[a for a in obj['assertions'] if a[0]!=eligible[1].claim.key]
        obj['unresolved']=[eligible[0].claim.key,'unrelated_scope']
        before=deepcopy(summary);repaired,edits=repair_objectives(summary,{0:branch})
        self.assertEqual(summary,before)
        after=repaired[0]['summary'];self.assertNotIn(eligible[2].claim.key,[a[0] for a in after['assertions']])
        self.assertEqual([a for a in obj['assertions'] if '/objective/' not in a[0]],
                         [a for a in after['assertions'] if '/objective/' not in a[0]])
        self.assertEqual(after['unresolved'],['unrelated_scope'])
        self.assertEqual({e['operation'] for e in edits},{'replace','add','remove_objective_unresolved_flag'})
        for e in edits:
            self.assertEqual(e['scope'],next(r.claim.scope() for r in branch if r.claim.key==e['key']))

    def test_noop_is_identical_and_conflicting_source_is_not_resolved(self):
        reports,summary=self.fixture()
        for a in summary[0]['summary']['assertions']:
            if '/objective/' in a[0]:a[1]=float(a[1])
        changed,edits=repair_objectives(summary,{0:reports})
        self.assertEqual(canonical(changed),canonical(summary));self.assertEqual(edits,[])
        report=next(r for r in reports if r.claim.task_identifier=='objective')
        contrary=replace(report,identifier='contrary',claim=replace(report.claim,asserted_value=report.claim.asserted_value+1))
        with self.assertRaises(ValueError):repair_objectives(summary,{0:reports+[contrary]})

    def test_correct_number_at_wrong_scope_is_not_preserved(self):
        reports,summary=self.fixture();obj=summary[0]['summary']
        first=next(r for r in reports if r.claim.task_identifier=='objective')
        a=next(a for a in obj['assertions'] if a[0]==first.claim.key);a[0]='different_entity/objective/current'
        field=next(f for f in field_records(reports,[obj]) if f['key']==first.claim.key)
        self.assertTrue(field['omitted']);self.assertFalse(field['preserved'])
        # Foreign citation and wrong value are explicit, but no mental process is inferred.
        other=next(r for r in reports if r.claim.task_identifier=='objective' and r.claim.key!=first.claim.key)
        obj['assertions'].append([first.claim.key,other.claim.asserted_value,[other.identifier]])
        field=next(f for f in field_records(reports,[obj]) if f['key']==first.claim.key)
        self.assertTrue(field['scope_citation_mismatch'])

    def test_frozen_source_pairing_and_resume_never_resamples_malformed(self):
        config=json.loads(Path('configs/frozen/root-diagnostic-v1.json').read_text())
        config.update(name='numerical-preservation-fixture',pair_indices=[0],ordering_seed=2026101701)
        class Model:
            alias='qwen3';batch_size=32;load_seconds=0;settings={'max_output_tokens':2304}
            def __init__(self):self.calls=0
            def run(self,requests):
                self.calls+=len(requests)
                return [{'text':'malformed completed answer','finish_reason':'stop','input_tokens':10,'output_tokens':3,
                    'allocated_inference_seconds':.01,'batch_wall_seconds':.01*len(requests)} for r in requests]
        model=Model()
        with tempfile.TemporaryDirectory() as directory,patch('rep_sensitivity.models.reuse_or_load',return_value=(model,False)):
            # Self-contained archive fixture: no ignored pilot downloads, GPU,
            # or network is required to verify provenance/cache behavior.
            source=Path(directory)/'source';(source/'qwen3/calls').mkdir(parents=True)
            (source/'qwen3/scores').mkdir();pair=generate_pair('development',0,2);corpus=freeze(pair)
            (source/'pairs.json').write_text(json.dumps([pair]));(source/'manifest.json').write_text('{"fixture":true}')
            (source/'frozen-reports.json').write_text(json.dumps({pair['pair_id']:corpus}));rows=[]
            for wi in (0,1):
                for condition in ('single','exact'):
                    rs=repeat(thaw(corpus['reports'][wi]),corpus['selected'],condition,'development')
                    world=pair['worlds'][wi];summaries=[];calls=[]
                    for i,branch in enumerate(partition(rs,pair['seed'])):
                        raw=canonical(lossless_summary(branch));obj,status=parse(raw,world['tie_order'],manager=True)
                        summaries.append({'manager':i,'summary':obj,'parse_status':status})
                        calls.append({'stage':'manager'+str(i),'prompt':make_prompt(world,branch,'ordinary',role='manager'),
                            'response':{'text':raw,'finish_reason':'stop'}})
                    calls.append({'stage':'root','prompt':make_prompt(world,[],'ordinary',summaries=summaries,
                        public_registry=registry(rs),public_ancestry=ancestry_registry(rs)),
                        'response':{'text':'fixture root unused by replay','finish_reason':'stop'}})
                    hashes=[]
                    for c in calls:
                        h=digest([wi,condition,c]);c['request_hash']=h;hashes.append(h)
                        (source/'qwen3/calls'/(h+'.json.gz')).write_bytes(gzip.compress(json.dumps(c).encode()))
                    rows.append({'world':wi,'policy':'ordinary','organization':'hierarchical','condition':condition,'repetition':0,'request_hashes':hashes})
            (source/'qwen3/scores'/(pair['pair_id']+'.json')).write_text(json.dumps(rows))
            config['source_run']=str(source)
            pairs,jobs=plan(config);config['input_inventory_sha256']=digest(input_inventory(jobs))
            self.assertEqual(len(jobs),8);self.assertEqual(len({j['trial']['trial_id'] for j in jobs}),8)
            for wi in (0,1):
                selected={j['trial']['arm']:j for j in jobs if j['trial']['world']==wi}
                self.assertEqual(selected['A']['source_manager_request_hashes'],selected['C']['source_manager_request_hashes'])
                self.assertEqual(selected['B']['source_manager_request_hashes'],selected['D']['source_manager_request_hashes'])
                self.assertEqual(selected['A']['prompt'],selected['C']['prompt'])
            run(config,model,root=directory);n=model.calls
            self.assertEqual(n,8)
            score=next(Path(directory,config['name'],'qwen3','scores').glob('*.json'));before=score.read_bytes()
            self.assertTrue(all(r['operational_failure'] and not r['correct'] for r in json.loads(before)))
            run(config,model,root=directory)
            self.assertEqual(model.calls,n);self.assertEqual(score.read_bytes(),before)


if __name__=='__main__':unittest.main()
