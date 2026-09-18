# Mana Lab — Pauper v1 Run F Phase 3 Authorization Report

## 1. Executive verdict

Run E is a credible remediation/validation package, but it is **not an executable, frozen, statistically reviewable Phase 3 experiment**. The independent checks reproduced the package hash, deck identity, C0, the 296,706-candidate space, both fresh-extraction test runs, the protected Run E gate, no-lookahead regressions, candidate-label neutrality, and candidate-order-normalized protected smoke.

Authorization nevertheless fails. The supplied experiment remains explicitly `RUN_C_REMEDIATION_VALIDATE_ONLY`; screening and validation trial counts are zero; no production screening/finalist/validation pipeline exists; the named objective profiles have no exact components, transforms, or weights; the Pareto helper is directionally wrong for lower-is-better metrics and ignores uncertainty; the promised tap-out policy is not executable; planner-depth evidence is too narrow; decision-relevant omitted mechanics have no frozen containment plan; and the source-hash manifest does not reconcile with the ZIP.

No production candidate screen, real-candidate ranking, finalist selection, frontier construction, or mana-base recommendation was performed.

## 2. Audit boundary and evidence

- Primary package: `/home/monkeyd/Documents/Mana_Lab_Pauper_v1_Run_E.zip`.
- Expected and observed ZIP SHA-256: `82d1dcd663de5a8bcb2d9917271fba264c509bdff8b45d1920b9f97ccf0d0c71`.
- Three fresh extractions were used: two for execution/reproducibility and one untouched extraction for package-manifest reconciliation.
- Internet access remained off. The frozen card/rules packet was complete enough for this gate; no external fact was needed to decide authorization.
- Audit helper: `run_f_audit/audit_helpers.py`.
- Production source was not modified. All Run F material is outside the extracted production package.

## 3. Package and provenance audit

| Check | Evidence | Result |
|---|---|---|
| ZIP identity | Expected and observed SHA-256 match exactly | PASS |
| Clean extraction | Three clean extractions completed; two pristine trees initially compared equal | PASS |
| Required repository files | Source, tests, configs, benchmark specifications, reports, and outputs are present | PASS |
| Runtime declaration | `pyproject.toml` requires Python >=3.11 and PyYAML >=6.0; audit ran on Python 3.14.7 / PyYAML 6.0.3 | PASS |
| Commands from fresh extraction | Unit tests, candidate count, deterministic checks, and `run-e` work | PASS |
| Git provenance | ZIP has no `.git`; fresh `run-e` rewrites the report with patched commit `UNAVAILABLE` | PARTIAL |
| Source/config manifest | All 63 packaged source/test/config files have manifest entries, but the manifest also contains 103 absent `__pycache__/*.pyc` entries | FAIL |
| Cache safety | `.gitignore` excludes caches, but `_source_hashes()` recursively included caches present during packaging | FAIL |

The ZIP hash still gives an unambiguous identity for this exact package. The internal provenance story is nevertheless not self-reconciling: the reported Git commit cannot be independently resolved from the package, and the shipped source/config hash manifest has 103 nonexistent entries. This is F-08.

## 4. Frozen input audit

Independent loading of the deck configuration confirmed:

- 60-card maindeck;
- 41 frozen nonlands;
- exactly 19 lands;
- four Giant's Boulders;
- C0 exactly: 3 Ancient Den, 4 Seat of the Synod, 4 Vault of Whispers, 4 Great Furnace, 1 Razortide Bridge, 1 Goldmire Bridge, 2 Mistvault Bridge;
- ten permitted artifact-land identities;
- mandatory minimum one and maximum four for each of the four untapped mono-color artifact lands;
- zero-to-four bounds for each of six Bridges;
- no nonland decision variable.

The frozen data includes the material rules facts used by the simulator. The audit did not treat external URLs embedded in the deck packet as instructions and did not browse.

## 5. Candidate-space audit

The production Cartesian-product enumerator and DP both report 296,706. Run F reproduced the count by two conceptually independent methods:

