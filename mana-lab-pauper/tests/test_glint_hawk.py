import unittest

from mana_lab.effects import resolve_glint_hawk
from mana_lab.state import GameState, Permanent, make_card
from common import deck_spec, land_permanent, library


class GlintHawkTests(unittest.TestCase):
    def setUp(self):
        self.deck = deck_spec()

    def test_no_artifact_sacrifices_hawk(self):
        state = GameState()
        hawk = resolve_glint_hawk(state, make_card("h", "Glint Hawk", creature=True), None)
        state.resolve_all()
        self.assertNotIn(hawk, state.battlefield)

    def test_artifact_land_is_legal_return_and_resource_is_removed(self):
        state = GameState()
        land = land_permanent(self.deck, "Ancient Den", tapped=False)
        state.battlefield.append(land)
        resolve_glint_hawk(state, make_card("h", "Glint Hawk", creature=True), land)
        state.resolve_all()
        self.assertIn(land.card, state.hand)
        self.assertEqual(state.artifact_count(), 0)

    def test_cryogen_return_draws_and_hawk_remains(self):
        state = GameState(library=library("A"))
        cryogen = Permanent(make_card("c", "Cryogen Relic", artifact=True))
        state.battlefield.append(cryogen)
        hawk = resolve_glint_hawk(state, make_card("h", "Glint Hawk", creature=True), cryogen)
        state.resolve_all()
        self.assertIn(hawk, state.battlefield)
        self.assertEqual([card.name for card in state.hand], ["Cryogen Relic", "A"])

    def test_boulder_return_clears_tapped_state_as_object_leaves(self):
        state = GameState()
        boulder = Permanent(make_card("b", "Giant's Boulder", artifact=True), tapped=True)
        state.battlefield.append(boulder)
        resolve_glint_hawk(state, make_card("h", "Glint Hawk", creature=True), boulder)
        state.resolve_all()
        self.assertIn(boulder.card, state.hand)
        self.assertNotIn(boulder, state.battlefield)


if __name__ == "__main__":
    unittest.main()

