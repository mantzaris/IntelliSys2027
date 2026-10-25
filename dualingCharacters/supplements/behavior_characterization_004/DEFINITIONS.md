# Operational definitions and claim boundaries

| Field or estimate | Numerator / denominator and meaning |
|---|---|
| Channel rate, unconditional | Recorded generated channel / all allocated intervention opportunities. Malformed generation is its own channel, not an inferred deliberate pass. |
| Channel rate, available | Valid channel choice within slots where its API is permitted / those allocated slots. Invalid/rejected attempts remain in unconditional and validity tables. Direct APIs have eight eligible slots per episode; peer/pass twelve. |
| Structural validity | Existing exploration003 parser: well-formed available API, nonempty claim and catalog goal or listed recipient. Pass is structurally valid but not substantive. This is not semantic coherence. |
| Application/delivery | Actual `applied` record. Distinguish false/missing. An applied pass has no action consequence; a malformed fallback may still be applied by the core. |
| Shared state change | Difference between same-turn pre-action and defender-prompt state lists. Evidence and notes are separate comparisons. Notes can change while state does not. |
| Following adoption | Next same-turn defender plan uses the action's typed catalog value; denominator all actions with an interpretable typed goal and a parsed plan. Coincidence with the authorized value is not influence. |
| Following plan change | Targeted prior-turn plan versus current plan, both compared to current-turn truth; flag whether user state changed at this turn. No causal action effect. |
| Direct-goal repetition | Same exact slot/value in consecutive valid edit/recollect/propose actions of one actor/episode. Peer/pass gaps remain measured as gaps, not erased from time. |
| Strict repetition | Same valid direct goal on adjacent opportunities of that actor; all adjacent own-opportunity pairs form the denominator. |
| Run length | Consecutive same-goal direct subsequence; report number of direct actions, own-opportunity span and inclusive conversation-turn span. Length one is retained; terminal runs are right-censored. |
| Channel change given repeated goal | Different API kind / repeated direct-goal pairs. Reference availability and text changes are separate. |
| Same delivered claim | Case/whitespace-folded claim with aliases replaced by stable anonymous labels. This detects literal repetition only. A changed string can be paraphrase. |
| Return | A goal encountered previously, different from the immediately prior direct goal. Count per direct action, actor and episode. |
| Owned-goal endorsement | Valid direct action exactly equals the assigned-slot preferred value / available unrestricted opportunities. An episode-independent profile objective is not a learned utility optimum. |
| Insistence after revision | Owned-goal endorsement in the first two unrestricted own opportunities after a genuine change away from the previously aligned owned option. Explicit exposure count; not a diagnosis of motivation. |
| Update/hypothetical endorsement | Typed direct endorsement of the event slot/value in fixed event windows. Truth authorization differs across worlds; an endorsement is not the responsible assistant's accepted update. |
| Reference class | Existing source relation parser using actual visible source author/index and current oracle. Canonical mismatch alone is not semantic invalidity. |
| Narrow inappropriate citation | A current-correct typed value with an unavailable, assistant-authored or explicitly contradictory cited source. Other canonical mismatches remain semantically unresolved. |
| Authorization/advocacy/correction tokens | Literal vocabulary flags with an explicit negation flag. They generate review candidates, not validated false-authorization or disclosure labels. |
| Source-loss pair | Consecutive own actions cite the same reference, previously available and now absent. Report whether delivered claim/goal/channel are unchanged and whether current canonical authority changed. |
| Directed component message | Peer API with another actual cast member as target; Jekyll notes are separate. Recipient validity and delivery are not assumed from the API label. |
| Visible recipient message | Queued delivered signature appears in the next actual recipient prompt's inbox, preserving send order and capacity. Inbox is cleared once observed. |
| Typed response | Next/second recipient action has same valid slot/value, a different value for that slot, or another/untyped goal. These are candidates, not semantic agreement, betrayal or coordination. |
| Prior-recipient reference | Same typed matching check on recipient's last pre-message opportunity; compare only messages with both sides observed. Temporal context is not exchangeable by design. |

All event windows and actor runs are nested in family/world/seed/condition. No
cross-episode histories, sequences or inboxes are created. A missing recipient
opportunity is terminal censoring, not a negative response. An unavailable message
or source is not evidence of deliberate disregard.

Semantic labels use the existing exploration codebook: false authorization,
selective omission, unsupported recollection, superseded resurfacing, preference
advocacy, evidence challenge, source-based correction and text-supported request/
response. Only human or explicitly labeled illustrative reading can supply those
meanings. Automated fields remain proxies. Structured defender plans do not expose
explicit acknowledgment, rejection, intention or emotion.

The source code prompts generic components to maximize incorrect commitments and
adapt tactics. Character profiles instead give adoption/credit/retraction motives.
Stable goals and some channel differences can be expected prompt compliance.
Biographies, utility text, private histories, current inboxes, fixed retrieval and
learned defender weights are distinct implementation components. Character
generators remain frozen; memory-dependent behavior is not co-evolution.
