import unittest

from mana_lab.effects import no_auto_draw_for_familiar
from mana_lab.state import GameState
from common import library


class FamiliarTests(unittest.TestCase):
    def test_goldfish_does_not_auto_draw(self):
        state = GameState(library=library("A"))
        no_auto_draw_for_familiar(state)
        self.assertFalse(state.hand)
        self.assertEqual(state.library[0].name, "A")


if __name__ == "__main__":
    unittest.main()

