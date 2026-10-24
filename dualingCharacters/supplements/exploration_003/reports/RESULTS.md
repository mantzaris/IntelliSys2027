# Exploration results — exploratory analysis under the frozen protocol

Evidence cutoff: 2026-10-24T21:48:41.317447+00:00. Primary: Qwen base defender, generator seed17, eight paired pilot families, 16-turn episodes, 12 opportunities. No new model calls.

| Condition | Mean episode categories | Pooled categories | Mean two-action sequences | Mean transition types | Structurally substantive /192 | Character input+output tokens |
|---|---:|---:|---:|---:|---:|---:|
| C2 | 3.3125 | 5 | 3.7500 | 0.0000 | 128 | N/A: deterministic |
| C3 | 6.5625 | 33 | 9.7500 | 2.3125 | 191 | 241008 |
| C4 | 5.7500 | 36 | 7.6875 | 1.2500 | 179 | 281525 |
| C5 | 6.3750 | 31 | 9.1875 | 1.1250 | 192 | 256851 |
| C6 | 7.2500 | 29 | 8.5625 | 1.9375 | 175 | 230848 |
| A1 | 6.5000 | 31 | 9.1875 | 1.5000 | 192 | 248067 |
| A2 | 5.5625 | 30 | 8.6875 | 1.1250 | 192 | 212409 |
| A3 | 4.7500 | 26 | 3.8750 | 1.1875 | 130 | 246985 |

Primary C5−C3: **-0.1875 categories per episode**, paired-family 95% interval **[-1.6250, +1.1875]**. Ten thousand family resamples preserve both worlds. One generator seed and eight families do not establish equivalence or population generality.

Zero transition coverage for C2 means unavailable pre-action character observations, not zero physical transitions. Missing-state actions are excluded from that particular category count. A3 loses coverage through rejected actions in reserved communication slots; this is a design/formatting difference, not an isolated semantic effect of relationships.

## Persistence and complementarity

| Condition/role | Same slot/value / comparisons | Rate |
|---|---:|---:|
| C3 Generic | 71/96 | 73.96% |
| C5 Rival | 34/38 | 89.47% |
| C5 Hyde | 43/48 | 89.58% |

| Observable | C3 | C5 |
|---|---:|---:|
| Collective categories beyond the largest actor, mean/episode | 2.0625 | 1.75 |
| API/reference changes during repeated goals | 33 | 45 |
| Repeated-goal comparisons, denominator | 71 | 77 |
| Returns after a different direct goal | 8 | 2 |
| Structurally substantive applied actions /192 opportunities | 191 | 192 |
| Recorded working-memory changes, including notes /192 | 131 | 128 |
| Immediate targeted-state correct-to-incorrect transitions /192 | 62 | 0 |
| Immediate targeted-state incorrect-to-correct transitions /192 | 4 | 2 |

These are descriptive counts with dependent actions. Changes in API/reference class are tactic proxies, not semantic development. Targeted-state transitions compare the same-turn pre/post working state; they do not measure the causal effect on the following answer. Notes, peer delivery and executable decisions are different channels. Full action frequencies, validity reasons, source-visible contradictions and adoption flags retain their denominators in the CSV tables.

Pooled overlap: 16 shared categories, 15 C5-only and 17 C3-only. The full union spends twice the intervention budget and is not an improvement estimate.

| Equal-budget archive | Mean categories | Qualification |
|---|---:|---|
| C3,12 opportunities per episode | 6.5625 | Single trajectory |
| C5,12 opportunities per episode | 6.3750 | Single trajectory |
| Six C3 + six C5 prefix opportunities | 6.1875 | Two initial trajectories; actual costs reported separately |

At the whole-archive level, balanced methods across paired families can add categories at the same number of opportunities. This is a different question from within-episode breadth.
- C3: 33.00 categories (range 33–33 across100fixed family orderings;192opportunities).
- C5: 31.00 categories (range 31–31 across100fixed family orderings;192opportunities).
- balanced_mixture: 34.49 categories (range 30–38 across100fixed family orderings;192opportunities).

All whole-archive allocations use 192 character calls and 256 defender calls. Actual prompt/history and output tokens differ:

| Archive | Mean character tokens | Mean defender tokens | Total-token allocation range |
|---|---:|---:|---:|
| C3 | 241008.00 | 294264.00 | 535272–535272 |
| C5 | 256851.00 | 300804.00 | 557655–557655 |
| balanced_mixture | 248869.68 | 297411.50 | 543014–549671 |

These are measured token sums from archived trajectories, not condition-specific timing or equal FLOPs. The primary chronological token-prefix contrasts are in `primary_paired_contrasts.json`.

## Main collections remain observational

| Contrast | Seed | Round | Shared defender weights | Mean coverage difference | Family95% interval |
|---|---:|---:|---|---:|---|
| C5−C3 | 17 | 0 | True | -0.140 | [-0.463, +0.177] |
| C5−C4 | 17 | 0 | True | +2.287 | [+1.967, +2.603] |
| C5−A1 | 17 | 0 | True | +0.017 | [-0.227, +0.267] |
| C5−C3 | 17 | 1 | False | -0.037 | [-0.313, +0.240] |
| C5−C4 | 17 | 1 | False | +2.577 | [+2.310, +2.840] |
| C5−A1 | 17 | 1 | False | +0.013 | [-0.230, +0.253] |
| C5−C3 | 29 | 0 | True | +0.083 | [-0.233, +0.397] |
| C5−C4 | 29 | 0 | True | +2.223 | [+1.903, +2.530] |
| C5−A1 | 29 | 0 | True | +0.093 | [-0.183, +0.380] |
| C5−C3 | 29 | 1 | False | -0.290 | [-0.573, +0.007] |
| C5−C4 | 29 | 1 | False | +2.247 | [+1.937, +2.550] |
| C5−A1 | 29 | 1 | False | +0.027 | [-0.203, +0.270] |

These estimates are conditional on the named generator seed. Round1 uses different trained defenders and families. No seed population interval or causal learning effect is inferred. Main C2/C6/A2/A3 and C5seed43 were absent at the cutoff. Later completions do not enter these tables.

## Scientific assessment

**Inconclusive for broader useful exploration.** The primary endpoint and measured-token checks do not show a clear C5 breadth advantage. Higher typed-goal repetition supports persistent pursuit in this narrow sense, while API/reference changes require semantic validation before they count as tactic development. Some pooled categories are complementary, and balanced archives can gain modest coverage, but the within-episode mixture does not improve mean coverage.

The similar motive-only results do not identify a biography contribution. History/peer pilot differences remain entangled with action validity, routing, sampling variation and descriptor mechanics. Distinct owned slots permit simultaneous adoption. Source visibility can change a descriptor even when the claim is repeated verbatim. Nothing here shows the trained defender becoming a better explorer.

Retain original antagonist-free outcomes: C5−C3 is negative at both currently matched completed seeds. Exploration generation is a separate endpoint; it does not reverse those findings. Human semantic labels are pending.
