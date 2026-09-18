from __future__ import annotations

import copy
from dataclasses import dataclass
from itertools import product
from typing import Iterable

from .cards import COLORS, DeckSpec, LandSpec
from .effects import ScryDecision
from .mana import ManaCost
from .payment import can_pay_from_state
from .state import GameState, PhysicalCard


BASELINE_LAND_POLICY = "baseline_hand_demand"
ALTERNATE_LAND_POLICY = "alternate_tempo_untapped"
BASELINE_ACTION_POLICY = "baseline_hand_demand"
ALTERNATE_ACTION_POLICY = "alternate_tempo_untapped"
BASELINE_SCRY_POLICY = "boulder_scry_baseline"
ALTERNATE_SCRY_POLICY = "boulder_scry_alternate"
BASELINE_RESERVE_POLICY = "reserve_one_reply"
ALTERNATE_RESERVE_POLICY = "tap_out_development"
BASELINE_INFORMATION_POLICY = "baseline_information_value"
CONSERVATIVE_INFORMATION_POLICY = "conservative_information_value"

INTERACTION_COSTS = {
    "Galvanic Blast": ManaCost(colored={"R": 1}),
    "Dispatch": ManaCost(colored={"W": 1}),
    "Reckoner's Bargain": ManaCost(generic=1, colored={"B": 1}),
}


@dataclass(frozen=True)
class VisibleState:
    hand: tuple[tuple[str, str], ...]
    battlefield: tuple[tuple[str, str, bool], ...]
    graveyard: tuple[str, ...]
    turn: int
    phase: str
    land_drop_available: bool

    @classmethod
    def from_state(cls, state: GameState) -> "VisibleState":
        return cls(
            hand=tuple(sorted((card.name, card.uid) for card in state.hand)),
            battlefield=tuple(sorted((p.card.name, p.card.uid, p.tapped) for p in state.battlefield)),
            graveyard=tuple(sorted(card.name for card in state.graveyard)),
            turn=state.turn,
            phase=state.phase,
            land_drop_available=state.land_drop_available,
        )


def _demanded_colors(hand: Iterable[PhysicalCard], deck: DeckSpec, horizon: int) -> set[str]:
    demanded: set[str] = set()
    for physical in hand:
        card = deck.card_by_name.get(physical.name)
        if card and card.earliest_realistic_turn <= horizon:
            demanded.update(card.rules.get("colored_cost", {}).keys())
    return demanded


def _future_source_profiles(state: GameState, deck: DeckSpec, candidate: LandSpec) -> list[tuple[str, ...]]:
    profiles = [tuple(p.land_spec.colors) for p in state.battlefield if p.is_land and p.land_spec]
    profiles.append(tuple(candidate.colors))
    return profiles


def _profiles_can_pay(profiles: list[tuple[str, ...]], cost: ManaCost, boulders: int) -> bool:
    if len(profiles) < cost.total:
        return False
    choices = []
    for colors in profiles:
        choices.append([(color, False) for color in colors] + [(color, True) for color in "WUBRG"])
    for outputs in product(*choices):
        if sum(filtered for _, filtered in outputs) > boulders:
            continue
        pool = {color: 0 for color in COLORS}
        for color, _ in outputs:
            pool[color] += 1
        valid = True
        for color, count in cost.colored.items():
            if pool[color] < count:
                valid = False
                break
            pool[color] -= count
        if valid and sum(pool.values()) >= cost.generic:
            return True
    return False


def _future_coverage(state: GameState, deck: DeckSpec, land: LandSpec) -> tuple[int, int]:
    demanded = _demanded_colors(state.hand, deck, state.turn + 1)
    profiles = _future_source_profiles(state, deck, land)
    direct = len(demanded.intersection({color for source in profiles for color in source}))
    boulders = sum(p.card.name == "Giant's Boulder" for p in state.battlefield)
    joint = 0
    for physical in state.hand:
        spec = deck.card_by_name.get(physical.name)
        if not spec or spec.earliest_realistic_turn > state.turn + 1:
            continue
        cost = ManaCost.from_rules(spec.rules, state.artifact_count() + int(land.artifact))
        joint += int(_profiles_can_pay(profiles, cost, boulders))
    return direct, joint


def visible_future_coverage(state: GameState, deck: DeckSpec) -> tuple[int, int]:
    """Visible next-turn color and joint-cost coverage, including tapped lands.

    This deliberately uses no library information.  It values the mana profile
    left by a complete planner sequence, so production land actions and the
    compatibility ``choose_land`` helper share the same semantics.
    """
    demanded = _demanded_colors(state.hand, deck, state.turn + 1)
    profiles = [tuple(p.land_spec.colors) for p in state.battlefield if p.is_land and p.land_spec]
    direct = len(demanded.intersection({color for source in profiles for color in source}))
    boulders = sum(p.card.name == "Giant's Boulder" for p in state.battlefield)
    joint = 0
    for physical in state.hand:
        spec = deck.card_by_name.get(physical.name)
        if not spec or spec.earliest_realistic_turn > state.turn + 1:
            continue
        cost = ManaCost.from_rules(spec.rules, state.artifact_count())
        joint += int(_profiles_can_pay(profiles, cost, boulders))
    return direct, joint


