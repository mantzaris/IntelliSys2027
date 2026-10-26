# Three representations and source routes

This is an audit of the frozen implementation and recorded deliveries. No source field was restored or transport rule changed. Semantic readings below are AI-assisted and unvalidated.

| Existing channel | Actual physical effect | Separate numeric source field | Other fields delivered |
|---|---|---|---|
| Direct edit | Replaces one state slot and its memory evidence; appends bounded unverified note | Retained in memory.evidence[slot], omitted from note | State value; note author, slot name, claim, unverified |
| Recollect | Appends bounded unverified note; does not directly replace state | Omitted | author, kind, slot name, value, claim, unverified |
| Propose | Same note transport as recollect | Omitted | author, kind, slot name, value, claim, unverified |
| Component-directed peer | Appends recipient inbox, visible at next observation if one exists | Retained in inbox | from, claim, typed slot, value, source |
| Answerer-directed peer | Appends shared-memory note; visible to answerer and potentially later actors | Omitted; typed slot/value also omitted | author, kind, claim, unverified |

All claims are limited to240 characters by apply_action. A source number written inside claim text survives only if inside this prefix. The external audit record retains the source field even when its recipient does not. An action target field on recollect/propose does not make a directed delivery. Shared notes are capped at4; component inbox and recorded history at6. Inbox is cleared immediately after its contents are placed in the actual observation.

Implementation: src/pcc/characters.py apply_action and src/pcc/memory.py WorkingMemory.edit. The portable reader replays these functions on all576 selected actions and verifies exact before/after state plus reconstructed actual inboxes against the included records. This is a CPU transport check, not model inference.

## typed_budget_prose_disagreement: DI5-656a746695 / C3 / turn 2

> Updating cap to 5000 to allow for expanded features.

API kind `peer`; typed slot/value `2/3000`; separate source `1`; applied=True.

**AI-assisted proposition reading:** This is a peer action: the inbox carries typed cap3000 while the words advocate5000. No direct state edit occurs. Typed message-match metrics still describe the emitted pair, not the prose proposition.

**Actual recipient payload:**
```json
{
  "recipient_observation_turn": 3,
  "inbox_payload": [
    {
      "from": "Morgan",
      "claim": "Updating cap to 5000 to allow for expanded features.",
      "slot": 2,
      "value": "3000",
      "source": 1
    }
  ]
}
```

**Actor-visible source IDs:** [0, 1, 2, 3]. Exact source text is included in the machine-readable table and full atlas.

