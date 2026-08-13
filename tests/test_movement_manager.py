import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.models.bot_settings import BotMode, BotSettings
from core.modules.movement_manager import MovementManager, MovementStatus


class FakeInput:

    def __init__(self):
        self.presses = []
        self.releases = []
        self.held = set()

    def press(self, key, hold_ms=50):
        self.presses.append((key, hold_ms))
        self.held.add(key)
        return True

    def release(self, key):
        self.releases.append(key)
        was_held = key in self.held
        self.held.discard(key)
        return was_held

    def is_held(self, key):
        return key in self.held


class BusyInput(FakeInput):

    def press(self, key, hold_ms=50):
        return False


def create_state(x=120, y=100, *, radius_mode=BotMode.STATIC_POINT):
    player = SimpleNamespace(
        x=x,
        y=y,
        start_x=100,
        start_y=100,
        position_locked=True,
        position_valid=True,
        position_updated_at=0.0,
        position_revision=1,
        position_history=[],
        fresh=True,
    )
    player.has_fresh_position = lambda max_age=None: player.fresh
    state = SimpleNamespace(
        connected=True,
        player=player,
        target=SimpleNamespace(exists=False),
        in_combat=False,
        navigation_active=False,
        navigation_status="idle",
        navigation_reason="",
        navigation_distance=None,
        navigation_key=None,
    )
    settings = BotSettings()
    settings.mode = radius_mode
    return state, settings


