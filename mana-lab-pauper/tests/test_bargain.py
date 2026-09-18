import unittest

from mana_lab.effects import can_cast_bargain, cast_reckoners_bargain
from mana_lab.state import GameState, Permanent, make_card
from common import deck_spec, land_permanent, library


class BargainTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def test_requires_legal_sacrifice(self):
        state = GameState()
        self.assertFalse(can_cast_bargain(state))
        with self.assertRaises(ValueError):
            cast_reckoners_bargain(state, Permanent(make_card("x", "X")))

    def test_land_sacrifice_immediately_removes_resource_and_logs_choice(self):
        state = GameState(library=library("A", "B"))
        land = land_permanent(self.deck, "Vault of Whispers", tapped=False)
        state.battlefield.append(land)
        cast_reckoners_bargain(state, land)
        self.assertNotIn(land, state.battlefield)
        self.assertEqual(state.artifact_count(), 0)
        event = next(event for event in state.events if event["event"] == "bargain_cast")
        self.assertEqual(event["sacrifice"], "Vault of Whispers")


if __name__ == "__main__":
    unittest.main()

