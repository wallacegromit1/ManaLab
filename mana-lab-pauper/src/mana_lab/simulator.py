from __future__ import annotations

import copy
import gzip
import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cards import DeckSpec
from .effects import leave_battlefield, no_auto_draw_for_familiar, resolve_scry
from .mana import ManaCost
from .metrics import GzipEventWriter, SmokeAggregator
from .mulligan import london_mulligan
from .payment import PaymentPlan, enumerate_payment_plans, execute_payment, find_payment_plan, remap_payment_plan
from .policies import (
    ALTERNATE_ACTION_POLICY,
    ALTERNATE_LAND_POLICY,
    ALTERNATE_SCRY_POLICY,
    BASELINE_ACTION_POLICY,
    BASELINE_INFORMATION_POLICY,
    BASELINE_RESERVE_POLICY,
    BASELINE_LAND_POLICY,
    BASELINE_SCRY_POLICY,
    CONSERVATIVE_INFORMATION_POLICY,
    ActionOption,
    choose_action,
    make_scry_policy,
    opponent_options,
    opponent_window_status,
    visible_future_coverage,
)
from .state import GameState, Permanent, PhysicalCard, make_card


INTERACTION_CARDS = {"Dispatch", "Galvanic Blast"}
INFORMATION_CARDS = {"Thoughtcast", "Baleful Strix", "Cryogen Relic", "Giant's Boulder", "Reckoner's Bargain"}

INFORMATION_VALUE_PROFILES = {
    BASELINE_INFORMATION_POLICY: {
        "draw_1": 100,
        "draw_2": 190,
        "scry_2": 80,
    },
    CONSERVATIVE_INFORMATION_POLICY: {
        "draw_1": 35,
        "draw_2": 60,
        "scry_2": 20,
    },
}


def _physical_deck(deck: DeckSpec, land_counts: dict[str, int]) -> list[PhysicalCard]:
    cards: list[PhysicalCard] = []
    index = 0
    for spec in deck.cards:
        for _ in range(spec.copies):
            cards.append(make_card(f"nonland-{index}", spec.name, artifact=spec.is_artifact, creature=spec.is_creature))
            index += 1
    for land_name in sorted(land_counts):
        land = deck.land_by_name[land_name]
        for _ in range(land_counts[land_name]):
            cards.append(make_card(f"land-{index}", land_name, artifact=land.artifact, land=True))
            index += 1
    if len(cards) != deck.maindeck_size:
        raise ValueError("physical deck does not match maindeck size")
    return cards


def _permutation(seed: int, size: int) -> list[int]:
    indices = list(range(size))
    random.Random(seed).shuffle(indices)
    return indices


def _shuffled(base: list[PhysicalCard], seed: int) -> list[PhysicalCard]:
    return [base[index] for index in _permutation(seed, len(base))]


def _stable_scenario_seed(base_seed: int, scenario: str, trial: int, attempt: int) -> int:
    digest = hashlib.sha256(f"{scenario}|{trial}|{attempt}".encode()).digest()
    return base_seed + int.from_bytes(digest[:8], "big")


def _source_presence(hand: list[PhysicalCard], deck: DeckSpec, color: str) -> bool:
    return any(card.name in deck.land_by_name and color in deck.land_by_name[card.name].colors for card in hand)


def _joint_ub(hand: list[PhysicalCard], deck: DeckSpec) -> bool:
    return _source_presence(hand, deck, "U") and _source_presence(hand, deck, "B")


def _permanent_signature(permanent: Permanent) -> tuple:
    return (
        permanent.card.name,
        permanent.tapped,
        permanent.is_land,
        () if permanent.land_spec is None else tuple(permanent.land_spec.colors),
        permanent.token,
        tuple(sorted((str(key), str(value)) for key, value in permanent.metadata.items())),
    )


def _visible_search_key(state: GameState, due: int, hard: int, spells: int, depth: int, path_kinds: tuple[str, ...]) -> tuple:
    return (
        tuple(sorted((card.name, card.uid) for card in state.hand)),
        tuple(sorted((_permanent_signature(p), p.card.uid) for p in state.battlefield)),
        tuple(sorted(card.name for card in state.graveyard)),
        tuple(sorted(state.mana_pool.amounts.items())),
        state.land_drop_available,
        state.turn,
        state.phase,
        tuple((item.label, item.kind) for item in state.stack),
        tuple(
            (event.get("kind"), event.get("count"), event.get("reason"))
            for event in state.events
            if event["event"] == "information_node"
        ),
        due,
        hard,
        spells,
        depth,
        path_kinds,
    )


@dataclass(frozen=True)
class PlannerAction:
    kind: str
    label: str
    key: tuple
    card_uid: str | None = None
    payment: PaymentPlan | None = None
    target_uid: str | None = None
    sacrifice_uid: str | None = None
    discard_uid: str | None = None
    reveals_information: bool = False
    due: bool = False
    hard_deadline: bool = False


def _is_due(deck: DeckSpec, card_name: str, turn: int) -> bool:
    spec = deck.card_by_name[card_name]
    if spec.earliest_realistic_turn > turn:
        return False
    return any(turn in windows for windows in spec.desired_windows.values()) or turn >= spec.earliest_realistic_turn


def _is_hard_deadline(deck: DeckSpec, card_name: str, turn: int) -> bool:
    spec = deck.card_by_name[card_name]
    deadlines = [max(windows) for windows in spec.desired_windows.values() if windows]
    return bool(deadlines) and min(deadlines) <= turn


