# Corrected fixed-event annotation: event006-v2

The 72 event IDs and evidence windows are unchanged. This version corrects missingness and separates the incoming claim from the recipient's response. The original v1 rubric, forms, code and archive remain byte-identical. See [AMENDMENTS.md](AMENDMENTS.md), including the answerer-follow-up display correction affecting eight answerer-directed items. The other 64 events are component-directed. Their response distributions must not be pooled as peer influence.

Use [review/ANNOTATOR_GUIDE.md](review/ANNOTATOR_GUIDE.md), [review/RUBRIC.md](review/RUBRIC.md), [schema](review/SCHEMA.json), and the two **blank** corrected forms. `statement_annotation_status=assessed` with no labels explicitly means none apply after reviewing the entire set. Blank status means unassessed: it provides no positive or negative evidence about any label. `unratable` requires a dimension-specific reason. Assessed uncertainty is retained as a judgment, not converted to missing. Every dimension has its own jointly assessed denominator. Primary response does not borrow statement coverage. Zero denominators produce null/unavailable metrics.

Compound incoming messages can mix factual assertions, preferences and criticism. Quote the relevant clauses in supporting_turns/notes; use existing mixed, normative_preference and uncertainty categories as the rubric specifies. Secondary recipient responses go only in `secondary_response_notes`. No new semantic taxonomy from the author worksheet is imposed on raters.

From `dualingCharacters/`:

```bash
PYTHONPATH=src:. .venv/bin/python -m supplements.results_clarity_007.review_package --output /tmp/event006-v2-review
PYTHONPATH=src:. .venv/bin/python -m supplements.results_clarity_007.ratings_v2 --check-blank --forms supplements/results_clarity_007/review/rater_1_event006_v2.csv supplements/results_clarity_007/review/rater_2_event006_v2.csv
```

Give each independent rater the same `/tmp/event006-v2-review` evidence, one blank form, and authored disjoint calibration examples. Do not give the author worksheet or interpretation documents. Their task is this fixed event packet; older episode/window forms are optional additional work, not also required. There are 72 planned events, 36 linked episodes, 12 anchor family/world/seed triplets and 11 unique families. Scheduling two actors per triplet does not create independent scenario families.

After genuine assessments, preserve each submitted CSV and provenance separately. Complete the provenance template with actual rater identifier, UTC completion time, human-assessment assertion and the SHA256 of the submitted form. Keep rubric/schema/stimulus binding hashes. Do not infer or transfer labels from v1 forms. Then:

```bash
PYTHONPATH=src:. .venv/bin/python -m supplements.results_clarity_007.ratings_v2 --forms /path/rater1.csv /path/rater2.csv --provenance /path/provenance1.json /path/provenance2.json --output /path/new-independent-agreement.json
```

The command rejects duplicate/unknown/missing planned IDs, incompatible label/status combinations, unknown labels, wrong hashes, non-independent provenance and existing output paths. It retains all rows and reason fields; it reports planned, assessed, unratable, unassessed, jointly assessed and excluded items per dimension and route, exact agreement, and label-specific positive/negative agreement with explicit numerators/denominators. A recorded provenance assertion does not authenticate a person's identity: the author must verify its origin. Adjudication must be stored separately and never substituted for either independent submission.

No human ratings were found in the supplied historical forms. Blank templates yield no research agreement result. Tests contain explicitly synthetic labels solely to exercise software; these are outside all research tables. Author review still needs two actual independent assessments, calibration record, missingness-aware agreement and separately preserved adjudication. Revised rubric decisions during calibration require a new recorded version before held-out assessment.
