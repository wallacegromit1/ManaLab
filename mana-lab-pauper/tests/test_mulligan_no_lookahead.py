import unittest

from mana_lab.mulligan import BASELINE_MULLIGAN, london_mulligan
from mana_lab.state import make_card
from common import deck_spec


class MulliganNoLookaheadTests(unittest.TestCase):
    def test_future_library_order_does_not_change_keep_or_bottom(self):
        deck = deck_spec()
        seven = [
            make_card("d", "Ancient Den", artifact=True, land=True),
            make_card("s", "Seat of the Synod", artifact=True, land=True),
            make_card("t", "Thoughtcast"),
            make_card("g", "Glint Hawk"),
            make_card("b", "Giant's Boulder", artifact=True),
            make_card("m", "Myr Enforcer", artifact=True, creature=True),
            make_card("c", "Cryogen Relic", artifact=True),
        ]
        results = []
        for hidden in ("Hidden A", "Hidden B"):
            def draw_seven(attempt, hidden_name=hidden):
                return list(seven), [make_card("hidden", hidden_name)]
            results.append(london_mulligan(deck, BASELINE_MULLIGAN, draw_seven))
        self.assertEqual(tuple(card.uid for card in results[0].hand), tuple(card.uid for card in results[1].hand))
        self.assertEqual(results[0].mulligans, results[1].mulligans)


if __name__ == "__main__":
    unittest.main()

