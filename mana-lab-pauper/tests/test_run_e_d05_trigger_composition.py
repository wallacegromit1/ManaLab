import unittest

from mana_lab.policies import BASELINE_SCRY_POLICY
from mana_lab.simulator import apply_planner_action, cast_card, generate_legal_actions
from mana_lab.state import Permanent, make_card
from common import deck_spec, state_with_lands


class TriggerCompositionTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def cast_bargain(self, sacrifice, lands, hidden=("A", "B", "C")):
        state = state_with_lands(self.deck, lands, library_names=hidden)
        state.turn = 3
        state.battlefield.append(sacrifice)
        bargain = make_card("b", "Reckoner's Bargain")
        state.hand = [bargain]
        cast_card(state, self.deck, bargain, bargain_sacrifice=sacrifice)
        return state

    def test_bargain_nihil_trigger_survives_and_draws_when_black_available(self):
        nihil = Permanent(make_card("n", "Nihil Spellbomb", artifact=True))
        state = self.cast_bargain(
            nihil,
            ["Vault of Whispers", "Goldmire Bridge", "Ancient Den"],
        )
        reasons = [e["reason"] for e in state.events if e["event"] == "draw"]
        self.assertEqual(reasons, ["Nihil Spellbomb", "Reckoner's Bargain", "Reckoner's Bargain"])
        self.assertTrue(any(e["event"] == "nihil_draw_paid" for e in state.events))

    def test_nihil_trigger_declines_when_black_unavailable(self):
        nihil = Permanent(make_card("n", "Nihil Spellbomb", artifact=True))
        state = self.cast_bargain(nihil, ["Vault of Whispers", "Ancient Den"])
        self.assertTrue(any(e["event"] == "nihil_draw_opportunity" and not e["payable"] for e in state.events))
        self.assertFalse(any(e["event"] == "nihil_draw_paid" for e in state.events))

    def test_bargain_cryogen_trigger_precedes_spell_draws(self):
        cryogen = Permanent(make_card("c", "Cryogen Relic", artifact=True))
        state = self.cast_bargain(cryogen, ["Vault of Whispers", "Seat of the Synod"])
        reasons = [e["reason"] for e in state.events if e["event"] == "draw"]
        self.assertEqual(reasons, ["Cryogen Relic leave draw", "Reckoner's Bargain", "Reckoner's Bargain"])

    def test_sacrifice_is_chosen_before_any_draw(self):
        nihil = Permanent(make_card("n", "Nihil Spellbomb", artifact=True))
        state = self.cast_bargain(nihil, ["Vault of Whispers", "Seat of the Synod", "Ancient Den"])
        leave = next(e["event_id"] for e in state.events if e["event"] == "permanent_left")
        first_draw = next(e["event_id"] for e in state.events if e["event"] == "draw")
        self.assertLess(leave, first_draw)

    def test_actual_production_action_path_preserves_nihil_trigger(self):
        state = state_with_lands(
            self.deck, ["Vault of Whispers", "Goldmire Bridge", "Ancient Den"],
            library_names=("A", "B", "C"),
        )
        state.turn = 3
        nihil = Permanent(make_card("n", "Nihil Spellbomb", artifact=True))
        state.battlefield.append(nihil)
        state.hand = [make_card("b", "Reckoner's Bargain")]
        action = next(
            a for a in generate_legal_actions(state, self.deck)
            if a.label == "Reckoner's Bargain" and a.sacrifice_uid == "n"
            and any(use.permanent.card.name == "Ancient Den" for use in a.payment.uses)
        )
        apply_planner_action(
            state, self.deck, action, scry_policy_name=BASELINE_SCRY_POLICY,
            reveal_information=True,
        )
        self.assertTrue(any(e["event"] == "nihil_draw_opportunity" for e in state.events))
        self.assertTrue(any(e["event"] == "nihil_draw_paid" for e in state.events))


if __name__ == "__main__":
    unittest.main()
