import unittest

from mana_lab.policies import BASELINE_ACTION_POLICY, BASELINE_SCRY_POLICY
from mana_lab.simulator import choose_next_action, enumerate_action_sequences
from mana_lab.state import Permanent, make_card
from common import deck_spec, state_with_lands


class BargainLandLossTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def root(self, state):
        return choose_next_action(
            state, self.deck, action_policy_name=BASELINE_ACTION_POLICY,
            scry_policy_name=BASELINE_SCRY_POLICY,
        )

    def test_three_land_velocity_does_not_sacrifice_land(self):
        state = state_with_lands(self.deck, ["Vault of Whispers", "Seat of the Synod", "Ancient Den"])
        state.turn = 3
        state.hand = [make_card("b", "Reckoner's Bargain")]
        self.assertIsNone(self.root(state))

    def test_nonland_artifact_or_creature_is_selected(self):
        for permanent in (
            Permanent(make_card("n", "Nihil Spellbomb", artifact=True)),
            Permanent(make_card("h", "Glint Hawk", creature=True)),
        ):
            state = state_with_lands(self.deck, ["Vault of Whispers", "Seat of the Synod", "Ancient Den"])
            state.turn = 3
            state.battlefield.append(permanent)
            state.hand = [make_card("b", "Reckoner's Bargain")]
            action = self.root(state)
            self.assertEqual(action.label, "Reckoner's Bargain")
            self.assertEqual(action.sacrifice_uid, permanent.card.uid)

    def test_held_land_does_not_erase_battlefield_loss(self):
        state = state_with_lands(self.deck, ["Vault of Whispers", "Seat of the Synod", "Ancient Den"])
        state.turn = 3
        state.land_drop_available = False
        state.hand = [
            make_card("b", "Reckoner's Bargain"),
            make_card("held", "Great Furnace", artifact=True, land=True),
        ]
        bargain_results = [
            r for r in enumerate_action_sequences(state, self.deck, scry_policy_name=BASELINE_SCRY_POLICY)
            if r.actions and r.actions[0] == "Reckoner's Bargain"
        ]
        self.assertTrue(bargain_results)
        self.assertTrue(all(r.option.land_loss == 1 for r in bargain_results))

    def test_hard_deadline_is_explicit_exception(self):
        state = state_with_lands(self.deck, ["Vault of Whispers", "Seat of the Synod", "Ancient Den"])
        state.turn = 4
        state.land_drop_available = False
        state.hand = [make_card("b", "Reckoner's Bargain")]
        self.assertEqual(self.root(state).label, "Reckoner's Bargain")


if __name__ == "__main__":
    unittest.main()
