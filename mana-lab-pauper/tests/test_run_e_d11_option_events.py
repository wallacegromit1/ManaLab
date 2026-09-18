import unittest

from mana_lab.metrics import PHASE3_METRIC_REGISTRY
from mana_lab.policies import BASELINE_SCRY_POLICY
from mana_lab.simulator import apply_planner_action, generate_legal_actions
from mana_lab.state import Permanent, make_card
from common import deck_spec, state_with_lands


class OptionEventContractTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def test_normal_bargain_trace_emits_nihil_opportunity_and_outcome(self):
        state = state_with_lands(
            self.deck,
            ["Vault of Whispers", "Seat of the Synod", "Ancient Den"],
            library_names=("A", "B", "C"),
        )
        nihil = Permanent(make_card("n", "Nihil Spellbomb", artifact=True))
        state.battlefield.append(nihil)
        bargain = make_card("b", "Reckoner's Bargain")
        state.hand = [bargain]
        action = next(
            a for a in generate_legal_actions(state, self.deck)
            if a.label == "Reckoner's Bargain" and a.sacrifice_uid == "n"
        )
        apply_planner_action(
            state, self.deck, action, scry_policy_name=BASELINE_SCRY_POLICY,
            reveal_information=True,
        )
        self.assertTrue(any(e["event"] == "nihil_draw_opportunity" for e in state.events))
        self.assertTrue(any(e["event"] in {"nihil_draw_paid", "nihil_draw_declined"} for e in state.events))

    def test_fixture_only_options_are_not_phase3_aggregates(self):
        for name in ("blood_token_activation_option", "munitions_activation_option", "cryogen_stun_activation_option"):
            self.assertEqual(PHASE3_METRIC_REGISTRY[name]["status"], "validation_only")


if __name__ == "__main__":
    unittest.main()