def _target_variants(permanents: list[Permanent]) -> list[Permanent]:
    unique: dict[tuple, Permanent] = {}
    for permanent in sorted(permanents, key=lambda p: (p.card.name, p.card.uid)):
        signature = _permanent_signature(permanent)
        unique.setdefault(signature, permanent)
    return list(unique.values())


def generate_legal_actions(state: GameState, deck: DeckSpec, *, include_land_actions: bool = True) -> list[PlannerAction]:
    actions: list[PlannerAction] = []
    if include_land_actions and state.land_drop_available and state.phase in {"main", "main1", "main2"}:
        by_name: dict[str, PhysicalCard] = {}
        for card in sorted(state.hand, key=lambda c: (c.name, c.uid)):
            if card.name in deck.land_by_name:
                by_name.setdefault(card.name, card)
        for name, card in sorted(by_name.items()):
            actions.append(PlannerAction("land", f"Play {name}", ("land", name), card_uid=card.uid))

    # Blood has no opponent-dependent target, so its activation is a real
    # production planner option.  Hidden draw identity remains behind the same
    # causal information boundary as spell draw effects.
    bloods = _target_variants([
        permanent for permanent in state.battlefield
        if permanent.card.name == "Blood" and not permanent.tapped
    ])
    discard_by_name: dict[str, PhysicalCard] = {}
    for discard in sorted(state.hand, key=lambda c: (c.name, c.uid)):
        discard_by_name.setdefault(discard.name, discard)
    blood_plans = enumerate_payment_plans(state, ManaCost(generic=1))
    for blood_permanent in bloods:
        for discard in discard_by_name.values():
            for plan in blood_plans:
                actions.append(PlannerAction(
                    "blood_activation", "Activate Blood",
                    ("activate", "Blood", plan.canonical_key, "discard", discard.name),
                    payment=plan, target_uid=blood_permanent.card.uid,
                    discard_uid=discard.uid, reveals_information=True,
                ))

    by_name: dict[str, PhysicalCard] = {}
    for card in sorted(state.hand, key=lambda c: (c.name, c.uid)):
        if card.name in deck.card_by_name and card.name not in INTERACTION_CARDS:
            by_name.setdefault(card.name, card)
    for name, card in sorted(by_name.items()):
        spec = deck.card_by_name[name]
        cost = ManaCost.from_rules(spec.rules, state.artifact_count())
        plans = enumerate_payment_plans(state, cost)
        for plan in plans:
            payment_key = plan.canonical_key
            if name == "Reckoner's Bargain":
                sacrifices = _target_variants([p for p in state.battlefield if p.is_artifact or p.is_creature])
                for sacrifice in sacrifices:
                    actions.append(
                        PlannerAction(
                            "spell", name, ("spell", name, payment_key, "sac", _permanent_signature(sacrifice)),
                            card.uid, plan, sacrifice_uid=sacrifice.card.uid, reveals_information=True,
                            due=_is_due(deck, name, state.turn), hard_deadline=_is_hard_deadline(deck, name, state.turn),
                        )
                    )
                continue
            if name == "Glint Hawk":
                targets: list[Permanent | None] = [None] + _target_variants([p for p in state.battlefield if p.is_artifact])
                for target in targets:
                    target_key = ("none",) if target is None else ("target", _permanent_signature(target))
                    actions.append(
                        PlannerAction(
                            "spell", name, ("spell", name, payment_key, "return", target_key), card.uid, plan,
                            target_uid=None if target is None else target.card.uid,
                            reveals_information=target is not None and target.card.name == "Cryogen Relic",
                            due=_is_due(deck, name, state.turn), hard_deadline=_is_hard_deadline(deck, name, state.turn),
                        )
                    )
                continue
            actions.append(
                PlannerAction(
                    "spell", name, ("spell", name, payment_key), card.uid, plan,
                    reveals_information=name in INFORMATION_CARDS,
                    due=_is_due(deck, name, state.turn), hard_deadline=_is_hard_deadline(deck, name, state.turn),
                )
            )
    return sorted(actions, key=lambda action: action.key)


def _resolve_or_defer_draw(state: GameState, count: int, reason: str, reveal_information: bool) -> None:
    if reveal_information:
        state.draw(count, reason=reason)
    else:
        state.log("information_node", kind="draw", count=count, reason=reason)


def _information_value(events: list[dict[str, Any]], policy_name: str) -> int:
    if policy_name not in INFORMATION_VALUE_PROFILES:
        raise ValueError(f"unknown information policy {policy_name}")
    profile = INFORMATION_VALUE_PROFILES[policy_name]
    value = 0
    for event in events:
        if event["event"] != "information_node":
            continue
        count = int(event.get("count", 0))
        if event.get("kind") == "scry":
            value += int(profile.get(f"scry_{count}", profile["scry_2"] * count / 2))
        else:
            value += int(profile.get(f"draw_{count}", profile["draw_1"] * count))
    return value


