import unittest

from mana_lab.policies import (
    BASELINE_ACTION_POLICY,
    BASELINE_INFORMATION_POLICY,
    BASELINE_SCRY_POLICY,
    CONSERVATIVE_INFORMATION_POLICY,
)
from mana_lab.simulator import choose_next_action, enumerate_action_sequences
from mana_lab.state import Permanent, make_card
from common import deck_spec, state_with_lands


class InformationContinuationTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def sequences(self, state, policy=BASELINE_INFORMATION_POLICY):
        return enumerate_action_sequences(
            state, self.deck, scry_policy_name=BASELINE_SCRY_POLICY,
            information_policy_name=policy,
        )

    def test_strix_continues_to_known_enforcer(self):
        state = state_with_lands(
            self.deck,
            ["Seat of the Synod", "Vault of Whispers", "Ancient Den", "Great Furnace"],
        )
        state.turn = 3
        state.hand = [
            make_card("s", "Baleful Strix", artifact=True, creature=True),
            make_card("e", "Myr Enforcer", artifact=True, creature=True),
        ]
        self.assertTrue(any(r.actions[:2] == ("Baleful Strix", "Myr Enforcer") for r in self.sequences(state)))

    def test_thoughtcast_and_cryogen_continue_with_known_card(self):
        for information_card in ("Thoughtcast", "Cryogen Relic"):
            state = state_with_lands(
                self.deck,
                ["Seat of the Synod", "Vault of Whispers", "Ancient Den", "Great Furnace"],
            )
            state.turn = 3
            state.hand = [
                make_card("i", information_card, artifact=information_card == "Cryogen Relic"),
                make_card("n", "Nihil Spellbomb", artifact=True),
            ]
            self.assertTrue(any(r.actions[:2] == (information_card, "Nihil Spellbomb") for r in self.sequences(state)))

    def test_bargain_and_boulder_continue_with_known_card(self):
        bargain = state_with_lands(self.deck, ["Vault of Whispers", "Seat of the Synod", "Great Furnace"])
        bargain.turn = 3
        bargain.battlefield.append(Permanent(make_card("c", "Blood", artifact=True), token=True))
        bargain.hand = [make_card("b", "Reckoner's Bargain"), make_card("n", "Nihil Spellbomb", artifact=True)]
        self.assertTrue(any(r.actions[:2] == ("Reckoner's Bargain", "Nihil Spellbomb") for r in self.sequences(bargain)))

        boulder = state_with_lands(self.deck, ["Ancient Den", "Vault of Whispers"])
        boulder.turn = 2
        boulder.hand = [make_card("b", "Giant's Boulder", artifact=True), make_card("n", "Nihil Spellbomb", artifact=True)]
        self.assertTrue(any(r.actions[:2] == ("Giant's Boulder", "Nihil Spellbomb") for r in self.sequences(boulder)))

    def test_hidden_library_cannot_change_pre_reveal_root(self):
        roots = []
        for hidden in (("Ancient Den", "Dispatch"), ("Myr Enforcer", "Blood Fountain")):
            state = state_with_lands(self.deck, ["Seat of the Synod", "Vault of Whispers", "Great Furnace"], library_names=hidden)
            state.turn = 3
            state.hand = [make_card("t", "Thoughtcast")]
            roots.append(choose_next_action(
                state, self.deck, action_policy_name=BASELINE_ACTION_POLICY,
                scry_policy_name=BASELINE_SCRY_POLICY,
            ).key)
        self.assertEqual(roots[0], roots[1])

    def test_information_profiles_are_explicit_and_distinct(self):
        state = state_with_lands(self.deck, ["Seat of the Synod", "Vault of Whispers", "Great Furnace"])
        state.turn = 3
        state.hand = [make_card("t", "Thoughtcast")]
        baseline = max(r.option.information_value for r in self.sequences(state, BASELINE_INFORMATION_POLICY))
        conservative = max(r.option.information_value for r in self.sequences(state, CONSERVATIVE_INFORMATION_POLICY))
        self.assertGreater(baseline, conservative)


if __name__ == "__main__":
    unittest.main()
