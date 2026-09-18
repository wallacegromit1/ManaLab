import unittest

from mana_lab.effects import ScryDecision, activate_boulder_filter, resolve_boulder, resolve_scry
from mana_lab.mana import ManaCost
from mana_lab.state import GameState, Permanent, make_card
from common import deck_spec, library, state_with_lands


class BoulderTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def test_cast_then_filter_with_two_lands(self):
        state = state_with_lands(self.deck, ["Ancient Den", "Seat of the Synod"], library_names=("A", "B", "C"))
        first, second = state.battlefield
        state.tap_land_for(first, "W")
        state.mana_pool.pay(ManaCost(generic=1))
        boulder = Permanent(make_card("b", "Giant's Boulder", artifact=True))
        state.battlefield.append(boulder)
        state.tap_land_for(second, "U")
        before = state.mana_pool.total
        activate_boulder_filter(state, boulder, "B")
        self.assertEqual(state.mana_pool.total, before)
        self.assertTrue(boulder.tapped)
        with self.assertRaises(ValueError):
            activate_boulder_filter(state, boulder, "R")
        state.begin_turn(2)
        self.assertFalse(boulder.tapped)

    def test_one_land_cast_leaves_no_activation_mana(self):
        state = state_with_lands(self.deck, ["Ancient Den"])
        land = state.battlefield[0]
        state.tap_land_for(land, "W")
        state.mana_pool.pay(ManaCost(generic=1))
        boulder = Permanent(make_card("b", "Giant's Boulder", artifact=True))
        state.battlefield.append(boulder)
        with self.assertRaises(ValueError):
            activate_boulder_filter(state, boulder, "U")

    def test_all_scry_two_movements(self):
        cases = [
            (ScryDecision((0, 1), (0, 1)), ["A", "B", "C", "D"]),
            (ScryDecision((0, 1), (1, 0)), ["B", "A", "C", "D"]),
            (ScryDecision((1,), (1,)), ["B", "C", "D", "A"]),
            (ScryDecision((0,), (0,)), ["A", "C", "D", "B"]),
            (ScryDecision((), ()), ["C", "D", "A", "B"]),
        ]
        for decision, expected in cases:
            state = GameState(library=library("A", "B", "C", "D"))
            resolve_scry(state, 2, lambda revealed, visible, d=decision: d)
            self.assertEqual([card.name for card in state.library], expected)

    def test_recast_gets_second_independent_scry(self):
        seen = []
        state = GameState(library=library("A", "B", "C", "D"))
        policy = lambda revealed, visible: (seen.append(tuple(card.name for card in revealed)) or ScryDecision((0, 1), (0, 1)))
        resolve_boulder(state, make_card("b", "Giant's Boulder", artifact=True), policy)
        boulder = next(p for p in state.battlefield if p.card.name == "Giant's Boulder")
        state.battlefield.remove(boulder)
        state.hand.append(boulder.card)
        resolve_boulder(state, boulder.card, policy)
        self.assertEqual(len(seen), 2)


if __name__ == "__main__":
    unittest.main()

