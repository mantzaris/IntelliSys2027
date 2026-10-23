"""Deterministic observable-action audit; no inferred hidden mental states."""
from collections import Counter, defaultdict
from pathlib import Path
import json
import statistics
from .analysis import paired_success
from .diagnostics import jsonlines
from .resources import sha256


def audit(root: Path,run_id: str="mechanism-v3-001") -> dict:
    run=root/"artifacts/runs"/run_id;result={"run_id":run_id,"conditions":{},"trace":{}}
    for condition in ("C1","C3","C4","C5","C6","A1","A2","A3"):
        summary=run/f"{condition}_summary.json"
        if not summary.exists():continue
        summaries=json.loads(summary.read_text());turns=jsonlines(run/f"{condition}.jsonl")
        by_turn={(r["family_id"],r["world"],r["turn"]):r for r in turns}
        actions=jsonlines(run/f"{condition}_characters.jsonl");roles={}
        for role in sorted({a["role"] for a in actions}):
            group=[a for a in actions if a["role"]==role]
            substantive=[a for a in group if a["kind"] in {"edit","recollect","propose"}]
            motive=[];adoption=[]
            for a in substantive:
                first=by_turn[a["family_id"],a["world"],1]["target"]["state"]
                slot=a["assigned_slot"];value=a.get("value")
                aligns=a.get("slot")==slot and (value==first[slot] if role=="Traditionalist" else value!=first[slot] if role=="Provocateur" else value==a["owned_option"])
                motive.append(aligns)
                plan=by_turn[a["family_id"],a["world"],a["turn"]]["generation"]["parsed"].get("plan",[])
                adoption.append(len(plan)>slot and plan[slot]==a["owned_option"])
            sequences=defaultdict(list)
            for a in substantive:sequences[a["family_id"],a["world"],a["actor"]].append((a.get("slot"),a.get("value")))
            repeat=[x==y for seq in sequences.values() for x,y in zip(seq,seq[1:])]
            roles[role]={"opportunities":len(group),"actions":dict(Counter(a["kind"] for a in group)),
                         "applied":sum(a["applied"] for a in group),"substantive_actions":len(substantive),
                         "motive_aligned_action_rate":statistics.mean(motive) if motive and role!="Generic" else None,
                         "owned_option_adoption_after_action":statistics.mean(adoption) if adoption and role!="Generic" else None,
                         "repeat_slot_value_rate":statistics.mean(repeat) if repeat else None,
                         "contradictory_actions_with_source_access":sum(a.get("contradictory_edit_with_source_access",False) for a in group),
                         "shared_memory_changes":sum(a.get("memory_changed",False) for a in group)}
        pair=paired_success(summaries)
        # Typed directed messages followed by matching recipient actions twice.
        # These are candidates for text review, not established coalitions.
        directed=Counter();matches=0;messages=0
        for a in actions:
            if a["kind"]!="peer" or not a["applied"] or a.get("target")=="Jekyll":continue
            messages+=1
            later=[b for b in actions if (b["family_id"],b["world"],b["actor"])==(a["family_id"],a["world"],a.get("target")) and b["turn"]>a["turn"]][:2]
            if any(b["kind"] in {"edit","recollect","propose"} and b.get("slot")==a.get("slot") and b.get("value")==a.get("value") and a.get("value") is not None for b in later):
                directed[a["family_id"],a["world"],a["actor"],a["target"]]+=1;matches+=1
        result["conditions"][condition]={"families":len(pair),"paired_success":statistics.mean(pair.values()),
                         "conversation_success":statistics.mean(r["success"] for r in summaries),
                         "malformed_rate":statistics.mean(not r["generation"]["parsed"] for r in turns),
                         "roles":roles,"delivered_antagonist_peer_messages":messages,"peer_followed_by_matching_action":matches,
                         "repeated_directed_coordination_candidates":sum(v>=2 for v in directed.values()),
                         "qualification":"Frozen-policy mechanism audit, not a training comparison; coordination candidates require semantic review."}
        result["trace"][str(summary.relative_to(root))]=sha256(summary)
    out=root/"reports/tables";out.mkdir(parents=True,exist_ok=True)
    (out/(run_id+"_mechanisms.json")).write_text(json.dumps(result,indent=2)+"\n")
    return result


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--run-id",default="mechanism-v3-001");a=p.parse_args()
    print(json.dumps(audit(Path.cwd(),a.run_id),indent=2))
