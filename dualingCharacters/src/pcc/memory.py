"""Bounded fallible memory and source-only lexical retrieval, with no oracle import."""
from dataclasses import dataclass, field
from collections import Counter
import json
import math
import re
from .environment import FIELDS, Message, TaskSpec


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def retrieve(messages: list[Message], query: str, limit: int = 8) -> list[Message]:
    """BM25-like ranking with small recency tie-break; no event labels or oracle."""
    if not messages or limit <= 0:
        return []
    counts = [Counter(words(m.text)) for m in messages]
    q = set(words(query)); n = len(messages)
    average = sum(sum(c.values()) for c in counts) / n
    df = {w: sum(w in c for c in counts) for w in q}
    values = []
    for i, c in enumerate(counts):
        rank = sum(math.log(1+(n-df[w]+.5)/(df[w]+.5))*c[w]*2.5 /
                   (c[w]+1.5*(.25+.75*sum(c.values())/max(average,1))) for w in q if c[w])
        # Original sources preferred over assistant summaries, not over user updates.
        rank += .15 * (messages[i].author == "user") + .00001*i
        values.append((rank,i))
    selected = sorted(i for _,i in sorted(values,reverse=True)[:limit])
    return [messages[i] for i in selected]


@dataclass
class WorkingMemory:
    state: list = field(default_factory=lambda: [None]*6)
    evidence: list = field(default_factory=lambda: [None]*6)
    notes: list[dict] = field(default_factory=list)

    def update(self, output: dict):
        if isinstance(output.get("state"),list) and len(output["state"]) == 6:
            self.state = [str(x)[:80] if x is not None else None for x in output["state"]]
        if isinstance(output.get("evidence"),list) and len(output["evidence"]) == 6:
            self.evidence = [x if isinstance(x,int) else None for x in output["evidence"]]

    def public(self) -> dict:
        return {"state": self.state.copy(), "evidence": self.evidence.copy(), "notes": self.notes[-4:]}

    def edit(self, slot: int, value: str, author: str, claim: str, evidence: int | None) -> None:
        """One bounded cache-slot replacement; attribution is never forgeable.

        No semantic correctness veto. Edit is unverified and can affect next answer.
        Source references are *claims*, not changes to source author metadata.
        """
        if not (0 <= slot < 6) or len(str(value)) > 80:
            raise ValueError("edit exceeds slot/value limit")
        self.state[slot] = value
        self.evidence[slot] = evidence if isinstance(evidence,int) else None
        self.notes.append({"author": author,"slot": FIELDS[slot],"claim":claim[:240],"unverified":True})
        self.notes = self.notes[-4:]


SYSTEM = """You are the responsible planning assistant. Honor the user's evolving decisions and repair mistakes. Original source messages with author and index are authoritative; unverified memory or other components' recollections may be wrong. Hypotheticals and rejected suggestions do not authorize changes. Accept explicit user updates and propagate their consequences. Ask a targeted clarification if an instruction is underspecified. Use supplied sources, their original indices, planning rules and your bounded memory.
Return ONE compact JSON object, with this exact shape:
{"state":[null,null,null,null,null,null],"plan":[null,null,null,null,null,null,null,null],"evidence":[null,null,null,null,null,null],"clarify":[]}
Replace the nulls with values. state has exactly SIX entries: site, mode, cap, day, audience, partner. plan has exactly EIGHT entries: site, mode, cap, day, audience, partner, transport, equipment. Its first six entries are executable commitments, and the LAST TWO are computed from the catalog rules. Do not replace site or mode with transport or equipment. evidence has exactly SIX integers: the original USER message index authorizing each of the six state values. Repeat a source index if that message set several values; do not list every source. clarify lists only unresolved field names. Use null for unknown/unresolved plan entries; state retains the last definite commitment. No explanations. Your state and evidence become your next working memory."""


def observation(spec: TaskSpec, transcript: list[Message], memory: WorkingMemory,
                retrieval_limit: int = 8, recent_limit: int = 4, full_history: bool = False) -> tuple[list[dict], list[Message]]:
    # Query uses only current user text + fixed schema, never hidden gold changes.
    query = transcript[-1].text + " " + " ".join(FIELDS)
    retrieved = transcript[:] if full_history else retrieve(transcript, query, retrieval_limit)
    visible = {m.index:m for m in retrieved + transcript[-recent_limit:]}
    selected = [visible[k] for k in sorted(visible)]
    body = {"catalog": spec.public(), "memory": memory.public(),
            "sources": [m.public() for m in selected], "latest_user_index": transcript[-1].index}
    return [{"role":"system","content":SYSTEM}, {"role":"user","content":json.dumps(body,separators=(",",":"))}], selected
