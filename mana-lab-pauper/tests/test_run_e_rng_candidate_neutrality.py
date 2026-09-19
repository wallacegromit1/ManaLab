import unittest
import hashlib

from mana_lab.simulator import _stable_scenario_seed, simulate_trial
from common import deck_spec


class RNGCandidateNeutralityTests(unittest.TestCase):
    def test_rng_matches_frozen_purpose_scenario_replicate_trial_attempt_contract(self):
        payload = b"mulligan_draw|baseline_primary|2026091701|17|2"
        expected = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
        observed = _stable_scenario_seed(2026091701, "baseline_primary", 17, 2)
        self.assertEqual(observed, expected)
        self.assertNotEqual(
            observed,
            _stable_scenario_seed(2026091702, "baseline_primary", 17, 2),
        )
        self.assertNotEqual(
            observed,
            _stable_scenario_seed(2026091701, "baseline_primary", 17, 3),
        )

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
        # Run H H-03 requires candidate identity on every production event.
        # Candidate labels therefore differ as provenance, but must not alter
        # any scientific event content or randomness.
        self.assertEqual({event["candidate"] for event in left_events}, {"LEFT"})
        self.assertEqual({event["candidate"] for event in right_events}, {"RIGHT"})
        left_science = [{k: v for k, v in event.items() if k != "candidate"} for event in left_events]
        right_science = [{k: v for k, v in event.items() if k != "candidate"} for event in right_events]
        self.assertEqual(left_science, right_science)


if __name__ == "__main__":
    unittest.main()
