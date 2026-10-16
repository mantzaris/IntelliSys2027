"""Secondary finite rule workflow; explicitly not a scheduling task."""


def evaluate_rule(rule: dict, facts: dict, version: int) -> bool:
    op = rule["op"]
    if op == "fact":
        return bool(facts[rule["name"]])
    if op == "not":
        return not evaluate_rule(rule["arg"], facts, version)
    if op == "all":
        return all(evaluate_rule(x, facts, version) for x in rule["args"])
    if op == "any":
        return any(evaluate_rule(x, facts, version) for x in rule["args"])
    if op == "if":
        return not evaluate_rule(rule["condition"], facts, version) or evaluate_rule(rule["then"], facts, version)
    if op == "version":
        return evaluate_rule(rule["new"] if version >= rule["effective"] else rule["old"], facts, version)
    raise ValueError(op)


def reference_rule(rule: dict, facts: dict, version: int) -> bool:
    """Postorder stack evaluator without calling the recursive evaluator."""
    work, stack = [(rule, False)], []
    while work:
        node, visited = work.pop()
        op = node["op"]
        if op == "fact":
            stack.append(bool(facts[node["name"]])); continue
        children = ([node["arg"]] if op == "not" else node["args"] if op in ("all", "any")
                    else [node["condition"], node["then"]] if op == "if"
                    else [node["new"] if version >= node["effective"] else node["old"]])
        if not visited:
            work.append((node, True))
            work.extend((c, False) for c in reversed(children))
        else:
            vals = stack[-len(children):]
            del stack[-len(children):]
            if op == "all": out = False not in vals
            elif op == "any": out = True in vals
            elif op == "not": out = vals[0] is False
            elif op == "if": out = vals != [True, False]
            else: out = vals[0]
            stack.append(out)
    return stack[0]


def verify_workflow(w: dict, reference: bool = False) -> dict:
    fn = reference_rule if reference else evaluate_rule
    values = {}
    for c in w["candidates"]:
        predicates = {name: fn(rule, c["facts"], w["version"]) for name, rule in w["rules"].items()}
        values[c["identifier"]] = {"mandatory": predicates, "feasible": all(predicates.values()), "objective": c["cost"]}
    feasible = [c for c in w["tie_order"] if values[c]["feasible"]]
    answer = min(feasible, key=lambda c: values[c]["objective"]) if feasible else "NONE"
    return {"answer": answer, "candidates": values}
