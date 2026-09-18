from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml


COLORS = ("W", "U", "B", "R", "G", "C")


@dataclass(frozen=True)
class LandSpec:
    name: str
    colors: tuple[str, ...]
    artifact: bool = False
    enters_tapped: bool = False
    indestructible: bool = False
    min_copies: int = 0
    max_copies: int = 4

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "LandSpec":
        return cls(
            name=value["name"],
            colors=tuple(value.get("colors", ())),
            artifact=bool(value.get("artifact", False)),
            enters_tapped=bool(value.get("enters_tapped", False)),
            indestructible=bool(value.get("indestructible", False)),
            min_copies=int(value.get("min_copies", 0)),
            max_copies=int(value.get("max_copies", 4)),
        )


@dataclass(frozen=True)
class CardSpec:
    name: str
    copies: int = 1
    mana_cost: str = ""
    tags: frozenset[str] = frozenset()
    rules: dict[str, Any] = field(default_factory=dict)
    timing: str = "own_turn"
    earliest_realistic_turn: int = 1
    desired_windows: dict[str, dict[int, float]] = field(default_factory=dict)

    @property
    def is_artifact(self) -> bool:
        return "artifact" in self.tags or bool(self.rules.get("artifact_on_battlefield"))

    @property
    def is_creature(self) -> bool:
        return "creature" in self.tags

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "CardSpec":
        windows = {
            profile: {int(turn): float(weight) for turn, weight in values.items()}
            for profile, values in value.get("desired_windows", {}).items()
        }
        return cls(
            name=value["name"],
            copies=int(value.get("copies", 1)),
            mana_cost=value.get("mana_cost", ""),
            tags=frozenset(value.get("mana_relevant_tags", ())),
            rules=dict(value.get("rules_model", {})),
            timing=value.get("timing", "own_turn"),
            earliest_realistic_turn=int(value.get("earliest_realistic_turn", 1)),
            desired_windows=windows,
        )


@dataclass(frozen=True)
class DeckSpec:
    name: str
    version: str
    maindeck_size: int
    land_count: int
    cards: tuple[CardSpec, ...]
    lands: tuple[LandSpec, ...]
    current_mana_base: tuple[tuple[str, int], ...]
    mechanics_required: tuple[str, ...]
    policy_contract: dict[str, Any]
    raw: dict[str, Any]

    @property
    def nonland_count(self) -> int:
        return sum(card.copies for card in self.cards)

    @property
    def land_by_name(self) -> dict[str, LandSpec]:
        return {land.name: land for land in self.lands}

    @property
    def card_by_name(self) -> dict[str, CardSpec]:
        return {card.name: card for card in self.cards}

    def expanded_nonlands(self) -> list[str]:
        return [card.name for card in self.cards for _ in range(card.copies)]

    def expanded_lands(self, counts: dict[str, int] | None = None) -> list[str]:
        chosen = counts or dict(self.current_mana_base)
        return [name for name, count in chosen.items() for _ in range(count)]

    def validate_integrity(self) -> None:
        if self.nonland_count != 41:
            raise ValueError(f"expected 41 frozen nonlands, found {self.nonland_count}")
        if sum(dict(self.current_mana_base).values()) != self.land_count:
            raise ValueError("current mana base does not match land-count constraint")
        if self.nonland_count + self.land_count != self.maindeck_size:
            raise ValueError("maindeck does not reconcile")
        pool = self.land_by_name
        for name, copies in self.current_mana_base:
            land = pool[name]
            if not land.min_copies <= copies <= land.max_copies:
                raise ValueError(f"{name} violates copy bounds")


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} does not contain a mapping")
    return data


def load_deck(path: str | Path) -> DeckSpec:
    raw = load_yaml(path)
    cards = tuple(CardSpec.from_mapping(value) for value in raw["cards"]["maindeck"])
    lands = tuple(LandSpec.from_mapping(value) for value in raw["candidate_pool"]["lands"])
    base = tuple((value["name"], int(value["copies"])) for value in raw["current_mana_base"])
    spec = DeckSpec(
        name=raw["deck"]["name"],
        version=raw["deck"]["version"],
        maindeck_size=int(raw["deck"]["maindeck_size"]),
        land_count=int(raw["optimization"]["total_land_count"]["value"]),
        cards=cards,
        lands=lands,
        current_mana_base=base,
        mechanics_required=tuple(raw["mechanics_required"]),
        policy_contract=dict(raw["policy_contract"]),
        raw=raw,
    )
    spec.validate_integrity()
    return spec


def canonical_counts(items: Iterable[tuple[str, int]]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(((name, int(count)) for name, count in items), key=lambda pair: pair[0]))

