import unittest

from mana_lab.simulator import cast_card
from mana_lab.state import make_card
from common import deck_spec, state_with_lands


class SameTurnSequencingTests(unittest.TestCase):
    def test_artifact_first_reduces_second_affinity_spell(self):
        deck = deck_spec()
        state = state_with_lands(deck, ["Seat of the Synod", "Vault of Whispers"])
        spellbomb = make_card("n", "Nihil Spellbomb", artifact=True)
        familiar = make_card("f", "Refurbished Familiar", artifact=True, creature=True)
        state.hand = [spellbomb, familiar]
        cast_card(state, deck, spellbomb)
        cast_card(state, deck, familiar)
        self.assertEqual([event["card"] for event in state.events if event["event"] == "spell_cast"], ["Nihil Spellbomb", "Refurbished Familiar"])
        self.assertEqual(state.artifact_count(), 4)


if __name__ == "__main__":
    unittest.main()

