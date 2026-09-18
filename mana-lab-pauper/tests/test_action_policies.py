import unittest

from mana_lab.policies import ALTERNATE_ACTION_POLICY, BASELINE_ACTION_POLICY, BASELINE_SCRY_POLICY
from mana_lab.simulator import enumerate_action_sequences, execute_action_policy
from mana_lab.state import make_card
from common import deck_spec, state_with_lands


class ActionPolicyTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def _state(self):
        state = state_with_lands(self.deck, ["Seat of the Synod", "Vault of Whispers"])
        state.turn = 2
        state.hand = [
            make_card("n", "Nihil Spellbomb", artifact=True),
            make_card("f", "Refurbished Familiar", artifact=True, creature=True),
            make_card("d", "Dispatch"),
        ]
        return state

    def test_enumerates_multi_spell_lines(self):
        results = enumerate_action_sequences(self._state(), self.deck, scry_policy_name=BASELINE_SCRY_POLICY)
        actions = {result.actions for result in results}
        self.assertIn(("Nihil Spellbomb", "Refurbished Familiar"), actions)

    def test_named_policies_are_executable_and_logged(self):
        for policy in (BASELINE_ACTION_POLICY, ALTERNATE_ACTION_POLICY):
            state = self._state()
            selected = execute_action_policy(state, self.deck, action_policy_name=policy, scry_policy_name=BASELINE_SCRY_POLICY)
            self.assertIsInstance(selected, tuple)
            event = next(event for event in state.events if event["event"] == "policy_action_sequence")
            self.assertEqual(event["policy"], policy)

    def test_same_visible_state_is_deterministic(self):
        selections = []
        for _ in range(2):
            state = self._state()
            selections.append(execute_action_policy(state, self.deck, action_policy_name=BASELINE_ACTION_POLICY, scry_policy_name=BASELINE_SCRY_POLICY))
        self.assertEqual(selections[0], selections[1])


if __name__ == "__main__":
    unittest.main()

