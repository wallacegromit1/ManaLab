# Run H defects for separate Run I remediation

RUN H AUTHORIZATION — PHASE 3 NOT AUTHORIZED

## H-01 — Synthetic-only production stages; forged dependency accepted; incomplete config enforcement.

Severity: BLOCKER. Prior blocker: F-01.

Source: `phase3_pipeline.py:51,97,120,129,138,152,160,174,207; phase3_config.py:74` (verbatim copies in reference/; function-line map in evidence/source_locations.json).

Observed: run_real always raises, including regardless of control state. stage_04_medium accepts an external synthetic 03_screen.json containing only status PASS, matching config_hash and a forged artifact hash. It does not load candidate/event rows. C0/boundary protection is caller-supplied; no production caller derives all 56 protected IDs or carries them through every serious stage. The test with an empty protection set is a caller-contract probe, not a claim that an existing production optimizer eliminated C0.

Required remediation: Implement testable production stages with typed input/output schemas, validated artifact/code/config/policy/seed lineage, candidate persistence, atomic immutable writes and restart semantics. Separate authorization identity from scientific config. Reject invalid planner bounds, seed use, adaptive counts, weights, C0, scenario policies and unknown metric references.

Acceptance regression: Synthetic end-to-end pipeline executes actual simulation/aggregation/statistical paths; restart/tamper/missing-input tests; C0 and all boundary IDs survive each serious stage; authorization changes no scientific parameters.

## H-02 — Profiles consume flat scalars rather than executing declared populations, weights and uncertainty.

Severity: BLOCKER. Prior blocker: F-02.

Source: `phase3_profiles.py:17,52; frozen config decision_profiles` (verbatim copies in reference/; function-line map in evidence/source_locations.json).

Observed: All six hand-set scalar vectors compare correctly, but changing turns/aggregation leaves output unchanged. A single scalar name cannot distinguish all-spell, colored-spell and affinity-only castability. Comparator uses first component exceeding materiality, ignores uncertainty/no-worse constraints and later tradeoffs. Affinity de-correlated variant is identical to original; metadata presence is not substantive de-correlation.

Required remediation: Implement profile-specific aggregation from validated raw sufficient statistics, explicit numeric weights and population IDs; use paired uncertainty and coherent conflict/tie semantics. Justify priority and truly test overlap/leave-one-out/de-correlated alternatives.

Acceptance regression: Hand-calculated spell/turn/play-draw fixtures for every profile, not only preaggregated constants; conflicting components and overlapping intervals retain alternatives; altered weights/windows change the expected result.

## H-03 — Aggregation coverage is a label registry; trace contracts and sequence joins are incomplete.

Severity: BLOCKER. Prior blocker: F-03.

Source: `phase3_metrics.py:11,56,63,91,148` (verbatim copies in reference/; function-line map in evidence/source_locations.json).

Observed: An opening-hand-only trace is accepted; missing identity fields default; different desired-window profiles pool. Exact-turn checks violate by-T2 definitions. Cryogen/Hawk reader expects returned while producer logs card; draw counts are not constrained by source-instance/order/deadline. Cross-scenario resolutions count as double-spell. T2 full-effect interaction is ignored. Candidate/spell/paired/robustness tables are not produced.

Required remediation: Implement every required aggregate with executable routing; reconstruct denominators by declared profile/opportunity/window; distinguish absent/not-applicable/incomplete; enforce complete trial identity and validated event joins. Correct all 11 predicates against frozen definitions.

Acceptance regression: Production-schema positive/negative fixtures for every metric/predicate; no future draw satisfies earlier deadline; correct Hawk event field and draw ordering; duplicate/missing/mixed identities reject; real schema-shaped tables emitted from synthetic traces.

## H-04 — Uncertainty relation improved, but production multiplicity, adaptive precision and regret are absent.

Severity: BLOCKER. Prior blocker: F-04.

Source: `metrics.py:247,315; phase3_pipeline.py:16,97,160; statistics.py` (verbatim copies in reference/; function-line map in evidence/source_locations.json).

Observed: Stochastic missing intervals remain unresolved and lower-is-better legacy elimination is prevented. However reversed bounds are sorted, nonfinite inputs are not rejected, and CI [-.001,.8] at no-worse .0025/material .005 is labeled practically_equivalent. That is evidence of no worse, not two-sided equivalence. Holm appears as text, not an executed stage procedure. Caller-supplied intervals are not tied to keys, sample count, family or simultaneous coverage. profile_regret assumes scalar higher-is-better.