def choose_land(state: GameState, deck: DeckSpec, policy_name: str) -> PhysicalCard | None:
    """Evaluate land plays using reachable visible-state action sequences.

    This compatibility entry point uses the same sequence evaluator as the
    unified planner.  Production play treats a land as an ordinary planner
    action rather than calling this function before spell search.
    """
    legal = [card for card in state.hand if card.name in deck.land_by_name]
    if not legal or not state.land_drop_available:
        return None
    from .simulator import evaluate_post_land_state

    scored: list[tuple[tuple, str, str, PhysicalCard, dict]] = []
    for card in legal:
        branch = copy.deepcopy(state)
        branch_card = next(item for item in branch.hand if item.uid == card.uid)
        spec = deck.land_by_name[card.name]
        branch.play_land(branch_card, spec)
        sequence = evaluate_post_land_state(branch, deck)
        coverage, joint = _future_coverage(state, deck, spec)
        current_usable = len(branch.untapped_lands())
        bridge_slack = int(spec.enters_tapped and sequence["spell_executions"] == 0 and sequence["reserve_preserved"])
        # In a true slack window raw untapped capacity is not treated as
        # realized functionality.  This is what permits future-color Bridges
        # to win when no visible same-turn action or reply consumes the mana.
        effective_current_usable = len(state.untapped_lands()) if bridge_slack else current_usable
        if policy_name == BASELINE_LAND_POLICY:
            score = (sequence["due_executions"], int(sequence["reserve_preserved"]), effective_current_usable, joint, coverage, bridge_slack)
        elif policy_name == ALTERNATE_LAND_POLICY:
            score = (current_usable, sequence["spell_executions"], joint, coverage, int(sequence["reserve_preserved"]), -int(spec.enters_tapped))
        else:
            raise ValueError(f"unknown land policy {policy_name}")
        details = {
            "executable_due_actions": sequence["due_executions"],
            "executable_spell_actions": sequence["spell_executions"],
            "reserve_preserved": sequence["reserve_preserved"],
            "current_usable": current_usable,
            "effective_current_usable": effective_current_usable,
            "future_color_coverage": coverage,
            "future_joint_castability": joint,
            "bridge_slack": bridge_slack,
        }
        scored.append((score, card.name, card.uid, card, details))
    best_score = max(item[0] for item in scored)
    selected = min((item for item in scored if item[0] == best_score), key=lambda item: (item[1], item[2]))
    state.log("policy_land_choice", policy=policy_name, selected=selected[3].name, score=list(best_score), rationale=selected[4])
    return selected[3]


@dataclass(frozen=True)
class ActionOption:
    key: str
    due_executions: int
    artifact_count: int
    cards_drawn: int
    reserve_preserved: bool
    untapped_resources: int
    land_loss: int
    hard_deadline_executions: int = 0
    spell_executions: int = 0
    raw_spell_casts: int = 0
    future_color_coverage: int = 0
    future_joint_castability: int = 0
    information_value: int = 0
    lost_colors: int = 0
    lost_untapped_sources: int = 0
    artifact_loss: int = 0


def choose_action(
    options: Iterable[ActionOption],
    policy_name: str,
    *,
    reserve_policy_name: str = BASELINE_RESERVE_POLICY,
) -> ActionOption | None:
    choices = list(options)
    if not choices:
        return None
    if reserve_policy_name == BASELINE_RESERVE_POLICY:
        reserve_score = lambda action: int(action.reserve_preserved)
    elif reserve_policy_name == ALTERNATE_RESERVE_POLICY:
        # A true tap-out robustness policy never gives an action credit merely
        # for retaining an opponent-window reply.  Availability is still
        # measured at the opponent window; it is simply not optimized here.
        reserve_score = lambda action: 0
    else:
        raise ValueError(f"unknown reserve policy {reserve_policy_name}")

    if policy_name == BASELINE_ACTION_POLICY:
        # Authoritative Run E precedence:
        # hard deadline > payable reply > battlefield-land preservation >
        # functional due execution > artifact/resource preservation > visible
        # future mana coverage > current usable mana > other functional spells
        # > causal information value > raw casts.  Card names never enter this
        # strategic score.
        score = lambda action: (
            action.hard_deadline_executions,
            reserve_score(action),
            -action.land_loss,
            -action.lost_untapped_sources,
            -action.lost_colors,
            action.due_executions,
            -action.artifact_loss,
            action.artifact_count,
            action.future_joint_castability,
            action.future_color_coverage,
            action.untapped_resources,
            action.spell_executions,
            action.information_value,
            action.raw_spell_casts,
        )
    elif policy_name == ALTERNATE_ACTION_POLICY:
        # Tempo policy differs deliberately: after deadlines and reserve, it
        # maximizes (never minimizes) immediately untapped resources.
        score = lambda action: (
            action.hard_deadline_executions,
            reserve_score(action),
            action.untapped_resources,
            -action.land_loss,
            action.due_executions,
            action.spell_executions,
            action.artifact_count,
            action.future_joint_castability,
            action.future_color_coverage,
            action.information_value,
            action.raw_spell_casts,
        )
    else:
        raise ValueError(f"unknown action policy {policy_name}")
    best = max(score(action) for action in choices)
    return sorted((action for action in choices if score(action) == best), key=lambda action: action.key)[0]


