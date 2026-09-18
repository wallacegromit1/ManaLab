from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product

from .cards import COLORS
from .mana import ManaCost
from .state import GameState, Permanent


@dataclass(frozen=True)
class SourceUse:
    """One physical land used by a payment plan.

    When ``via_boulder`` is present the land's native mana is consumed by that
    Boulder and replaced by ``produced``.  The net-zero virtual-source model
    avoids execution-order mana creation.
    """

    permanent: Permanent
    produced: str
    via_boulder: Permanent | None = None
    input_color: str | None = None


@dataclass(frozen=True)
class PaymentPlan:
    uses: tuple[SourceUse, ...]
    cost: ManaCost
    spent: tuple[tuple[str, int], ...] = ()
    remaining_pool: tuple[tuple[str, int], ...] = ()

    @property
    def canonical_key(self) -> tuple:
        return (
            tuple(sorted((u.permanent.card.uid, u.produced, "" if u.via_boulder is None else u.via_boulder.card.uid) for u in self.uses)),
            self.remaining_pool,
        )


def _pool_payments(amounts: dict[str, int], cost: ManaCost) -> list[tuple[dict[str, int], dict[str, int]]]:
    """Enumerate generic-payment choices because remaining colors matter."""
    after_colored = {color: int(amounts.get(color, 0)) for color in COLORS}
    colored_spent = {color: 0 for color in COLORS}
    for color, needed in cost.colored.items():
        if after_colored.get(color, 0) < needed:
            return []
        after_colored[color] -= needed
        colored_spent[color] += needed
    if sum(after_colored.values()) < cost.generic:
        return []

    results: dict[tuple[tuple[str, int], ...], tuple[dict[str, int], dict[str, int]]] = {}

    def allocate(index: int, remaining: int, work: dict[str, int], generic_spent: dict[str, int]) -> None:
        if index == len(COLORS):
            if remaining:
                return
            left = tuple((color, work[color]) for color in COLORS)
            spent = {
                color: colored_spent[color] + generic_spent.get(color, 0)
                for color in COLORS
                if colored_spent[color] + generic_spent.get(color, 0)
            }
            results[left] = (spent, dict(work))
            return
        color = COLORS[index]
        for use in range(min(work[color], remaining) + 1):
            work[color] -= use
            if use:
                generic_spent[color] = use
            allocate(index + 1, remaining - use, work, generic_spent)
            generic_spent.pop(color, None)
            work[color] += use

    allocate(0, cost.generic, dict(after_colored), {})
    return list(results.values())


def _post_payment_signature(state: GameState, plan: PaymentPlan) -> tuple:
    tapped = {use.permanent.card.uid for use in plan.uses}
    tapped.update(use.via_boulder.card.uid for use in plan.uses if use.via_boulder is not None)
    permanent_state = tuple(sorted((p.card.uid, p.card.name, p.tapped or p.card.uid in tapped) for p in state.battlefield))
    return permanent_state, plan.remaining_pool


def enumerate_payment_plans(state: GameState, cost: ManaCost, *, allow_boulder: bool = True) -> list[PaymentPlan]:
    """Return every strategically distinct legal post-payment resource state."""
    lands = sorted(state.untapped_lands(), key=lambda p: (p.card.name, p.card.uid))
    boulders = sorted(
        (p for p in state.battlefield if p.card.name == "Giant's Boulder" and not p.tapped),
        key=lambda p: p.card.uid,
    )
    starting_pool = {color: state.mana_pool.amounts.get(color, 0) for color in COLORS}
    plans_by_result: dict[tuple, PaymentPlan] = {}
    for source_count in range(min(len(lands), cost.total) + 1):
        if sum(starting_pool.values()) + source_count < cost.total:
            continue
        for chosen in combinations(lands, source_count):
            options: list[list[tuple[str, Permanent | None, str]]] = []
            for land in chosen:
                native = [(color, None, color) for color in sorted(land.land_spec.colors)]
                # "Any color" is W/U/B/R/G.  Colorless is not a color.
                filtered = [(output, boulder, sorted(land.land_spec.colors)[0]) for boulder in boulders for output in "WUBRG"]
                options.append(native + (filtered if allow_boulder else []))
            for outputs in product(*options):
                used_boulders = [b.card.uid for _, b, _ in outputs if b is not None]
                if len(used_boulders) != len(set(used_boulders)):
                    continue
                pool = dict(starting_pool)
                uses: list[SourceUse] = []
                for land, (output, boulder, input_color) in zip(chosen, outputs):
                    pool[output] += 1
                    uses.append(SourceUse(land, output, boulder, input_color))
                for spent, remaining in _pool_payments(pool, cost):
                    plan = PaymentPlan(
                        tuple(uses), cost, tuple(sorted(spent.items())), tuple((color, remaining[color]) for color in COLORS)
                    )
                    signature = _post_payment_signature(state, plan)
                    old = plans_by_result.get(signature)
                    if old is None or plan.canonical_key < old.canonical_key:
                        plans_by_result[signature] = plan
    return sorted(plans_by_result.values(), key=lambda plan: plan.canonical_key)


