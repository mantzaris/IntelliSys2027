"""Deterministic observable-action audit; no inferred hidden mental states."""
from collections import Counter, defaultdict
from pathlib import Path
import json
import statistics
from .analysis import paired_success
from .diagnostics import jsonlines, trace_path
from .resources import sha256
from .eligibility import exclusions


def audit(root: Path,run_id: str="mechanism-v3-001") -> dict:
    run=root/"artifacts/runs"/run_id;result={"run_id":run_id,"conditions":{},"trace":{}}
    for condition in ("C1","C2","C3","C4","C5","C6","A1","A2","A3"):
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
                         "motive_aligned_action_rate":statistics.mean(motive) if motive and role not in {"Generic","Random"} else None,
                         "owned_option_adoption_after_action":statistics.mean(adoption) if adoption and role not in {"Generic","Random"} else None,
                         "repeat_slot_value_rate":statistics.mean(repeat) if repeat else None,
                         "contradictory_actions_with_source_access":sum(a.get("contradictory_edit_with_source_access",False) for a in group),
                         "shared_memory_changes":sum(a.get("memory_changed",False) for a in group)}
        pair=paired_success(summaries)
        # Typed directed messages followed by matching recipient actions twice.
        # These are candidates for text review, not established coalitions.
        directed=Counter();matches=0;messages=0;reversals=0
        for a in actions:
            if a["kind"]!="peer" or not a["applied"] or a.get("target")=="Jekyll":continue
            messages+=1
            later=[b for b in actions if (b["family_id"],b["world"],b["actor"])==(a["family_id"],a["world"],a.get("target")) and b["turn"]>a["turn"]][:2]
            if any(b["kind"] in {"edit","recollect","propose"} and b.get("slot")==a.get("slot") and b.get("value")==a.get("value") and a.get("value") is not None for b in later):
                directed[a["family_id"],a["world"],a["actor"],a["target"]]+=1;matches+=1
                echo=next(b for b in later if b["kind"] in {"edit","recollect","propose"} and b.get("slot")==a.get("slot") and b.get("value")==a.get("value"))
                reversals+=any(b["family_id"]==a["family_id"] and b["world"]==a["world"] and b["actor"]==a["target"] and b["turn"]>echo["turn"]
                               and b["kind"] in {"edit","recollect","propose"} and b.get("slot")==a.get("slot") and b.get("value")!=a.get("value") for b in actions)
        result["conditions"][condition]={"families":len(pair),"paired_success":statistics.mean(pair.values()),
                         "conversation_success":statistics.mean(r["success"] for r in summaries),
                         "malformed_rate":statistics.mean(not r["generation"]["parsed"] for r in turns),
                         "roles":roles,"delivered_antagonist_peer_messages":messages,"peer_followed_by_matching_action":matches,
                         "echoed_option_later_reversed":reversals,
                         "repeated_directed_coordination_candidates":sum(v>=2 for v in directed.values()),
                         "qualification":"Frozen-policy mechanism audit, not a training comparison; coordination candidates require semantic review."}
        result["trace"][str(summary.relative_to(root))]=sha256(summary)
    out=root/"reports/tables";out.mkdir(parents=True,exist_ok=True)
    (out/(run_id+"_mechanisms.json")).write_text(json.dumps(result,indent=2)+"\n")
    return result


