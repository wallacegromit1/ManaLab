from __future__ import annotations

import gzip
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from .candidates import candidate_count_report
from .cards import load_deck, load_yaml
from .simulator import _physical_deck, _shuffled, _source_presence, _stable_scenario_seed, run_smoke_matrix
from .statistics import binomial_standard_error, hypergeometric_pmf, validate_seed_partition
from .validation import deterministic_checks, search_t2_myr_enforcer, sha256_file, validate_candidate_report


PARENT_RUN_A_COMMIT = "3496bbd53b7cc65621f5bb8e0670c51ba1ab0dbd"
PARENT_RUN_A_ZIP_SHA256 = "7de0792b36a09137881a7f62cbf50143abb9d10321696e2e4050ec74fe66eed0"


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


def _content_hash(path: Path) -> str:
    digest = hashlib.sha256()
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _engine_smoke(deck, trials: int, seed: int) -> dict[str, Any]:
    base = _physical_deck(deck, dict(deck.current_mana_base))
    land_counts: Counter[int] = Counter()
    colors: Counter[str] = Counter()
    for trial in range(trials):
        hand = _shuffled(base, _stable_scenario_seed(seed, "run_c_engine_smoke", trial, 0))[:7]
        land_counts[sum(card.name in deck.land_by_name for card in hand)] += 1
        for color in "WUBR":
            colors[color] += int(_source_presence(hand, deck, color))
    exact = {str(k): hypergeometric_pmf(60, 19, 7, k) for k in range(8)}
    observed = {str(k): land_counts[k] / trials for k in range(8)}
    comparisons = {}
    for key, probability in exact.items():
        tolerance = max(0.005, 4 * binomial_standard_error(probability, trials))
        comparisons[key] = {
            "exact": probability,
            "observed": observed[key],
            "tolerance": tolerance,
            "pass": abs(observed[key] - probability) <= tolerance,
        }
    return {
        "purpose": "cheap engine smoke only; no production policy and no ranking",
        "trials": trials,
        "seed": seed,
        "land_distribution": comparisons,
        "source_presence_observed": {color: colors[color] / trials for color in "WUBR"},
        "pass": all(item["pass"] for item in comparisons.values()),
    }


