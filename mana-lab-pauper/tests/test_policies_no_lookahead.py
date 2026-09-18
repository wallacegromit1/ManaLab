import inspect
import unittest

from mana_lab.policies import ALTERNATE_LAND_POLICY, BASELINE_LAND_POLICY, choose_land, policy_source_has_candidate_branch
from mana_lab.state import GameState, make_card
from common import deck_spec


class PolicyNoLookaheadTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def _state(self, hidden):
        return GameState(
            hand=[
                make_card("d", "Ancient Den", artifact=True, land=True),
                make_card("m", "Mistvault Bridge", artifact=True, land=True),
                make_card("s", "Baleful Strix", artifact=True, creature=True),
            ],
            library=[make_card("hidden", hidden)],
            turn=1,
            phase="main",
        )

    def test_hidden_library_sentinel_land_decisions(self):
        for policy in (BASELINE_LAND_POLICY, ALTERNATE_LAND_POLICY):
            choices = [choose_land(self._state(hidden), self.deck, policy).name for hidden in ("Future A", "Future B")]
            self.assertEqual(choices[0], choices[1])

    def test_land_policy_deterministic(self):
        names = [choose_land(self._state("X"), self.deck, BASELINE_LAND_POLICY).name for _ in range(3)]
        self.assertEqual(len(set(names)), 1)

    def test_no_candidate_specific_policy_branch(self):
        self.assertFalse(policy_source_has_candidate_branch())

    def test_policy_signature_has_no_candidate_identity(self):
        self.assertNotIn("candidate", inspect.signature(choose_land).parameters)


if __name__ == "__main__":
    unittest.main()

