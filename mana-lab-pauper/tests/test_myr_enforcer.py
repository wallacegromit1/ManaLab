import unittest

from mana_lab.validation import search_t2_myr_enforcer
from common import deck_spec


class MyrEnforcerTests(unittest.TestCase):
    def test_t2_enforcer_impossible_in_relaxed_exact_shell_search(self):
        self.assertIsNone(search_t2_myr_enforcer(deck_spec()))


if __name__ == "__main__":
    unittest.main()

