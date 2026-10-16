"""An independent checker can recover each assigned result from worker access alone."""
import unittest
from rep_sensitivity.assignments import assign,access_view
from rep_sensitivity.generation import generate
from rep_sensitivity.schema import world_from_dict
from rep_sensitivity.verification import reference_verify


class WorkerAccessTests(unittest.TestCase):
    def test_no_required_task_data_is_hidden_from_workers(self):
        for pair in generate('live_development',24,2):
            if pair['evaluation']['kind']!='schedule':continue
            for wi,world in enumerate(pair['worlds']):
                for task in assign(world,'near_overlap'):
                    view=access_view(world,task)
                    projected={k:v for k,v in view.items() if k not in ('kind','semantics')}
                    projected['jobs']=[{**j,'demands':j.get('demands',{})} for j in view['jobs']]
                    # Make absent, irrelevant constraints vacuous without using hidden truth.
                    projected.setdefault('precedence',[])
                    resources={r for j in projected['jobs'] for r in j['demands']}
                    projected.setdefault('capacities',{r:1+sum(j['demands'].get(r,0) for j in projected['jobs']) for r in resources})
                    projected['tie_order']=[c['identifier'] for c in projected['candidates']]
                    checked=reference_verify(world_from_dict(projected))
                    for cid,truth in pair['evaluation']['oracle'][wi]['candidates'].items():
                        if task.family=='objective':self.assertEqual(checked['objective'][cid],truth['objective'])
                        else:
                            keys=[task.family] if task.family!='resource' else [k for k in truth['mandatory'] if
                                k.startswith('resource:') and (task.resource is None or k=='resource:'+task.resource)]
                            self.assertEqual(checked['feasible'][cid],all(truth['mandatory'][k] for k in keys))
