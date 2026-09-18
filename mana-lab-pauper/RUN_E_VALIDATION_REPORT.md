# Mana Lab — Pauper v1 Run E validation report

## A. Executive result

Remediation status: **PASS**. Phase-3 readiness for independent authorization: **YES**. No mana-base optimization, screening, ranking, finalist selection, or Pareto analysis was performed.

## B. Provenance

- Input ZIP SHA-256: `0d99524f834a09bae1c256d8dd57ad06b2265e35a824f7104697e569bcb9a5e7` (verified before extraction).
- Run C implementation marker supplied: `1e81305724376ede4387bdbe6080cdc0f32339ee`.
- Run C packaging marker supplied: `5220d16ade01610d9d5656a062021048b3f0fff5`.
- Patched source commit: `f6a2dcaf604f4b14566ae0e269f6535754b365d1`.
- Final output ZIP SHA-256 is written after packaging to the detached `Mana_Lab_Pauper_v1_Run_E.zip.sha256` manifest because an archive cannot contain its own final hash.
- Frozen source/config hashes: `outputs/run_e/source_config_hashes.json`.

## C. Patch table

| Run D ID | Severity | Root Cause | Files Changed | Repair | Regression Test | Result |
|---|---|---|---|---|---|---|
| D-01 | BLOCKER | Production planner omitted future-color land value | `policies.py; simulator.py` | Visible future coverage in terminal action score | `test_run_e_d01_production_land_semantics.py` | PASS |
| D-02 | BLOCKER | Alternate score maximized negative untapped mana | `policies.py` | Explicit tempo precedence maximizes untapped resources | `test_run_e_d02_alternate_tempo.py` | PASS |
| D-03 | BLOCKER | Search terminated all continuation at information nodes | `simulator.py; policies.py` | Unresolved causal nodes permit known-card continuation; two value profiles | `test_run_e_d03_information_continuation.py` | PASS |
| D-04 | BLOCKER | Land loss subtracted held lands and followed velocity | `simulator.py; policies.py` | Physical battlefield loss and color/source deltas precede optional velocity | `test_run_e_d04_bargain_land_loss.py` | PASS |
| D-05 | BLOCKER | Bargain cleared composed triggers | `simulator.py` | Spell-below-trigger queue retained and resolved compositionally | `test_run_e_d05_trigger_composition.py` | PASS |
| D-06 | BLOCKER | Raw Hawk cast counted as functional | `simulator.py` | Raw cast and mandatory functional resolution separated | `test_run_e_d06_hawk_functionality.py` | PASS |
| D-07 | MAJOR | Priority prose/code ambiguity | `policies.py; RUN_E_POLICY_SPEC.md` | One executable lexicographic precedence | `test_run_e_d07_policy_precedence.py` | PASS |
| D-08 | MAJOR | Repeated spell windows lacked denominator identity | `state.py; simulator.py; metrics.py` | Unique opportunity IDs, roles, sequences and pairing context | `test_run_e_d08_metric_windows.py` | PASS |
| D-09 | MAJOR | Dependency meant both used and necessary | `payment.py; simulator.py` | Separate used/rescue/dependency fields with counterfactual | `test_run_e_d09_boulder_metrics.py` | PASS |
| D-10 | MAJOR | Paired estimator accepted positional mismatches | `statistics.py` | Keyed observations and strict ordered identity checks | `test_run_e_d10_paired_statistics.py` | PASS |
| D-11 | MAJOR | Fixture-only options advertised as production metrics | `metrics.py; simulator.py` | Nihil production events; three target-dependent options validation-only | `test_run_e_d11_option_events.py` | PASS |

## D. Production-planner reconstruction

The executable planner generates land plays, spells, distinct payment outcomes, Boulder filters, Hawk return targets, and Bargain sacrifice targets in one action graph. Baseline precedence is: hard deadline; payable opponent reply; battlefield-land/untapped/color preservation; functional due execution; artifact preservation; visible future joint/color access; current usable resources; other functional executions; causal information value; raw casts. The alternate policy moves immediately untapped resources directly after deadline/reserve. Canonical keys are only final ties.

Unknown draws/scries create unresolved information nodes. Search continues only with already-visible cards and resources, never with hidden identities. Execution then reveals legally and replans. Bargain places the spell below triggers produced by its additional cost. Hawk and Bargain emit separate raw-cast and functional-resolution events. State keys cover physical identities, tapped state, land drop, mana pool, trigger queue and unresolved information.