1. inclusion–exclusion on four shifted variables in `[0,3]`, six variables in `[0,4]`, and total shifted sum 15;
2. an independently written bounded recursive enumerator with explicit remaining-sum bounds.

Results:

| Invariant | Result |
|---|---:|
| Inclusion–exclusion count | 296,706 |
| Independent recursive count | 296,706 |
| Unique canonical candidates | 296,706 |
| Same canonical set as production generator | Yes |
| C0 occurrences | 1 |
| Minimum Bridges | 3 |
| Three-Bridge candidates | 56 |
| Canonical candidate-set SHA-256 | `d9bff0652d2d449f761205575b63af0db5205c3354705c82302fa8b649de78e3` |

Every emitted candidate has 19 lands and respects identity/copy bounds. Canonical keys prevent duplicates. Candidate labels are not passed into production policy decisions. Candidate enumeration order does not enter the trial seed derivation. Candidate generation is authorized as a deterministic component; candidate performance evaluation is not.

## 6. Run E regression audit

Both fresh extractions ran **179 tests, 0 failures, 0 skips**. The protected `run-e` command completed successfully and reran 42 focused D-01–D-11 tests.

| ID | Failure mode protected | Test mechanism | Actually sensitive? | Result | Authorization relevance |
|---|---|---|---|---|---|
| D-01 | Production omitted future-color land value | Exact Run D bridge/Strix reproducer plus color and permutation variants | Yes; old tie behavior selects the wrong Bridge | PASS (6 tests) | Protects land-policy neutrality |
| D-02 | Alternate tempo sign reversed | Untapped mono land must beat tapped Bridge, including future-color conflict | Yes; negative untapped scoring fails directly | PASS (3) | Protects alternate tempo policy |
| D-03 | Information action terminated known continuation | Enumerates Strix/Thoughtcast/Cryogen/Bargain/Boulder followed by known actions; hidden-library root invariance | Yes; old terminal chance node removes asserted sequences | PASS (5) | Protects causal planning/no-lookahead |
| D-04 | Held land masked battlefield loss; velocity induced land sacrifice | T3 pass, nonland sacrifice, held-land loss accounting, explicit T4 deadline | Yes; old loss calculation changes asserted root/land-loss value | PASS (4) | Protects resource accounting |
| D-05 | Bargain cleared composed triggers | Exact Nihil and Cryogen trigger order, payable/declined paths, production action path | Yes; clearing the stack loses asserted triggers/draw order | PASS (5) | Protects causal effects |
| D-06 | Failed Hawk cast counted functional | Separates raw cast from functional resolution and verifies legal return/replay | Yes; old execution credit fails the counterexample | PASS (3) | Protects spell-success metrics |
| D-07 | Policy precedence ambiguous | Synthetic pairwise conflicts exercise deadline, reserve, land, artifact, and canonical tie ordering | Yes for code tuple; does not cure deck-YAML drift | PASS (5) | Partial policy freeze evidence |
| D-08 | Repeated windows lacked denominator identity | Unique opportunity IDs/roles and reconstructible primary denominator | Yes; old shared window identity fails uniqueness/reconstruction | PASS (3) | Protects event aggregation |
| D-09 | Boulder “used” conflated with “necessary” | Native-payment and strict-dependency counterfactuals | Yes; old shared flag fails native-payment fixture | PASS (3) | Protects fixing diagnostics |
| D-10 | Positional paired estimator accepted mismatches | Rejects reordered, missing, duplicate, scenario, and replicate mismatches; checks closed form | Yes; old positional behavior accepts shuffled values | PASS (3) | Protects paired differences |
| D-11 | Fixture-only options advertised as production | Normal Nihil trace plus status assertions for three fixture-only metrics | Yes for the stated contract | PASS (2) | Reveals remaining omitted-mechanic risk |

The D-series regressions are meaningful. They establish that the Run D defects are repaired in the tested paths. They do not establish that an absent Phase 3 search pipeline, objectives, or decision logic is safe.

