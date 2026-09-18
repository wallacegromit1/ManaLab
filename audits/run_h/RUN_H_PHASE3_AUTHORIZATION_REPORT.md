# RUN H AUTHORIZATION — PHASE 3 NOT AUTHORIZED

Run H independently audited the exact Run G package on 2026-09-18. Seven Run F blockers remain open; F-08 package provenance is closed. Run G's readiness PASS is reproducible but is not evidence of production readiness. No conditional authorization is granted. Production was not patched.

## Integrity and reproduction

- Run G expected and observed SHA-256: `ca7f2ed96cfc0a19041304af4d29bdbb4bf9c9b3908d10f35ffadb0599813e9d`.
- Run E expected and observed SHA-256: `82d1dcd663de5a8bcb2d9917271fba264c509bdff8b45d1920b9f97ccf0d0c71`.
- ZIP integrity: no corrupt member. Required Run G reports/configuration present.
- Untouched parent: **179 tests pass**. Fresh G extraction A: **205 tests pass**. Fresh G extraction B: **205 tests pass**. Both gates return machine-readable PASS.
- D-01–D-11 regression modules remain passing in both full logs. These tests establish their tested properties, not all Phase 3 properties.
- Independent inclusion/exclusion and enumeration: **296,706**, unique identities; C0 once; **56** three-Bridge candidates. Enumeration was identity/count-only.
- External adversarial suite: **89 checks, 59 pass, 30 fail**. These are individual contract probes, not 30 independent blockers. Additional observations are in supplemental_checks.json.

## F-01–F-08 disposition

| Blocker | Status | Independent result |
| --- | --- | --- |
| F-01 | FAIL | Stage methods exist; stages 3–9 contain fixed fixtures, strings and assertions, not production evidence flow. run_real unconditionally raises. Forged prerequisite accepted. |
| F-02 | FAIL | Six scalar-vector arithmetic tests pass; profile aggregation metadata changes have no effect. No upstream profile-specific aggregator. Comparator ignores uncertainty. |
| F-03 | FAIL | 29 registry routing labels, not 29 implementations. Incomplete/mixed traces accepted; by-turn and Cryogen/Hawk predicates fail. |
| F-04 | FAIL | Low-level direction, missing-CI retention and explicit protections pass; no production paired-CI/multiplicity/frontier caller. Wide CI is labeled equivalent. |
| F-05 | FAIL | Tap-out genuinely differs; sequencing, mulligan and scry alternatives also differ. Registry accepts wrong policy kind; simulate_trial couples scry to sequencing. |
| F-06 | FAIL | 28 registry rows reviewed. Tested primitives do not make all production actions available; NOT MATERIAL declarations do not contain indirect effects. |
| F-07 | FAIL | All six stable at 7/8/9/10, but maximum explored sequence lengths are only 2,2,3,2,4,2. Independent variants also checked. |
| F-08 | PASS | 78 files match independently; content-tree hash matches; no immutable mutation; cross-extraction ordinary dry-run hashes equal. |

## Production-path assessment

There is no complete execution path behind the authorization refusal. Stage 2 counts identities without persisting the candidate evidence required by later stages. Stages 3–9 exercise hardcoded examples or emit configuration prose. They do not simulate, aggregate all required metrics, select finalists, validate independently, run sensitivity scenarios, construct a real frontier or write the promised result tables. No real production path was run. Enabling execution requires new implementation, not simply authorization.

## Scientific assessment

Direction-aware low-level dominance and explicit low-N/uncertainty retention are improvements. They are not wired to aligned production paired differences, multiplicity control, sequentially valid adaptive intervals or an auditable frontier. Profile-specific weighted populations remain prose. This prevents scientific authorization even if orchestration were added.

## Mechanics and planner risk

Tested effect primitives and raw-only labels do not contain indirect mana and draw effects. Blood activation and Familiar's conditional draw can affect later resources without being explicit objective components. Depth stability is real for the supplied small states but does not exercise the declared depth boundary. No actual ranking impact is claimed or measured.

## Provenance

The 78-file cache-free manifest reconciles with content-tree SHA-256 `0fbc3204571a8df35e4ed27887a79c2ae5bdfc73371f4354cde53e17617ecffc`. Both extractions preserve immutable files and produce identical ordinary-content hashes for every dry-run JSON artifact. This repairs F-08. It does not repair missing verification of upstream artifact hashes at pipeline stages.

## Required next action

Separate **Run I remediation**, covering H-01–H-07 and their acceptance tests in RUN_H_DEFECTS.md. Re-audit after implementation. Do not launch Phase 3 or choose a mana base on this evidence.

## Limits and attestation

No screening, ranking, real shortlist/frontier, confirmatory candidate comparison or recommendation occurred. Two identical C0 traces under different labels were used solely for machinery invariance; performance summaries were not retained. The shipped suites were reproduced as requested and contain historical regression fixtures, not newly commissioned optimization. No web or external card-data updates were used. Missing production paths are explicitly untestable, not silently counted as passing. GitHub publication awaits a user-selected repository and scope.
