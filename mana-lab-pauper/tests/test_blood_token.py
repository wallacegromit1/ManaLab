import unittest

from mana_lab.effects import activate_blood, enter_artifact
from mana_lab.state import GameState, make_card
from common import library


class BloodTokenTests(unittest.TestCase):
    def test_fountain_creates_artifact_token(self):
        state = GameState()
        enter_artifact(state, make_card("f", "Blood Fountain", artifact=True))
        state.resolve_all()
        self.assertEqual(state.artifact_count(), 2)
        self.assertEqual(sorted(p.card.name for p in state.battlefield), ["Blood", "Blood Fountain"])

    def test_activation_pays_all_costs_and_cannot_reuse_token(self):
        discard = make_card("d", "Discard Me")
        state = GameState(library=library("Drawn"), hand=[discard])
        blood = state.create_token("Blood", artifact=True)
        state.mana_pool.add("W")
        activate_blood(state, blood, discard)
        self.assertNotIn(blood, state.battlefield)
        self.assertEqual([card.name for card in state.hand], ["Drawn"])
        with self.assertRaises(ValueError):
            activate_blood(state, blood, state.hand[0])


if __name__ == "__main__":
    unittest.main()

