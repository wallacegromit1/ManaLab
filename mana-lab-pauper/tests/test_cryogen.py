import unittest

from mana_lab.effects import activate_cryogen, enter_artifact, leave_battlefield, sacrifice_to_munitions
from mana_lab.state import GameState, Permanent, make_card
from common import library


class CryogenTests(unittest.TestCase):
    def test_enter_draws_exact_top(self):
        state = GameState(library=library("A", "B"))
        enter_artifact(state, make_card("c", "Cryogen Relic", artifact=True))
        state.resolve_all()
        self.assertEqual([card.name for card in state.hand], ["A"])

    def test_each_battlefield_leave_mode_triggers(self):
        for action in ("return", "munitions", "self"):
            state = GameState(library=library("A"))
            cryogen = Permanent(make_card("c", "Cryogen Relic", artifact=True))
            state.battlefield.append(cryogen)
            if action == "return":
                leave_battlefield(state, cryogen, "hand", reason="test")
            elif action == "munitions":
                sacrifice_to_munitions(state, cryogen)
            else:
                activate_cryogen(state, cryogen)
            state.resolve_all()
            self.assertEqual([card.name for card in state.hand if card.name == "A"], ["A"], action)

    def test_nonbattlefield_move_does_not_trigger(self):
        state = GameState(library=library("A"), hand=[make_card("c", "Cryogen Relic", artifact=True)])
        state.graveyard.append(state.hand.pop())
        self.assertFalse(state.stack)
        self.assertFalse(state.hand)


if __name__ == "__main__":
    unittest.main()

