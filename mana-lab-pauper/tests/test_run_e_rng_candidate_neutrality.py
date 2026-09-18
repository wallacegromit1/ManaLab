import unittest

from mana_lab.simulator import simulate_trial
from common import deck_spec


class RNGCandidateNeutralityTests(unittest.TestCase):
    def test_candidate_label_does_not_change_trial_randomness(self):
        deck = deck_spec()
        kwargs = dict(
            land_counts=dict(deck.current_mana_base), scenario_label="mixed|baseline", trial=3,
            seed=2026091702, on_play=False, mulligan_policy="baseline_functional_london",
            sequencing_policy="baseline_hand_demand",
        )
        left, left_events = simulate_trial(deck, candidate_label="LEFT", **kwargs)
        right, right_events = simulate_trial(deck, candidate_label="RIGHT", **kwargs)
        left.pop("candidate")
        right.pop("candidate")
        self.assertEqual(left, right)
        self.assertEqual(left_events, right_events)


if __name__ == "__main__":
    unittest.main()
