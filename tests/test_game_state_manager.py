import dataclasses
import threading
import time
import unittest
from unittest.mock import patch

from core.managers.game_state_manager import GameStateManager
from core.models.game_state import GameState
from core.models.vision_snapshot import VisionSnapshot


class FakeProcessManager:
    def get_active_game(self):
        return {"id": "test"}

    def get_window_position(self):
        return {"width": 1920, "height": 1080}

    def get_window_handle(self):
        return 1234

    def is_connected(self):
        return True


class BlockingVision:
    entered = threading.Event()
    release = threading.Event()
    calls = []

    def __init__(self, *_args, **_kwargs):
        self.latest_image_observed_at = 0.0

    def start(self):
        self.calls.append(("start", threading.get_ident()))

    def update(self, state):
        self.calls.append(("update", threading.get_ident()))
        self.entered.set()
        self.release.wait(1.0)
        state.player.hp_percent = 73
        self.latest_image_observed_at = time.perf_counter()

    def update_auxiliary(self, _state):
        pass

    def reset_position_reader(self):
        pass

    def stop(self):
        self.calls.append(("stop", threading.get_ident()))


class StartupBlockingVision:
    entered = threading.Event()
    release = threading.Event()

    def __init__(self, *_args, **_kwargs):
        self.latest_image_observed_at = 0.0

    def start(self):
        self.entered.set()
        self.release.wait(1.0)

    def update(self, _state):
        pass

    def update_auxiliary(self, _state):
        pass

    def reset_position_reader(self):
        pass

    def stop(self):
        pass


class GameStateManagerTests(unittest.TestCase):

    def setUp(self):
        BlockingVision.entered = threading.Event()
        BlockingVision.release = threading.Event()
        BlockingVision.calls = []
        StartupBlockingVision.entered = threading.Event()
        StartupBlockingVision.release = threading.Event()

    @staticmethod
    def finish_stop(manager):
        deadline = time.perf_counter() + 1.0
        while time.perf_counter() < deadline:
            if manager.stop():
                return True
            time.sleep(0.01)
        return False

    def test_slow_vision_never_blocks_the_automation_snapshot_tick(self):
        manager = GameStateManager(FakeProcessManager())
        with patch(
            "core.managers.game_state_manager.VisionManager",
            BlockingVision,
        ):
            manager.start()
            self.assertTrue(BlockingVision.entered.wait(0.5))
            started = time.perf_counter()

            manager.update()

            self.assertLess(time.perf_counter() - started, 0.03)
            BlockingVision.release.set()
            self.assertTrue(self.finish_stop(manager))

        thread_ids = {thread_id for _, thread_id in BlockingVision.calls}
        self.assertEqual(len(thread_ids), 1)
        self.assertNotIn(threading.get_ident(), thread_ids)

    def test_stop_is_pending_while_the_vision_thread_is_still_alive(self):
        manager = GameStateManager(FakeProcessManager())
        with patch(
            "core.managers.game_state_manager.VisionManager",
            BlockingVision,
        ):
            manager.start()
            self.assertTrue(BlockingVision.entered.wait(0.5))

            self.assertFalse(manager.stop())
            self.assertIsNotNone(manager._vision_thread)
            self.assertTrue(manager._vision_thread.is_alive())

            BlockingVision.release.set()
            self.assertTrue(self.finish_stop(manager))

        self.assertIsNone(manager._vision_thread)

    def test_start_wait_can_be_cancelled_without_declaring_shutdown(self):
        manager = GameStateManager(FakeProcessManager())
        result = []
        with patch(
            "core.managers.game_state_manager.VisionManager",
            StartupBlockingVision,
        ):
            starter = threading.Thread(
                target=lambda: result.append(manager.start()),
            )
            starter.start()
            self.assertTrue(StartupBlockingVision.entered.wait(0.5))

            manager.request_stop()
            starter.join(0.5)

            self.assertEqual(result, [False])
            self.assertFalse(manager.stop())

            StartupBlockingVision.release.set()
            self.assertTrue(self.finish_stop(manager))

        self.assertIsNone(manager._vision_thread)

    def test_stop_requested_before_start_is_latched_then_cleared(self):
        manager = GameStateManager(FakeProcessManager())
        manager.request_stop()

        self.assertFalse(manager.start())
        self.assertTrue(manager.stop())

        with patch(
            "core.managers.game_state_manager.VisionManager",
            BlockingVision,
        ):
            self.assertTrue(manager.start())
            BlockingVision.release.set()
            self.assertTrue(self.finish_stop(manager))

    def test_vision_snapshot_is_immutable(self):
        state = GameState()
        snapshot = VisionSnapshot.from_state(
            state,
            sequence=1,
            published_at=2.0,
            frame_observed_at=2.0,
            position_epoch=0,
        )

        with self.assertRaises(dataclasses.FrozenInstanceError):
            snapshot.connected = True

    def test_resource_validity_and_timestamps_cross_the_snapshot_boundary(self):
        manager = GameStateManager(FakeProcessManager())
        observed = GameState()
        observed.player.update_hp(37.0, observed_at=10.0)
        observed.player.update_mp(24.0, observed_at=11.0)
        snapshot = VisionSnapshot.from_state(
            observed,
            sequence=1,
            published_at=12.0,
            frame_observed_at=12.0,
            position_epoch=0,
        )

        manager._apply_snapshot(snapshot, position_epoch=0)

        self.assertEqual(manager.state.player.hp_percent, 37.0)
        self.assertTrue(manager.state.player.hp_valid)
        self.assertEqual(manager.state.player.hp_updated_at, 10.0)
        self.assertEqual(manager.state.player.mp_percent, 24.0)
        self.assertTrue(manager.state.player.mp_valid)
        self.assertEqual(manager.state.player.mp_updated_at, 11.0)

    def test_refresh_rejects_a_position_from_the_previous_epoch(self):
        manager = GameStateManager(FakeProcessManager())
        observed = GameState()
        observed.connected = True
        observed.player.update_position(120, 130, observed_at=time.perf_counter())
        now = time.perf_counter()
        old_snapshot = VisionSnapshot.from_state(
            observed,
            sequence=1,
            published_at=now,
            frame_observed_at=now,
            position_epoch=0,
        )
        manager.refresh_player_position()
        manager._latest_snapshot = old_snapshot

        manager.update()

        self.assertFalse(manager.state.player.position_valid)

    def test_stale_frame_disables_state_instead_of_reusing_old_target(self):
        manager = GameStateManager(FakeProcessManager())
        observed = GameState()
        observed.connected = True
        observed.target.exists = True
        observed.in_combat = True
        now = time.perf_counter()
        manager._latest_snapshot = VisionSnapshot.from_state(
            observed,
            sequence=1,
            published_at=now,
            frame_observed_at=now - manager.FRAME_TIMEOUT_SECONDS - 0.1,
            position_epoch=0,
        )

        manager.update()

        self.assertFalse(manager.state.connected)
        self.assertFalse(manager.state.target.exists)
        self.assertFalse(manager.state.in_combat)


if __name__ == "__main__":
    unittest.main()
