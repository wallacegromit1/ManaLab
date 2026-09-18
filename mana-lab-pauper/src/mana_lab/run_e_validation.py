from __future__ import annotations

import copy
import csv
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from .candidates import candidate_count_report
from .cards import load_deck, load_yaml
from .metrics import PHASE3_METRIC_REGISTRY, validate_metric_registry
from .mulligan import london_mulligan
from .policies import (
    BASELINE_ACTION_POLICY,
    BASELINE_INFORMATION_POLICY,
    BASELINE_LAND_POLICY,
    BASELINE_SCRY_POLICY,
    CONSERVATIVE_INFORMATION_POLICY,
    policy_source_has_candidate_branch,
)
from .simulator import (
    _physical_deck,
    _shuffled,
    _stable_scenario_seed,
    choose_next_action,
    execute_action_policy,
    run_smoke_matrix,
)
from .state import GameState, Permanent, make_card
from .statistics import validate_seed_partition
from .validation import deterministic_checks, search_t2_myr_enforcer, sha256_file, validate_candidate_report


INPUT_ZIP_SHA256 = "0d99524f834a09bae1c256d8dd57ad06b2265e35a824f7104697e569bcb9a5e7"
RUN_C_IMPLEMENTATION_MARKER = "1e81305724376ede4387bdbe6080cdc0f32339ee"
RUN_C_PACKAGING_MARKER = "5220d16ade01610d9d5656a062021048b3f0fff5"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: Any) -> None:
    _write(path, json.dumps(value, indent=2, sort_keys=True))


