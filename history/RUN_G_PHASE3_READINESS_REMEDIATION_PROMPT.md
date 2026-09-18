# MANA LAB — PAUPER v1
## RUN G — PHASE 3 READINESS REMEDIATION IMPLEMENTATION + REVALIDATION

### RECOMMENDED CONFIGURATION
- Mode: **Work**
- Model: **GPT-5.6 Sol**
- Reasoning: **High**
- Web: **OFF**
- Primary production input: **`Mana_Lab_Pauper_v1_Run_E.zip`**
- Required parent SHA-256: **`82d1dcd663de5a8bcb2d9917271fba264c509bdff8b45d1920b9f97ccf0d0c71`**
- Supporting input: **`Mana_Lab_Pauper_v1_Run_G_Input_Supplement.zip`**
- Audit authority: the complete **Run F — Phase 3 Authorization Audit** outputs if present in the project/workspace
- Output: patched Run G repository archive + Phase-3 readiness artifacts

**Do NOT perform mana-base optimization. Do NOT screen, rank, shortlist, construct a candidate frontier, or recommend a mana base.**

---

# 1. ROLE

Act as a senior:
- Python simulation and experiment-pipeline engineer;
- Monte Carlo/statistical validation engineer;
- optimization-methodology engineer;
- reproducibility engineer;
- Magic: The Gathering rules/modeling specialist;
- competitive Pauper Affinity sequencing specialist;
- adversarial software QA reviewer.

You are repairing **Mana Lab — Pauper v1** after **Run F failed Phase 3 authorization**. The measurement engine has already survived substantial implementation QA. Your task is to make the **Phase 3 decision/execution layer explicit, safe, frozen, testable, and reproducible** without running the actual optimization.

---

# 2. AUTHORITATIVE INPUT / INTEGRITY GATE

Before editing anything:

1. Locate `Mana_Lab_Pauper_v1_Run_E.zip`.
2. Compute SHA-256.
3. Require exact match:
   `82d1dcd663de5a8bcb2d9917271fba264c509bdff8b45d1920b9f97ccf0d0c71`
4. Extract to a fresh directory.
5. Run the existing full test suite before modification.
6. Reconcile against Run E's known state: **179 tests passed**, D-01 through D-11 regressions passed, candidate count **296,706**, C0 exactly once.
7. If the exact parent ZIP is unavailable or the hash mismatches, STOP with:
   **`INPUT BLOCKED — EXACT RUN E PARENT MISSING OR HASH MISMATCH`**

Do not substitute Run C. Do not reconstruct production source from the specification packet.

If full Run F files are available, treat them as the defect authority, especially:
- `RUN_F_PHASE3_AUTHORIZATION_REPORT.md`
- `RUN_F_ACCEPTANCE_MATRIX.csv`
- `RUN_F_PHASE3_FROZEN_CONFIG.md`
- `RUN_F_REPRODUCIBILITY.md`
- `RUN_F_DEFECTS.md`
- `audit_helpers.py`

If some Run F artifacts are unavailable, use `RUN_F_FAILURE_BRIEF.md` as the minimum known defect set and explicitly mark any unknown Run F item as unresolved rather than inventing it.

---

# 3. NON-NEGOTIABLE SCOPE

This is **readiness remediation**, not execution.

Allowed:
- code/config/schema changes;
- deterministic checks;
- unit/integration/regression tests;
- synthetic/toy candidate tests;
- tiny protected smoke runs whose outputs are not interpreted competitively;
- exact candidate-count verification;
- dry-run pipeline wiring;
- config/provenance/hash generation.

Forbidden:
- performance screening of the 296,706 legal bases;
- candidate ranking or scoring for competitive selection;
- finalist selection;
- high-precision candidate comparisons;
- Pareto/frontier construction on real candidate performance;
- any mana-base recommendation;
- any claim that C0 or another base is better.

If a test needs multiple candidates, use synthetic fixtures or explicitly non-inferential protected smoke cases only.

---

# 4. PRIMARY RUN F REMEDIATION TARGETS

Close every Run F blocking finding. At minimum, address these known categories.

## G1 — Phase 3 pipeline exists as executable code
Implement a reproducible staged pipeline with explicit entry points for:
1. input/config validation;
2. exact candidate enumeration / deterministic features;
3. safe screening;
4. medium paired simulation;
5. finalist selection;
6. fresh independent validation;
7. robustness/sensitivity runs;
8. Pareto/frontier analysis;
9. reporting.

Each stage must:
- read frozen config rather than hidden constants;
- write machine-readable outputs;
- preserve candidate identity deterministically;
- record code/config/seed hashes;
- refuse to continue when prerequisites fail;
- support a **dry-run/readiness mode** that proves wiring without real optimization.

Do not execute stages 3–9 on the real candidate space in Run G.

