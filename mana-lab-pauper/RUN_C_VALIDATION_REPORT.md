# Mana Lab — Pauper v1 Run C validation report

## Executive result

### `RUN C IMPLEMENTATION — READY FOR INDEPENDENT QA`

Run C repaired and revalidated the measurement engine. It did not simulate the legal candidate space for performance, rank candidates, construct a frontier, or recommend a mana base. Phase 3 remains unauthorized pending Run D.

## Implemented patches

| Patch | Run B finding | Files changed | Status | Validation |
|---|---|---|---|---|
| P1 | Causal/no-lookahead action search | `simulator.py; policies.py` | PASS | Run C causal + information-boundary suite |
| P2 | First-valid payment/search-order dependence | `payment.py; simulator.py` | PASS | payment branching + permutation fixtures |
| P3 | Individually-castable land shortcut | `policies.py; simulator.py` | PASS | executable sequence land-policy fixtures |
| P4 | Forced land-before-spell sequencing | `simulator.py; state.py` | PASS | Hawk return/replay and order-shape fixtures |
| P5 | Boulder/Bargain/opponent-window gaps | `payment.py; simulator.py; policies.py; effects.py` | PASS | integrated mechanics fixtures |
| P6 | Boulder scry semantic mismatch | `policies.py` | PASS | missing-color/castability/hidden-third fixtures |
| P7 | Additive reserve proxy | `policies.py; simulator.py` | PASS | actual-resource reserve fixtures |
| P8 | Incomplete Phase-3 event schema | `simulator.py; metrics.py` | PASS | metric dictionary + deterministic fixtures |
| P9 | Only 72 full-policy smoke trials | `simulator.py; run_c_validation.py` | PASS | production policy on every protected trial |

## Architecture

- Root actions are chosen from visible state only. Search stops at draws and scry; execution reveals information and invokes the policy again.
- Payment search enumerates all strategically distinct post-payment resource states and deduplicates only identical resulting resources.
- Land plays, spells, Hawk returns, Bargain sacrifices, and payment plans share one bounded action graph.
- Baseline reserve distinguishes held, payable, demanded, preserved, and spent interaction. No opponent action probability is invented.
- Raw typed events capture pre-spend snapshots, desired spell windows, ETB blockage, multi-action feasibility, filters, thresholds, Hawk/Bargain transitions, and opponent windows.

## Validation

- Full unit suite: **133 passed, 0 failed, 0 skipped**.
- Separate no-lookahead execution: **18 passed, 0 failed**.
- Frozen deck: **60 cards / 41 nonlands / 19 lands / four Giant's Boulders**.
- Candidate enumeration: **296,706**; independent DP: **296,706**; C0 occurrences: **1**.
- Minimum Bridges: **3**; three-Bridge class: **56**.
- T2 Myr Enforcer relaxed impossibility fixture: **PASS**.
- Metric contract: **PASS** for every configured primary/secondary metric.
- Independent seed partition: **PASS**.
- Cheap engine exact-vs-simulation smoke: **PASS** at **20,000** raw sevens.
- Production-policy smoke: **2 trials per scenario/candidate**, every trial using the production planner; protected fixtures only; no comparisons interpreted.
- Same-config/seed reproducibility rerun: **PASS** on decompressed/ordinary content hashes.

## No-lookahead result

Current decisions were invariant when only hidden library content changed for mulligan keep/bottom, land choice, root spell action, payment, Bargain sacrifice, Hawk return, Boulder deployment, Boulder scry, Thoughtcast, Strix, and Cryogen. Later decisions may react only after draw/scry information is legally revealed.

## Candidate neutrality

Policy definitions, depth, pruning, and tie breaks contain no candidate identity. Hand, land, battlefield, and payment permutations passed. Random draws are paired by scenario/trial/attempt and do not depend on candidate iteration order.

## Remaining limitations

- Opponent behavior and target arrival probabilities remain unspecified; interaction is therefore a raw counterfactual resource metric.
- Target-dependent late Boulder, Cryogen stun, Munitions, Blood, and Nihil choices require explicit fixtures and are not assigned speculative value.
- The own-main planner is bounded to depth 8 (12 executed replans). This covers the frozen turn-1–4 benchmark fixtures but must be re-audited before scope expansion.
- Desired timing profiles and baseline/alternate heuristics are frozen subjective assumptions, not empirical play-rate claims.
- Production smoke is machinery validation, not a precision performance experiment.
- The separate Run B report file was not supplied; the complete Run B ruling and counterexamples embedded in the Run C instruction were used as the audit authority.

## Phase 3 readiness statement

The implementation package is ready to be submitted for independent Run D audit. Run C does not authorize Phase 3.

### `RUN C IMPLEMENTATION — READY FOR INDEPENDENT QA`
