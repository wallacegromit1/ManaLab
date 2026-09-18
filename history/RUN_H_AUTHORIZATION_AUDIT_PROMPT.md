# MANA LAB — PAUPER v1
## RUN H — INDEPENDENT PHASE 3 AUTHORIZATION AUDIT

### RECOMMENDED CONFIGURATION

- Mode: **Work**
- Model: **GPT-6 Astra** or strongest available audit model
- Reasoning: **High**
- Web: **OFF**, unless authoritative card/rules verification becomes materially necessary
- Primary audit input: **`Mana_Lab_Pauper_v1_Run_G.zip`**
- Required Run G SHA-256:  
  **`ca7f2ed96cfc0a19041304af4d29bdbb4bf9c9b3908d10f35ffadb0599813e9d`**
- Required Run E parent SHA-256:  
  **`82d1dcd663de5a8bcb2d9917271fba264c509bdff8b45d1920b9f97ccf0d0c71`**
- Prior defect authority: complete Run F audit package
- Audit target: Run G Phase 3 readiness implementation
- Output: independent authorization verdict and complete audit artifacts

**Do not perform mana-base optimization. Do not screen, score, rank, shortlist, validate, compare, or recommend real candidate mana bases.**

---

# 1. ROLE

Act as an independent senior:

- Python simulation and experiment-pipeline auditor;
- Monte Carlo and statistical-methodology auditor;
- reproducibility and provenance engineer;
- adversarial software QA reviewer;
- Magic: The Gathering rules/modeling specialist;
- competitive Pauper Affinity sequencing specialist.

Run G claims to have repaired all eight Run F authorization blockers. Your task is to determine independently whether the implementation is genuinely safe and complete enough to authorize Phase 3 execution.

Do not defer to Run G’s own PASS result. Reproduce its evidence, inspect its implementation, construct adversarial counterexamples, and issue an independent authorization decision.

---

# 2. INPUT INTEGRITY GATE

Before auditing:

1. Locate `Mana_Lab_Pauper_v1_Run_G.zip`.
2. Compute its SHA-256.
3. Require the exact match:

   `ca7f2ed96cfc0a19041304af4d29bdbb4bf9c9b3908d10f35ffadb0599813e9d`

4. Extract the ZIP into at least two fresh directories.
5. Confirm no archive corruption.
6. Confirm the required Run G deliverables are present.
7. Locate the exact Run E parent when available and verify:

   `82d1dcd663de5a8bcb2d9917271fba264c509bdff8b45d1920b9f97ccf0d0c71`

8. Locate and use the complete Run F audit artifacts as the defect authority:

   - `RUN_F_PHASE3_AUTHORIZATION_REPORT.md`
   - `RUN_F_ACCEPTANCE_MATRIX.csv`
   - `RUN_F_PHASE3_FROZEN_CONFIG.md`
   - `RUN_F_REPRODUCIBILITY.md`
   - `RUN_F_DEFECTS.md`
   - `audit_helpers.py`
   - associated evidence files

If the Run G ZIP is missing or its hash differs, stop with:

**`RUN H INPUT BLOCKED — EXACT RUN G PACKAGE MISSING OR HASH MISMATCH`**

Do not repair, reinterpret, or substitute the production package during the audit.

---

# 3. AUDIT INDEPENDENCE AND SCOPE

Run H is an authorization audit, not an implementation run.

Allowed:

- read-only source/config/report inspection;
- fresh-extraction test execution;
- deterministic candidate enumeration and count verification;
- independent combinatorial checks;
- synthetic and toy candidate fixtures;
- protected C0 machinery checks that are not competitively interpreted;
- tiny non-inferential smoke runs;
- adversarial policy, profile, aggregation, provenance and statistical fixtures;
- independent audit helpers stored outside the production package.

Forbidden:

- editing Run G production files;
- executing real-candidate performance screening;
- scoring or ranking the 296,706 legal mana bases;
- constructing a real shortlist or frontier;
- selecting finalists;
- running confirmatory real-candidate validation;
- recommending a mana base;
- using any observed candidate result to revise profiles, tolerances or rules.

If a defect is found, document it. Do not patch it in Run H.

---

# 4. CLAIMS THAT MUST BE REPRODUCED

Independently reproduce or falsify the following Run G claims:

