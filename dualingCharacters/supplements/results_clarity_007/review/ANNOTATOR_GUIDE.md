# Annotator guide — corrected fixed-event packet

1. Open the supplied REVIEW.html offline. Read CALIBRATION_V2.md and RUBRIC.md. The same event IDs/windows are used for both raters; do not select another exchange.
2. Work only in your assigned `rater_*_event006_v2.csv`. Keep all 72 rows. The columns group six familiar dimensions: response, incoming statement labels, correctness, citation, authority and visibility. Added status/reason columns record missingness, not new semantic tasks.
3. Attempt the primary recipient response for every item. Set its status to assessed and choose a response, or unratable with a specific reason. Blank means not yet assessed. Give supporting turn/source IDs.
4. Assess the other dimensions as available. The optional incoming-label set can remain blank/not_assessed. To record that **no labels apply after considering every label**, set statement_annotation_status=assessed and leave statement_labels empty. These are different decisions.
5. Keep secondary recipient-response readings in secondary_response_notes. Incoming statement_labels concerns the selected claim. For compound messages, identify the clauses in notes; do not force factual audience claims, recommendations and criticism into one assertion.
6. Use uncertain for a completed but uncertain judgment. Use unratable only when assessment cannot be made, with a dimension-specific reason. Preserve missingness rather than guessing.
7. Save your original CSV and complete the accompanying provenance template with your real rater identifier, UTC completion time and completed-form SHA256. Do not alter the supplied selection/stimulus/rubric/schema hashes. Preserve independent labels before any adjudication.

You need not also complete the old full-episode/window packets. All examples and measurements concern synthetic scripted conversations, not real human participants. The author repository contains AI interpretations and condition keys and must not be used as the blinded stimulus. Style and routing can still reveal a condition; record concerns without attempting to identify it.

A spreadsheet can widen or hide unused columns; do not rename/delete them. Use literal status/label strings from the rubric. No field is prefilled with a judgment. The validator rejects malformed combinations and old v1 forms; it never fills missing labels.