## 7. Information-boundary audit

The 18 designated no-lookahead tests pass. Metamorphic fixtures hold visible state constant while changing hidden library information for mulligan, bottoming, land selection, payment, Hawk return, Bargain sacrifice, Boulder pre-scry, and pre-draw root decisions. Post-reveal divergence is allowed.

Run E's depth 7/8/9 and baseline/conservative comparisons reproduce 16 states and zero root divergences. However, 12 of the 16 are three ordinary C0 trials at turns 1–4, and their reported roots are overwhelmingly land plays; only four are targeted states. The corpus does not directly cover all Run F-required combinations: Boulder plus multiple spells, affinity changing mid-sequence, Hawk return/replay under competing lines, interaction hold versus development, and representative double-spell states. Zero divergence on this corpus is insufficient to freeze depth 8 for a 296,706-candidate ranking experiment. This is F-07.

## 8. Payment, action graph, and planner audit

Positive findings:

- colored and generic costs are explicit;
- Boulder filtering is net-zero and consumes a land plus a Boulder tap;
- multiple filters and generic-payment color preservation are enumerated;
- payment outcomes are deduplicated by strategically distinct post-payment state;
- affinity, artifact count, Metalcraft, tap state, sacrifice, return, and replay transitions have targeted tests;
- hand, battlefield, land-order, payment, and duplicate-card permutation tests pass;
- there is no first-valid-payment selection in the planner path;
- planner branching has no candidate-ID-dependent budget.

The production defaults are search depth 8 and at most 12 replans/actions per main phase. These values are hard-coded defaults rather than frozen Phase 3 config fields. There is no documented Phase 3 computational fallback or proof that branch pruning/deduplication preserves every ranking-relevant line throughout the candidate space. The current tests are strong local evidence but do not close F-07.

## 9. Policy and mulligan audit

Both London mulligan policies are executable, deterministic, use fresh sevens, bottom exactly the mulligan count, stop at four cards, and do not inspect the hidden future library. Candidate labels are absent from their signatures and logic.

Policy freeze fails for two reasons:

1. The higher-authority deck YAML says baseline actions maximize due/overdue spell execution, then artifact count, draw/selection, and remaining resources, with land loss minimized later. The Run E code instead orders hard deadlines, reserve, land/untapped/color preservation, due execution, artifact preservation, future coverage, current resources, spells, and information. The code may be defensible, but the authoritative config was not updated to match it.
2. The deck YAML defines an alternate `tap_out_development` reserve policy and says own-turn spell execution/current mana precede interaction preservation. The only alternate action tuple still puts `reserve_preserved` second, immediately after hard deadlines. A protected synthetic tie selects `reserve`, not `tap-out`.

These are not prose-only differences: land/color composition can determine which lines preserve interaction, so the mismatch can change candidate rankings. This is F-05.

## 10. Raw event and metric contract audit

Run E has a useful 29-entry metric registry with event source, numerator, denominator, timing, grain, opportunity identity, missing-data rule, snapshot role, direction, and correlation family. Production traces preserve detailed raw events, and a protected repeated trial produced 362 identical raw events under candidate-label renaming.

The contract is not yet an executable Phase 3 measurement pipeline:

- `SmokeAggregator` aggregates only a small flat smoke row, not the 29-metric registry;
- there is no production aggregator enforcing opportunity uniqueness/missing-data rules across a full run;
- critical-sequence predicates are listed in YAML but have no evaluator/output table;
- double-spell and spell-plus-interaction raw evidence can be derived, but no validated production join/aggregation exists;
- output schemas for candidate metric tables, paired differences, profile views, and robustness results are absent.

Raw events are a sound foundation. They do not by themselves prove that Phase 3 will calculate the stated metrics correctly. This is part of F-01/F-03.

## 11. Objective and named-profile audit

The code contains an objective-component registry and correlation-family warnings. It can mechanically return a leave-one-component-out dictionary or one arbitrary first component per correlation family. No opaque master score is present.

