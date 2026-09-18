import unittest

from mana_lab.mana import ManaCost
from mana_lab.simulator import cast_card
from mana_lab.state import GameState, make_card
from common import deck_spec, state_with_lands


class AffinityTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def test_cost_tables_zero_through_eight(self):
        cases = {
            "Thoughtcast": (4, {"U": 1}),
            "Refurbished Familiar": (3, {"B": 1}),
            "Utrom Monitor": (4, {"U": 1}),
            "Myr Enforcer": (7, {}),
        }
        for name, (generic, colored) in cases.items():
            rules = self.deck.card_by_name[name].rules
            for artifacts in range(9):
                cost = ManaCost.from_rules(rules, artifacts)
                self.assertEqual(cost.generic, max(0, generic - artifacts), (name, artifacts))
                self.assertEqual(cost.colored, colored)

    def test_prior_artifact_resolution_reduces_later_cost(self):
        state = state_with_lands(self.deck, ["Seat of the Synod", "Vault of Whispers"])
        before = ManaCost.from_rules(self.deck.card_by_name["Refurbished Familiar"].rules, state.artifact_count())
        state.add_permanent(make_card("spellbomb", "Nihil Spellbomb", artifact=True))
        after = ManaCost.from_rules(self.deck.card_by_name["Refurbished Familiar"].rules, state.artifact_count())
        self.assertEqual(before.generic - after.generic, 1)


if __name__ == "__main__":
    unittest.main()

