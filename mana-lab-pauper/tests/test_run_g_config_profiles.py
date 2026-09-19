import copy
import unittest
from pathlib import Path

from mana_lab.phase3_config import load_phase3_config, validate_phase3_config
from mana_lab.phase3_policies import POLICY_REGISTRY, validate_policy_freeze
from mana_lab.phase3_profiles import (
    compare_profile_vectors,
    decorrelated_profile,
    evaluate_profile,
    leave_one_component_out,
)


ROOT = Path(__file__).resolve().parents[1]


class RunGConfigAndProfileTests(unittest.TestCase):
    def setUp(self):
        self.config = load_phase3_config(ROOT / "RUN_G_PHASE3_FROZEN_CONFIG.yaml")

    def test_concrete_config_has_no_behavior_placeholders(self):
        validate_phase3_config(self.config, ROOT)
        self.assertGreater(self.config["trial_plan"]["screening_trials_per_candidate"], 0)
        self.assertGreater(self.config["trial_plan"]["validation_trials_per_candidate"], 0)

    def test_seed_partitions_are_independent(self):
        random = self.config["randomness"]
        values = [random["selection_seed"], random["validation_seed"], *random["replicate_seeds"]]
        self.assertEqual(len(values), len(set(values)))

    def test_validation_seed_collision_rejected(self):
        broken = copy.deepcopy(self.config)
        broken["randomness"]["validation_seed"] = broken["randomness"]["selection_seed"]
        with self.assertRaises(ValueError):
            validate_phase3_config(broken, ROOT)

    def test_policy_hash_drift_aborts(self):
        broken = copy.deepcopy(self.config["policies"])
        broken["identities"]["reserve_alternate"]["content_hash"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "policy hash drift"):
            validate_policy_freeze(broken)

    def test_requested_policy_names_are_all_executable_registry_entries(self):
        for item in self.config["policies"]["identities"].values():
            self.assertIn(item["id"], POLICY_REGISTRY)

    def test_profile_vector_calculation_is_hand_checkable(self):
        profile = self.config["decision_profiles"]["double_spell_sensitive"]
        left = evaluate_profile(profile, {
            "double_spell_success": 0.31,
            "spell_plus_held_interaction_success": 0.22,
        })
        right = evaluate_profile(profile, {
            "double_spell_success": 0.30,
            "spell_plus_held_interaction_success": 0.40,
        })
        self.assertEqual(left[0].metric, "double_spell_success")
        self.assertEqual(left[0].value, 0.31)
        # Run H H-02 supersedes the first-component-wins behavior:
        # materially opposed components must remain an explicit conflict.
        self.assertEqual(compare_profile_vectors(left, right), "conflict")

    def test_missing_profile_metric_is_an_error(self):
        profile = self.config["decision_profiles"]["balanced"]
        with self.assertRaisesRegex(ValueError, "profile metric missing"):
            evaluate_profile(profile, {})

    def test_overlap_metadata_and_sensitivity_variants_exist(self):
        for profile in self.config["decision_profiles"].values():
            self.assertTrue(profile["overlap_rationale"])
            self.assertTrue(decorrelated_profile(profile)["metric_vector"])
            self.assertTrue(leave_one_component_out(profile))


if __name__ == "__main__":
    unittest.main()

