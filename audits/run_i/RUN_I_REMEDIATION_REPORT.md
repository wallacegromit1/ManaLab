# Mana Lab — Run I readiness remediation report

## Decision

**RUN I REMEDIATION — NOT READY FOR RE-AUDIT**

The branch implements substantial targeted Run H remediation, but the exact
Run I gate requires complete production behavior for all H-01–H-07. That
condition is not established. This report is a self-audit, not an independent
authorization; Phase 3 remains prohibited.

## Authority and scope

- Parent: `70dbce16e6604245a3ee962b1cb0c2d7800ede06`.
- Source of defects: `audits/run_h/RUN_H_DEFECTS.md` (unchanged).
- Acceptance: `audits/run_h/RUN_H_ACCEPTANCE_MATRIX.csv` (unchanged).
- Frozen Run E / Run G archive hashes recorded in provenance manifest.
- Scientific configuration, frozen deck and candidate pool have not been
  changed; no real mana-base performance rankings are reported.

## H-01 — PARTIAL

Root cause: Run G had a synthetic-only stage graph and weak prerequisites.
Implementation: `phase3_pipeline.py`, `phase3_config.py`,
`phase3_stage_schemas.py`; stage envelope/type validation, stage-chain hashes,
atomic immutable writes, fully persisted legal candidate identities, exact
C0 + 56 boundary protection and immutable event-payload identity. The
mulligan draw seed derivation now matches the declared purpose/scenario/
replicate/trial/attempt hash without changing frozen seed values.
The candidate-neutral C0-equivalent fixtures execute the real
`simulate_trial -> aggregate_trial_events -> paired_difference` path.
Pending: stage 04 medium, 05 finalist selection, 06 fresh candidate
validation, 08 frontier and 09 final report are machinery/control checks,
not a complete real-candidate production analysis. Production stage
schemas do not prove completion of those algorithms. Stages 03 and 07
retain raw traces; a general full-space input/output workflow is not yet
demonstrated.

## H-02 — PARTIAL

Root cause: flat scalar profile evaluation ignored event populations.
Implementation: `phase3_profiles.py` reconstructs six named ordered
vectors from trial events, distinguishes all/colored/affinity populations,
keeps turn/scenario/aggregation IDs, applies explicit declared turn weights,
and supports paired-component comparisons, leave-one-out and declared
de-correlated variants. Pending: complete hand-calculated, play/draw-weighted
fixture matrix for every component, execution of all sensitivity variants
through a production decision caller, absent-population policies and
cross-population pairing proof.

## H-03 — PARTIAL

Root cause: routing labels without full aggregation, permissive traces and
mis-specified deadline/source predicates. Implementation:
`phase3_metrics.py`, `state.py`, `effects.py`, `simulator.py` introduce
strict production identity, complete T1–T4 snapshots, physical source IDs,
deadline-aware critical predicates, denominator-state enum and
trace-derived candidate/spell/paired/robustness tables. Same physical card
can count as two distinct spell executions after recast.
Pending: all 29 routes need explicit numerical/denominator aggregation and
positive/negative production-schema fixtures; several routes currently
return event subsets and should not be represented as fully measured
production metrics. Source-event ordering and every opportunity join
still need independent adversarial proof.

## H-04 — PARTIAL

Root cause: isolated uncertainty primitives lacked multiplicity and
end-to-end production inference. Implementation: `metrics.py` and
`statistics.py` validate finite/ordered intervals, retain unknown/low-N
cases, distinguish one-sided no-worse from two-sided equivalence, compute
key-aligned paired differences, Holm family control, conservative
across-look Bonferroni bounds, oriented frontier and regret primitives.
Pending: frozen profile/stage/candidate comparison families and adaptive
looks must actually be invoked from production stages; reversible
screening ledger and full paired-difference table families remain absent.

## H-05 — PARTIAL

Root cause: sequencing selected scry implicitly and descriptive hashes
could hide role-kind replacement. Implementation: `phase3_policies.py`,
`simulator.py`, `phase3_config.py`, `phase3_pipeline.py` independently
pass mulligan, sequencing, scry, reserve, information and planner bounds.
Every robustness tuple is executed in candidate-neutral validation;
events and stage artifacts stamp policy/scenario identity. Pending:
full per-role execution-binding audit, decision-sensitive information-policy
boundary fixtures and production candidate-stage policy execution.

## H-06 — PARTIAL / MODEL-RISK BLOCKER

Root cause: tested mechanics primitives were not necessarily planner
options and declarations of NOT MATERIAL lacked executable bounds.
Implementation: Blood activation is an actual causal planner option;
`phase3_model_risk.py` exposes Familiar conditional-draw,
resource-vs-target, sacrifice and single destructive land-removal
sensitivities. Pending: Blood Fountain's frozen data specifies the
activation cost but not the full recursion/target effect; Fountain can
be reachable by turn 4 and is not proved immaterial. Familiar's extra
draw requires continuation through future decisions. Munitions/Cryogen
target-conditional effects and removal/Bridge resilience lack
decision-sensitive candidate-neutral bounds. Old NOT MATERIAL rows
remain unclosed rather than being quietly relabeled.

## H-07 — PARTIAL

Root cause: earlier six states stopped after 2–4 actions despite being
described as search-depth evidence. Implementation: `simulator.py` and
`phase3_depth.py` capture actual root actions, expanded nodes, branches,
terminals, prunes, stop reasons, maximum explored depth/sequence length.
A seventh exact-deck-type Hawk/affinity stress structure reaches seven
actions in the deeper search; forced depth 3 loses that path. Pending:
the new stress state is turn 5, beyond the frozen turn-4 scoring horizon;
decision sensitivity for each on-horizon pruning/action limit and legal
post-reveal divergence remain to be certified as part of a final gate.

## F-08 — ARCHIVAL PASS PRESERVED

Run H reference/authority/evidence remain unmodified. The untouched
archives match the frozen SHA-256 checks in the CI workflow. New Run I
source hashes are separate from original Run G package hashes.

## Meaning of a green CI result

A passing unit suite establishes the properties tested; it does not turn
the above PARTIAL requirements into PASS. The production simulator is not
authorized to rank legal mana-base candidates.