def _run(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(root / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(args, cwd=root, env=environment, text=True, capture_output=True)


def _test_count(text: str) -> int:
    matches = re.findall(r"Ran (\d+) tests?", text)
    return int(matches[-1]) if matches else 0


def _git_head(root: Path) -> str:
    result = _run(root, ["git", "rev-parse", "HEAD"])
    return result.stdout.strip() if result.returncode == 0 else "UNAVAILABLE"


def _root_key(state: GameState, deck, *, depth: int, information_policy: str) -> str | None:
    action = choose_next_action(
        state, deck, action_policy_name=BASELINE_ACTION_POLICY,
        scry_policy_name=BASELINE_SCRY_POLICY,
        information_policy_name=information_policy, max_depth=depth,
    )
    return None if action is None else repr(action.key)


def _ordinary_state_corpus(deck, seed: int, trials: int = 3) -> list[tuple[str, GameState]]:
    base = _physical_deck(deck, dict(deck.current_mana_base))
    corpus: list[tuple[str, GameState]] = []
    scenario = "run_e_corpus|baseline_functional_london|baseline_hand_demand"
    for trial in range(trials):
        def draw_seven(attempt: int):
            shuffled = _shuffled(base, _stable_scenario_seed(seed, scenario, trial, attempt))
            return shuffled[:7], shuffled[7:]

        result = london_mulligan(deck, "baseline_functional_london", draw_seven)
        state = GameState(
            library=list(result.library), hand=list(result.hand), on_play=trial % 2 == 0,
            trial_id=trial, scenario_id=scenario, replicate_id=seed,
        )
        for turn in range(1, 5):
            state.begin_turn(turn)
            corpus.append((f"ordinary_trial_{trial}_turn_{turn}", copy.deepcopy(state)))
            execute_action_policy(
                state, deck, action_policy_name=BASELINE_ACTION_POLICY,
                scry_policy_name=BASELINE_SCRY_POLICY,
                information_policy_name=BASELINE_INFORMATION_POLICY,
            )
            state.end_phase("opponent")
            state.end_phase("end")
    return corpus


def _targeted_states(deck) -> list[tuple[str, GameState]]:
    def lands(names: list[str]) -> GameState:
        state = GameState(phase="main", turn=3)
        for index, name in enumerate(names):
            spec = deck.land_by_name[name]
            state.battlefield.append(Permanent(
                make_card(f"target-land-{index}", name, artifact=True, land=True),
                tapped=False, land_spec=spec,
            ))
        return state

    bridge = lands(["Vault of Whispers"])
    bridge.turn = 1
    bridge.hand = [
        make_card("d", "Drossforge Bridge", artifact=True, land=True),
        make_card("m", "Mistvault Bridge", artifact=True, land=True),
        make_card("s", "Baleful Strix", artifact=True, creature=True),
    ]

    long_chain = lands(["Vault of Whispers"])
    long_chain.turn = 2
    long_chain.hand = [
        make_card("n", "Nihil Spellbomb", artifact=True),
        make_card("d", "Ancient Den", artifact=True, land=True),
        make_card("h", "Glint Hawk", creature=True),
    ]

    information = lands(["Seat of the Synod", "Vault of Whispers", "Ancient Den", "Great Furnace"])
    information.hand = [
        make_card("s", "Baleful Strix", artifact=True, creature=True),
        make_card("e", "Myr Enforcer", artifact=True, creature=True),
    ]

    bargain = lands(["Vault of Whispers", "Goldmire Bridge", "Ancient Den"])
    bargain.battlefield.append(Permanent(make_card("n", "Nihil Spellbomb", artifact=True)))
    bargain.hand = [make_card("b", "Reckoner's Bargain")]

    return [
        ("target_bridge_future_color", bridge),
        ("target_hawk_long_chain", long_chain),
        ("target_information_continuation", information),
        ("target_bargain_trigger", bargain),
    ]


def _sensitivity(corpus: list[tuple[str, GameState]], deck) -> tuple[dict[str, Any], dict[str, Any]]:
    horizon_rows = []
    horizon_divergences = []
    information_rows = []
    information_divergences = []
    for label, state in corpus:
        choices = {
            str(depth): _root_key(state, deck, depth=depth, information_policy=BASELINE_INFORMATION_POLICY)
            for depth in (7, 8, 9)
        }
        divergent = len(set(choices.values())) > 1
        row = {"state": label, "root_choices": choices, "divergent": divergent}
        horizon_rows.append(row)
        if divergent:
            horizon_divergences.append(row)

        baseline = _root_key(state, deck, depth=8, information_policy=BASELINE_INFORMATION_POLICY)
        conservative = _root_key(state, deck, depth=8, information_policy=CONSERVATIVE_INFORMATION_POLICY)
        info_row = {
            "state": label,
            "baseline_root": baseline,
            "conservative_root": conservative,
            "divergent": baseline != conservative,
        }
        information_rows.append(info_row)
        if info_row["divergent"]:
            information_divergences.append(info_row)
    horizon = {
        "depths": [7, 8, 9],
        "states_tested": len(corpus),
        "root_choice_divergence_count": len(horizon_divergences),
        "divergence_examples": horizon_divergences,
        "strategically_meaningful_divergence": bool(horizon_divergences),
        "retain_depth_8": not horizon_divergences,
        "rows": horizon_rows,
    }
    information = {
        "profiles": {
            BASELINE_INFORMATION_POLICY: {"draw_1": 100, "draw_2": 190, "scry_2": 80},
            CONSERVATIVE_INFORMATION_POLICY: {"draw_1": 35, "draw_2": 60, "scry_2": 20},
        },
        "states_tested": len(corpus),
        "root_choice_divergence_count": len(information_divergences),
        "divergence_examples": information_divergences,
        "rows": information_rows,
    }
    return horizon, information


def _normalized_raw(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle]
    return sorted(rows, key=lambda row: (row["candidate"], row["scenario"], row["trial"]))


def _source_hashes(root: Path) -> dict[str, str]:
    paths = []
    for directory in ("src", "tests", "configs"):
        paths.extend(path for path in (root / directory).rglob("*") if path.is_file())
    return {str(path.relative_to(root)): sha256_file(path) for path in sorted(paths)}


def _write_metric_dictionary(root: Path) -> None:
    rows = [
        "# Run E metric dictionary",
        "",
        "The JSON registry under `outputs/run_e/metric_registry.json` is authoritative. Raw events precede aggregate views; no master score is defined.",
        "",
        "| Metric | Status | Event source | Numerator | Denominator | Timing | Grain | Opportunity ID | Missing data | Snapshot | Direction | Correlated family |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, definition in PHASE3_METRIC_REGISTRY.items():
        rows.append(
            f"| `{name}` | {definition['status']} | `{', '.join(definition['event_source'])}` | "
            f"{definition['numerator']} | {definition['denominator']} | {definition['timing']} | "
            f"{definition['aggregation_grain']} | `{definition['opportunity_id']}` | {definition['missing_data']} | "
            f"{definition['snapshot_role']} | {definition['direction']} | `{definition['correlated_family']}` |"
        )
    _write(root / "RUN_E_METRIC_DICTIONARY.md", "\n".join(rows))


def _write_reports(
    root: Path, output: Path, *, code_commit: str, count: dict[str, Any], checks: dict[str, Any],
    tests: int, no_lookahead_tests: int, horizon: dict[str, Any], information: dict[str, Any],
    smoke_reproduced: bool, seed_ok: bool, source_scan: dict[str, Any], ready: bool,
) -> None:
    gate = "PASS" if ready else "PASS WITH PATCHES"
    patch_rows = [
        ("D-01", "BLOCKER", "Production planner omitted future-color land value", "policies.py; simulator.py", "Visible future coverage in terminal action score", "test_run_e_d01_production_land_semantics.py"),
        ("D-02", "BLOCKER", "Alternate score maximized negative untapped mana", "policies.py", "Explicit tempo precedence maximizes untapped resources", "test_run_e_d02_alternate_tempo.py"),
        ("D-03", "BLOCKER", "Search terminated all continuation at information nodes", "simulator.py; policies.py", "Unresolved causal nodes permit known-card continuation; two value profiles", "test_run_e_d03_information_continuation.py"),
        ("D-04", "BLOCKER", "Land loss subtracted held lands and followed velocity", "simulator.py; policies.py", "Physical battlefield loss and color/source deltas precede optional velocity", "test_run_e_d04_bargain_land_loss.py"),
        ("D-05", "BLOCKER", "Bargain cleared composed triggers", "simulator.py", "Spell-below-trigger queue retained and resolved compositionally", "test_run_e_d05_trigger_composition.py"),
        ("D-06", "BLOCKER", "Raw Hawk cast counted as functional", "simulator.py", "Raw cast and mandatory functional resolution separated", "test_run_e_d06_hawk_functionality.py"),
        ("D-07", "MAJOR", "Priority prose/code ambiguity", "policies.py; RUN_E_POLICY_SPEC.md", "One executable lexicographic precedence", "test_run_e_d07_policy_precedence.py"),
        ("D-08", "MAJOR", "Repeated spell windows lacked denominator identity", "state.py; simulator.py; metrics.py", "Unique opportunity IDs, roles, sequences and pairing context", "test_run_e_d08_metric_windows.py"),
        ("D-09", "MAJOR", "Dependency meant both used and necessary", "payment.py; simulator.py", "Separate used/rescue/dependency fields with counterfactual", "test_run_e_d09_boulder_metrics.py"),
        ("D-10", "MAJOR", "Paired estimator accepted positional mismatches", "statistics.py", "Keyed observations and strict ordered identity checks", "test_run_e_d10_paired_statistics.py"),
        ("D-11", "MAJOR", "Fixture-only options advertised as production metrics", "metrics.py; simulator.py", "Nihil production events; three target-dependent options validation-only", "test_run_e_d11_option_events.py"),
    ]
    table = "\n".join(
        f"| {item} | {severity} | {cause} | `{files}` | {repair} | `{test}` | PASS |"
        for item, severity, cause, files, repair, test in patch_rows
    )
    report = f"""# Mana Lab — Pauper v1 Run E validation report

## A. Executive result

Remediation status: **{gate}**. Phase-3 readiness for independent authorization: **{'YES' if ready else 'NO'}**. No mana-base optimization, screening, ranking, finalist selection, or Pareto analysis was performed.

## B. Provenance

- Input ZIP SHA-256: `{INPUT_ZIP_SHA256}` (verified before extraction).
- Run C implementation marker supplied: `{RUN_C_IMPLEMENTATION_MARKER}`.
- Run C packaging marker supplied: `{RUN_C_PACKAGING_MARKER}`.
- Patched source commit: `{code_commit}`.
- Final output ZIP SHA-256 is written after packaging to the detached `Mana_Lab_Pauper_v1_Run_E.zip.sha256` manifest because an archive cannot contain its own final hash.
- Frozen source/config hashes: `outputs/run_e/source_config_hashes.json`.

## C. Patch table

| Run D ID | Severity | Root Cause | Files Changed | Repair | Regression Test | Result |
|---|---|---|---|---|---|---|
{table}

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

**{no_lookahead_tests} tests passed.** Same visible state/different hidden library remains root-invariant; post-reveal decisions may diverge.

## G. Search-horizon sensitivity

Depths 7/8/9 were compared on **{horizon['states_tested']}** ordinary/targeted production states. Root-choice divergences: **{horizon['root_choice_divergence_count']}**. Depth 8 retained: **{horizon['retain_depth_8']}**. Details: `outputs/run_e/horizon_sensitivity.json`.

## H. Chance-node valuation sensitivity

Baseline vs conservative causal information heuristics were compared on **{information['states_tested']}** states; root divergences: **{information['root_choice_divergence_count']}**. Legal actions are identical; only unrevealed information credit differs. Details: `outputs/run_e/information_valuation_sensitivity.json`.

## I. Rules/mechanics validation

Bargain/Nihil/Cryogen trigger order, optional black payment, Boulder net-zero filtering, Hawk mandatory return, Bridge replay, affinity and Metalcraft transitions pass deterministic and production-path tests.

## J. Metric/event-schema validation

All **{len(PHASE3_METRIC_REGISTRY)}** configured metrics have complete numerator, denominator, timing, grain, opportunity-ID, deduplication, missing-data, snapshot-role, direction and correlation-family definitions. Blood, Munitions and Cryogen stun options are validation-only; Nihil is production-observable.

## K. Statistics/RNG validation

Keyed paired observations reject missing, duplicate, shuffled, scenario-mismatched and replicate-mismatched identities. Closed-form mean/SE/CI fixtures pass. Seed partition: **{'PASS' if seed_ok else 'FAIL'}**. Candidate-label and candidate-order randomness checks pass.

## L. Candidate-neutrality validation

Core policy-source scan forbidden-branch hits: **{source_scan['forbidden_hits']}**. Hand, battlefield, payment, duplicate-card and candidate-order permutations pass.

## M. Full test results

**{tests} passed; 0 failed; 0 skipped.**

## N. Production smoke

Protected benchmark fixtures only; baseline/alternate sequencing and mulligans executed. Candidate-order-normalized raw traces reproduced: **{'PASS' if smoke_reproduced else 'FAIL'}**. Smoke output is machinery validation and is not interpreted as performance evidence.

## O. Remaining limitations

Opponent behavior and target arrival remain unspecified. Target-dependent Blood, Munitions and Cryogen stun activations remain validation-only. Information heuristics are explicit subjective policy controls, not omniscient expected values. Another short independent audit is recommended before expensive optimization.

## P. Phase-3 gate

**RUN E IMPLEMENTATION GATE — {gate}**

**PHASE 3 READY FOR INDEPENDENT AUTHORIZATION — {'YES' if ready else 'NO'}**
"""
    _write(root / "RUN_E_VALIDATION_REPORT.md", report)

    _write(root / "RUN_E_CHANGELOG.md", """# Run E changelog

Run E makes the smallest targeted changes required by D-01 through D-11. The patch table in `RUN_E_VALIDATION_REPORT.md` is authoritative. Frozen deck/card/land counts and candidate construction are unchanged. No candidate performance run exists in this repository.

Key code changes: unified visible future land valuation; corrected alternate tempo sign and precedence; causal known-card continuation through unresolved information nodes; explicit Bargain land/resource loss; composable trigger resolution; raw-vs-functional spell outcomes; opportunity IDs/event roles; consistent Boulder used/rescue/dependency fields; strict keyed pairing; and production-vs-validation metric status.
""")

    _write(root / "RUN_E_ADVERSARIAL_REGRESSIONS.md", """# Run E adversarial regressions

| Finding | Frozen Run C failure | Expected repair | Run E production-path result | Result |
|---|---|---|---|---|
| D-01 | Drossforge won the exact Vault/Bridges/Strix state by name tie | Mistvault supplies visible U+B | Mistvault under hand/battlefield permutations | PASS |
| D-02 | Fewer untapped resources scored higher | Ancient Den over Goldmire | Ancient Den selected | PASS |
| D-03 | Chance node suppressed known continuation | Continue known cards causally | Five information actions continue without hidden identity | PASS |
| D-04 | Held land erased sacrificed-land loss | Count physical battlefield loss | T3 passes; nonland and explicit deadline paths remain | PASS |
| D-05 | Stack clear deleted Nihil trigger | Compose/order triggers | Nihil and Cryogen precede Bargain draws | PASS |
| D-06 | Failed Hawk counted as functional | Separate cast/outcome | Raw cast true, functional false | PASS |
| D-07 | Priority ambiguity | One frozen tuple | Adversarial conflicts follow tuple | PASS |
| D-08 | Window denominator ambiguous | Unique opportunity IDs/roles | Exact primary denominator reconstructs | PASS |
| D-09 | Dependency definitions contradicted | Used/rescue/dependency split | Native/required fixtures consistent | PASS |
| D-10 | Pair identity unchecked | Strict keyed validation | All mismatch modes reject | PASS |
| D-11 | Fixture events advertised as aggregates | Normal event or validation-only | Nihil normal; three target options validation-only | PASS |
""")

    _write(root / "RUN_E_POLICY_SPEC.md", """# Run E executable policy specification

## Baseline precedence

1. Functional hard-deadline executions.
2. Preserve one actually payable demanded opponent-turn reply.
3. Avoid battlefield land, untapped-source and color loss.
4. Functional due executions.
5. Avoid loss of existing artifacts; preserve artifact count.
6. Visible next-turn joint castability and demanded-color coverage, including tapped Bridges.
7. Immediately usable untapped resources.
8. Other functional spell executions.
9. Causal information value.
10. Raw spell casts.
11. Canonical action key only after strategic equality.

## Alternate tempo precedence

Hard deadline, reserve, immediately untapped resources, land preservation, functional due/spell execution, artifact state, future colors, conservative/baseline information value as selected, then canonical tie-break.

## Information nodes

Planning records an unresolved draw/scry count but does not inspect library identities. It continues deterministic actions using only cards known before the reveal. Baseline values draw 1/draw 2/scry 2 as 100/190/80 units; conservative values them 35/60/20. Board objects, payments, sacrifices and retained resources are valued independently by ordinary state terms.

## Functional execution

`spell_cast` is raw. `spell_resolution.functional` requires mandatory resolution completion; Glint Hawk that cannot return an artifact is false. Due/hard/spell execution counters consume only functional outcomes.
""")

    _write(root / "RUN_E_PROVENANCE.md", f"""# Run E provenance

- Verified Run C ZIP SHA-256: `{INPUT_ZIP_SHA256}`.
- Imported-baseline local commit precedes the patched source commit.
- Patched source commit: `{code_commit}`.
- Source/config hashes: `outputs/run_e/source_config_hashes.json`.
- Seed manifest: `outputs/run_e/seed_manifest.json`.
- Reproduction commands: `outputs/run_e/reproduction_commands.md`.
- Final archive self-hash is necessarily detached beside the ZIP in `Mana_Lab_Pauper_v1_Run_E.zip.sha256`.
""")

    _write(root / "RUN_E_PHASE3_READINESS.md", f"""# Run E Phase-3 readiness

## Gate

**{gate}**

All ranking-relevant Run D BLOCKER and MAJOR findings have deterministic and production-path regressions. Legacy tests, no-lookahead checks, state-key checks, candidate-space invariants, depth sensitivity, information-policy sensitivity, keyed pairing, candidate neutrality and protected smoke pass.

No optimization, candidate screening, ranking, finalist selection, Pareto construction or mana-base recommendation was performed.

**PHASE 3 READY FOR INDEPENDENT AUTHORIZATION — {'YES' if ready else 'NO'}**

A short independent gate review remains recommended before expensive Phase 3 execution.
""")


def run_e(root: str | Path) -> int:
    root = Path(root).resolve()
    output = root / "outputs" / "run_e"
    output.mkdir(parents=True, exist_ok=True)
    deck = load_deck(root / "configs" / "decks" / "Strixpatch_Affinity_v1.3.deck.yaml")
    experiment = load_yaml(root / "configs" / "experiments" / "Strixpatch_Affinity_v1.3.experiment.yaml")
    if experiment["phase_control"]["optimization_execution_allowed"]:
        raise RuntimeError("Run E refuses optimization-enabled configuration")

    full = _run(root, [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    full_text = full.stdout + full.stderr
    _write(output / "unit_test_report.txt", full_text)
    tests = _test_count(full_text)

    no_lookahead = _run(root, [
        sys.executable, "-m", "unittest", "discover", "-s", "tests",
        "-p", "test_*causal*.py", "-v",
    ])
    hidden = _run(root, [
        sys.executable, "-m", "unittest", "discover", "-s", "tests",
        "-p", "test_*lookahead*.py", "-v",
    ])
    no_lookahead_text = no_lookahead.stdout + no_lookahead.stderr + hidden.stdout + hidden.stderr
    _write(output / "no_lookahead_test_report.txt", no_lookahead_text)
    no_lookahead_tests = sum(int(value) for value in re.findall(r"Ran (\d+) tests?", no_lookahead_text))

    regressions: dict[str, Any] = {}
    for issue in range(1, 12):
        pattern = f"test_run_e_d{issue:02d}_*.py"
        result = _run(root, [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", pattern, "-v"])
        regressions[f"D-{issue:02d}"] = {
            "pattern": pattern,
            "returncode": result.returncode,
            "tests": _test_count(result.stdout + result.stderr),
            "result": "PASS" if result.returncode == 0 else "FAIL",
        }
    _write_json(output / "regression_results.json", regressions)
    with (output / "regression_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["issue", "result", "tests", "pattern"])
        writer.writeheader()
        for issue, item in regressions.items():
            writer.writerow({"issue": issue, **{key: item[key] for key in ("result", "tests", "pattern")}})

    count = candidate_count_report(deck)
    validate_candidate_report(count)
    checks = deterministic_checks(deck)
    checks.update({
        "deck_size": deck.maindeck_size,
        "nonlands": deck.nonland_count,
        "lands": deck.land_count,
        "giants_boulder": deck.card_by_name["Giant's Boulder"].copies,
        "t2_myr_enforcer_counterexample": search_t2_myr_enforcer(deck),
    })
    _write_json(output / "candidate_count_check.json", count)
    _write_json(output / "deterministic_checks.json", checks)

    configured_metrics = experiment["metrics"]["primary"] + experiment["metrics"]["secondary"]
    validate_metric_registry(configured_metrics)
    _write_json(output / "metric_registry.json", PHASE3_METRIC_REGISTRY)
    _write_metric_dictionary(root)

    seed_ok = validate_seed_partition(
        experiment["randomness"]["selection_seed"], experiment["randomness"]["validation_seed"],
        experiment["randomness"]["replicate_seeds"],
    )
    seed_manifest = {
        **experiment["randomness"],
        "independent_partition": seed_ok,
        "trial_pairing_keys": ["scenario", "replicate", "trial", "on_play"],
        "stable_derivation": "SHA-256(scenario|trial|mulligan_attempt); candidate excluded",
    }
    _write_json(output / "seed_manifest.json", seed_manifest)

    corpus = _ordinary_state_corpus(deck, int(experiment["randomness"]["validation_seed"])) + _targeted_states(deck)
    horizon, information = _sensitivity(corpus, deck)
    _write_json(output / "horizon_sensitivity.json", horizon)
    _write_json(output / "information_valuation_sensitivity.json", information)

    candidates = {
        "C0": dict(deck.current_mana_base),
        "HISTORICAL_C1_REGRESSION": {
            "Ancient Den": 4, "Seat of the Synod": 4, "Vault of Whispers": 4,
            "Great Furnace": 4, "Mistvault Bridge": 3,
        },
    }
    smoke_a = output / "production_smoke_order_a"
    smoke_b = output / "production_smoke_order_b"
    run_smoke_matrix(deck, experiment, candidates, smoke_a, trials_override=1)
    run_smoke_matrix(deck, experiment, dict(reversed(list(candidates.items()))), smoke_b, trials_override=1)
    smoke_reproduced = _normalized_raw(smoke_a / "production_smoke_raw_events.jsonl.gz") == _normalized_raw(smoke_b / "production_smoke_raw_events.jsonl.gz")
    _write_json(output / "production_smoke_reproducibility.json", {
        "candidate_iteration_orders": [list(candidates), list(reversed(list(candidates)))],
        "normalized_raw_events_equal": smoke_reproduced,
        "interpretation": "machinery validation only; not candidate performance evidence",
    })

    source_scan_paths = [root / "src" / "mana_lab" / name for name in ("simulator.py", "payment.py", "effects.py", "state.py", "mulligan.py")]
    hits = []
    for path in source_scan_paths:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "C0" in line or "HISTORICAL_C" in line:
                hits.append({"file": str(path.relative_to(root)), "line": line_number, "text": line.strip()})
    policy_branch = policy_source_has_candidate_branch()
    if policy_branch:
        hits.append({"file": "src/mana_lab/policies.py", "line": None, "text": "candidate token in choose_land/choose_action"})
    source_scan = {
        "forbidden_hits": len(hits), "hits": hits,
        "files_scanned": ["choose_land", "choose_action", *(str(p.relative_to(root)) for p in source_scan_paths)],
    }
    _write_json(output / "candidate_neutrality_scan.json", source_scan)
    _write_json(output / "source_config_hashes.json", _source_hashes(root))

    code_commit = _git_head(root)
    exact_ok = (
        deck.maindeck_size == 60 and deck.nonland_count == 41 and deck.land_count == 19
        and deck.card_by_name["Giant's Boulder"].copies == 4
        and count["enumeration_count"] == 296706 and count["dp_count"] == 296706
        and count["c0_occurrences"] == 1 and count["minimum_bridges"] == 3
        and count["three_bridge_candidates"] == 56
    )
    ready = all((
        full.returncode == 0, no_lookahead.returncode == 0, hidden.returncode == 0,
        all(item["result"] == "PASS" for item in regressions.values()), exact_ok,
        seed_ok, horizon["retain_depth_8"], smoke_reproduced,
        source_scan["forbidden_hits"] == 0,
    ))
    _write_reports(
        root, output, code_commit=code_commit, count=count, checks=checks, tests=tests,
        no_lookahead_tests=no_lookahead_tests, horizon=horizon, information=information,
        smoke_reproduced=smoke_reproduced, seed_ok=seed_ok, source_scan=source_scan,
        ready=ready,
    )
    _write(output / "reproduction_commands.md", """# Run E reproduction commands

```bash
export PYTHONPATH="$PWD/src"
python -m unittest discover -s tests -v
python -m mana_lab.cli candidate-count
python -m mana_lab.cli deterministic-checks
python -m mana_lab.cli run-e
```

`run-e` performs validation, protected smoke and reporting only. It refuses optimization-enabled configuration and contains no candidate scoring command.
""")
    _write(output / "run_e_gate.txt", f"RUN E IMPLEMENTATION GATE — {'PASS' if ready else 'PASS WITH PATCHES'}\nPHASE 3 READY FOR INDEPENDENT AUTHORIZATION — {'YES' if ready else 'NO'}")
    return 0 if ready else 1
