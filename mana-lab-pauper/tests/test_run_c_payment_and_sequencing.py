import copy
import unittest

from mana_lab.mana import ManaCost
from mana_lab.payment import enumerate_payment_plans, execute_payment
from mana_lab.policies import BASELINE_ACTION_POLICY, BASELINE_SCRY_POLICY, opponent_options
from mana_lab.simulator import enumerate_action_sequences, execute_action_policy
from mana_lab.state import Permanent, make_card
from common import deck_spec, land_permanent, state_with_lands


class RunCPaymentTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def test_generic_payment_preserves_both_colored_alternatives(self):
        state = state_with_lands(self.deck, ["Seat of the Synod", "Great Furnace"])
        plans = enumerate_payment_plans(state, ManaCost(generic=1))
        untapped_sets = set()
        for plan in plans:
            branch = copy.deepcopy(state)
            execute_payment(branch, plan)
            untapped_sets.add(tuple(sorted(p.card.name for p in branch.untapped_lands())))
        self.assertEqual(untapped_sets, {("Great Furnace",), ("Seat of the Synod",)})

    def test_battlefield_permutation_invariance(self):
        outcomes = []
        for names in (["Seat of the Synod", "Great Furnace"], ["Great Furnace", "Seat of the Synod"]):
            state = state_with_lands(self.deck, list(names))
            plans = enumerate_payment_plans(state, ManaCost(generic=1))
            preserved = []
            for plan in plans:
                branch = copy.deepcopy(state)
                execute_payment(branch, plan)
                preserved.append(tuple(sorted(p.card.name for p in branch.untapped_lands())))
            outcomes.append(sorted(preserved))
        self.assertEqual(outcomes[0], outcomes[1])

    def test_native_source_and_boulder_filter_remain_distinct(self):
        state = state_with_lands(self.deck, ["Ancient Den", "Great Furnace"])
        state.battlefield.append(Permanent(make_card("b", "Giant's Boulder", artifact=True)))
        plans = enumerate_payment_plans(state, ManaCost(colored={"R": 1}))
        signatures = {
            (tuple(sorted(use.permanent.card.name for use in plan.uses)), sum(use.via_boulder is not None for use in plan.uses))
            for plan in plans
        }
        self.assertIn((("Great Furnace",), 0), signatures)
        self.assertIn((("Ancient Den",), 1), signatures)

    def test_first_generic_spell_can_preserve_second_colored_spell(self):
        state = state_with_lands(self.deck, ["Seat of the Synod", "Great Furnace"])
        possible = set()
        for plan in enumerate_payment_plans(state, ManaCost(generic=1)):
            branch = copy.deepcopy(state)
            execute_payment(branch, plan)
            possible.add((bool(enumerate_payment_plans(branch, ManaCost(colored={"U": 1}))), bool(enumerate_payment_plans(branch, ManaCost(colored={"R": 1})))))
        self.assertEqual(possible, {(True, False), (False, True)})

    def test_boulder_filter_is_net_zero_in_payment_engine(self):
        state = state_with_lands(self.deck, ["Ancient Den"])
        boulder = Permanent(make_card("b", "Giant's Boulder", artifact=True))
        state.battlefield.append(boulder)
        plan = next(plan for plan in enumerate_payment_plans(state, ManaCost(colored={"R": 1})) if any(use.via_boulder for use in plan.uses))
        execute_payment(state, plan)
        self.assertEqual(state.mana_pool.total, 0)
        self.assertTrue(boulder.tapped)

    def test_spell_plus_interaction_reserve_uses_correct_generic_source(self):
        state = state_with_lands(self.deck, ["Ancient Den", "Great Furnace"])
        state.turn = 2
        state.hand = [make_card("n", "Nihil Spellbomb", artifact=True), make_card("g", "Galvanic Blast")]
        execute_action_policy(state, self.deck, action_policy_name=BASELINE_ACTION_POLICY, scry_policy_name=BASELINE_SCRY_POLICY)
        self.assertIn("Nihil Spellbomb", [event.get("card") for event in state.events if event["event"] == "spell_cast"])
        self.assertTrue(opponent_options(state)["Galvanic Blast"])


class RunCSequencingTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def _actions(self, state):
        return {result.actions: result.state for result in enumerate_action_sequences(state, self.deck, scry_policy_name=BASELINE_SCRY_POLICY)}

    def test_hawk_return_replay_untapped_land(self):
        state = state_with_lands(self.deck, ["Ancient Den"])
        state.turn = 2
        state.hand = [make_card("h", "Glint Hawk", creature=True)]
        actions = self._actions(state)
        sequence = next(key for key in actions if key[:2] == ("Glint Hawk", "Play Ancient Den"))
        replayed = next(p for p in actions[sequence].battlefield if p.card.name == "Ancient Den")
        self.assertFalse(replayed.tapped)

    def test_hawk_return_replay_bridge_tapped(self):
        state = state_with_lands(self.deck, ["Ancient Den"])
        bridge = land_permanent(self.deck, "Razortide Bridge", "bridge", tapped=False)
        state.battlefield.append(bridge)
        state.turn = 2
        state.hand = [make_card("h", "Glint Hawk", creature=True)]
        actions = self._actions(state)
        sequence = next(key for key in actions if key[:2] == ("Glint Hawk", "Play Razortide Bridge"))
        replayed = next(p for p in actions[sequence].battlefield if p.card.uid == "bridge")
        self.assertTrue(replayed.tapped)

    def test_hawk_cannot_replay_after_land_drop_consumed(self):
        state = state_with_lands(self.deck, ["Ancient Den"])
        state.turn = 2
        state.land_drop_available = False
        state.hand = [make_card("h", "Glint Hawk", creature=True)]
        self.assertFalse(any("Play Ancient Den" in result.actions for result in enumerate_action_sequences(state, self.deck, scry_policy_name=BASELINE_SCRY_POLICY)))

    def test_same_name_targets_with_different_state_not_collapsed(self):
        state = state_with_lands(self.deck, ["Ancient Den", "Ancient Den"])
        state.battlefield[0].tapped = True
        state.turn = 2
        state.hand = [make_card("h", "Glint Hawk", creature=True)]
        roots = [action for action in __import__("mana_lab.simulator", fromlist=["generate_legal_actions"]).generate_legal_actions(state, self.deck) if action.label == "Glint Hawk"]
        return_targets = [action for action in roots if action.target_uid is not None]
        self.assertEqual(len(return_targets), 2)

    def test_land_then_spell_sequence(self):
        state = state_with_lands(self.deck, [])
        state.turn = 1
        state.hand = [make_card("d", "Vault of Whispers", artifact=True, land=True), make_card("f", "Blood Fountain", artifact=True)]
        self.assertTrue(any(result.actions[:2] == ("Play Vault of Whispers", "Blood Fountain") for result in enumerate_action_sequences(state, self.deck, scry_policy_name=BASELINE_SCRY_POLICY)))

    def test_setup_spell_then_land_then_second_spell(self):
        state = state_with_lands(self.deck, ["Vault of Whispers"])
        state.turn = 2
        state.hand = [
            make_card("n", "Nihil Spellbomb", artifact=True),
            make_card("d", "Ancient Den", artifact=True, land=True),
            make_card("h", "Glint Hawk", creature=True),
        ]
        sequences = [result.actions for result in enumerate_action_sequences(state, self.deck, scry_policy_name=BASELINE_SCRY_POLICY)]
        self.assertTrue(any(sequence[:3] == ("Nihil Spellbomb", "Play Ancient Den", "Glint Hawk") for sequence in sequences))


if __name__ == "__main__":
    unittest.main()
