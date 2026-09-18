import unittest

from mana_lab.policies import BASELINE_ACTION_POLICY, ActionOption, choose_action


def option(key, **updates):
    values = dict(
        key=key, due_executions=0, artifact_count=0, cards_drawn=0,
        reserve_preserved=True, untapped_resources=0, land_loss=0,
    )
    values.update(updates)
    return ActionOption(**values)


class PolicyPrecedenceTests(unittest.TestCase):
    def test_hard_deadline_overrides_reserve(self):
        selected = choose_action([
            option("reserve", reserve_preserved=True),
            option("deadline", reserve_preserved=False, hard_deadline_executions=1),
        ], BASELINE_ACTION_POLICY)
        self.assertEqual(selected.key, "deadline")

    def test_reserve_precedes_ordinary_due_execution(self):
        selected = choose_action([
            option("reserve", reserve_preserved=True),
            option("due", reserve_preserved=False, due_executions=1),
        ], BASELINE_ACTION_POLICY)
        self.assertEqual(selected.key, "reserve")

    def test_land_loss_precedes_promised_draw(self):
        selected = choose_action([
            option("keep-land"),
            option("draw", land_loss=1, cards_drawn=2, information_value=190),
        ], BASELINE_ACTION_POLICY)
        self.assertEqual(selected.key, "keep-land")

    def test_artifact_threshold_precedes_optional_velocity(self):
        selected = choose_action([
            option("metalcraft", artifact_count=3),
            option("velocity", artifact_count=2, cards_drawn=2, information_value=190),
        ], BASELINE_ACTION_POLICY)
        self.assertEqual(selected.key, "metalcraft")

    def test_strategic_features_precede_canonical_key(self):
        selected = choose_action([
            option("aaa", future_joint_castability=0),
            option("zzz", future_joint_castability=1),
        ], BASELINE_ACTION_POLICY)
        self.assertEqual(selected.key, "zzz")


if __name__ == "__main__":
    unittest.main()
