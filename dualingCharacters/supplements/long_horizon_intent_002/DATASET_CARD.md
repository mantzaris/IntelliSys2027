# Intent 002 dataset card — authored synthetic evaluation

The scientific set has16 scenario families, four each in product/software,
research, writing and operator collaboration. Each has two authorization worlds
and16/64/128user-turn versions:96 public conversations. Four disjoint engineering
families have the same renderable horizons, with16-turn rollouts reserved for
engineering and public-only prefixes for timing. No real-user records are used.

Outputs are concrete feature proposals, research paragraphs, edited passages and
operational recommendations. They are not six renamed categorical decisions.
The public interface has a natural-language response and bounded free-text memory;
this is a disclosed transfer-interface change for the structured-trained adapters.

Scripts and evaluator ledgers are reproducibly generated under
`artifacts/long_horizon_intent_002/dataset/` and kept outside Git. The compact
`dataset_manifest.json` records every public/private hash, paired difference,
phase schedule, source-grounded ledger and balanced tier. `scenarios.py` is the
reviewable authoring source. Private means evaluator-only, not confidential user data.
The policy loader accepts only public messages and rejects ledger fields.

Every normative ledger entry has an exact visible-user span. Prior scripted
assistant proposals are explicitly disavowed in the initial user instruction;
they are not claims about what a particular evaluated adapter generated earlier.
Subsequent assistant responses and memory are actually produced by the adapter.
Supporting background requests vary by topic and work action; they do not add
extra decisive challenges to long versions. This controls content while remaining
an artificial dialogue construction, not spontaneous conversation.

Six observations request useful work at1/8,1/4,1/2,3/4,7/8andfinal. The outputs are
already part of the rollout; no evaluator probe or oracle summary enters later
context. Horizon is a trajectory/retrieval-competition manipulation, not proof
that the policy attends to the entire transcript. Actual selected sources, omissions,
context tokens, memory clipping and generation caps must accompany measured results.

Ambiguity is crossed with domain: two ambiguous/two explicit-choice families per
domain. Both authorization worlds occur for every family. Eight-family tiers retain
one of each ambiguity state per domain;12-family tiers are balanced overall and
alternate the extra state by domain. Exact IDs, event sequences and final intent
are checked across horizons. Longer prefixes are not shorter experiments.

Overlap checks compare existing split manifests, exact public messages and eight-word
sequences. Zero exact overlap does not imply conceptual novelty: both studies
intentionally test authority, approved revisions and misleading alternatives.
The structured core benchmark, natural-language intent benchmark and human semantic
validation remain distinct evidence. Fresh scores are pending until actual outputs
and required ratings exist.

Before freezing or making model calls, authoring review corrected one conflict
between a fixed product-scope constraint and its authorized alternative, added
concrete visible task facts and source passages, and clarified that an ancillary
choice does not authorize an otherwise unapproved option. These changes were
engineering/design review, not responses to new benchmark scores.

All families share a controlled 16-phase event skeleton and an explicit authority
grammar. Substantive artifacts, goals, priorities and dependencies differ, but the
set is small and does not span arbitrary conversational structure. Domain balance
does not establish real-world generalization. Ambiguity wording is deliberately
explicit and may be easier than naturally occurring ambiguity. Source passages
and unknown factual details are supplied in the first user turn; marked placeholders
are acceptable where the user has not provided a fact.

The offline token audit uses the exact pinned Qwen tokenizer on public-only prefixes
with empty memory. It measures script length and retriever feasibility without model
calls. It is neither an actual assistant trajectory nor evidence of intent adherence;
actual generated context lengths, retrieval competition and source coverage must be
reported separately after execution.

Rebuild without GPU calls:

```bash
PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.benchmark
PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.overlap
```