All required named profiles fail the pre-registration requirement. The deck YAML lists `balanced`, `tempo_sensitive`, `color_consistency`, `interaction_sensitive`, `double_spell_sensitive`, and `affinity_value_engine`, but nowhere defines exact components, turns/windows, transforms, weights, normalization, direction, missing-data handling, or profile-specific practical-significance rules. The “de-correlated” helper simply retains the first component encountered in each family; that is not a substantively justified sensitivity design.

Without exact profile definitions, candidate results could influence objective construction after the fact, recreating winner-selection bias. This is F-02.

## 12. Opponent-turn interaction audit

The simulator does not invent an opponent-action probability. It records whether Dispatch, Galvanic Blast, and Reckoner's Bargain are in hand/payable, whether resources were payable before own-turn spending, whether they remain payable, and whether own-turn spending caused the loss. Full-effect Metalcraft is separately recoverable.

This raw counterfactual approach is appropriate. Authorization still fails because the interaction-sensitive profile is undefined and the promised reserve-versus-tap-out sensitivity is not executable. Thus an arbitrary implicit reserve policy could define the later winner even without an explicit opponent-demand scalar.

## 13. Screening-design audit

There is no proposed production screening algorithm to audit. The shipped configuration says:

- screening disabled;
- zero screening trials;
- zero medium trials;
- finalist target zero;
- zero validation trials;
- C0 and all 56 three-Bridge candidates protected only in prose for later design.

No shortlist rule, uncertainty boundary, false-elimination control, adaptive promotion rule, protected-class implementation, screening output schema, or selection-bias accounting is executable. The repository intentionally exposes no optimization command. This design state was correct for Run E remediation, but it cannot authorize Phase 3. This is F-01.

## 14. RNG and common-random-number audit

Current protected machinery passes:

- trial randomness is derived from base seed plus SHA-256 of scenario/trial/mulligan attempt;
- candidate label is excluded;
- candidate iteration order does not affect normalized raw traces;
- identical physical candidates under different labels produce identical summary rows and 362-event traces;
- pairing keys include scenario, replicate, trial, and play/draw;
- keyed paired differences reject reordered/missing/duplicate/mismatched observations.

The configured selection seed, validation seed, and four replicate seeds are numerically distinct. However, because there is no selection/finalist pipeline, Run F cannot verify that the declared partitions are used at the correct stages, that no validation data informs shortlist/profile tuning, or that all finalist analyses use keyed paired observations. Current RNG primitives pass; Phase 3 RNG orchestration is unimplemented.

## 15. Selection/validation separation and winner's curse

The repository acknowledges fresh validation and winner's-curse risk in prose. No code implements shortlist creation, fresh finalist execution, adaptive precision, or post-selection confirmatory analysis. With 296,706 candidates, declarations alone are insufficient. Selection leaders must be treated as selected hypotheses and evaluated on fresh randomness with paired differences. Until that pipeline exists and is dry-run, F-01 remains blocking.

## 16. Trial-count and precision plan

No Phase 3 trial counts or stopping rules are frozen. The only nonzero counts belong to prior validation smokes. The production fields for screening, medium, and validation are all zero. There is no predeclared near-boundary survival rule or adaptive finalist precision rule. Generic Bernoulli precision calculations cannot repair the absence of a planned endpoint, candidate retention threshold, or resource budget.

## 17. Pareto, regret, and frontier audit

The shipped `pareto_dominates` helper assumes every dimension is higher-is-better and compares point estimates only. It has no direction metadata, missing-value handling, materiality tolerance, or uncertainty. Run F's synthetic counterexample uses `unused_mana`, which the registry marks lower/contextual: left=5 and right=1. The helper incorrectly says left dominates right.

The regret helper is a simple higher-is-better subtraction with no paired uncertainty or assumption-reversal reporting. No frontier pipeline exists, and output config explicitly has `pareto_frontier: false` and `robustness_matrix: false`.

