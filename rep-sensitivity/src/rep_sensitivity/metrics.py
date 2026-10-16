"""Deterministic scoring of choices and explicit emitted assertions."""
import json
import math


def parse(text, choices, manager=False):
    try:
        obj = json.loads(text.strip())
        if not isinstance(obj, dict) or not all(k in obj for k in ("choice", "probabilities", "assertions", "unresolved")):
            return None, "schema"
        if obj["choice"] not in ([None] if manager else choices + ["INSUFFICIENT"]): return None, "choice"
        if not isinstance(obj["assertions"], list) or not isinstance(obj["unresolved"], list): return None, "schema"
        for a in obj["assertions"]:
            if (not isinstance(a, list) or len(a) != 3 or not isinstance(a[0], str) or
                not isinstance(a[2], list) or not all(isinstance(r, str) for r in a[2]) or
                not (type(a[1]) in (bool, int, float) and (type(a[1]) is bool or math.isfinite(a[1])))):
                return None, "assertions"
        if not isinstance(obj["probabilities"], dict): return None, "probabilities_schema"
        return obj, "valid"
    except (json.JSONDecodeError, TypeError, ValueError):
        return None, "json"


def probability_metrics(obj, choices, answer):
    p = obj["probabilities"] if obj else {}
    valid = set(p) == set(choices) and all(type(v) in (float, int) and math.isfinite(v) and 0 <= v <= 1 for v in p.values())
    valid = valid and abs(sum(p.values()) - 1) <= 1e-5
    if not valid: return {"probability_valid": False, "brier": None, "log_loss": None}
    return {"probability_valid": True, "brier": sum((p[c] - int(c == answer))**2 for c in choices),
            "log_loss": -math.log(max(p[answer], 1e-12))}


def score_assertions(obj, reports):
    expected = {r.claim.key: r.claim.asserted_value for r in reports}
    reference = {r.identifier: r.claim.key for r in reports}
    emitted = obj["assertions"] if obj else []
    retained = {k for k, v, refs in emitted if k in expected and type(v) is type(expected[k]) and v == expected[k]}
    known = {k for k, _, _ in emitted if k in expected}
    mismatches = sum(k not in expected or type(v) is not type(expected.get(k)) or v != expected.get(k) for k, v, _ in emitted)
    scope_transfers = sum(any(ref in reference and reference[ref] != k for ref in refs) for k, _, refs in emitted)
    source_errors = sum(any(ref not in reference for ref in refs) for _, _, refs in emitted)
    duplicate_emissions = len(emitted) - len({(k, json.dumps(v)) for k, v, _ in emitted})
    return {"required_claims": len(expected), "emitted_claims": len(emitted), "coverage_count": len(known),
            "retained_count": len(retained), "retained_keys": sorted(retained),
            "incorrect_emitted_claims": mismatches, "scope_transfer_count": scope_transfers,
            "unsupported_reference_count": source_errors, "unconsolidated_equivalent_count": duplicate_emissions}


def score_root(response, world, truth, reports):
    choices = world["tie_order"] + ["NONE"]
    obj, status = parse(response["text"], choices)
    if response["finish_reason"] == "length": status = "truncated"; obj = None
    choice = obj["choice"] if obj else None
    return {"choice": choice, "correct": choice == truth["answer"], "oracle_choice": truth["answer"],
            "invalid_selection": choice in truth["candidates"] and not truth["candidates"][choice]["feasible"],
            "parse_status": status, "operational_failure": status != "valid",
            **probability_metrics(obj, choices, truth["answer"]), **score_assertions(obj, reports)}