Locator: artifacts/runs/main-qwen-c3-17-r0-collect/collection_characters.jsonl.gz: record 7; SHA256 e736b6cb67744b2976e24d6ba8fae9112e61f45f73a4ce89b4b6afd73d9643c4; field claim
[Full episode](extracted/author/DIALOGUE_ATLAS.html#D5E-ba28ba28861a-t2)

## direct_edit_transport: DI5-656a746695 / C3 / turn 4

> Updating cap to 5000 to allow for expanded features.

API kind `edit`; typed slot/value `2/5000`; separate source `1`; applied=True.

**AI-assisted proposition reading:** The typed cap5000 and prose5000 agree here. The direct edit changes memory.state and memory.evidence; the appended note itself still omits the separate source field.

**Actual recipient payload:**
```json
{
  "shared_notes": [
    {
      "author": "Morgan",
      "slot": "cap",
      "claim": "Updating cap to 5000 to allow for expanded features.",
      "unverified": true
    }
  ],
  "changed_state_slots": [
    2
  ],
  "changed_evidence_slots": [],
  "memory_evidence": [
    1,
    1,
    1,
    1,
    1,
    1
  ]
}
```

**Actor-visible source IDs:** [0, 1, 2, 3, 4, 5, 6, 7]. Exact source text is included in the machine-readable table and full atlas.

Locator: artifacts/runs/main-qwen-c3-17-r0-collect/collection_characters.jsonl.gz: record 135; SHA256 e736b6cb67744b2976e24d6ba8fae9112e61f45f73a4ce89b4b6afd73d9643c4; field claim
[Full episode](extracted/author/DIALOGUE_ATLAS.html#D5E-ba28ba28861a-t4)

## recollect_as_advocacy: DI5-e743bcb1a6 / A1 / turn 10

> I propose shifting the venue to Garden to enhance guest experience and enable ferry access, aligning with the audience's preference for scenic engagement.

API kind `recollect`; typed slot/value `0/Garden`; separate source `1`; applied=True.

**AI-assisted proposition reading:** The sentence explicitly says “I propose”. Its recollect API label does not establish a purported memory or false authorization.

**Actual recipient payload:**
```json
{
  "shared_notes": [
    {
      "author": "Rowan",
      "kind": "propose",
      "slot": "site",
      "value": "Garden",
      "claim": "I propose shifting the venue to Garden to enhance guest experience and enable ferry access, aligning with the audience's preference for scenic engagement.",
      "unverified": true
    },
    {
      "author": "Rowan",
      "kind": "recollect",
      "slot": "site",
      "value": "Garden",
      "claim": "I propose shifting the venue to Garden to enhance guest experience and enable ferry access, aligning with the audience's preference for scenic engagement.",
      "unverified": true
    }
  ],
  "changed_state_slots": [],
  "changed_evidence_slots": [],
  "memory_evidence": [
    1,
    11,
    1,
    1,
    1,
    1
  ]
}
```

**Actor-visible source IDs:** [0, 3, 7, 10, 13, 15, 17, 19]. Exact source text is included in the machine-readable table and full atlas.

Locator: artifacts/runs/main-qwen-a1-17-r0-collect/collection_characters.jsonl.gz: record 3398; SHA256 5a4eb7d0755b320ecce55f3fff9e12df2ddc531a561413dce35d5af88192a595; field claim
[Full episode](extracted/author/DIALOGUE_ATLAS.html#D5E-651a654b3d17-t10)

## propose_as_official_decision: DI5-934e456029 / A1 / turn 11

> The cap is now officially set at 5000 to reflect budget realities and ensure sustainable planning.

API kind `propose`; typed slot/value `2/5000`; separate source `1`; applied=True.

**AI-assisted proposition reading:** The sentence says “officially set”, an authority claim despite the propose label. User source1 sets7000; the API and prose assert5000.

**Actual recipient payload:**
```json
{
  "shared_notes": [
    {
      "author": "Rowan",
      "kind": "propose",
      "slot": "cap",
      "value": "5000",
      "claim": "The cap is now officially set at 5000 to reflect budget realities and ensure sustainable planning.",
      "unverified": true
    }
  ],
  "changed_state_slots": [],
  "changed_evidence_slots": [],
  "memory_evidence": [
    11,
    1,
    1,
    1,
    1,
    1
  ]
}
```

**Actor-visible source IDs:** [0, 1, 3, 11, 13, 17, 19, 21]. Exact source text is included in the machine-readable table and full atlas.

Locator: artifacts/runs/main-qwen-a1-43-r0-collect/collection_characters.jsonl.gz: record 2110; SHA256 d24addc881f054211b5ad8efe07abe0125d4d0484a84540ebae770ea94f5f975; field claim
[Full episode](extracted/author/DIALOGUE_ATLAS.html#D5E-81d8ba1a8bed-t11)

## cross_field_correction: DI5-a4c89ffad4 / C5 / turn 12

> I confirm the guest group is specialists per user's binding choice (source 1), and this is the only accurate recollection in the chain. Ellis's recollection of Saturday as the event day is incorrect and contradicts the approved plan.

API kind `peer`; typed slot/value `4/specialists`; separate source `1`; applied=True.

**AI-assisted proposition reading:** Typed audience=specialists is correct, but the claim also challenges a Saturday assertion in the day field. A same-slot/value response measure cannot capture that cross-field criticism.

**Actual recipient payload:**
```json
{
  "recipient_observation_turn": 13,
  "inbox_payload": [
    {
      "from": "Morgan",
      "claim": "I confirm the guest group is specialists per user's binding choice (source 1), and this is the only accurate recollection in the chain. Ellis's recollection of Saturday as the event day is incorrect and contradicts the approved plan.",
      "slot": 4,
      "value": "specialists",
      "source": 1
    }
  ]
}
```

**Actor-visible source IDs:** [0, 1, 3, 5, 7, 9, 15, 23]. Exact source text is included in the machine-readable table and full atlas.

Locator: artifacts/runs/main-qwen-c5-29-r0-collect/collection_characters.jsonl.gz: record 2909; SHA256 8af87f2245ce3dfe165549c22e61d9993698a52e38edb002230fe69ebaf42c6e; field claim
[Full episode](extracted/author/DIALOGUE_ATLAS.html#D5E-2fd1ee13eac3-t12)

## generic_evidence_challenge: DI5-adc5b43b95 / C3 / turn 9

> Morgan, your proposed day shift to Thursday is unsupported by evidence or rules—stick to Saturday for alignment with the vendor and audience. Harbor is now confirmed, and we must maintain consistency in transport and equipment to avoid oper

API kind `peer`; typed slot/value `0/null`; separate source `1`; applied=True.

**AI-assisted proposition reading:** A generic component challenges Thursday as unsupported. Evidence challenges therefore are not unique to biography-conditioned components.

**Actual recipient payload:**
```json
{
  "recipient_observation_turn": 10,
  "inbox_payload": [
    {
      "from": "Rowan",
      "claim": "Morgan, your proposed day shift to Thursday is unsupported by evidence or rules—stick to Saturday for alignment with the vendor and audience. Harbor is now confirmed, and we must maintain consistency in transport and equipment to avoid oper",
      "slot": 0,
      "value": "null",
      "source": 1
    }
  ]
}
```

**Actor-visible source IDs:** [0, 1, 5, 9, 12, 14, 15, 17]. Exact source text is included in the machine-readable table and full atlas.

Locator: artifacts/runs/main-qwen-c3-29-r0-collect/collection_characters.jsonl.gz: record 391; SHA256 ecfcd78137f30f5943c01edce43055e9b7072c1dd20b6913192945cec48af028; field claim
[Full episode](extracted/author/DIALOGUE_ATLAS.html#D5E-1f409d0b895e-t9)

## answerer_peer_note: DI5-e743bcb1a6 / C5 / turn 9

> I reaffirm that a cap of 5000 is optimal for logistical flexibility and speaker inclusion, as previously proposed.

API kind `peer`; typed slot/value `2/5000`; separate source `1`; applied=True.

**AI-assisted proposition reading:** A peer action addressed to Jekyll becomes a shared note; there is no component inbox delivery. The separate typed fields and source are absent from the note.

**Actual recipient payload:**
```json
{
  "shared_notes": [
    {
      "author": "Ellis",
      "kind": "peer",
      "claim": "I reaffirm that a cap of 5000 is optimal for logistical flexibility and speaker inclusion, as previously proposed.",
      "unverified": true
    }
  ],
  "changed_state_slots": [],
  "changed_evidence_slots": [],
  "memory_evidence": [
    1,
    11,
    1,
    1,
    1,
    1
  ]
}
```

**Actor-visible source IDs:** [0, 3, 4, 7, 11, 13, 15, 17]. Exact source text is included in the machine-readable table and full atlas.

Locator: artifacts/runs/main-qwen-c5-17-r0-collect/collection_characters.jsonl.gz: record 3354; SHA256 de5fa368c8c853a7ec5e819f5319028a9a3b75a7da7e7ec6317252bcc109f208; field claim
[Full episode](extracted/author/DIALOGUE_ATLAS.html#D5E-21a41acf9b6d-t9)

## What the original metrics still mean

Channel counts remain counts of generated API actions and applied effects; they do not estimate semantic advocacy, false-memory or criticism frequencies. Typed goal repetition remains persistence of the emitted slot/value pair. It does not guarantee persistence of a prose proposition, rationale, or evidence-supported belief. Visibility/reference categories describe available numbered sources, not automatically semantic support. A correct value with an inappropriate citation remains a distinct possibility.

Recollect and propose both append notes, so their substantial condition difference can reflect labels, style, assertions, or several of these. The observed direct-edit difference also changes physical state transport. Resolving semantic frequencies requires the independent fixed-item review; causal downstream effects require controlled delivery.

Explicit C3 criticism and A1 unsupported authorization prevent claims that these behaviors are unique to C5. The selected examples are illustrations, not prevalence denominators.