## G2 — Freeze a concrete Phase 3 experiment configuration
Create a benchmark-specific frozen config for Strixpatch Affinity v1.3, separate from generic templates.

It must explicitly define:
- exact deck-spec path/hash;
- candidate-space rules;
- C0 protection;
- selection seed(s);
- validation seed(s) independent from selection;
- replicate seeds if used;
- play/draw scenarios;
- baseline + alternate London mulligan profiles;
- baseline + alternate sequencing profiles;
- target turn horizon;
- raw primary/secondary metrics;
- screening trial count and safety rule;
- medium and validation trial counts;
- finalist-retention rule;
- uncertainty method;
- practical/materiality tolerances;
- multiple-comparison handling where relevant;
- robustness scenarios;
- output files;
- stop conditions.

No zero/blank placeholder that affects Phase 3 behavior may remain.

## G3 — Fully define named decision profiles
The project requires at least:
- balanced functionality;
- tempo-sensitive;
- color-consistency;
- interaction-sensitive;
- double-spell-sensitive.

For every profile, specify in code/config/documentation:
- exact metric vector or exact formula;
- metric directions;
- aggregation across turns/spells/scenarios;
- normalization, if any;
- practical/materiality tolerance;
- overlap/double-counting rationale;
- missing-data behavior;
- tie behavior;
- uncertainty handling.

Prefer transparent **metric vectors / lexicographic or Pareto-safe rules** over one opaque master score. If any weighted composite is used, weights must be explicit and justified, with leave-one-component-out and de-correlated variants defined before execution.

No profile may exist only as a label.

## G4 — Replace unsafe Pareto/dominance logic
Implement and test an uncertainty-aware dominance relation.

A candidate may not be declared to dominate another merely because point estimates are numerically better.

The implementation must distinguish:
- exact/deterministic dimensions;
- paired stochastic differences;
- practical equivalence/no-worse tolerances;
- material improvement;
- unresolved comparisons.

Requirements:
- metric directions are explicit;
- no dominance on hidden composite scores;
- no irreversible screen elimination from noisy means alone;
- close/uncertain comparisons remain unresolved;
- C0 can never disappear because of a bookkeeping/screening shortcut;
- synthetic test fixtures prove dominant, dominated, tied, practically equivalent, and statistically unresolved cases.

Document the exact statistical rule used for screening elimination and final Pareto status. If family-wise or multiplicity control is needed, make it explicit.

## G5 — Prevent policy drift
Freeze the exact production policy identities used by Phase 3.

Add machine-checkable policy provenance for:
- baseline sequencing;
- alternate sequencing;
- baseline London mulligan;
- alternate London mulligan;
- Boulder scry policy where relevant;
- opponent-window reserve behavior.

Each policy should have a stable version/id and content/config hash. Every Phase 3 result row or manifest must identify the policy/scenario used.

The pipeline must fail fast if:
- a requested policy name is missing;
- policy content/hash differs from the frozen config;
- screening and validation silently use different production policies.

Policy changes are allowed only as explicit robustness scenarios and must be labeled as such.

## G6 — Resolve unsupported-mechanic gaps
Create a benchmark mechanic coverage registry for every mana-relevant Strixpatch mechanic.

For each required mechanic classify exactly one:
- `IMPLEMENTED + TESTED`
- `IMPLEMENTED, NEEDS TEST`
- `NOT IMPLEMENTED`
- `NOT MATERIAL`

At minimum audit:
- artifact lands;
- ETB-tapped Bridges;
- Giant's Boulder deployment/filtering/tap limits/scry;
- affinity/cost reduction;
- artifact count + Metalcraft;
- Baleful Strix UB payment;
- Dispatch white + Metalcraft distinction;
- Glint Hawk return/replay sequencing;
- Reckoner's Bargain payment/sacrifice/resource effects;
- Thoughtcast/Myr Enforcer/Refurbished Familiar/Utrom Monitor affinity;
- Cryogen Relic draw behavior;
- opponent-turn Blast/Dispatch/Bargain availability;
- Blood/Nihil/Munitions/Cryogen-stun options where the current model exposes them;
- London mulligan;
- play/draw.

Any decision-relevant `NOT IMPLEMENTED` mechanic blocks readiness.

For target-dependent effects whose value cannot be modeled without opponent assumptions, either:
- keep them as raw option/counterfactual metrics excluded from competitive objective profiles; or
- add explicit frozen sensitivity fixtures.

Never assign speculative target-arrival value silently.

