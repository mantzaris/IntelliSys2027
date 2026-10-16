"""Common information/output contract; policies differ only in instructions."""
from .schema import canonical
from .reports import registry
from copy import deepcopy

POLICIES = {
    "ordinary": "Synthesize the supplied reports and make the required decision. Emit the explicit findings supporting your synthesis.",
    "checklist": "Before deciding, account for each required predicate for each candidate. Record missing or conflicting results. Require all mandatory predicates to pass, then compare objectives. Emit the findings in your coverage checklist.",
    "scope": "Account for each required predicate. Consolidate equivalent claims only when candidate, entity, predicate, condition and version agree. Shared ancestry means copies add no independent evidence. Preserve separate verification executions and all distinct scopes, unique clauses and exceptions. Keep unresolved conflicts explicit. A challenge requires examination, not an automatic veto. A timestamp overrides earlier information only under an explicit update rule. Resolve mandatory constraints before comparing objectives. Emit the retained findings.",
}
CONTRACT = ('Return only one JSON object in this field order: "assertions", "unresolved", "candidate_assessments", "choice", "probabilities". No Markdown fences. '
            'For a final decision, choice is a candidate ID, NONE, or INSUFFICIENT. '
            'Probabilities map every candidate ID and NONE to numbers in [0,1] summing to 1; '
            'use {} only when insufficient information. '
            'Each assertion is an object {"key": "scope_key", "value": true, "reports": ["report_ID"]}. '
            'The example true is a placeholder, not a finding. Boolean predicates use true/false, never PASS/FAIL strings; '
            'objective values are numbers, never task names. Use the scope keys in the registry for key, and report IDs for reports. '
            'unresolved is a list of scope keys with missing/conflicting information. '
            'candidate_assessments lists each candidate with fields candidate, all_mandatory_pass, objective. '
            'all_mandatory_pass is true only if EVERY required Boolean finding for that candidate is true; '
            'it is false if ANY is false, and null if unknown. objective is the numerical reported objective or null if unknown. '
            'Choose the candidate with the smallest objective AMONG those whose all_mandatory_pass is true. '
            'Do not provide private reasoning or extra prose. An intermediate summary uses candidate_assessments=[], choice=null and probabilities={}.')

OUTPUT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "assertions": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "properties": {"key": {"type": "string"}, "value": {"type": ["boolean", "number"]},
                           "reports": {"type": "array", "items": {"type": "string"}}},
            "required": ["key", "value", "reports"]}},
        "unresolved": {"type": "array", "items": {"type": "string"}},
        "candidate_assessments": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "properties": {"candidate": {"type": "string"}, "all_mandatory_pass": {"type": ["boolean", "null"]},
                           "objective": {"type": ["number", "null"]}},
            "required": ["candidate", "all_mandatory_pass", "objective"]}},
        "choice": {"type": ["string", "null"]},
        "probabilities": {"type": "object", "additionalProperties": {"type": "number"}}
    }, "required": ["assertions", "unresolved", "candidate_assessments", "choice", "probabilities"]
}

# The same fields have role-appropriate types, fixed for every aggregation policy.
# These constraints contain no finding values or choice labels.
MANAGER_OUTPUT_SCHEMA=deepcopy(OUTPUT_SCHEMA)
MANAGER_OUTPUT_SCHEMA['properties']['choice']={'type':'null'}
MANAGER_OUTPUT_SCHEMA['properties']['probabilities']={'type':'object','maxProperties':0}
MANAGER_OUTPUT_SCHEMA['properties']['candidate_assessments']={'type':'array','maxItems':0}


def task_header(world):
    metric = "makespan (maximum completion time)" if world["kind"] == "schedule" else "cost"
    return (f"Select the minimum-{metric} feasible candidate from the supplied set, not a global optimum. "
            f"A report with task_identifier objective gives the candidate's numerical {metric}; lower is better. "
            "Every other task reports a mandatory Boolean constraint. PASS means true and FAIL means false. "
            "Feasibility requires EVERY mandatory Boolean predicate to be true. Any mandatory failure rules out that candidate; "
            "a favorable objective cannot compensate. If none is feasible, answer NONE. "
            "If necessary evidence is absent or an unresolved contradiction prevents selection, answer INSUFFICIENT. "
            "First minimize the numerical objective among feasible candidates. ONLY for equal objective values, choose the earliest candidate in this priority order: " + canonical(world["tie_order"]) + ". "
            "For schedules, execution is non-preemptive with half-open intervals [start,start+duration). ")


def make_prompt(world, reports, policy, role="root", summaries=None, ancestry=True,
                public_registry=None, extra_evidence=None, public_ancestry=None):
    reg = public_registry if public_registry is not None else registry(reports)
    instructions = task_header(world) + "\n" + POLICIES[policy] + "\n" + CONTRACT
    if role == "manager":
        instructions = ("Your role is intermediate manager: summarize only the received findings. The decision rule below is for the root.\n"+
                        instructions+"\nDo not choose a final candidate or assess whole-candidate feasibility. Use candidate_assessments=[], choice=null, probabilities={}. The root will see your summary and the scope registry, not the raw reports.")
    payload = {"scope_registry": reg, "reports": [r.visible(ancestry) for r in reports]}
    if summaries is not None: payload["intermediate_summaries"] = summaries
    if ancestry and public_ancestry is not None: payload["report_ancestry_registry"] = public_ancestry
    if extra_evidence is not None: payload["authoritative_task_data"] = extra_evidence
    return instructions + "\nINPUT\n" + canonical(payload)
