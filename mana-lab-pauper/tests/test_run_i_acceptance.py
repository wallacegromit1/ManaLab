import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mana_lab.metrics import (
    MetricEvidence, uncertainty_aware_dominance, uncertainty_aware_frontier,
    uncertainty_aware_regret,
)
from mana_lab.phase3_config import load_phase3_config, scientific_config_hash, validate_phase3_config
from mana_lab.phase3_metrics import aggregate_trial_events, evaluate_critical_sequences, validate_event_stream
from mana_lab.phase3_pipeline import Phase3Pipeline, safe_screen_decision
from mana_lab.phase3_profiles import aggregate_profile_events, evaluate_profile
from mana_lab.phase3_model_risk import (
    blood_activation_option, fountain_recursion_resource_bound,
    single_land_removal_sensitivity, target_conditional_activation_options,
)
from mana_lab.phase3_depth import planner_depth_audit
from mana_lab.phase3_policies import validate_policy_freeze
from mana_lab.statistics import (
    PairedEstimate, TrialObservation, adaptive_paired_difference,
    holm_family, paired_difference,
)
from mana_lab.cards import load_deck
from mana_lab.state import GameState, Permanent, make_card

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


    def _profile_trace(self):
        rows = []
        counter = 1
        def add(kind, turn, **kw):
            nonlocal counter
            rows.append(ev(counter, kind, turn, scenario="baseline_primary", **kw))
            counter += 1
        add("opening_hand", 0, opening_land_count=3, mulligans=0, keep_size=7)
        for turn in range(1, 5):
            add("state_snapshot", turn, event_role="primary_pre_spend_opportunity",
                usable_untapped_mana=turn, joint_UB=(turn >= 2), timing="start_own_main")
            add("spell_window", turn, event_role="primary_pre_spend_opportunity",
                opportunity_id=f"spell-{turn}", card="Baleful Strix",
                card_instance=f"strix-{turn}", uid=f"strix-{turn}",
                castable=(turn >= 2), colored_cost={"U": 1, "B": 1},
                weight=1.0, timing="start_own_main", profile="baseline_practical")
            if turn >= 2:
                add("spell_window", turn, event_role="primary_pre_spend_opportunity",
                    opportunity_id=f"aff-{turn}", card="Thoughtcast",
                    card_instance=f"thought-{turn}", uid=f"thought-{turn}",
                    castable=True, colored_cost={"U": 1}, weight=1.0,
                    timing="start_own_main", profile="baseline_practical")
                add("opponent_window", turn, card="Dispatch", interaction_in_hand=True,
                    payable=True, metalcraft=True)
            add("etb_tempo", turn, blocked_action=False)
            add("multi_action_window", turn, timing="start_own_main",
                double_spell_feasible=(turn >= 3),
                spell_plus_interaction_feasible=(turn >= 2))
        add("spell_resolution", 2, card="Cryogen Relic", uid="cry", functional=True)
        add("draw", 2, reason="Cryogen Relic enter draw", source_uid="cry")
        add("spell_resolution", 3, card="Glint Hawk", uid="hawk", functional=True)
        add("glint_hawk_return", 3, card="Cryogen Relic", uid="cry")
        add("draw", 3, reason="Cryogen Relic leave draw", source_uid="cry")
        add("spell_resolution", 4, card="Myr Enforcer", uid="e1", functional=True)
        add("spell_resolution", 4, card="Thoughtcast", uid="t1", functional=True)
        return rows

    def test_every_frozen_profile_executes_from_raw_trace(self):
        trace = self._profile_trace()
        for name, profile in self.config["decision_profiles"].items():
            vector = aggregate_profile_events(profile, [trace])
            self.assertEqual(len(vector), len(profile["metric_vector"]), name)
            self.assertTrue(all(item.population_id for item in vector))
        changed = copy.deepcopy(self.config["decision_profiles"]["tempo_sensitive"])
        original = aggregate_profile_events(
            self.config["decision_profiles"]["tempo_sensitive"], [trace]
        )
        changed["metric_vector"][0]["turns"] = [1, 2]
        changed["metric_vector"][0]["aggregation"] = "turn-weighted mean with weights T1=.8 T2=.2"
        altered = aggregate_profile_events(changed, [trace])
        self.assertNotEqual(original[0].value, altered[0].value)
        self.assertNotEqual(original[0].population_id, altered[0].population_id)

    def test_holm_adaptive_frontier_and_regret_are_uncertainty_aware(self):
        a = [TrialObservation("s", 1, i, True, 1.0 + .1 * i) for i in range(8)]
        b = [TrialObservation("s", 1, i, True, .5 + .1 * i) for i in range(8)]
        estimate = paired_difference(a, b)
        family = holm_family({"a": estimate, "b": estimate}, family_alpha=.05)
        self.assertEqual(len(family), 2)
        adaptive = adaptive_paired_difference(
            a, b, family_alpha=.05, maximum_looks=4, family_size=2
        )
        self.assertGreaterEqual(
            adaptive.confidence_high - adaptive.confidence_low,
            estimate.confidence_high - estimate.confidence_low,
        )
        wide = {
            ("A", "B"): {"m": MetricEvidence("higher", False, .1, -.5, .7, .01, .02)}
        }
        self.assertEqual(uncertainty_aware_frontier(["A", "B"], wide), ("A", "B"))
        regret = uncertainty_aware_regret(
            PairedEstimate(10, -.1, .05, -.2, 0.0, "keyed"), direction="higher"
        )
        self.assertGreaterEqual(regret.point_regret, 0.0)
        self.assertTrue(regret.unresolved)

    def _state_with_lands(self, deck, names):
        state = GameState(phase="main", turn=4)
        for index, name in enumerate(names):
            state.battlefield.append(Permanent(
                make_card(f"land-{index}", name, artifact=True, land=True),
                tapped=False, land_spec=deck.land_by_name[name],
            ))
        return state

    def test_model_risk_resource_and_target_axes_are_executable(self):
        deck = load_deck(ROOT / "configs/decks/Strixpatch_Affinity_v1.3.deck.yaml")
        blood = self._state_with_lands(deck, ["Great Furnace"])
        blood.battlefield.append(
            Permanent(make_card("blood", "Blood", artifact=True), token=True)
        )
        blood.hand = [make_card("discard", "Nihil Spellbomb", artifact=True)]
        option = blood_activation_option(blood, deck)
        self.assertTrue(option.resource_payable)
        self.assertTrue(option.executable)

        target_state = self._state_with_lands(
            deck, ["Seat of the Synod", "Vault of Whispers", "Great Furnace"]
        )
        target_state.battlefield += [
            Permanent(make_card("m", "Makeshift Munitions")),
            Permanent(make_card("c", "Cryogen Relic", artifact=True)),
            Permanent(make_card("s", "Nihil Spellbomb", artifact=True)),
        ]
        absent = target_conditional_activation_options(
            target_state, munitions_target_available=False,
            cryogen_tapped_target_available=False,
        )
        present = target_conditional_activation_options(
            target_state, munitions_target_available=True,
            cryogen_tapped_target_available=True,
        )
        self.assertTrue(absent["munitions"].resource_payable)
        self.assertFalse(absent["munitions"].executable)
        self.assertTrue(present["munitions"].executable)
        self.assertTrue(absent["cryogen"].resource_payable)
        self.assertFalse(absent["cryogen"].executable)
        self.assertTrue(present["cryogen"].executable)

        fountain = self._state_with_lands(
            deck, ["Vault of Whispers", "Seat of the Synod", "Great Furnace", "Ancient Den"]
        )
        fountain.battlefield.append(Permanent(make_card("f", "Blood Fountain", artifact=True)))
        bound = fountain_recursion_resource_bound(fountain)
        self.assertTrue(bound["resource_payable"])
        self.assertTrue(bound["blocking_if_reachable"])

        removal = self._state_with_lands(deck, ["Great Furnace", "Mistvault Bridge"])
        result = {row["land"]: row for row in single_land_removal_sensitivity(removal, deck)}
        self.assertTrue(result["Great Furnace"]["removed"])
        self.assertFalse(result["Mistvault Bridge"]["removed"])

    def test_depth_boundary_stress_reaches_configured_neighborhood(self):
        deck = load_deck(ROOT / "configs/decks/Strixpatch_Affinity_v1.3.deck.yaml")
        audit = planner_depth_audit(deck)
        self.assertTrue(audit["boundary_stress"]["deliberately_truncated_fails"])
        self.assertGreaterEqual(
            audit["boundary_stress"]["deep"]["maximum_sequence_length"], 7
        )
        self.assertGreater(
            audit["boundary_stress"]["shallow"]["stopping_reasons"]["depth_limit"], 0
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
