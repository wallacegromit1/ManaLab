# Experiment Workflow and Reporting

## Phase 0 — Chat design freeze
Before Work:
1. freeze exact deck and C0;
2. verify material card/rules facts;
3. define legal candidate pool;
4. identify required mechanics;
5. define spell-demand windows/profiles;
6. define policies;
7. define primary metrics;
8. define validation tests;
9. identify unresolved assumptions.

No final mana recommendation yet.

## Phase 1 — Work Build
Build:
- repository;
- configs;
- mechanics;
- simulator;
- policies;
- enumeration;
- metrics;
- tests;
- small validation runs.

STOP before full optimization.

Deliver a validation report and reproducible commands.

## Phase 2 — Chat implementation QA
Review:
- model completeness;
- policy realism;
- lookahead;
- objective overlap;
- test coverage;
- omitted mechanics.

Patch before expensive execution.

## Phase 3 — Work Execute
Perform:
- exact candidate enumeration;
- deterministic metrics;
- protected/safe screening;
- medium simulations;
- finalist selection;
- fresh high-precision validation;
- robustness/sensitivity matrix;
- Pareto/frontier construction.

## Phase 4 — Chat interpretation
Decide whether evidence supports:
- unique optimum;
- robust best candidate;
- unresolved frontier.

Do not equate simulator-score changes with match-win-rate changes.

## Phase 5 — Optional Astra audit
Use when:
- finalists are close;
- methodology is contested;
- one subjective component drives the result;
- a high-confidence unique-optimum claim is proposed.

Audit should target failure modes, not automatically rerun everything.

## Final report
Include:
1. decision label;
2. exact recommended base or frontier;
3. C0 comparison;
4. raw primary metrics;
5. spell/turn-level changes;
6. policy/sensitivity matrix;
7. uncertainty;
8. limitations;
9. reproduction instructions.