- exact Run E parent integrity;
- untouched Run E baseline of 179 passing tests;
- patched Run G suite of 205 passing tests;
- D-01 through D-11 regressions remain passing;
- exact candidate count of 296,706;
- C0 appears exactly once;
- minimum-Bridge class contains exactly 56 candidates;
- canonical candidate identity is deterministic;
- selection, validation and replicate seeds are disjoint;
- policy identities and hashes are complete and drift-sensitive;
- the true tap-out reserve policy is executable;
- all required profiles are fully defined;
- all metric-registry entries have executable aggregation coverage;
- critical-sequence predicates are executable;
- stochastic point estimates cannot create dominance;
- close or uncertain screening comparisons are retained;
- C0 and protected structural classes cannot be eliminated;
- all six structural planner fixtures are stable at depths 7/8/9;
- no ranking-relevant unsupported mechanic remains;
- the cache-free source/config manifest reconciles exactly;
- two fresh dry runs produce identical ordinary-content hashes;
- dry-run artifacts contain no ranking, recommendation or real performance evidence;
- the packaged one-command readiness gate returns machine-readable PASS from a fresh extraction.

---

# 5. PRIMARY AUTHORIZATION QUESTION

Determine whether Run G provides a genuinely executable and safe Phase 3 system—not merely a convincing dry-run scaffold.

In particular, establish whether an independently authorized follow-on run could enable production execution without inventing or materially changing:

- stage inputs or outputs;
- candidate simulation wiring;
- metric aggregation;
- screening logic;
- finalist selection;
- validation isolation;
- adaptive precision;
- robustness execution;
- Pareto/frontier construction;
- reporting logic;
- authorization handling.

If substantial production behavior remains a stub, synthetic-only implementation, hardcoded demonstration, schema placeholder or undocumented manual step, Phase 3 is not ready.

---

# 6. RUN F BLOCKER RE-AUDIT

Audit every blocker independently.

## F-01 — Executable and frozen Phase 3 pipeline

Verify all nine stages:

1. input/config validation;
2. deterministic enumeration/features;
3. safe screening;
4. medium paired simulation;
5. finalist retention;
6. fresh independent validation;
7. robustness/sensitivity;
8. Pareto/frontier;
9. reporting.

For each stage verify:

- callable entry point;
- concrete production input schema;
- concrete output schema;
- immutable prerequisite checking;
- config/code/policy/seed provenance;
- deterministic candidate identity;
- failure behavior;
- restart/resume behavior;
- stage-order enforcement;
- C0 and protected-class handling;
- no selection/validation leakage.

Determine whether the implementation can operate on real authorized evidence after authorization, rather than only returning synthetic PASS artifacts.

A `run_real()` method that simply refuses execution is acceptable only if a complete, separately testable production path already exists behind the authorization gate. If enabling Phase 3 would require new orchestration code, F-01 remains open.

## F-02 — Named decision profiles

For every profile verify:

- exact metric vector;
- direction;
- aggregation across turns, spells and play/draw;
- normalization;
- missing-data behavior;
- practical no-worse tolerance;
- material-improvement tolerance;
- uncertainty treatment;
- tie behavior;
- overlap rationale;
- leave-one-component-out variant;
- substantive de-correlated variant.

Profiles must be executable from raw or aggregated candidate evidence. Configuration prose that cannot be evaluated by production code is insufficient.

Construct hand-calculated fixtures for every profile and confirm the exact vector and comparison result.

Check whether lexicographic ordering creates an unacknowledged near-scalar priority that could force a winner despite meaningful tradeoffs.

## F-03 — Metric aggregation and critical sequences

Verify production aggregation for every Phase 3 metric, not merely a routing label.

Test:

- success;
- failure;
- not applicable;
- missing required event;
- duplicate event ID;
- duplicate opportunity ID;
- repeated diagnostic windows;
- primary-window selection;
- cross-event joins;
- spell-instance identity;
- turn identity;
- scenario identity;
- functional versus raw casts;
- denominator reconstruction;
- empty denominators;
- target-dependent exclusions.

Independently hand-check all eleven critical-sequence predicates.

Confirm that candidate-, spell-, turn-, paired-difference- and robustness-table outputs can actually be generated with their promised provenance columns.

## F-04 — Safe dominance, screening and frontier logic

Construct adversarial fixtures for:

- exact dominance;
- exact inferiority;
- mixed directions;
- exact ties;
- practical equivalence;
- material improvement;
- one materially worse dimension;
- overlapping confidence intervals;
- missing uncertainty;
- missing metric values;
- conflicting profiles;
- lower-is-better metrics;
- deterministic plus stochastic mixed vectors;
- multiple-comparison-adjusted intervals.

Verify:

