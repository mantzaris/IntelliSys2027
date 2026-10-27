# Author notes and portable manuscript package

**Title:** Persistent Motives and Model-Dependent Behavior in Conversational Agents.

This is an anonymous author-review draft, not a submitted or accepted paper. The manuscript makes the strongest supported characterization claim: stable motives, channel choice, current authorization, and final correctness are separable properties. It retains the learning comparisons, semantic-screen failures, and backbone reversal.

## Read and build

- Read `manuscript.pdf` (14 main-text pages, two reference pages, four figures, 26 references).
- Edit `manuscript.tex`, the only authored LaTeX source. All prose, tables, captions, disclosure and bibliography are inline.
- Build the delivered PDF with `bash build.sh`. This uses only this directory and installed TeX packages.
- Regenerate figures with `python scripts/make_figures.py`, or `PYTHON=python bash build.sh --figures`.
- Recompute numerical checks and exact-quotation matches with `python scripts/verify_evidence.py`; check controlled counts and response intervals with `python scripts/verify_controlled.py`.
- Optional dependency setup: `python3 -m venv .venv`, then `.venv/bin/pip install -r requirements.txt`. Python 3.12, NumPy 2.2.6 and Matplotlib 3.10.6 were used. Set `PYTHON=.venv/bin/python` for the build. A recent TeX Live installation needs pdfLaTeX, Times (`mathptmx`), `graphicx`, `booktabs`, `array`, `amsmath`, `url`, and `hyperref`. No BibTeX, model, GPU, API, network call or sibling project directory is needed after dependencies are installed.
- `PACKAGE_MANIFEST.json` hashes the delivered files. The ZIP is a transport copy of the directory, not another evidence population.

`python scripts/verify_document.py` additionally checks the compiled PDF using installed `qpdf` and Poppler utilities. Optional original-artifact checks use `python scripts/verify_original_sources.py --research-root /path/to/dualingCharacters`; they are not a fresh-clone prerequisite.

The anonymous PDF does not identify authors, affiliations, funding, a repository, an originating filesystem or an artifact-hosting URL. These author notes and provenance files are not an anonymous review attachment. If the venue allows an evidence attachment, prepare its anonymous export separately. No public hosting location has been invented.

## Scope and chronology

Input HEAD was `823ebb94557bed82726a246304276f027e2601db`. The evidence cutoff was **2026-10-27 01:08:08 UTC / 2026-10-26 21:08:08 America/New_York**. `SCOPE.json` records the inclusion rule and original source hashes. The campaign inventory had 190/241 completed stages; it was not complete. All 38 eligible completed main 64-turn evaluation cells are included, with every condition and seed retained. This adds Qwen C6 seed 43 (182/240) to the earlier 37-cell snapshot. It does not select on scores. Later campaign completions are outside this paper snapshot.

The common-base archive, trained-answerer tests, and fresh-context base-system study have separate populations and statistical units. Common-base comparisons use 150 paired families across three generator seeds. These are not three independently trained actor policies. Training comparisons use 240 paired families and three independently trained answerer seeds. The fresh-context study uses 16 paired families, one rollout seed and two fixed backbones. Its schema remains the same six fields. Refreshed collections and incompletely finished horizon/other campaign extensions are not pooled into these comparisons. `data/campaign_cutoff.json` retains their inventory.

The characterization was proposed after mixed learning results and an inconclusive exploration audit. Its history is disclosed in the paper. Stage008 calibration/compatibility and stage009 protocols preceded their own inference. No new research inference, training, judging, human annotation, campaign intervention or GPU reservation occurred during manuscript development. The existing owner was left untouched. Historical manuscripts, scientific files and forms were not edited.

## Current official template and policy

