import unittest

from mana_lab.metrics import PHASE3_METRIC_REGISTRY, validate_metric_registry
from mana_lab.simulator import record_spell_windows
from mana_lab.state import make_card
from common import deck_spec, state_with_lands


class MetricWindowIdentityTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def test_repeated_windows_have_unique_opportunity_ids_and_roles(self):
        state = state_with_lands(self.deck, ["Seat of the Synod", "Vault of Whispers"])
        state.turn = 2
        state.trial_id = 7
        state.scenario_id = "fixture"
        state.replicate_id = 11
        state.hand = [make_card("s", "Baleful Strix", artifact=True, creature=True)]
        record_spell_windows(state, self.deck, "start_own_main")
        record_spell_windows(state, self.deck, "before_relevant_action")
        events = [e for e in state.events if e["event"] == "spell_window"]
        self.assertEqual(len({e["opportunity_id"] for e in events}), len(events))
        self.assertIn("primary_pre_spend_opportunity", {e["event_role"] for e in events})
        self.assertIn("diagnostic_pre_action", {e["event_role"] for e in events})
        self.assertTrue(all(e["card_instance"] == "s" for e in events))

    def test_primary_denominator_is_independently_reconstructible(self):
        state = state_with_lands(self.deck, ["Seat of the Synod"])
        state.turn = 2
        state.hand = [make_card("s", "Baleful Strix", artifact=True, creature=True)]
        record_spell_windows(state, self.deck, "start_own_main")
        record_spell_windows(state, self.deck, "after_relevant_action")
        primary = [e for e in state.events if e["event"] == "spell_window" and e["event_role"] == "primary_pre_spend_opportunity"]
        self.assertEqual(len(primary), 2)  # two configured Strix profiles
        self.assertEqual(sum(bool(e["castable"]) for e in primary), 0)

    def test_registry_has_complete_contract(self):
        validate_metric_registry(PHASE3_METRIC_REGISTRY)


if __name__ == "__main__":
    unittest.main()