- point estimates alone never eliminate stochastic candidates;
- uncertainty is based on aligned paired differences;
- a candidate must be no worse on every eligible dimension;
- at least one dimension must show material improvement;
- unresolved comparisons remain unresolved;
- comparison direction is correct;
- no hidden composite score determines the frontier;
- C0 cannot disappear;
- screening decisions are reversible and auditable.

Audit both the low-level relation and its actual pipeline callers.

## F-05 — Policy identity and drift prevention

Verify machine-checkable identity for:

- baseline sequencing;
- alternate sequencing;
- baseline mulligan;
- alternate mulligan;
- baseline Boulder scry;
- alternate Boulder scry;
- baseline reserve;
- tap-out reserve;
- baseline information valuation;
- alternate information valuation.

Confirm that hashes bind actual executable behavior, not only descriptive registry text. A source-code behavior change that leaves registry prose unchanged must still be detected by the code/config provenance controls.

Construct states where:

- baseline reserve and tap-out intentionally differ;
- baseline and alternate sequencing differ;
- baseline and alternate mulligans differ;
- baseline and alternate scry differ;
- baseline and alternate information policies differ.

Check that result rows record every relevant policy/scenario identity and hash.

Confirm screening and validation cannot silently use different policies except under a labeled robustness scenario.

## F-06 — Mechanic coverage and containment

Review every row in `RUN_G_MECHANICS_COVERAGE.csv`.

For each `IMPLEMENTED + TESTED` row, locate the real production implementation and sensitive test.

For every `NOT MATERIAL` row, challenge the classification and require a concrete containment argument.

Pay special attention to:

- Refurbished Familiar’s conditional draw;
- Blood token activation;
- Blood Fountain recursion;
- Makeshift Munitions activation;
- Cryogen stun activation;
- opponent target arrival;
- opponent removal;
- Bridge indestructibility.

Determine whether any excluded mechanic can plausibly reorder candidate mana bases through color, untapped mana, artifact count, affinity, Metalcraft, sacrifice timing or resilience.

If a ranking-relevant mechanic is absent and has no convincing frozen containment sensitivity, authorization fails.

## F-07 — Planner depth and information boundaries

Reproduce all six Run G structural classes:

- Boulder with multiple spells;
- affinity changing mid-sequence;
- Hawk return/replay with competing lines;
- interaction hold versus development;
- representative double-spell state;
- Bargain resource and trigger composition.

Verify:

- depths 7/8/9 independently;
- root choice;
- terminal/result counts;
- candidate-neutral state construction;
- baseline and tap-out sensitivity;
- information-policy sensitivity;
- hidden-library invariance before reveal;
- permissible divergence after reveal.

Add independent adversarial states within these classes where tractable. Check whether the fixture corpus is genuinely sensitive to depth/pruning defects rather than trivially stable because all relevant lines terminate early.

Confirm planner depth and action bounds are read from the frozen Phase 3 config during production execution.

## F-08 — Provenance and reproducibility

From an untouched fresh extraction:

- regenerate the allowlisted source/config/test manifest;
- require exact file-set and hash equality;
- confirm no cache/generated file is included;
- confirm no source/config/test file is omitted;
- confirm the content-tree hash is stable;
- confirm running tests or readiness does not mutate immutable provenance;
- confirm policy behavior is covered by the source tree identity;
- confirm ZIP identity and content-tree identity have clear, non-circular roles.

Run the readiness gate independently from two fresh extractions and compare normalized ordinary content.

---

# 7. FROZEN CONFIGURATION AUDIT

Review `RUN_G_PHASE3_FROZEN_CONFIG.yaml` line by line.

Reject authorization if any behaviorally relevant field is:

- zero when it should be a production value;
- blank;
- ambiguous;
- prose-only where code requires a value;
- inconsistent with implementation;
- impossible to enforce;
- selected after viewing results;
- dependent on an unstated manual step.

Audit at minimum:

- deck path/hash;
- parent archive hash;
- candidate rules;
- C0;
- target horizon;
- all seeds;
- replicate use;
- play/draw weights;
- mulligan policies;
- sequencing policies;
- reserve policies;
- scry policies;
- information policies;
- planner depth/action bounds;
- metric lists;
- profiles;
- trial counts;
- screening safety;
- multiplicity;
- finalist retention;
- validation/adaptive precision;
- practical tolerances;
- robustness scenarios;
- output files;
- stop conditions;
- authorization status.

Confirm that Run H authorization could be represented without rewriting scientific parameters.

---

# 8. STATISTICAL AUDIT

Verify that the frozen design properly separates:

