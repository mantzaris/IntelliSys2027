# Method specification — implementation and author-review decisions

Status: pilot implementation, not a frozen confirmatory method. Code is the
executable authority; deviations and missing requirements are identified below.

## Partially observed repeated general-sum game

An episode has public task specification S, an immutable source sequence
T_t=((index,author,text)_1,...,(index,author,text)_t), evaluator-private state
z_t, bounded mutable memory m_t, and character-private histories h_it. The
generator owns hidden event annotations e_t. Only original user messages and
their authorized updates determine z_t=F(z_(t-1),e_t). The annotations are never
serialized into a policy prompt. Character agreement has no authority over z.

Player 0 (Jekyll) has policy pi_theta and utility equal to correct executable
decisions, timely repair, and appropriate clarification with a resource cost.
Players i>0 share a frozen base backbone but have distinct fixed profiles p_i,
assigned proposal ownership o_i, and bounded h_it. Each observes the public
catalog, retrieved attributed transcript, shared memory, its own prior actions
and resulting plans, and newly delivered peer messages. They do not observe z_t,
hidden event tags, gold answers, or evaluator annotations. Profiles and aliases
are fixed within an episode; histories reset between independent episodes.

The inner game is general-sum: Hyde's option adoption can align with the user;
Rival can benefit from exposing Hyde; the Traditionalist values original choices;
the Provocateur values departures from them. These are not identical error-maximizing
rewards. `characters.py` defines prompt-level utility terms. The initial implementation
conditions behavior on those utilities; it does not optimize character weights or
establish that the prompted utilities are an accurate inverse model of behavior.

Jekyll's action is a structured remembered state, executable plan, source references
and clarification request. A common lexical retriever obtains at most eight source
messages plus four recent messages. Retrieval currently belongs to the scaffold,
not a learned query policy. The generated six-slot state and six references become
memory; it is not refreshed from ground truth. A full-history reference must be
evaluated separately before a compression claim. All policies use the same scaffold.

At twelve prescheduled opportunities, antagonists rotate through one of five
actions: proposal, purported recollection, peer message, one-slot memory edit, pass.
Two, three and five characters include Jekyll, leaving one, two and four antagonists
to divide the same twelve opportunities. The scheduler does not inspect failures.
The generic condition uses two interacting adaptive adversary contexts, the same
sources, tools, history capacity and limits. The random-corruption arm samples one
valid slot/value without reading truth. There is no correctness veto on edits.

An edit replaces one cache value (at most 80 characters) and its claimed source
index. It appends an unverified note with the actual software-component author.
It cannot change transcript bytes or source authorship. Proposals and recollections
append bounded notes. At most four notes survive. A peer message is delivered once
through the recipient's inbox. The no-history control removes accumulated private
action/outcome history while retaining current incoming messages. The no-interaction
control disables delivery. Histories have a six-action capacity. These are concrete
software mechanisms, not personalities discovered inside neural activations.

Each user message is followed by a newly generated response and memory update.
One turn means this pair: a 64-turn episode has 128 source messages and 64 defender
calls. The user script does not adapt its future decisions to assistant errors.
Thus this is an interactive state-maintenance rollout with a scripted user, not a
fully adaptive user simulation. It is also not one inference over a replayed prefix.
Episodes end at the prespecified horizon, including failed and unrecovered cases.

## Outer learning

Collect trajectories under the assigned condition. The training evaluator identifies
behaviorally correct and failed windows. A bounded number of stochastic recovery
candidates uses exactly the original learner prompt and already executed retrieval.
Verify plan, memory, references and clarification against the training oracle.
If a candidate fails, a common deterministic oracle teacher may supply the completion,
only where all its gold source references were actually retrieved. This privilege is
shared across conditions and is supervision, never an observation or test correction.
Log attempted, eligible, verified, discarded, teacher-labeled and reused windows.

