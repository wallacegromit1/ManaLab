from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .cards import LandSpec
from .mana import ManaPool


@dataclass(frozen=True)
class PhysicalCard:
    uid: str
    name: str
    is_artifact: bool = False
    is_creature: bool = False
    is_land: bool = False


@dataclass
class Permanent:
    card: PhysicalCard
    tapped: bool = False
    land_spec: LandSpec | None = None
    token: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_artifact(self) -> bool:
        return self.card.is_artifact

    @property
    def is_creature(self) -> bool:
        return self.card.is_creature

    @property
    def is_land(self) -> bool:
        return self.card.is_land


@dataclass
class StackItem:
    label: str
    resolve: Callable[["GameState"], None]
    kind: str = "trigger"


@dataclass
class GameState:
    library: list[PhysicalCard] = field(default_factory=list)
    hand: list[PhysicalCard] = field(default_factory=list)
    battlefield: list[Permanent] = field(default_factory=list)
    graveyard: list[PhysicalCard] = field(default_factory=list)
    exile: list[PhysicalCard] = field(default_factory=list)
    stack: list[StackItem] = field(default_factory=list)
    mana_pool: ManaPool = field(default_factory=ManaPool)
    turn: int = 0
    on_play: bool = True
    land_drop_available: bool = True
    phase: str = "pre_game"
    revealed_scry: tuple[PhysicalCard, ...] = ()
    events: list[dict[str, Any]] = field(default_factory=list)
    trial_id: int | None = None
    scenario_id: str | None = None
    replicate_id: int | str | None = None
    _token_counter: int = 0
    _event_counter: int = 0
    _window_counter: int = 0

    def log(self, event: str, **details: Any) -> None:
        self._event_counter += 1
        identity = {
            "trial_id": self.trial_id,
            "scenario": self.scenario_id,
            "replicate": self.replicate_id,
            "on_play": self.on_play,
        }
        self.events.append({
            "event_id": self._event_counter,
            "event": event,
            "turn": self.turn,
            "phase": self.phase,
            **identity,
            **details,
        })

    def next_window_sequence(self) -> int:
        self._window_counter += 1
        return self._window_counter

    def draw(
        self, count: int = 1, reason: str = "draw", *, source_uid: str | None = None
    ) -> list[PhysicalCard]:
        drawn: list[PhysicalCard] = []
        for _ in range(count):
            if not self.library:
                break
            card = self.library.pop(0)
            self.hand.append(card)
            drawn.append(card)
            self.log(
                "draw", card=card.name, uid=card.uid, reason=reason,
                source_uid=source_uid,
            )
        return drawn

    def begin_turn(self, turn: int) -> None:
        self.turn = turn
        self.phase = "untap"
        self.mana_pool.clear()
        for permanent in self.battlefield:
            permanent.tapped = False
        self.land_drop_available = True
        self.log("untap")
        self.phase = "draw"
        if not (turn == 1 and self.on_play):
            self.draw(1, reason="turn_draw")
        else:
            self.log("draw_skipped", reason="on_play_turn_one")
        self.phase = "main"

    def end_phase(self, next_phase: str) -> None:
        self.mana_pool.clear()
        self.phase = next_phase
        self.log("mana_pool_emptied")

    def play_land(self, card: PhysicalCard, spec: LandSpec) -> Permanent:
        if self.phase not in {"main", "main1", "main2"}:
            raise ValueError("land may be played only in an own main phase")
        if not self.land_drop_available or card not in self.hand:
            raise ValueError("illegal land play")
        self.hand.remove(card)
        permanent = Permanent(card=card, tapped=spec.enters_tapped, land_spec=spec)
        self.battlefield.append(permanent)
        self.land_drop_available = False
        returned_by_hawk = any(
            event["event"] == "glint_hawk_return" and event.get("uid") == card.uid
            for event in self.events
        )
        self.log(
            "land_played",
            card=card.name,
            uid=card.uid,
            tapped=permanent.tapped,
            artifact=spec.artifact,
            colors=list(spec.colors),
            hawk_replay=returned_by_hawk,
        )
        if returned_by_hawk:
            self.log(
                "hawk_land_replay",
                card=card.name,
                uid=card.uid,
                entered_tapped=permanent.tapped,
                realized_mana_loss=int(permanent.tapped),
            )
        return permanent

    def artifact_count(self) -> int:
        return sum(1 for permanent in self.battlefield if permanent.is_artifact)

    def metalcraft(self) -> bool:
        return self.artifact_count() >= 3

    def untapped_lands(self) -> list[Permanent]:
        return [p for p in self.battlefield if p.is_land and not p.tapped]

    def tap_land_for(self, permanent: Permanent, color: str) -> None:
        if permanent not in self.battlefield or not permanent.is_land or permanent.tapped:
            raise ValueError("land is not a usable source")
        if permanent.land_spec is None or color not in permanent.land_spec.colors:
            raise ValueError("land cannot produce requested color")
        permanent.tapped = True
        self.mana_pool.add(color)
        self.log("mana_produced", source=permanent.card.name, color=color)

    def add_permanent(self, card: PhysicalCard, *, tapped: bool = False, token: bool = False) -> Permanent:
        permanent = Permanent(card=card, tapped=tapped, token=token)
        self.battlefield.append(permanent)
        self.log("permanent_entered", card=card.name, uid=card.uid, token=token)
        return permanent

    def create_token(self, name: str, *, artifact: bool, creature: bool = False) -> Permanent:
        self._token_counter += 1
        card = PhysicalCard(f"token-{self._token_counter}", name, artifact, creature, False)
        return self.add_permanent(card, token=True)

    def push(self, item: StackItem) -> None:
        self.stack.append(item)
        self.log("stack_push", label=item.label, kind=item.kind)

    def resolve_top(self) -> None:
        if not self.stack:
            raise ValueError("stack is empty")
        item = self.stack.pop()
        self.log("stack_resolve", label=item.label, kind=item.kind)
        item.resolve(self)

    def resolve_all(self) -> None:
        while self.stack:
            self.resolve_top()

    def visible_snapshot(self) -> tuple:
        return (
            tuple(sorted((card.name, card.uid) for card in self.hand)),
            tuple(sorted((p.card.name, p.card.uid, p.tapped) for p in self.battlefield)),
            tuple(sorted(card.name for card in self.graveyard)),
            self.turn,
            self.phase,
            self.land_drop_available,
            tuple(card.name for card in self.revealed_scry),
            tuple((color, self.mana_pool.amounts[color]) for color in sorted(self.mana_pool.amounts)),
            tuple((item.label, item.kind) for item in self.stack),
            tuple(
                (event.get("kind"), event.get("count"), event.get("reason"))
                for event in self.events
                if event["event"] == "information_node"
            ),
        )


def make_card(uid: str, name: str, *, artifact: bool = False, creature: bool = False, land: bool = False) -> PhysicalCard:
    return PhysicalCard(uid=uid, name=name, is_artifact=artifact, is_creature=creature, is_land=land)
