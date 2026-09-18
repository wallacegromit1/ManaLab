# Mana Lab — Pauper v1 Source Index

Mana Lab v1 is a reusable **Pauper mana-base simulation and optimization project**.

The core sources define how to model, validate, optimize and report. Deck-specific benchmark files are deliberately separated so no archetype-specific assumption becomes a global rule.

## Authority order
1. Current user instruction
2. Current deck/problem input
3. Current experiment configuration
4. Project Instructions
5. Core project sources
6. Prior audits/results

## Core sources
- `01_PAUPER_SCOPE_AND_DECISION_STANDARD.md`
- `02_DECK_INPUT_CONTRACT.md`
- `03_CARD_AND_MANA_MODEL.md`
- `04_GAME_STATE_AND_POLICY_MODEL.md`
- `05_METRICS_AND_OPTIMIZATION.md`
- `06_VALIDATION_AND_STATISTICS.md`
- `07_EXPERIMENT_WORKFLOW_AND_REPORTING.md`
- `08_DECK_SPEC_TEMPLATE.yaml`
- `09_EXPERIMENT_CONFIG_TEMPLATE.yaml`
- `10_ACCEPTANCE_TESTS.md`
- `11_MODEL_RISK_LESSONS.md`
- `12_PAUPER_MECHANICS_COVERAGE.md`

## Benchmark sources
`benchmarks/` contains the first regression case:
- frozen Strixpatch Affinity v1.3 problem definition;
- the rejected prior audit;
- the prior Sol workbook.

These are used to validate Mana Lab, not to dictate future conclusions.

## Design principle
Mana Lab may end in:
- `UNIQUE OPTIMUM ESTABLISHED`
- `ROBUST BEST CANDIDATE, NOT UNIQUE`
- `NO UNIQUE OPTIMUM ESTABLISHED`

Returning an unresolved frontier is a successful result when the evidence warrants it.
