import unittest

from mana_lab.policies import BASELINE_ACTION_POLICY, BASELINE_SCRY_POLICY
from mana_lab.simulator import apply_planner_action, choose_next_action, enumerate_action_sequences
from mana_lab.state import make_card
from common import deck_spec, state_with_lands


class HawkFunctionalityTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def test_no_return_cast_is_raw_but_not_functional(self):
        state = state_with_lands(self.deck, ["Ancient Den"])
        state.turn = 2
        state.land_drop_available = False
        state.hand = [make_card("h", "Glint Hawk", creature=True)]
        result = next(
            r for r in enumerate_action_sequences(state, self.deck, scry_policy_name=BASELINE_SCRY_POLICY)
            if r.actions == ("Glint Hawk",) and r.planner_actions[0].target_uid is None
        )
        self.assertEqual(result.option.raw_spell_casts, 1)
        self.assertEqual(result.option.spell_executions, 0)
        resolution = next(e for e in result.state.events if e["event"] == "spell_resolution")
        self.assertFalse(resolution["functional"])

    def test_production_prefers_legal_return(self):
        state = state_with_lands(self.deck, ["Ancient Den"])
        state.turn = 2
        state.hand = [make_card("h", "Glint Hawk", creature=True)]
        action = choose_next_action(
            state, self.deck, action_policy_name=BASELINE_ACTION_POLICY,
            scry_policy_name=BASELINE_SCRY_POLICY,
        )
        self.assertIsNotNone(action.target_uid)

    def test_return_and_replay_bridge_remains_tapped(self):
        state = state_with_lands(self.deck, ["Ancient Den", "Razortide Bridge"])
        state.turn = 2
        state.hand = [make_card("h", "Glint Hawk", creature=True)]
        result = next(
            r for r in enumerate_action_sequences(state, self.deck, scry_policy_name=BASELINE_SCRY_POLICY)
            if r.actions[:2] == ("Glint Hawk", "Play Razortide Bridge")
        )
        bridge = next(p for p in result.state.battlefield if p.card.name == "Razortide Bridge")
        self.assertTrue(bridge.tapped)
        self.assertTrue(any(e["event"] == "spell_resolution" and e["functional"] for e in result.state.events))


if __name__ == "__main__":
    unittest.main()
