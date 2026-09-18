import unittest

from mana_lab.effects import ScryDecision, resolve_scry
from mana_lab.policies import BASELINE_SCRY_POLICY, make_scry_policy
from mana_lab.state import GameState, make_card
from common import deck_spec, library


class ScryNoLookaheadTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def test_same_top_two_different_third_same_decision(self):
        policy = make_scry_policy(self.deck, BASELINE_SCRY_POLICY)
        decisions = []
        for third in ("Hidden X", "Hidden Y"):
            state = GameState(library=library("Ancient Den", "Thoughtcast", third))
            decisions.append(resolve_scry(state, 2, policy))
        self.assertEqual(decisions[0], decisions[1])

    def test_policy_cannot_access_library(self):
        state = GameState(library=library("A", "B", "SECRET"))

        def sentinel(revealed, visible):
            self.assertFalse(hasattr(visible, "library"))
            self.assertEqual([card.name for card in revealed], ["A", "B"])
            return ScryDecision((), ())

        resolve_scry(state, 2, sentinel)
        self.assertEqual(state.library[0].name, "SECRET")

    def test_bottom_both_does_not_reconsult_new_top(self):
        calls = []
        state = GameState(library=library("A", "B", "C", "D"))
        resolve_scry(state, 2, lambda revealed, visible: (calls.append(tuple(c.name for c in revealed)) or ScryDecision((), ())))
        self.assertEqual(calls, [("A", "B")])


if __name__ == "__main__":
    unittest.main()