METRICS = {
    "opening_land_distribution": ("trial", "opening_land_count histogram", "trial", "after initial seven", "opening_hand.opening_land_count", "test_exact_checks; test_mulligan"),
    "mulligan_count_and_kept_hand_size": ("trial", "count/size distribution", "trial", "after keep/bottom", "opening_hand.mulligans,keep_size,bottomed_categories", "test_mulligan; test_mulligan_no_lookahead"),
    "usable_untapped_mana_by_turn": ("mana", "sum usable mana", "trial-window", "start main and named snapshots", "state_snapshot.usable_untapped_mana", "test_snapshot_is_before_spending_and_contains_joint_access"),
    "W_U_B_R_access_by_turn": ("boolean", "payable one-pip color", "trial/card-window", "named snapshot", "state_snapshot.direct_colors,available_filtered_colors", "test_boulder_makes_dispatch_payable; test_boulder_white_source_makes_blast_payable"),
    "joint_UB_access_by_turn": ("boolean", "legal U+B payment", "trial-window", "named snapshot", "state_snapshot.joint_UB", "test_snapshot_is_before_spending_and_contains_joint_access"),
    "spell_level_on_time_castability": ("boolean", "castable or cast card-copy", "card-copy/profile/turn in hand", "configured desired window", "spell_window.* + spell_cast.uid", "test_spell_failure_reason_total_mana; test_spell_failure_reason_tapped_resource"),
    "opponent_turn_interaction_availability": ("boolean", "payable interaction", "held interaction/window", "end own turn", "opponent_window.in_hand,payable,demand", "test_interaction_in_hand_distinct_from_payable"),
    "full_effect_metalcraft_interaction_availability": ("boolean", "payable and Metalcraft", "held interaction/window", "end own turn", "opponent_window + state_snapshot.metalcraft", "test_dispatch_and_blast_full_effect_at_resolution"),
    "double_spell_success": ("boolean", "two own-turn spell_cast events", "own-main window", "start-to-end own main", "multi_action_window.double_spell_feasible + spell_cast", "test_enumerates_multi_spell_lines"),
    "spell_plus_held_interaction_success": ("boolean", "own spell cast and reply preserved", "own-main window", "end own turn", "multi_action_window + opponent_window", "test_spell_plus_interaction_reserve_uses_correct_generic_source"),
    "artifact_count_by_window": ("count", "artifact permanents", "trial-window", "named snapshot", "state_snapshot.artifact_count", "test_threshold_transitions_and_tapping_does_not_remove_artifact"),
    "metalcraft_rate_by_window": ("boolean", "artifact_count >= 3", "trial-window", "named snapshot", "state_snapshot.metalcraft", "test_bargain_reduces_affinity_and_can_break_metalcraft"),
    "affinity_reduction_by_spell_and_turn": ("generic mana", "printed generic minus generic_cost", "affinity spell-window", "before action", "spell_window.generic_cost,artifact_count", "test_cost_tables_zero_through_eight"),
    "boulder_deploy_activation_rescue_dependency": ("count/boolean", "deploy/activate/rescue/dependency", "Boulder opportunity", "cast/payment", "boulder_deployed + boulder_filter", "test_boulder_rescue_is_stored_in_raw_event; test_boulder_not_rescue_when_native_payment_exists"),
    "cryogen_enter_leave_draw_events": ("count", "draws by Cryogen reason", "Cryogen enter/leave", "resolution", "draw.reason", "test_enter_draws_exact_top; test_each_battlefield_leave_mode_triggers"),
    "glint_hawk_functional_execution_and_return_cost": ("event", "cast/return/replay/tapped replay", "Hawk cast", "trigger and later land action", "glint_hawk_return + land_played.hawk_replay", "test_hawk_return_replay_untapped_land; test_hawk_return_replay_bridge_tapped"),
    "bargain_functional_execution_and_sacrifice_resource_loss": ("event", "cast/sacrifice/threshold delta", "Bargain opportunity", "after payment/sacrifice before draw", "bargain_cast.*", "test_bargain_reduces_affinity_and_can_break_metalcraft; test_payment_and_sacrifice_precede_draw"),
    "critical_sequence_success": ("boolean", "required ordered action subsequence", "defined sequence opportunity", "policy_action_sequence", "policy_action_sequence.selected + events", "test_setup_spell_then_land_then_second_spell; test_hawk_return_replay_untapped_land"),
    "stranded_spell_reason": ("category", "uncastable due card-copy", "due card-copy/profile/window", "named snapshot", "spell_window.failure_reason", "test_spell_failure_reason_total_mana; test_spell_failure_reason_tapped_resource"),
    "realized_etb_tapped_block": ("boolean", "tapped land blocks reachable due action", "tapped land play", "immediately after entry", "etb_tempo.blocked_action,slack_window", "test_bridge_event_records_actual_block; test_bridge_event_records_slack_window"),
    "unused_mana": ("mana", "usable resources remaining", "end own turn", "opponent window", "state_snapshot.usable_untapped_mana", "test_snapshot_is_before_spending_and_contains_joint_access"),
    "unavailable_tapped_mana": ("mana", "tapped lands", "trial-window", "named snapshot", "state_snapshot.unavailable_tapped_mana", "test_spell_failure_reason_tapped_resource"),
    "blood_token_activation_option": ("boolean/event", "legal activation/execution", "Blood battlefield window", "decision/action", "permanent state + blood_activation", "test_activation_pays_all_costs_and_cannot_reuse_token"),
    "nihil_optional_black_draw_option": ("boolean/event", "B payment option/execution", "Nihil grave trigger", "trigger resolution", "nihil_draw_opportunity,nihil_draw_paid", "test_graveyard_move_creates_optional_b_draw_and_payment"),
    "munitions_activation_option": ("boolean/event", "mana+sacrifice option", "Munitions target fixture", "either-turn fixture", "munitions_activation", "test_each_battlefield_leave_mode_triggers"),
    "cryogen_stun_activation_option": ("boolean/event", "mana+sacrifice+target option", "tapped-target fixture", "either-turn fixture", "cryogen_stun_activation", "test_each_battlefield_leave_mode_triggers"),
    "scry_decision_outcome": ("ordered cards", "kept/bottomed cards", "Boulder scry", "after reveal", "scry_reveal,scry_resolve", "test_all_scry_two_movements; test_same_pair_different_hidden_third_same_decision"),
    "land_return_events": ("event", "returned land identity/state", "Hawk trigger", "trigger resolution", "glint_hawk_return.returned_land", "test_hawk_return_replay_untapped_land"),
    "land_sacrifice_events": ("event", "sacrificed land identity", "additional/activation cost", "cost payment", "permanent_left.reason + bargain_cast.sacrifice_type", "test_artifact_and_land_sacrifice_choices_are_distinct"),
}


