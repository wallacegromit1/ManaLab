import unittest

from mana_lab.mana import ManaCost
from mana_lab.payment import enumerate_payment_plans, execute_payment
from mana_lab.state import Permanent, make_card
from common import deck_spec, state_with_lands


class BoulderMetricTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def filtered_event(self, land, color):
        state = state_with_lands(self.deck, [land])
        state.battlefield.append(Permanent(make_card("b", "Giant's Boulder", artifact=True)))
        plan = next(
            p for p in enumerate_payment_plans(state, ManaCost(colored={color: 1}))
            if any(use.via_boulder for use in p.uses)
        )
        execute_payment(state, plan)
        return next(e for e in state.events if e["event"] == "boulder_filter")

    def test_used_but_not_rescue_when_native_payment_exists(self):
        event = self.filtered_event("Great Furnace", "R")
        self.assertTrue(event["boulder_used"])
        self.assertFalse(event["rescue"])
        self.assertFalse(event["dependency"])

    def test_strictly_required_is_rescue_and_dependency(self):
        event = self.filtered_event("Ancient Den", "R")
        self.assertTrue(event["boulder_used"])
        self.assertTrue(event["rescue"])
        self.assertTrue(event["dependency"])

    def test_deployed_boulder_without_activation_has_no_usage_event(self):
        state = state_with_lands(self.deck, ["Ancient Den"])
        state.battlefield.append(Permanent(make_card("b", "Giant's Boulder", artifact=True)))
        self.assertFalse(any(e["event"] in {"boulder_filter", "boulder_usage"} for e in state.events))


if __name__ == "__main__":
    unittest.main()
