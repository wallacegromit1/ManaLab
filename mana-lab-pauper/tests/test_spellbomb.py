import unittest

from mana_lab.effects import leave_battlefield, resolve_nihil_optional_draw
from mana_lab.state import GameState, Permanent, make_card
from common import library


class SpellbombTests(unittest.TestCase):
    def test_graveyard_move_creates_optional_b_draw_and_payment(self):
        state = GameState(library=library("A"))
        spellbomb = Permanent(make_card("n", "Nihil Spellbomb", artifact=True))
        state.battlefield.append(spellbomb)
        state.mana_pool.add("B")
        leave_battlefield(state, spellbomb, "graveyard", reason="activation")
        resolve_nihil_optional_draw(state, pay_black=True)
        self.assertEqual(state.mana_pool.total, 0)
        self.assertEqual([card.name for card in state.hand], ["A"])

    def test_return_to_hand_does_not_trigger(self):
        state = GameState()
        spellbomb = Permanent(make_card("n", "Nihil Spellbomb", artifact=True))
        state.battlefield.append(spellbomb)
        leave_battlefield(state, spellbomb, "hand", reason="Hawk")
        self.assertFalse(state.stack)


if __name__ == "__main__":
    unittest.main()

