import unittest

from mana_lab.mulligan import ALTERNATE_MULLIGAN, BASELINE_MULLIGAN, choose_bottom, london_mulligan, should_keep
from mana_lab.state import make_card
from common import deck_spec


def cards(names):
    return [make_card(f"c-{index}", name, land=name in deck_spec().land_by_name) for index, name in enumerate(names)]


class MulliganTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def test_baseline_requires_two_to_four_and_t2_two_mana(self):
        both_bridges = cards(["Mistvault Bridge", "Razortide Bridge", "Thoughtcast", "Thoughtcast", "Dispatch", "Glint Hawk", "Myr Enforcer"])
        one_mono = cards(["Mistvault Bridge", "Ancient Den", "Thoughtcast", "Thoughtcast", "Dispatch", "Glint Hawk", "Myr Enforcer"])
        self.assertFalse(should_keep(both_bridges, 7, self.deck, BASELINE_MULLIGAN))
        self.assertTrue(should_keep(one_mono, 7, self.deck, BASELINE_MULLIGAN))

    def test_alternate_keeps_two_to_five_lands(self):
        hand = cards(["Mistvault Bridge", "Razortide Bridge", "Thoughtcast", "Thoughtcast", "Dispatch", "Glint Hawk", "Myr Enforcer"])
        self.assertTrue(should_keep(hand, 7, self.deck, ALTERNATE_MULLIGAN))

    def test_four_card_size_automatic(self):
        hand = cards(["Thoughtcast"] * 7)
        self.assertTrue(should_keep(hand, 4, self.deck, BASELINE_MULLIGAN))

    def test_bottom_exact_count_and_deterministic(self):
        hand = cards(["Ancient Den", "Seat of the Synod", "Vault of Whispers", "Thoughtcast", "Dispatch", "Glint Hawk", "Myr Enforcer"])
        a = choose_bottom(hand, 2, self.deck)
        b = choose_bottom(hand, 2, self.deck)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 2)

    def test_london_draws_fresh_seven_and_bottoms_mulligan_count(self):
        attempts = [
            cards(["Thoughtcast"] * 7) + cards(["Myr Enforcer"] * 53),
            cards(["Ancient Den", "Seat of the Synod", "Thoughtcast", "Dispatch", "Glint Hawk", "Myr Enforcer", "Cryogen Relic"]) + cards(["Myr Enforcer"] * 53),
        ]

        def draw_seven(attempt):
            chosen = attempts[min(attempt, 1)]
            return chosen[:7], chosen[7:]

        result = london_mulligan(self.deck, BASELINE_MULLIGAN, draw_seven)
        self.assertEqual(result.mulligans, 1)
        self.assertEqual(len(result.hand), 6)
        self.assertEqual(len(result.bottomed), 1)
        self.assertNotEqual(result.attempts[0], result.attempts[1])


if __name__ == "__main__":
    unittest.main()

