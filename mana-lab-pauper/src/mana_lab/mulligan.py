from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Callable

from .cards import DeckSpec
from .state import PhysicalCard


BASELINE_MULLIGAN = "baseline_functional_london"
ALTERNATE_MULLIGAN = "alternate_landcount_london"


@dataclass(frozen=True)
class MulliganResult:
    hand: tuple[PhysicalCard, ...]
    library: tuple[PhysicalCard, ...]
    mulligans: int
    bottomed: tuple[PhysicalCard, ...]
    attempts: tuple[tuple[str, ...], ...]


def _land_cards(hand: list[PhysicalCard], deck: DeckSpec) -> list[PhysicalCard]:
    return [card for card in hand if card.name in deck.land_by_name]


def visible_two_mana_by_t2(hand: list[PhysicalCard], deck: DeckSpec) -> bool:
    lands = _land_cards(hand, deck)
    if len(lands) < 2:
        return False
    # Two Bridges cannot provide two usable mana on T2 because the second enters
    # tapped. Any visible untapped mono land supplies the second usable source.
    return any(not deck.land_by_name[card.name].enters_tapped for card in lands)


def should_keep(hand: list[PhysicalCard], final_size: int, deck: DeckSpec, policy_name: str) -> bool:
    if final_size <= 4:
        return True
    lands = len(_land_cards(hand, deck))
    if policy_name == BASELINE_MULLIGAN:
        return 2 <= lands <= 4 and visible_two_mana_by_t2(hand, deck)
    if policy_name == ALTERNATE_MULLIGAN:
        return 2 <= lands <= 5
    raise ValueError(f"unknown mulligan policy {policy_name}")


def choose_bottom(hand: list[PhysicalCard], count: int, deck: DeckSpec) -> tuple[PhysicalCard, ...]:
    if count == 0:
        return ()
    if count < 0 or count > len(hand):
        raise ValueError("invalid bottom count")
    final_size = len(hand) - count
    target_ranges = {6: (2, 3), 5: (2, 2), 4: (1, 2)}
    low, high = target_ranges.get(final_size, (2, 3))

    def retained_score(bottom_indices: tuple[int, ...]) -> tuple:
        kept = [card for index, card in enumerate(hand) if index not in bottom_indices]
        lands = _land_cards(kept, deck)
        distance = 0 if low <= len(lands) <= high else min(abs(len(lands) - low), abs(len(lands) - high))
        two_mana = int(visible_two_mana_by_t2(kept, deck))
        colors = {
            color
            for card in lands
            for color in deck.land_by_name[card.name].colors
        }
        due_colors = {
            color
            for card in kept
            if card.name in deck.card_by_name and deck.card_by_name[card.name].earliest_realistic_turn <= 3
            for color in deck.card_by_name[card.name].rules.get("colored_cost", {})
        }
        coverage = len(colors.intersection(due_colors))
        early_actions = sum(
            card.name in deck.card_by_name and deck.card_by_name[card.name].earliest_realistic_turn <= 2
            for card in kept
        )
        canonical_kept = tuple(sorted((card.name, card.uid) for card in kept))
        return (-distance, two_mana, coverage, early_actions, canonical_kept)

    subsets = list(combinations(range(len(hand)), count))
    best_score = max(retained_score(indices) for indices in subsets)
    best = min(
        (indices for indices in subsets if retained_score(indices) == best_score),
        key=lambda indices: tuple(sorted((hand[index].name, hand[index].uid) for index in indices)),
    )
    return tuple(hand[index] for index in best)


def london_mulligan(
    deck: DeckSpec,
    policy_name: str,
    draw_seven: Callable[[int], tuple[list[PhysicalCard], list[PhysicalCard]]],
) -> MulliganResult:
    attempts: list[tuple[str, ...]] = []
    for mulligans in range(4):
        hand, library = draw_seven(mulligans)
        if len(hand) != 7:
            raise ValueError("London mulligan must draw a fresh seven")
        attempts.append(tuple(card.name for card in hand))
        final_size = 7 - mulligans
        if should_keep(hand, final_size, deck, policy_name):
            bottomed = choose_bottom(hand, mulligans, deck)
            bottom_ids = {card.uid for card in bottomed}
            kept = tuple(card for card in hand if card.uid not in bottom_ids)
            return MulliganResult(kept, tuple(library + list(bottomed)), mulligans, bottomed, tuple(attempts))
    raise AssertionError("automatic four-card keep should make this unreachable")

