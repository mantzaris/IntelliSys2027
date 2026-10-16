"""Task, organization, communication, evidence, and job graphs remain distinct."""
import random


def partition(reports, seed, spread_copies=False):
    families = sorted({r.claim.task_identifier for r in reports})
    random.Random(seed).shuffle(families)
    owners = {f: i % 2 for i, f in enumerate(families)}
    branches = [[], []]
    for i, r in enumerate(reports):
        branch = owners[r.claim.task_identifier]
        if spread_copies and r.parent_report_identifiers: branch = 1-branch
        branches[branch].append(r)
    return branches


def build_graphs(world, reports, architecture, seed):
    tasks = sorted({r.claim.task_identifier for r in reports})
    branches = partition(reports, seed)
    task_graph = {"nodes": tasks + ["select"], "edges": [[t, "select"] for t in tasks]}
    if architecture == "flat":
        organization = {"nodes": tasks + ["root"], "edges": [[t, "root"] for t in tasks]}
        communication = [[r.identifier, "root"] for r in reports]
    else:
        organization = {"nodes": tasks + ["manager0", "manager1", "root"],
                        "edges": [[t, "manager" + str(i)] for i, rs in enumerate(branches)
                                  for t in sorted({r.claim.task_identifier for r in rs})] +
                                 [["manager0", "root"], ["manager1", "root"]]}
        communication = [[r.identifier, "manager"+str(i)] for i, rs in enumerate(branches) for r in rs]
        communication += [["summary0", "root"], ["summary1", "root"]]
    ancestry = []
    for r in reports:
        ancestry.extend([[p, r.identifier] for p in r.parent_report_identifiers])
        if not r.parent_report_identifiers:
            ancestry.extend([[s, r.claim.verification_execution_identifier] for s in r.claim.source_identifiers])
            ancestry.append([r.claim.verification_execution_identifier, r.identifier])
    return {"task_dependency": task_graph, "organization": organization,
            "communication_access": communication, "evidence_report_ancestry": ancestry,
            "job_precedence": world.get("precedence", [])}
