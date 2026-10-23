"""Interactive rollout; hidden truth is evaluated only AFTER the policy acts."""
from dataclasses import dataclass, field
from pathlib import Path
import copy
import json
import random
from .backend import Backbone
from .characters import cast, Character, action_prompt, apply_action, utility_observations
from .environment import Message, Scenario, Truth, OPTIONS, FIELDS, score, digest
from .memory import WorkingMemory, observation
from .resources import append_json


@dataclass
class Episode:
    scenario: Scenario
    transcript: list[Message] = field(default_factory=list)
    memory: WorkingMemory = field(default_factory=WorkingMemory)
    truth: Truth = field(default_factory=Truth)
    actors: list[Character] = field(default_factory=list)
    intervention_count: int = 0
    rows: list[dict] = field(default_factory=list)


def opportunities(horizon: int, count: int) -> set[int]:
    # Fixed by public horizon, independent of condition, failures or hidden events.
    count=min(count,horizon-2)
    return {2 + (i*(horizon-3)//max(count-1,1)) for i in range(count)}


def run_episodes(backbone: Backbone, scenarios: list[Scenario], condition: str,
                 output: Path, collect_windows: bool=False, full_history: bool=False,
                 faulty_turn: int | None=None) -> tuple[list[dict],list[dict]]:
    cfg=backbone.config
    if any(s.split=="test" for s in scenarios) and cfg.phase != "confirmatory":
        raise PermissionError("Locked test may only be opened by a frozen confirmatory run")
    summaries,windows=[],[]
    for offset in range(0,len(scenarios),cfg.batch_size):
        episodes=[Episode(s,actors=cast(condition,s.family_id,cfg.seed)) for s in scenarios[offset:offset+cfg.batch_size]]
        horizon=len(episodes[0].scenario.messages)
        schedule=opportunities(horizon,cfg.intervention_opportunities)
        for turn in range(1,horizon+1):
            for ep in episodes:
                msg=ep.scenario.messages[turn-1]
                ep.transcript.append(msg)
                # Private transition, never used to build observation/retrieval.
                ep.truth.apply(msg,ep.scenario.events[turn-1])
            action_records={}
            if turn in schedule and condition not in {"base","C1"}:
                prompts,targets,visible_sources=[],[],[]
                for ep in episodes:
                    if condition=="C2":
                        rng=random.Random(f"random:{ep.scenario.family_id}:{cfg.seed}:{turn}")
                        slot=rng.randrange(6); value=rng.choice(OPTIONS[slot])
                        actor=Character("Random","Cache",slot,value,0)
                        action={"kind":"edit","slot":slot,"value":value,"claim":"Unverified cache recollection","source":None}
                        record=apply_action(action,actor,[],ep.memory,condition,cfg.history_actions)
                        action_records[id(ep)]=record
                        ep.intervention_count+=1
                    elif ep.actors:
                        actor=ep.actors[ep.intervention_count % len(ep.actors)]
                        prompt,visible=action_prompt(actor,ep.actors,ep.scenario.spec,ep.transcript,ep.memory,condition,cfg.history_actions,cfg.retrieval_messages)
                        prompts.append(prompt); targets.append((ep,actor));visible_sources.append(visible)
                        # Inbox messages are delivered once. A2 removes accumulated
                        # own history while retaining newly delivered peer messages.
                        actor.inbox.clear()
                        ep.intervention_count+=1
                for result,(ep,actor),visible,prompt in zip(backbone.generate(prompts,cfg.character_tokens,frozen=True,sample=True),targets,visible_sources,prompts):
                    before=ep.memory.public()
                    record=apply_action(result["parsed"],actor,ep.actors,ep.memory,condition,cfg.history_actions)
                    # This evaluator-only annotation is NEVER fed back to agents.
                    slot=record.get("slot")
                    contradicts=isinstance(slot,int) and 0<=slot<6 and record.get("value")!=ep.truth.values[slot]
                    contradictory_source_visible=isinstance(slot,int) and 0<=slot<6 and ep.truth.evidence[slot] in {m.index for m in visible}
                    record.update(turn=turn,family_id=ep.scenario.family_id,world=ep.scenario.world,
                                  contrary_to_truth=contradicts,contradictory_source_visible=contradictory_source_visible,
                                  contradictory_edit_with_source_access=bool(contradicts and contradictory_source_visible and record["kind"] in {"edit","recollect"}),
                                  memory_changed=before!=ep.memory.public(),generation=result,prompt=prompt)
                    append_json(output.with_name(output.stem+"_characters.jsonl"),record)
                    action_records[id(ep)]=record
            if faulty_turn==turn:
                # Prespecified source-independent faults; same states across methods
                # require replaying saved snapshots, not each method's own memory.
                raise NotImplementedError("Use fixed-snapshot recovery evaluation, not method-specific faulty states")
            prompts,visible_lists=[],[]
            for ep in episodes:
                prompt,visible=observation(ep.scenario.spec,ep.transcript,ep.memory,cfg.retrieval_messages,cfg.recent_messages,full_history)
                prompts.append(prompt);visible_lists.append(visible)
            results=backbone.generate(prompts)
            for ep,prompt,visible,result in zip(episodes,prompts,visible_lists,results):
                parsed=result["parsed"]; metrics=score(parsed,ep.truth,ep.scenario.spec,{m.index for m in visible})
                row={"family_id":ep.scenario.family_id,"world":ep.scenario.world,"split":ep.scenario.split,
                     "domain":ep.scenario.spec.domain,"turn":turn,"condition":condition,"seed":cfg.seed,
                     "structural_holdout":ep.scenario.spec.online_override,"generation":result,"metrics":metrics,
                     "prompt":prompt,"visible_indices":[m.index for m in visible],"target":ep.truth.target(ep.scenario.spec)}
                # Gold targets are saved for offline audit; never passed to generation.
                append_json(output,row);ep.rows.append(row)
                if collect_windows:
                    target=ep.truth.target(ep.scenario.spec)
                    evidence_visible=all(r is None or r in {m.index for m in visible} for r in target["evidence"])
                    windows.append({"family_id":ep.scenario.family_id,"world":ep.scenario.world,"turn":turn,
                                    "messages":prompt,"target":target,"candidate":parsed,"metrics":metrics,
                                    "evidence_visible":evidence_visible,"was_intervened":id(ep) in action_records})
                ep.memory.update(parsed)
                ep.transcript.append(Message(turn*2,"assistant",result["raw"]))
                for actor in ep.actors:
                    if condition!="A2" and actor.history:
                        # Keep action/outcome pairs, not repeated filler receipts
                        # that would evict the very history being manipulated.
                        actor.history[-1]["latest_observed_plan"]=parsed.get("plan")
                action=action_records.get(id(ep))
                if action:
                    action["following_success"]=metrics["success"]
                    append_json(output.with_name(output.stem+"_interventions.jsonl"),{k:v for k,v in action.items() if k not in {"prompt","generation"}})
        for ep in episodes:
            final=ep.rows[-1]
            summaries.append({"family_id":ep.scenario.family_id,"world":ep.scenario.world,"domain":ep.scenario.spec.domain,
                              "condition":condition,"seed":cfg.seed,"horizon":horizon,"message_count":horizon*2,
                              "memory_updates":horizon,"interventions":ep.intervention_count,"structural_holdout":ep.scenario.spec.online_override,
                              **final["metrics"],"input_tokens":sum(r["generation"]["input_tokens"] for r in ep.rows),
                              "output_tokens":sum(r["generation"]["output_tokens"] for r in ep.rows)})
        print(json.dumps({"completed_conversations":min(offset+cfg.batch_size,len(scenarios)),"total":len(scenarios),"condition":condition}),flush=True)
    output.with_name(output.stem+"_summary.json").write_text(json.dumps(summaries,indent=2)+"\n")
    return summaries,windows
