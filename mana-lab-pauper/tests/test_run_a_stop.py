import inspect
import unittest

from mana_lab import cli
from mana_lab.cards import load_yaml
from mana_lab.metrics import OVERLAP_FAMILIES, SmokeAggregator
from mana_lab.validation import run_a
from common import ROOT


class RunAStopTests(unittest.TestCase):
    def test_config_hard_stop_flags(self):
        config = load_yaml(ROOT / "configs" / "experiments" / "Strixpatch_Affinity_v1.3.experiment.yaml")
        phase = config["phase_control"]
        self.assertFalse(phase["optimization_execution_allowed"])
        self.assertFalse(phase["exhaustive_candidate_simulation_allowed"])
        self.assertFalse(phase["finalist_selection_allowed"])
        self.assertFalse(phase["optimality_label_allowed"])
        self.assertEqual(config["search"]["screening"]["trials_per_candidate"], 0)

    def test_cli_exposes_no_optimization_command(self):
        source = inspect.getsource(cli.main)
        self.assertNotIn('add_parser("optimize"', source)
        self.assertNotIn('add_parser("screen"', source)

    def test_no_opaque_master_score_and_overlap_registry_complete(self):
        expected = {
            "spell_miss_etb_unavailable",
            "color_and_castability",
            "boulder_and_castability",
            "artifact_affinity_metalcraft",
            "metalcraft_full_effect",
            "mulligan_early_castability",
        }
        self.assertEqual(set(OVERLAP_FAMILIES), expected)
        self.assertFalse(hasattr(SmokeAggregator(), "score"))

    def test_historical_c1_has_no_priority_flag(self):
        config = load_yaml(ROOT / "configs" / "experiments" / "Strixpatch_Affinity_v1.3.experiment.yaml")
        rules = " ".join(config["search"]["protected_candidate_rules"])
        self.assertIn("regression fixture only", rules)
        self.assertNotIn("preferred", rules.lower())

    def test_no_fixed_opponent_scalar_or_generic_tapland_score_in_source(self):
        source = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "src" / "mana_lab").glob("*.py"))
        self.assertNotIn("0.55", source)
        self.assertNotIn("tapland_penalty", source)
        self.assertNotIn("master_score", source)


if __name__ == "__main__":
    unittest.main()