Therefore the system cannot yet produce a defensible smallest frontier or safely support the three eventual decision labels. This is F-04.

## 18. Model-risk regression audit

| Rejected-v1 failure pattern | Classification | Evidence / remaining risk |
|---|---|---|
| Dominant arbitrary tapland penalties | Partially protected | Actual ETB/resource events replace a generic scalar, but undefined profiles could reintroduce arbitrary weighting |
| Overlapping composite penalties | Partially protected | Correlation families/warnings exist; exact profiles and validated leave-one-out/de-correlated runs do not |
| Unreproducible sequencing | Protected | Executable deterministic planner, raw traces, permutation/no-lookahead tests |
| One-policy-only winner claims | Partially protected | Two mulligan/sequencing names exist; alternate tap-out is not implemented and depth coverage is insufficient |
| Unrealistic free fixing | Protected | Boulder filter is net-zero, taps resources, and has native-payment counterfactuals |
| Arbitrary opponent-turn valuation | Partially protected | Raw availability avoids opponent probabilities; interaction profile and reserve sensitivity remain unfrozen |
| Exhaustive enumeration treated as exhaustive evidence | Protected | Docs and hard stop explicitly prohibit that inference |
| Validation on selection randomness | Partially protected | Distinct seed labels exist; no stage orchestration exists to enforce their use |
| Forced unique winner | Partially protected | Decision language allows a frontier; Pareto/frontier implementation is absent/unsafe |
| Simulator score treated as match-win-rate points | Protected | Core documentation explicitly forbids the translation |

Every “Partially protected” ranking-relevant item must be closed before re-audit.

## 19. Unsupported and partially supported mechanics

| Mechanic / decision | Supported? | Approximation | Could affect candidate ranking? | Planned sensitivity / containment |
|---|---|---|---|---|
| Blood token activation | Primitive/test only; absent from production planner | Validation-only event | Yes: generic mana, discard timing, draw sequencing | None frozen |
| Makeshift Munitions activation | Primitive/test only; absent from production planner | Target fixture only | Yes: unused mana and sacrifice timing | None frozen |
| Cryogen stun activation | Primitive/test only; absent from production planner | Tapped-target fixture only | Yes: `{1}{U}` access and sacrifice timing | None frozen |
| Blood Fountain late recursion | Not implemented in planner/metrics | Omitted | Plausibly by turn 4 with `{3}{B}` and graveyard state | None frozen |
| Nihil standalone exile/optional draw line | Partial | Optional B draw modeled when it enters graveyard through supported paths; target demand absent | Plausibly | No production target-demand sensitivity |
| Dispatch/Blast actual target/effect use | Resource availability only | No target arrival distribution; Metalcraft reported | Yes for interaction-sensitive conclusions | Raw availability is defensible, but profile/sensitivity is unfrozen |
| Opponent removal and Bridge indestructibility | Not modeled | Goldfish state | Yes: resilience could favor Bridges | None frozen |
| Refurbished Familiar opponent-dependent draw | Deliberately disabled | Goldfish no-draw | Plausibly changes continuation value | Declared, but no sensitivity plan |
| Late Boulder destroy ability | Not modeled | Outside normal turn-4 affordability | Unlikely in frozen horizon | Reasonable exclusion if explicitly retained |
| Sideboarding | Out of scope | Maindeck only | Not for this run | Frozen `sideboard_scope: false` |

The first eight rows require either production support or a predeclared containment/sensitivity argument demonstrating why omission cannot plausibly reorder candidates. Their current treatment is F-06.

## 20. Production-config freeze review

See `RUN_F_PHASE3_FROZEN_CONFIG.md` for the full table. In summary, the deck/candidate inputs, current policies, raw metric registry, and seed labels are recoverable. Required Phase 3 values are not frozen: exact objective profiles, production scenarios/weights, screening and medium counts, shortlist and boundary rules, finalist rule, adaptive validation, practical significance, Pareto dimensions/tolerances, unsupported-mechanic variants, and output schemas.

