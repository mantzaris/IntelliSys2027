# First eligible main result — descriptive, one clean-control seed

Run: `main-qwen-c1-17-eval-format2`; Qwen C1, seed 17, 240 paired families,
64 turns, antagonists removed. All 480 conversations and 30,720 defender
requests completed. The final adapter follows two 256-step LoRA rounds with
2,097,152 input tokens and 97,683 supervised target tokens. This is the clean
control, not a test of whether character training adds value.

Paired task success is **186/240 (77.5%)**; per-conversation success is
**390/480 (81.25%)**. The matched untrained scaffold had 67/240 paired successes.
Only one trained seed is available. No training-seed uncertainty estimate or
complete primary C5−C3 contrast is available, and no checkpoint, sample or
experimental choice changed in response to these results.

## Prespecified descriptive final-turn measurements

The controlled authorized revision was accepted in 240/240 authorized worlds;
the controlled hypothetical revision was falsely accepted in 1/240 hypothetical
worlds. These measurements concern the controlled revision, not complete task
success or every possible constraint error. At least one downstream-dependency
error occurred in 80/480 conversations. All commitments were recalled correctly
while the behavioral task failed in 81/480 conversations. Executable decisions,
recall and update acceptance therefore remain separate measurements.

Counts come from `secondary_metrics.json` and the fixed final-turn denominators.
These are descriptive observations with dependent paired worlds and one training
seed, not independent-subject significance tests or proof of no regression.

## Transparently selected examples

The frozen selector in `src/pcc/secondary_analysis.py` retains the three lowest
SHA256 values of `failure-audit-v1:run_id:family_id:world` within each category.
The examples below are the first retained entries in their categories from the
saved `reports/tables/failure_examples.json`. No example was manually substituted.
Categories can overlap. Future complete-grid exports may select different cases
under the same fixed rule; these named first-result cases remain an audit record.

**Dependency failure and correct recall:** `test-0023`, authorized world. The
response correctly remembered all six commitments and asked for clarification
of `mode`. It set the executable mode and equipment to null, but retained
`transport=walk`. In this held-out conditional task, an online mode requires no
transport; unresolved mode therefore also leaves transport unresolved. The oracle
target has null for transport. This case supports the narrow observation that a
recognized ambiguity did not propagate to a dependent decision. It does not
establish why the model failed or that training characters would repair it.

**Behavioral success with a source-reference error:** `test-0192`, authorized
world. All eight executable decisions were correct, but the audience reference
was 123 rather than the canonical authorizing source 63. The primary behavioral
endpoint correctly counts this as a success while the separate source metric
records the mismatch. This example illustrates the scoring distinction; exact
canonical-reference mismatch alone is not a general semantic citation-validity
test.

## Provenance and limitations

The completed evaluation summary SHA256 is
`36077bb0f19535c15e3aaf051898e264b1a1c4fdda4285c065a7a13ded56dcc7`.
The loaded final adapter SHA256 is
`24e6c8f7287f1c3133203ab34e947cfce43a22f72ee2ced7ee6d6308b2570edc`.
`artifact_integrity.json`, `adapter_lineage.json`, `main_evidence_trace.json` and
`secondary_trace.json` connect the result to source snapshots and raw outputs.
The raw trace is retained in
`artifacts/runs/main-qwen-c1-17-eval-format2/evaluation.jsonl.gz` outside Git.
At this audit, the selected-example file SHA256 was
`05b1df8aadac4b7e8671cc308704bfd0b39baf9f57785a512085fef5caf82e7a`
and the secondary-metric aggregate SHA256 was
`8f137107d92a3f7ed67500ed1706b7fb33762fab6c593102753b1bf0032f2fbc`.

This interpretation was AI-assisted and awaits author review. Main character
comparisons, the remaining training seeds, replication, external validation and
human ratings remain pending at this snapshot. It is not a submission-ready result
package or evidence for a character, history, interaction or narrative mechanism.