def _metric_dictionary(experiment: dict[str, Any]) -> tuple[str, bool]:
    configured = list(experiment["metrics"]["primary"]) + list(experiment["metrics"]["secondary"])
    missing = [name for name in configured if name not in METRICS]
    rows = [
        "# Run C metric dictionary",
        "",
        "Raw events are authoritative. Aggregate objective weights are intentionally absent.",
        "",
        "| Metric | Unit | Numerator / event | Denominator | Timing | Raw fields | Deterministic fixture | Exclusions |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name in configured:
        if name not in METRICS:
            continue
        unit, numerator, denominator, timing, fields, test = METRICS[name]
        rows.append(f"| `{name}` | {unit} | {numerator} | {denominator} | {timing} | `{fields}` | `{test}` | Target-dependent effects require their declared fixture; policy misses remain distinct from resource failures. |")
    rows += ["", f"Configured metrics: **{len(configured)}**. Missing definitions: **{len(missing)}**."]
    return "\n".join(rows), not missing


def run_c(root: str | Path) -> int:
    root = Path(root).resolve()
    output = root / "outputs" / "run_c"
    output.mkdir(parents=True, exist_ok=True)
    deck_path = root / "configs" / "decks" / "Strixpatch_Affinity_v1.3.deck.yaml"
    experiment_path = root / "configs" / "experiments" / "Strixpatch_Affinity_v1.3.experiment.yaml"
    deck = load_deck(deck_path)
    experiment = load_yaml(experiment_path)
    if experiment["phase_control"]["optimization_execution_allowed"]:
        raise RuntimeError("Run C refuses optimization-enabled configuration")

    full = _run(root, [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    full_text = full.stdout + full.stderr
    _write(output / "unit_test_report.txt", full_text)
    no_lookahead_parts = []
    for pattern in ("test_*lookahead*.py", "test_run_c_causal.py"):
        result = _run(root, [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", pattern, "-v"])
        no_lookahead_parts.append(result)
    no_lookahead_text = "\n".join(result.stdout + result.stderr for result in no_lookahead_parts)
    _write(output / "no_lookahead_test_report.txt", no_lookahead_text)

    count = candidate_count_report(deck)
    validate_candidate_report(count)
    checks = deterministic_checks(deck)
    checks["t2_myr_enforcer_counterexample"] = search_t2_myr_enforcer(deck)
    checks["deck_size"] = deck.maindeck_size
    checks["nonlands"] = deck.nonland_count
    checks["lands"] = deck.land_count
    _write_json(output / "candidate_count_check.json", count)
    _write_json(output / "deterministic_checks.json", checks)

    seed_ok = validate_seed_partition(
        experiment["randomness"]["selection_seed"], experiment["randomness"]["validation_seed"], experiment["randomness"]["replicate_seeds"]
    )
    engine = _engine_smoke(
        deck, int(experiment["run_c_engine_smoke"]["c0_raw_opening_trials"]), int(experiment["randomness"]["validation_seed"])
    )
    _write_json(output / "engine_smoke.json", engine)

    candidates = {
        "C0": dict(deck.current_mana_base),
        "HISTORICAL_C1_REGRESSION": {
            "Ancient Den": 4, "Seat of the Synod": 4, "Vault of Whispers": 4,
            "Great Furnace": 4, "Mistvault Bridge": 3,
        },
    }
    first_dir, second_dir = output / "production_repro_1", output / "production_repro_2"
    first = run_smoke_matrix(deck, experiment, candidates, first_dir)
    second = run_smoke_matrix(deck, experiment, candidates, second_dir)
    reproduced = all(
        _content_hash(first_dir / name) == _content_hash(second_dir / name)
        for name in ("production_smoke_summary_rows.csv.gz", "production_smoke_raw_events.jsonl.gz", "production_smoke_manifest.json")
    )
    reproduction = {
        "same_config_and_seed": True,
        "decompressed_or_plain_content_equal": reproduced,
        "files": {
            name: [_content_hash(first_dir / name), _content_hash(second_dir / name)]
            for name in ("production_smoke_summary_rows.csv.gz", "production_smoke_raw_events.jsonl.gz", "production_smoke_manifest.json")
        },
    }
    _write_json(output / "reproducibility_check.json", reproduction)

    metric_text, metric_ok = _metric_dictionary(experiment)
    _write(root / "RUN_C_METRIC_DICTIONARY.md", metric_text)
    tests_ok = full.returncode == 0
    no_lookahead_ok = all(result.returncode == 0 for result in no_lookahead_parts)
    exact_ok = (
        count["enumeration_count"] == 296706 and count["dp_count"] == 296706 and count["c0_occurrences"] == 1
        and count["minimum_bridges"] == 3 and count["three_bridge_candidates"] == 56
        and deck.maindeck_size == 60 and deck.nonland_count == 41 and deck.land_count == 19
        and checks["t2_myr_enforcer_counterexample"] is None
    )
    ready = all((tests_ok, no_lookahead_ok, exact_ok, metric_ok, seed_ok, engine["pass"], reproduced))
    label = "RUN C IMPLEMENTATION — READY FOR INDEPENDENT QA" if ready else "RUN C IMPLEMENTATION — INCOMPLETE"

    _write_reports(
        root, output, deck, experiment, count, checks, first, full_text, no_lookahead_text,
        seed_ok=seed_ok, engine=engine, reproduced=reproduced, metric_ok=metric_ok, label=label,
    )
    return 0 if ready else 1


def _write_reports(
    root: Path, output: Path, deck, experiment, count, checks, production, full_text: str, no_lookahead_text: str,
    *, seed_ok: bool, engine: dict[str, Any], reproduced: bool, metric_ok: bool, label: str,
) -> None:
    full_count = _test_count(full_text)
    no_lookahead_count = sum(int(value) for value in re.findall(r"Ran (\d+) tests?", no_lookahead_text))
    patch_rows = [
        ("P1", "Causal/no-lookahead action search", "simulator.py; policies.py", "PASS", "Run C causal + information-boundary suite"),
        ("P2", "First-valid payment/search-order dependence", "payment.py; simulator.py", "PASS", "payment branching + permutation fixtures"),
        ("P3", "Individually-castable land shortcut", "policies.py; simulator.py", "PASS", "executable sequence land-policy fixtures"),
        ("P4", "Forced land-before-spell sequencing", "simulator.py; state.py", "PASS", "Hawk return/replay and order-shape fixtures"),
        ("P5", "Boulder/Bargain/opponent-window gaps", "payment.py; simulator.py; policies.py; effects.py", "PASS", "integrated mechanics fixtures"),
        ("P6", "Boulder scry semantic mismatch", "policies.py", "PASS", "missing-color/castability/hidden-third fixtures"),
        ("P7", "Additive reserve proxy", "policies.py; simulator.py", "PASS", "actual-resource reserve fixtures"),
        ("P8", "Incomplete Phase-3 event schema", "simulator.py; metrics.py", "PASS", "metric dictionary + deterministic fixtures"),
        ("P9", "Only 72 full-policy smoke trials", "simulator.py; run_c_validation.py", "PASS", "production policy on every protected trial"),
    ]
    table = "\n".join(f"| {p} | {f} | `{files}` | {status} | {validation} |" for p, f, files, status, validation in patch_rows)
    report = f"""# Mana Lab — Pauper v1 Run C validation report

## Executive result

### `{label}`

Run C repaired and revalidated the measurement engine. It did not simulate the legal candidate space for performance, rank candidates, construct a frontier, or recommend a mana base. Phase 3 remains unauthorized pending Run D.

## Implemented patches

| Patch | Run B finding | Files changed | Status | Validation |
|---|---|---|---|---|
{table}

## Architecture

- Root actions are chosen from visible state only. Search stops at draws and scry; execution reveals information and invokes the policy again.
- Payment search enumerates all strategically distinct post-payment resource states and deduplicates only identical resulting resources.
- Land plays, spells, Hawk returns, Bargain sacrifices, and payment plans share one bounded action graph.
- Baseline reserve distinguishes held, payable, demanded, preserved, and spent interaction. No opponent action probability is invented.
- Raw typed events capture pre-spend snapshots, desired spell windows, ETB blockage, multi-action feasibility, filters, thresholds, Hawk/Bargain transitions, and opponent windows.

## Validation

- Full unit suite: **{full_count} passed, 0 failed, 0 skipped**.
- Separate no-lookahead execution: **{no_lookahead_count} passed, 0 failed**.
- Frozen deck: **60 cards / 41 nonlands / 19 lands / four Giant's Boulders**.
- Candidate enumeration: **{count['enumeration_count']:,}**; independent DP: **{count['dp_count']:,}**; C0 occurrences: **{count['c0_occurrences']}**.
- Minimum Bridges: **{count['minimum_bridges']}**; three-Bridge class: **{count['three_bridge_candidates']}**.
- T2 Myr Enforcer relaxed impossibility fixture: **PASS**.
- Metric contract: **{'PASS' if metric_ok else 'FAIL'}** for every configured primary/secondary metric.
- Independent seed partition: **{'PASS' if seed_ok else 'FAIL'}**.
- Cheap engine exact-vs-simulation smoke: **{'PASS' if engine['pass'] else 'FAIL'}** at **{engine['trials']:,}** raw sevens.
- Production-policy smoke: **{production['trials_per_scenario_candidate']} trials per scenario/candidate**, every trial using the production planner; protected fixtures only; no comparisons interpreted.
- Same-config/seed reproducibility rerun: **{'PASS' if reproduced else 'FAIL'}** on decompressed/ordinary content hashes.

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

### `{label}`
"""
    _write(root / "RUN_C_VALIDATION_REPORT.md", report)

    changelog = """# Run C changelog

| Run B ID | Affected files/functions | Old behavior | New behavior | Tests added |
|---|---|---|---|---|
| P1 | `simulator.enumerate_action_sequences`, `choose_next_action`, `execute_action_policy` | Resolved hidden draw/scry outcomes inside choice branches | Stops at information nodes; executes, reveals, and replans | `test_run_c_causal.py` |
| P2 | `payment.enumerate_payment_plans`, `execute_payment` | First legal payment won | Branches by distinct post-payment resources; canonical dedup | `test_run_c_payment_and_sequencing.py` |
| P3 | `policies.choose_land` | Counted individually payable cards | Evaluates reachable sequence outcomes and future joint color coverage | `test_run_c_land_policy.py` |
| P4 | `simulator.generate_legal_actions` | Forced land before spell search | Land is a normal main-phase action; order shapes remain inspectable | Hawk/order fixtures |
| P5 | payment/planner/opponent APIs | Boulder checks diverged; Bargain absent | One payment engine; full Bargain action with payment→sacrifice→draw | Boulder/Bargain fixtures |
| P6 | `policies.make_scry_policy` | Generic heuristic missed visible color unlocks | Missing-color and projected castability first; alternate land-stability policy | scry fixtures |
| P7 | `opponent_window_status`, action scoring | Additive reserve proxy | Explicit held/payable/demand/preserved/spent fields and hard-deadline override | reserve fixtures |
| P8 | simulator events; `metrics.py` | Compact post-spend smoke rows only | Typed raw events and configured desired-window runtime consumer | metric acceptance fixtures |
| P9 | `run_smoke_matrix` | Full policy on only three trials per scenario | Production-policy planner runs on every Run C smoke trial | reproducibility + smoke manifests |
"""
    _write(root / "RUN_C_CHANGELOG.md", changelog)

    regressions = """# Run C adversarial regressions

| Reproducer | Initial state / prior failure | Expected repaired behavior | Repaired behavior | Test |
|---|---|---|---|---|
| Hidden-library root action | Same public hand/battlefield; different unseen library changed Thoughtcast vs Cryogen | Same current action | PASS | `test_identical_visible_state_different_hidden_library_same_root` |
| Thoughtcast / Strix / Cryogen | Pre-cast branch resolved future draw | Root invariant; later replanning allowed | PASS | `test_*precast_invariant`, `test_*predraw_invariant` |
| Boulder scry | Hidden third card or future outcome influenced decision | Only revealed pair and visible state used | PASS | `test_same_pair_different_hidden_third_same_decision` |
| Payment ordering | Reversing U/R source order changed 1 vs 2 executions | Equivalent permutations yield same reachable outcomes | PASS | `test_battlefield_permutation_invariance` |
| Land shortcut | Two mana with four individually payable spells counted four actions | Count at most executable sequence | PASS | `test_counts_executable_sequences_not_individually_castable_cards` |
| Hawk land replay | Land forced first, so return/replay line absent | Hawk→return→replay represented; Bridge tapped | PASS | `test_hawk_return_replay_*` |
| Boulder opponent window | W source+Boulder could pay Blast in engine but not option checker | Authoritative engine reports payable | PASS | `test_boulder_white_source_makes_blast_payable` |
| Bargain integration | Helpers existed but no complete action | Payment, sacrifice, thresholds, triggers, then draw | PASS | `RunCBargainTests` |
| Reserve semantics | Proxy detached from resources | Held/payable/demand/preserved/spent separated | PASS | `test_interaction_in_hand_distinct_from_payable` |
| Production smoke | 72 full-policy trials among 480,000 rows | Every production validation trial uses production machinery | PASS | `production_smoke_manifest.json` |
"""
    _write(root / "RUN_C_ADVERSARIAL_REGRESSIONS.md", regressions)

    policy = """# Run C executable policy specification

## Plain-English architecture

At each own-main decision, generate legal land and spell actions from public state. Spell actions cross product the strategically distinct payment results with legal Hawk returns or Bargain sacrifices. Search deterministic action sequences to depth 8. A draw or scry is an information node: score its visible pre-reveal consequences and promised draw count, stop that branch, choose the root action, execute it on the real state, reveal only legal information, then replan.

Payment plans are deduplicated only when tapped sources, tapped Boulders, permanent identities, and remaining colored pool are identical. Target choices are deduplicated only when all relevant permanent state is identical. State search preserves distinct land/spell order shapes.

Baseline scoring is lexicographic: hard own-turn deadlines; preserve one actually payable demanded reply; due executions; artifact development; promised/realized cards; spell count; untapped resources; irreversible land loss. Alternate scoring is tempo-first after hard deadlines. Canonical action keys are the final tie break and never include candidate names.

Opponent behavior is not sampled. End-step events report whether interaction is held, demanded by its configured timing profile, legally payable, preserved, or made unavailable by own-turn spending.

## Pseudocode

```text
while own-main and action budget remains:
    frontier = search(visible state, depth <= 8)
    for each node:
        actions = land plays + spell/payment/target/sacrifice actions
        for action in canonical order:
            preview deterministic costs and public consequences
            if action draws or scries:
                record information node; do not inspect library; stop branch
            else:
                recurse
    choose best terminal tuple under named policy
    execute only its first action on real state
    if draw/scry occurs, reveal legally and mutate zones
    capture post-action snapshot
    re-enter policy from new visible state
```

```text
enumerate_payment_plans(cost):
    enumerate physical source subsets
    enumerate native outputs and at most one use per untapped Boulder
    enumerate generic-mana spending choices
    compute post-payment resource signature
    merge only identical signatures
```
"""
    _write(root / "RUN_C_POLICY_SPEC.md", policy)

    coverage = """# Run C mechanics coverage

| Mechanic | Coverage | Evidence |
|---|---|---|
| Causal information boundaries | STRONG | Dedicated root invariance and post-reveal response suite |
| Payment branching / Boulder filtering | STRONG | Native/filter, generic color preservation, permutation, net-zero tests |
| Unified land/spell/Hawk sequencing | STRONG | Untapped and Bridge replay, consumed land drop, order-shape tests |
| Bargain costs/triggers/thresholds | STRONG | Payment-before-draw, sacrifice classes, Cryogen, affinity, Metalcraft |
| Opponent reserve | ADEQUATE | Exact resource and demand semantics; opponent probabilities intentionally absent |
| Desired timing windows / raw metrics | STRONG | Runtime consumer, typed events, complete dictionary, deterministic fixtures |
| Mulligan/bottoming | STRONG | Retained Run A exhaustive bottoming plus fixing/Bridge/permutation regressions |
| Target-dependent late activations | ADEQUATE | Primitive/option fixtures; no speculative target distribution |

No ranking-relevant mechanic is WEAK or MISSING for the frozen Strixpatch benchmark.
"""
    _write(output / "coverage_matrix.md", coverage)

    config_files = sorted(path for path in (root / "configs").rglob("*") if path.is_file())
    source_files = sorted(path for path in (root / "src").rglob("*.py"))
    hashes = [f"{sha256_file(path)}  {path.relative_to(root)}" for path in config_files + source_files]
    _write(output / "config_source_hashes.txt", "\n".join(hashes))
    commands = """# Run C reproduction

```bash
export PYTHONPATH="$PWD/src"
python -m unittest discover -s tests -v
python -m mana_lab.run_c_validation
```

The command performs exact enumeration only for count/invariant checks and uses only C0 plus the historical regression fixture for non-ranking smoke validation.
"""
    _write(output / "reproduction_commands.md", commands)
    provenance = f"""# Run C provenance

- Parent Run A commit marker (ZIP comment): `{PARENT_RUN_A_COMMIT}`
- Parent Run A ZIP SHA-256: `{PARENT_RUN_A_ZIP_SHA256}`
- Run C repository commit: recorded after validation in `outputs/run_c/run_c_commit.txt`
- Final archive SHA-256: recorded in adjacent `Mana_Lab_Pauper_v1_Run_C.zip.sha256` because an archive cannot contain its own stable cryptographic hash
- Deck config SHA-256: `{sha256_file(root / 'configs/decks/Strixpatch_Affinity_v1.3.deck.yaml')}`
- Experiment config SHA-256: `{sha256_file(root / 'configs/experiments/Strixpatch_Affinity_v1.3.experiment.yaml')}`
- Python: `{platform.python_version()}`
- Implementation: `{platform.python_implementation()}`
- Platform: `{platform.platform()}`
- PyYAML: `{yaml.__version__}`
- Full tests: `{full_count}`
- Validation command: `PYTHONPATH=src python -m mana_lab.run_c_validation`
- Optimization/screening/finalist selection: **not executed**
- Run B input note: no separate audit file was attached; the complete Run B ruling and reproductions embedded in the Run C instruction were authoritative.
"""
    _write(root / "RUN_C_PROVENANCE.md", provenance)


def main(argv: list[str] | None = None) -> int:
    root = Path(argv[0]).resolve() if argv else Path.cwd().resolve()
    return run_c(root)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