def _resolve_simulator_stack(
    state: GameState,
    *,
    reveal_information: bool,
    stop_size: int = 0,
) -> None:
    """Resolve newly-created spell/trigger objects without deleting peers.

    Information-producing objects become causal information nodes during
    planning.  Known visible actions may continue afterward; hidden card
    identities are not inspected until execution calls this with
    ``reveal_information=True``.
    """
    while len(state.stack) > stop_size:
        item = state.stack.pop()
        state.log("stack_resolve", label=item.label, kind=item.kind)
        if item.label == "Cryogen Relic leave draw":
            _resolve_or_defer_draw(state, 1, item.label, reveal_information)
        elif item.label == "Nihil Spellbomb optional B draw":
            plan = find_payment_plan(state, ManaCost(colored={"B": 1}))
            state.log(
                "nihil_draw_opportunity",
                opportunity_id=f"nihil|{state.turn}|{state._event_counter + 1}",
                payable=plan is not None,
                event_role="option_opportunity",
            )
            if plan is None:
                state.log("nihil_draw_declined", reason="black_mana_unavailable")
            else:
                execute_payment(state, plan)
                _resolve_or_defer_draw(state, 1, "Nihil Spellbomb", reveal_information)
                state.log("nihil_draw_paid", event_role="option_execution")
        elif item.label == "Reckoner's Bargain":
            _resolve_or_defer_draw(state, 2, item.label, reveal_information)
        else:
            item.resolve(state)


def cast_card(
    state: GameState,
    deck: DeckSpec,
    physical: PhysicalCard,
    *,
    scry_policy_name: str = BASELINE_SCRY_POLICY,
    hawk_return: Permanent | None = None,
    bargain_sacrifice: Permanent | None = None,
    payment_plan: PaymentPlan | None = None,
    reveal_information: bool = True,
) -> None:
    if physical not in state.hand or physical.name not in deck.card_by_name:
        raise ValueError("card is not castable from hand")
    spec = deck.card_by_name[physical.name]
    if physical.name in INTERACTION_CARDS:
        raise ValueError("interaction requires a target fixture")
    cost = ManaCost.from_rules(spec.rules, state.artifact_count())
    plan = payment_plan
    if plan is None and physical.name == "Reckoner's Bargain" and bargain_sacrifice is not None and bargain_sacrifice.card.name == "Nihil Spellbomb":
        plans = enumerate_payment_plans(state, cost)
        preserving: list[PaymentPlan] = []
        for candidate in plans:
            probe = copy.deepcopy(state)
            execute_payment(probe, remap_payment_plan(probe, candidate))
            if find_payment_plan(probe, ManaCost(colored={"B": 1})) is not None:
                preserving.append(candidate)
        plan = min(preserving or plans, key=lambda item: item.canonical_key) if plans else None
    plan = plan or find_payment_plan(state, cost)
    if plan is None:
        raise ValueError("mana cost cannot be paid")
    direct_plan_exists = find_payment_plan(state, cost, allow_boulder=False) is not None
    uses_boulder = any(use.via_boulder is not None for use in plan.uses)
    filtered_colors = [use.produced for use in plan.uses if use.via_boulder is not None]
    execute_payment(state, remap_payment_plan(state, plan))
    state.hand.remove(physical)
    related_opportunities = [
        event["opportunity_id"]
        for event in state.events
        if event["event"] == "spell_window" and event.get("uid") == physical.uid
    ]
    state.log(
        "spell_cast", card=physical.name, uid=physical.uid, generic_cost=cost.generic,
        colored_cost=dict(cost.colored), artifact_count_before=state.artifact_count(),
        affinity_reduction=(int(spec.rules.get("generic_cost", 0)) - cost.generic) if spec.rules.get("affinity_for_artifacts") else 0,
        related_opportunity_ids=related_opportunities, event_role="raw_cast",
    )
    if uses_boulder:
        state.log(
            "boulder_usage", card=physical.name, activation_count=len(filtered_colors), filtered_colors=filtered_colors,
            boulder_used=True, rescue=not direct_plan_exists, dependency=not direct_plan_exists,
            dependency_counterfactual="chosen action is not payable at this state without Boulder",
            tap_resource_consumption=len(filtered_colors),
        )

    if physical.name == "Thoughtcast":
        state.graveyard.append(physical)
        _resolve_or_defer_draw(state, 2, "Thoughtcast", reveal_information)
        state.log(
            "spell_resolution", card=physical.name, uid=physical.uid, mandatory_completed=True,
            permanent_retained=False, functional=True, event_role="execution_outcome",
        )
        return
    if physical.name == "Reckoner's Bargain":
        if bargain_sacrifice is None or bargain_sacrifice not in state.battlefield or not (bargain_sacrifice.is_artifact or bargain_sacrifice.is_creature):
            raise ValueError("Bargain requires a legal sacrifice")
        before_artifacts = state.artifact_count()
        before_metalcraft = state.metalcraft()
        sacrifice_name = bargain_sacrifice.card.name
        sacrifice_uid = bargain_sacrifice.card.uid
        sacrifice_type = "land" if bargain_sacrifice.is_land else ("artifact" if bargain_sacrifice.is_artifact else "creature")
        untapped_lost = int(bargain_sacrifice.is_land and not bargain_sacrifice.tapped)
        colors_lost = sorted(bargain_sacrifice.land_spec.colors) if bargain_sacrifice.is_land and bargain_sacrifice.land_spec else []
        stack_size = len(state.stack)
        leave_battlefield(state, bargain_sacrifice, "graveyard", reason="Reckoner's Bargain additional cost")
        generated = state.stack[stack_size:]
        del state.stack[stack_size:]
        # The spell is below all triggers created while paying its additional
        # cost.  Existing unrelated stack objects are retained untouched.
        from .state import StackItem
        state.push(StackItem("Reckoner's Bargain", lambda game: None, kind="spell"))
        for trigger in generated:
            state.push(trigger)
        state.log(
            "bargain_cast", sacrifice=sacrifice_name, sacrifice_uid=sacrifice_uid, sacrifice_type=sacrifice_type,
            artifact_count_before=before_artifacts, artifact_count_after=state.artifact_count(),
            metalcraft_before=before_metalcraft, metalcraft_after=state.metalcraft(), payment_before_draw=True,
            battlefield_land_loss=int(sacrifice_type == "land"), colors_lost=colors_lost,
            untapped_source_loss=untapped_lost,
        )
        _resolve_simulator_stack(state, reveal_information=reveal_information, stop_size=stack_size)
        state.graveyard.append(physical)
        state.log(
            "spell_resolution", card=physical.name, uid=physical.uid, mandatory_completed=True,
            permanent_retained=False, functional=True, event_role="execution_outcome",
        )
        return
    if physical.name == "Glint Hawk":
        hawk = state.add_permanent(physical)
        legal = [p for p in state.battlefield if p.is_artifact and p is not hawk]
        if hawk_return is None or hawk_return not in legal:
            leave_battlefield(state, hawk, "graveyard", reason="Glint Hawk no legal return")
            state.log("glint_hawk_sacrificed")
            state.log(
                "spell_resolution", card=physical.name, uid=physical.uid, mandatory_completed=False,
                permanent_retained=False, functional=False, event_role="execution_outcome",
            )
            return
        returned_name, returned_uid, returned_land, was_tapped = (
            hawk_return.card.name, hawk_return.card.uid, hawk_return.is_land, hawk_return.tapped
        )
        stack_size = len(state.stack)
        leave_battlefield(state, hawk_return, "hand", reason="Glint Hawk return")
        state.log(
            "glint_hawk_return", card=returned_name, uid=returned_uid, returned_land=returned_land,
            was_tapped=was_tapped,
        )
        _resolve_simulator_stack(state, reveal_information=reveal_information, stop_size=stack_size)
        state.log(
            "spell_resolution", card=physical.name, uid=physical.uid, mandatory_completed=True,
            permanent_retained=True, functional=True, event_role="execution_outcome",
        )
        return
    if physical.name == "Giant's Boulder":
        state.add_permanent(physical)
        state.log(
            "boulder_deployed", uid=physical.uid, deployment_opportunity_cost=len(plan.uses),
            resources_consumed=[use.permanent.card.name for use in plan.uses],
        )
        if reveal_information:
            resolve_scry(state, 2, make_scry_policy(deck, scry_policy_name), label="Giant's Boulder scry 2")
        else:
            state.log("information_node", kind="scry", count=2, reason="Giant's Boulder scry 2")
        state.log(
            "spell_resolution", card=physical.name, uid=physical.uid, mandatory_completed=True,
            permanent_retained=True, functional=True, event_role="execution_outcome",
        )
        return
    if spec.is_artifact:
        state.add_permanent(physical)
        if physical.name == "Blood Fountain":
            state.create_token("Blood", artifact=True)
        elif physical.name == "Baleful Strix":
            _resolve_or_defer_draw(state, 1, "Baleful Strix", reveal_information)
        elif physical.name == "Cryogen Relic":
            _resolve_or_defer_draw(state, 1, "Cryogen Relic enter draw", reveal_information)
        elif physical.name == "Refurbished Familiar":
            no_auto_draw_for_familiar(state)
        state.log(
            "spell_resolution", card=physical.name, uid=physical.uid, mandatory_completed=True,
            permanent_retained=True, functional=True, event_role="execution_outcome",
        )
        return
    state.add_permanent(physical)
    state.log(
        "spell_resolution", card=physical.name, uid=physical.uid, mandatory_completed=True,
        permanent_retained=True, functional=True, event_role="execution_outcome",
    )


