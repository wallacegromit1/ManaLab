from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from .cards import DeckSpec
from .mana import ManaCost
from .payment import find_payment_plan
from .simulator import generate_legal_actions, record_timing_snapshot
from .state import GameState


@dataclass(frozen=True)
class ResourceOption:
    name: str
    resource_payable: bool
    target_available: bool | None
    executable: bool
    artifact_count_before: int
    metalcraft_before: bool
    notes: str = ""


def blood_activation_option(state: GameState, deck: DeckSpec) -> ResourceOption:
    actions = [action for action in generate_legal_actions(state, deck) if action.kind == "blood_activation"]
    blood_exists = any(p.card.name == "Blood" and not p.tapped for p in state.battlefield)
    resource = blood_exists and bool(state.hand) and find_payment_plan(state, ManaCost(generic=1)) is not None
    return ResourceOption(
        "Blood activation", resource, None, bool(actions),
        state.artifact_count(), state.metalcraft(),
        "No opponent target is required; planner reachability must equal resource feasibility.",
    )


def familiar_draw_counterfactual(state: GameState, deck: DeckSpec) -> dict[str, Any]:
    """Candidate-neutral zero-versus-one-draw containment branch.

    This is post-hoc sensitivity evidence only. It never exposes the card
    identity to a sequencing decision before a legal draw would occur.
    """
    no_draw = copy.deepcopy(state)
    with_draw = copy.deepcopy(state)
    before = record_timing_snapshot(no_draw, deck, "familiar_counterfactual_no_draw")
    drawn = with_draw.draw(1, reason="Refurbished Familiar conditional counterfactual")
    after = record_timing_snapshot(with_draw, deck, "familiar_counterfactual_draw")
    return {
        "draw_available": bool(drawn),
        "no_draw": before,
        "with_draw": after,
        "hand_delta": len(with_draw.hand) - len(no_draw.hand),
        "artifact_delta": with_draw.artifact_count() - no_draw.artifact_count(),
        "counterfactual_only": True,
    }


def target_conditional_activation_options(
    state: GameState,
    *,
    munitions_target_available: bool,
    cryogen_tapped_target_available: bool,
) -> dict[str, ResourceOption]:
    munitions = next((p for p in state.battlefield if p.card.name == "Makeshift Munitions"), None)
    sacrifice_available = any(
        (p.is_artifact or p.is_creature) and p is not munitions
        for p in state.battlefield
    )
    munitions_resource = (
        munitions is not None and sacrifice_available
        and find_payment_plan(state, ManaCost(generic=1)) is not None
    )
    cryogen = next((p for p in state.battlefield if p.card.name == "Cryogen Relic"), None)
    cryogen_resource = (
        cryogen is not None
        and find_payment_plan(state, ManaCost(generic=1, colored={"U": 1})) is not None
    )
    return {
        "munitions": ResourceOption(
            "Makeshift Munitions activation", munitions_resource,
            munitions_target_available,
            munitions_resource and munitions_target_available,
            state.artifact_count(), state.metalcraft(),
            "Target availability is externally supplied and never inferred from mana resources.",
        ),
        "cryogen": ResourceOption(
            "Cryogen Relic stun activation", cryogen_resource,
            cryogen_tapped_target_available,
            cryogen_resource and cryogen_tapped_target_available,
            state.artifact_count(), state.metalcraft(),
            "Tapped-target availability is externally supplied and never inferred from mana resources.",
        ),
    }


def fountain_recursion_resource_bound(state: GameState) -> dict[str, Any]:
    fountain = next((p for p in state.battlefield if p.card.name == "Blood Fountain"), None)
    resource_payable = (
        fountain is not None and not fountain.tapped
        and find_payment_plan(state, ManaCost(generic=3, colored={"B": 1})) is not None
    )
    own_graveyard_creatures = sorted(
        card.name for card in state.graveyard if card.is_creature
    )
    return {
        "resource_payable": resource_payable,
        "own_graveyard_creature_targets": own_graveyard_creatures,
        "target_count": len(own_graveyard_creatures),
        "effect_modeled": False,
        "blocking_if_reachable": bool(resource_payable),
        "reason": (
            "Frozen project sources specify the 3B/tap/sacrifice activation cost "
            "but do not freeze the recursion effect/target contract. Run I does "
            "not fill that material rules gap from memory."
        ),
    }


def single_land_removal_sensitivity(state: GameState, deck: DeckSpec) -> list[dict[str, Any]]:
    """One-land destructive-removal bound with Bridge indestructibility respected."""
    results: list[dict[str, Any]] = []
    for permanent in [p for p in state.battlefield if p.is_land and p.land_spec is not None]:
        probe = copy.deepcopy(state)
        target = next(p for p in probe.battlefield if p.card.uid == permanent.card.uid)
        indestructible = bool(target.land_spec and target.land_spec.indestructible)
        before = {
            "artifact_count": probe.artifact_count(),
            "metalcraft": probe.metalcraft(),
            "untapped_lands": len(probe.untapped_lands()),
        }
        if not indestructible:
            probe.battlefield.remove(target)
            if not target.token:
                probe.graveyard.append(target.card)
        after = {
            "artifact_count": probe.artifact_count(),
            "metalcraft": probe.metalcraft(),
            "untapped_lands": len(probe.untapped_lands()),
        }
        results.append({
            "land": permanent.card.name,
            "indestructible": indestructible,
            "removed": not indestructible,
            "before": before,
            "after": after,
            "artifact_delta": after["artifact_count"] - before["artifact_count"],
            "untapped_land_delta": after["untapped_lands"] - before["untapped_lands"],
        })
    return results


def sacrifice_resource_delta(before: GameState, after: GameState) -> dict[str, Any]:
    """Shared containment record for sacrifice-induced future-resource changes."""
    before_colors = {
        color for p in before.battlefield
        if p.is_land and not p.tapped and p.land_spec is not None
        for color in p.land_spec.colors
    }
    after_colors = {
        color for p in after.battlefield
        if p.is_land and not p.tapped and p.land_spec is not None
        for color in p.land_spec.colors
    }
    return {
        "artifact_delta": after.artifact_count() - before.artifact_count(),
        "metalcraft_before": before.metalcraft(),
        "metalcraft_after": after.metalcraft(),
        "untapped_land_delta": len(after.untapped_lands()) - len(before.untapped_lands()),
        "colors_lost": sorted(before_colors - after_colors),
        "hand_delta": len(after.hand) - len(before.hand),
    }
