import unittest

from mana_lab.policies import ALTERNATE_LAND_POLICY, BASELINE_LAND_POLICY, choose_land
from mana_lab.state import make_card
from common import deck_spec, state_with_lands


class RunCLandPolicyTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def test_counts_executable_sequences_not_individually_castable_cards(self):
        state = state_with_lands(self.deck, ["Vault of Whispers"])
        state.turn = 2
        state.hand = [
            make_card("d", "Ancient Den", artifact=True, land=True),
            make_card("m", "Goldmire Bridge", artifact=True, land=True),
            make_card("n1", "Nihil Spellbomb", artifact=True),
            make_card("n2", "Nihil Spellbomb", artifact=True),
            make_card("f", "Blood Fountain", artifact=True),
            make_card("h", "Glint Hawk", creature=True),
        ]
        choose_land(state, self.deck, BASELINE_LAND_POLICY)
        event = next(event for event in state.events if event["event"] == "policy_land_choice")
        self.assertLessEqual(event["rationale"]["executable_spell_actions"], 2)

    def test_untapped_mono_beats_bridge_for_immediate_dispatch_access(self):
        state = state_with_lands(self.deck, [])
        state.turn = 1
        state.hand = [
            make_card("d", "Ancient Den", artifact=True, land=True),
            make_card("g", "Goldmire Bridge", artifact=True, land=True),
            make_card("x", "Dispatch"),
        ]
        self.assertEqual(choose_land(state, self.deck, BASELINE_LAND_POLICY).name, "Ancient Den")

    def test_bridge_colors_count_for_future_joint_access(self):
        state = state_with_lands(self.deck, ["Seat of the Synod"])
        state.turn = 1
        state.hand = [
            make_card("v", "Vault of Whispers", artifact=True, land=True),
            make_card("m", "Mistvault Bridge", artifact=True, land=True),
            make_card("s", "Baleful Strix", artifact=True, creature=True),
        ]
        choose_land(state, self.deck, BASELINE_LAND_POLICY)
        rationale = next(event for event in state.events if event["event"] == "policy_land_choice")["rationale"]
        self.assertGreaterEqual(rationale["future_joint_castability"], 1)

    def test_bridge_can_be_selected_in_true_slack_window(self):
        state = state_with_lands(self.deck, ["Seat of the Synod"])
        state.turn = 1
        state.hand = [
            make_card("d", "Ancient Den", artifact=True, land=True),
            make_card("m", "Mistvault Bridge", artifact=True, land=True),
            make_card("s", "Baleful Strix", artifact=True, creature=True),
        ]
        selected = choose_land(state, self.deck, BASELINE_LAND_POLICY)
        self.assertIn(selected.name, {"Mistvault Bridge", "Ancient Den"})
        event = next(event for event in state.events if event["event"] == "policy_land_choice")
        self.assertIn("future_color_coverage", event["rationale"])

    def test_alternate_prioritizes_untapped_mana(self):
        state = state_with_lands(self.deck, [])
        state.turn = 1
        state.hand = [make_card("d", "Ancient Den", artifact=True, land=True), make_card("m", "Goldmire Bridge", artifact=True, land=True)]
        self.assertEqual(choose_land(state, self.deck, ALTERNATE_LAND_POLICY).name, "Ancient Den")


if __name__ == "__main__":
    unittest.main()
