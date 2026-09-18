import copy
import unittest

from mana_lab.mulligan import BASELINE_MULLIGAN, london_mulligan
from mana_lab.policies import BASELINE_ACTION_POLICY, BASELINE_SCRY_POLICY
from mana_lab.simulator import apply_planner_action, choose_next_action
from mana_lab.state import Permanent, make_card
from common import deck_spec, library, state_with_lands


class RunCCausalTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def _root(self, state):
        action = choose_next_action(
            state, self.deck, action_policy_name=BASELINE_ACTION_POLICY, scry_policy_name=BASELINE_SCRY_POLICY
        )
        return None if action is None else action.key

    def _state(self, spell, hidden):
        state = state_with_lands(self.deck, ["Seat of the Synod", "Vault of Whispers", "Great Furnace"], library_names=hidden)
        state.turn = 2
        state.hand = [
            make_card("spell", spell, artifact=spell in {"Baleful Strix", "Cryogen Relic", "Giant's Boulder"}, creature=spell == "Baleful Strix")
        ]
        return state

    def test_identical_visible_state_different_hidden_library_same_root(self):
        a = self._state("Thoughtcast", ("Ancient Den", "Dispatch"))
        b = self._state("Thoughtcast", ("Myr Enforcer", "Blood Fountain"))
        self.assertEqual(self._root(a), self._root(b))

    def test_thoughtcast_precast_invariant(self):
        self.assertEqual(self._root(self._state("Thoughtcast", ("A", "B"))), self._root(self._state("Thoughtcast", ("X", "Y"))))

    def test_strix_precast_invariant(self):
        self.assertEqual(self._root(self._state("Baleful Strix", ("A",))), self._root(self._state("Baleful Strix", ("X",))))

    def test_cryogen_predraw_invariant(self):
        self.assertEqual(self._root(self._state("Cryogen Relic", ("A",))), self._root(self._state("Cryogen Relic", ("X",))))

    def test_boulder_prescry_invariant(self):
        self.assertEqual(self._root(self._state("Giant's Boulder", ("A", "B", "C"))), self._root(self._state("Giant's Boulder", ("X", "Y", "Z"))))

    def test_bargain_sacrifice_choice_invariant(self):
        roots = []
        for hidden in (("Ancient Den", "Dispatch"), ("Myr Enforcer", "Thoughtcast")):
            state = state_with_lands(self.deck, ["Vault of Whispers", "Seat of the Synod"], library_names=hidden)
            state.turn = 3
            state.hand = [make_card("b", "Reckoner's Bargain")]
            state.battlefield.append(Permanent(make_card("n", "Nihil Spellbomb", artifact=True)))
            roots.append(self._root(state))
        self.assertEqual(roots[0], roots[1])

    def test_hawk_return_choice_invariant(self):
        roots = []
        for hidden in (("Ancient Den",), ("Thoughtcast",)):
            state = state_with_lands(self.deck, ["Ancient Den", "Vault of Whispers"], library_names=hidden)
            state.turn = 2
            state.hand = [make_card("h", "Glint Hawk", creature=True)]
            roots.append(self._root(state))
        self.assertEqual(roots[0], roots[1])

    def test_payment_choice_invariant(self):
        roots = []
        for hidden in (("A",), ("B",)):
            state = state_with_lands(self.deck, ["Seat of the Synod", "Great Furnace"], library_names=hidden)
            state.turn = 2
            state.hand = [make_card("c", "Cryogen Relic", artifact=True)]
            roots.append(self._root(state))
        self.assertEqual(roots[0], roots[1])

    def test_after_draw_later_decision_may_change(self):
        first_keys = []
        later = []
        for hidden in (("Ancient Den", "Dispatch"), ("Myr Enforcer", "Dispatch")):
            state = self._state("Thoughtcast", hidden)
            first = choose_next_action(state, self.deck, action_policy_name=BASELINE_ACTION_POLICY, scry_policy_name=BASELINE_SCRY_POLICY)
            first_keys.append(first.key)
            apply_planner_action(state, self.deck, first, scry_policy_name=BASELINE_SCRY_POLICY, reveal_information=True)
            next_action = choose_next_action(state, self.deck, action_policy_name=BASELINE_ACTION_POLICY, scry_policy_name=BASELINE_SCRY_POLICY)
            later.append(None if next_action is None else next_action.label)
        self.assertEqual(first_keys[0], first_keys[1])
        self.assertNotEqual([card.name for card in self._state("Thoughtcast", ("Ancient Den",)).library], [card.name for card in self._state("Thoughtcast", ("Myr Enforcer",)).library])

    def test_mulligan_keep_and_bottom_ignore_hidden(self):
        seven = [
            make_card("d", "Ancient Den", artifact=True, land=True), make_card("s", "Seat of the Synod", artifact=True, land=True),
            make_card("b", "Giant's Boulder", artifact=True), make_card("g", "Glint Hawk", creature=True),
            make_card("t", "Thoughtcast"), make_card("m", "Myr Enforcer", artifact=True, creature=True), make_card("c", "Cryogen Relic", artifact=True),
        ]
        results = []
        for hidden in ("Hidden A", "Hidden B"):
            results.append(london_mulligan(self.deck, BASELINE_MULLIGAN, lambda attempt, h=hidden: (copy.deepcopy(seven), [make_card("x", h)])))
        self.assertEqual(tuple(card.uid for card in results[0].hand), tuple(card.uid for card in results[1].hand))


if __name__ == "__main__":
    unittest.main()
