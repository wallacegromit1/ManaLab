import unittest

from mana_lab.policies import opponent_options
from mana_lab.state import make_card
from common import deck_spec, state_with_lands


class OpponentReserveTests(unittest.TestCase):
    def test_options_observe_actual_tapped_state(self):
        deck = deck_spec()
        state = state_with_lands(deck, ["Great Furnace"])
        state.hand = [make_card("g", "Galvanic Blast")]
        self.assertTrue(opponent_options(state)["Galvanic Blast"])
        state.tap_land_for(state.battlefield[0], "R")
        self.assertTrue(opponent_options(state)["Galvanic Blast"], "floating mana is an actual current-window resource")
        state.end_phase("opponent")
        self.assertFalse(opponent_options(state)["Galvanic Blast"])

    def test_mana_cannot_be_banked_to_opponent_window(self):
        deck = deck_spec()
        state = state_with_lands(deck, ["Great Furnace"])
        state.tap_land_for(state.battlefield[0], "R")
        state.end_phase("opponent")
        self.assertEqual(state.mana_pool.total, 0)


if __name__ == "__main__":
    unittest.main()
