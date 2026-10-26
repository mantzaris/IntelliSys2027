# Fixed event-review protocol, event006-v1

This post hoc validation direction follows the existing dialogue005 readings and review findings. It is not part of the original confirmatory preregistration. It fixes stimuli before independent human ratings; it does not turn prior AI interpretations into blinded evidence.

The population remains the12 original anchor seed/family/world triplets,11 unique families. For each triplet, the actual reserved communication opportunities are grouped by scheduled actor index. Choose the lowest SHA256 of `event006-v1|case_id|actor_index|opportunity` among that actor's two reserved slots. Match the same opportunity across C3/C5/A1. This yields24 matched event sets and72 items, all available at cutoff. Outcomes, action kind, validity, delivery, response and correctness do not enter selection. After selection, all72 outputs were peer actions:64 component deliveries and8 answerer notes, all observed. No passes, rejected actions or missing first follow-ups occurred in these selected slots; the rule would have retained them. A pass, rejected action, answerer-directed note, invalid recipient or unavailable follow-up stays selected.

EVENT_SELECTION.json is the author key; reviewer IDs and order are opaque. The selected action, route, actual inbox/shared memory, last prior recipient opportunity, first and second later opportunities, current user authority, and source evidence form a fixed item. No semantic filter replaces the next opportunity with a more relevant one. Full context is linked. Both raters receive identical evidence and item IDs. Additional interesting material may be flagged in notes but does not enter the primary agreement denominator.

Use the first follow-up for the primary response class, with second follow-up as context. For answerer notes, use the same turn's answer and next turn as follow-ups. Mechanical no-message/missing-follow-up is separated from semantic nonresponse. API kinds, typed goals, actual propositions, correctness, citation support, claimed authority and visibility remain separate. The rubric contains a deterministic tie rule for overlapping response classes and optional multilabel statement annotations.

Two independent raters are required. Blank forms and authored disjoint calibration examples are supplied. Neither is a research result. Do not provide AI readings or condition keys. Blinding is limited by visible style, cast and routing. Preserve each independent form, provenance and any later adjudication separately. Do not transfer labels from older windows or expanded full episodes. Calibration-driven rubric changes require a dated revision and reissued packet; calibration never enters held-out agreement.

Report all72 planned items, jointly rated fixed items, uncertainty, unratable and missing counts. Exact response agreement includes uncertain as a category. For each label, positive agreement is2a/(2a+b+c) and negative agreement2d/(2d+b+c), with undefined denominators reported missing. Multilabel statement judgments are compared label by label. These are descriptive agreement quantities, not independent-action significance tests. Repeated families/seeds and multiple events create dependence. No semantic condition frequency has yet been validated.

## Ingestion

Preserve completed forms outside the repository templates. Fill each accompanying provenance template with actual rater ID, UTC completion time, `human_assessment=true`, source_type=independent_human, and SHA256 of the completed CSV. Existing selection/rubric hashes remain as supplied. Missing submissions remain pending.

From dualingCharacters:

```bash
PYTHONPATH=src:. python -m supplements.evidence_validation_006.ratings \
  --forms /path/to/rater1.csv /path/to/rater2.csv \
  --provenance /path/to/rater1_provenance.json /path/to/rater2_provenance.json \
  --output /path/to/new_versioned_validation.json
```

The command checks duplicate/unknown IDs, all planned rows, allowed labels, required dimensions, provenance hashes and distinct rater identities. It refuses to overwrite an existing result. It cannot independently authenticate human authorship; the provenance must be real and reviewed. No agreement is computed from AI readings. Synthetic fixtures used by unit tests stay in temporary test directories and never enter research tables.
