# Mana Lab — Pauper v1 Run G Phase 3 readiness report

## A. Run G verdict

**RUN G IMPLEMENTATION — READY FOR INDEPENDENT PHASE 3 AUTHORIZATION**

This is an implementation/readiness verdict only. Run G does not authorize Phase 3. An independent Run H audit must decide authorization.

## B. Parent integrity

- Input: `Mana_Lab_Pauper_v1_Run_E.zip`.
- Expected SHA-256: `82d1dcd663de5a8bcb2d9917271fba264c509bdff8b45d1920b9f97ccf0d0c71`.
- Observed SHA-256: `82d1dcd663de5a8bcb2d9917271fba264c509bdff8b45d1920b9f97ccf0d0c71`.
- Untouched baseline: 179 tests passed.
- Run E D-01 through D-11 regressions remained passing.
- Candidate space: 296,706 by production enumeration and independent DP; C0 exactly once; 56 minimum-Bridge candidates.

## C. Run F blocker remediation

| Run F | Remediation | Changed files/functions | Regression evidence | Status | Residual risk |
|---|---|---|---|---|---|
| F-01 | Nine-stage artifact graph; immutable prerequisites; C0/protected-class retention; conservative screening; fresh validation; dry run | `phase3_pipeline.py`; frozen config | `test_run_g_dominance_pipeline.py` | PASS | Real execution remains intentionally blocked pending Run H |
| F-02 | Six exact lexicographic metric vectors with direction, aggregation, tolerances, missingness, uncertainty, overlap rationale, leave-one-out and de-correlation | frozen config; `phase3_profiles.py` | `test_run_g_config_profiles.py` | PASS | Profile priority is explicit model judgment |
| F-03 | Registry-complete aggregation routing; event/opportunity duplicate rejection; denominator reconstruction; eleven critical-sequence predicates; provenance schema | `phase3_metrics.py` | `test_run_g_event_aggregation.py` | PASS | Target-dependent value is excluded, not estimated |
| F-04 | Direction-, tolerance- and paired-CI-aware dominance; exact/stochastic distinction; unresolved status; safe screening | `metrics.py::uncertainty_aware_dominance`; `safe_screen_decision` | dominant/equivalent/lower/uncertain/missing fixtures | PASS | Frontier conclusions still require fresh validation evidence |
| F-05 | Machine-checkable policy IDs/hashes; unknown/hash drift abort; reserve policy separated from sequencing; true tap-out executable and labeled | `phase3_policies.py`; `policies.py::choose_action`; simulator policy propagation | policy drift and baseline-versus-tap-out fixtures | PASS | Policy sensitivity remains a required robustness axis |
| F-06 | Every benchmark mechanic classified; ranking-relevant rows require `IMPLEMENTED + TESTED`; target/opponent assumptions contained as raw counterfactuals or `NOT MATERIAL` boundaries | mechanic CSV; readiness validator | registry coverage/blocking tests | PASS | Opponent target/removal model remains out of scope and explicit |
| F-07 | Six targeted structural classes; depth 7/8/9 root stability; terminal-state counts; reserve sensitivity | `phase3_depth.py` | structural audit: 6/6 stable | PASS | Fixture stability is not a proof over every reachable state |
| F-08 | Explicit allowlist; caches/generated files excluded; exact file equality; content-tree SHA-256 | `provenance.py`; source manifest | cache exclusion and repeatability test | PASS | No Git history in the archive; content identity replaces it |

## D. Tests and readiness gate

- Patched full suite: 205 tests passed, 0 failed, 0 skipped.
- Required five profiles plus affinity/value-engine profile: complete.
- Policy hash drift: aborts.
- Selection/validation seeds: distinct; all replicate seeds distinct.
- Candidate identity and policy behavior: candidate-neutral; preexisting label/order invariance regressions pass.
- Dominance fixtures: decisive, dominated/no-worse inversion, practical equivalence, lower-is-better and statistically unresolved cases pass.
- Screening fixtures: C0, insufficient evidence and uncertainty cannot be eliminated.
- Dry-run stage graph: reproducible; no ranking or recommendation fields produced.
- Planner depth: all six predeclared structural classes stable at 7/8/9.
- Mechanic registry: no decision-relevant unsupported gap.
- One-command readiness result: machine-readable PASS.

## E. Files changed

Production code changed only in `src/mana_lab/metrics.py`, `policies.py` and `simulator.py`; eight focused Run G modules were added. Five Run G test files were added. The frozen config, mechanic registry and required reports/specifications were added at repository root. Exact paths are enumerated by `outputs/run_g/source_config_manifest.json` and `RUN_G_CHANGELOG.md`.

## F. Remaining limitations and model risk

- Opponent demand, target arrival and removal are not assigned speculative probabilities or values. Option availability is raw/counterfactual and excluded from competitive profiles.
- Refurbished Familiar's opponent-dependent draw is not assumed in the baseline goldfish state.
- The named profiles and practical tolerances are preregistered judgments, not empirical match-win mappings.
- Planner-depth stability is strong targeted evidence, not a mathematical proof over the full state graph.
- A later run must keep raw outcomes, apply paired uncertainty/multiplicity exactly as frozen, and return a frontier when assumptions disagree.

## G. No-optimization attestation

No real candidate performance was screened, scored, ranked, shortlisted, validated or placed on a frontier. No mana base was recommended. Deterministic enumeration and synthetic/protected machinery checks are the only candidate-space operations.

## H. Authorization boundary

Run G's production flag remains `PENDING_INDEPENDENT_RUN_H` and its real-execution entry point fails closed. This report requests independent authorization review; it does not grant authorization.

