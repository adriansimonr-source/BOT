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
    selection_id=1,
    name="Enemy",
    hp=100,
    hp_valid=True,
):
    return SimpleNamespace(
        target=SimpleNamespace(
            exists=exists,
            selection_id=selection_id,
            name=name,
            level=1,
            hp_percent=hp,
            hp_valid=hp_valid,
            hp_observed_at=0.0,
        )
    )


class AutoTargetSelectionTests(unittest.TestCase):
    @staticmethod
    def update_at(module, state, now):
        with patch(
            "core.modules.auto_target.time.perf_counter",
            return_value=now,
        ):
            return module.update(state)

    def test_stalled_target_cycles_after_the_default_timeout(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=100)

        self.assertFalse(self.update_at(module, state, 0.0))
        self.assertFalse(self.update_at(module, state, 9.999))
        self.assertTrue(self.update_at(module, state, 10.0))

        self.assertEqual(input_manager.keys, ["E"])

    def test_stall_timeout_uses_the_configured_milliseconds(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        module.target_interval = 6000
        state = create_state(hp=100)

        self.assertFalse(self.update_at(module, state, 1.0))
        self.assertFalse(self.update_at(module, state, 6.999))
        self.assertTrue(self.update_at(module, state, 7.0))

        self.assertEqual(input_manager.keys, ["E"])

    def test_observed_damage_restarts_the_timeout_if_hp_becomes_unknown(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=100)

        self.assertFalse(self.update_at(module, state, 0.0))
        state.target.hp_percent = 99
        self.assertFalse(self.update_at(module, state, 9.0))
        state.target.hp_valid = False
        state.target.hp_percent = 100
        self.assertFalse(self.update_at(module, state, 18.999))
        self.assertTrue(self.update_at(module, state, 19.0))

        self.assertEqual(input_manager.keys, ["E"])

    def test_unknown_hp_cycles_when_no_damage_was_ever_observed(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=0, hp_valid=False)

        self.assertFalse(self.update_at(module, state, 0.0))
        self.assertFalse(self.update_at(module, state, 9.999))
        self.assertTrue(self.update_at(module, state, 10.0))

        self.assertEqual(input_manager.keys, ["E"])

    def test_temporary_unknown_hp_does_not_restart_the_stall_timeout(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=100)

        self.assertFalse(self.update_at(module, state, 0.0))
        state.target.hp_valid = False
        self.assertFalse(self.update_at(module, state, 5.0))
        state.target.hp_valid = True
        self.assertTrue(self.update_at(module, state, 10.0))

        self.assertEqual(input_manager.keys, ["E"])

    def test_stable_partial_hp_also_cycles_a_stalled_self_selection(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=80)

        self.assertFalse(self.update_at(module, state, 0.0))
        self.assertFalse(self.update_at(module, state, 9.999))
        self.assertTrue(self.update_at(module, state, 10.0))

        self.assertEqual(input_manager.keys, ["E"])

    def test_first_partial_reading_does_not_move_the_selection_deadline(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=0, hp_valid=False)

        self.assertFalse(self.update_at(module, state, 0.0))
        state.target.hp_valid = True
        state.target.hp_percent = 80
        self.assertFalse(self.update_at(module, state, 9.0))
        self.assertTrue(self.update_at(module, state, 10.0))

        self.assertEqual(input_manager.keys, ["E"])

    def test_hp_oscillation_does_not_fake_repeated_progress(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=80)

        self.assertFalse(self.update_at(module, state, 0.0))
        state.target.hp_percent = 82
        self.assertFalse(self.update_at(module, state, 4.0))
        state.target.hp_percent = 80
        self.assertFalse(self.update_at(module, state, 8.0))
        self.assertTrue(self.update_at(module, state, 10.0))

        self.assertEqual(input_manager.keys, ["E"])

    def test_identity_change_restarts_the_progress_timeout(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=100, selection_id=1)

        self.assertFalse(self.update_at(module, state, 0.0))
        state.target.selection_id = 2
        self.assertFalse(self.update_at(module, state, 9.0))
        self.assertFalse(self.update_at(module, state, 10.0))
        self.assertTrue(self.update_at(module, state, 19.0))

        self.assertEqual(input_manager.keys, ["E"])

    def test_failed_stalled_target_send_retries_without_restarting_timeout(self):
        input_manager = FakeInput([False, True])
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=100)

        self.assertFalse(self.update_at(module, state, 0.0))
        self.assertFalse(self.update_at(module, state, 10.0))
        self.assertTrue(self.update_at(module, state, 10.05))

        self.assertEqual(input_manager.keys, ["E", "E"])

    def test_same_selection_retries_from_the_successful_press_time(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(hp=100)

        self.assertFalse(self.update_at(module, state, 0.0))
        self.assertTrue(self.update_at(module, state, 10.0))
        self.assertFalse(self.update_at(module, state, 11.0))
        self.assertFalse(self.update_at(module, state, 19.999))
        self.assertTrue(self.update_at(module, state, 20.0))

        self.assertEqual(input_manager.keys, ["E", "E"])

    def test_auto_target_does_not_require_hp_fields(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = SimpleNamespace(
            target=SimpleNamespace(
                exists=True,
                selection_id=1,
                name="Enemy",
                level=1,
            )
        )

        self.assertFalse(self.update_at(module, state, 50.0))
        self.assertEqual(input_manager.keys, [])

    def test_missing_target_requests_selection_and_respects_four_seconds(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(exists=False, selection_id=0, name="")

        self.assertTrue(self.update_at(module, state, 0.0))
        self.assertFalse(self.update_at(module, state, 0.999))
        self.assertFalse(self.update_at(module, state, 1.0))
        self.assertFalse(self.update_at(module, state, 3.999))
        self.assertTrue(self.update_at(module, state, 4.0))

        self.assertEqual(input_manager.keys, ["E", "E"])

    def test_new_allowed_selection_is_held_while_it_makes_progress(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(exists=False, selection_id=0, name="")

        self.assertTrue(self.update_at(module, state, 0.0))
        state.target.exists = True
        state.target.selection_id = 2
        state.target.name = "Enemy"
        state.target.hp_percent = 50
        self.assertFalse(self.update_at(module, state, 0.1))
        state.target.hp_percent = 40
        self.assertFalse(self.update_at(module, state, 9.0))
        self.assertFalse(self.update_at(module, state, 18.999))
        self.assertTrue(self.update_at(module, state, 19.0))

        self.assertEqual(input_manager.keys, ["E", "E"])

    def test_preexisting_ignored_target_changes_immediately(self):
        input_manager = FakeInput()
        rules = TargetRules()
        rules.set_blacklist(["Ignored"], enabled=True)
        module = AutoTarget(input_manager, rules)

        self.assertTrue(
            self.update_at(
                module,
                create_state(name="Ignored"),
                0.0,
            )
        )
        self.assertEqual(input_manager.keys, ["E"])

    def test_new_ignored_selection_is_held_for_four_seconds(self):
        input_manager = FakeInput()
        rules = TargetRules()
        rules.set_blacklist(["Ignored"], enabled=True)
        module = AutoTarget(input_manager, rules)
        state = create_state(exists=False, selection_id=0, name="")

        self.assertTrue(self.update_at(module, state, 0.0))
        state.target.exists = True
        state.target.selection_id = 2
        state.target.name = "Ignored"
        self.assertFalse(self.update_at(module, state, 0.1))
        self.assertFalse(self.update_at(module, state, 4.099))
        self.assertTrue(self.update_at(module, state, 4.101))

        self.assertEqual(input_manager.keys, ["E", "E"])

    def test_name_resolution_does_not_create_a_new_selection(self):
        input_manager = FakeInput()
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(selection_id=7, name="", hp=50)

        self.assertFalse(self.update_at(module, state, 0.0))
        state.target.name = "Resolved"
        self.assertFalse(self.update_at(module, state, 9.999))
        self.assertTrue(self.update_at(module, state, 10.0))

        self.assertEqual(input_manager.keys, ["E"])

    def test_failed_input_does_not_arm_the_selection_wait(self):
        input_manager = FakeInput([False, True])
        module = AutoTarget(input_manager, TargetRules())
        state = create_state(exists=False, selection_id=0, name="")

        self.assertFalse(self.update_at(module, state, 0.0))
        self.assertTrue(self.update_at(module, state, 0.05))

        self.assertEqual(input_manager.keys, ["E", "E"])
        self.assertTrue(module._selection_request_pending)


if __name__ == "__main__":
    unittest.main()
