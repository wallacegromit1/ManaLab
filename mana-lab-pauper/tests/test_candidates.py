import unittest

from mana_lab.candidates import candidate_count_report
from mana_lab.validation import EXPECTED_HISTOGRAM, validate_candidate_report
from common import deck_spec


class CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = candidate_count_report(deck_spec())

    def test_independent_counts(self):
        self.assertEqual(self.report["enumeration_count"], 296706)
        self.assertEqual(self.report["dp_count"], 296706)

    def test_boundaries_and_histogram(self):
        self.assertEqual(self.report["minimum_bridges"], 3)
        self.assertEqual(self.report["three_bridge_candidates"], 56)
        self.assertEqual(self.report["bridge_histogram"], EXPECTED_HISTOGRAM)

    def test_invariants_and_c0(self):
        self.assertEqual(self.report["unique_keys"], 296706)
        self.assertEqual(self.report["c0_occurrences"], 1)
        validate_candidate_report(self.report)


if __name__ == "__main__":
    unittest.main()

