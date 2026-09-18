from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from .mana import ManaCost
from .state import GameState, Permanent, PhysicalCard, StackItem, make_card


def draw_trigger(label: str, count: int = 1) -> StackItem:
    return StackItem(label, lambda state: state.draw(count, reason=label))


def enter_artifact(state: GameState, card: PhysicalCard) -> Permanent:
    permanent = state.add_permanent(card)
    if card.name == "Cryogen Relic":
        state.push(draw_trigger("Cryogen Relic enter draw"))
    elif card.name == "Blood Fountain":
        state.push(StackItem("Blood Fountain create Blood", lambda game: game.create_token("Blood", artifact=True)))
    return permanent


def leave_battlefield(
    state: GameState,
    permanent: Permanent,
    destination: str,
    *,
    reason: str,
) -> None:
    if permanent not in state.battlefield:
        raise ValueError("permanent is not on the battlefield")
    state.battlefield.remove(permanent)
    if destination == "hand":
        state.hand.append(permanent.card)
    elif destination == "graveyard":
        if not permanent.token:
            state.graveyard.append(permanent.card)
    elif destination == "exile":
        if not permanent.token:
            state.exile.append(permanent.card)
    else:
        raise ValueError("unsupported destination")
    state.log("permanent_left", card=permanent.card.name, destination=destination, reason=reason)
    if permanent.card.name == "Cryogen Relic":
        state.push(draw_trigger("Cryogen Relic leave draw"))
    if permanent.card.name == "Nihil Spellbomb" and destination == "graveyard":
        state.push(StackItem("Nihil Spellbomb optional B draw", lambda game: game.log("nihil_draw_opportunity")))


def activate_boulder_filter(state: GameState, boulder: Permanent, color: str) -> None:
    if boulder not in state.battlefield or boulder.card.name != "Giant's Boulder" or boulder.tapped:
        raise ValueError("Boulder is not a usable filter")
    if state.mana_pool.total < 1:
        raise ValueError("Boulder activation requires one mana")
    before = state.mana_pool.total
    state.mana_pool.pay(ManaCost(generic=1))
    boulder.tapped = True
    state.mana_pool.add(color)
    after = state.mana_pool.total
    if after != before:
        raise AssertionError("Boulder filter violated net-zero conservation")
    state.log("boulder_filter", color=color, net_mana=0)


@dataclass(frozen=True)
class ScryDecision:
    keep_indices: tuple[int, ...]
    keep_order: tuple[int, ...]

    def validate(self, seen_count: int) -> None:
        if set(self.keep_indices) != set(self.keep_order):
            raise ValueError("keep order must contain exactly the kept indices")
        if any(index < 0 or index >= seen_count for index in self.keep_indices):
            raise ValueError("invalid scry index")


ScryPolicy = Callable[[tuple[PhysicalCard, ...], Any], ScryDecision]


def resolve_scry(state: GameState, count: int, policy: ScryPolicy, *, label: str = "scry") -> ScryDecision:
    revealed = tuple(state.library[:count])
    state.revealed_scry = revealed
    state.log("scry_reveal", cards=[card.name for card in revealed], count=len(revealed))
    # Import lazily to keep the rules engine independent of a policy module.
    # The policy receives an immutable visible-state projection, never the
    # library object or any other hidden zone.
    from .policies import VisibleState

    decision = policy(revealed, VisibleState.from_state(state))
    decision.validate(len(revealed))
    kept = [revealed[index] for index in decision.keep_order]
    bottomed = [card for index, card in enumerate(revealed) if index not in decision.keep_indices]
    remainder = state.library[len(revealed) :]
    state.library[:] = kept + remainder + bottomed
    state.log(
        "scry_resolve",
        label=label,
        kept=[card.name for card in kept],
        bottomed=[card.name for card in bottomed],
    )
    state.revealed_scry = ()
    return decision


def resolve_boulder(state: GameState, card: PhysicalCard, policy: ScryPolicy) -> Permanent:
    permanent = enter_artifact(state, card)
    state.log("boulder_deployed", uid=card.uid)
    resolve_scry(state, 2, policy, label="Giant's Boulder scry 2")
    return permanent


