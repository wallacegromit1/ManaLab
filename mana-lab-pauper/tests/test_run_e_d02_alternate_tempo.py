import unittest

from mana_lab.policies import ALTERNATE_ACTION_POLICY, ALTERNATE_SCRY_POLICY
from mana_lab.simulator import choose_next_action
from mana_lab.state import make_card
from common import deck_spec, state_with_lands


class AlternateTempoTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def root(self, state):
        return choose_next_action(
            state, self.deck, action_policy_name=ALTERNATE_ACTION_POLICY,
            scry_policy_name=ALTERNATE_SCRY_POLICY,
        )

    def test_run_d_den_beats_bridge(self):
        state = state_with_lands(self.deck, [])
        state.hand = [
            make_card("d", "Ancient Den", artifact=True, land=True),
            make_card("g", "Goldmire Bridge", artifact=True, land=True),
        ]
        self.assertEqual(self.root(state).label, "Play Ancient Den")

    def test_future_color_does_not_reverse_immediate_tempo(self):
        state = state_with_lands(self.deck, [])
        state.turn = 1
        state.hand = [
            make_card("d", "Ancient Den", artifact=True, land=True),
            make_card("m", "Mistvault Bridge", artifact=True, land=True),
            make_card("s", "Baleful Strix", artifact=True, creature=True),
        ]
        self.assertEqual(self.root(state).label, "Play Ancient Den")

    def test_equal_functionality_tie_is_order_invariant(self):
        labels = []
        cards = [
            make_card("d", "Ancient Den", artifact=True, land=True),
            make_card("f", "Great Furnace", artifact=True, land=True),
        ]
        for hand in (cards, list(reversed(cards))):
            state = state_with_lands(self.deck, [])
            state.hand = list(hand)
            labels.append(self.root(state).label)
        self.assertEqual(labels[0], labels[1])


if __name__ == "__main__":
    unittest.main()
