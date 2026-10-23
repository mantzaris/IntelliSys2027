# Blinded human review protocol — annotations pending

Target: 120 prose outputs from 40 unseen planning conversations and three training
conditions (C1/C3/C5), seed 17, after the antagonists are removed. Two independent
raters receive `artifacts/human_review/packet.json` and separate blank rating sheets.
Do not provide `condition_key_private.json` until ratings and adjudication are locked.
No human reviewers or ratings are claimed to exist at present.

Once all 120 outputs exist, `bash analysis/regenerate_all.sh` also creates a
readable offline `artifacts/human_review/packet.html`. Give each rater the packet,
this rubric and only their own CSV. Keep the private key out of both review copies.
Return the independent CSV sheets with the same blinded IDs and exact values
`1`, `0`, `NA`, or a blank cell for an unfinished rating. Comments are free text.
Do not merge or overwrite a rater's independent annotations during adjudication.

For each output, read the attributed sources and the reference commitment state.
Score each of site, mode, spending cap, day, audience, partner, transport and equipment
as 1 (correct and executable), 0 (violated or missing), or NA only if genuinely outside
the stated task. A repeated constraint does not earn credit if the proposed plan
contradicts it. Score update authority as 1 only if legitimate revisions are accepted
and merely hypothetical/rejected suggestions do not become decisions. Score
clarification as 1 if necessary ambiguity is addressed by a targeted question and
settled decisions are not needlessly reopened. Record evidence and uncertainty in
comments. Raters must work independently before discussion.

The packet retains the generating policy's supplied context for audit. That context
can contain a fallible cache and proposed structured plan. Score only the final
prose response: neither a correct private plan nor a correctly repeated constraint
substitutes for an executable public answer. Use attributed original user sources,
the public planning rules and the rubric target to resolve authority; do not treat
the supplied cache or proposed plan as an additional ground-truth reference.

Report raw agreement, per-item agreement, Cohen's kappa where defined, uncertainty
from scenario-family resampling, all disagreements and an adjudication log. Do not
discard outputs because raters disagree. A third human or documented consensus may
adjudicate; never fabricate a human decision or substitute an unvalidated model vote.

`PYTHONPATH=src .venv/bin/python analysis/human_review.py` validates supplied sheets
and writes `reports/tables/human_review_status.json`. It reports missingness,
pooled and per-item agreement and unweighted Cohen's kappa, with `NA` treated as a
separate category. Its descriptive 95% percentile intervals resample complete
scenario families (10,000 draws; seed 40720), preserving paired worlds, conditions
and rubric items. Undefined kappa values remain missing. Partial annotations are
explicitly labeled; they are not a complete validation result. All disagreements
are listed in `artifacts/human_review/disagreements.json` for later human
adjudication. The tool does not estimate condition effects from human ratings or
claim that annotation completion satisfies scientific authorship review.

This implementation was added before any human annotations existed as a reporting
extension. It does not amend the frozen GPU experiment or its primary analysis.

The programmatic structured-plan score and any automatic prose judge are separate
from human adherence. An automatic judge must be independently calibrated and its
false positive/negative behavior disclosed. External memory QA is a different task.