def _castability_failure(state: GameState, deck: DeckSpec, physical: PhysicalCard) -> tuple[bool, str | None]:
    spec = deck.card_by_name[physical.name]
    cost = ManaCost.from_rules(spec.rules, state.artifact_count())
    if physical.name == "Reckoner's Bargain" and not any(p.is_artifact or p.is_creature for p in state.battlefield):
        return False, "sacrifice_resource"
    if enumerate_payment_plans(state, cost):
        return True, None
    if len(state.untapped_lands()) + state.mana_pool.total < cost.total:
        probe = copy.deepcopy(state)
        for permanent in probe.battlefield:
            if permanent.is_land or permanent.card.name == "Giant's Boulder":
                permanent.tapped = False
        if enumerate_payment_plans(probe, cost):
            return False, "tapped_resource"
        return False, "total_mana"
    return False, "color"


def record_spell_windows(state: GameState, deck: DeckSpec, timing: str) -> None:
    window_sequence = state.next_window_sequence()
    role = {
        "start_own_main": "primary_pre_spend_opportunity",
        "end_own_turn_opponent_window": "primary_post_spend_remainder",
        "before_relevant_action": "diagnostic_pre_action",
        "after_relevant_action": "diagnostic_post_action",
    }.get(timing, "fixture_or_diagnostic")
    for physical in sorted(state.hand, key=lambda card: (card.name, card.uid)):
        spec = deck.card_by_name.get(physical.name)
        if spec is None:
            continue
        castable, reason = _castability_failure(state, deck, physical)
        cost = ManaCost.from_rules(spec.rules, state.artifact_count())
        profiles = spec.desired_windows or {"unprofiled": {state.turn: 1.0}}
        for profile, windows in profiles.items():
            if state.turn not in windows:
                continue
            opportunity_id = (
                f"{state.scenario_id or 'fixture'}|{state.replicate_id if state.replicate_id is not None else 'fixture'}|"
                f"{state.trial_id if state.trial_id is not None else 'fixture'}|{state.turn}|{state.phase}|"
                f"{window_sequence}|{physical.uid}|{profile}"
            )
            state.log(
                "spell_window", timing=timing, card=physical.name, uid=physical.uid, profile=profile,
                weight=windows[state.turn], in_hand=True, due=True, castable=castable, cast=False,
                failure_reason=reason, generic_cost=cost.generic, colored_cost=dict(cost.colored),
                artifact_count=state.artifact_count(), metalcraft=state.metalcraft(),
                window_sequence=window_sequence, card_instance=physical.uid,
                opportunity_id=opportunity_id, event_role=role,
            )


