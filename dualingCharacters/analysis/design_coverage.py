"""Data-only coverage audit; no policy outputs, exclusions or experiment changes."""
from pathlib import Path
from collections import defaultdict
import json
from pcc.environment import make_family
from pcc.freeze import verify_freeze
from pcc.resources import sha256
from pcc.study_analysis import write_csv


def regenerate(root: Path):
    plan=verify_freeze(root)["plan"];cells=defaultdict(lambda:{"families":0,"clarification_families":0})
    pairing=defaultdict(lambda:{"families":0,"identical_final_behavioral_targets":0,"ambiguous_controlled_update_slot":0})
    specifications=[("test",i,64) for i in range(plan["test_families"])]
    for r in plan["rounds"]:
        specifications.extend(("train",i,r["horizon"]) for i in range(r["start_family"],r["start_family"]+r["families"]))
    # The original frozen natural-validation function uses the first twenty
    # paired families (forty conversations), from a larger released manifest.
    specifications.extend(("natural",i,64) for i in range(20))
    for partition,number,horizon in specifications:
        family,paired=make_family(partition,number,horizon)
        cell=cells[partition,family.spec.domain,family.spec.online_override]
        cell["families"]+=1;cell["clarification_families"]+=any(e.kind=="ambiguous" for e in family.events)
        left=family.truth_at(horizon).target(family.spec);right=paired.truth_at(horizon).target(paired.spec)
        slot=family.events[family.switch_turn-1].updates[0][0]
        pairing[partition]["families"]+=1
        pairing[partition]["identical_final_behavioral_targets"]+=int((left["plan"],left["clarify"])==(right["plan"],right["clarify"]))
        pairing[partition]["ambiguous_controlled_update_slot"]+=int(left["plan"][slot] is None)
    rows=[{"partition":p,"domain":d,"structural_holdout":s,**v} for (p,d,s),v in sorted(cells.items())]
    result={"classification":"Post-baseline data-only design audit; no outcome-based changes",
        "qualification":"Decision-approval phrase banks and graph instances are partitioned; public conversation grammar is shared. Clarification cases are concentrated in particular domain/structure cells, so these are not fully orthogonal factors.",
        "counts":rows,"paired_world_identifiability":dict(pairing),"source_hashes":{name:sha256(root/name) for name in ("src/pcc/environment.py","src/pcc/validation.py","configs/freeze.json","analysis/design_coverage.py")}}
    out=root/"reports/tables";(out/"design_coverage.json").write_text(json.dumps(result,indent=2)+"\n")
    write_csv(out/"design_coverage.csv",rows)
    print(json.dumps(rows))


if __name__=="__main__":regenerate(Path(__file__).resolve().parents[1])
