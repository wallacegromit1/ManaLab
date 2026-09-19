import json
import tempfile
import unittest
from pathlib import Path

from mana_lab.metrics import MetricEvidence, pareto_dominates, uncertainty_aware_dominance
from mana_lab.phase3_config import load_phase3_config
from mana_lab.phase3_pipeline import Phase3Pipeline, safe_screen_decision


ROOT = Path(__file__).resolve().parents[1]


class RunGDominanceTests(unittest.TestCase):
    def test_exact_dominance(self):
        result = uncertainty_aware_dominance({
            "high": MetricEvidence("higher", True, 2.0, materiality_tolerance=0.5),
            "low": MetricEvidence("lower", True, -1.0, materiality_tolerance=0.5),
        })
        self.assertEqual(result.status, "dominates")

    def test_practical_equivalence(self):
        result = uncertainty_aware_dominance({
            "m": MetricEvidence("higher", True, 0.003, no_worse_tolerance=0.005, materiality_tolerance=0.01)
        })
        self.assertEqual(result.status, "practically_equivalent")

    def test_stochastic_overlap_is_unresolved(self):
        result = uncertainty_aware_dominance({
            "m": MetricEvidence("higher", False, 0.02, -0.01, 0.05, 0.005, 0.01)
        })
        self.assertEqual(result.status, "unresolved")

    def test_missing_uncertainty_is_unresolved(self):
        result = uncertainty_aware_dominance({"m": MetricEvidence("higher", False, 1.0)})
        self.assertEqual(result.status, "unresolved")

    def test_lower_is_better_run_f_counterexample_no_longer_dominates(self):
        self.assertFalse(pareto_dominates({"unused_mana": 5.0}, {"unused_mana": 1.0}, ["unused_mana"]))

    def test_screening_never_eliminates_protected_low_n_or_uncertain(self):
        dominant = uncertainty_aware_dominance({
            "m": MetricEvidence("higher", False, 0.05, 0.04, 0.06, 0.005, 0.01)
        })
        unresolved = uncertainty_aware_dominance({
            "m": MetricEvidence("higher", False, 0.0, -0.02, 0.02, 0.005, 0.01)
        })
        self.assertEqual(safe_screen_decision("C0", dominant, protected_candidates={"C0"}, trials=999, minimum_trials=100), "RETAIN_PROTECTED")
        self.assertEqual(safe_screen_decision("X", dominant, protected_candidates={"C0"}, trials=10, minimum_trials=100), "RETAIN_INSUFFICIENT_EVIDENCE")
        self.assertEqual(safe_screen_decision("X", unresolved, protected_candidates={"C0"}, trials=999, minimum_trials=100), "RETAIN_UNRESOLVED_OR_NONDOMINATED")


class RunGPipelineDryRunTests(unittest.TestCase):
    def setUp(self):
        self.config = load_phase3_config(ROOT / "RUN_G_PHASE3_FROZEN_CONFIG.yaml")

    def test_complete_dry_run_is_reproducible_and_noninferential(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            a = Phase3Pipeline(ROOT, self.config, first).run_readiness_dry_run()
            b = Phase3Pipeline(ROOT, self.config, second).run_readiness_dry_run()
            self.assertEqual(a["manifest_hash"], b["manifest_hash"])
            self.assertFalse(a["ranking_produced"])
            self.assertFalse(a["recommendation_produced"])
            final = json.loads((Path(first) / "09_report.json").read_text())
            self.assertIn("candidate_id", final["output_schema_fields"])
            self.assertIn("policy_hash", final["output_schema_fields"])
            self.assertIn("seed_partition", final["output_schema_fields"])

    def test_run_i_real_entrypoint_exercises_machinery_without_optimization(self):
        # Run H H-01 supersedes the Run G unconditional failure expectation.
        # The entrypoint now executes only a candidate-neutral/C0-equivalent
        # machinery fixture and must never emit a ranking or recommendation.
        with tempfile.TemporaryDirectory() as output:
            result = Phase3Pipeline(ROOT, self.config, output).run_real()
            self.assertEqual(result["status"], "PASS")
            self.assertFalse(result["ranking_produced"])
            self.assertFalse(result["recommendation_produced"])

            root = Path(output)
            for name, stage in (
                ("03_trial_events.jsonl", "03_screen"),
                ("07_robustness_events.jsonl", "07_robustness"),
            ):
                record = json.loads((root / f"{stage}.json").read_text())
                self.assertEqual(record["payload"]["raw_event_payload"]["file"], name)
                self.assertTrue((root / name).read_bytes())
            # Reuse must validate raw scientific evidence, not just stage hashes.
            event_path = root / "03_trial_events.jsonl"
            event_path.write_text(event_path.read_text() + "{}\n")
            with self.assertRaisesRegex(RuntimeError, "tampered raw-event payload"):
                Phase3Pipeline(ROOT, self.config, output).stage_04_medium()


if __name__ == "__main__":
    unittest.main()