def record_timing_snapshot(state: GameState, deck: DeckSpec, timing: str) -> dict[str, Any]:
    direct_colors = sorted({color for p in state.untapped_lands() for color in p.land_spec.colors})
    usable = len(state.untapped_lands()) + state.mana_pool.total
    boulder_ready = any(p.card.name == "Giant's Boulder" and not p.tapped for p in state.battlefield)
    filtered = list("WUBRG") if boulder_ready and state.untapped_lands() else []
    snapshot = {
        "timing": timing,
        "direct_colors": direct_colors,
        "joint_UB": bool(find_payment_plan(state, ManaCost(colored={"U": 1, "B": 1}))),
        "usable_untapped_mana": usable,
        "available_filtered_colors": filtered,
        "unavailable_tapped_mana": sum(p.is_land and p.tapped for p in state.battlefield),
        "artifact_count": state.artifact_count(),
        "metalcraft": state.metalcraft(),
        "land_drop_available": state.land_drop_available,
    }
    state.log(
        "state_snapshot", **snapshot,
        event_role=("primary_pre_spend_opportunity" if timing == "start_own_main" else "diagnostic_or_remainder"),
    )
    record_spell_windows(state, deck, timing)
    return snapshot


def _due_castable_count(state: GameState, deck: DeckSpec) -> int:
    return sum(
        _is_due(deck, card.name, state.turn) and _castability_failure(state, deck, card)[0]
        for card in state.hand
        if card.name in deck.card_by_name and card.name not in INTERACTION_CARDS
    )


def apply_planner_action(
    state: GameState,
    deck: DeckSpec,
    action: PlannerAction,
    *,
    scry_policy_name: str,
    reveal_information: bool,
) -> None:
    if action.kind == "land":
        card = next(card for card in state.hand if card.uid == action.card_uid)
        permanent = state.play_land(card, deck.land_by_name[card.name])
        blocked = False
        if permanent.tapped:
            actual = _due_castable_count(state, deck)
            probe = copy.deepcopy(state)
            next(p for p in probe.battlefield if p.card.uid == permanent.card.uid).tapped = False
            blocked = _due_castable_count(probe, deck) > actual
        state.log("etb_tempo", card=card.name, entered_tapped=permanent.tapped, blocked_action=blocked, slack_window=not blocked)
        return

    if action.kind == "blood_activation":
        blood_permanent = next(
            (p for p in state.battlefield if p.card.uid == action.target_uid and p.card.name == "Blood"),
            None,
        )
        discard = next((card for card in state.hand if card.uid == action.discard_uid), None)
        if blood_permanent is None or blood_permanent.tapped or discard is None or action.payment is None:
            raise ValueError("Blood activation resources are no longer available")
        before_artifacts = state.artifact_count()
        before_metalcraft = state.metalcraft()
        execute_payment(state, remap_payment_plan(state, action.payment))
        state.hand.remove(discard)
        state.graveyard.append(discard)
        leave_battlefield(state, blood_permanent, "graveyard", reason="Blood activation")
        _resolve_or_defer_draw(state, 1, "Blood activation", reveal_information)
        state.log(
            "blood_activation", discarded=discard.name, discarded_uid=discard.uid,
            artifact_count_before=before_artifacts, artifact_count_after=state.artifact_count(),
            metalcraft_before=before_metalcraft, metalcraft_after=state.metalcraft(),
            mana_paid=1, event_role="option_execution",
        )
        return

    card = next(card for card in state.hand if card.uid == action.card_uid)
    target = next((p for p in state.battlefield if p.card.uid == action.target_uid), None)
    sacrifice = next((p for p in state.battlefield if p.card.uid == action.sacrifice_uid), None)
    cast_card(
        state, deck, card, scry_policy_name=scry_policy_name, hawk_return=target,
        bargain_sacrifice=sacrifice, payment_plan=action.payment, reveal_information=reveal_information,
    )


@dataclass
class ActionSequenceResult:
    state: GameState
    actions: tuple[str, ...]
    option: ActionOption
    planner_actions: tuple[PlannerAction, ...] = ()


def _functional_outcome(state: GameState, action: PlannerAction) -> bool:
    if action.kind != "spell":
        return False
    return any(
        event["event"] == "spell_resolution"
        and event.get("uid") == action.card_uid
        and bool(event.get("functional"))
        for event in reversed(state.events)
    )


