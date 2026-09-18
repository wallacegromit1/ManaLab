from __future__ import annotations

from pathlib import Path

from mana_lab.cards import load_deck
from mana_lab.state import GameState, Permanent, make_card


ROOT = Path(__file__).resolve().parents[1]
DECK_PATH = ROOT / "configs" / "decks" / "Strixpatch_Affinity_v1.3.deck.yaml"


def deck_spec():
    return load_deck(DECK_PATH)


def library(*names: str):
    return [make_card(f"lib-{index}", name) for index, name in enumerate(names)]


def land_permanent(deck, name: str, uid: str | None = None, *, tapped: bool | None = None) -> Permanent:
    spec = deck.land_by_name[name]
    return Permanent(
        make_card(uid or f"land-{name}", name, artifact=True, land=True),
        tapped=spec.enters_tapped if tapped is None else tapped,
        land_spec=spec,
    )


def state_with_lands(deck, names: list[str], *, library_names: tuple[str, ...] = ()) -> GameState:
    state = GameState(library=library(*library_names), phase="main", turn=1)
    state.battlefield = [land_permanent(deck, name, f"land-{index}", tapped=False) for index, name in enumerate(names)]
    return state

