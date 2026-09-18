import unittest

from mana_lab.effects import resolve_scry
from mana_lab.mana import ManaCost
from mana_lab.payment import enumerate_payment_plans
from mana_lab.policies import (
    ALTERNATE_SCRY_POLICY,
    BASELINE_SCRY_POLICY,
    make_scry_policy,
    opponent_options,
    opponent_window_status,
    VisibleState,
    _scry_score,
)
from mana_lab.simulator import cast_card, generate_legal_actions
from mana_lab.state import GameState, Permanent, make_card
from common import deck_spec, library, state_with_lands


class RunCBoulderOpponentTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def _fixed_state(self, interaction):
        state = state_with_lands(self.deck, ["Ancient Den"])
        state.battlefield.append(Permanent(make_card("b", "Giant's Boulder", artifact=True)))
        state.hand = [make_card("i", interaction)]
        return state

    def test_boulder_white_source_makes_blast_payable(self):
        self.assertTrue(opponent_options(self._fixed_state("Galvanic Blast"))["Galvanic Blast"])

    def test_boulder_makes_dispatch_payable(self):
        state = state_with_lands(self.deck, ["Great Furnace"])
        state.battlefield.append(Permanent(make_card("b", "Giant's Boulder", artifact=True)))
        state.hand = [make_card("d", "Dispatch")]
        self.assertTrue(opponent_options(state)["Dispatch"])

    def test_boulder_makes_bargain_black_payable_with_sacrifice(self):
        state = state_with_lands(self.deck, ["Ancient Den", "Seat of the Synod"])
        state.battlefield.append(Permanent(make_card("b", "Giant's Boulder", artifact=True)))
        state.hand = [make_card("r", "Reckoner's Bargain")]
        self.assertTrue(opponent_options(state)["Reckoner's Bargain"])

    def test_boulder_any_color_does_not_include_colorless(self):
        state = state_with_lands(self.deck, ["Ancient Den"])
        state.battlefield.append(Permanent(make_card("b", "Giant's Boulder", artifact=True)))
        for color in "WUBRG":
            self.assertTrue(enumerate_payment_plans(state, ManaCost(colored={color: 1})), color)
        self.assertFalse(enumerate_payment_plans(state, ManaCost(colored={"C": 1})))

    def test_interaction_in_hand_distinct_from_payable(self):
        state = GameState(hand=[make_card("g", "Galvanic Blast")], phase="main", turn=2)
        status = opponent_window_status(state, self.deck)["Galvanic Blast"]
        self.assertTrue(status["in_hand"])
        self.assertTrue(status["demand"])
        self.assertFalse(status["payable"])


class RunCBargainTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def test_no_legal_sacrifice_means_no_action(self):
        state = GameState(hand=[make_card("r", "Reckoner's Bargain")], phase="main", turn=2)
        state.mana_pool.add("B", 2)
        self.assertFalse(any(action.label == "Reckoner's Bargain" for action in generate_legal_actions(state, self.deck)))

    def test_artifact_and_land_sacrifice_choices_are_distinct(self):
        state = state_with_lands(self.deck, ["Vault of Whispers", "Seat of the Synod"])
        state.battlefield.append(Permanent(make_card("n", "Nihil Spellbomb", artifact=True)))
        state.hand = [make_card("r", "Reckoner's Bargain")]
        actions = [action for action in generate_legal_actions(state, self.deck) if action.label == "Reckoner's Bargain"]
        sacrifice_names = {
            next(p.card.name for p in state.battlefield if p.card.uid == action.sacrifice_uid)
            for action in actions
        }
        self.assertIn("Vault of Whispers", sacrifice_names)
        self.assertIn("Nihil Spellbomb", sacrifice_names)

    def test_bargain_reduces_affinity_and_can_break_metalcraft(self):
        state = state_with_lands(self.deck, ["Vault of Whispers", "Seat of the Synod"])
        relic = Permanent(make_card("n", "Nihil Spellbomb", artifact=True))
        state.battlefield.append(relic)
        state.hand = [make_card("r", "Reckoner's Bargain")]
        before_cost = ManaCost.from_rules(self.deck.card_by_name["Myr Enforcer"].rules, state.artifact_count()).generic
        cast_card(state, self.deck, state.hand[0], bargain_sacrifice=relic)
        after_cost = ManaCost.from_rules(self.deck.card_by_name["Myr Enforcer"].rules, state.artifact_count()).generic
        event = next(event for event in state.events if event["event"] == "bargain_cast")
        self.assertTrue(event["metalcraft_before"])
        self.assertFalse(event["metalcraft_after"])
        self.assertEqual(after_cost, before_cost + 1)

    def test_bargain_cryogen_leave_draw_then_bargain_draw(self):
        state = state_with_lands(self.deck, ["Vault of Whispers", "Seat of the Synod"], library_names=("A", "B", "C"))
        cryogen = Permanent(make_card("c", "Cryogen Relic", artifact=True))
        state.battlefield.append(cryogen)
        bargain = make_card("r", "Reckoner's Bargain")
        state.hand = [bargain]
        cast_card(state, self.deck, bargain, bargain_sacrifice=cryogen)
        draws = [(event["card"], event["reason"]) for event in state.events if event["event"] == "draw"]
        self.assertEqual(draws[0], ("A", "Cryogen Relic leave draw"))
        self.assertEqual([card for card, _ in draws], ["A", "B", "C"])

    def test_payment_and_sacrifice_precede_draw(self):
        state = state_with_lands(self.deck, ["Vault of Whispers", "Seat of the Synod"], library_names=("A", "B"))
        relic = Permanent(make_card("n", "Nihil Spellbomb", artifact=True))
        state.battlefield.append(relic)
        bargain = make_card("r", "Reckoner's Bargain")
        state.hand = [bargain]
        cast_card(state, self.deck, bargain, bargain_sacrifice=relic)
        payment_id = next(e["event_id"] for e in state.events if e["event"] == "payment")
        sacrifice_id = next(e["event_id"] for e in state.events if e["event"] == "permanent_left")
        draw_id = next(e["event_id"] for e in state.events if e["event"] == "draw")
        self.assertLess(payment_id, sacrifice_id)
        self.assertLess(sacrifice_id, draw_id)


class RunCScryPolicyTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def _state(self, top, hidden="HIDDEN"):
        state = state_with_lands(self.deck, ["Seat of the Synod"], library_names=(*top, hidden))
        state.turn = 2
        state.hand = [make_card("s", "Baleful Strix", artifact=True, creature=True)]
        state.battlefield.append(Permanent(make_card("b", "Giant's Boulder", artifact=True)))
        return state

    def test_missing_color_land_unlocking_strix_is_first(self):
        state = self._state(("Vault of Whispers", "Myr Enforcer"))
        decision = resolve_scry(state, 2, make_scry_policy(self.deck, BASELINE_SCRY_POLICY))
        self.assertEqual(decision.keep_order[0], 0)

    def test_same_pair_different_hidden_third_same_decision(self):
        decisions = []
        for hidden in ("Ancient Den", "Thoughtcast"):
            state = self._state(("Vault of Whispers", "Myr Enforcer"), hidden)
            decisions.append(resolve_scry(state, 2, make_scry_policy(self.deck, BASELINE_SCRY_POLICY)))
        self.assertEqual(decisions[0], decisions[1])

    def test_alternate_policy_is_land_stability_biased(self):
        state = GameState(library=library("Ancient Den", "Thoughtcast", "X"), phase="main", turn=1)
        baseline = resolve_scry(state, 2, make_scry_policy(self.deck, BASELINE_SCRY_POLICY))
        state = GameState(library=library("Ancient Den", "Thoughtcast", "X"), phase="main", turn=1)
        alternate = resolve_scry(state, 2, make_scry_policy(self.deck, ALTERNATE_SCRY_POLICY))
        self.assertEqual(alternate.keep_order[0], 0)
        self.assertNotEqual(make_scry_policy(self.deck, BASELINE_SCRY_POLICY).__name__, make_scry_policy(self.deck, ALTERNATE_SCRY_POLICY).__name__)

    def test_scry_projection_counts_artifact_lands_for_affinity(self):
        state = state_with_lands(self.deck, ["Ancient Den", "Seat of the Synod", "Vault of Whispers", "Great Furnace"])
        state.turn = 3
        visible = VisibleState.from_state(state)
        score = _scry_score(make_card("e", "Myr Enforcer", artifact=True, creature=True), visible, self.deck, land_first=False)
        self.assertEqual(score[0], 425)


if __name__ == "__main__":
    unittest.main()