def enumerate_action_sequences(
    state: GameState,
    deck: DeckSpec,
    *,
    scry_policy_name: str,
    max_depth: int = 8,
    include_land_actions: bool = True,
    information_policy_name: str = BASELINE_INFORMATION_POLICY,
) -> list[ActionSequenceResult]:
    """Enumerate causal visible-state sequences through unresolved chance nodes.

    Draw/scry identities remain unknown in planning.  The branch may continue
    with cards and resources already visible before the information action.
    """
    if information_policy_name not in INFORMATION_VALUE_PROFILES:
        raise ValueError(f"unknown information policy {information_policy_name}")
    initial_land_uids = {p.card.uid for p in state.battlefield if p.is_land}
    initial_untapped_land_uids = {p.card.uid for p in state.battlefield if p.is_land and not p.tapped}
    initial_artifact_uids = {p.card.uid for p in state.battlefield if p.is_artifact}
    initial_land_colors = {
        color
        for p in state.battlefield
        if p.is_land and p.land_spec
        for color in p.land_spec.colors
    }
    initial_draws = sum(e["event"] == "draw" for e in state.events)
    initial_event_count = len(state.events)
    results: list[ActionSequenceResult] = []
    visited: set[tuple] = set()

    def record(
        current: GameState,
        labels: tuple[str, ...],
        actions: tuple[PlannerAction, ...],
        due: int,
        hard: int,
        spells: int,
        raw_spells: int,
    ) -> None:
        status = opponent_window_status(current, deck)
        demanded = any(bool(item["demand"]) for item in status.values())
        reserve = not demanded or any(bool(item["demand"]) and bool(item["payable"]) for item in status.values())
        pending_cards = sum(int(e.get("count", 0)) for e in current.events if e["event"] == "information_node" and e.get("kind") == "draw")
        current_land_uids = {p.card.uid for p in current.battlefield if p.is_land}
        current_artifact_uids = {p.card.uid for p in current.battlefield if p.is_artifact}
        current_land_colors = {
            color
            for p in current.battlefield
            if p.is_land and p.land_spec
            for color in p.land_spec.colors
        }
        future_coverage, future_joint = visible_future_coverage(current, deck)
        option = ActionOption(
            key=" > ".join(str(a.key) for a in actions) if actions else "PASS",
            due_executions=due,
            artifact_count=current.artifact_count(),
            cards_drawn=sum(e["event"] == "draw" for e in current.events) - initial_draws + pending_cards,
            reserve_preserved=reserve,
            untapped_resources=len(current.untapped_lands()) + current.mana_pool.total,
            land_loss=len(initial_land_uids - current_land_uids),
            hard_deadline_executions=hard,
            spell_executions=spells,
            raw_spell_casts=raw_spells,
            future_color_coverage=future_coverage,
            future_joint_castability=future_joint,
            information_value=_information_value(current.events[initial_event_count:], information_policy_name),
            lost_colors=len(initial_land_colors - current_land_colors),
            lost_untapped_sources=len(initial_untapped_land_uids - current_land_uids),
            artifact_loss=len(initial_artifact_uids - current_artifact_uids),
        )
        results.append(ActionSequenceResult(copy.deepcopy(current), labels, option, actions))

    def recurse(
        current: GameState,
        labels: tuple[str, ...],
        actions: tuple[PlannerAction, ...],
        due: int,
        hard: int,
        spells: int,
        raw_spells: int,
        depth: int,
    ) -> None:
        # Root identity is strategically relevant: equivalent terminal states
        # reached before vs. after an unresolved information action must both
        # remain available to the root chooser.
        root_path = tuple(str(action.key) for action in actions[:1])
        key = _visible_search_key(current, due, hard, spells, depth, root_path)
        if key in visited:
            return
        visited.add(key)
        record(current, labels, actions, due, hard, spells, raw_spells)
        if depth >= max_depth:
            return
        for action in generate_legal_actions(current, deck, include_land_actions=include_land_actions):
            branch = copy.deepcopy(current)
            try:
                apply_planner_action(branch, deck, action, scry_policy_name=scry_policy_name, reveal_information=False)
            except ValueError:
                continue
            next_labels = labels + (action.label,)
            next_actions = actions + (action,)
            functional = _functional_outcome(branch, action)
            next_due = due + int(functional and action.due)
            next_hard = hard + int(functional and action.hard_deadline)
            next_spells = spells + int(functional)
            next_raw_spells = raw_spells + int(action.kind == "spell")
            recurse(
                branch, next_labels, next_actions, next_due, next_hard,
                next_spells, next_raw_spells, depth + 1,
            )

    recurse(copy.deepcopy(state), (), (), 0, 0, 0, 0, 0)
    return results


def _selected_result(
    results: list[ActionSequenceResult],
    policy_name: str,
    reserve_policy_name: str = BASELINE_RESERVE_POLICY,
) -> ActionSequenceResult | None:
    selected_option = choose_action(
        (result.option for result in results), policy_name,
        reserve_policy_name=reserve_policy_name,
    )
    if selected_option is None:
        return None
    return min(
        (result for result in results if result.option == selected_option),
        key=lambda result: tuple(action.key for action in result.planner_actions),
    )


def choose_next_action(
    state: GameState,
    deck: DeckSpec,
    *,
    action_policy_name: str,
    scry_policy_name: str,
    information_policy_name: str = BASELINE_INFORMATION_POLICY,
    reserve_policy_name: str = BASELINE_RESERVE_POLICY,
    max_depth: int = 8,
) -> PlannerAction | None:
    results = enumerate_action_sequences(
        state, deck, scry_policy_name=scry_policy_name, max_depth=max_depth,
        information_policy_name=information_policy_name,
    )
    selected = _selected_result(results, action_policy_name, reserve_policy_name)
    return None if selected is None or not selected.planner_actions else selected.planner_actions[0]


