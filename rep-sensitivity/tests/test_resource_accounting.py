from datetime import datetime,timezone
import unittest
from rep_sensitivity.resources import measure_telemetry


class ResourceAccountingTests(unittest.TestCase):
    def test_batches_are_not_counted_once_per_call(self):
        def utc(t):return datetime.fromtimestamp(t,tz=timezone.utc).isoformat()
        calls=[{'response':{'started_utc':utc(0),'batch_wall_seconds':10}} for _ in range(32)]
        telemetry=[{'utc':utc(t),'query_exit_codes':[0,0],
                    'gpu_csv':'GPU, 40000, 49140, 90, 100, 70','process_csv':'1, vllm, 40000'} for t in (0,5,10)]
        result=measure_telemetry(calls,telemetry)
        self.assertEqual(result['accepted_batch_window_seconds'],10)
        self.assertEqual(result['gross_device_energy_joules_on_covered_intervals'],1000)
        self.assertEqual(result['temporal_coverage_fraction'],1)
        self.assertEqual(measure_telemetry(calls,[])['gross_device_energy_joules_on_covered_intervals'],None)
