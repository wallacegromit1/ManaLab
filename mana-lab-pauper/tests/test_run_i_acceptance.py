import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mana_lab.metrics import MetricEvidence, uncertainty_aware_dominance
from mana_lab.phase3_config import load_phase3_config, scientific_config_hash, validate_phase3_config
from mana_lab.phase3_metrics import aggregate_trial_events, evaluate_critical_sequences, validate_event_stream
from mana_lab.phase3_pipeline import Phase3Pipeline, safe_screen_decision
from mana_lab.phase3_policies import validate_policy_freeze
from mana_lab.statistics import TrialObservation, paired_difference

ROOT = Path(__file__).resolve().parents[1]


def ev(i, kind, turn=0, **kw):
    row = dict(event_id=i, event=kind, turn=turn, scenario="run-i-test",
               replicate=1, trial_id=0, on_play=True)
    row.update(kw)
    return row


class RunIAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.config = load_phase3_config(ROOT / "RUN_G_PHASE3_FROZEN_CONFIG.yaml")

    def test_control_metadata_is_not_scientific_identity(self):
        changed = copy.deepcopy(self.config)
        changed["phase_control"]["authorization_status"] = "SYNTHETIC_CONTROL_TOGGLE"
        changed["phase_control"]["optimization_execution_allowed"] = True
        self.assertEqual(scientific_config_hash(self.config), scientific_config_hash(changed))

    def test_config_adversarial_mutations_fail_closed(self):
        mutations = [
            lambda c: c["scenarios"].__setitem__("planner_search_depth", 0),
            lambda c: c["trial_plan"].__setitem__("validation_adaptive_batch", 0),
            lambda c: c["candidate_space"]["c0"].__setitem__("Ancient Den", 99),
            lambda c: c["scenarios"]["primary_play_draw"][0].__setitem__("weight", -1),
            lambda c: c["decision_profiles"]["balanced"]["metric_vector"][0].__setitem__("metric", "invented"),
            lambda c: c["decision_profiles"]["balanced"]["metric_vector"][0].__setitem__("materiality_tolerance", -1),
            lambda c: c["input"]["parent_archive"].__setitem__("sha256", "0" * 64),
            lambda c: c["robustness_scenarios"][0].__setitem__("sequencing", "unknown"),
        ]
        for mutate in mutations:
            broken = copy.deepcopy(self.config)
            mutate(broken)
            with self.assertRaises(ValueError):
                validate_phase3_config(broken, ROOT)

    def test_policy_role_kind_and_runtime_replacement_reject(self):
        broken = copy.deepcopy(self.config["policies"])
        broken["identities"]["sequencing_baseline"] = copy.deepcopy(
            broken["identities"]["scry_baseline"]
        )
        with self.assertRaisesRegex(ValueError, "role-kind"):
            validate_policy_freeze(broken)
        import mana_lab.policies as policies
        with patch.object(policies, "choose_action", lambda options, *a, **k: list(options)[-1]):
            with self.assertRaisesRegex(ValueError, "executable binding drift"):
                validate_policy_freeze(self.config["policies"])

    def test_uncertainty_contracts_reject_bad_intervals_and_wide_equivalence(self):
        with self.assertRaises(ValueError):
            uncertainty_aware_dominance({"m": MetricEvidence("higher", False, .2, .4, .1)})
        with self.assertRaises(ValueError):
            uncertainty_aware_dominance({"m": MetricEvidence("higher", True, float("nan"))})
        result = uncertainty_aware_dominance({
            "m": MetricEvidence("higher", False, .1, -.001, .8, .0025, .005)
        })
        self.assertEqual(result.status, "unresolved")

    def test_event_identity_deadlines_and_sequence_isolation(self):
        with self.assertRaises(ValueError):
            validate_event_stream([{"event_id": 1, "event": "opening_hand"}])
        opening = ev(1, "opening_hand", opening_land_count=2, mulligans=0, keep_size=7)
        with self.assertRaises(ValueError):
            aggregate_trial_events([opening])
        strix_t1 = ev(2, "spell_resolution", 1, card="Baleful Strix", uid="s", functional=True)
        self.assertTrue(evaluate_critical_sequences([strix_t1])["T2_STRIX_UB"])
        late = [
            ev(2, "spell_resolution", 2, card="Cryogen Relic", uid="c", functional=True),
            ev(3, "draw", 4, reason="Cryogen Relic enter draw"),
        ]
        self.assertFalse(evaluate_critical_sequences(late)["T2_CRYOGEN"])
        mixed = [
            ev(2, "spell_resolution", 4, card="Glint Hawk", uid="h", functional=True),
            dict(ev(3, "spell_resolution", 4, card="Nihil Spellbomb", uid="n", functional=True),
                 scenario="other"),
        ]
        self.assertFalse(evaluate_critical_sequences(mixed)["T4_DOUBLE_SPELL"])

    def test_paired_keys_still_fail_closed(self):
        left = [TrialObservation("s", 1, 0, True, .5)]
        right = [TrialObservation("s", 1, 1, True, .5)]
        with self.assertRaises(ValueError):
            paired_difference(left, right)

    def test_intrinsic_protections_do_not_depend_on_caller_set(self):
        dominant = uncertainty_aware_dominance({
            "m": MetricEvidence("higher", True, 1.0, materiality_tolerance=.1)
        })
        self.assertEqual(
            safe_screen_decision("C0", dominant, protected_candidates=set(),
                                 trials=1000, minimum_trials=1),
            "RETAIN_PROTECTED",
        )
        self.assertEqual(
            safe_screen_decision("boundary", dominant, protected_candidates=set(),
                                 trials=1000, minimum_trials=1, bridge_count=3),
            "RETAIN_PROTECTED",
        )

    def test_forged_prerequisite_rejected(self):
        with tempfile.TemporaryDirectory() as output:
            p = Phase3Pipeline(ROOT, self.config, output)
            Path(output, "03_screen.json").write_text(json.dumps({
                "stage": "03_screen", "status": "PASS",
                "artifact_content_hash": "FORGED",
            }))
            with self.assertRaises(RuntimeError):
                p.stage_04_medium()


if __name__ == "__main__":
    unittest.main()
