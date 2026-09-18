import tempfile
import unittest
from pathlib import Path

from mana_lab.cards import load_deck
from mana_lab.phase3_depth import REQUIRED_STRUCTURAL_CLASSES, planner_depth_audit, structural_state_corpus
from mana_lab.phase3_readiness import validate_mechanic_registry
from mana_lab.policies import (
    ALTERNATE_ACTION_POLICY,
    ALTERNATE_RESERVE_POLICY,
    BASELINE_RESERVE_POLICY,
    ActionOption,
    choose_action,
    policy_source_has_candidate_branch,
)
from mana_lab.provenance import source_manifest


ROOT = Path(__file__).resolve().parents[1]


def option(key, reserve):
    return ActionOption(
        key=key, due_executions=0, artifact_count=0, cards_drawn=0,
        reserve_preserved=reserve, untapped_resources=1, land_loss=0,
        spell_executions=1 if key == "tap-out" else 0,
    )


class RunGPolicyMechanicDepthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deck = load_deck(ROOT / "configs/decks/Strixpatch_Affinity_v1.3.deck.yaml")

    def test_true_tap_out_policy_no_longer_selects_reserve_on_equal_resources(self):
        choices = [option("tap-out", False), option("reserve", True)]
        baseline = choose_action(choices, ALTERNATE_ACTION_POLICY, reserve_policy_name=BASELINE_RESERVE_POLICY)
        tap_out = choose_action(choices, ALTERNATE_ACTION_POLICY, reserve_policy_name=ALTERNATE_RESERVE_POLICY)
        self.assertEqual(baseline.key, "reserve")
        self.assertEqual(tap_out.key, "tap-out")

    def test_no_candidate_specific_policy_behavior(self):
        self.assertFalse(policy_source_has_candidate_branch())

    def test_mechanic_registry_has_no_ranking_relevant_gap(self):
        result = validate_mechanic_registry(ROOT / "RUN_G_MECHANICS_COVERAGE.csv")
        self.assertEqual(result["ranking_relevant_gaps"], 0)

    def test_structural_depth_corpus_is_complete_and_stable(self):
        corpus = structural_state_corpus(self.deck)
        self.assertEqual({name for name, _ in corpus}, REQUIRED_STRUCTURAL_CLASSES)
        audit = planner_depth_audit(self.deck)
        self.assertTrue(audit["pass"])
        self.assertTrue(audit["reserve_sensitivity"]["both_executable"])

    def test_source_manifest_excludes_caches_and_is_order_stable(self):
        first = source_manifest(ROOT)
        second = source_manifest(ROOT)
        self.assertEqual(first, second)
        self.assertFalse(any("__pycache__" in path or path.endswith(".pyc") for path in first))


if __name__ == "__main__":
    unittest.main()

