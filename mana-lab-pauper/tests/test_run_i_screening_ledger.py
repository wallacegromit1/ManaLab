"""Candidate-neutral adversarial tests for the reversible screening ledger."""
import unittest

from mana_lab.phase3_screening_ledger import ReversibleScreeningLedger
from mana_lab.statistics import TrialObservation


def samples(candidate, n, *, first=1.0, rest=None, split=None, scenario="fixture"):
    values = [first] * n
    if split is not None:
        values[split:] = [rest] * (n - split)
    return tuple(
        TrialObservation(scenario, 1, index, index % 2 == 0, value, candidate)
        for index, value in enumerate(values)
    )


class ReversibleScreeningLedgerTests(unittest.TestCase):
    def ledger(self, *, minimum=8, max_looks=2):
        return ReversibleScreeningLedger(
            candidate_bridge_counts={"comparator": 4, "candidate": 4, "C0": 4, "bridge": 3},
            protected_candidates={"C0", "bridge"},
            registered_claims=(
                ("comparator", "candidate", "balanced", "castable"),
                ("comparator", "candidate", "tempo", "usable"),
                ("comparator", "C0", "balanced", "castable"),
                ("comparator", "bridge", "balanced", "castable"),
            ),
            family_id="qa-entire-preregistered-family",
            minimum_trials=minimum,
            maximum_looks=max_looks,
        )

    def record(self, ledger, candidate="candidate", profile="balanced", metric="castable",
               n=8, left=None, right=None, look=1, partition="selection"):
        return ledger.record(
            comparator="comparator", candidate=candidate, profile=profile,
            components={metric: (
                samples("comparator", n, first=1.0) if left is None else left,
                samples(candidate, n, first=0.0) if right is None else right,
            )},
            dimensions={metric: ("higher", 0.0025, 0.005)},
            look=look, partition=partition,
        )

    def test_global_disposition_requires_every_registered_profile(self):
        ledger = self.ledger()
        first = self.record(ledger)
        self.assertEqual(first.status, "PAIR_ELIMINATION_SUPPORTED")
        self.assertEqual(ledger.candidate_disposition("candidate"),
                         "RETAIN_PROFILE_CONFLICT_OR_UNRESOLVED")
        self.record(ledger, profile="tempo", metric="usable")
        self.assertEqual(ledger.candidate_disposition("candidate"),
                         "ELIMINATION_SUPPORTED_WITHIN_REGISTERED_FAMILY")

    def test_new_look_can_reverse_previous_pair_elimination(self):
        ledger = self.ledger()
        self.record(ledger)
        self.record(ledger, profile="tempo", metric="usable")
        self.assertEqual(ledger.candidate_disposition("candidate"),
                         "ELIMINATION_SUPPORTED_WITHIN_REGISTERED_FAMILY")
        revised = self.record(
            ledger, look=2, n=16,
            left=samples("comparator", 16, first=1.0, rest=0.0, split=8),
            right=samples("candidate", 16, first=0.0, rest=1.0, split=8),
        )
        self.assertEqual(revised.status, "RETAIN_UNRESOLVED_OR_NONDOMINATED")
        self.assertEqual(ledger.candidate_disposition("candidate"),
                         "RETAIN_PROFILE_CONFLICT_OR_UNRESOLVED")
        self.assertEqual(len(ledger.audit_rows()), 3)
        self.assertEqual(ledger.audit_hash(), ledger.audit_hash())

    def test_protected_and_small_trials_always_retain(self):
        ledger = self.ledger(minimum=512)
        self.assertEqual(self.record(ledger).status, "RETAIN_INSUFFICIENT_EVIDENCE")
        self.assertEqual(self.record(ledger, candidate="C0").status, "RETAIN_PROTECTED")
        self.assertEqual(self.record(ledger, candidate="bridge").status, "RETAIN_PROTECTED")
        self.assertEqual(ledger.candidate_disposition("C0"), "RETAIN_PROTECTED")
        self.assertEqual(ledger.candidate_disposition("bridge"), "RETAIN_PROTECTED")

    def test_production_contract_rejects_bad_family_and_partition(self):
        ledger = self.ledger()
        with self.assertRaisesRegex(ValueError, "validation"):
            self.record(ledger, partition="validation")
        with self.assertRaisesRegex(ValueError, "pre-registered"):
            self.record(ledger, metric="unknown")
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self.record(ledger, right=samples("other", 8))
        with self.assertRaisesRegex(ValueError, "paired observation"):
            self.record(ledger, right=samples("candidate", 7))
        with self.assertRaisesRegex(ValueError, "precision"):
            self.ledger(minimum=1)

    def test_adaptive_look_rejects_replay_or_nonincreasing_sample(self):
        ledger = self.ledger()
        self.record(ledger)
        with self.assertRaisesRegex(ValueError, "out of order"):
            self.record(ledger, look=1)
        with self.assertRaisesRegex(ValueError, "grow"):
            self.record(ledger, look=2, n=8)
        self.record(ledger, look=2, n=16)
        with self.assertRaisesRegex(ValueError, "out of order"):
            self.record(ledger, look=3, n=32)

    def test_family_and_component_identity_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            ReversibleScreeningLedger(
                candidate_bridge_counts={"a": 4, "b": 4},
                protected_candidates=(),
                registered_claims=[("a", "b", "p", "m")] * 2,
                family_id="x", minimum_trials=8, maximum_looks=2,
            )
        ledger = self.ledger()
        with self.assertRaisesRegex(ValueError, "registered comparison"):
            ledger.record(
                comparator="comparator", candidate="candidate",
                profile="not-a-profile", components={"castable": (samples("comparator", 8), samples("candidate", 8))},
                dimensions={"castable": ("higher", 0.0, 0.0)}, look=1,
            )


if __name__ == "__main__":
    unittest.main()