class MovementManagerTests(unittest.TestCase):

    @staticmethod
    def update_at(
        module,
        state,
        now,
        *,
        x=None,
        y=None,
        new_sample=False,
    ):
        if x is not None:
            state.player.x = x
        if y is not None:
            state.player.y = y
        if new_sample:
            state.player.position_revision += 1
            state.player.position_history.append(
                (
                    state.player.position_revision,
                    now,
                    state.player.x,
                    state.player.y,
                )
            )
        with patch(
            "core.modules.movement_manager.time.perf_counter",
            return_value=now,
        ):
            return module.update(state)

    def start_forced_return(self, module, state, *, first=1.0):
        self.assertFalse(self.update_at(module, state, first))
        self.assertEqual(module._outside_samples, 1)
        sent = self.update_at(
            module,
            state,
            first + 0.1,
            new_sample=True,
        )
        self.assertTrue(sent)
        return first + 0.1

    def evaluate_current_command(
        self,
        module,
        state,
        *,
        x=None,
        y=None,
    ):
        now = module._command["observe_after"] + 0.01
        return self.update_at(
            module,
            state,
            now,
            x=x,
            y=y,
            new_sample=True,
        )

    def test_outside_radius_requires_two_fresh_samples(self):
        state, settings = create_state()
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)

        self.assertFalse(self.update_at(module, state, 1.0))
        self.assertEqual(input_manager.presses, [])

        state.player.x = 121
        self.assertFalse(self.update_at(module, state, 1.05))
        self.assertEqual(input_manager.presses, [])

        self.assertTrue(
            self.update_at(module, state, 1.1, new_sample=True)
        )
        self.assertEqual(input_manager.presses, [("W", 400)])
        self.assertEqual(module.status, MovementStatus.RETURNING)
        self.assertEqual(state.navigation_reason, "fuera_de_radio")

    def test_target_pauses_forced_return_and_then_resumes_same_attempt(self):
        state, settings = create_state()
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)
        self.start_forced_return(module, state)

        state.target.exists = True
        self.assertFalse(self.update_at(module, state, 1.2))

        self.assertEqual(module.status, MovementStatus.PAUSED)
        self.assertFalse(state.navigation_active)
        self.assertEqual(state.navigation_reason, "objetivo_o_combate")
        self.assertIn("W", input_manager.releases)
        self.assertEqual(module._attempts, 1)

        state.target.exists = False
        self.assertTrue(self.update_at(module, state, 1.3))

        self.assertEqual(module.status, MovementStatus.RETURNING)
        self.assertTrue(state.navigation_active)
        self.assertEqual(state.navigation_reason, "fuera_de_radio")
        self.assertEqual(module._attempts, 1)
        self.assertEqual([key for key, _ in input_manager.presses], ["W", "W"])

    def test_two_reliable_improvements_confirm_a_direction(self):
        state, settings = create_state()
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)
        self.start_forced_return(module, state)

        self.assertTrue(
            self.evaluate_current_command(module, state, x=118)
        )
        self.assertEqual(module._candidate_key, "W")
        self.assertIsNone(module._preferred_key)
        self.assertEqual(module.reason, "confirmando_direccion")

        self.assertTrue(
            self.evaluate_current_command(module, state, x=116)
        )
        self.assertIsNone(module._candidate_key)
        self.assertEqual(module._preferred_key, "W")
        self.assertEqual(
            [key for key, _ in input_manager.presses],
            ["W", "W", "W"],
        )
        self.assertEqual(module._command["phase"], "follow")

    def test_every_generated_movement_pulse_is_at_most_650_ms(self):
        state, settings = create_state(x=400)
        settings.movement_hold_ms = 10_000
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)
        self.start_forced_return(module, state)

        self.evaluate_current_command(module, state, x=398)
        self.evaluate_current_command(module, state, x=396)

        self.assertEqual(
            input_manager.presses,
            [("W", 500), ("W", 500), ("W", 650)],
        )
        self.assertTrue(
            all(
                100 <= hold_ms <= module.MAX_DRIVE_HOLD_MS
                for _, hold_ms in input_manager.presses
            )
        )

    def test_coordinate_sample_during_hold_waits_for_a_post_settle_sample(self):
        state, settings = create_state()
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)
        sent_at = self.start_forced_return(module, state)
        observe_after = module._command["observe_after"]

        self.assertFalse(
            self.update_at(
                module,
                state,
                sent_at + 0.1,
                x=118,
                new_sample=True,
            )
        )
        self.assertLess(sent_at + 0.1, observe_after)
        self.assertEqual(input_manager.presses, [("W", 400)])
        self.assertEqual(module._command["revision"], 2)

        self.assertFalse(self.update_at(module, state, observe_after + 0.01))
        self.assertEqual(input_manager.presses, [("W", 400)])
        self.assertEqual(module.policy.estimates["W"].samples, 0)

        self.assertTrue(
            self.update_at(
                module,
                state,
                observe_after + 0.02,
                x=116,
                new_sample=True,
            )
        )
        self.assertEqual([key for key, _ in input_manager.presses], ["W", "W"])
        self.assertEqual(module.policy.estimates["W"].samples, 1)

    def test_missing_coordinate_after_command_enters_cooldown(self):
        state, settings = create_state()
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)
        self.start_forced_return(module, state)
        deadline = module._command["sample_deadline"]

        self.assertFalse(self.update_at(module, state, deadline + 0.01))

        self.assertEqual(module.status, MovementStatus.COOLDOWN)
        self.assertFalse(state.navigation_active)
        self.assertEqual(state.navigation_reason, "sin_coordenada_nueva")
        self.assertIsNone(module._command)

    def test_busy_input_enters_cooldown_after_750_ms(self):
        state, settings = create_state()
        input_manager = BusyInput()
        module = MovementManager(input_manager, settings)

        self.assertFalse(self.update_at(module, state, 1.0))
        self.assertFalse(
            self.update_at(module, state, 1.1, new_sample=True)
        )
        self.assertEqual(module.status, MovementStatus.RETURNING)
        self.assertEqual(module.reason, "esperando_entrada")

        self.assertFalse(self.update_at(module, state, 1.84))
        self.assertEqual(module.status, MovementStatus.RETURNING)

        self.assertFalse(self.update_at(module, state, 1.86))
        self.assertEqual(module.status, MovementStatus.COOLDOWN)
        self.assertEqual(module.reason, "entrada_ocupada")
        self.assertFalse(state.navigation_active)

    def test_watchdog_cools_down_retries_once_and_then_fails(self):
        state, settings = create_state()
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)
        started_at = self.start_forced_return(module, state)

        self.assertFalse(
            self.update_at(
                module,
                state,
                started_at + module.NO_PROGRESS_SECONDS + 0.01,
            )
        )
        self.assertEqual(module.status, MovementStatus.COOLDOWN)
        self.assertEqual(module.reason, "retorno_sin_progreso")
        self.assertFalse(state.navigation_active)

        retry_at = module._retry_not_before
        self.assertFalse(self.update_at(module, state, retry_at - 0.01))
        self.assertEqual(len(input_manager.presses), 1)
        self.assertTrue(self.update_at(module, state, retry_at + 0.01))
        self.assertEqual(module._attempts, 2)
        self.assertEqual(len(input_manager.presses), 2)

        second_started_at = module._attempt_started_at
        self.assertFalse(
            self.update_at(
                module,
                state,
                second_started_at + module.NO_PROGRESS_SECONDS + 0.01,
            )
        )
        self.assertEqual(module.status, MovementStatus.COOLDOWN)

        exhausted_at = module._retry_not_before + 0.01
        self.assertFalse(self.update_at(module, state, exhausted_at))
        self.assertEqual(module.status, MovementStatus.FAILED)
        self.assertEqual(module.reason, "retorno_agotado")
        self.assertFalse(state.navigation_active)
        self.assertEqual(len(input_manager.presses), module.MAX_ATTEMPTS)

        self.assertFalse(self.update_at(module, state, exhausted_at + 20.0))
        self.assertEqual(len(input_manager.presses), module.MAX_ATTEMPTS)

    def test_failed_state_recovers_at_origin_and_can_return_again(self):
        state, settings = create_state()
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)
        module._game_state = state
        module._origin = (100, 100)
        module.status = MovementStatus.FAILED
        module.reason = "retorno_agotado"
        module._attempts = module.MAX_ATTEMPTS

        self.assertFalse(
            self.update_at(
                module,
                state,
                1.0,
                x=100,
                y=100,
                new_sample=True,
            )
        )
        self.assertEqual(module.status, MovementStatus.IDLE)
        self.assertEqual(module.reason, "en_posicion")

        self.assertFalse(
            self.update_at(
                module,
                state,
                2.0,
                x=120,
                y=100,
                new_sample=True,
            )
        )
        self.assertTrue(
            self.update_at(module, state, 2.1, new_sample=True)
        )
        self.assertEqual(module.status, MovementStatus.RETURNING)

    def test_combat_pause_reduces_learned_orientation_confidence(self):
        state, settings = create_state()
        module = MovementManager(FakeInput(), settings)
        module.policy.observe(
            "W",
            400,
            (120, 100),
            (118, 100),
            (100, 100),
        )
        confidence = module.policy.confidence_for("W")
        self.start_forced_return(module, state)

        state.target.exists = True
        self.assertFalse(self.update_at(module, state, 1.2))

        paused_confidence = module.policy.confidence_for("W")
        self.assertLess(paused_confidence, confidence)

        self.assertFalse(self.update_at(module, state, 1.3))
        self.assertEqual(
            module.policy.confidence_for("W"),
            paused_confidence,
        )

    def test_external_pause_discards_the_command_without_learning_from_it(self):
        state, settings = create_state()
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)
        self.start_forced_return(module, state)

        with patch(
            "core.modules.movement_manager.time.perf_counter",
            return_value=1.2,
        ):
            self.assertTrue(module.suspend("bot_pausado"))

        self.assertEqual(module.status, MovementStatus.PAUSED)
        self.assertIsNone(module._command)
        self.assertIn("W", input_manager.releases)
        self.assertEqual(module.policy.estimates["W"].samples, 0)

        self.assertTrue(
            self.update_at(
                module,
                state,
                2.0,
                x=115,
                new_sample=True,
            )
        )
        self.assertEqual(module.policy.estimates["W"].samples, 0)

    def test_no_movement_uses_deterministic_search_then_cools_down(self):
        state, settings = create_state()
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)
        self.start_forced_return(module, state)

        for _ in range(8):
            self.evaluate_current_command(module, state)

        self.assertEqual(
            [key for key, _ in input_manager.presses],
            ["W", "A", "D", "A", "W", "D", "D", "W"],
        )
        self.assertEqual(module.status, MovementStatus.COOLDOWN)
        self.assertEqual(module.reason, "sin_direccion_util")
        self.assertFalse(state.navigation_active)

    def test_arrival_releases_movement_and_finishes_return(self):
        state, settings = create_state()
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)
        self.start_forced_return(module, state)

        self.assertFalse(
            self.evaluate_current_command(module, state, x=101)
        )

        self.assertEqual(module.status, MovementStatus.IDLE)
        self.assertEqual(module.reason, "en_posicion")
        self.assertFalse(state.navigation_active)
        self.assertIsNone(module._command)
        self.assertIn("W", input_manager.releases)

    def test_configured_radius_uses_euclidean_distance(self):
        cases = (
            (BotMode.STATIC_25, (115, 120), (116, 120), 25.0),
            (BotMode.STATIC_50, (130, 140), (131, 140), 50.0),
            (BotMode.STATIC_75, (145, 160), (146, 160), 75.0),
            (BotMode.STATIC_100, (160, 180), (161, 180), 100.0),
        )

        for mode, boundary, outside, radius in cases:
            with self.subTest(radius=radius, position="boundary"):
                state, settings = create_state(
                    x=boundary[0],
                    y=boundary[1],
                    radius_mode=mode,
                )
                input_manager = FakeInput()
                module = MovementManager(input_manager, settings)
                self.update_at(module, state, 1.0)
                self.update_at(module, state, 1.1, new_sample=True)

                self.assertAlmostEqual(state.navigation_distance, radius)
                self.assertEqual(input_manager.presses, [])

            with self.subTest(radius=radius, position="outside"):
                state, settings = create_state(
                    x=outside[0],
                    y=outside[1],
                    radius_mode=mode,
                )
                input_manager = FakeInput()
                module = MovementManager(input_manager, settings)
                self.start_forced_return(module, state)

                self.assertGreater(state.navigation_distance, radius)
                self.assertEqual(input_manager.presses, [("W", 400)])
                self.assertEqual(module.reason, "fuera_de_radio")

    def test_forced_return_finishes_inside_the_radius_hysteresis_band(self):
        state, settings = create_state(
            x=151,
            y=100,
            radius_mode=BotMode.STATIC_50,
        )
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)
        self.start_forced_return(module, state)

        self.assertFalse(
            self.evaluate_current_command(module, state, x=110)
        )

        self.assertEqual(module.status, MovementStatus.IDLE)
        self.assertEqual(module.reason, "en_posicion")
        self.assertLessEqual(
            state.navigation_distance,
            module.RETURN_ORIGIN_TOLERANCE,
        )

    def test_episode_reset_preserves_the_learned_motion_model(self):
        state, settings = create_state()
        module = MovementManager(FakeInput(), settings)
        module.policy.observe(
            "A",
            400,
            (120, 100),
            (117, 100),
            (100, 100),
        )

        module._reset_episode()

        self.assertEqual(module.policy.estimates["A"].samples, 1)
        self.assertEqual(
            module.policy.rank_keys((120, 100), (100, 100))[0],
            "A",
        )

    def test_second_return_tries_the_previously_learned_key_first(self):
        state, settings = create_state()
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)
        self.start_forced_return(module, state)

        self.evaluate_current_command(module, state)
        self.evaluate_current_command(module, state, x=118)
        self.evaluate_current_command(module, state, x=116)
        self.assertFalse(
            self.evaluate_current_command(module, state, x=101)
        )
        self.assertEqual(module.status, MovementStatus.IDLE)

        press_count = len(input_manager.presses)
        self.assertFalse(
            self.update_at(
                module,
                state,
                10.0,
                x=120,
                new_sample=True,
            )
        )
        self.assertTrue(
            self.update_at(module, state, 10.1, new_sample=True)
        )

        self.assertEqual(len(input_manager.presses), press_count + 1)
        self.assertEqual(input_manager.presses[-1][0], "A")

    def test_off_mode_and_stale_coordinates_never_move(self):
        state, settings = create_state(radius_mode=BotMode.OFF)
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)

        self.assertFalse(self.update_at(module, state, 1.0))
        self.assertFalse(
            self.update_at(module, state, 2.0, new_sample=True)
        )

        settings.mode = BotMode.STATIC_POINT
        state.player.fresh = False
        self.assertFalse(
            self.update_at(module, state, 3.0, new_sample=True)
        )

        self.assertEqual(input_manager.presses, [])
        self.assertEqual(module.status, MovementStatus.IDLE)
        self.assertFalse(state.navigation_active)

    def test_one_coordinate_of_jitter_does_not_validate_direction(self):
        state, settings = create_state()
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)
        self.start_forced_return(module, state)

        self.assertTrue(
            self.evaluate_current_command(module, state, x=119)
        )

        self.assertIsNone(module._candidate_key)
        self.assertIsNone(module._preferred_key)
        self.assertEqual(
            [key for key, _ in input_manager.presses],
            ["W", "A"],
        )

    def test_online_calibration_converges_with_forward_and_strafe(self):
        state, settings = create_state(x=120, y=120)
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)
        handled_presses = 0
        now = 1.0

        for _ in range(40):
            self.update_at(
                module,
                state,
                now,
                new_sample=now > 1.0,
            )
            if len(input_manager.presses) > handled_presses:
                key, hold_ms = input_manager.presses[-1]
                handled_presses = len(input_manager.presses)
                distance = max(1, round(hold_ms * 6 / 1000))
                if key == "W":
                    state.player.x -= distance
                elif key == "A":
                    state.player.y -= distance
                else:
                    state.player.y += distance
            if module.status == MovementStatus.IDLE and now > 1.0:
                break
            now += 0.75

        self.assertEqual(module.status, MovementStatus.IDLE)
        self.assertEqual(module.reason, "en_posicion")
        self.assertLessEqual(state.navigation_distance, module.ARRIVAL_TOLERANCE)
        self.assertIn("W", [key for key, _ in input_manager.presses])
        self.assertIn("A", [key for key, _ in input_manager.presses])


if __name__ == "__main__":
    unittest.main()
