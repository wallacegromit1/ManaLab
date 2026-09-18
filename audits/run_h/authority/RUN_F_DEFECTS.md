# Run F Defects and Remediation Requirements

No production files were patched. The following defects are reproduced against a fresh Run E extraction.

## F-01 — No executable/frozen Phase 3 pipeline

- Severity: **BLOCKER**
- Location: `configs/experiments/Strixpatch_Affinity_v1.3.experiment.yaml`; `src/mana_lab/cli.py`; absence of Phase 3 orchestration modules.
- Reproduction: inspect `phase_control` and `search`; optimization is false, screening is disabled, and screening/medium/finalist/validation counts are all zero. CLI exposes only candidate count, deterministic checks, and Run A/C/E validation.
- Causal risk: shortlist, protection, seed-stage separation, multiplicity containment, and finalist validation would need to be invented during execution, after candidate results could be visible.
- Required remediation: ship a separate Phase 3 config and orchestrator implementing staged screening, C0/boundary protection, near-boundary retention, fresh validation, adaptive precision, and final report outputs.
- Required regression: synthetic/toy end-to-end pipeline test proving every stage, protected-candidate retention, seed switch, and no validation leakage.
- Re-audit: full screening/RNG/selection/validation/multiplicity/dry-run sections.

## F-02 — Named objective profiles are undefined

- Severity: **BLOCKER**
- Location: deck YAML `decision_profiles`; `metrics.py` objective-component registry.
- Reproduction: `audit_helpers.py` reports six named profiles and zero exact profile definitions.
- Causal risk: post-result profile construction can create a false winner and double-count correlated failures.
- Required remediation: freeze each profile's metrics, event windows, transforms, directions, normalization, weights/vector comparison, overlap rationale, missing-data rule, and practical-significance rule. Freeze leave-one-out and de-correlated variants.
- Required regression: config-schema rejection for incomplete profiles plus synthetic calculations with hand-checked outputs.
- Re-audit: objective/profile and model-risk sections.

## F-03 — Metric registry has no production aggregation pipeline

- Severity: **BLOCKER**
- Location: `src/mana_lab/metrics.py`; `SmokeAggregator`; absence of critical-sequence evaluators.
- Reproduction: raw production traces exist, but `SmokeAggregator` consumes only the flat smoke fields. No command emits all registry metrics, critical-sequence rows, paired candidate metric rows, or robustness tables.
- Causal risk: denominators, joins, deduplication, and missing-data behavior can change measured rankings even if raw simulation is correct.
- Required remediation: implement schema-validated raw-event aggregation, exact critical-sequence predicates, denominator reconstruction, duplicate rejection, and inspectable candidate/turn/spell outputs.
- Required regression: synthetic event streams covering success, failure, missing/not-applicable, duplicate IDs, repeated windows, and cross-event joins.
- Re-audit: raw-event/metric and pipeline dry-run sections.

## F-04 — Pareto/frontier helper is directionally and statistically unsafe

- Severity: **BLOCKER**
- Location: `src/mana_lab/metrics.py::pareto_dominates` and `profile_regret`.
- Minimal reproduction: `pareto_dominates({"unused_mana": 5}, {"unused_mana": 1}, ["unused_mana"])` returns true although the registry marks unused mana lower/contextual.
- Causal risk: a worse candidate can eliminate a better candidate; point-estimate dominance can also eliminate candidates whose uncertainty overlaps.
- Required remediation: use per-metric direction, eligibility, tolerance/materiality, missingness, and paired uncertainty; forbid irreversible noisy dominance; add near-frontier logic and paired regret uncertainty.
- Required regression: mixed-direction, tie, tolerance, missing-value, uncertain-overlap, and decisive-dominance fixtures.
- Re-audit: Pareto/regret/frontier and shortlist-safety sections.

## F-05 — Policy contract drift; advertised tap-out policy is not executable

- Severity: **BLOCKER**
- Location: deck YAML `policy_contract`; `RUN_E_POLICY_SPEC.md`; `policies.py::choose_action`; `simulator.py::simulate_trial`.
- Minimal reproduction: two synthetic alternate-policy options identical except reserve status select `reserve`; the deck contract requires `tap_out_development` and own-turn execution/mana before reserve.
- Additional discrepancy: authoritative deck-YAML baseline precedence differs materially from Run E code precedence.
- Causal risk: land colors/tapped profiles determine whether interaction can be preserved, so the policy mismatch can reorder candidates.
- Required remediation: choose one authoritative contract, update config/spec/code together, implement reserve policy as an independent scenario dimension, and reject unknown/mismatched policies.
- Required regression: state fixtures where baseline and true tap-out intentionally diverge, plus config-to-code policy identity checks.
- Re-audit: policy neutrality, interaction, robustness, and depth sections.

## F-06 — Decision-relevant omitted mechanics lack containment

- Severity: **BLOCKER**
- Location: metric registry validation-only statuses; production action generator; Run E limitations.
- Reproduction: Blood, Munitions, and Cryogen stun primitives have tests but are absent from production legal actions; Blood recursion, actual target arrival, opponent removal/Bridge indestructibility, and Familiar conditional draw lack Phase 3 sensitivity plans.
- Causal risk: colored/generic mana, untapped resources, sacrifice timing, artifact thresholds, and Bridge resilience differ across candidate mana bases.
- Required remediation: either model the mechanics in candidate-neutral production scenarios or freeze and justify containment variants demonstrating ranking immateriality. Keep raw resource availability separate from speculative demand/value.
- Required regression: production-path option/activation tests and sensitivity fixtures for every retained approximation.
- Re-audit: unsupported-mechanic and model-risk sections.

## F-07 — Planner-depth/information evidence lacks structural coverage

- Severity: **MAJOR, authorization-blocking**
- Location: `run_e_validation.py::_ordinary_state_corpus`, `_targeted_states`, `_sensitivity`; horizon/information JSON.
- Reproduction: 16 states = 12 ordinary C0 turn snapshots plus four targeted states. Most ordinary roots are land plays. Required combinations such as Boulder plus multiple spells, affinity transitions, Hawk return/replay choices, interaction hold/development, and representative double-spells are not directly audited.
- Causal risk: depth/pruning instability could correlate with mana-base structure while remaining invisible in the small corpus.
- Required remediation: expand a candidate-neutral targeted corpus across each required structural class, record node/branch counts and root/terminal differences, and predeclare acceptance thresholds.
- Required regression: depth 7/8/9 (and deeper where tractable) plus information-policy comparisons for every structural class.
- Re-audit: planner-depth/pruning and policy-sensitivity sections.

## F-08 — Provenance/hash manifest does not reconcile

- Severity: **MAJOR, authorization-blocking**
- Location: `outputs/run_e/source_config_hashes.json`; `run_e_validation.py::_source_hashes`; package lacks `.git`.
- Minimal reproduction: untouched fresh extraction has 63 packaged source/test/config files and a 166-entry manifest; the 103 extra entries are absent `__pycache__/*.pyc` files. `git rev-parse HEAD` fails; fresh `run-e` writes commit `UNAVAILABLE`.
- Causal risk: a third party cannot reconcile the claimed source manifest or independently resolve the commit; normal validation mutates reported provenance.
- Required remediation: generate the manifest from an allowlist of source/config/test files while excluding caches/generated files; include a verifiable source version marker or content-tree hash; make reports deterministic outside immutable source inputs.
- Required regression: fresh-archive manifest equality, no extra/missing entries, and same-config ordinary-content hash reproducibility.
- Re-audit: package/provenance and reproducibility sections.