def execute_action_policy(
    state: GameState,
    deck: DeckSpec,
    *,
    action_policy_name: str,
    scry_policy_name: str,
    max_actions: int = 12,
    information_policy_name: str = BASELINE_INFORMATION_POLICY,
    reserve_policy_name: str = BASELINE_RESERVE_POLICY,
    search_depth: int = 8,
) -> tuple[str, ...]:
    executed: list[str] = []
    roots: list[str] = []
    for _ in range(max_actions):
        action = choose_next_action(
            state, deck, action_policy_name=action_policy_name, scry_policy_name=scry_policy_name,
            information_policy_name=information_policy_name, reserve_policy_name=reserve_policy_name,
            max_depth=search_depth,
        )
        if action is None:
            break
        roots.append(str(action.key))
        record_timing_snapshot(state, deck, "before_relevant_action")
        apply_planner_action(state, deck, action, scry_policy_name=scry_policy_name, reveal_information=True)
        executed.append(action.label)
        record_timing_snapshot(state, deck, "after_relevant_action")
    state.log(
        "policy_action_sequence", policy=action_policy_name, reserve_policy=reserve_policy_name,
        selected=executed,
        causal_root_decisions=roots, replanned_after_information=True,
    )
    return tuple(executed)


def evaluate_post_land_state(state: GameState, deck: DeckSpec) -> dict[str, Any]:
    results = enumerate_action_sequences(
        state, deck, scry_policy_name=BASELINE_SCRY_POLICY, max_depth=6, include_land_actions=False
    )
    selected = _selected_result(results, BASELINE_ACTION_POLICY)
    if selected is None:
        return {"due_executions": 0, "spell_executions": 0, "reserve_preserved": True, "best_due_without_land": 0}
    return {
        "due_executions": selected.option.due_executions,
        "spell_executions": selected.option.spell_executions,
        "reserve_preserved": selected.option.reserve_preserved,
        "best_due_without_land": 0,
    }