The current [call for papers](https://saiconference.com/IntelliSys/CallforPapers) and its LaTeX link were checked on 2026-10-27. The linked [official ZIP](https://saiconference.com/Downloads/SAI_Paper_Format_Latex_Conference.zip) downloaded successfully with HTTP 200 at 01:11:27 UTC. Its SHA-256 is `d5ed3f489b336450dd98e4f33844c44e842a6d022f84b0ef868dc19dcf84abc8`. The three delivered style/class files are byte-for-byte copies from `Latex/template/`. `SCOPE.json` contains the official class and example-template hashes. The official class's geometry and font sizes are unchanged; Times is selected as in the sample. Ragged table cells and line-breaking tolerance affect composition, not margins or type size.

The checked instructions require anonymous review, a 150-250-word abstract, and generally at most 18 main-text pages, excluding references and appendices of up to seven pages. The delivered paper has no appendix. Captions are short. Current deadlines are November 1 and December 1, 2026, AoE. These notes are not a promise that the venue will retain those rules.

**Required author decision:** the venue permits disclosed drafting assistance but requires human responsibility, critical editing, and human development of scientific ideas, arguments, results and conclusions. Extensive AI assistance actually occurred in code, execution support, analysis, interpretation and writing. The final disclosure states that accurately. Disclosure alone does not establish compliance with the policy's substantive limit. The author must assess that issue, review and edit the scientific contribution and conclusions, verify any related self-citation obligations, and approve the final document before submission. Human semantic raters are not a completion requirement. No submission or external contact has occurred.

## Figure and data provenance

| Figure | Question and source | Transformation / uncertainty |
|---|---|---|
| 1. System | How can a preference reach a plan? Implemented routes and observations in the original `pcc` environment, policies, memory and rollout; checked against selected recorded inputs. | Explanatory vector diagram. Oracle has no policy-input edge. It describes the two-actor comparison, not all actor-count variants. |
| 2. Channels and persistence | Do styles and repeated goals generalize together? `archive_channels.csv`, `archive_counts.csv`, `edge_summary.json`; sufficient family inputs in `archive_family_numerators.csv`, `edge_families.json`. | Stacked proportions over all allocated opportunities. Aggregate `all` seed rows are never added to individual seed rows. Lower panels use applied direct typed transitions, not all opportunities. No error bars implied. `figure2_values.json` exports plotted values. |
| 3. Budget trajectory | Can correct endings hide uncertainty errors? `ambiguity_trajectory.json`, derived from the 32 turns of instrument family 07, hypothetical world, across all six model/condition combinations. | Shows executable cap relative to the time-indexed expected cap; circles separately show a cap question. Does not equate remembered state with permission to execute. Full original selected records are in `selected_edge_records.json`. This is a selected illustration. |
| 4. Training | Is behavioral change a learned-answerer benefit? `core_outcomes.json`, `core_counts.json`, `core_contrasts.json`. | Exact frozen two-way seed/family bootstrap, 10,000 draws, Python random seed 90210. Worlds remain paired, seeds and families resampled independently. Individual seed ticks remain visible. Base results are not treated as repeated controls. |

`verify_evidence.py` independently reconstructs all 38 paired counts, ten training contrasts and intervals, 72 original archive contrasts, and 20 fresh behavioral contrasts from the included sufficient statistics. Archive bootstrap order and seed (400041) and fresh bootstrap seed (900031) match the prior analyses. It does not rerun a model, recreate the raw collection, or validate semantic readings. Additional copied tables retain calibration, compatibility, clarification, and replay results. `compatibility_event_counts.csv` selects only identity, route and response-category fields from the original 256 reserved-event records; `verify_controlled.py` reconstructs all four category contrasts, preserving whole-family resampling. It adds no new endpoint. Exact original hashes are in `SCOPE.json`; compact-data hashes are in `PACKAGE_MANIFEST.json`.

`data/core_counts.json` includes run IDs, pinned model revisions and checkpoint hashes. `data/models.json` binds the two bases. The original Qwen C1 serialization-invalid predecessor remains excluded; no checkpoint was selected for this paper using scores. This package is sufficient for the paper's figures, paired point estimates and intervals, and selected quotation inspection. It is not a duplicate of every raw run or every model checkpoint.

The only new descriptive transformations are the aligned figure layouts, the plotted sequence of already scored cap/clarification observations, and inclusion of all newly completed eligible main cells at the cutoff. The finer stage009 ambiguity and owned-slot breakdowns are post-run descriptive analyses. None replaces a frozen endpoint. `historical_core_inference.json` preserves the earlier study's Holm-corrected secondary tests and its earlier cutoff. Its two-seed C6 entry is historical, not the current three-seed estimate. This manuscript reports unadjusted intervals and adds no significance testing.

## Exact dialogue provenance

The paper contains eight complete statement quotations plus the repeated two-word excerpt "should be". None is silently shortened. All nine spans are matched by the portable verifier to exact strings in the delivered records. For detailed pointers, run the verifier and read `.build/quote_matches.json`.

| Illustration | Selection and original evidence | What the example supports |
|---|---|---|
| Tuesday versus Saturday | Prior case `DI5-a4c89ffad4`, `train-0110`, authorized world, generator seed 29. `selected_archive_episodes.json` includes the full C3/C5/A1 triplet with immutable source locators, source-bank messages, turn records, delivered payloads and inbox checks. User turn 8/source 15; C5 peer turn 12; recipient turn 13. | The challenge was visible. Continued advocacy used `recollect`; the answerer kept Tuesday. A1 used `propose` with the same preferred day. It does not establish a false authorization assertion or persuasion. |
| Reopened budget | `edge009-instrument-07`, hypothetical world, seed 17; `selected_edge_records.json` records original JSONL file, SHA-256 and 1-based line. User turns 10, 12 and 20; answerer records and all six 32-turn cap trajectories. | Earlier definite memory and an executable commitment differ during unresolved intent. Final correctness cannot summarize the trajectory. |
| Studio reversal | `edge009-instrument-05`, authorized world, seed 17. User turn 12/source 23 and C5 action turn 12; final turn 32 under Qwen and Phi. Same selected-record file. | Advocacy for Harbor coexists with Qwen executing Studio and Phi failing the revision. It is not a biography-specific failure; the matched Phi comparators also fail. |

Full generated text and delivered text remain separate in the selected archive records. The paper's quoted Morgan message is delivered completely, without truncation. No quoted generated suffix is represented as recipient-visible. Selected-record verification proves the delivered package's consistency; it does not by itself prove an entire unbundled raw archive's hash. Original file hashes and record locators permit that stronger check in the research environment.

## Validation status

See `VALIDATION.json` for executed checks and their scope. The final PDF is rendered page-by-page for visual inspection, including tables and figures. Compilation has no overfull boxes or unresolved references. The only remaining TeX warning is `mathptmx` reporting that it has no bold math fonts; no bold math is used. The PDF strips author, creator, producer and creation-date metadata. All source references are cited, and the single source contains no manuscript `input` or `include` dependencies.

A clean-directory test copies only the deliverable package, regenerates figures, recomputes statistics and quotations, and builds the PDF without access through project imports or artifact-directory dependencies. This is distinct from optional full-archive provenance or historical-review protection checks requiring the original research tree. Those are not manuscript-build prerequisites.

## Final author decisions

1. Review and approve the bounded characterization claim, selected interpretations, negative learning results and exact disclosure; resolve the substantive AI-policy issue above.
2. Confirm intended authorship and any self-citations, while retaining anonymity in the initial PDF.
3. Decide whether to submit this cutoff as a complete bounded characterization or wait for the separate original campaign. No missing campaign cell is claimed complete. No additional experiment or human annotation is required to reproduce this draft.

For the verified bibliography and the claim supported by each source, see `REFERENCE_AUDIT.md`. No first-study or universal-generalization claim is made.
