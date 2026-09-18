import unittest

from mana_lab.statistics import at_least_one, hypergeometric_pmf, joint_presence_two_sets
from mana_lab.simulator import _joint_ub
from mana_lab.state import make_card
from mana_lab.validation import deterministic_checks
from common import deck_spec


class ExactChecksTests(unittest.TestCase):
    def test_raw_seven_distribution(self):
        expected = [
            0.058212162537,
            0.221206217641,
            0.331809326462,
            0.254088222966,
            0.106984514933,
            0.024688734215,
            0.002880352325,
            0.000130468921,
        ]
        actual = [hypergeometric_pmf(60, 19, 7, lands) for lands in range(8)]
        for value, target in zip(actual, expected):
            self.assertAlmostEqual(value, target, places=12)
        self.assertAlmostEqual(sum(actual), 1.0, places=12)

    def test_direct_source_presence(self):
        self.assertAlmostEqual(at_least_one(60, 5, 7), 0.474562172527, places=12)
        self.assertAlmostEqual(at_least_one(60, 7, 7), 0.600879549232, places=12)
        self.assertAlmostEqual(at_least_one(60, 4, 7), 0.399499625745, places=12)
        self.assertAlmostEqual(joint_presence_two_sets(60, 7, 7, 2, 7), 0.392405791175, places=12)

    def test_joint_ub_fixture_is_presence_not_two_mana_payment(self):
        hand = [make_card("m", "Mistvault Bridge", artifact=True, land=True)]
        self.assertTrue(_joint_ub(hand, deck_spec()))

    def test_c0_source_facts(self):
        result = deterministic_checks(deck_spec())
        self.assertTrue(result["acceptance"]["c0_facts_match"])
        self.assertEqual(result["c0"]["direct_sources"], {"W": 5, "U": 7, "B": 7, "R": 4})


if __name__ == "__main__":
    unittest.main()