- raw measurements from profile comparisons;
- sampling uncertainty from model uncertainty;
- statistical significance from practical significance;
- selection randomness from validation randomness;
- exploratory screening from confirmatory validation.

Audit:

- common-random-number pairing;
- exact pairing-key alignment;
- selection-stage multiplicity;
- confirmatory multiplicity;
- winner’s-curse containment;
- adaptive validation rules;
- near-boundary retention;
- profile conflict;
- regret computation;
- frontier uncertainty.

Check whether the proposed trial counts and stopping rules are operationally meaningful. Do not claim they are sufficient merely because they are nonzero.

No simulator metric may be translated into match-win-rate points.

---

# 9. ADVERSARIAL TEST REQUIREMENTS

At minimum, add external audit-only tests for:

- config completeness;
- behaviorally meaningful policy hash drift;
- C0 retention at every serious stage;
- protected 3-Bridge-class retention;
- candidate-order invariance;
- candidate-label invariance;
- profile calculations;
- profile overlap metadata;
- leave-one-out variants;
- de-correlated variants;
- metric aggregation completeness;
- critical-sequence correctness;
- safe dominance;
- unresolved screening retention;
- validation-seed isolation;
- policy/scenario provenance;
- unsupported-mechanic blocking;
- fresh-extraction manifest equality;
- dry-run reproducibility;
- dry-run non-ranking attestation;
- production-path completeness behind the authorization gate.

Store Run H helpers and evidence outside the extracted Run G package.

---

# 10. AUTHORIZATION STANDARD

Authorize Phase 3 only if all of the following are true:

- exact Run G package verified;
- all original and Run G tests pass fresh;
- all eight Run F blockers are independently closed;
- the real production path is complete behind the authorization gate;
- profiles and aggregations are executable rather than descriptive;
- screening cannot eliminate from noisy means;
- dominance/frontier logic respects direction, materiality and uncertainty;
- selection and validation are technically isolated;
- policy drift controls bind actual behavior;
- no ranking-relevant unsupported mechanic remains;
- planner-depth evidence is structurally meaningful;
- provenance reconciles exactly;
- no optimization occurred during Run H.

A readiness gate passing its own tests is necessary but not sufficient.

---

# 11. REQUIRED RUN H DELIVERABLES

Produce:

1. `RUN_H_PHASE3_AUTHORIZATION_REPORT.md`
2. `RUN_H_ACCEPTANCE_MATRIX.csv`
3. `RUN_H_DEFECTS.md`
4. `RUN_H_FROZEN_CONFIG_AUDIT.md`
5. `RUN_H_PIPELINE_EXECUTABILITY_AUDIT.md`
6. `RUN_H_PROFILE_AND_METRIC_AUDIT.md`
7. `RUN_H_STATISTICAL_AUDIT.md`
8. `RUN_H_MECHANICS_AND_MODEL_RISK_AUDIT.md`
9. `RUN_H_PROVENANCE_REPRODUCIBILITY.md`
10. `RUN_H_NO_OPTIMIZATION_ATTESTATION.md`
11. all audit-only helpers and machine-readable evidence
12. an archive and detached SHA-256 for the complete Run H audit package

Map every F-01 through F-08 blocker to:

- Run G claim;
- independent reproduction;
- adversarial test;
- observed result;
- PASS/FAIL;
- remaining risk;
- authorization consequence.

---

# 12. FINAL VERDICT

Return exactly one:

### `RUN H AUTHORIZATION — PHASE 3 AUTHORIZED`

Use only if every authorization-critical requirement passes and no production-path implementation remains to be invented.

OR:

### `RUN H AUTHORIZATION — PHASE 3 NOT AUTHORIZED`

Use if any blocker, major execution gap, unsupported ranking-relevant mechanic, unresolved provenance issue or scientifically material ambiguity remains.

Do not patch Run G. Do not issue a conditional authorization that silently requires later code changes. If remediation is needed, enumerate the exact defects for a separate Run I remediation task.

---

# 13. FINAL RESPONSE FORMAT

Return:

**A. Run H verdict**

**B. Input integrity**
- Run G ZIP name;
- expected SHA-256;
- observed SHA-256;
- fresh-extraction test results.

**C. F-01 through F-08 audit table**

**D. Production-path executability assessment**

**E. Statistical and scientific assessment**

**F. Mechanics and model-risk assessment**

**G. Provenance and reproducibility assessment**

**H. Authorization blockers or conditions**

**I. No-optimization attestation**

**J. Deliverable links**

Stop there. Do not discuss which mana base might be best.