def simulate_trial(
    deck: DeckSpec,
    land_counts: dict[str, int],
    *,
    candidate_label: str,
    scenario_label: str,
    trial: int,
    seed: int,
    on_play: bool,
    mulligan_policy: str,
    sequencing_policy: str,
    scry_policy_name: str | None = None,
    audit_full_action_policy: bool = True,
    information_policy_name: str = BASELINE_INFORMATION_POLICY,
    reserve_policy_name: str = BASELINE_RESERVE_POLICY,
    planner_search_depth: int = 8,
    planner_max_actions: int = 12,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    base = _physical_deck(deck, land_counts)

    def draw_seven(attempt: int):
        shuffled = _shuffled(base, _stable_scenario_seed(seed, scenario_label, trial, attempt))
        return shuffled[:7], shuffled[7:]

    raw_hand, _ = draw_seven(0)
    raw_lands = sum(card.name in deck.land_by_name for card in raw_hand)
    raw_presence = {color: _source_presence(raw_hand, deck, color) for color in "WUBR"}
    result = london_mulligan(deck, mulligan_policy, draw_seven)
    state = GameState(
        library=list(result.library), hand=list(result.hand), on_play=on_play,
        trial_id=trial, scenario_id=scenario_label, replicate_id=seed,
    )
    action_policy = BASELINE_ACTION_POLICY if sequencing_policy == BASELINE_LAND_POLICY else ALTERNATE_ACTION_POLICY
    # Legacy callers may omit the scry axis, but Phase 3 callers pass it
    # independently. Sequencing must never silently select a different scry
    # policy when an explicit scry identity is supplied.
    if scry_policy_name is None:
        scry_policy_name = BASELINE_SCRY_POLICY if sequencing_policy == BASELINE_LAND_POLICY else ALTERNATE_SCRY_POLICY
    state.log(
        "opening_hand", opening_land_count=raw_lands, keep_size=len(result.hand), mulligans=result.mulligans,
        bottomed=[card.name for card in result.bottomed],
        bottomed_categories=["land" if card.name in deck.land_by_name else "spell" for card in result.bottomed],
    )
    usable: dict[int, int] = {}
    access_t2 = {color: False for color in "WUBR"}
    ub_t2 = False
    artifacts_t3 = 0
    metalcraft_t3 = False
    opponent_t3 = 0
    for turn in range(1, 5):
        state.begin_turn(turn)
        start = record_timing_snapshot(state, deck, "start_own_main")
        start_interaction_status = opponent_window_status(state, deck)
        usable[turn] = int(start["usable_untapped_mana"])
        if turn == 2:
            for color in "WUBR":
                access_t2[color] = bool(find_payment_plan(state, ManaCost(colored={color: 1})))
            ub_t2 = bool(find_payment_plan(state, ManaCost(colored={"U": 1, "B": 1})))
        sequences = enumerate_action_sequences(
            state, deck, scry_policy_name=scry_policy_name,
            information_policy_name=information_policy_name,
            max_depth=planner_search_depth,
        )
        state.log(
            "multi_action_window", timing="start_own_main",
            double_spell_feasible=any(result.option.spell_executions >= 2 for result in sequences),
            spell_plus_interaction_feasible=any(result.option.spell_executions >= 1 and result.option.reserve_preserved for result in sequences),
        )
        execute_action_policy(
            state, deck, action_policy_name=action_policy, scry_policy_name=scry_policy_name,
            information_policy_name=information_policy_name, reserve_policy_name=reserve_policy_name,
            search_depth=planner_search_depth, max_actions=planner_max_actions,
        )
        if turn == 3:
            artifacts_t3 = state.artifact_count()
            metalcraft_t3 = state.metalcraft()
        status = opponent_window_status(state, deck)
        for name, item in status.items():
            payable_before_spending = bool(start_interaction_status[name]["payable"])
            spent_during_own_turn = payable_before_spending and not bool(item["payable"])
            state.log(
                "opponent_window", card=name, interaction_in_hand=item["in_hand"], payable=item["payable"],
                demand=item["demand"], resource_preserved=item["payable"],
                metalcraft=state.metalcraft(),
                payable_before_own_turn_spending=payable_before_spending,
                resource_spent=spent_during_own_turn,
                preservation_failure_reason=(
                    None if item["payable"] or not item["in_hand"]
                    else "own_turn_spend" if spent_during_own_turn else "not_payable_at_start"
                ),
            )
        if turn == 3:
            opponent_t3 = sum(bool(item["payable"]) for item in status.values())
        record_timing_snapshot(state, deck, "end_own_turn_opponent_window")
        state.end_phase("opponent")
        state.end_phase("end")

    cast_names = [event["card"] for event in state.events if event["event"] == "spell_cast"]
    executed_identity = {
        "candidate": candidate_label,
        "mulligan_policy": mulligan_policy,
        "sequencing_policy": sequencing_policy,
        "scry_policy": scry_policy_name,
        "information_policy": information_policy_name,
        "reserve_policy": reserve_policy_name,
        "planner_search_depth": int(planner_search_depth),
        "planner_max_actions": int(planner_max_actions),
    }
    for event in state.events:
        event.update(executed_identity)

    row = {
        "candidate": candidate_label, "scenario": scenario_label, "replicate": seed, "trial": trial,
        **executed_identity,
        "pairing_id": f"scenario={scenario_label}|replicate={seed}|trial={trial}|on_play={int(on_play)}",
        "on_play": on_play,
        "raw_opening_lands": raw_lands, "raw_W": raw_presence["W"], "raw_U": raw_presence["U"],
        "raw_B": raw_presence["B"], "raw_R": raw_presence["R"], "raw_joint_UB": _joint_ub(raw_hand, deck),
        "mulligans": result.mulligans, "kept_hand_size": len(result.hand),
        **{f"usable_mana_t{turn}": usable[turn] for turn in range(1, 5)},
        **{f"{color}_t2": access_t2[color] for color in "WUBR"},
        "UB_t2": ub_t2, "artifacts_t3": artifacts_t3, "metalcraft_t3": metalcraft_t3,
        "opponent_options_t3": opponent_t3,
        "boulder_deployed": any(event["event"] == "boulder_deployed" for event in state.events),
        "policy_decisions": sum(event["event"] == "policy_action_sequence" for event in state.events),
        "spells_cast": len(cast_names),
    }
    return row, state.events


def run_smoke_matrix(
    deck: DeckSpec,
    experiment: dict[str, Any],
    candidates: dict[str, dict[str, int]],
    output_dir: str | Path,
    *,
    trials_override: int | None = None,
) -> dict[str, Any]:
    """Production-policy validation; every trial uses the Phase-3 planner."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    trials = trials_override or int(experiment.get("run_c_production_validation", {}).get("trials_per_scenario", 25))
    validation_scope = experiment.get("run_c_production_validation", {})
    seed = int(experiment["randomness"]["validation_seed"])
    event_path = output_dir / "production_smoke_summary_rows.csv.gz"
    raw_path = output_dir / "production_smoke_raw_events.jsonl.gz"
    summaries: dict[str, Any] = {}
    with GzipEventWriter(event_path) as writer, gzip.open(raw_path, "wt", encoding="utf-8") as raw:
        for play_draw in validation_scope.get("play_draw", experiment["scenarios"]["play_draw"]):
            for mulligan_policy in validation_scope.get("mulligans", experiment["scenarios"]["mulligans"]):
                for sequencing_policy in validation_scope.get("sequencing", experiment["scenarios"]["sequencing"]):
                    scenario = f"{play_draw}|{mulligan_policy}|{sequencing_policy}"
                    summaries[scenario] = {}
                    for candidate_label, counts in candidates.items():
                        aggregate = SmokeAggregator()
                        for trial in range(trials):
                            on_play = play_draw == "all_play" or (play_draw == "mixed" and trial % 2 == 0)
                            row, events = simulate_trial(
                                deck, counts, candidate_label=candidate_label, scenario_label=scenario, trial=trial,
                                seed=seed, on_play=on_play, mulligan_policy=mulligan_policy,
                                sequencing_policy=sequencing_policy, audit_full_action_policy=True,
                            )
                            writer.write(row)
                            aggregate.add(row)
                            raw.write(json.dumps({"candidate": candidate_label, "scenario": scenario, "trial": trial, "events": events}, sort_keys=True) + "\n")
                        summaries[scenario][candidate_label] = aggregate.summary()
    result = {
        "banner": "MACHINERY VALIDATION ONLY — NOT A RANKING / NOT AN OPTIMIZATION",
        "policy": "production_visible_state_planner_all_trials", "trials_per_scenario_candidate": trials,
        "validation_seed": seed, "selection_seed_used": False, "event_file": event_path.name,
        "raw_event_file": raw_path.name, "summaries": summaries,
    }
    (output_dir / "production_smoke_manifest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
