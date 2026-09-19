"""Hand-calculated play/draw population and paired inference tests (Run I)."""
import unittest

from mana_lab.phase3_profiles import aggregate_profile_events, compare_profile_trials
from mana_lab.statistics import TrialObservation, stratified_paired_difference


PROFILE = {
    "metric_vector": [{
        "metric": "usable_untapped_mana_by_turn",
        "direction": "higher",
        "aggregation": "turn-weighted mean with weights T1=.25 T2=.75",
        "turns": [1, 2],
        "scenarios": ["weighted_primary"],
        "no_worse_tolerance": .0025,
        "materiality_tolerance": .005,
        "normalization": "none",
        "missing_data": "error",
    }],
}


def trial(*, on_play, trial_id, turn1, turn2, candidate="fixture"):
    fields = dict(scenario="baseline_primary", replicate=1,
                  trial_id=trial_id, on_play=on_play, candidate=candidate)
    return [
        dict(fields, event_id=1, event="opening_hand", turn=0),
        dict(fields, event_id=2, event="state_snapshot", turn=1,
             event_role="primary_pre_spend_opportunity",
             usable_untapped_mana=turn1),
        dict(fields, event_id=3, event="state_snapshot", turn=2,
             event_role="primary_pre_spend_opportunity",
             usable_untapped_mana=turn2),
    ]


class RunIWeightedPopulationTests(unittest.TestCase):
    def test_explicit_play_draw_weight_changes_raw_profile_outcome(self):
        play = trial(on_play=True, trial_id=0, turn1=1, turn2=3)
        draw = trial(on_play=False, trial_id=1, turn1=5, turn2=7)
        raw_play = .25 * 1 + .75 * 3
        raw_draw = .25 * 5 + .75 * 7
        weighted = aggregate_profile_events(
            PROFILE, [play, draw], play_draw_weights={True: .75, False: .25},
        )
        self.assertAlmostEqual(weighted[0].value, .75 * raw_play + .25 * raw_draw)
        equally_weighted = aggregate_profile_events(
            PROFILE, [play, draw], play_draw_weights={True: .5, False: .5},
        )
        self.assertNotEqual(weighted[0].value, equally_weighted[0].value)
        self.assertAlmostEqual(aggregate_profile_events(PROFILE, [play])[0].value, raw_play)

    def test_missing_or_invalid_population_does_not_silently_reweight(self):
        play = trial(on_play=True, trial_id=0, turn1=1, turn2=3)
        with self.assertRaisesRegex(ValueError, "missing"):
            aggregate_profile_events(
                PROFILE, [play], play_draw_weights={True: .5, False: .5},
            )
        with self.assertRaisesRegex(ValueError, "sum to one"):
            aggregate_profile_events(
                PROFILE, [play], play_draw_weights={True: .9, False: .9},
            )
        with self.assertRaisesRegex(ValueError, "boolean"):
            aggregate_profile_events(PROFILE, [play], play_draw_weights={"play": 1.0})

    def test_hand_calculated_stratified_paired_estimate_and_alignment(self):
        left = [
            TrialObservation("s", 1, i, i < 4, 10.0 if i < 4 else 0.0, "A")
            for i in range(8)
        ]
        right = [
            TrialObservation("s", 1, i, i < 4, 8.0 if i < 4 else 2.0, "B")
            for i in range(8)
        ]
        estimate = stratified_paired_difference(
            left, right, on_play_weights={True: .75, False: .25},
        )
        self.assertAlmostEqual(estimate.mean_difference, .75 * 2 + .25 * -2)
        self.assertEqual(estimate.pairing_mode, "keyed_stratified_play_draw")
        with self.assertRaisesRegex(ValueError, "missing"):
            stratified_paired_difference(
                left[:4], right[:4], on_play_weights={True: .5, False: .5},
            )
        with self.assertRaisesRegex(ValueError, "aligned"):
            stratified_paired_difference(
                left, right[::-1], on_play_weights={True: .5, False: .5},
            )

    def test_profile_comparison_exposes_weighted_paired_difference(self):
        left = [
            trial(on_play=i < 2, trial_id=i, turn1=2 if i < 2 else 0,
                  turn2=2 if i < 2 else 0, candidate="A")
            for i in range(4)
        ]
        right = [
            trial(on_play=i < 2, trial_id=i, turn1=0 if i < 2 else 2,
                  turn2=0 if i < 2 else 2, candidate="B")
            for i in range(4)
        ]
        comparisons = compare_profile_trials(
            PROFILE, left, right, play_draw_weights={True: .75, False: .25},
        )
        self.assertAlmostEqual(comparisons[0].paired.mean_difference, 1.0)
        self.assertEqual(comparisons[0].paired.pairing_mode, "keyed_stratified_play_draw")


if __name__ == "__main__":
    unittest.main()
