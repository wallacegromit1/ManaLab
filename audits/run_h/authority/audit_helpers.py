#!/usr/bin/env python3
"""Independent, non-optimizing Run F audit checks.

This helper never evaluates candidate performance.  It verifies package/input
invariants and demonstrates protected synthetic counterexamples in the shipped
analysis helpers and policy configuration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from math import comb
from pathlib import Path

import yaml


EXPECTED_ZIP_SHA256 = "82d1dcd663de5a8bcb2d9917271fba264c509bdff8b45d1920b9f97ccf0d0c71"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inclusion_exclusion_count() -> int:
    # Shift four mandatory mono lands from [1,4] to [0,3].  The remaining six
    # Bridge variables are [0,4].  Count solutions to the shifted sum of 15.
    total = 0
    for mono_violations in range(5):
        for bridge_violations in range(7):
            remainder = 15 - 4 * mono_violations - 5 * bridge_violations
            if remainder >= 0:
                total += (
                    (-1) ** (mono_violations + bridge_violations)
                    * comb(4, mono_violations)
                    * comb(6, bridge_violations)
                    * comb(remainder + 9, 9)
                )
    return total


def recursive_candidate_audit(deck):
    ranges = [range(land.min_copies, land.max_copies + 1) for land in deck.lands]
    current = dict(deck.current_mana_base)
    keys: list[str] = []
    bridge_histogram: Counter[int] = Counter()
    c0_occurrences = 0

    def recurse(index: int, remaining: int, values: list[int]) -> None:
        nonlocal c0_occurrences
        if index == len(ranges):
            if remaining != 0:
                return
            pairs = tuple(sorted((land.name, values[i]) for i, land in enumerate(deck.lands)))
            keys.append("|".join(f"{name}:{count}" for name, count in pairs))
            bridge_histogram[sum(values[i] for i, land in enumerate(deck.lands) if land.enters_tapped)] += 1
            if all(values[i] == current.get(land.name, 0) for i, land in enumerate(deck.lands)):
                c0_occurrences += 1
            return
        lower = sum(item.start for item in ranges[index + 1 :])
        upper = sum(item.stop - 1 for item in ranges[index + 1 :])
        for value in ranges[index]:
            if lower <= remaining - value <= upper:
                recurse(index + 1, remaining - value, values + [value])

    recurse(0, deck.land_count, [])
    return {
        "count": len(keys),
        "unique": len(set(keys)),
        "c0_occurrences": c0_occurrences,
        "minimum_bridges": min(bridge_histogram),
        "three_bridge_candidates": bridge_histogram[3],
        "candidate_set_sha256": hashlib.sha256("\n".join(sorted(keys)).encode()).hexdigest(),
        "keys": set(keys),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(args.repo / "src"))
    from mana_lab.cards import load_deck
    from mana_lab.candidates import enumerate_candidates
    from mana_lab.metrics import pareto_dominates
    from mana_lab.policies import ALTERNATE_ACTION_POLICY, ActionOption, choose_action

    deck = load_deck(args.repo / "configs/decks/Strixpatch_Affinity_v1.3.deck.yaml")
    experiment = yaml.safe_load(
        (args.repo / "configs/experiments/Strixpatch_Affinity_v1.3.experiment.yaml").read_text()
    )
    recursive = recursive_candidate_audit(deck)
    production_keys = {candidate.key for candidate in enumerate_candidates(deck)}

    base_option = dict(
        due_executions=0,
        artifact_count=0,
        cards_drawn=0,
        untapped_resources=1,
        land_loss=0,
    )
    tap_out = ActionOption(key="tap-out", reserve_preserved=False, **base_option)
    reserve = ActionOption(key="reserve", reserve_preserved=True, **base_option)
    alternate_selection = choose_action([tap_out, reserve], ALTERNATE_ACTION_POLICY)

    profile_names = set(deck.raw.get("decision_profiles", []))
    configured_profile_definitions = experiment.get("objective_profiles", {})
    screening = experiment["search"]["screening"]
    result = {
        "zip": {
            "expected": EXPECTED_ZIP_SHA256,
            "observed": file_sha256(args.zip),
        },
        "frozen_input": {
            "deck_size": deck.maindeck_size,
            "nonlands": deck.nonland_count,
            "lands": deck.land_count,
            "giants_boulder": deck.card_by_name["Giant's Boulder"].copies,
            "c0": dict(deck.current_mana_base),
        },
        "candidate_space": {
            "inclusion_exclusion_count": inclusion_exclusion_count(),
            **{key: value for key, value in recursive.items() if key != "keys"},
            "same_set_as_production_generator": recursive["keys"] == production_keys,
        },
        "phase3_freeze_gaps": {
            "phase": experiment["phase_control"]["phase"],
            "optimization_allowed": experiment["phase_control"]["optimization_execution_allowed"],
            "screening_enabled": screening["enabled"],
            "screening_trials": screening["trials_per_candidate"],
            "medium_trials": experiment["search"]["medium_trials"],
            "finalist_count_target": experiment["search"]["finalist_count_target"],
            "validation_trials": experiment["search"]["validation_trials"],
            "named_profiles": sorted(profile_names),
            "defined_profiles": sorted(configured_profile_definitions),
            "missing_exact_profile_definitions": sorted(profile_names - set(configured_profile_definitions)),
        },
        "synthetic_counterexamples": {
            "pareto_direction": {
                "metric": "unused_mana (lower is better)",
                "left": 5.0,
                "right": 1.0,
                "shipped_helper_says_left_dominates": pareto_dominates(
                    {"unused_mana": 5.0}, {"unused_mana": 1.0}, ["unused_mana"]
                ),
                "expected": False,
            },
            "alternate_tap_out": {
                "configured_policy": deck.policy_contract["opponent_reserve_alternate"],
                "equal_options_selected": alternate_selection.key,
                "expected_for_true_tap_out": "tap-out",
            },
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
