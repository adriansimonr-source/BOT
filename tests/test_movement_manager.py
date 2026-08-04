import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.models.bot_settings import BotMode, BotSettings
from core.modules.movement_manager import MovementManager, MovementStatus


class FakeInput:

    def __init__(self):
        self.presses = []
        self.release_count = 0

    def press(self, key, hold_ms=50):
        self.presses.append((key, hold_ms))
        return True

    def release_all(self):
        self.release_count += 1


class BusyInput(FakeInput):

    def __init__(self):
        super().__init__()
        self.busy = True

    def press(self, key, hold_ms=50):
        if self.busy:
            return False
        return super().press(key, hold_ms)


def create_state(x=110, y=100, *, radius_mode=BotMode.STATIC_POINT):
    player = SimpleNamespace(
        x=x,
        y=y,
        start_x=100,
        start_y=100,
        position_locked=True,
        position_valid=True,
        position_updated_at=0.0,
        position_revision=1,
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

    def test_first_fresh_sample_outside_radius_forces_return(self):
        state, settings = create_state()
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)

        with patch("core.modules.movement_manager.time.perf_counter", return_value=1.0):
            sent = module.update(state)

        self.assertTrue(sent)
        self.assertEqual(input_manager.presses, [("W", 250)])
        self.assertTrue(state.navigation_active)
        self.assertEqual(state.navigation_reason, "fuera_de_radio")

    def test_repeats_a_key_that_reduces_distance_and_stops_on_arrival(self):
        state, settings = create_state()
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)

        with patch("core.modules.movement_manager.time.perf_counter", return_value=1.0):
            module.update(state)

        state.player.x = 108
        state.player.position_revision = 2
        with patch("core.modules.movement_manager.time.perf_counter", return_value=2.0):
            module.update(state)

        self.assertEqual([key for key, _ in input_manager.presses], ["W", "W"])

        state.player.x = 101
        state.player.position_revision = 3
        with patch("core.modules.movement_manager.time.perf_counter", return_value=3.0):
            module.update(state)

        self.assertEqual(module.status, MovementStatus.IDLE)
        self.assertFalse(state.navigation_active)
        self.assertEqual(state.navigation_reason, "en_posicion")
        self.assertEqual(input_manager.release_count, 1)

    def test_tries_lateral_recovery_when_no_key_moves_the_player(self):
        state, settings = create_state()
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)

        with patch("core.modules.movement_manager.time.perf_counter", return_value=1.0):
            module.update(state)

        for revision in range(2, 7):
            state.player.position_revision = revision
            with patch(
                "core.modules.movement_manager.time.perf_counter",
                return_value=float(revision),
            ):
                module.update(state)

        self.assertEqual(
            [key for key, _ in input_manager.presses],
            ["W", "A", "D", "A", "D", "W"],
        )
        self.assertEqual(module.status, MovementStatus.RECOVERING)
        self.assertEqual(state.navigation_reason, "bloqueado")

    def test_selected_target_pauses_and_releases_navigation(self):
        state, settings = create_state(radius_mode=BotMode.STATIC_100)
        settings.set_return_delay(3)
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)

        with patch("core.modules.movement_manager.time.perf_counter", return_value=1.0):
            module.update(state)
        state.player.position_revision = 2
        with patch("core.modules.movement_manager.time.perf_counter", return_value=4.1):
            module.update(state)

        state.target.exists = True
        with patch("core.modules.movement_manager.time.perf_counter", return_value=4.2):
            module.update(state)

        self.assertEqual(module.status, MovementStatus.PAUSED)
        self.assertFalse(state.navigation_active)
        self.assertEqual(input_manager.release_count, 1)

    def test_outside_radius_overrides_target_and_combat(self):
        state, settings = create_state(
            x=131,
            y=140,
            radius_mode=BotMode.STATIC_50,
        )
        state.target.exists = True
        state.in_combat = True
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)

        with patch("core.modules.movement_manager.time.perf_counter", return_value=1.0):
            sent = module.update(state)

        self.assertTrue(sent)
        self.assertEqual(input_manager.presses, [("W", 250)])
        self.assertTrue(state.navigation_active)
        self.assertEqual(state.navigation_reason, "fuera_de_radio")

    def test_quiet_timeout_returns_to_start_even_inside_radius(self):
        state, settings = create_state(radius_mode=BotMode.STATIC_100)
        settings.set_return_delay(3)
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)

        with patch("core.modules.movement_manager.time.perf_counter", return_value=1.0):
            module.update(state)
        state.player.position_revision = 2
        with patch("core.modules.movement_manager.time.perf_counter", return_value=4.1):
            module.update(state)

        self.assertEqual(input_manager.presses, [("W", 250)])
        self.assertEqual(state.navigation_reason, "quieto")

    def test_unlimited_or_stale_positions_never_move(self):
        state, settings = create_state(radius_mode=BotMode.OFF)
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)

        with patch("core.modules.movement_manager.time.perf_counter", return_value=1.0):
            module.update(state)
        state.player.position_revision = 2
        with patch("core.modules.movement_manager.time.perf_counter", return_value=2.0):
            module.update(state)

        settings.mode = BotMode.STATIC_POINT
        state.player.fresh = False
        state.player.position_revision = 3
        with patch("core.modules.movement_manager.time.perf_counter", return_value=3.0):
            module.update(state)

        self.assertEqual(input_manager.presses, [])
        self.assertFalse(state.navigation_active)

    def test_retries_when_the_input_scheduler_is_temporarily_busy(self):
        state, settings = create_state()
        input_manager = BusyInput()
        module = MovementManager(input_manager, settings)

        with patch("core.modules.movement_manager.time.perf_counter", return_value=1.0):
            sent = module.update(state)

        self.assertFalse(sent)
        self.assertEqual(module.status, MovementStatus.RETURNING)
        self.assertEqual(module.reason, "esperando_entrada")

        input_manager.busy = False
        with patch("core.modules.movement_manager.time.perf_counter", return_value=1.1):
            sent = module.update(state)

        self.assertTrue(sent)
        self.assertEqual(input_manager.presses, [("W", 250)])

    def test_euclidean_boundaries_for_50_100_and_150(self):
        cases = (
            (BotMode.STATIC_50, (130, 140), (131, 140), 50.0),
            (BotMode.STATIC_100, (160, 180), (161, 180), 100.0),
            (BotMode.STATIC_150, (190, 220), (191, 220), 150.0),
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
                with patch(
                    "core.modules.movement_manager.time.perf_counter",
                    return_value=1.0,
                ):
                    module.update(state)

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
                with patch(
                    "core.modules.movement_manager.time.perf_counter",
                    return_value=1.0,
                ):
                    module.update(state)

                self.assertGreater(state.navigation_distance, radius)
                self.assertEqual(input_manager.presses, [("W", 250)])
                self.assertEqual(state.navigation_reason, "fuera_de_radio")

    def test_coordinate_change_without_new_revision_does_not_trigger_radius(self):
        state, settings = create_state(
            x=130,
            y=140,
            radius_mode=BotMode.STATIC_50,
        )
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)

        with patch("core.modules.movement_manager.time.perf_counter", return_value=1.0):
            module.update(state)
        state.player.x = 131
        with patch("core.modules.movement_manager.time.perf_counter", return_value=1.1):
            module.update(state)

        self.assertEqual(input_manager.presses, [])

    def test_radius_waits_for_a_fresh_sample_after_coordinate_timeout(self):
        state, settings = create_state(
            x=131,
            y=140,
            radius_mode=BotMode.STATIC_50,
        )
        input_manager = FakeInput()
        module = MovementManager(input_manager, settings)

        with patch("core.modules.movement_manager.time.perf_counter", return_value=1.0):
            module.update(state)
        with patch("core.modules.movement_manager.time.perf_counter", return_value=4.0):
            module.update(state)
        with patch("core.modules.movement_manager.time.perf_counter", return_value=4.1):
            module.update(state)

        self.assertEqual(input_manager.presses, [("W", 250)])
        self.assertEqual(state.navigation_reason, "sin_coordenada_nueva")

        state.player.position_revision = 2
        with patch("core.modules.movement_manager.time.perf_counter", return_value=5.0):
            module.update(state)

        self.assertEqual(input_manager.presses, [("W", 250), ("W", 250)])


if __name__ == "__main__":
    unittest.main()
