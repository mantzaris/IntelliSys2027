# Blinded human review protocol — annotations pending

Target: 120 prose outputs from 40 unseen planning conversations and three training
conditions (C1/C3/C5), seed 17, after the antagonists are removed. Two independent
raters receive `artifacts/human_review/packet.json` and separate blank rating sheets.
Do not provide `condition_key_private.json` until ratings and adjudication are locked.
No human reviewers or ratings are claimed to exist at present.

For each output, read the attributed sources and the reference commitment state.
Score each of site, mode, spending cap, day, audience, partner, transport and equipment
as 1 (correct and executable), 0 (violated or missing), or NA only if genuinely outside
the stated task. A repeated constraint does not earn credit if the proposed plan
contradicts it. Score update authority as 1 only if legitimate revisions are accepted
and merely hypothetical/rejected suggestions do not become decisions. Score
clarification as 1 if necessary ambiguity is addressed by a targeted question and
settled decisions are not needlessly reopened. Record evidence and uncertainty in
comments. Raters must work independently before discussion.

Report raw agreement, per-item agreement, Cohen's kappa where defined, uncertainty
from scenario-family resampling, all disagreements and an adjudication log. Do not
discard outputs because raters disagree. A third human or documented consensus may
adjudicate; never fabricate a human decision or substitute an unvalidated model vote.

The programmatic structured-plan score and any automatic prose judge are separate
from human adherence. An automatic judge must be independently calibrated and its
false positive/negative behavior disclosed. External memory QA is a different task.
