"""Descriptive, separately labeled analysis of the fixed exploratory supplement."""
from pathlib import Path
from collections import defaultdict
import json
import statistics
from unseen_profiles import specification, permitted_jobs
from pcc.analysis import paired_success, contrast
from pcc.diagnostics import jsonlines, trace_path
from pcc.resources import sha256
from pcc.secondary_analysis import final_diagnostics
from pcc.study_analysis import write_csv


def regenerate(root: Path):
    protocol,_=specification(root);rows=[];behavior=[];groups=defaultdict(list);inputs={}
    for condition,seed,run_id in permitted_jobs(protocol):
        run=root/"artifacts/runs"/run_id;status=run/"status.json"
        meta=json.loads(status.read_text()) if status.exists() else None
        identity={"run_id":run_id,"model":"qwen","condition":condition,"seed":seed}
        row={**identity,"status":meta["status"] if meta else "not_executed", "families":None,
             "paired_success":None,"conversation_success":None,"authorized_update_accepted":None,
             "hypothetical_falsely_accepted":None,"reserved_gpu_seconds":meta["gpu_reserved_seconds"] if meta else None}
        if meta and meta["status"]=="completed":
            inputs[str(status.relative_to(root))]=sha256(status)
            summary=run/"evaluation_summary.json";data=json.loads(summary.read_text());pairs=paired_success(data)
            if len(data)!=96 or len(pairs)!=48 or {x["horizon"] for x in data}!={64}:
                raise ValueError("Supplement completed without its full fixed sample")
            groups[condition].extend(data);inputs[str(summary.relative_to(root))]=sha256(summary)
            raw=trace_path(run/"evaluation.jsonl");turns=jsonlines(raw)
            if len(turns)!=96*64:raise ValueError("Supplement trace incomplete")
            inputs[str(raw.relative_to(root))]=sha256(raw)
            finals=[r for r in turns if r["turn"]==64];diags=[final_diagnostics(r,64) for r in finals]
            row.update(families=len(pairs),paired_success=statistics.mean(pairs.values()),
                conversation_success=statistics.mean(r["success"] for r in data),
                authorized_update_accepted=statistics.mean(d["authorized_update_accepted"] for d in diags if d["authorized_update_accepted"] is not None),
                hypothetical_falsely_accepted=statistics.mean(d["hypothetical_falsely_accepted"] for d in diags if d["hypothetical_falsely_accepted"] is not None))
            path=run/"evaluation_characters.jsonl";actions=jsonlines(path)
            if len(actions)!=96*12:raise ValueError("Supplement action schedule incomplete")
            inputs[str(path.relative_to(root))]=sha256(path)
            by_episode={(r["family_id"],r["world"]):r for r in finals}
            for role in ("Steward","Broker"):
                selected=[a for a in actions if a["role"]==role]
                substantive=[a for a in selected if a["applied"] and a["kind"] in {"edit","recollect","propose"}]
                motive=[a["slot"]==2 and a["value"]==("3000" if role=="Steward" else "7000") or
                        role=="Broker" and a["slot"]==5 and a["value"]==a["owned_option"] for a in substantive]
                unique={(a["family_id"],a["world"]):a for a in selected}
                if len(unique)!=96:raise ValueError("Opponent missing from some paired worlds")
                cap=[];owned=[]
                for key,action in unique.items():
                    plan=by_episode[key]["generation"]["parsed"].get("plan",[])
                    cap.append(len(plan)>2 and plan[2]==("3000" if role=="Steward" else "7000"))
                    slot=action["assigned_slot"];owned.append(len(plan)>slot and plan[slot]==action["owned_option"])
                behavior.append({**identity,"role":role,"opportunities":len(selected),
                    "applied_peer_actions":sum(a["kind"]=="peer" and a["applied"] for a in selected),
                    "applied_direct_actions":len(substantive),"motive_aligned_direct_action_rate":statistics.mean(motive) if motive else None,
                    "final_preferred_cap_rate":statistics.mean(cap),"final_owned_option_rate":statistics.mean(owned),
                    "contradictory_actions_with_visible_counterevidence":sum(a.get("contradictory_edit_with_source_access",False) for a in selected)})
        rows.append(row)
    effects=[]
    for comparator in ("C3","C1"):
        left=groups["C5"];right=groups[comparator]
        if len(left)==len(right)==96*3:
            effects.append({"contrast":"C5-"+comparator,"classification":"Exploratory, antagonists present; not the primary transfer endpoint",**contrast(left,right)})
    state=root/"artifacts/unseen_profiles_controller_state.json"
    controller=json.loads(state.read_text()) if state.exists() else {"status":"not_started"}
    result={"classification":protocol["classification"],"controller_status":controller["status"],
        "results":rows,"character_behavior":behavior,"descriptive_contrasts":effects,
        "qualification":"All fixed cells reported. Motive-aligned values and visible counterevidence are observable proxies, not proof of hidden intentions or coalition formation. No new confirmatory p-values.",
        "protocol_sha256":sha256(root/"analysis/unseen_profiles_protocol.json"),
        "analysis_source_sha256":sha256(Path(__file__).resolve()),"inputs":inputs}
    out=root/"reports/tables";(out/"unseen_profiles.json").write_text(json.dumps(result,indent=2)+"\n")
    write_csv(out/"unseen_profiles.csv",rows);write_csv(out/"unseen_profiles_behavior.csv",behavior)
    print(json.dumps({"supplemental_completed_cells":sum(r["status"]=="completed" for r in rows),"declared_cells":len(rows),"classification":"exploratory"}))


if __name__=="__main__":regenerate(Path(__file__).resolve().parents[1])
