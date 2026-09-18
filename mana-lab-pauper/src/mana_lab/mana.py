from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Iterable

from .cards import COLORS


@dataclass(frozen=True)
class ManaCost:
    generic: int = 0
    colored: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_rules(cls, rules: dict, artifact_count: int = 0) -> "ManaCost":
        generic = int(rules.get("generic_cost", 0))
        if rules.get("affinity_for_artifacts"):
            generic = max(0, generic - artifact_count)
        colored = {color: int(amount) for color, amount in rules.get("colored_cost", {}).items()}
        return cls(generic=generic, colored=colored)

    @property
    def total(self) -> int:
        return self.generic + sum(self.colored.values())


@dataclass
class ManaPool:
    amounts: dict[str, int] = field(default_factory=lambda: {color: 0 for color in COLORS})

    def copy(self) -> "ManaPool":
        return ManaPool(dict(self.amounts))

    def add(self, color: str, amount: int = 1) -> None:
        if color not in COLORS or amount < 0:
            raise ValueError("invalid mana addition")
        self.amounts[color] = self.amounts.get(color, 0) + amount

    def clear(self) -> None:
        for color in COLORS:
            self.amounts[color] = 0

    @property
    def total(self) -> int:
        return sum(self.amounts.values())

    def can_pay(self, cost: ManaCost) -> bool:
        work = self.copy()
        for color, needed in cost.colored.items():
            if work.amounts.get(color, 0) < needed:
                return False
            work.amounts[color] -= needed
        return work.total >= cost.generic

    def pay(self, cost: ManaCost) -> dict[str, int]:
        if not self.can_pay(cost):
            raise ValueError("cost cannot be paid")
        spent = {color: 0 for color in COLORS}
        for color in sorted(cost.colored):
            needed = cost.colored[color]
            self.amounts[color] -= needed
            spent[color] += needed
        remaining = cost.generic
        for color in ("C", "G", "R", "B", "U", "W"):
            use = min(self.amounts[color], remaining)
            self.amounts[color] -= use
            spent[color] += use
            remaining -= use
        assert remaining == 0
        return {color: amount for color, amount in spent.items() if amount}


def affinity_cost(generic: int, colored: dict[str, int], artifact_count: int) -> ManaCost:
    return ManaCost(max(0, generic - artifact_count), dict(colored))


def sources_can_pay(source_colors: Iterable[tuple[str, ...]], cost: ManaCost) -> bool:
    """Exact small-source assignment without assuming a source makes two mana."""
    sources = list(source_colors)
    if len(sources) < cost.total:
        return False
    required = [color for color, count in cost.colored.items() for _ in range(count)]

    def assign(index: int, unused: tuple[int, ...]) -> bool:
        if index == len(required):
            return len(unused) >= cost.generic
        color = required[index]
        return any(
            color in sources[pos] and assign(index + 1, tuple(i for i in unused if i != pos))
            for pos in unused
        )

    return assign(0, tuple(range(len(sources))))


def source_assignments(source_colors: Iterable[tuple[str, ...]], cost: ManaCost) -> list[tuple[int, ...]]:
    """Return source-index subsets capable of paying a cost; useful for auditable planning."""
    sources = list(source_colors)
    results: list[tuple[int, ...]] = []
    for size in range(cost.total, len(sources) + 1):
        for indices in combinations(range(len(sources)), size):
            if sources_can_pay([sources[i] for i in indices], cost):
                results.append(indices)
        if results:
            break
    return results

