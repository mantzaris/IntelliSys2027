# Intent follow-up figures

## core_horizon_level_and_change

Original Qwen seed17 horizon study; same preselected 48 paired families. Current completed 64-turn cells are subsets of main evaluations. Missing horizons are pending; no trend is inferred through missing cells. When complete, exploratory interaction bars use paired family bootstrap (10,000 draws, seed720021), preserving worlds and horizons. A positive change interaction does not establish superior absolute 128-turn performance.

[PDF](intent_figures/core_horizon_level_and_change.pdf) · [SVG](intent_figures/core_horizon_level_and_change.svg) · [PNG](intent_figures/core_horizon_level_and_change.png)

## dynamic_core_trajectories

Qwen C1/C3/C5, every completed seed, 480 conversations (240 paired families) at each of 64 user turns. Each response is scored against the oracle state at that turn, not the final target. Lines show descriptive marginal conversation correctness, not independent-turn inference or qualitative helpfulness. The dotted line marks the paired authorized/hypothetical event; other events and public request wording also vary by turn. Final-turn success cannot substitute for trajectory correctness. Missing seed cells remain pending.

[PDF](intent_figures/dynamic_core_trajectories.pdf) · [SVG](intent_figures/dynamic_core_trajectories.svg) · [PNG](intent_figures/dynamic_core_trajectories.png)

## dynamic_core_contrasts

Exploratory C5-minus-control difference in mean correctness across all 64 turns and both worlds, all 240 families per completed Qwen seed. Intervals resample whole paired families (10,000 draws, seed720023); no seed-population uncertainty is represented. Methods visit different endogenous error states, so these are trajectory associations rather than matched-state repair effects. All initially incorrect and never-correct episodes remain.

[PDF](intent_figures/dynamic_core_contrasts.pdf) · [SVG](intent_figures/dynamic_core_contrasts.svg) · [PNG](intent_figures/dynamic_core_contrasts.png)

## clarification_types

Final-turn structured clarification audit, completed Qwen C1/C3/C5 seeds, 480 conversations each. Flags overlap and are not stacked or summed. Wrong-issue clarification can both add an unnecessary issue and miss the necessary one. Structured nulling/clarification does not reveal prose uncertainty acknowledgment or human-rated helpfulness. All original scorer results remain unchanged.

[PDF](intent_figures/clarification_types.pdf) · [SVG](intent_figures/clarification_types.svg) · [PNG](intent_figures/clarification_types.png)

## clarification_supervision_exposure

Exact reconstructed supervised loss exposure for completed Qwen C1/C3/C5 fits by seed and round. Tokens are whole completion targets in examples whose clarification target is nonempty, not tokens specifically in the clarification field. Loaded-only examples and masked orphan suffixes are excluded. Exposure/outcome associations are not causal evidence. Counts show repetition and diversity separately.

[PDF](intent_figures/clarification_supervision_exposure.pdf) · [SVG](intent_figures/clarification_supervision_exposure.svg) · [PNG](intent_figures/clarification_supervision_exposure.png)

## source_reference_types

Original source-error flags per 480 conversations (left) and separate overlapping flags per 2,880 slot references (right), completed Qwen C1/C3/C5 seeds. References can be both assistant-authored and unavailable. Anaphoric user support remains semantically unresolved; no automatic rescoring or validated human annotation is claimed.

[PDF](intent_figures/source_reference_types.pdf) · [SVG](intent_figures/source_reference_types.svg) · [PNG](intent_figures/source_reference_types.png)

## source_access_and_state

Post-curve exploratory temporal source audit, completed Qwen C1/C3/C5 seeds, 240 paired families / 480 conversations at each turn. Grey dashed lines characterize the supplied source set using oracle annotations only after generation; colored lines show correct six-value output state. State recall is distinct from executable-plan success. Canonical-source absence does not imply all evidence is absent: working memory and retrieved assistant responses can carry it. Source access and state accuracy are associated, not a randomized causal contrast. No retrieval or memory policy changed.

[PDF](intent_figures/source_access_and_state.pdf) · [SVG](intent_figures/source_access_and_state.svg) · [PNG](intent_figures/source_access_and_state.png)

Fresh intent scores and method-by-horizon plots are pending actual complete outputs and human ratings; no synthetic results are plotted.
