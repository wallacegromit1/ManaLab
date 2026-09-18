import copy
import json
import random
import unittest

from mana_lab.cards import COLORS
from mana_lab.mana import ManaCost
from mana_lab.metrics import OBJECTIVE_COMPONENT_REGISTRY, RAW_EVENT_CONTRACT, objective_components, pareto_dominates, profile_regret
from mana_lab.mulligan import BASELINE_MULLIGAN, should_keep
from mana_lab.payment import enumerate_payment_plans, execute_payment
from mana_lab.policies import BASELINE_ACTION_POLICY, BASELINE_SCRY_POLICY
from mana_lab.simulator import (
    apply_planner_action,
    choose_next_action,
    generate_legal_actions,
    record_spell_windows,
    record_timing_snapshot,
    simulate_trial,
)
from mana_lab.state import GameState, Permanent, make_card
from mana_lab.statistics import paired_difference, replicate_identifier, validate_seed_partition
from common import deck_spec, state_with_lands


class RunCMetricAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def _land_action(self, state, name):
        return next(action for action in generate_legal_actions(state, self.deck) if action.kind == "land" and action.label == f"Play {name}")

    def test_bridge_event_records_actual_block(self):
        state = GameState(
            hand=[make_card("g", "Goldmire Bridge", artifact=True, land=True), make_card("f", "Blood Fountain", artifact=True)],
            phase="main", turn=1,
        )
        apply_planner_action(state, self.deck, self._land_action(state, "Goldmire Bridge"), scry_policy_name=BASELINE_SCRY_POLICY, reveal_information=True)
        event = next(event for event in state.events if event["event"] == "etb_tempo")
        self.assertTrue(event["blocked_action"])
        self.assertFalse(event["slack_window"])

    def test_bridge_event_records_slack_window(self):
        state = GameState(hand=[make_card("g", "Goldmire Bridge", artifact=True, land=True)], phase="main", turn=1)
        apply_planner_action(state, self.deck, self._land_action(state, "Goldmire Bridge"), scry_policy_name=BASELINE_SCRY_POLICY, reveal_information=True)
        event = next(event for event in state.events if event["event"] == "etb_tempo")
        self.assertFalse(event["blocked_action"])
        self.assertTrue(event["slack_window"])

    def test_boulder_rescue_is_stored_in_raw_event(self):
        state = state_with_lands(self.deck, ["Ancient Den"])
        state.battlefield.append(Permanent(make_card("b", "Giant's Boulder", artifact=True)))
        plan = next(plan for plan in enumerate_payment_plans(state, ManaCost(colored={"R": 1})) if any(use.via_boulder for use in plan.uses))
        execute_payment(state, plan)
        event = next(event for event in state.events if event["event"] == "boulder_filter")
        self.assertTrue(event["rescue"])
        self.assertEqual(event["net_mana"], 0)

    def test_boulder_not_rescue_when_native_payment_exists(self):
        state = state_with_lands(self.deck, ["Great Furnace"])
        state.battlefield.append(Permanent(make_card("b", "Giant's Boulder", artifact=True)))
        filtered = next(plan for plan in enumerate_payment_plans(state, ManaCost(colored={"R": 1})) if any(use.via_boulder for use in plan.uses))
        execute_payment(state, filtered)
        self.assertFalse(next(event for event in state.events if event["event"] == "boulder_filter")["rescue"])

    def test_snapshot_is_before_spending_and_contains_joint_access(self):
        state = state_with_lands(self.deck, ["Seat of the Synod", "Vault of Whispers"])
        state.turn = 2
        snapshot = record_timing_snapshot(state, self.deck, "start_own_main")
        self.assertEqual(snapshot["usable_untapped_mana"], 2)
        self.assertTrue(snapshot["joint_UB"])
        self.assertEqual(set(snapshot["direct_colors"]), {"U", "B"})

    def test_snapshot_filtered_colors_exclude_colorless(self):
        state = state_with_lands(self.deck, ["Ancient Den"])
        state.battlefield.append(Permanent(make_card("b", "Giant's Boulder", artifact=True)))
        snapshot = record_timing_snapshot(state, self.deck, "fixture")
        self.assertEqual(set(snapshot["available_filtered_colors"]), set("WUBRG"))

    def test_opponent_event_distinguishes_spent_from_never_payable(self):
        _, events = simulate_trial(
            self.deck, dict(self.deck.current_mana_base), candidate_label="C0", scenario_label="event-fixture",
            trial=0, seed=2026091702, on_play=True, mulligan_policy="baseline_functional_london",
            sequencing_policy="baseline_hand_demand",
        )
        windows = [event for event in events if event["event"] == "opponent_window"]
        self.assertTrue(windows)
        for event in windows:
            if event["resource_spent"]:
                self.assertTrue(event["payable_before_own_turn_spending"])
                self.assertFalse(event["payable"])

    def test_spell_failure_reason_total_mana(self):
        state = state_with_lands(self.deck, ["Seat of the Synod"])
        state.turn = 2
        state.hand = [make_card("s", "Baleful Strix", artifact=True, creature=True)]
        record_spell_windows(state, self.deck, "fixture")
        event = next(event for event in state.events if event["event"] == "spell_window")
        self.assertFalse(event["castable"])
        self.assertEqual(event["failure_reason"], "total_mana")

    def test_spell_failure_reason_tapped_resource(self):
        state = state_with_lands(self.deck, ["Seat of the Synod", "Vault of Whispers"])
        state.battlefield[1].tapped = True
        state.turn = 2
        state.hand = [make_card("s", "Baleful Strix", artifact=True, creature=True)]
        record_spell_windows(state, self.deck, "fixture")
        event = next(event for event in state.events if event["event"] == "spell_window")
        self.assertEqual(event["failure_reason"], "tapped_resource")

    def test_metric_event_contract_has_all_major_families(self):
        expected = {"opening_hand", "state_snapshot", "spell_window", "etb_tempo", "multi_action_window", "boulder_filter", "bargain_cast", "glint_hawk_return", "opponent_window"}
        self.assertEqual(set(RAW_EVENT_CONTRACT), expected)
        for definition in RAW_EVENT_CONTRACT.values():
            self.assertTrue(definition["denominator"])
            self.assertTrue(definition["timing"])

    def test_objective_registry_supports_leave_one_out_and_decorrelation(self):
        left = objective_components(leave_out="boulder_rescue")
        self.assertNotIn("boulder_rescue", left)
        self.assertLessEqual(len(objective_components(decorrelated=True)), len(OBJECTIVE_COMPONENT_REGISTRY))

    def test_pareto_and_regret_helpers_do_not_select_winner(self):
        self.assertTrue(pareto_dominates({"a": 2, "b": 1}, {"a": 1, "b": 1}, ["a", "b"]))
        self.assertAlmostEqual(profile_regret({"balanced": 0.8}, {"balanced": 1.0})["balanced"], 0.2)


