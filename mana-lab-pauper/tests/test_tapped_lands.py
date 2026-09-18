import unittest

from mana_lab.state import GameState, make_card
from common import deck_spec


class TappedLandTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def test_bridge_enters_tapped_and_counts_as_artifact(self):
        state = GameState(hand=[make_card("bridge", "Mistvault Bridge", artifact=True, land=True)], phase="main")
        permanent = state.play_land(state.hand[0], self.deck.land_by_name["Mistvault Bridge"])
        self.assertTrue(permanent.tapped)
        self.assertEqual(state.artifact_count(), 1)
        with self.assertRaises(ValueError):
            state.tap_land_for(permanent, "U")

    def test_mono_land_enters_untapped_and_taps_once(self):
        state = GameState(hand=[make_card("den", "Ancient Den", artifact=True, land=True)], phase="main")
        permanent = state.play_land(state.hand[0], self.deck.land_by_name["Ancient Den"])
        self.assertFalse(permanent.tapped)
        state.tap_land_for(permanent, "W")
        with self.assertRaises(ValueError):
            state.tap_land_for(permanent, "W")


if __name__ == "__main__":
    unittest.main()