def find_payment_plan(state: GameState, cost: ManaCost, *, allow_boulder: bool = True) -> PaymentPlan | None:
    """Compatibility helper; strategic search uses ``enumerate_payment_plans``."""
    plans = enumerate_payment_plans(state, cost, allow_boulder=allow_boulder)
    return plans[0] if plans else None


def remap_payment_plan(state: GameState, plan: PaymentPlan) -> PaymentPlan:
    by_uid = {p.card.uid: p for p in state.battlefield}
    uses = []
    for use in plan.uses:
        source = by_uid.get(use.permanent.card.uid)
        boulder = None if use.via_boulder is None else by_uid.get(use.via_boulder.card.uid)
        if source is None or (use.via_boulder is not None and boulder is None):
            raise ValueError("payment plan no longer matches battlefield")
        uses.append(SourceUse(source, use.produced, boulder, use.input_color))
    return PaymentPlan(tuple(uses), plan.cost, plan.spent, plan.remaining_pool)


def execute_payment(state: GameState, plan: PaymentPlan) -> dict[str, int]:
    plan = remap_payment_plan(state, plan)
    direct_plan_available = bool(enumerate_payment_plans(state, plan.cost, allow_boulder=False))
    seen_sources: set[str] = set()
    seen_boulders: set[str] = set()
    for use in plan.uses:
        if use.permanent.tapped or use.permanent.card.uid in seen_sources:
            raise ValueError("payment source is not available")
        seen_sources.add(use.permanent.card.uid)
        use.permanent.tapped = True
        if use.via_boulder is None:
            state.log("mana_produced", source=use.permanent.card.name, color=use.produced)
        else:
            if use.via_boulder.tapped or use.via_boulder.card.uid in seen_boulders:
                raise ValueError("Boulder is not available")
            seen_boulders.add(use.via_boulder.card.uid)
            use.via_boulder.tapped = True
            state.log(
                "boulder_filter", source=use.permanent.card.name, boulder_uid=use.via_boulder.card.uid,
                input_color=use.input_color, color=use.produced, net_mana=0, resource_consumed=True,
                boulder_used=True,
                rescue=not direct_plan_available,
                dependency=not direct_plan_available,
                dependency_counterfactual="chosen payment is unavailable at this state without Boulder",
            )
    for color, amount in plan.remaining_pool:
        state.mana_pool.amounts[color] = amount
    spent = dict(plan.spent)
    state.log(
        "payment", generic=plan.cost.generic, colored=dict(plan.cost.colored), spent=spent,
        sources=[u.permanent.card.name for u in plan.uses], source_uids=[u.permanent.card.uid for u in plan.uses],
        filters=sum(u.via_boulder is not None for u in plan.uses), remaining_pool=dict(plan.remaining_pool),
    )
    return spent


def can_pay_from_state(state: GameState, cost: ManaCost, *, allow_boulder: bool = True) -> bool:
    return bool(enumerate_payment_plans(state, cost, allow_boulder=allow_boulder))
