import unittest

from mana_lab.state import GameState
from common import library


class PlayDrawTests(unittest.TestCase):
    def test_on_play_skips_turn_one_draw(self):
        state = GameState(library=library("A", "B"), on_play=True)
        state.begin_turn(1)
        self.assertEqual(len(state.hand), 0)
        state.begin_turn(2)
        self.assertEqual([card.name for card in state.hand], ["A"])

    def test_on_draw_draws_turn_one(self):
        state = GameState(library=library("A", "B"), on_play=False)
        state.begin_turn(1)
        self.assertEqual([card.name for card in state.hand], ["A"])


if __name__ == "__main__":
    unittest.main()

