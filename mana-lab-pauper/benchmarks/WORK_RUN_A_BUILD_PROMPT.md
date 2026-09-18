# WORK RUN A — BUILD AND VALIDATE MANA LAB PAUPER v1

Build the reusable **Mana Lab — Pauper v1** simulator/repository and ingest the frozen benchmark **Strixpatch Affinity v1.3**.

This is a **BUILD + VALIDATION RUN ONLY**.

## HARD STOP

You must **STOP before full mana-base optimization**.

Do **not**:
- run Monte Carlo across all 296,706 candidates;
- screen/eliminate candidates for performance;
- select finalists;
- construct a final Pareto frontier;
- recommend any 19-land configuration;
- label any candidate best/optimal;
- emit `UNIQUE OPTIMUM ESTABLISHED`, `ROBUST BEST CANDIDATE, NOT UNIQUE`, or `NO UNIQUE OPTIMUM ESTABLISHED`;
- modify the 41 frozen nonlands;
- treat the prior Sol C1 or prior Astra C0 recommendation as truth.

If any instruction or existing source appears to conflict with this stop, this prompt and the current benchmark authority win.

## INPUTS / AUTHORITY

Use, in order:
1. current Run-A instructions;
2. `Strixpatch_Affinity_v1.3.deck.yaml`;
3. `Strixpatch_Affinity_v1.3.experiment.yaml`;
4. `STRIXPATCH_MODEL_SPEC.md`;
5. `STRIXPATCH_VALIDATION_PLAN.md`;
6. Mana Lab core sources `00`–`12`;
7. `90_STRIXPATCH_AFFINITY_V1.3_INPUT.md` as the original benchmark constraint source;
8. prior Astra audit / Sol workbook as regression evidence only.

Record SHA-256 hashes of all inputs used.

## REQUIRED REPOSITORY

Create a clean auditable repository with reusable abstractions, not Strixpatch-name special cases. A suggested minimum structure:

```text
mana-lab-pauper/
  README.md
  pyproject.toml (or equivalent reproducible environment)
  configs/
    decks/Strixpatch_Affinity_v1.3.deck.yaml
    experiments/Strixpatch_Affinity_v1.3.experiment.yaml
  src/mana_lab/
    cards.py
    mana.py
    state.py
    effects.py
    payment.py
    policies.py
    mulligan.py
    simulator.py
    candidates.py
    metrics.py
    statistics.py
    validation.py
    cli.py
  tests/
    test_input_integrity.py
    test_candidates.py
    test_payment.py
    test_tapped_lands.py
    test_affinity.py
    test_metalcraft.py
    test_boulder.py
    test_scry_no_lookahead.py
    test_cryogen.py
    test_triggers.py
    test_glint_hawk.py
    test_bargain.py
    test_blood_token.py
    test_spellbomb.py
    test_mulligan.py
    test_policies_no_lookahead.py
    test_exact_checks.py
    test_run_a_stop.py
  outputs/run_a/
```

Equivalent organization is acceptable if it is clearer and fully reproducible.

## IMPLEMENTATION REQUIREMENTS

### State and information
Track physical card identities/zones, actual library order, hand, battlefield, graveyard/exile when relevant, turn/play-draw, land-drop availability, tapped state, mana/payment resources, artifacts/Metalcraft, spell state, and legally revealed scry information.

Policies may never inspect unseen future library cards.

### Mana/payment
Implement explicit W/U/B/R/colorless/generic payment with conservation. Filters consume mana. Affinity reduces generic only. Candidate artifact lands enter/tap/count exactly as specified.

### Required benchmark mechanics
Implement and test all mechanics in `mechanics_required`, especially:
- artifact lands + ETB-tapped Bridges;
- Giant's Boulder actual **scry 2** library manipulation;
- Giant's Boulder `{1}` + tap color filtering as **net-zero filtering, not ramp**;
- artifact count / affinity / Metalcraft;
- actual draw state changes;
- Cryogen Relic enter **and leave** draw triggers;
- minimal trigger queue/order needed for Cryogen + additional-cost sacrifices;
- Glint Hawk artifact return, including artifact lands and Cryogen/Boulder;
- Reckoner's Bargain additional-cost sacrifice and resource loss;
- Blood Fountain -> Blood artifact token and its state;
- Nihil Spellbomb optional B draw opportunity;
- opponent-turn untapped-resource availability;
- same-turn multi-spell sequencing;
- London mulligan/bottoming;
- play/draw distinction.

