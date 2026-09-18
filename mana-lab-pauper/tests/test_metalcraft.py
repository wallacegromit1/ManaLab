import unittest

from mana_lab.effects import interaction_state, leave_battlefield
from mana_lab.state import GameState, Permanent, make_card


class MetalcraftTests(unittest.TestCase):
    def test_threshold_transitions_and_tapping_does_not_remove_artifact(self):
        state = GameState()
        artifacts = [Permanent(make_card(f"a{i}", f"A{i}", artifact=True), tapped=(i == 0)) for i in range(3)]
        state.battlefield.extend(artifacts)
        self.assertTrue(state.metalcraft())
        leave_battlefield(state, artifacts[0], "hand", reason="test")
        self.assertFalse(state.metalcraft())

    def test_dispatch_and_blast_full_effect_at_resolution(self):
        for artifacts in range(3):
            self.assertFalse(interaction_state("Dispatch", artifacts)["metalcraft"])
            self.assertEqual(interaction_state("Galvanic Blast", artifacts)["damage"], 2)
        self.assertEqual(interaction_state("Dispatch", 3)["full_effect"], "exile")
        self.assertEqual(interaction_state("Galvanic Blast", 3)["damage"], 4)


if __name__ == "__main__":
    unittest.main()