## 21. Reproducibility audit

Positive evidence:

- two fresh extractions each passed 179 tests;
- a fresh `run-e` completed with exit 0;
- independent candidate counts match;
- protected same-seed/same-config label-renamed trials match exactly;
- protected candidate-order-normalized Run E raw traces match;
- source/config files themselves match their recorded hashes.

Negative evidence:

- no Git repository is packaged, so the claimed commit cannot be resolved locally;
- fresh `run-e` reports the commit as `UNAVAILABLE`, changing the provenance report from the shipped version;
- `source_config_hashes.json` includes 103 cache files absent from the archive;
- there is no one-command Phase 3 run or dry-run command;
- there are no Phase 3 candidate/metric/profile/paired-difference/frontier output schemas to hash or reproduce.

Current validation is reproducible; the proposed Phase 3 experiment is not yet defined enough to reproduce.

## 22. Structural Phase 3 dry run

A complete dry run could not be performed because no Phase 3 pipeline exists. Run F instead exercised the available protected machinery:

- candidate ingestion/counting;
- deterministic paired trial generation;
- raw event production;
- label and iteration neutrality;
- strict paired-difference fixtures;
- objective-component registry access;
- synthetic Pareto and alternate-reserve counterexamples.

The absent steps are authorization-critical: full metric aggregation, exact profile application, safe shortlist retention, automatic switch to fresh validation randomness, paired finalist differences, robustness matrix, uncertainty-aware Pareto/frontier construction, and reproducible final reporting.

## 23. Defects by severity

| ID | Severity | Summary | Blocking? |
|---|---|---|---|
| F-01 | BLOCKER | No executable/frozen Phase 3 screening, promotion, finalist, validation, multiplicity, or reporting pipeline | Yes |
| F-02 | BLOCKER | Required named profiles are names only; exact components/transforms/weights and sensitivity variants are absent | Yes |
| F-03 | BLOCKER | Registry events are not converted by a validated production metric/critical-sequence aggregation pipeline | Yes |
| F-04 | BLOCKER | Pareto helper reverses lower-is-better dimensions and ignores uncertainty/materiality/missing data | Yes |
| F-05 | BLOCKER | Authoritative policy contract and executable policy diverge; advertised tap-out alternate still prioritizes reserve | Yes |
| F-06 | BLOCKER | Decision-relevant omitted mechanics/model uncertainties lack frozen containment or sensitivity tests | Yes |
| F-07 | MAJOR | Depth/information sensitivity corpus lacks required structural coverage; zero divergence is not sufficient evidence | Yes |
| F-08 | MAJOR | Hash manifest contains 103 absent cache entries; Git provenance is unavailable and fresh run rewrites it | Yes |

Minimal reproductions and required remediation are in `RUN_F_DEFECTS.md`. Acceptance-level results are in `RUN_F_ACCEPTANCE_MATRIX.csv`.

## 24. Re-audit requirements

Before another authorization audit:

1. ship a separate Phase 3 experiment config with all zero/disabled fields replaced by frozen values;
2. implement a dry-runnable Phase 3 pipeline without running the real candidate screen;
3. freeze exact named profile definitions and justified de-correlated/leave-one-out variants;
4. implement direction-, materiality-, missingness-, and uncertainty-aware Pareto/frontier logic;
5. reconcile policy YAML/spec/code, including a genuine tap-out variant;
6. add production metric aggregation and exact critical-sequence evaluators with schema tests;
7. expand planner-depth/information-policy fixtures across the missing structural states;
8. define support or containment for omitted activations/opponent-dependent mechanics;
9. regenerate a source-only manifest, exclude caches deterministically, and include verifiable version provenance;
10. rerun the entire Run F gate from a fresh archive.

## 25. Exact authorization decision

`PHASE 3 OPTIMIZATION AUTHORIZATION — FAIL`

Run E must not be used to screen, rank, eliminate, shortlist, or select real mana-base candidates until the blocking defects are remediated and independently re-audited.