class RunCStatisticsTests(unittest.TestCase):
    def test_paired_difference_known_fixture(self):
        result = paired_difference([1, 0, 1, 1], [0, 0, 1, 0])
        self.assertEqual(result.trials, 4)
        self.assertAlmostEqual(result.mean, 0.5)
        self.assertLess(result.ci_low, result.mean)
        self.assertGreater(result.ci_high, result.mean)

    def test_single_pair_zero_standard_error(self):
        result = paired_difference([1], [0])
        self.assertEqual(result.standard_error, 0.0)
        self.assertEqual((result.ci_low, result.ci_high), (1.0, 1.0))

    def test_pairing_rejects_unmatched_trials(self):
        with self.assertRaises(ValueError):
            paired_difference([1, 2], [1])

    def test_seed_partition_and_replicate_ids(self):
        self.assertTrue(validate_seed_partition(1, 2, [3, 4, 5]))
        self.assertFalse(validate_seed_partition(1, 2, [2, 3]))
        self.assertEqual(replicate_identifier(7, "play", 9), "seed=7|scenario=play|trial=9")


class RunCPermutationAndMulliganTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def _selected(self, state):
        action = choose_next_action(state, self.deck, action_policy_name=BASELINE_ACTION_POLICY, scry_policy_name=BASELINE_SCRY_POLICY)
        return None if action is None else action.label

    def test_land_order_permutation_invariance(self):
        selected = []
        for names in (["Seat of the Synod", "Great Furnace"], ["Great Furnace", "Seat of the Synod"]):
            state = state_with_lands(self.deck, list(names))
            state.turn = 2
            state.hand = [make_card("n", "Nihil Spellbomb", artifact=True), make_card("g", "Galvanic Blast")]
            selected.append(self._selected(state))
        self.assertEqual(selected[0], selected[1])

    def test_battlefield_permutation_invariance_same_uids(self):
        state = state_with_lands(self.deck, ["Seat of the Synod", "Great Furnace"])
        state.turn = 2
        state.hand = [make_card("n", "Nihil Spellbomb", artifact=True), make_card("g", "Galvanic Blast")]
        other = copy.deepcopy(state)
        other.battlefield.reverse()
        self.assertEqual(self._selected(state), self._selected(other))

    def test_hand_permutation_invariance(self):
        cards = [make_card("n", "Nihil Spellbomb", artifact=True), make_card("f", "Refurbished Familiar", artifact=True, creature=True)]
        values = []
        for order in (cards, list(reversed(cards))):
            state = state_with_lands(self.deck, ["Seat of the Synod", "Vault of Whispers"])
            state.turn = 2
            state.hand = copy.deepcopy(order)
            values.append(self._selected(state))
        self.assertEqual(values[0], values[1])

    def test_random_permutations_stable(self):
        base = state_with_lands(self.deck, ["Ancient Den", "Seat of the Synod", "Great Furnace"])
        base.turn = 2
        base.hand = [make_card("n", "Nihil Spellbomb", artifact=True), make_card("g", "Galvanic Blast"), make_card("d", "Dispatch")]
        expected = self._selected(base)
        rng = random.Random(17)
        for _ in range(10):
            state = copy.deepcopy(base)
            rng.shuffle(state.battlefield)
            rng.shuffle(state.hand)
            self.assertEqual(self._selected(state), expected)

    def test_boulder_not_free_mana_in_mulligan(self):
        hand = [
            make_card("m", "Mistvault Bridge", artifact=True, land=True), make_card("r", "Razortide Bridge", artifact=True, land=True),
            make_card("b", "Giant's Boulder", artifact=True), make_card("s", "Baleful Strix", artifact=True, creature=True),
            make_card("t", "Thoughtcast"), make_card("h", "Glint Hawk", creature=True), make_card("e", "Myr Enforcer", artifact=True, creature=True),
        ]
        self.assertFalse(should_keep(hand, 7, self.deck, BASELINE_MULLIGAN))

    def test_bridge_plus_untapped_land_is_functional_keep(self):
        hand = [
            make_card("m", "Mistvault Bridge", artifact=True, land=True), make_card("d", "Ancient Den", artifact=True, land=True),
            make_card("b", "Giant's Boulder", artifact=True), make_card("s", "Baleful Strix", artifact=True, creature=True),
            make_card("t", "Thoughtcast"), make_card("h", "Glint Hawk", creature=True), make_card("e", "Myr Enforcer", artifact=True, creature=True),
        ]
        self.assertTrue(should_keep(hand, 7, self.deck, BASELINE_MULLIGAN))


if __name__ == "__main__":
    unittest.main()
