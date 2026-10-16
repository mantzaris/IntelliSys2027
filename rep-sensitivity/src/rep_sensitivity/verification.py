"""Event-boundary verifier and separately coded integer-slot reference checker."""
from .schema import ScheduleWorld

FAMILIES = ("precedence_release", "resource", "deadline_downtime", "objective")


def validate_world(w: ScheduleWorld) -> None:
    ids = [j.identifier for j in w.jobs]
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError("Jobs must have unique identifiers")
    if any(j.duration <= 0 or type(j.duration) is not int or j.release < 0 for j in w.jobs):
        raise ValueError("Positive integer durations and nonnegative releases required")
    if any(type(v) is not int or v <= 0 for v in w.capacities.values()):
        raise ValueError("Positive integer capacities required")
    for j in w.jobs:
        if set(j.demands) - set(w.capacities) or any(type(v) is not int or v < 0 for v in j.demands.values()):
            raise ValueError("Unknown resource or invalid demand")
    remaining = set(ids)
    for u, v in w.precedence:
        if u not in remaining or v not in remaining:
            raise ValueError("Unknown precedence endpoint")
    while remaining:
        ready = {v for v in remaining if not any(b == v and a in remaining for a, b in w.precedence)}
        if not ready:
            raise ValueError("Precedence graph must be acyclic")
        remaining -= ready
    cids = [c.identifier for c in w.candidates]
    if len(cids) != len(set(cids)) or set(cids) != set(w.tie_order) or len(cids) != len(w.tie_order):
        raise ValueError("Tie order must be a permutation of candidate identifiers")
    for c in w.candidates:
        if set(c.starts) != set(ids) or any(type(v) is not int or v < 0 for v in c.starts.values()):
            raise ValueError("Every job needs one nonnegative integer start")
    for resource, windows in w.downtime.items():
        if resource not in w.capacities or any(a < 0 or a >= b for a, b in windows):
            raise ValueError("Invalid downtime")


def verify(w: ScheduleWorld) -> dict:
    validate_world(w)
    values = {}
    for c in w.candidates:
        ends = {j.identifier: c.starts[j.identifier] + j.duration for j in w.jobs}
        pred = all(ends[a] <= c.starts[b] for a, b in w.precedence)
        release = all(c.starts[j.identifier] >= j.release for j in w.jobs)
        resources, peaks = {}, {}
        for r, capacity in w.capacities.items():
            events = {}
            for j in w.jobs:
                a, b, d = c.starts[j.identifier], ends[j.identifier], j.demands.get(r, 0)
                events[a] = events.get(a, 0) + d
                events[b] = events.get(b, 0) - d
            load = peak = 0
            for t in sorted(events):
                load += events[t]  # Aggregate starts/ends: intervals are half-open.
                peak = max(peak, load)
            peaks[r], resources[r] = peak, peak <= capacity
        deadline = all(j.deadline is None or ends[j.identifier] <= j.deadline for j in w.jobs)
        down = all(not (j.demands.get(r, 0) > 0 and c.starts[j.identifier] < b and a < ends[j.identifier])
                   for r, windows in w.downtime.items() for a, b in windows for j in w.jobs)
        mandatory = {"precedence_release": pred and release,
                     "deadline_downtime": deadline and down, **{"resource:" + r: v for r, v in resources.items()}}
        values[c.identifier] = {"mandatory": mandatory, "feasible": all(mandatory.values()),
                                "objective": max(ends.values()), "peaks": peaks}
    rank = {c: i for i, c in enumerate(w.tie_order)}
    feasible = [c for c, v in values.items() if v["feasible"]]
    answer = min(feasible, key=lambda c: (values[c]["objective"], rank[c])) if feasible else "NONE"
    return {"answer": answer, "candidates": values}


def reference_verify(w: ScheduleWorld) -> dict:
    """Independent discrete occupancy implementation for bounded integer worlds."""
    valid, lengths = [], {}
    checks = {}
    jobs = {j.identifier: j for j in w.jobs}
    for c in w.candidates:
        finish = {name: start + jobs[name].duration for name, start in c.starts.items()}
        horizon = max(finish.values())
        if horizon > 100000:
            raise ValueError("Reference checker restricted to small horizons")
        ok = True
        for name, start in c.starts.items():
            job = jobs[name]
            ok &= start >= job.release and (job.deadline is None or finish[name] <= job.deadline)
            for r in job.demands:
                if job.demands[r]:
                    for t in range(start, finish[name]):
                        if any(t >= a and t < b for a, b in w.downtime.get(r, [])):
                            ok = False
        for before, after in w.precedence:
            if finish[before] > c.starts[after]:
                ok = False
        for t in range(horizon):
            for r, capacity in w.capacities.items():
                occupied = sum(jobs[name].demands.get(r, 0) for name, start in c.starts.items()
                               if start <= t < finish[name])
                if occupied > capacity:
                    ok = False
        checks[c.identifier] = bool(ok)
        lengths[c.identifier] = horizon
        if ok:
            valid.append(c.identifier)
    chosen = "NONE"
    for c in w.tie_order:
        if c in valid and (chosen == "NONE" or lengths[c] < lengths[chosen]):
            chosen = c
    return {"answer": chosen, "feasible": checks, "objective": lengths}
