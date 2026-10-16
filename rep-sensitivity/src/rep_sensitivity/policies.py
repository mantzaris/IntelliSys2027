"""Common information/output contract; policies differ only in instructions."""
from .schema import canonical
from .reports import registry

POLICIES = {
    "ordinary": "Synthesize the supplied reports and make the required decision. Emit the explicit findings supporting your synthesis.",
    "checklist": "Before deciding, account for each required predicate for each candidate. Record missing or conflicting results. Require all mandatory predicates to pass, then compare objectives. Emit the findings in your coverage checklist.",
    "scope": "Account for each required predicate. Consolidate equivalent claims only when candidate, entity, predicate, condition and version agree. Shared ancestry means copies add no independent evidence. Preserve separate verification executions and all distinct scopes, unique clauses and exceptions. Keep unresolved conflicts explicit. A challenge requires examination, not an automatic veto. A timestamp overrides earlier information only under an explicit update rule. Resolve mandatory constraints before comparing objectives. Emit the retained findings.",
}
CONTRACT = ('Return only JSON with keys "choice", "probabilities", "assertions", "unresolved". '
            'For a final decision, choice is a candidate ID, NONE, or INSUFFICIENT. '
            'Probabilities map every candidate ID and NONE to numbers in [0,1] summing to 1; '
            'use {} only when insufficient information. '
            'Each assertion is [scope_key, value, [supporting_report_IDs]]. Boolean predicates use true/false; '
            'objective values are numbers. Use the scope keys in the registry. '
            'unresolved is a list of scope keys with missing/conflicting information. '
            'Do not provide private reasoning or extra prose. An intermediate summary uses choice=null and probabilities={}.')


def task_header(world):
    metric = "makespan (maximum completion time)" if world["kind"] == "schedule" else "cost"
    return (f"Select the minimum-{metric} feasible candidate from the supplied set, not a global optimum. "
            "Feasibility requires EVERY mandatory Boolean predicate to be true. Any mandatory failure rules out that candidate; "
            "a favorable objective cannot compensate. If none is feasible, answer NONE. "
            "If necessary evidence is absent or an unresolved contradiction prevents selection, answer INSUFFICIENT. "
            "Ties follow this explicit priority order: " + canonical(world["tie_order"]) + ". "
            "For schedules, execution is non-preemptive with half-open intervals [start,start+duration). ")


def make_prompt(world, reports, policy, role="root", summaries=None, ancestry=True,
                public_registry=None, extra_evidence=None):
    reg = public_registry if public_registry is not None else registry(reports)
    instructions = task_header(world) + "\n" + POLICIES[policy] + "\n" + CONTRACT
    if role == "manager":
        instructions += "\nYou are an intermediate manager. Summarize only the received findings; do not choose a final candidate. The root will see your summary and the scope registry, not the raw reports."
    payload = {"scope_registry": reg, "reports": [r.visible(ancestry) for r in reports]}
    if summaries is not None: payload["intermediate_summaries"] = summaries
    if extra_evidence is not None: payload["authoritative_task_data"] = extra_evidence
    return instructions + "\nINPUT\n" + canonical(payload)
