from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import product
from typing import Iterable, Iterator

from .cards import DeckSpec, LandSpec, canonical_counts


@dataclass(frozen=True)
class Candidate:
    counts: tuple[tuple[str, int], ...]
    bridge_count: int

    @property
    def key(self) -> str:
        return "|".join(f"{name}:{count}" for name, count in self.counts)

    def as_dict(self) -> dict[str, int]:
        return dict(self.counts)


def enumerate_candidates(deck: DeckSpec) -> Iterator[Candidate]:
    lands = deck.lands
    ranges = [range(land.min_copies, land.max_copies + 1) for land in lands]
    for values in product(*ranges):
        if sum(values) != deck.land_count:
            continue
        counts = canonical_counts(zip((land.name for land in lands), values))
        bridge_count = sum(value for land, value in zip(lands, values) if land.enters_tapped)
        yield Candidate(counts, bridge_count)


def count_candidates_dp(deck: DeckSpec) -> int:
    coefficient = [0] * (deck.land_count + 1)
    coefficient[0] = 1
    for land in deck.lands:
        updated = [0] * (deck.land_count + 1)
        for current, ways in enumerate(coefficient):
            if not ways:
                continue
            for copies in range(land.min_copies, land.max_copies + 1):
                if current + copies <= deck.land_count:
                    updated[current + copies] += ways
        coefficient = updated
    return coefficient[deck.land_count]


def candidate_count_report(deck: DeckSpec) -> dict:
    count = 0
    histogram: Counter[int] = Counter()
    keys: set[str] = set()
    current_map = dict(deck.current_mana_base)
    current = canonical_counts((land.name, current_map.get(land.name, 0)) for land in deck.lands)
    current_occurrences = 0
    minimum_bridges = 999
    for candidate in enumerate_candidates(deck):
        count += 1
        histogram[candidate.bridge_count] += 1
        minimum_bridges = min(minimum_bridges, candidate.bridge_count)
        if candidate.key in keys:
            raise AssertionError("duplicate candidate")
        keys.add(candidate.key)
        if candidate.counts == current:
            current_occurrences += 1
        values = candidate.as_dict()
        for land in deck.lands:
            if not land.min_copies <= values[land.name] <= land.max_copies:
                raise AssertionError("candidate violates bound")
            if not land.artifact:
                raise AssertionError("benchmark candidate is not an artifact land")
    return {
        "enumeration_count": count,
        "dp_count": count_candidates_dp(deck),
        "minimum_bridges": minimum_bridges,
        "three_bridge_candidates": histogram[3],
        "bridge_histogram": {str(key): histogram[key] for key in sorted(histogram)},
        "c0_occurrences": current_occurrences,
        "unique_keys": len(keys),
    }