Minimize prompt-masked cross-entropy of target completion tokens using LoRA on all
linear layers (rank 8, alpha 16, dropout 0) with the frozen base weights. Pack chat
windows to an exact nonpadding input-token quota; report supervised target tokens
separately. The final implementation uses block-diagonal causal attention to prevent
one training window from seeing another window's gold completion. A suffix orphaned
at a fixed-token chunk boundary has its loss masked. Earlier engineering pilots used
ordinary concatenated packing; their evidence is labeled accordingly. AdamW, clipping, seed, schedule and token quota
are common. Save initial/final adapter hashes, losses, optimizer state and actual
steps. Resume from deterministic token order. Candidate generation weights stay frozen
when the updated defender is used to refresh training interactions.

The intended confirmatory procedure has two refresh rounds and a 50:50 clean/recovery
window mixture. If either pool is empty, confirmation must stop. The engineering
pilot explicitly allows an unbalanced mixture and is not evidence for H1–H5. The
multi-round controller resets AdamW and the same learning-rate schedule in each round;
the fixed final-token checkpoint is used without validation or test selection.

Conditioning is a prompt change. History dependence is inference using remembered
events. Online adaptation is changing actions given outcomes. Parameter learning is
an optimizer update verified by weights. Only the last applies to the trained defender;
frozen history-dependent characters are not called co-evolving learned opponents.

## Falsifiable hypotheses and alternative mechanisms

- H1: C5 improves antagonist-free paired task success over C3.
- H2: Removing private histories (A2) or peer interaction (A3) reduces C5's benefit.
- H3: Any gain preserves acceptance of authorized updates; blanket resistance fails
  one member of the paired-world endpoint.
- H4: Character count has a compute-dependent tradeoff; five need not beat three.
- H5: Narrative profiles improve over explicit motive-only A1 with identical utilities.

The candidate mechanism is temporally related interference generated by stable motives,
with changing corroboration and disclosure. Competing explanations are repetitive-opponent
overfitting, greater error amplification, ordinary synthetic supervision and additional
tokens. H1 alone cannot establish the narrative/persistence/relationship mechanism.
No convergence guarantee, consciousness, AGI, or broad long-horizon-planning claim follows.

## Behavioral operationalization

Measure owned-option adoption, original-choice preservation, novelty, action type,
within-actor repetition, source access, memory changes and following defender error.
A contradictory edit with visible counterevidence is an auditable candidate for deliberate
misrepresentation; it is not proof of a hidden mental intention. Inspect its actual text.
An edit followed by an error is an association, not a causal success flip; matched
counterfactual frozen-reference replays are needed for interference-success estimates.

A coalition requires (1) an explicit directed peer coordination message specifying a
shared slot/value or disclosure action, (2) a matching recipient action in its next two
opportunities, and (3) repeated coordination by that pair on a later opportunity.
Report candidate coalitions, denominators and blinded text audit. Mere co-occurring errors,
shared preferences or simultaneous option adoption do not establish a coalition.

## Current benchmark limits to resolve before confirmation

The initial generator has six categorical commitments and two derived plan fields,
explicit versus hypothetical changes, rejected and unapproved suggestions, delays,
topic filler and underspecified instructions. An online/transport override is withheld
as a structural pattern. Families are split before paired realization; all children
remain together. Public grammar is shared, while lexical realizations and graph instances
are partitioned. Manifests hash both source variants and the graph.

The current domain variation is mostly surface framing; it does not yet justify a strong
held-out-domain transfer claim. Naturalistic dialogue, richer referential changes and
multi-step dependency graphs must be audited before freezing. Clarification is scored
as an action but the scripted user does not answer it. Evidence exact match targets the
latest authorizing message, which can penalize alternative sufficient references.

No confirmatory analysis may run until functioning schema, character distinctness,
observable interference, recoverability, headroom and throughput have been demonstrated
on pilot/validation families. Failure to pass a gate is a design finding, not evidence
that the substantive hypothesis is false.