Do not approximate Boulder scry as “virtual sources,” a scalar bonus, or a fixed rescue percentage.
Do not approximate opponent-turn interaction with a fixed credit scalar.
Do not add a generic tapland penalty to a score.

### Policies
Implement the exact named baseline/alternate land, action, scry, reserve, and London policies in the deck/model spec. Use stable deterministic tie breaks and identical policy definitions for all candidate bases.

Log enough information to audit why each policy chose its action.

### Real-world evidence boundary
Preserve the source/evidence notes in the model spec. They may motivate fixtures and policy sensitivity, but **must not become hidden weights**.

In particular:
- the user calls the late-August 4C Boulder lists “Junkdog's” lists;
- web indexing independently shows the linked Reddit brewer as `Visual-Lawyer7861`, so the identity link is unverified;
- do not attempt to resolve that by guessing;
- pre-Zeta 4C results can validate Boulder/Cryogen/Hawk play patterns, not the exact post-Zeta Strix/Dispatch 60;
- observational/self-reported win rates must not calibrate utility.

## CANDIDATE GENERATOR

Implement full legal enumeration because the exact **count check** is cheap, but do **not simulate the full space**.

Required exact targets:
- legal candidates = **296,706**;
- minimum Bridges = **3**;
- three-Bridge candidates = **56**;
- full bridge-count histogram must match `STRIXPATCH_VALIDATION_PLAN.md`.

Implement a second independent counting method (DP/generating-function coefficient) and compare it to enumeration.

## TESTS

Implement every test in `STRIXPATCH_VALIDATION_PLAN.md`.

Zero tolerance for:
- mana creation/loss bugs;
- colored-pip reduction by affinity;
- Bridge producing mana on its entry turn;
- Boulder seeing hidden card 3 during scry policy;
- Cryogen leave triggers omitted on Hawk return or sacrifice;
- incorrect Bargain/Cryogen trigger order;
- candidate-specific policy branches;
- mulligan/bottoming future lookahead;
- opponent mana “banked” across turns/steps.

If the exact-shell T2 Myr Enforcer “impossible” fixture is disproved by a legal sequence, **STOP and report the counterexample**; do not silently rewrite the fixture.

## DETERMINISTIC CHECKS

Reproduce:
- C0 land/source facts;
- exact raw-seven 19-land hypergeometric distribution;
- opening-seven direct W5/U7/B7/R4 presence probabilities;
- joint U+B direct-source presence fixture;
- guaranteed/impossible payment fixtures.

Simulation smoke checks must fall within predeclared sampling tolerance of exact quantities.

## SMOKE SIMULATION ONLY

After unit/deterministic tests pass, run only the configured **small smoke validation** for:
- C0;
- historical C1 regression fixture.

Use 20,000 trials per configured scenario/candidate unless resource constraints demand fewer; if fewer, state why.

Purpose: verify mechanics, event logging, paired randomization, and policy execution.

**Do not compare the smoke outputs to pick a winner.** Put `NOT A RANKING / NOT AN OPTIMIZATION` at the top of the smoke report.

## REQUIRED OUTPUTS

Write under `outputs/run_a/`:
1. `repository_tree.txt`
2. `environment.txt`
3. `config_hashes.txt`
4. `candidate_count_check.json`
5. `deterministic_checks.json`
6. `unit_test_report.txt`
7. `no_lookahead_test_report.txt`
8. `coverage_matrix.md`
9. `smoke_validation_report.md`
10. `reproduction_commands.md`
11. `run_a_stop_certificate.md`
12. any machine-readable event/summary files needed to audit the smoke run.

Also provide a concise `RUN_A_VALIDATION_REPORT.md` containing:
- what was implemented;
- exact tests passed/failed;
- coverage status for every required mechanic;
- any model/spec ambiguities discovered;
- any deviations from config and why;
- smoke exact-vs-simulation agreement;
- a prominent statement that no final optimization was run.

## FAILURE / ESCALATION RULE

If a required mechanic cannot be implemented faithfully, a deterministic target disagrees, or policy/no-lookahead behavior is ambiguous:
1. do not improvise;
2. preserve the failing fixture/log;
3. mark Run A **FAIL or CONDITIONAL**;
4. stop before optimization;
5. return the smallest precise question/issue for Phase 2 Chat QA.

## FINAL STOP CONDITION

Once the repository builds, required tests run, smoke validation completes, and the Run-A report is written, **STOP**.

The next step is **Phase 2 Chat implementation QA**. Full candidate optimization requires a new explicit authorization after that review.
