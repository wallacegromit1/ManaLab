from __future__ import annotations

import copy
from typing import Any

from .policies import (
    ALTERNATE_RESERVE_POLICY,
    BASELINE_ACTION_POLICY,
    BASELINE_INFORMATION_POLICY,
    BASELINE_RESERVE_POLICY,
    BASELINE_SCRY_POLICY,
)
from .simulator import _selected_result, enumerate_action_sequences
from .state import GameState, Permanent, make_card


REQUIRED_STRUCTURAL_CLASSES = {
    "boulder_multiple_spells",
    "affinity_changes_mid_sequence",
    "hawk_return_replay_competing_lines",
    "interaction_hold_vs_development",
    "representative_double_spell",
    "bargain_resource_and_trigger_composition",
}


def structural_state_corpus(deck) -> list[tuple[str, GameState]]:
    def state_with_lands(names: list[str], turn: int) -> GameState:
        state = GameState(phase="main", turn=turn)
        for index, name in enumerate(names):
            state.battlefield.append(Permanent(
                make_card(f"g-depth-land-{index}", name, artifact=True, land=True),
                tapped=False, land_spec=deck.land_by_name[name],
            ))
        return state

    boulder = state_with_lands(["Seat of the Synod", "Vault of Whispers", "Ancient Den"], 3)
    boulder.battlefield.append(Permanent(make_card("g-boulder", "Giant's Boulder", artifact=True)))
    boulder.hand = [
        make_card("g-strix", "Baleful Strix", artifact=True, creature=True),
        make_card("g-familiar", "Refurbished Familiar", artifact=True, creature=True),
    ]

    affinity = state_with_lands(["Seat of the Synod", "Vault of Whispers"], 2)
    affinity.battlefield.append(Permanent(make_card("g-existing", "Giant's Boulder", artifact=True)))
    affinity.hand = [
        make_card("g-nihil", "Nihil Spellbomb", artifact=True),
        make_card("g-thoughtcast", "Thoughtcast"),
        make_card("g-familiar-2", "Refurbished Familiar", artifact=True, creature=True),
    ]

    hawk = state_with_lands(["Ancient Den", "Seat of the Synod", "Vault of Whispers"], 3)
    hawk.battlefield.append(Permanent(make_card("g-cryogen", "Cryogen Relic", artifact=True)))
    hawk.hand = [
        make_card("g-hawk", "Glint Hawk", creature=True),
        make_card("g-thoughtcast-2", "Thoughtcast"),
    ]

    interaction = state_with_lands(["Great Furnace", "Seat of the Synod", "Vault of Whispers"], 3)
    interaction.hand = [
        make_card("g-blast", "Galvanic Blast"),
        make_card("g-thoughtcast-3", "Thoughtcast"),
        make_card("g-nihil-2", "Nihil Spellbomb", artifact=True),
    ]

    double = state_with_lands(["Ancient Den", "Seat of the Synod", "Vault of Whispers", "Great Furnace"], 4)
    double.hand = [
        make_card("g-strix-2", "Baleful Strix", artifact=True, creature=True),
        make_card("g-hawk-2", "Glint Hawk", creature=True),
        make_card("g-nihil-3", "Nihil Spellbomb", artifact=True),
    ]

    bargain = state_with_lands(["Vault of Whispers", "Goldmire Bridge", "Ancient Den"], 3)
    bargain.battlefield.append(Permanent(make_card("g-nihil-field", "Nihil Spellbomb", artifact=True)))
    bargain.hand = [
        make_card("g-bargain", "Reckoner's Bargain"),
        make_card("g-familiar-3", "Refurbished Familiar", artifact=True, creature=True),
    ]
    return [
        ("boulder_multiple_spells", boulder),
        ("affinity_changes_mid_sequence", affinity),
        ("hawk_return_replay_competing_lines", hawk),
        ("interaction_hold_vs_development", interaction),
        ("representative_double_spell", double),
        ("bargain_resource_and_trigger_composition", bargain),
    ]


def planner_depth_audit(deck, depths: tuple[int, ...] = (7, 8, 9)) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    corpus = structural_state_corpus(deck)
    if {name for name, _ in corpus} != REQUIRED_STRUCTURAL_CLASSES:
        raise AssertionError("structural planner corpus is incomplete")
    for label, state in corpus:
        choices: dict[str, str] = {}
        result_counts: dict[str, int] = {}
        for depth in depths:
            results = enumerate_action_sequences(
                copy.deepcopy(state), deck, scry_policy_name=BASELINE_SCRY_POLICY,
                information_policy_name=BASELINE_INFORMATION_POLICY, max_depth=depth,
            )
            selected = _selected_result(results, BASELINE_ACTION_POLICY, BASELINE_RESERVE_POLICY)
            choices[str(depth)] = "PASS" if selected is None else selected.option.key
            result_counts[str(depth)] = len(results)
        stable = len(set(choices.values())) == 1
        if not stable:
            failures.append(label)
        rows.append({
            "structural_class": label,
            "root_choices": choices,
            "terminal_state_counts": result_counts,
            "stable": stable,
        })

    # The reserve sensitivity must be executable on the specific hold/develop
    # structure, even when its selected root happens to tie in a given fixture.
    interaction_state = dict(corpus)["interaction_hold_vs_development"]
    results = enumerate_action_sequences(
        copy.deepcopy(interaction_state), deck, scry_policy_name=BASELINE_SCRY_POLICY,
        information_policy_name=BASELINE_INFORMATION_POLICY, max_depth=8,
    )
    reserve = _selected_result(results, BASELINE_ACTION_POLICY, BASELINE_RESERVE_POLICY)
    tap_out = _selected_result(results, BASELINE_ACTION_POLICY, ALTERNATE_RESERVE_POLICY)
    return {
        "depths": list(depths),
        "acceptance_rule": "all six predeclared structural fixtures have identical selected roots at depths 7/8/9",
        "states_tested": len(rows),
        "required_structural_classes": sorted(REQUIRED_STRUCTURAL_CLASSES),
        "unstable_classes": failures,
        "pass": not failures,
        "reserve_sensitivity": {
            "baseline_root": None if reserve is None else reserve.option.key,
            "tap_out_root": None if tap_out is None else tap_out.option.key,
            "both_executable": reserve is not None and tap_out is not None,
        },
        "rows": rows,
    }

