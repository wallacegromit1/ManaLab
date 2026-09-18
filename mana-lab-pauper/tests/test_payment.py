import unittest

from mana_lab.mana import ManaCost, ManaPool, affinity_cost, sources_can_pay
from mana_lab.payment import execute_payment, find_payment_plan
from mana_lab.state import GameState, Permanent, make_card
from common import deck_spec, land_permanent, state_with_lands


class PaymentTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def test_pool_conserves_and_colored_pips_are_strict(self):
        pool = ManaPool()
        pool.add("W")
        self.assertTrue(pool.can_pay(ManaCost(colored={"W": 1})))
        self.assertFalse(pool.can_pay(ManaCost(colored={"U": 1})))
        pool.pay(ManaCost(colored={"W": 1}))
        self.assertEqual(pool.total, 0)

    def test_generic_accepts_colored_mana(self):
        pool = ManaPool()
        pool.add("R", 2)
        pool.pay(ManaCost(generic=2))
        self.assertEqual(pool.total, 0)

    def test_affinity_reduces_generic_only(self):
        cost = affinity_cost(4, {"U": 1}, 8)
        self.assertEqual(cost.generic, 0)
        self.assertEqual(cost.colored, {"U": 1})

    def test_distinct_sources_for_strix(self):
        self.assertFalse(sources_can_pay([("U", "B")], ManaCost(colored={"U": 1, "B": 1})))
        self.assertTrue(sources_can_pay([("U",), ("B",)], ManaCost(colored={"U": 1, "B": 1})))

    def test_boulder_filter_is_net_zero_and_taps(self):
        state = state_with_lands(self.deck, ["Ancient Den", "Ancient Den"])
        boulder = Permanent(make_card("b", "Giant's Boulder", artifact=True))
        state.battlefield.append(boulder)
        plan = find_payment_plan(state, ManaCost(colored={"U": 1, "B": 1}))
        self.assertIsNone(plan, "one Boulder cannot repair two missing colored pips")
        plan = find_payment_plan(state, ManaCost(colored={"U": 1}))
        self.assertIsNotNone(plan)
        execute_payment(state, plan)
        self.assertEqual(state.mana_pool.total, 0)
        self.assertTrue(boulder.tapped)

    def test_two_boulders_can_filter_two_sources(self):
        state = state_with_lands(self.deck, ["Ancient Den", "Ancient Den"])
        state.battlefield += [
            Permanent(make_card("b1", "Giant's Boulder", artifact=True)),
            Permanent(make_card("b2", "Giant's Boulder", artifact=True)),
        ]
        plan = find_payment_plan(state, ManaCost(colored={"U": 1, "B": 1}))
        self.assertIsNotNone(plan)

    def test_phase_boundary_clears_pool(self):
        state = GameState()
        state.mana_pool.add("W")
        state.end_phase("opponent")
        self.assertEqual(state.mana_pool.total, 0)


if __name__ == "__main__":
    unittest.main()

