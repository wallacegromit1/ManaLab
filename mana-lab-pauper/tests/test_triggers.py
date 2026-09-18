import unittest

from mana_lab.effects import cast_reckoners_bargain
from mana_lab.state import GameState, Permanent, make_card
from common import library


class TriggerOrderingTests(unittest.TestCase):
    def test_cryogen_trigger_resolves_above_bargain(self):
        state = GameState(library=library("A", "B", "C"))
        cryogen = Permanent(make_card("c", "Cryogen Relic", artifact=True))
        state.battlefield.append(cryogen)
        cast_reckoners_bargain(state, cryogen)
        self.assertEqual([item.label for item in state.stack], ["Reckoner's Bargain", "Cryogen Relic leave draw"])
        state.resolve_all()
        self.assertEqual([card.name for card in state.hand], ["A", "B", "C"])
        draws = [event["card"] for event in state.events if event["event"] == "draw"]
        self.assertEqual(draws, ["A", "B", "C"])


if __name__ == "__main__":
    unittest.main()