## E. Run D reproducer results

| ID | Frozen Run C behavior | Expected | Run E behavior | Result |
|---|---|---|---|---|
| D-01 | Production chose Drossforge in Vault + two Bridges + Strix | Mistvault for visible U+B future access | Production chooses Mistvault under order permutations | PASS |
| D-02 | Alternate tempo could prefer tapped Goldmire to untapped Den | Maximize immediate untapped resource | Production chooses Ancient Den | PASS |
| D-03 | Information action ended all planning, including known cards | Continue known deterministic actions without hidden identity | Strix/Thoughtcast/Cryogen/Bargain/Boulder continuation is present | PASS |
| D-04 | Bargain could sacrifice a mana land for velocity; held land masked loss | Preserve battlefield mana absent higher deadline | T3 passes; nonland sacrifices work; explicit T4 deadline exception works | PASS |
| D-05 | Bargain cleared Nihil trigger | Preserve/order all generated triggers | Nihil/Cryogen resolve before Bargain draws; payable/declined paths explicit | PASS |
| D-06 | Self-sacrificed Hawk received execution credit | Raw cast true, functional outcome false | Separate events/counters enforce distinction | PASS |
| D-07 | Prose and code precedence conflicted | One executable priority order | Conflict fixtures follow the documented tuple | PASS |
| D-08 | Repeated spell windows shared an ambiguous denominator | Unique opportunity identity and role | Trial/turn/phase/sequence/card/profile IDs emitted | PASS |
| D-09 | Dependency meant both use and necessity | Separate used/rescue/dependency | Native and strict-dependency fixtures agree across events | PASS |
| D-10 | Equal-length shuffled vectors were accepted | Strict pairing-key identity | Missing/duplicate/shuffled/scenario/replicate mismatches reject | PASS |
| D-11 | Some option metrics existed only in fixtures | Emit normally or mark validation-only | Nihil emits normally; Blood/Munitions/Cryogen stun are validation-only | PASS |

The unchanged Run C baseline suite also passes. Machine-readable mapping: `outputs/run_e/regression_results.json`.

## F. No-lookahead validation

**18 tests passed.** Same visible state/different hidden library remains root-invariant; post-reveal decisions may diverge.

## G. Search-horizon sensitivity

Depths 7/8/9 were compared on **16** ordinary/targeted production states. Root-choice divergences: **0**. Depth 8 retained: **True**. Details: `outputs/run_e/horizon_sensitivity.json`.

## H. Chance-node valuation sensitivity

Baseline vs conservative causal information heuristics were compared on **16** states; root divergences: **0**. Legal actions are identical; only unrevealed information credit differs. Details: `outputs/run_e/information_valuation_sensitivity.json`.

## I. Rules/mechanics validation

Bargain/Nihil/Cryogen trigger order, optional black payment, Boulder net-zero filtering, Hawk mandatory return, Bridge replay, affinity and Metalcraft transitions pass deterministic and production-path tests.

## J. Metric/event-schema validation

All **29** configured metrics have complete numerator, denominator, timing, grain, opportunity-ID, deduplication, missing-data, snapshot-role, direction and correlation-family definitions. Blood, Munitions and Cryogen stun options are validation-only; Nihil is production-observable.

## K. Statistics/RNG validation

Keyed paired observations reject missing, duplicate, shuffled, scenario-mismatched and replicate-mismatched identities. Closed-form mean/SE/CI fixtures pass. Seed partition: **PASS**. Candidate-label and candidate-order randomness checks pass.

## L. Candidate-neutrality validation

Core policy-source scan forbidden-branch hits: **0**. Hand, battlefield, payment, duplicate-card and candidate-order permutations pass.

## M. Full test results

**179 passed; 0 failed; 0 skipped.**

## N. Production smoke

Protected benchmark fixtures only; baseline/alternate sequencing and mulligans executed. Candidate-order-normalized raw traces reproduced: **PASS**. Smoke output is machinery validation and is not interpreted as performance evidence.

## O. Remaining limitations

Opponent behavior and target arrival remain unspecified. Target-dependent Blood, Munitions and Cryogen stun activations remain validation-only. Information heuristics are explicit subjective policy controls, not omniscient expected values. Another short independent audit is recommended before expensive optimization.

## P. Phase-3 gate

**RUN E IMPLEMENTATION GATE — PASS**

**PHASE 3 READY FOR INDEPENDENT AUTHORIZATION — YES**