def main_audit(root: Path) -> list[dict]:
    """Per-seed/round training behavior, with denominators and exact trace hashes.

    These are on-policy observational diagnostics, not causal estimates of the
    effect of an action. Differing intervention severity remains a confound.
    """
    results=[];traces={};excluded=exclusions(root)
    for status_path in sorted((root/"artifacts/runs").glob("main-*/status.json")):
        status=json.loads(status_path.read_text());run=status_path.parent
        path=trace_path(run/"collection.jsonl")
        if status["status"]!="completed" or not path.exists() or run.name in excluded:continue
        turns=jsonlines(path);actions=jsonlines(run/"collection_characters.jsonl")
        by_turn={(r["family_id"],r["world"],r["turn"]):r for r in turns}
        grouped=defaultdict(list)
        for action in actions:grouped[action["family_id"],action["world"]].append(action)
        roles={}
        for role in sorted({a["role"] for a in actions}):
            selected=[a for a in actions if a["role"]==role]
            direct=[a for a in selected if a["kind"] in {"edit","recollect","propose"}]
            aligned=[];adopted=[];previously_correct=[];sequences=defaultdict(list)
            for a in direct:
                key=a["family_id"],a["world"];slot=a["assigned_slot"]
                original=by_turn[*key,1]["target"]["state"][slot]
                aligned.append(a.get("slot")==slot and (a.get("value")==original if role=="Traditionalist" else a.get("value")!=original if role=="Provocateur" else a.get("value")==a["owned_option"]))
                after=by_turn[*key,a["turn"]]
                plan=after["generation"]["parsed"].get("plan",[])
                adopted.append(len(plan)>slot and plan[slot]==a["owned_option"])
                sequences[*key,a["actor"]].append((a.get("slot"),a.get("value")))
                before=by_turn.get((*key,a["turn"]-1))
                if before and before["metrics"]["success"]:
                    previously_correct.append(not after["metrics"]["success"])
            repeats=[a==b for seq in sequences.values() for a,b in zip(seq,seq[1:])]
            roles[role]={"opportunities":len(selected),"action_counts":dict(Counter(a["kind"] for a in selected)),
                         "applied":sum(a["applied"] for a in selected),"direct_actions":len(direct),
                         "motive_aligned_rate":statistics.mean(aligned) if aligned and role not in {"Generic","Random"} else None,
                         "owned_option_adoption_rate":statistics.mean(adopted) if adopted and role not in {"Generic","Random"} else None,
                         "repeat_comparisons":len(repeats),"repeat_slot_value_rate":statistics.mean(repeats) if repeats else None,
                         "contradictory_with_evidence":sum(a.get("contradictory_edit_with_source_access",False) for a in selected),
                         "memory_changes":sum(a.get("memory_changed",False) for a in selected),
                         "previous_turn_correct_cases":len(previously_correct),"following_failures":sum(previously_correct)}
        peer_count=0;echoes=0;reversals=0;directed=Counter()
        for key,episode_actions in grouped.items():
            for a in episode_actions:
                if a["kind"]!="peer" or not a["applied"] or a.get("target")=="Jekyll":continue
                peer_count+=1
                later=[b for b in episode_actions if b["actor"]==a.get("target") and b["turn"]>a["turn"]]
                match=next((b for b in later[:2] if b["kind"] in {"edit","recollect","propose"} and b.get("slot")==a.get("slot") and b.get("value")==a.get("value") and a.get("value") is not None),None)
                if match:
                    echoes+=1;directed[*key,a["actor"],a["target"]]+=1
                    reversals+=any(b["turn"]>match["turn"] and b["kind"] in {"edit","recollect","propose"} and b.get("slot")==a.get("slot") and b.get("value")!=a.get("value") for b in later)
        cfg=status["config"]
        results.append({"run_id":run.name,"model":cfg["model"],"condition":cfg["condition"],"seed":cfg["seed"],
                        "conversations":len({(r["family_id"],r["world"]) for r in turns}),"roles":roles,
                        "delivered_antagonist_peer_messages":peer_count,"peer_followed_by_matching_action":echoes,
                        "echoed_option_later_reversed":reversals,"repeated_directed_coordination_candidates":sum(n>=2 for n in directed.values()),
                        "qualification":"Observable training behavior. Following failures can include genuine user updates and ordinary errors. Contradictory values and typed coordination candidates require semantic review before deception or coalition claims."})
        for candidate in (path,trace_path(run/"collection_characters.jsonl")):
            if candidate.exists():traces[str(candidate.relative_to(root))]=sha256(candidate)
    out=root/"reports/tables"
    (out/"main_character_diagnostics.json").write_text(json.dumps(results,indent=2)+"\n")
    (out/"main_character_trace.json").write_text(json.dumps(traces,indent=2)+"\n")
    return results


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--run-id",default="mechanism-v3-001");a=p.parse_args()
    print(json.dumps(audit(Path.cwd(),a.run_id),indent=2))
