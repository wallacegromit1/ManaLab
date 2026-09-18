import copy
import unittest

from mana_lab.phase3_metrics import (
    aggregate_trial_events,
    evaluate_critical_sequences,
    validate_aggregation_coverage,
    validate_event_stream,
)


def base_event(event_id, event, turn=0, **updates):
    value = {
        "event_id": event_id, "event": event, "turn": turn,
        "scenario": "synthetic", "replicate": 77, "trial_id": 4, "on_play": True,
    }
    value.update(updates)
    return value


class RunGEventAggregationTests(unittest.TestCase):
    def _events(self):
        return [
            base_event(1, "opening_hand", opening_land_count=3, keep_size=6, mulligans=1),
            base_event(
                2, "state_snapshot", turn=2, event_role="primary_pre_spend_opportunity",
                usable_untapped_mana=2, joint_UB=True, direct_colors=["U", "B"],
                available_filtered_colors=[], artifact_count=2, metalcraft=False,
            ),
            base_event(
                3, "spell_window", turn=2, event_role="primary_pre_spend_opportunity",
                opportunity_id="synthetic|strix", card="Baleful Strix", castable=True,
            ),
            base_event(4, "spell_resolution", turn=2, card="Baleful Strix", functional=True),
            base_event(5, "spell_resolution", turn=4, card="Glint Hawk", functional=True),
            base_event(6, "spell_resolution", turn=4, card="Nihil Spellbomb", functional=True),
            base_event(
                7, "opponent_window", turn=3, card="Dispatch", interaction_in_hand=True,
                payable=True, metalcraft=True,
            ),
            base_event(8, "etb_tempo", turn=2, entered_tapped=True, blocked_action=True),
        ]

    def test_registry_has_an_aggregation_route_for_every_metric(self):
        validate_aggregation_coverage()

    def test_synthetic_stream_aggregates_denominators_and_joins(self):
        result = aggregate_trial_events(self._events())
        self.assertEqual(result["spell_opportunities"], 1)
        self.assertEqual(result["spell_castable"], 1)
        self.assertEqual(result["realized_etb_tapped_blocks"], 1)
        self.assertTrue(result["critical_sequences"]["T2_STRIX_UB"])
        self.assertTrue(result["critical_sequences"]["T4_DOUBLE_SPELL"])
        self.assertTrue(result["critical_sequences"]["OPP_FULL_DISPATCH"])

    def test_duplicate_event_ids_rejected(self):
        events = self._events()
        events.append(copy.deepcopy(events[-1]))
        with self.assertRaisesRegex(ValueError, "duplicate event_id"):
            validate_event_stream(events)

    def test_duplicate_primary_opportunities_rejected(self):
        events = self._events()
        duplicate = copy.deepcopy(events[2])
        duplicate["event_id"] = 99
        events.append(duplicate)
        with self.assertRaisesRegex(ValueError, "duplicate primary opportunity"):
            validate_event_stream(events)

    def test_incomplete_trace_does_not_invent_sequence_success(self):
        result = evaluate_critical_sequences(self._events()[:3])
        self.assertFalse(any(result.values()))


if __name__ == "__main__":
    unittest.main()

