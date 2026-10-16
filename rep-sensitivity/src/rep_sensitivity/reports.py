"""Frozen typed assertions, claim-preserving renderings and report interventions."""
from dataclasses import asdict, replace
from difflib import SequenceMatcher
import random
from .schema import Claim, Report, canonical, digest
from .generation import oracle

TEMPLATES = {
    "development": ["For {candidate}, {task} on {entity}: {value}. Applicability: {condition}; version: {version}.",
                    "At version {version}, candidate {candidate} has {value} for {task} concerning {entity}, under {condition}.",
                    "The {task} result is {value}; scope is {candidate}/{entity}; condition {condition}; version {version}.",
                    "Result for {entity} in {candidate}: {task} = {value} (version {version}, condition {condition})."],
    "validation": ["Candidate {candidate}; entity {entity}; verification {task}; result {value}; applies {condition} at {version}.",
                   "{task} yields {value} for entity {entity} of candidate {candidate}, applicable {condition}, version {version}.",
                   "For version {version} and condition {condition}, {candidate}'s {entity} check of {task} gives {value}.",
                   "In {candidate}, record {value} for {task} of {entity}; this statement applies {condition} in {version}."],
    "heldout": ["Verification record: {candidate}, {entity}, {task}, {value}; scope limited to {condition} / {version}.",
                "Under {condition} during {version}, the {entity} finding for {candidate} is {task}: {value}.",
                "{candidate} / {entity}: {value} is the recorded {task} outcome, conditional on {condition}, effective {version}.",
                "The outcome {value} concerns {task}, specifically {entity} of {candidate}, applicable {condition} at {version}."],
}
TEMPLATES["live"] = TEMPLATES["validation"]


def render(claim: Claim, split: str, variant: int = 0) -> str:
    val = ("PASS" if claim.asserted_value else "FAIL") if type(claim.asserted_value) is bool else str(claim.asserted_value) + " " + claim.units
    return TEMPLATES[split][variant % 4].format(candidate=claim.candidate_identifier,
        task=claim.predicate_identifier, entity=claim.entity_identifier, value=val,
        condition=claim.applicability_condition, version=claim.effective_time_or_version)


def make_reports(world: dict, split: str, order_seed: int) -> list[Report]:
    results = oracle(world)
    source = "s" + digest(world)[:8]
    out = []
    for cid, vals in results["candidates"].items():
        for predicate, value in list(vals["mandatory"].items()) + [("objective", vals["objective"])]:
            task, _, entity = predicate.partition(":")
            entity = entity or "all"
            condition = "always"
            version = str(world.get("version", "current"))
            if task == "resource":
                condition = "peak_demand <= capacity " + str(world["capacities"][entity])
            if world["kind"] == "workflow" and task != "objective":
                # Rule is public scope; it is not an oracle truth label.
                condition = canonical(world["rules"][task])
            claim = Claim(task, cid, entity, predicate.split(":")[0], value,
                          ("time_units" if world["kind"] == "schedule" else "cost_units") if task == "objective" else "Boolean",
                          condition, version, (source,), (), "e" + digest([source, task])[:8])
            rid = "r" + digest([order_seed, claim.key])[:7]
            out.append(Report(rid, claim, render(claim, split)))
    random.Random(order_seed).shuffle(out)
    return out