def _visible_land_specs(visible: VisibleState, deck: DeckSpec) -> tuple[list[LandSpec], list[LandSpec]]:
    battlefield = [deck.land_by_name[name] for name, _, _ in visible.battlefield if name in deck.land_by_name]
    held = [deck.land_by_name[name] for name, _ in visible.hand if name in deck.land_by_name]
    return battlefield, held


def _scry_score(card: PhysicalCard, visible: VisibleState, deck: DeckSpec, *, land_first: bool) -> tuple[int, int, str]:
    land = deck.land_by_name.get(card.name)
    battlefield_lands, held_lands = _visible_land_specs(visible, deck)
    needs_land = len(battlefield_lands) + len(held_lands) <= visible.turn
    boulders = sum(name == "Giant's Boulder" for name, _, _ in visible.battlefield)
    due_specs = [
        deck.card_by_name[name]
        for name, _ in visible.hand
        if name in deck.card_by_name and deck.card_by_name[name].earliest_realistic_turn <= visible.turn + 1
    ]
    existing_profiles = [tuple(spec.colors) for spec in battlefield_lands + held_lands]
    artifact_count = sum(
        name in deck.land_by_name
        or (name in deck.card_by_name and deck.card_by_name[name].is_artifact)
        or name == "Blood"
        for name, _, _ in visible.battlefield
    )
    if land:
        before = sum(_profiles_can_pay(existing_profiles, ManaCost.from_rules(spec.rules, artifact_count), boulders) for spec in due_specs)
        after = sum(
            _profiles_can_pay(
                existing_profiles + [tuple(land.colors)],
                ManaCost.from_rules(spec.rules, artifact_count + int(land.artifact)),
                boulders,
            )
            for spec in due_specs
        )
        unlocks_due = after > before
        if unlocks_due:
            return (500, after - before, card.name)
        if needs_land:
            return (450 if land_first else 425, len(land.colors), card.name)
        demanded = {color for spec in due_specs for color in spec.rules.get("colored_cost", {})}
        adds_color = bool(demanded.intersection(land.colors) - {color for profile in existing_profiles for color in profile})
        if adds_color:
            return (400, len(land.colors), card.name)
        return (250 if land_first else 150, len(land.colors), card.name)
    spec = deck.card_by_name.get(card.name)
    if spec and spec.earliest_realistic_turn <= visible.turn + 1:
        projected = _profiles_can_pay(existing_profiles, ManaCost.from_rules(spec.rules, artifact_count), boulders)
        return ((425 if projected else 225) if not land_first else (350 if projected else 200), int(projected), card.name)
    if spec and ("draw" in spec.tags or "artifact" in spec.tags):
        return (175, 0, card.name)
    return (0, 0, card.name)


def make_scry_policy(deck: DeckSpec, policy_name: str):
    if policy_name not in {BASELINE_SCRY_POLICY, ALTERNATE_SCRY_POLICY}:
        raise ValueError(f"unknown scry policy {policy_name}")
    land_first = policy_name == ALTERNATE_SCRY_POLICY

    def policy(revealed: tuple[PhysicalCard, ...], visible: VisibleState) -> ScryDecision:
        scores = [_scry_score(card, visible, deck, land_first=land_first) for card in revealed]
        kept = tuple(index for index, score in enumerate(scores) if score[0] > 0)
        ordered = tuple(sorted(kept, key=lambda i: (-scores[i][0], -scores[i][1], scores[i][2], revealed[i].uid)))
        return ScryDecision(keep_indices=kept, keep_order=ordered)

    policy.__name__ = policy_name
    return policy


def opponent_window_status(state: GameState, deck: DeckSpec | None = None, profile: str = "baseline_practical") -> dict[str, dict[str, object]]:
    names = {card.name for card in state.hand}
    has_sacrifice = any(p.is_artifact or p.is_creature for p in state.battlefield)
    result: dict[str, dict[str, object]] = {}
    for name, cost in INTERACTION_COSTS.items():
        in_hand = name in names
        payable = in_hand and can_pay_from_state(state, cost) and (name != "Reckoner's Bargain" or has_sacrifice)
        demand = in_hand
        if deck is not None and name in deck.card_by_name:
            windows = deck.card_by_name[name].desired_windows.get(profile, {})
            demand = in_hand and windows.get(state.turn, 0.0) > 0
        result[name] = {"in_hand": in_hand, "payable": payable, "demand": demand}
    return result


def opponent_options(state: GameState) -> dict[str, bool]:
    return {name: bool(status["payable"]) for name, status in opponent_window_status(state).items()}


def policy_source_has_candidate_branch() -> bool:
    import inspect

    source = inspect.getsource(choose_land) + inspect.getsource(choose_action)
    forbidden = ("C0", "C1", "HISTORICAL_C1", "candidate_label", "candidate_name")
    return any(token in source for token in forbidden)
