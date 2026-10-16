"""Coarse device telemetry for accepted inference batches, with explicit coverage."""
from datetime import datetime
import csv
import io


def merge_intervals(intervals):
    merged=[]
    for start,end in sorted(set(intervals)):
        if merged and start<=merged[-1][1]:merged[-1]=(merged[-1][0],max(end,merged[-1][1]))
        else:merged.append((start,end))
    return merged


def measure_telemetry(calls,records):
    intervals=merge_intervals([(datetime.fromisoformat(r['response']['started_utc']).timestamp(),
                               datetime.fromisoformat(r['response']['started_utc']).timestamp()+r['response']['batch_wall_seconds'])
                              for r in calls if 'started_utc' in r['response']])
    samples=[]
    for row in records:
        if row['query_exit_codes'][0]!=0:continue
        try:
            fields=next(csv.reader(io.StringIO(row['gpu_csv'])))
            sample={'time':datetime.fromisoformat(row['utc']).timestamp(),
                    'vram':float(fields[1]),'utilization':float(fields[3]),'power':float(fields[4]),
                    'processes':len(row['process_csv'].splitlines()) if row['process_csv'] else 0}
            samples.append(sample)
        except (ValueError,IndexError,StopIteration):continue
    samples=sorted({s['time']:s for s in samples}.values(),key=lambda s:s['time'])
    active=[s for s in samples if any(start<=s['time']<=end for start,end in intervals)]
    joules=covered=0.0
    for a,b in zip(samples,samples[1:]):
        dt=b['time']-a['time']
        if not 0<dt<=30:continue
        for start,end in intervals:
            lo,hi=max(start,a['time']),min(end,b['time'])
            if lo>=hi:continue
            powers=[a['power']+(b['power']-a['power'])*(t-a['time'])/dt for t in (lo,hi)]
            joules+=(hi-lo)*sum(powers)/2;covered+=hi-lo
    elapsed=sum(end-start for start,end in intervals)
    return {'accepted_batch_window_seconds':elapsed,'telemetry_covered_seconds':covered,
            'temporal_coverage_fraction':covered/elapsed if elapsed else None,'active_samples':len(active),
            'sampled_peak_vram_mib':max((s['vram'] for s in active),default=None),
            'sampled_mean_gpu_utilization_percent':sum(s['utilization'] for s in active)/len(active) if active else None,
            'sampled_multiple_compute_processes':any(s['processes']>1 for s in active),
            'gross_device_energy_joules_on_covered_intervals':joules if covered else None,
            'interpretation':'Coarse nvidia-smi samples, linearly interpolated with gaps at most 30 seconds. Device energy is not incremental model energy or a kernel-time measurement. Unaccepted interrupted work is excluded.'}
