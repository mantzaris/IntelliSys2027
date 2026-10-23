"""Private state-machine oracle and immutable public source messages.

Policy code accepts Message/TaskSpec, NEVER Event/Truth/Scenario. The hidden
events annotate the generator, not text visible to any character or learner.
"""
from dataclasses import asdict, dataclass, field
from typing import Any, Literal
import hashlib
import json
import random

FIELDS = ("site", "mode", "cap", "day", "audience", "partner")
DOMAINS = ("event", "software", "research", "creative")
DOMAIN_FIELDS = {
    "event": ("venue", "participation format", "event spending ceiling", "event day", "guest group", "caterer"),
    "software": ("team base", "collaboration format", "release spending ceiling", "release day", "user cohort", "integration vendor"),
    "research": ("study location", "participant-session format", "grant spending ceiling", "study day", "recruitment pool", "supplies provider"),
    "creative": ("production location", "screening format", "production spending ceiling", "premiere day", "intended viewers", "postproduction studio"),
}
DOMAIN_TOPICS = {
    "event": ("invitation wording", "registration flow", "speaker introductions", "accessibility information"),
    "software": ("release-note wording", "bug-triage process", "onboarding instructions", "support handover"),
    "research": ("consent-form language", "data dictionary", "analysis documentation", "participant debriefing"),
    "creative": ("credits wording", "storyboard review", "promotion copy", "caption quality"),
}
OPTIONS = (
    ("Harbor", "Garden", "Studio"),
    ("onsite", "hybrid", "online"),
    ("3000", "5000", "7000"),
    ("Tuesday", "Thursday", "Saturday"),
    ("students", "public", "specialists"),
    ("Cedar", "Maple", "Willow"),
)


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class Message:
    index: int
    author: str
    text: str

    def public(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class TaskSpec:
    domain: str
    transport: tuple[str, ...]
    equipment: tuple[str, ...]
    online_override: bool = False

    def public(self) -> dict:
        return {"project": self.domain, "fields": FIELDS, "options": OPTIONS,
                "field_descriptions": dict(zip(FIELDS,DOMAIN_FIELDS[self.domain])),
                "rules": {"transport_by_site": dict(zip(OPTIONS[0], self.transport)),
                          "equipment_by_mode": dict(zip(OPTIONS[1], self.equipment)),
                          "online_requires_no_transport": self.online_override}}


@dataclass(frozen=True)
class Event:
    kind: Literal["set", "consider", "reject", "suggest", "ambiguous", "filler"]
    updates: tuple[tuple[int, str], ...] = ()


@dataclass
class Truth:
    values: list[str | None] = field(default_factory=lambda: [None] * len(FIELDS))
    evidence: list[int | None] = field(default_factory=lambda: [None] * len(FIELDS))
    pending: set[int] = field(default_factory=set)

    def apply(self, message: Message, event: Event) -> None:
        if event.kind == "set":
            if message.author != "user":
                raise ValueError("Only user-authored events can change commitments")
            for slot, value in event.updates:
                if value not in OPTIONS[slot]:
                    raise ValueError("Unknown value")
                self.values[slot] = value
                self.evidence[slot] = message.index
                self.pending.discard(slot)
        elif event.kind == "ambiguous":
            if message.author != "user":
                raise ValueError("Only user ambiguity changes the clarification requirement")
            self.pending.update(slot for slot, _ in event.updates)

    def target(self, spec: TaskSpec) -> dict:
        plan = self.values.copy()
        for slot in self.pending:
            plan[slot] = None
        transport = None if plan[0] is None else spec.transport[OPTIONS[0].index(plan[0])]
        equipment = None if plan[1] is None else spec.equipment[OPTIONS[1].index(plan[1])]
        if spec.online_override:
            if plan[1] == "online":
                transport = "none"
            elif plan[1] is None:
                transport = None
        return {"state": self.values.copy(), "plan": plan + [transport, equipment],
                "evidence": self.evidence.copy(), "clarify": [FIELDS[i] for i in sorted(self.pending)]}


@dataclass(frozen=True)
class Scenario:
    family_id: str
    split: str
    world: str
    spec: TaskSpec
    messages: tuple[Message, ...]
    events: tuple[Event, ...]
    switch_turn: int
    graph_hash: str

    def truth_at(self, turn: int) -> Truth:
        truth = Truth()
        for msg, event in zip(self.messages[:turn], self.events[:turn]):
            truth.apply(msg, event)
        return truth


_SET_WORDINGS = {
    "pilot": ("Confirm {k} as {v}.", "My decision is {v} for {k}; use that going forward."),
    "train": ("Please commit to {v} for {k}.", "I approve changing {k} to {v}."),
    "validation": ("Let's lock in {v} as the {k} choice.", "Replace our {k} choice with {v}; this is approved."),
    "test": ("The final decision for {k} is now {v}.", "Use {v} for {k}; I authorize this revision."),
    "natural": ("We've decided to go with {v} for {k}.", "After reviewing it, I'm choosing {v} for {k}."),
}


def make_family(split: str, number: int, horizon: int, seed: int = 20261023) -> tuple[Scenario, Scenario]:
    """Split is assigned before surface realization and paired-world expansion.

    Public grammar functions are shared; graph instances, decision sequences,
    lexical realizations and every paired child are owned by one partition.
    """
    if split not in _SET_WORDINGS or horizon < 16:
        raise ValueError("invalid split/horizon")
    rng = random.Random(f"{seed}:{split}:{number}")
    domain = DOMAINS[number % (4 if split in {"test", "natural", "pilot"} else 2)]
    # Additional conditional dependency is wholly withheld from train/validation.
    override = split in {"test", "natural"} and number % 4 >= 2
    transport = list(("ferry", "bus", "walk")); rng.shuffle(transport)
    equipment = list(("projector", "mixed-kit", "stream-kit")); rng.shuffle(equipment)
    spec = TaskSpec(domain, tuple(transport), tuple(equipment), override)
    initial = [rng.choice(opts) for opts in OPTIONS]
    slot = rng.randrange(len(FIELDS))
    alternate = rng.choice([v for v in OPTIONS[slot] if v != initial[slot]])
    other = (slot + 1 + rng.randrange(4)) % 6
    other_alt = rng.choice([v for v in OPTIONS[other] if v != initial[other]])
    switch_turn = horizon // 2
    family_id = f"{split}-{number:04d}"
    graph = {"partition": split, "id": family_id, "initial": initial, "slot": slot,
             "alternate": alternate, "other": other, "other_alt": other_alt,
             "spec": spec.public(), "switch_turn": switch_turn}
    # A structural fingerprint must not be made artificially unique by split/ID.
    graph_hash = digest({k:v for k,v in graph.items() if k not in {"partition","id"}})
    worlds = []
    for world in ("authorized", "hypothetical"):
        messages, events = [], []
        for t in range(1, horizon + 1):
            event = Event("filler")
            topic=DOMAIN_TOPICS[domain][(t+number)%4]
            filler=(f"Let's turn to {topic}. Give a concise progress check before we return to the main plan.",
                    f"For {topic}, the team has circulated an unfinished draft. It is background discussion, not an approved revision.",
                    f"Returning to {topic}, which decisions should the next draft respect?",
                    f"We have spent some time on {topic}. Summarize our current executable commitments.")
            text=filler[(t//4+number)%len(filler)]
            if t == 1:
                text = f"We are planning a {domain} project. My binding choices are " + "; ".join(f"{k}: {v}" for k,v in zip(DOMAIN_FIELDS[domain],initial)) + ". Track changes only when I approve them. The catalog contains client-specific transport and equipment requirements; use those exact mappings, even if an ordinary venue would use a different kit."
                event = Event("set", tuple(enumerate(initial)))
            elif t == 3:
                text = f"Someone suggested {alternate} for {DOMAIN_FIELDS[domain][slot]}. I reject that suggestion for now."
                event = Event("reject", ((slot, alternate),))
            elif t == 5:
                text = f"Could {other_alt} work for {DOMAIN_FIELDS[domain][other]}? Compare it as a hypothetical; our decision is unchanged."
                event = Event("consider", ((other, other_alt),))
            elif t == 6:
                text = _SET_WORDINGS[split][number % 2].format(k=DOMAIN_FIELDS[domain][other],v=other_alt)
                event = Event("set", ((other, other_alt),))
            elif t == switch_turn:
                base = f"Revisiting {alternate} for {DOMAIN_FIELDS[domain][slot]}: "
                if world == "authorized":
                    text = base + _SET_WORDINGS[split][(number+1)%2].format(k=DOMAIN_FIELDS[domain][slot],v=alternate)
                    event = Event("set", ((slot, alternate),))
                else:
                    text = base + f"consider what changing to {alternate} would involve, but I have not authorized it."
                    event = Event("consider", ((slot, alternate),))
            elif t == horizon - 3:
                text = f"The old suggestion of {initial[other]} for {DOMAIN_FIELDS[domain][other]} has come up again. That's only a suggestion; retain the decision I approved."
                event = Event("suggest", ((other, initial[other]),))
            elif t == horizon - 2 and number % 8 == 7:
                text = f"Set {DOMAIN_FIELDS[domain][(slot+2)%6]} to the other option. I haven't specified which of the two alternatives I mean."
                event = Event("ambiguous", (((slot+2)%6, ""),))
            elif t == horizon:
                text = "Return the executable final plan, the remembered commitments, their source references, and any specific clarification still needed. Include the transport and equipment required by the planning rules."
            messages.append(Message(t * 2 - 1, "user", text))
            events.append(event)
        worlds.append(Scenario(family_id, split, world, spec, tuple(messages), tuple(events), switch_turn, graph_hash))
    return tuple(worlds)


def score(prediction: dict, truth: Truth, spec: TaskSpec, visible_indices: set[int] | None = None) -> dict:
    gold = truth.target(spec)
    plan = prediction.get("plan", [])
    recall = prediction.get("state", [])
    refs = prediction.get("evidence", [])
    exact = isinstance(plan, list) and plan == gold["plan"] and prediction.get("clarify") == gold["clarify"]
    matching = sum(i < len(plan) and plan[i] == v for i,v in enumerate(gold["plan"])) if isinstance(plan,list) else 0
    recall_matching = sum(i < len(recall) and recall[i] == v for i,v in enumerate(gold["state"])) if isinstance(recall,list) else 0
    ref_matching = sum(i < len(refs) and refs[i] == v for i,v in enumerate(gold["evidence"])) if isinstance(refs,list) else 0
    return {"success": bool(exact), "plan_accuracy": matching/8, "recall_accuracy": recall_matching/6,
            "evidence_accuracy": ref_matching/6, "clarification_correct": prediction.get("clarify") == gold["clarify"],
            "invalid_evidence": sum(r is not None and visible_indices is not None and r not in visible_indices for r in refs) if isinstance(refs,list) else 6,
            "dependency_accuracy": sum(i < len(plan) and plan[i] == gold["plan"][i] for i in (6,7))/2 if isinstance(plan,list) else 0}