def resolve_glint_hawk(state: GameState, hawk_card: PhysicalCard, return_target: Permanent | None) -> Permanent:
    hawk = state.add_permanent(hawk_card)

    def hawk_trigger(game: GameState) -> None:
        legal = [p for p in game.battlefield if p.is_artifact and p is not hawk]
        if return_target is None or return_target not in legal:
            leave_battlefield(game, hawk, "graveyard", reason="Glint Hawk no legal return")
            game.log("glint_hawk_sacrificed")
            return
        leave_battlefield(game, return_target, "hand", reason="Glint Hawk return")
        game.log(
            "glint_hawk_return",
            card=return_target.card.name,
            uid=return_target.card.uid,
            returned_land=return_target.is_land,
            was_tapped=return_target.tapped,
        )

    state.push(StackItem("Glint Hawk return-or-sacrifice", hawk_trigger))
    return hawk


def can_cast_bargain(state: GameState) -> bool:
    return any(p.is_artifact or p.is_creature for p in state.battlefield)


def cast_reckoners_bargain(state: GameState, sacrifice: Permanent) -> None:
    if sacrifice not in state.battlefield or not (sacrifice.is_artifact or sacrifice.is_creature):
        raise ValueError("Bargain requires a legal sacrifice")
    # The spell goes on the stack after all casting costs are paid. A trigger
    # created while paying costs is then placed above it.
    pending_before = len(state.stack)
    leave_battlefield(state, sacrifice, "graveyard", reason="Reckoner's Bargain additional cost")
    generated = state.stack[pending_before:]
    del state.stack[pending_before:]
    state.push(StackItem("Reckoner's Bargain", lambda game: game.draw(2, reason="Reckoner's Bargain"), kind="spell"))
    for trigger in generated:
        state.push(trigger)
    state.log(
        "bargain_cast",
        sacrifice=sacrifice.card.name,
        sacrifice_uid=sacrifice.card.uid,
        sacrifice_type="land" if sacrifice.is_land else ("artifact" if sacrifice.is_artifact else "creature"),
    )


def sacrifice_to_munitions(state: GameState, sacrifice: Permanent) -> None:
    if sacrifice not in state.battlefield or not (sacrifice.is_artifact or sacrifice.is_creature):
        raise ValueError("Munitions requires a legal sacrifice")
    leave_battlefield(state, sacrifice, "graveyard", reason="Makeshift Munitions activation")
    state.log("munitions_activation", sacrifice=sacrifice.card.name)


def activate_cryogen(state: GameState, cryogen: Permanent) -> None:
    if cryogen.card.name != "Cryogen Relic":
        raise ValueError("wrong permanent")
    leave_battlefield(state, cryogen, "graveyard", reason="Cryogen Relic activation")
    state.log("cryogen_stun_activation")


def activate_blood(state: GameState, blood: Permanent, discard: PhysicalCard) -> None:
    if blood not in state.battlefield or blood.card.name != "Blood" or blood.tapped:
        raise ValueError("Blood token is not usable")
    if discard not in state.hand or state.mana_pool.total < 1:
        raise ValueError("Blood activation costs cannot be paid")
    state.mana_pool.pay(ManaCost(generic=1))
    blood.tapped = True
    state.hand.remove(discard)
    state.graveyard.append(discard)
    leave_battlefield(state, blood, "graveyard", reason="Blood activation")
    state.draw(1, reason="Blood activation")
    state.log("blood_activation", discarded=discard.name)


def resolve_nihil_optional_draw(state: GameState, *, pay_black: bool) -> None:
    index = next((i for i in range(len(state.stack) - 1, -1, -1) if state.stack[i].label == "Nihil Spellbomb optional B draw"), None)
    if index is None:
        raise ValueError("no Nihil draw opportunity")
    state.stack.pop(index)
    if pay_black:
        state.mana_pool.pay(ManaCost(colored={"B": 1}))
        state.draw(1, reason="Nihil Spellbomb")
        state.log("nihil_draw_paid")
    else:
        state.log("nihil_draw_declined")


def interaction_state(card_name: str, artifact_count_at_resolution: int) -> dict[str, object]:
    if card_name == "Dispatch":
        return {"raw_effect": "tap", "metalcraft": artifact_count_at_resolution >= 3, "full_effect": "exile" if artifact_count_at_resolution >= 3 else None}
    if card_name == "Galvanic Blast":
        return {"damage": 4 if artifact_count_at_resolution >= 3 else 2, "metalcraft": artifact_count_at_resolution >= 3}
    raise ValueError("unsupported interaction")


def no_auto_draw_for_familiar(state: GameState) -> None:
    state.log("familiar_trigger_unresolved_model", reason="opponent_hand_unspecified")


def physical_cards(names: Iterable[str]) -> list[PhysicalCard]:
    return [make_card(f"card-{index}", name) for index, name in enumerate(names)]
