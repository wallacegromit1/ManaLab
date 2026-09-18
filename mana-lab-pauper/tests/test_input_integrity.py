import re
import unittest

from common import ROOT, deck_spec


class InputIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def test_deck_reconciles(self):
        self.assertEqual(self.deck.nonland_count, 41)
        self.assertEqual(sum(dict(self.deck.current_mana_base).values()), 19)
        self.assertEqual(self.deck.nonland_count + self.deck.land_count, 60)

    def test_frozen_nonlands_match_original_benchmark(self):
        text = (ROOT / "benchmarks" / "14-90_STRIXPATCH_AFFINITY_V1.3_INPUT.md").read_text(encoding="utf-8")
        section = text.split("## Frozen nonlands — 41", 1)[1].split("## Search space", 1)[0]
        parsed = {}
        for line in section.splitlines():
            match = re.fullmatch(r"(\d+) (.+)", line.strip())
            if match:
                parsed[match.group(2)] = int(match.group(1))
        self.assertEqual(parsed, {card.name: card.copies for card in self.deck.cards})

    def test_c0_exact(self):
        self.assertEqual(
            dict(self.deck.current_mana_base),
            {
                "Ancient Den": 3,
                "Goldmire Bridge": 1,
                "Great Furnace": 4,
                "Mistvault Bridge": 2,
                "Razortide Bridge": 1,
                "Seat of the Synod": 4,
                "Vault of Whispers": 4,
            },
        )

    def test_legality_dates_and_card_facts_frozen(self):
        raw = self.deck.raw
        self.assertIn("2026-09-07", raw["metadata"]["legality_note"])
        self.assertIn("2026-09-23", raw["metadata"]["legality_note"])
        boulder = self.deck.card_by_name["Giant's Boulder"].rules
        self.assertEqual(boulder["etb_scry"], 2)
        self.assertFalse(boulder["filter_is_ramp"])
        cryogen = self.deck.card_by_name["Cryogen Relic"].rules
        self.assertEqual((cryogen["etb_draw"], cryogen["leaves_battlefield_draw"]), (1, 1))
        monitor = self.deck.card_by_name["Utrom Monitor"].rules
        self.assertTrue(monitor["affinity_for_artifacts"])
        self.assertEqual(monitor["colored_cost"], {"U": 1})


if __name__ == "__main__":
    unittest.main()

