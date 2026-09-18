import copy
import unittest

from mana_lab.simulator import _visible_search_key
from mana_lab.state import StackItem, make_card
from common import deck_spec, state_with_lands


class StateDeduplicationTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def key(self, state):
        return _visible_search_key(state, 0, 0, 0, 0, ())

    def test_tapped_identity_land_drop_and_pool_are_distinct(self):
        base = state_with_lands(self.deck, ["Ancient Den", "Ancient Den"])
        tapped = copy.deepcopy(base)
        tapped.battlefield[0].tapped = True
        self.assertNotEqual(self.key(base), self.key(tapped))
        no_drop = copy.deepcopy(base)
        no_drop.land_drop_available = False
        self.assertNotEqual(self.key(base), self.key(no_drop))
        pool = copy.deepcopy(base)
        pool.mana_pool.add("B")
        self.assertNotEqual(self.key(base), self.key(pool))

    def test_stack_and_unresolved_information_are_distinct(self):
        base = state_with_lands(self.deck, ["Vault of Whispers"])
        stack = copy.deepcopy(base)
        stack.push(StackItem("Cryogen Relic leave draw", lambda game: None))
        self.assertNotEqual(self.key(base), self.key(stack))
        information = copy.deepcopy(base)
        information.log("information_node", kind="draw", count=1, reason="Baleful Strix")
        self.assertNotEqual(self.key(base), self.key(information))

    def test_boulder_and_target_identity_are_preserved(self):
        base = state_with_lands(self.deck, ["Ancient Den"])
        first = copy.deepcopy(base)
        second = copy.deepcopy(base)
        first.hand = [make_card("b1", "Giant's Boulder", artifact=True)]
        second.hand = [make_card("b2", "Giant's Boulder", artifact=True)]
        self.assertNotEqual(self.key(first), self.key(second))


if __name__ == "__main__":
    unittest.main()