## G7 — Phase 3 acceptance and adversarial tests
Add tests covering at least:
- concrete config completeness/no placeholders;
- seed partition independence;
- C0 forced inclusion in every serious stage;
- candidate identity/order invariance;
- no candidate-specific policy behavior;
- profile calculation correctness;
- profile overlap metadata present;
- Pareto safe/no-worse/material-better semantics;
- unresolved stochastic comparisons remain unresolved;
- screening cannot eliminate from insufficient evidence;
- fresh validation seed cannot equal selection seed;
- policy hash drift aborts;
- unsupported ranking-relevant mechanic blocks readiness;
- dry-run pipeline does not produce rankings/recommendations;
- output schema contains candidate/config/policy/seed provenance;
- same config+seed reproduces same dry-run artifacts.

Keep all Run E regression tests passing.

## G8 — Readiness command / gate
Provide one command that performs the complete **pre-optimization readiness gate** without doing actual optimization, for example:

`PYTHONPATH=src python -m mana_lab.phase3_readiness --config <frozen-config>`

It should verify:
- parent/config integrity;
- full tests;
- exact candidate count = 296,706;
- C0 exactly once;
- no blank Phase 3 settings;
- policy hashes;
- mechanic registry;
- objective/profile definitions;
- Pareto/screening synthetic tests;
- seed separation;
- output/provenance schema;
- dry-run stage wiring.

It must finish with a machine-readable PASS/FAIL and must not evaluate real candidate performance.

---

# 5. SCIENTIFIC / STATISTICAL RULES

Preserve the Mana Lab principles:
- raw measurements before scores;
- every metric/objective term precisely defined;
- event-level outcomes retained where required;
- no automatic double counting;
- leave-one-component-out / de-correlated objective variants predeclared;
- paired/common-random-number comparisons where valid;
- independent selection vs validation randomness;
- practical significance separate from Monte Carlo significance;
- no match-win-rate inference from simulator scores;
- model uncertainty separate from sampling uncertainty;
- no forced unique winner.

The readiness implementation should make these constraints hard to violate accidentally.

---

# 6. PRESERVATION RULES

Do not change:
- the locked 60-card benchmark definition;
- the frozen 41 nonlands;
- the 19-land requirement;
- the legal candidate pool/copy limits;
- C0 definition;
- validated mana/payment/state semantics unless a Run F defect proves a necessary correction.

If production engine code must change, document:
- why;
- exact functions/files;
- ranking relevance;
- new regression tests;
- whether prior Run E validation still holds.

Do not redesign the deck.

---

# 7. REQUIRED DELIVERABLES

Produce at minimum:

1. `Mana_Lab_Pauper_v1_Run_G.zip`
2. `Mana_Lab_Pauper_v1_Run_G.zip.sha256`
3. `RUN_G_PHASE3_READINESS_REPORT.md`
4. `RUN_G_CHANGELOG.md`
5. `RUN_G_PHASE3_FROZEN_CONFIG.yaml`
6. `RUN_G_DECISION_PROFILE_SPEC.md`
7. `RUN_G_MECHANICS_COVERAGE.csv`
8. `RUN_G_PHASE3_PIPELINE_SPEC.md`
9. `RUN_G_ACCEPTANCE_MATRIX.csv`
10. `RUN_G_REPRODUCIBILITY.md`
11. `RUN_G_PROVENANCE.md`
12. `RUN_G_NO_OPTIMIZATION_ATTESTATION.md`

Also preserve all source/tests/configs needed for one-command reproduction.

The report must map every Run F defect to:
- remediation;
- changed files/functions;
- tests;
- PASS/FAIL status;
- residual risk.

If the full Run F defect list is available, all eight blockers must be mapped individually. If it is unavailable, explicitly state which blockers could not be independently reconstructed and do **not** claim complete remediation.

---

# 8. COMPLETION STANDARD

Return exactly one implementation verdict:

### `RUN G IMPLEMENTATION — READY FOR INDEPENDENT PHASE 3 AUTHORIZATION`
Use only if:
- exact Run E parent/hash verified;
- all prior tests pass;
- all new readiness tests pass;
- all known Run F blockers are closed;
- no decision-relevant unsupported mechanic remains;
- the frozen Phase 3 config is complete;
- pipeline/profile/Pareto/policy-drift controls are executable;
- no optimization occurred.

OR:

### `RUN G BLOCKED — PHASE 3 NOT READY`
Use if any authorization-critical item remains unresolved.

**Do not authorize Phase 3 yourself.** A subsequent independent Run H audit must make that authorization decision.

---

# 9. FINAL RESPONSE FORMAT

Return:

**A. Run G verdict**

**B. Parent integrity**
- input ZIP name;
- expected SHA-256;
- observed SHA-256;
- baseline test count/result.

**C. Run F blocker remediation table**

**D. Tests and readiness-gate results**

**E. Files changed**

**F. Remaining limitations / model risk**

**G. No-optimization attestation**

**H. Deliverable links**

Stop there. Do not discuss which mana base looks best.