Required remediation: Validate interval/data contracts and metric completeness; compute aligned paired differences and simultaneous family-corrected claims. Specify families across candidates/components/profiles/stages and sequential validity for adaptive looks. Implement uncertainty-aware frontier/regret and reversible screening ledger.

Acceptance regression: Synthetic raw paired data reproduces manual intervals, duplicate/missing key rejection, adjusted and sequential boundary decisions, conflicting profiles and uncertain regret. Widening an interval cannot establish equivalence or new elimination.

## H-05 — Independent reserve repaired; full scenario identity and execution binding remain incomplete.

Severity: BLOCKER. Prior blocker: F-05.

Source: `phase3_policies.py:29,104; simulator.py:768; policies.py:196` (verbatim copies in reference/; function-line map in evidence/source_locations.json).

Observed: Reserve, sequencing, mulligan and scry alternatives intentionally differ in external fixtures. Registry hashes descriptive content; in-memory replacement is not caught by registry validation. Important qualification: on-disk behavior changes ARE covered by the complete file manifest at readiness. The defect is not a missing source file hash. Role-kind mismatch is accepted; simulate_trial has no independent scry argument and derives scry from sequencing, contradicting tempo_tapout and alternate_scry_information configurations. Output schema probe selects an arbitrary policy hash.

Required remediation: Bind typed roles to exact code-tree plus policy contract, validate every scenario, independently pass all policy axes and planner bounds, and stamp complete identity on events/results/stage artifacts. Reconcile legacy policy text with the explicit new authoritative freeze.

Acceptance regression: Unknown role and valid-hash/wrong-kind reject; each robustness tuple executes exactly declared policies; code-only on-disk changes fail before reuse; every result exposes all executed axes. Demonstrate a decision-sensitive information-policy state or explicitly constrain its claimed sensitivity.

## H-06 — Mechanics labels do not establish production reachability or ranking containment.

Severity: BLOCKER. Prior blocker: F-06.

Source: `RUN_G_MECHANICS_COVERAGE.csv; simulator.py:164; effects.py; tests/test_familiar.py` (verbatim copies in reference/; function-line map in evidence/source_locations.json).

Observed: Blood/Munitions/stun primitives are tested but not production planner actions. Blood needs own token, discard and mana, not an opponent target. Familiar test only checks no automatic draw; it does not implement promised zero-versus-available sensitivity. Excluding an explicit metric does not remove indirect draw, artifact, mana, sacrifice or future castability effects. Fountain recursion and removal/Bridge resilience have declarations rather than executable containment.

Required remediation: Implement required production mechanics or preregister executable candidate-neutral containment scenarios justified against frozen rules. Track resource availability separately from target value; leave unresolved model uncertainty blocking robust claims.

Acceptance regression: Production option/activation tests sensitive to payment, sacrifice, artifact thresholds, draw timing and legal target states. Every NOT MATERIAL claim links to an actual bound or sensitivity fixture, not self-reported relevance=false.

## H-07 — Six named classes are present but depth evidence is not boundary-sensitive.

Severity: MAJOR — authorization-blocking. Prior blocker: F-07.

Source: `phase3_depth.py:26,92; simulator.py:569,768` (verbatim copies in reference/; function-line map in evidence/source_locations.json).

Observed: At depths 7–10 longest explored paths are 2–4 actions. Shipped root_choices stores complete sequence keys; terminal_state_counts counts recorded prefixes, not independently established terminal nodes. Information policies change values but all shipped corpus choices remain identical. No Phase 3 production caller consumes frozen bounds.

Required remediation: Add candidate-neutral reachable stress states where useful lines reach relevant depth/pruning limits; record true roots, nodes, branches, terminals, prunes and stopping reasons. Compare oracle/deeper searches where tractable, plus reserve/information axes and reveal boundaries.

Acceptance regression: A deliberately truncated depth/pruning implementation must fail at least one corpus test. Test hidden-order invariance before reveal and legal divergence after reveal. Wire and stamp frozen depth/action limits in production.

F-08 is closed for package-level identity. No production edits were made. Expected/observed failures in audit JSON are deliberate adversarial evidence; not failed audit execution.