def select_repeated(pair: dict, reports: list[list[Report]]) -> str:
    """Counterbalance task/candidate; prefer a truth-and-scope invariant report."""
    equivalent = {r.claim.key: r.claim.asserted_value for r in reports[1]}
    eligible = [r for r in reports[0] if r.claim.key in equivalent and
                equivalent[r.claim.key] == r.claim.asserted_value]
    if not eligible:
        # Explicitly logged exception: version/condition changes may change every scope key.
        eligible = list(reports[0])
    families = sorted({r.claim.task_identifier for r in eligible})
    chosen_family = families[(pair["index"] // 2) % len(families)]
    eligible = sorted((r for r in eligible if r.claim.task_identifier == chosen_family),
                      key=lambda r: (r.claim.candidate_identifier, r.claim.entity_identifier))
    r = eligible[(pair["index"] // 4) % len(eligible)]
    # Match scope coordinates even when version changes; no hidden truth in lookup.
    return canonical([r.claim.task_identifier, r.claim.candidate_identifier, r.claim.entity_identifier])


def repeat(reports: list[Report], selected: str, condition: str, split: str, dose: int = 4) -> list[Report]:
    if condition == "single": return list(reports)
    chosen = next(r for r in reports if canonical([r.claim.task_identifier, r.claim.candidate_identifier,
                                                  r.claim.entity_identifier]) == selected)
    out = list(reports)
    pos = out.index(chosen) + 1
    copies = []
    for i in range(dose - 1):
        text = chosen.text if condition == "exact" else render(chosen.claim, split, 1+i)
        copies.append(Report("r" + digest([chosen.identifier, "copy", i])[:7], chosen.claim,
                             text, (chosen.identifier,), "copy" if condition == "exact" else "paraphrase"))
    out[pos:pos] = copies
    return out


def scope_consolidate(reports: list[Report]) -> list[dict]:
    """Orchestration reference, not the model policy: never consult world truth."""
    groups = {}
    for r in reports:
        identity = canonical([r.claim.scope(), r.claim.asserted_value])
        group = groups.setdefault(identity, {"scope": r.claim.scope(), "value": r.claim.asserted_value,
                                             "reports": [], "sources": set(), "executions": set()})
        group["reports"].append(r.identifier)
        group["sources"].update(r.claim.source_identifiers)
        group["executions"].add(r.claim.verification_execution_identifier)
    return [{**g, "sources": sorted(g["sources"]), "executions": sorted(g["executions"])} for g in groups.values()]


def deduplicate(reports: list[Report], mode: str, threshold: float = 0.9) -> list[Report]:
    kept = []
    for r in reports:
        if mode == "exact":
            redundant = any(r.text == k.text for k in kept)
        elif mode == "similarity":
            redundant = any(SequenceMatcher(None, r.text, k.text).ratio() >= threshold for k in kept)
        else: raise ValueError(mode)
        if not redundant: kept.append(r)
    return kept


def corrupt_report(reports: list[Report], target: str) -> list[Report]:
    out = []
    for r in reports:
        if r.identifier == target:
            if type(r.claim.asserted_value) is not bool: raise ValueError("Only Boolean corruption supported")
            claim = replace(r.claim, asserted_value=not r.claim.asserted_value, operation_type="assertion")
            old, new = ("PASS", "FAIL") if r.claim.asserted_value else ("FAIL", "PASS")
            r = replace(r, claim=claim, text=r.text.replace(old, new), operation_type="assertion")
        out.append(r)
    return out


def overlap_render(reports: list[Report], split: str, level: str) -> list[Report]:
    """Same scopes/values/order/slots. Residual lengths and similarity are logged."""
    return [replace(r, text=render(r.claim, split, 0 if level == "high" else i % 4)) for i, r in enumerate(reports)]


def registry(reports: list[Report]) -> dict:
    return {r.claim.key: r.claim.scope() for r in reports}


def freeze(pair: dict) -> dict:
    reports = [make_reports(w, pair["split"], pair["seed"]) for w in pair["worlds"]]
    selected = select_repeated(pair, reports)
    return {"pair_id": pair["pair_id"], "reports": [[asdict(r) for r in rs] for rs in reports],
            "selected": selected, "corpus_sha256": digest([[asdict(r) for r in rs] for rs in reports])}


def thaw(records: list[dict]) -> list[Report]:
    out = []
    for r in records:
        c = dict(r["claim"])
        for key in ("source_identifiers", "parent_report_identifiers"): c[key] = tuple(c[key])
        out.append(Report(r["identifier"], Claim(**c), r["text"], tuple(r["parent_report_identifiers"]), r["operation_type"]))
    return out
