import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.models.target_rules import TargetRules
from core.modules.auto_target import AutoTarget


class FakeInput:

    def __init__(self, outcomes=None):
        self.keys = []
        self.outcomes = iter(outcomes) if outcomes is not None else None

    def press(self, key):
        self.keys.append(key)
        return True if self.outcomes is None else next(self.outcomes)


def create_state(
    *,
    exists=True,
    hp=100,
    hp_valid=True,
    hp_observed_at=0.0,
    selection_id=1,
    name="Enemy",
):
    return SimpleNamespace(
        target=SimpleNamespace(
            exists=exists,
            hp_percent=hp,
            hp_valid=hp_valid,
            hp_observed_at=hp_observed_at,
            selection_id=selection_id,
            name=name,
            level=1,
        )
    )


class AutoTargetProgressTests(unittest.TestCase):

    @staticmethod
    def update_at(module, state, now, *, refresh_hp=True):
        if (
            refresh_hp
            and state.target.exists
            and state.target.hp_valid
        ):
            state.target.hp_observed_at = now
        with patch(
            "core.modules.auto_target.time.perf_counter",
            return_value=now,
        ):
            return module.update(state)

    def test_living_target_is_kept_then_changed_after_ten_seconds(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=100)

        self.assertFalse(self.update_at(module, state, 0.0))
        self.assertFalse(self.update_at(module, state, 9.999))
        self.assertTrue(self.update_at(module, state, 10.0))

        self.assertEqual(input_manager.keys, ["E"])

    def test_dead_target_requests_a_new_selection_immediately(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())

        self.assertTrue(
            self.update_at(module, create_state(hp=0), 0.0)
        )

        self.assertEqual(input_manager.keys, ["E"])

    def test_unvalidated_zero_hp_is_held_as_unknown(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(
            hp=0,
            hp_valid=False,
            hp_observed_at=None,
        )

        self.assertFalse(
            self.update_at(module, state, 0.0, refresh_hp=False)
        )

        self.assertEqual(input_manager.keys, [])

    def test_meaningful_damage_starts_a_new_progress_window(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=100)

        self.update_at(module, state, 0.0)
        state.target.hp_percent = 50
        self.assertFalse(self.update_at(module, state, 9.0))
        self.assertFalse(self.update_at(module, state, 18.999))
        self.assertTrue(self.update_at(module, state, 19.0))

        self.assertEqual(input_manager.keys, ["E"])

    def test_five_points_from_ninety_is_not_ten_percent_progress(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=90)

        self.update_at(module, state, 0.0)
        state.target.hp_percent = 85
        self.assertFalse(self.update_at(module, state, 5.0))
        self.assertTrue(self.update_at(module, state, 10.0))

        self.assertEqual(input_manager.keys, ["E"])

    def test_progress_must_be_strictly_below_ninety_percent(self):
        exact_input = FakeInput()
        exact_module = AutoTarget(exact_input, TargetRules())
        exact_state = create_state(hp=100)
        self.update_at(exact_module, exact_state, 0.0)
        exact_state.target.hp_percent = 90
        self.assertFalse(self.update_at(exact_module, exact_state, 5.0))
        self.assertTrue(self.update_at(exact_module, exact_state, 10.0))

        below_input = FakeInput()
        below_module = AutoTarget(below_input, TargetRules())
        below_state = create_state(hp=100)
        self.update_at(below_module, below_state, 0.0)
        below_state.target.hp_percent = 89.99
        self.assertFalse(self.update_at(below_module, below_state, 5.0))
        self.assertFalse(self.update_at(below_module, below_state, 10.0))

        self.assertEqual(exact_input.keys, ["E"])
        self.assertEqual(below_input.keys, [])

    def test_new_selection_restarts_the_blocked_timer(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=100, selection_id=1)

        self.update_at(module, state, 0.0)
        state.target.selection_id = 2
        self.assertFalse(self.update_at(module, state, 9.0))
        self.assertFalse(self.update_at(module, state, 10.0))
        self.assertTrue(self.update_at(module, state, 19.0))

        self.assertEqual(input_manager.keys, ["E"])

    def test_name_ocr_does_not_restart_the_same_selection(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=100, selection_id=7, name="")

        self.update_at(module, state, 0.0)
        state.target.name = "Enemy resolved by OCR"
        self.assertFalse(self.update_at(module, state, 9.0))
        self.assertTrue(self.update_at(module, state, 10.0))

        self.assertEqual(input_manager.keys, ["E"])

    def test_selection_request_is_not_spammed_while_vision_settles(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=0)

        self.assertTrue(self.update_at(module, state, 0.0))
        self.assertFalse(self.update_at(module, state, 0.25))
        self.assertFalse(self.update_at(module, state, 0.999))
        self.assertFalse(self.update_at(module, state, 1.0))
        self.assertFalse(self.update_at(module, state, 3.999))
        self.assertTrue(self.update_at(module, state, 4.0))

        self.assertEqual(input_manager.keys, ["E", "E"])

    def test_new_selection_is_held_for_four_seconds(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(exists=False, hp=0, selection_id=0, name="")

        self.assertTrue(self.update_at(module, state, 0.0))
        state.target.exists = True
        state.target.selection_id = 2
        self.assertFalse(self.update_at(module, state, 0.1))
        self.assertFalse(self.update_at(module, state, 4.099))
        self.assertTrue(self.update_at(module, state, 4.101))

        self.assertEqual(input_manager.keys, ["E", "E"])

    def test_new_target_after_request_is_held_without_an_extra_e(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=0, selection_id=1)

        self.assertTrue(self.update_at(module, state, 0.0))
        state.target.selection_id = 2
        state.target.hp_percent = 100
        self.assertFalse(self.update_at(module, state, 0.1))
        self.assertFalse(self.update_at(module, state, 1.0))

        self.assertEqual(input_manager.keys, ["E"])

    def test_same_visual_identity_gets_a_fresh_window_after_e(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=100, selection_id=1)

        self.update_at(module, state, 0.0)
        self.assertTrue(self.update_at(module, state, 10.0))
        self.assertFalse(self.update_at(module, state, 11.0))
        self.assertFalse(self.update_at(module, state, 20.999))
        self.assertTrue(self.update_at(module, state, 21.0))

        self.assertEqual(input_manager.keys, ["E", "E"])

    def test_rejected_filter_changes_target_without_waiting_ten_seconds(self):
        input_manager = FakeInput()
        rules = TargetRules()
        rules.set_blacklist(["Ignored"], enabled=True)
        module = AutoTarget(input_manager, rules)

        self.assertTrue(
            self.update_at(
                module,
                create_state(hp=100, name="Ignored"),
                0.0,
            )
        )

        self.assertEqual(input_manager.keys, ["E"])

    def test_failed_input_does_not_arm_the_selection_wait(self):
        input_manager = FakeInput([False, True])
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(exists=False, hp=0, selection_id=0, name="")

        self.assertFalse(self.update_at(module, state, 0.0))
        self.assertTrue(self.update_at(module, state, 0.05))

        self.assertEqual(input_manager.keys, ["E", "E"])
        self.assertTrue(module._selection_request_pending)

    def test_stale_hp_does_not_consume_the_progress_window(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=100)

        self.assertFalse(self.update_at(module, state, 0.0))
        self.assertFalse(
            self.update_at(module, state, 10.0, refresh_hp=False)
        )

        state.target.hp_observed_at = 10.0
        self.assertFalse(
            self.update_at(module, state, 10.0, refresh_hp=False)
        )
        state.target.hp_observed_at = 20.0
        self.assertTrue(
            self.update_at(module, state, 20.0, refresh_hp=False)
        )

        self.assertEqual(input_manager.keys, ["E"])


if __name__ == "__main__":
    unittest.main()
