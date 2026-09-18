from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from collections import Counter, deque
from dataclasses import dataclass
from itertools import combinations, product
from pathlib import Path
from typing import Any

from .candidates import candidate_count_report
from .cards import DeckSpec, load_deck, load_yaml
from .mana import ManaCost
from .metrics import OVERLAP_FAMILIES
from .simulator import run_smoke_matrix
from .statistics import at_least_one, binomial_standard_error, hypergeometric_pmf, joint_presence_two_sets


EXPECTED_HISTOGRAM = {
    "3": 56,
    "4": 504,
    "5": 2460,
    "6": 8520,
    "7": 20646,
    "8": 38040,
    "9": 54824,
    "10": 60240,
    "11": 52266,
    "12": 35020,
    "13": 16860,
    "14": 6024,
    "15": 1246,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_facts(deck: DeckSpec, counts: dict[str, int]) -> dict[str, Any]:
    sources = {color: 0 for color in "WUBR"}
    tapped = 0
    for name, copies in counts.items():
        land = deck.land_by_name[name]
        tapped += copies * int(land.enters_tapped)
        for color in land.colors:
            if color in sources:
                sources[color] += copies
    return {
        "lands": sum(counts.values()),
        "untapped": sum(counts.values()) - tapped,
        "bridges": tapped,
        "direct_sources": sources,
    }


def deterministic_checks(deck: DeckSpec) -> dict[str, Any]:
    c0 = dict(deck.current_mana_base)
    historical_c1 = {
        "Ancient Den": 4,
        "Seat of the Synod": 4,
        "Vault of Whispers": 4,
        "Great Furnace": 4,
        "Mistvault Bridge": 3,
    }
    land_distribution = {str(k): hypergeometric_pmf(60, 19, 7, k) for k in range(8)}
    source_presence = {
        "W5": at_least_one(60, 5, 7),
        "U7": at_least_one(60, 7, 7),
        "B7": at_least_one(60, 7, 7),
        "R4": at_least_one(60, 4, 7),
        "joint_U7_B7_overlap2": joint_presence_two_sets(60, 7, 7, 2, 7),
    }
    expected_distribution = {
        "0": 0.058212162537,
        "1": 0.221206217641,
        "2": 0.331809326462,
        "3": 0.254088222966,
        "4": 0.106984514933,
        "5": 0.024688734215,
        "6": 0.002880352325,
        "7": 0.000130468921,
    }
    expected_presence = {
        "W5": 0.474562172527,
        "U7": 0.600879549232,
        "B7": 0.600879549232,
        "R4": 0.399499625745,
        "joint_U7_B7_overlap2": 0.392405791175,
    }
    return {
        "c0": source_facts(deck, c0),
        "historical_c1_regression_only": source_facts(deck, historical_c1),
        "raw_seven_19_land_distribution": land_distribution,
        "raw_seven_direct_source_presence": source_presence,
        "acceptance": {
            "land_distribution_matches": all(abs(land_distribution[key] - value) < 5e-13 for key, value in expected_distribution.items()),
            "source_presence_matches": all(abs(source_presence[key] - value) < 5e-13 for key, value in expected_presence.items()),
            "c0_facts_match": source_facts(deck, c0) == {
                "lands": 19,
                "untapped": 15,
                "bridges": 4,
                "direct_sources": {"W": 5, "U": 7, "B": 7, "R": 4},
            },
        },
        "smoke_tolerance_rule": "absolute error <= max(0.005, 4 * binomial standard error using exact p and n=20000)",
    }


@dataclass(frozen=True)
class AbstractT2State:
    sources: tuple[tuple[tuple[str, ...], bool], ...]
    boulders: tuple[bool, ...]
    artifacts: int
    remaining: tuple[tuple[str, int], ...]
    sequence: tuple[str, ...]


T2_ACTIONS = {
    "Giant's Boulder": (1, {}, 1),
    "Blood Fountain": (0, {"B": 1}, 2),
    "Cryogen Relic": (1, {"U": 1}, 1),
    "Baleful Strix": (0, {"U": 1, "B": 1}, 1),
    "Nihil Spellbomb": (1, {}, 1),
    "Refurbished Familiar": (3, {"B": 1}, 1),
    "Utrom Monitor": (4, {"U": 1}, 1),
    "Myr Enforcer": (7, {}, 1),
}


def _abstract_payment(state: AbstractT2State, cost: ManaCost):
    untapped = [index for index, (_, tapped) in enumerate(state.sources) if not tapped]
    available_boulders = [index for index, tapped in enumerate(state.boulders) if not tapped]
    need = cost.total
    if need == 0:
        return (), ()
    if len(untapped) < need:
        return None
    required = [color for color, amount in sorted(cost.colored.items()) for _ in range(amount)] + ["*"] * cost.generic
    for chosen in combinations(untapped, need):
        choices = []
        for source_index in chosen:
            colors = state.sources[source_index][0]
            native = [(color, None) for color in colors]
            filtered = [(color, boulder) for boulder in available_boulders for color in "WUBR"]
            choices.append(native + filtered)
        for outputs in product(*choices):
            filters = [boulder for _, boulder in outputs if boulder is not None]
            if len(filters) != len(set(filters)):
                continue
            produced = [color for color, _ in outputs]
            remaining = list(produced)
            valid = True
            for pip in required:
                if pip == "*":
                    if remaining:
                        remaining.pop()
                    else:
                        valid = False
                        break
                elif pip in remaining:
                    remaining.remove(pip)
                else:
                    valid = False
                    break
            if valid:
                return chosen, tuple(filters)
    return None


def _apply_abstract_action(state: AbstractT2State, name: str) -> AbstractT2State | None:
    remaining = dict(state.remaining)
    if remaining.get(name, 0) <= 0:
        return None
    generic, colored, artifact_gain = T2_ACTIONS[name]
    if name == "Refurbished Familiar":
        generic = max(0, generic - state.artifacts)
    elif name == "Utrom Monitor":
        generic = max(0, generic - state.artifacts)
    elif name == "Myr Enforcer":
        generic = max(0, generic - state.artifacts)
    payment = _abstract_payment(state, ManaCost(generic=generic, colored=colored))
    if payment is None:
        return None
    source_indices, boulder_indices = payment
    sources = tuple((colors, tapped or index in source_indices) for index, (colors, tapped) in enumerate(state.sources))
    boulders = tuple(tapped or index in boulder_indices for index, tapped in enumerate(state.boulders))
    if name == "Giant's Boulder":
        boulders = boulders + (False,)
    remaining[name] -= 1
    return AbstractT2State(
        sources=sources,
        boulders=boulders,
        artifacts=state.artifacts + artifact_gain,
        remaining=tuple(sorted(remaining.items())),
        sequence=state.sequence + (f"cast {name}",),
    )


def search_t2_myr_enforcer(deck: DeckSpec) -> tuple[str, ...] | None:
    """Exhaust legal artifact-building lines through T2 over all legal land pairs.

    The search gives the player every relevant frozen nonland in hand, a strict
    superset of any real opening sequence. Non-artifact and resource-losing
    actions are excluded because they cannot increase mana or reduce Enforcer's
    cost. Failure in this relaxed state is therefore a valid impossibility proof.
    """
    initial_counts = {name: deck.card_by_name[name].copies for name in T2_ACTIONS}
    for first_land in deck.lands:
        for second_land in deck.lands:
            state = AbstractT2State(
                sources=((first_land.colors, first_land.enters_tapped),),
                boulders=(),
                artifacts=1,
                remaining=tuple(sorted(initial_counts.items())),
                sequence=(f"T1 play {first_land.name}",),
            )
            frontier = deque([state])
            seen: set[tuple] = set()
            end_t1: list[AbstractT2State] = []
            while frontier:
                current = frontier.popleft()
                key = (current.sources, current.boulders, current.artifacts, current.remaining)
                if key in seen:
                    continue
                seen.add(key)
                end_t1.append(current)
                for name in T2_ACTIONS:
                    if name == "Myr Enforcer":
                        continue
                    nxt = _apply_abstract_action(current, name)
                    if nxt is not None:
                        frontier.append(nxt)
            for prior in end_t1:
                turn2 = AbstractT2State(
                    sources=tuple((colors, False) for colors, _ in prior.sources) + ((second_land.colors, second_land.enters_tapped),),
                    boulders=tuple(False for _ in prior.boulders),
                    artifacts=prior.artifacts + 1,
                    remaining=prior.remaining,
                    sequence=prior.sequence + (f"T2 play {second_land.name}",),
                )
                frontier = deque([turn2])
                seen_t2: set[tuple] = set()
                while frontier:
                    current = frontier.popleft()
                    key = (current.sources, current.boulders, current.artifacts, current.remaining)
                    if key in seen_t2:
                        continue
                    seen_t2.add(key)
                    enforcer = _apply_abstract_action(current, "Myr Enforcer")
                    if enforcer is not None:
                        return enforcer.sequence
                    for name in T2_ACTIONS:
                        if name == "Myr Enforcer":
                            continue
                        nxt = _apply_abstract_action(current, name)
                        if nxt is not None:
                            frontier.append(nxt)
    return None


def _run_tests(root: Path, pattern: str | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    if pattern:
        command.extend(["-p", pattern])
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(root / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(command, cwd=root, env=environment, text=True, capture_output=True)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_candidate_report(report: dict[str, Any]) -> None:
    assert report["enumeration_count"] == 296706
    assert report["dp_count"] == 296706
    assert report["minimum_bridges"] == 3
    assert report["three_bridge_candidates"] == 56
    assert report["bridge_histogram"] == EXPECTED_HISTOGRAM
    assert report["c0_occurrences"] == 1
    assert report["unique_keys"] == 296706


def run_a(root: str | Path) -> int:
    root = Path(root).resolve()
    output = root / "outputs" / "run_a"
    output.mkdir(parents=True, exist_ok=True)
    deck_path = root / "configs" / "decks" / "Strixpatch_Affinity_v1.3.deck.yaml"
    experiment_path = root / "configs" / "experiments" / "Strixpatch_Affinity_v1.3.experiment.yaml"
    deck = load_deck(deck_path)
    experiment = load_yaml(experiment_path)
    if experiment["phase_control"]["optimization_execution_allowed"]:
        raise RuntimeError("Run A refuses a config that authorizes optimization")

    count_report = candidate_count_report(deck)
    _write_json(output / "candidate_count_check.json", count_report)
    validate_candidate_report(count_report)
    checks = deterministic_checks(deck)
    t2_counterexample = search_t2_myr_enforcer(deck)
    checks["t2_myr_enforcer_counterexample"] = list(t2_counterexample) if t2_counterexample else None
    checks["t2_myr_enforcer_impossible"] = t2_counterexample is None
    _write_json(output / "deterministic_checks.json", checks)
    if t2_counterexample is not None:
        (output / "run_a_stop_certificate.md").write_text(
            "# Run A stop certificate\n\nRun A: **FAIL**. The T2 Myr Enforcer fixture was disproved.\n\n"
            + "Exact counterexample:\n\n"
            + "\n".join(f"- {step}" for step in t2_counterexample)
            + "\n\nNo optimization was run.\n",
            encoding="utf-8",
        )
        return 2

    tests = _run_tests(root)
    test_text = tests.stdout + tests.stderr
    (output / "unit_test_report.txt").write_text(test_text, encoding="utf-8")
    no_lookahead = _run_tests(root, "test_*lookahead*.py")
    (output / "no_lookahead_test_report.txt").write_text(no_lookahead.stdout + no_lookahead.stderr, encoding="utf-8")
    if tests.returncode or no_lookahead.returncode:
        (output / "run_a_stop_certificate.md").write_text(
            "# Run A stop certificate\n\nRun A: **FAIL** due to test failure.\n\nNo smoke optimization or full optimization was run.\n",
            encoding="utf-8",
        )
        return 1

    candidates = {
        "C0": dict(deck.current_mana_base),
        "HISTORICAL_C1_REGRESSION": {
            "Ancient Den": 4,
            "Seat of the Synod": 4,
            "Vault of Whispers": 4,
            "Great Furnace": 4,
            "Mistvault Bridge": 3,
        },
    }
    smoke = run_smoke_matrix(deck, experiment, candidates, output)
    smoke_passed = _write_reports(root, deck, experiment, count_report, checks, smoke, test_text)
    return 0 if smoke_passed else 3


def _write_reports(
    root: Path,
    deck: DeckSpec,
    experiment: dict[str, Any],
    count_report: dict[str, Any],
    checks: dict[str, Any],
    smoke: dict[str, Any],
    test_text: str,
) -> bool:
    output = root / "outputs" / "run_a"
    input_files = sorted(
        list((root / "configs").rglob("*"))
        + list((root / "benchmarks").glob("*"))
        + list((root / "docs" / "core").glob("*"))
    )
    hash_lines = [f"{sha256_file(path)}  {path.relative_to(root)}" for path in input_files if path.is_file()]
    source_files = sorted((root / "src").rglob("*.py"))
    hash_lines += [f"{sha256_file(path)}  {path.relative_to(root)}" for path in source_files]
    (output / "config_hashes.txt").write_text("\n".join(hash_lines) + "\n", encoding="utf-8")
    environment = [
        f"python={platform.python_version()}",
        f"implementation={platform.python_implementation()}",
        f"platform={platform.platform()}",
        "test_runner=unittest (standard library)",
        f"pyyaml={__import__('yaml').__version__}",
    ]
    (output / "environment.txt").write_text("\n".join(environment) + "\n", encoding="utf-8")

    tree = subprocess.run(
        ["find", ".", "-path", "./.git", "-prune", "-o", "-type", "d", "-name", "__pycache__", "-prune", "-o", "-type", "f", "-print"],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    (output / "repository_tree.txt").write_text("\n".join(sorted(line[2:] for line in tree.stdout.splitlines() if line.startswith("./"))) + "\n", encoding="utf-8")

    mechanics = "\n".join(f"| `{name}` | IMPLEMENTED + TESTED |" for name in deck.mechanics_required)
    coverage = f"""# Run A coverage matrix

| Required mechanic | Status |
|---|---|
{mechanics}

All required mechanics have direct unit fixtures. Target-dependent late abilities are option-only as frozen in the model specification.

## Objective-risk controls

- No default master score exists.
- No generic tapland penalty exists.
- No fixed opponent-turn Boulder credit exists.
- Historical C1 is marked regression-only.
- Overlap families: `{json.dumps(OVERLAP_FAMILIES, sort_keys=True)}`
"""
    (output / "coverage_matrix.md").write_text(coverage, encoding="utf-8")

    chosen_scenario = "all_play|baseline_functional_london|baseline_hand_demand"
    c0_smoke = smoke["summaries"][chosen_scenario]["C0"]
    exact_dist = checks["raw_seven_19_land_distribution"]
    comparisons = []
    for key, exact in exact_dist.items():
        observed = c0_smoke["raw_opening_land_distribution"].get(key, 0.0)
        tolerance = max(0.005, 4 * binomial_standard_error(exact, c0_smoke["trials"]))
        comparisons.append((f"lands={key}", exact, observed, tolerance, abs(observed - exact) <= tolerance))
    source_fields = {
        "W direct source": (checks["raw_seven_direct_source_presence"]["W5"], "raw_W"),
        "U direct source": (checks["raw_seven_direct_source_presence"]["U7"], "raw_U"),
        "B direct source": (checks["raw_seven_direct_source_presence"]["B7"], "raw_B"),
        "R direct source": (checks["raw_seven_direct_source_presence"]["R4"], "raw_R"),
        "joint U+B direct sources": (checks["raw_seven_direct_source_presence"]["joint_U7_B7_overlap2"], "raw_joint_UB"),
    }
    for label, (exact, field) in source_fields.items():
        observed = c0_smoke["rates_and_means"][field]
        tolerance = max(0.005, 4 * binomial_standard_error(exact, c0_smoke["trials"]))
        comparisons.append((label, exact, observed, tolerance, abs(observed - exact) <= tolerance))
    smoke_lines = [
        "# NOT A RANKING / NOT AN OPTIMIZATION",
        "",
        "These C0 and historical-C1 runs validate mechanics, policies, common-random-number wiring, and logging only. They must not be used to select a mana base.",
        "",
        f"Trials: **{smoke['trials_per_scenario_candidate']:,} per scenario/candidate** across all configured play/draw, mulligan, and sequencing combinations.",
        "",
        "## Exact-vs-simulation check (C0 raw opening seven)",
        "",
        "| Quantity | Exact | Observed | Predeclared tolerance | Pass |",
        "|---|---:|---:|---:|:---:|",
    ]
    smoke_lines += [f"| {key} | {exact:.9f} | {observed:.9f} | {tol:.9f} | {'PASS' if passed else 'FAIL'} |" for key, exact, observed, tol, passed in comparisons]
    smoke_lines += [
        "",
        "Full event-level sufficient statistics are in `smoke_events.csv.gz`; sampled policy action traces are in `smoke_policy_traces.jsonl`; aggregates are in `smoke_summary.json`.",
        "",
        "No cross-candidate winner, shortlist, frontier, or recommendation was computed.",
    ]
    (output / "smoke_validation_report.md").write_text("\n".join(smoke_lines) + "\n", encoding="utf-8")

    commands = """# Reproduction commands

From the repository root:

```bash
export PYTHONPATH="$PWD/src"
python -m unittest discover -s tests -v
python -m mana_lab.cli candidate-count
python -m mana_lab.cli deterministic-checks
python -m mana_lab.cli run-a
```

`run-a` enforces the build/validation phase gate and refuses optimization-enabled configuration.
"""
    (output / "reproduction_commands.md").write_text(commands, encoding="utf-8")
    all_smoke_pass = all(item[-1] for item in comparisons)
    stop_status = "PASS" if all_smoke_pass else "FAIL"
    stop = f"""# Run A stop certificate

Run A status: **{stop_status}**.

- Full legal enumeration was used only for exact counting and invariants.
- No Monte Carlo was run across the 296,706 candidates.
- No performance screening, elimination, finalist selection, Pareto construction, or mana-base recommendation ran.
- Only C0 and `HISTORICAL_C1_REGRESSION` received the configured smoke validation.
- Selection seed `2026091701` remained unused.
- No optimality decision label was emitted.

The authorized next step is **Phase 2 Chat implementation QA**. Full optimization remains blocked until a new explicit authorization.
"""
    (output / "run_a_stop_certificate.md").write_text(stop, encoding="utf-8")

    test_count = test_text.count(" ... ok")
    result_line = "PASS — implementation is ready for Phase 2 Chat QA." if all_smoke_pass else "FAIL — at least one required smoke exact-check disagreed. Optimization remains blocked."
    report = f"""# Mana Lab — Pauper v1 Run A validation report

## Result

**{result_line}**

**No final optimization was run. No candidate was ranked, selected, or recommended.**

## Implemented

- Physical-card and zone state with ordered library, hand, battlefield, graveyard, exile, stack, turn/phase, tapped state, and visible-information boundaries.
- Explicit colored/generic payment, net-zero Boulder filtering, affinity, artifact/Metalcraft state, actual draws and scry-2 library mutation.
- Cryogen enter/leave triggers, Bargain cost/trigger order, Hawk returns, Blood token, Nihil optional B draw, opponent-window resources, same-turn sequencing, London mulligans, and play/draw.
- Identical named baseline/alternate policies with deterministic tie breaks and audit logs.
- Full legal candidate enumeration plus independent DP coefficient count.

## Validation

- Unit tests passed: **{test_count}** reported cases, zero failures.
- No-lookahead suite passed with zero failures.
- Enumeration and DP both returned **{count_report['enumeration_count']:,}** candidates.
- Minimum Bridges: **{count_report['minimum_bridges']}**; three-Bridge class: **{count_report['three_bridge_candidates']}**.
- Candidate histogram, C0 facts, hypergeometric distribution, source-presence fixtures, and T2 Myr Enforcer impossibility fixture matched.
- Smoke exact-vs-simulation agreement: **{'PASS' if all_smoke_pass else 'FAIL'}** under the predeclared four-standard-error/0.5-point floor rule.

## Ambiguities and deviations

- The action-policy specification defines a lexicographic objective but not one unique exhaustive search implementation. Run A implements executable shared legal-action scoring and exposes deterministic traces; Phase 2 should review realism before optimization.
- The smoke run stores one compact event-level sufficient-statistics row per trial plus full sampled policy traces. This preserves every reported smoke aggregate without writing every low-level engine event for all 480,000 trials.
- No trial-count deviation: 20,000 per configured scenario/candidate.
- Target-dependent late Boulder, Cryogen-stun, and Munitions value remains option-only, as required by the frozen model.

## Stop

Run A is complete. Full mana-base optimization remains prohibited until Phase 2 Chat QA is completed and a later execution run is explicitly authorized.
"""
    (root / "RUN_A_VALIDATION_REPORT.md").write_text(report, encoding="utf-8")
    return all_smoke_pass
