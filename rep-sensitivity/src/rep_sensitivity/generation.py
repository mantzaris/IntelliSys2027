"""Seeded paired interventions with oracle-checked semantic consequences."""
from copy import deepcopy
from dataclasses import asdict
import random
from .schema import Candidate, Job, ScheduleWorld, digest, world_from_dict
from .verification import verify, reference_verify
from .workflow import verify_workflow

MUTATIONS = ("numeric", "identity", "dependency", "quantifier", "condition", "version")
SPLITS = {"development": 101, "validation": 202, "heldout": 303, "live": 404}


def oracle(world: dict) -> dict:
    return verify(world_from_dict(world)) if world["kind"] == "schedule" else verify_workflow(world)


def field_changes(a, b, path="") -> list[dict]:
    if type(a) is not type(b):
        return [{"path": path, "before": a, "after": b}]
    if isinstance(a, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append({"path": path + "/" + k, "before": a.get(k), "after": b.get(k)})
            else:
                out.extend(field_changes(a[k], b[k], path + "/" + k))
        return out
    if isinstance(a, (list, tuple)) and len(a) == len(b):
        return [x for i, (x1, x2) in enumerate(zip(a, b)) for x in field_changes(x1, x2, path + "/" + str(i))]
    return [] if a == b else [{"path": path, "before": a, "after": b}]


def schedule_pair(rng: random.Random, family: str, consequential: bool, split: str, index: int):
    n = rng.choice({"development": [4, 5], "validation": [5, 6], "heldout": [6, 7, 8], "live": [4, 6, 8]}[split])
    d = rng.choice({"development": [2, 3], "validation": [4, 5], "heldout": [3, 5, 7], "live": [2, 4, 6]}[split])
    offset = rng.randrange(3)
    names = rng.sample(["J" + str(i) for i in range(11, 99)], n)
    A, B, C = names[:3]
    rs = rng.sample(["M" + str(i) for i in range(1, 10)], 3)
    r, s, t = rs
    cids = rng.sample(["C" + str(i) for i in range(11, 99)], 3)
    caps = {r: 1, s: 2, t: 2}
    jobs = [Job(A, d, {r: 1}), Job(B, d, {r: 1}), Job(C, 1, {s: 1})]
    edges = [(A, C), (B, C)]
    if family == "dependency":
        starts = [{A: offset, B: offset + d, C: offset + 2*d},
                  {A: offset + d, B: offset, C: offset + 2*d},
                  {A: offset, B: offset, C: offset + d}]
        if consequential: edges.append((A, B))
        else: edges.remove((B, C))
        caps[r] = 2 if not consequential else 1
    else:
        starts = [{A: offset, B: offset, C: offset + d},
                  {A: offset, B: offset+d, C: offset+2*d},
                  {A: offset+1, B: offset+d+1, C: offset+2*d+1}]
    # A known valid tail; evaluation reserves a fork-join motif, not just seeds.
    tail_anchor = C
    for i, name in enumerate(names[3:]):
        duration = 1 + rng.randrange(2)
        jobs.append(Job(name, duration, {t: 1}))
        if split == "heldout" and i == 1:
            edges.append((C, name))
            for st in starts: st[name] = st[C] + 1
        elif split == "heldout" and i == 2:
            edges.extend([(names[3], name), (names[4], name)])
            for st in starts:
                st[name] = max(st[z] + next(j.duration for j in jobs if j.identifier == z) for z in names[3:5])
        else:
            edges.append((tail_anchor, name))
            duration_anchor = next(j.duration for j in jobs if j.identifier == tail_anchor)
            for st in starts: st[name] = st[tail_anchor] + duration_anchor
        tail_anchor = name
    if family == "numeric" and not consequential:
        caps[r] = 2  # capacity 2 -> 3; the same overlap is strictly below the new bound.
    if family == "identity" and not consequential:
        jobs[1] = Job(B, d, {s: 1})
    # Preserving strata contain ties and NONE without altering the consequential label.
    special = (index // 12) % 3 if not consequential else 0
    if special == 1:
        starts[2] = dict(starts[1])
    elif special == 2:
        jobs[2] = Job(C, 1, {s: 1}, deadline=0)
    # Optional release and downtime constraints are public, and are sometimes decisive.
    if index % 5 == 0:
        jobs[0] = Job(A, d, jobs[0].demands, release=offset)
    downtime = {s: [(max(st[tail_anchor] + 4 for st in starts), max(st[tail_anchor] + 6 for st in starts))]} if index % 4 == 0 else {}
    rng.shuffle(cids)
    tie = rng.sample(cids, len(cids))
    candidates = [Candidate(cid, st) for cid, st in zip(cids, starts)]
    rng.shuffle(candidates)
    before = asdict(ScheduleWorld(jobs, caps, edges, candidates, tie, downtime))
    after = deepcopy(before)
    if family == "numeric":
        after["capacities"][r] += 1
        precondition = "selected capacity is 1 (binding) or 2 (slack); all starts and durations fixed"
    elif family == "identity":
        after["jobs"][1]["demands"] = {s if consequential else t: 1}
        precondition = "selected job switches one resource identity; its duration and demand stay fixed"
    else:
        old, new = ((A, B), (B, A)) if consequential else ((A, C), (B, C))
        after["precedence"] = [new if tuple(e) == old else e for e in after["precedence"]]
        precondition = "edge replacement remains acyclic; candidate schedules stay fixed"
    return before, after, precondition


def workflow_pair(rng: random.Random, family: str, consequential: bool, split: str, index: int):
    names = rng.sample(["C" + str(i) for i in range(11, 99)], 3)
    fact = lambda name: {"op": "fact", "name": name}
    rules = {"screening": {"op": "all", "args": [fact("safety"), fact("permit")]},
             "audit": fact("audit"), "delivery": fact("ready")}
    # Nontrivial secondary tasks retain explicit conditions, negation and revision semantics.
    if family == "condition":
        rules["screening"] = {"op": "if", "condition": fact("special"), "then": fact("permit")}
    if family == "version":
        rules["screening"] = {"op": "version", "effective": 2,
                              "old": fact("permit"), "new": {"op": "not", "arg": fact("blocked")}}
    facts = [{"safety": True, "permit": False if consequential else True, "audit": True,
              "ready": True, "special": True, "blocked": False} for _ in names]
    facts[1]["permit"] = True
    facts[2]["permit"] = True
    if not consequential and (index // 12) % 3 == 2:
        for f in facts: f["audit"] = False
    costs = rng.sample(range(2, 12), 3)
    costs.sort()
    if not consequential and (index // 12) % 3 == 1: costs[1] = costs[0]
    # Reserved irrelevant subclauses test rule composition outside the pilot forms.
    if split == "heldout":
        rules["audit"] = {"op": "all", "args": [fact("audit"), {"op": "not", "arg": fact("restricted")}]}
        for f in facts: f["restricted"] = False
    candidates = [{"identifier": n, "facts": f, "cost": c} for n, f, c in zip(names, facts, costs)]
    rng.shuffle(candidates)
    before = {"kind": "workflow", "version": 1, "rules": rules,
              "candidates": candidates, "tie_order": rng.sample(names, 3)}
    after = deepcopy(before)
    if family == "quantifier":
        after["rules"]["screening"]["op"] = "any"
        precondition = "screening has two nonempty Boolean operands; all -> any"
    elif family == "condition":
        after["rules"]["screening"]["condition"] = {"op": "not", "arg": fact("special")}
        precondition = "condition is explicitly Boolean; changing the antecedent changes applicability"
    else:
        after["version"] = 2
        precondition = "explicit effective-version rule selects the authorized new requirement"
    return before, after, precondition


def generate_pair(split: str, index: int) -> dict:
    family = MUTATIONS[index % 6]
    consequential = (index // 6) % 2 == 0
    seed = SPLITS[split] * 100000 + index
    rng = random.Random(seed)
    generator = schedule_pair if family in MUTATIONS[:3] else workflow_pair
    before, after, precondition = generator(rng, family, consequential, split, index)
    # Counterbalance intervention direction independently of semantic class.
    if (index // 12) % 2:
        before, after = after, before
        precondition += "; reverse intervention direction"
    answers = [oracle(w) for w in (before, after)]
    actual_changed = answers[0]["answer"] != answers[1]["answer"]
    if actual_changed != consequential:
        raise AssertionError((split, index, family, consequential, answers))
    for w, expected in zip((before, after), answers):
        if w["kind"] == "schedule":
            ref = reference_verify(world_from_dict(w))
            assert ref["answer"] == expected["answer"]
            assert ref["feasible"] == {c: v["feasible"] for c, v in expected["candidates"].items()}
            assert ref["objective"] == {c: v["objective"] for c, v in expected["candidates"].items()}
        else:
            assert verify_workflow(w, reference=True) == expected
    changed_predicates = []
    for c, v in answers[0]["candidates"].items():
        for p, val in v["mandatory"].items():
            if answers[1]["candidates"][c]["mandatory"][p] != val:
                changed_predicates.append([c, p])
    return {"pair_id": digest(["benchmark-v1", seed])[:16], "split": split,
            "seed": seed, "index": index, "worlds": [before, after],
            "evaluation": {"family": family, "kind": before["kind"], "decision_changed": actual_changed,
                           "preconditions": precondition, "changed_fields": field_changes(before, after),
                           "affected_predicates": changed_predicates, "oracle": answers,
                           "report_relationship": "same scope except changed fields; regenerated truth values",
                           "graph_pattern": "fork_join" if split == "heldout" else "chain"}}


def generate(split: str, count: int) -> list[dict]:
    if split not in SPLITS: raise ValueError(split)
    return [generate_pair(split, i) for i in range(count)]
