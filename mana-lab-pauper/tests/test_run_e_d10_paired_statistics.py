import math
import unittest

from mana_lab.statistics import TrialObservation, paired_difference


def obs(trial, value, **updates):
    fields = dict(scenario="mixed|baseline", replicate=17, trial=trial, on_play=trial % 2 == 0, value=value)
    fields.update(updates)
    return TrialObservation(**fields)


class KeyedPairedStatisticsTests(unittest.TestCase):
    def test_closed_form_mean_se_and_ci(self):
        left = [obs(0, 2), obs(1, 4), obs(2, 6)]
        right = [obs(0, 1), obs(1, 2), obs(2, 3)]
        result = paired_difference(left, right)
        self.assertAlmostEqual(result.mean, 2.0)
        self.assertAlmostEqual(result.standard_error, 1 / math.sqrt(3))
        self.assertAlmostEqual(result.ci_low, 2 - 1.96 / math.sqrt(3))
        self.assertEqual(result.pairing_mode, "keyed")

    def test_shuffled_or_mismatched_identity_is_rejected(self):
        left = [obs(0, 1), obs(1, 2)]
        with self.assertRaises(ValueError):
            paired_difference(left, [obs(1, 1), obs(0, 2)])
        with self.assertRaises(ValueError):
            paired_difference(left, [obs(0, 1, scenario="other"), obs(1, 2)])
        with self.assertRaises(ValueError):
            paired_difference(left, [obs(0, 1, replicate=18), obs(1, 2)])

    def test_duplicate_and_missing_keys_are_rejected(self):
        with self.assertRaises(ValueError):
            paired_difference([obs(0, 1), obs(0, 2)], [obs(0, 0), obs(0, 1)])
        with self.assertRaises(ValueError):
            paired_difference(
                [{"scenario": "x", "replicate": 1, "trial": 0, "on_play": True, "value": 1}],
                [{"scenario": "x", "trial": 0, "on_play": True, "value": 0}],
            )


if __name__ == "__main__":
    unittest.main()
