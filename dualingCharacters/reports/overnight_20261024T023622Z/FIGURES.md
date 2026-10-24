# Figure captions and provenance

## paired_success

Antagonist-free 64-turn paired success, 240 families per model/condition/seed. Each point is one actual seed; diamonds are the single untrained reference. No seed-error bars are invented. Counts show completed/planned trained seeds; missing cells are pending. C1: clean; C2: random corruption; C3: generic adversaries; C4/C5/C6: two/three/five total characters; A1: motive-only; A2: private history removed; A3: peer interaction removed.

[PDF](figures/paired_success.pdf) · [SVG](figures/paired_success.svg) · [PNG](figures/paired_success.png)

## paired_contrasts

Individual-seed contrasts on common 240 paired families, 64 turns. Bars are exploratory family-bootstrap 95% intervals (10,000 draws, seed 40721). They do not capture training-seed variation; an interval containing zero is not equivalence. Complete planned-seed inference uses the separate frozen two-way analysis.

[PDF](figures/paired_contrasts.pdf) · [SVG](figures/paired_contrasts.svg) · [PNG](figures/paired_contrasts.png)

## rule_structure

Separate familiar versus held-out conditional rules, 120 paired families in each stratum, 64 turns; actual completed seed values only. These are descriptive strata with no independent-turn uncertainty. All ambiguous locked-test families are creative/held-out, so ambiguity is confounded.

[PDF](figures/rule_structure.pdf) · [SVG](figures/rule_structure.svg) · [PNG](figures/rule_structure.png)

## recall_behavior

Recall and behavioral success are separate endpoints over the same 480 conversations/seed at 64 turns. Recall requires six correct state values; behavioral success requires the eight executable decisions and correct clarification. Worlds are paired; these bars are descriptive, not independent-sample inference.

[PDF](figures/recall_behavior.pdf) · [SVG](figures/recall_behavior.svg) · [PNG](figures/recall_behavior.png)

## recovery_exposure

Exact reconstructed optimizer-loss exposure per completed fit, by model/condition/seed/round. Loaded buffer windows are excluded unless they contribute unmasked target loss. Repeated occurrences and top-five token shares quantify concentration, not additional independent recovery examples. Resume-prefix and orphaned suffix masking follow the frozen code.

[PDF](figures/recovery_exposure.pdf) · [SVG](figures/recovery_exposure.svg) · [PNG](figures/recovery_exposure.png)

Memory-removal and contested-goal plots remain pending; no supplementary model outcomes exist yet.
