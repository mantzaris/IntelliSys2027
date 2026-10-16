import copy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from rep_sensitivity.schema import Candidate, Claim, Job, Report, ScheduleWorld, digest
from rep_sensitivity.verification import verify, reference_verify, validate_world
from rep_sensitivity.generation import generate, generate_pair, oracle
from rep_sensitivity.reports import make_reports, freeze, thaw, repeat, scope_consolidate, registry, render, deduplicate
from rep_sensitivity.graphs import partition, build_graphs
from rep_sensitivity.policies import make_prompt
from rep_sensitivity.metrics import parse, probability_metrics, score_assertions
from rep_sensitivity.storage import Ledger, immutable_json
from rep_sensitivity.replay import prepare, execute_requests
from rep_sensitivity.analysis import bootstrap, repetition_values
from rep_sensitivity.controls import corrupt_ancestry, semantic_inventory, lineage_edges, packaging, unique_clause_control, superseded_reports, decision_from_claims
from rep_sensitivity.assignments import assign, access_view, coverage


class IntegrityTests(unittest.TestCase):
    def example(self, capacity):
        return ScheduleWorld([Job('A',2,{'m':1}),Job('B',2,{'m':1}),Job('C',1,{'n':1})],
            {'m':capacity,'n':1}, [('A','C'),('B','C')],
            [Candidate('P',{'A':0,'B':0,'C':2}),Candidate('Q',{'A':0,'B':2,'C':4})], ['P','Q'])

    def test_requested_capacity_example(self):
        self.assertEqual(verify(self.example(1))['answer'],'Q')
        self.assertEqual(verify(self.example(2))['answer'],'P')

    def test_boundary_and_downtime(self):
        w=self.example(1)
        self.assertTrue(verify(w)['candidates']['Q']['feasible'])
        self.assertTrue(verify(replace(w,downtime={'m':[(4,6)]}))['candidates']['Q']['feasible'])
        self.assertFalse(verify(replace(w,downtime={'m':[(3,4)]}))['candidates']['Q']['feasible'])

    def test_precedence_release_deadline(self):
        w=self.example(2)
        self.assertFalse(verify(replace(w,jobs=[Job('A',2,{'m':1},release=1),*w.jobs[1:]]))['candidates']['P']['feasible'])
        self.assertFalse(verify(replace(w,jobs=[*w.jobs[:2],Job('C',1,{'n':1},deadline=2)]))['candidates']['P']['feasible'])
        bad=replace(w,candidates=[Candidate('P',{'A':0,'B':0,'C':1})],tie_order=['P'])
        self.assertEqual(verify(bad)['answer'],'NONE')

    def test_ties_and_none(self):
        w=self.example(2)
        w=replace(w,candidates=[Candidate('P',w.candidates[0].starts),Candidate('Q',w.candidates[0].starts)],tie_order=['Q','P'])
        self.assertEqual(verify(w)['answer'],'Q')
        self.assertEqual(verify(replace(w,downtime={'m':[(0,100)]}))['answer'],'NONE')

    def test_cycle_and_invalid_input(self):
        with self.assertRaises(ValueError): verify(replace(self.example(2),precedence=[('A','B'),('B','A')]))
        with self.assertRaises(ValueError): verify(replace(self.example(2),capacities={'m':0,'n':1}))

    def test_every_generated_pair_and_reference(self):
        for split,n in [('development',24),('validation',36),('heldout',192),('live',24)]:
            for p in generate(split,n):
                ev=p['evaluation']
                self.assertTrue(ev['changed_fields'])
                self.assertEqual(ev['decision_changed'],ev['oracle'][0]['answer']!=ev['oracle'][1]['answer'])
                self.assertEqual([oracle(w) for w in p['worlds']],ev['oracle'])

    def test_matched_capacity_controls_and_benchmark_version(self):
        for split,n in [('development',24),('validation',36),('heldout',192),('live',24)]:
            for p in generate(split,n,benchmark_version=2):
                self.assertEqual([oracle(w) for w in p['worlds']],p['evaluation']['oracle'])
                self.assertNotEqual(p['pair_id'],generate_pair(split,p['index'])['pair_id'])
                if p['evaluation']['family']=='numeric':
                    edits=p['evaluation']['changed_fields']
                    self.assertEqual(len(edits),1)
                    self.assertEqual({edits[0]['before'],edits[0]['after']},{1,2})
                    if not p['evaluation']['decision_changed']:
                        self.assertEqual(p['evaluation']['affected_predicates'],[])

    def test_shared_claim_unique_clause_and_versions(self):
        counts={'decisive':0,'harmless':0}
        for p in generate('development',24,2):
            for world in p['worlds']:
                reports=make_reports(world,'development',p['seed'])
                self.assertEqual(decision_from_claims(world,reports),oracle(world)['answer'])
                for relevance in counts:
                    high,a=unique_clause_control(world,reports,'development',relevance+'_high',p['seed'])
                    low,b=unique_clause_control(world,reports,'development',relevance+'_low',p['seed'])
                    if high is None:
                        self.assertIsNone(low);continue
                    counts[relevance]+=1
                    self.assertEqual(a,b)
                    self.assertEqual(semantic_inventory(high),semantic_inventory(low))
                    self.assertEqual(semantic_inventory(high),semantic_inventory(reports))
                    self.assertEqual([r.identifier for r in high],[r.identifier for r in reports])
                    target=next(r for r in high if r.identifier==a['target_report'])
                    self.assertEqual(len(target.claims()),2)
                    obj={'assertions':[[c.key,c.asserted_value,[target.identifier]] for c in target.claims()]}
                    self.assertEqual(score_assertions(obj,high)['scope_transfer_count'],0)
            if p['evaluation']['family']=='version':
                ordered=sorted(p['worlds'],key=lambda w:w['version'])
                old,current=[make_reports(w,'development',p['seed']) for w in ordered]
                admitted=superseded_reports(current,old)
                self.assertEqual(len(admitted),len(old)+len(current))
                self.assertEqual({c.effective_time_or_version for r in admitted for c in r.claims()},{'1','2'})
        self.assertTrue(all(counts.values()))

    def test_determinism_split_separation(self):
        self.assertEqual(generate('development',24),generate('development',24))
        dev=generate('development',24); val=generate('validation',36)
        self.assertFalse({p['pair_id'] for p in dev}&{p['pair_id'] for p in val})
        self.assertTrue(all(p['evaluation']['graph_pattern']=='fork_join' for p in generate('heldout',12)))

    def test_frozen_claim_preservation_and_ancestry(self):
        for p in generate('development',24):
            corpus=freeze(p)
            for world in (0,1):
                rs=thaw(corpus['reports'][world])
                for condition in ('exact','paraphrase'):
                    repeated=repeat(rs,corpus['selected'],condition,p['split'])
                    self.assertEqual(len(repeated),len(rs)+3)
                    copies=[r for r in repeated if r.parent_report_identifiers]
                    for r in copies:
                        parent=next(x for x in rs if x.identifier==r.parent_report_identifiers[0])
                        self.assertEqual(r.claim,parent.claim)
                    self.assertEqual({(r.claim.key,str(r.claim.asserted_value)) for r in repeated},
                                     {(r.claim.key,str(r.claim.asserted_value)) for r in rs})

    def test_scope_binding_and_fresh_executions(self):
        claim=Claim('resource','C1','m1','resource',True,'Boolean',source_identifiers=('s',),verification_execution_identifier='e1')
        other=replace(claim,entity_identifier='m2')
        self.assertNotEqual(claim.key,other.key)
        reports=[Report('r1',claim,'same'),Report('r2',replace(claim,verification_execution_identifier='e2'),'same'),Report('r3',other,'same')]
        groups=scope_consolidate(reports)
        self.assertEqual(len(groups),2)
        self.assertEqual(groups[0]['executions'],['e1','e2'])
        self.assertEqual(groups[0]['sources'],['s'])

    def test_no_evaluator_leak(self):
        p=generate_pair('development',0)
        rs=make_reports(p['worlds'][0],p['split'],p['seed'])
        prompt=make_prompt(p['worlds'][0],rs,'scope')
        for forbidden in ('decision_changed','oracle_choice','affected_predicates','preconditions','mutation_family'):
            self.assertNotIn(forbidden,prompt)
        for v in registry(rs).values(): self.assertNotIn('asserted_value',v)

    def test_partition_and_graph_separation(self):
        p=generate_pair('development',0); f=freeze(p)
        rs=repeat(thaw(f['reports'][0]),f['selected'],'exact','development')
        branches=partition(rs,p['seed'])
        self.assertEqual(sum(map(len,branches)),len(rs))
        for branch in branches:
            for r in branch:
                if r.parent_report_identifiers: self.assertIn(r.parent_report_identifiers[0],[x.identifier for x in branch])
        graphs=build_graphs(p['worlds'][0],rs,'hierarchical',p['seed'])
        self.assertEqual(len(graphs),5)
        self.assertFalse(any(b=='root' and a.startswith('r') for a,b in graphs['communication_access']))

    def test_output_and_scope_metrics(self):
        obj,status=parse('{"choice":"C1","probabilities":{"C1":0.8,"NONE":0.2},"assertions":[],"unresolved":[]}', ['C1','NONE'])
        self.assertEqual(status,'valid')
        self.assertAlmostEqual(probability_metrics(obj,['C1','NONE'],'C1')['brier'],0.08)
        self.assertEqual(parse('not json',['C1'])[1],'json')
        r=Report('r1',Claim('t','C1','m','p',True,'Boolean'),'text')
        self.assertEqual(score_assertions({'assertions':[[r.claim.key,False,['r1']]]},[r])['retained_count'],0)

    def test_immutable_cache_and_repetitions(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=Ledger(d)
            k0=ledger.key('prompt',{}, {'repetition':0},'root')
            k1=ledger.key('prompt',{}, {'repetition':1},'root')
            self.assertNotEqual(k0,k1)
            value={'trial_id':'t','stage':'root','response':{'text':'bad JSON'}}
            ledger.accept(k0,value)
            self.assertEqual(ledger.get(k0),value)
            with self.assertRaises(RuntimeError): ledger.accept(k0,value)
            with self.assertRaises(RuntimeError): Ledger(d)
            immutable_json(Path(d)/'immutable.json',{'a':1})
            with self.assertRaises(RuntimeError): immutable_json(Path(d)/'immutable.json',{'a':2})

    def test_resume_does_not_resample_malformed(self):
        class FakeModel:
            settings={}; batch_size=4; calls=0
            def run(self,rs):
                self.calls+=len(rs)
                return [{'text':'MALFORMED','batch_wall_seconds':0.1} for _ in rs]
        request={'prompt':'x','trial':{'trial_id':'t','pair_id':'p','repetition':0},'stage':'root'}
        with tempfile.TemporaryDirectory() as d:
            m=FakeModel(); ledger=Ledger(d)
            a=execute_requests([request],m,ledger); b=execute_requests([request],m,ledger)
            self.assertEqual(m.calls,1); self.assertEqual(a,b)

    def test_cluster_statistics_and_contrast_signs(self):
        rows=[]
        for p in ('p1','p2','p3'):
            for org in ('flat','hierarchical'):
                for cond in ('single','exact','paraphrase'):
                    for world in (0,1):
                        rows.append({'pair_id':p,'model':'m','policy':'ordinary','organization':org,
                            'repetition':0,'world':world,'condition':cond,
                            'correct':not(org=='hierarchical' and cond!='single')})
        h=repetition_values(rows,interaction=True)
        self.assertEqual(h,{'p1':1.0,'p2':1.0,'p3':1.0})
        res=bootstrap(h,{p:('family',True) for p in h},replicates=100)
        self.assertEqual((res['estimate'],res['lower'],res['upper'],res['clusters']),(1,1,1,3))
        self.assertEqual(repetition_values(rows*10,interaction=True),h)

    def test_partial_overlap_and_real_lineage_corruption(self):
        p=generate_pair('development',0); f=freeze(p)
        rs=repeat(thaw(f['reports'][0]),f['selected'],'exact','development')
        corrupted=corrupt_ancestry(rs,7)
        self.assertEqual(semantic_inventory(rs),semantic_inventory(corrupted))
        self.assertNotEqual(lineage_edges(rs),lineage_edges(corrupted))
        lo,_=packaging(rs,'development','low_overlap');hi,_=packaging(rs,'development','high_overlap')
        self.assertEqual(semantic_inventory(lo),semantic_inventory(hi))
        self.assertEqual([r.identifier for r in lo],[r.identifier for r in hi])

    def test_live_assignment_coverage_and_restricted_access(self):
        w=generate_pair('live',0)['worlds'][0]
        for policy in ('nonoverlap','exact_overlap','near_overlap'):
            tasks=assign(w,policy,'fixed')
            self.assertEqual(coverage(tasks,w)['covered_assignments'],12)
            self.assertLessEqual(sum(a.output_cap for a in tasks),4096)
            for a in tasks:
                v=access_view(w,a)
                self.assertNotIn('oracle',v);self.assertNotIn('reports',v)
                if a.family=='objective':
                    self.assertNotIn('capacities',v);self.assertNotIn('precedence',v)


if __name__=='__main__': unittest.main()
