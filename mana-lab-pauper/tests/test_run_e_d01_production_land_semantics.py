import copy
import unittest

from mana_lab.policies import BASELINE_ACTION_POLICY, BASELINE_SCRY_POLICY
from mana_lab.simulator import choose_next_action
from mana_lab.state import make_card
from common import deck_spec, state_with_lands


class ProductionLandSemanticsTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def root(self, state):
        return choose_next_action(
            state, self.deck, action_policy_name=BASELINE_ACTION_POLICY,
            scry_policy_name=BASELINE_SCRY_POLICY,
        )

    def bridge_fixture(self):
        state = state_with_lands(self.deck, ["Vault of Whispers"])
        state.turn = 1
        state.hand = [
            make_card("d", "Drossforge Bridge", artifact=True, land=True),
            make_card("m", "Mistvault Bridge", artifact=True, land=True),
            make_card("s", "Baleful Strix", artifact=True, creature=True),
        ]
        return state

    def test_exact_run_d_reproducer_uses_production_path(self):
        self.assertEqual(self.root(self.bridge_fixture()).label, "Play Mistvault Bridge")

    def test_hand_and_battlefield_order_do_not_change_choice(self):
        expected = self.root(self.bridge_fixture()).label
        for reverse_hand in (False, True):
            state = self.bridge_fixture()
            if reverse_hand:
                state.hand.reverse()
            state.battlefield.reverse()
            self.assertEqual(self.root(state).label, expected)

    def test_other_color_permutation(self):
        state = state_with_lands(self.deck, ["Seat of the Synod"])
        state.turn = 1
        state.hand = [
            make_card("g", "Goldmire Bridge", artifact=True, land=True),
            make_card("r", "Rustvale Bridge", artifact=True, land=True),
            make_card("s", "Baleful Strix", artifact=True, creature=True),
        ]
        self.assertEqual(self.root(state).label, "Play Goldmire Bridge")

    def test_future_colors_count_while_bridge_is_tapped(self):
        action = self.root(self.bridge_fixture())
        self.assertEqual(action.label, "Play Mistvault Bridge")

    def test_immediate_untapped_reply_wins(self):
        state = state_with_lands(self.deck, [])
        state.turn = 1
        state.hand = [
            make_card("d", "Ancient Den", artifact=True, land=True),
            make_card("g", "Goldmire Bridge", artifact=True, land=True),
            make_card("x", "Dispatch"),
        ]
        self.assertEqual(self.root(state).label, "Play Ancient Den")

    def test_true_slack_can_choose_future_color_bridge(self):
        state = state_with_lands(self.deck, ["Seat of the Synod"])
        state.turn = 1
        state.hand = [
            make_card("d", "Ancient Den", artifact=True, land=True),
            make_card("m", "Mistvault Bridge", artifact=True, land=True),
            make_card("s", "Baleful Strix", artifact=True, creature=True),
        ]
        self.assertEqual(self.root(state).label, "Play Mistvault Bridge")


if __name__ == "__main__":
    unittest.main()
